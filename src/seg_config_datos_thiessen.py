# %% [markdown]
# ## 1. Configuración

# %%
import warnings, os, glob
from itertools import compress
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, MultiPoint, Polygon
from shapely.ops import voronoi_diagram
import joblib, shap

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor

warnings.filterwarnings('ignore')
pd.set_option('display.width', 160)
SEED = 42
np.random.seed(SEED)

RAW = 'data/raw'
PROC = 'data/processed'
FIG = 'figuras'
os.makedirs(PROC, exist_ok=True); os.makedirs(FIG, exist_ok=True)

# Estilo de gráficos: ejes y grilla recesivos, líneas finas
C_OBS, C_MOD, C_PERS, C_P = '#2a78d6', '#eb6834', '#8a8984', '#1baf7a'
plt.rcParams.update({'figure.dpi': 110, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#e4e3df', 'grid.linewidth': 0.6,
                     'axes.edgecolor': '#8a8984', 'axes.labelcolor': '#333', 'xtick.color': '#52514e',
                     'ytick.color': '#52514e', 'lines.linewidth': 1.5, 'font.size': 9, 'legend.frameon': False})

# %% [markdown]
# ## 2. Carga y limpieza de datos
#
# Formato de los archivos: `día mes año valor`. El valor `-1` indica dato faltante. Se detectó un bloque de fechas duplicadas en San Juan Bautista (1–10 ene 2018) con valores idénticos; se conserva la primera ocurrencia.
#
# No se completan faltantes con estaciones vecinas: el Thiessen dinámico redistribuye el área de la estación faltante entre las disponibles, lo que evita introducir series sintéticas que suavizan los extremos.

# %%
EST = {  # lat, lon — Estaciones_Pluviometricas.xlsx (DMH)
    'Paraguari': (-25.627040, -57.145998), 'Villarrica': (-25.753987, -56.437998),
    'Coronel_Oviedo': (-25.484017, -56.377995), 'Quyquyho': (-26.217039, -56.983002),
    'Pilar': (-26.881037, -58.318002), 'San_Juan_Bautista': (-26.669977, -57.133996),
    'Caazapa': (-26.174962, -56.355000), 'Encarnacion': (-27.225982, -55.837004)}
VF_GAUGE = (-26.392694, -57.129654)
NOMBRE = {'Paraguari': 'Paraguarí', 'Villarrica': 'Villarrica', 'Coronel_Oviedo': 'Coronel Oviedo', 'Quyquyho': 'Quyquyho',
          'Pilar': 'Pilar', 'San_Juan_Bautista': 'San Juan Bautista', 'Caazapa': 'Caazapá', 'Encarnacion': 'Encarnación'}

def leer_serie(path):
    d = pd.read_csv(path, sep=r'\s+', header=None, names=['d', 'm', 'y', 'v'])
    d.index = pd.to_datetime(dict(year=d.y, month=d.m, day=d.d))
    n_dup = d.index.duplicated().sum()
    s = d.v[~d.index.duplicated(keep='first')]
    return s.where(s >= 0), n_dup   # negativos (-1) -> NaN

P, dups = {}, {}
for k in EST:
    P[k], dups[k] = leer_serie(f'{RAW}/Precipitaciones/{k}.txt')
P = pd.DataFrame(P).asfreq('D')
Q, _ = leer_serie(f'{RAW}/Caudales/Caudal Villa Florida.txt')
Q = Q.asfreq('D').rename('Q')

print('Período:', P.index.min().date(), '→', P.index.max().date(), f'({len(P)} días)')
print('Fechas duplicadas eliminadas:', {k: v for k, v in dups.items() if v})
print('\nFaltantes (%):')
print(pd.concat([P, Q], axis=1).isna().mean().mul(100).round(1).to_string())

# %% [markdown]
# ### Series duplicadas: Quyquyho y Caazapá
#
# Las series originales de Quyquyho y Caazapá son idénticas día a día entre 1974 y 2016 (en las series entregadas por la fuente); desde 2017 se separan. Una de ellas fue completada con la otra. Para no contar dos veces la misma lluvia en el Thiessen, se trata Caazapá como faltante en 1974–2016 (tratamiento D2): en ese período su área se redistribuye entre las estaciones vecinas. La prueba de sensibilidad (Quyquyho o Caazapá como faltante) dio resultados equivalentes y ambas mejoran respecto a mantener la duplicación.

# %%
_m = P['Quyquyho'].notna() & P['Caazapa'].notna()
iguales = (P['Quyquyho'][_m] == P['Caazapa'][_m]).groupby(P.index[_m].year).mean()
print('Fracción de días idénticos Quyquyho = Caazapá por año:')
print(iguales.round(2).to_dict())
P_orig = P.copy()   # series tal como fueron entregadas (para el escenario B)
P.loc[P.index.year <= 2016, 'Caazapa'] = np.nan   # tratamiento D2
print(f"Faltantes de Caazapá tras el tratamiento: {P['Caazapa'].isna().mean():.1%}")

# %%
disp = pd.concat([P, Q.rename('Q Villa Florida')], axis=1).notna().groupby(P.index.year).mean()
fig, ax = plt.subplots(figsize=(10, 3.2))
im = ax.imshow(disp.T.values, aspect='auto', cmap='Blues', vmin=0, vmax=1, interpolation='nearest')
ax.set_yticks(range(disp.shape[1])); ax.set_yticklabels(disp.columns)
ax.set_xticks(range(0, len(disp), 3)); ax.set_xticklabels(disp.index[::3], rotation=90)
ax.grid(False); ax.set_title('Disponibilidad anual de datos (fracción de días con dato)', loc='left')
plt.colorbar(im, ax=ax, fraction=0.02)
plt.tight_layout(); plt.savefig(f'{FIG}/disponibilidad.png', dpi=150); plt.show()

# %% [markdown]
# El caudal en Villa Florida tiene un vacío continuo entre 2003 y 2012. Eso define la partición temporal: entrenamiento 1974–2002 y test 2013–2023, sin mezclar períodos.
#
# La estación Yuty (caudal) solo tiene registro desde 2016, íntegramente dentro del período de test, por lo que no se usa como predictor en esta etapa.

# %% [markdown]
# ## 3. Precipitación media areal — Thiessen dinámico
#
# Los polígonos de Thiessen se recortan con la cuenca de aporte a Villa Florida (proyección UTM 21S). Para cada día se recalculan los pesos usando únicamente las estaciones con dato; las combinaciones se guardan en caché.

# %%
cuenca = gpd.read_file(f'{RAW}/cuenca/VillaFlorida.shp').to_crs(32721)
# Disolver subcuencas y eliminar huecos internos (artefactos de la disolución)
_g = cuenca.geometry.union_all().buffer(50).buffer(-50)
_g = max(_g.geoms, key=lambda p: p.area) if _g.geom_type == 'MultiPolygon' else _g
geom = Polygon(_g.exterior)
A_KM2 = geom.area / 1e6
est_gs = gpd.GeoSeries([Point(lon, lat) for lat, lon in EST.values()], index=list(EST), crs=4326).to_crs(32721)
print(f'Área de la cuenca: {A_KM2:,.0f} km²')

_cache = {}
def pesos_thiessen(mask):
    key = tuple(bool(m) for m in mask)
    if key in _cache: return _cache[key]
    names = list(compress(EST, key))
    w, cells = pd.Series(0.0, index=list(EST)), {}
    if len(names) == 1:
        w[names[0]] = 1.0
    elif len(names) > 1:
        pts = est_gs[names]
        vor = voronoi_diagram(MultiPoint(list(pts)), envelope=geom.buffer(3e5))
        for cell in vor.geoms:
            for n in names:
                if cell.contains(pts[n]):
                    cells[n] = cell.intersection(geom)
                    w[n] = cells[n].area / geom.area
    _cache[key] = (w, cells)
    return w, cells

w_full, cells_full = pesos_thiessen([True] * len(EST))
print('Pesos de Thiessen con la red completa:')
print(w_full.sort_values(ascending=False).round(3).to_string())


# %% [markdown]
# ### Mapa de la cuenca y polígonos de Thiessen
#
# Coordenadas UTM 21S en km; norte hacia arriba (flecha N), barra de escala de 50 km.

# %%
from matplotlib.patches import FancyArrow, Rectangle
vf = gpd.GeoSeries([Point(VF_GAUGE[1], VF_GAUGE[0])], crs=4326).to_crs(32721)
XMIN, YMIN, XMAX, YMAX = geom.buffer(25e3).union(est_gs.union_all().buffer(20e3)).bounds

def dibujar_mapa(ax, cells, w, activos, titulo, etiquetas=True):
    for n, c in cells.items():
        if not c.is_empty:
            gpd.GeoSeries([c], crs=32721).plot(ax=ax, facecolor='#eef4fc', edgecolor='#2a78d6', linewidth=0.8)
    gpd.GeoSeries([geom], crs=32721).boundary.plot(ax=ax, color='#0b0b0b', linewidth=1.1)
    for n, p in est_gs.items():
        on = activos[list(EST).index(n)]
        ax.scatter(p.x, p.y, s=28 if on else 22, color=C_OBS if on else 'white', edgecolor=C_OBS if on else '#8a8984',
                   linewidth=1.2, zorder=3, marker='o' if on else 'X')
        if etiquetas:
            txt = f'{NOMBRE[n]}\n{w[n]:.1%}' if on else f'{NOMBRE[n]}\n(sin dato)'
            ax.annotate(txt, (p.x, p.y), xytext=(5, 5), textcoords='offset points', fontsize=7, color='#333',
                        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
    ax.scatter(vf.x[0], vf.y[0], s=70, marker='^', color=C_MOD, zorder=4)
    if etiquetas:
        ax.annotate('Villa Florida (Q)', (vf.x[0], vf.y[0]), xytext=(-8, -14), textcoords='offset points', fontsize=7,
                    ha='right', color='#333', bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85))
    ax.set_xlim(XMIN, XMAX); ax.set_ylim(YMIN, YMAX); ax.set_aspect('equal')
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v/1e3:.0f}'))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v/1e3:.0f}'))
    ax.set_xlabel('Este UTM 21S (km)', fontsize=7); ax.set_ylabel('Norte UTM 21S (km)', fontsize=7)
    ax.tick_params(labelsize=7); ax.grid(True, color='#eeeeea', lw=0.5)
    # flecha norte y barra de escala
    dx, dy = XMAX - XMIN, YMAX - YMIN
    ax.annotate('N', xy=(XMAX - 0.07*dx, YMAX - 0.05*dy), xytext=(XMAX - 0.07*dx, YMAX - 0.17*dy),
                ha='center', va='center', fontsize=10, fontweight='bold',
                arrowprops=dict(arrowstyle='-|>', color='#0b0b0b', lw=1.5))
    x0, y0 = XMIN + 0.05*dx, YMIN + 0.05*dy
    for i in range(2):
        ax.add_patch(Rectangle((x0 + i*25e3, y0), 25e3, 0.012*dy, facecolor='#0b0b0b' if i == 0 else 'white', edgecolor='#0b0b0b', lw=0.8))
    for i, lab in enumerate(['0', '25', '50 km']):
        ax.text(x0 + i*25e3, y0 + 0.025*dy, lab, ha='center', fontsize=6.5)
    ax.set_title(titulo, loc='left', fontsize=9)

fig, ax = plt.subplots(figsize=(7.2, 7.2))
dibujar_mapa(ax, cells_full, w_full, [True]*len(EST), f'Cuenca del Tebicuary hasta Villa Florida ({A_KM2:,.0f} km²)\nPolígonos de Thiessen y pesos con la red completa')
plt.tight_layout(); plt.savefig(f'{FIG}/mapa_thiessen.png', dpi=170); plt.show()

# %% [markdown]
# ### Thiessen dinámico: ejemplos
#
# Cuando una estación no tiene dato, su polígono desaparece y el área se reparte entre las vecinas. Se muestran dos situaciones reales del registro: la ausencia simultánea de Paraguarí y Coronel Oviedo (frecuente en los años 80) y la ausencia de Caazapá, la estación de mayor peso.

# %%
casos = [('Red completa', [True]*8),
         ('Sin Paraguarí ni Cnel. Oviedo', [n not in ('Paraguari', 'Coronel_Oviedo') for n in EST]),
         ('Sin Caazapá', [n != 'Caazapa' for n in EST])]
fig, axs = plt.subplots(1, 3, figsize=(13, 4.8))
for ax, (tit, m) in zip(axs, casos):
    w_c, cells_c = pesos_thiessen(m)
    dibujar_mapa(ax, cells_c, w_c, m, tit, etiquetas=True)
plt.tight_layout(); plt.savefig(f'{FIG}/thiessen_dinamico.png', dpi=160); plt.show()
print(pd.DataFrame({t: pesos_thiessen(m)[0] for t, m in casos}).round(3))

# %%
disp_mask = P.notna().values
W = np.array([pesos_thiessen(m)[0].values for m in disp_mask])
Pmed = pd.Series((W * np.nan_to_num(P.values)).sum(1), index=P.index)
Pmed[W.sum(1) == 0] = np.nan
cob_red = pd.Series(disp_mask @ w_full.values, index=P.index)  # fracción del área con su estación original disponible

serie = pd.DataFrame({'Pmed': Pmed, 'cob_red': cob_red, 'Q': Q})
serie.join(P).to_csv(f'{PROC}/serie_diaria.csv', index_label='fecha')
print(f'Combinaciones de estaciones distintas: {len(_cache)}')
print(f'Precipitación media anual de la cuenca: {Pmed.resample("YE").sum(min_count=330).mean():.0f} mm')
print(f'Días con cobertura original < 80 % del área: {(cob_red < 0.8).mean():.1%}')


# %%
Wdf = pd.DataFrame(W, index=P.index, columns=list(EST))
w_anual = Wdf.groupby(Wdf.index.year).mean()
orden_w = w_full.sort_values(ascending=False).index[:7]
paleta = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7']
fig, ax = plt.subplots(figsize=(10, 3.4))
ax.stackplot(w_anual.index, [w_anual[c] for c in orden_w], labels=[NOMBRE[c] for c in orden_w], colors=paleta, alpha=0.9, edgecolor='white', linewidth=0.4)
ax.set_ylim(0, 1); ax.set_xlim(w_anual.index.min(), w_anual.index.max())
ax.set_ylabel('Peso medio anual'); ax.legend(ncol=4, fontsize=7, loc='upper center', bbox_to_anchor=(0.5, -0.12))
ax.set_title('Evolución de los pesos de Thiessen dinámicos (media anual)', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/pesos_dinamicos.png', dpi=150); plt.show()

# %% [markdown]
# ### Tratamiento de los faltantes (-1): comparación de escenarios
#
# - Escenario A (adoptado): -1 → faltante; Thiessen dinámico con las estaciones disponibles.
# - Escenario B: -1 tratado como 0 mm con pesos fijos (error frecuente al leer estas series).
# - Escenario C: igual que A, pero se descartan del entrenamiento los días cuya ventana de 10 días incluye cobertura original < 50 % (con Caazapá tratada como faltante hasta 2016, la cobertura máxima en ese período es 58 %).
#
# El efecto sobre el modelo se evalúa en la sección 10.

# %%
Pmed_B = pd.Series(np.nan_to_num(P_orig.values) @ w_full.values, index=P.index)   # -1 -> 0, pesos fijos, series originales
anual = pd.DataFrame({'A: Thiessen dinámico': Pmed.resample('YE').sum(min_count=330),
                      'B: faltante = 0': Pmed_B.resample('YE').sum(min_count=330)})
anual.index = anual.index.year
dif = Pmed_B - Pmed
R = {}   # resultados clave para la memoria
R['faltantes'] = {'dias_alguna_faltante': float(P.isna().any(axis=1).mean()),
                  'Pmed_anual_A': float(anual.iloc[:, 0].mean()), 'Pmed_anual_B': float(anual.iloc[:, 1].mean()),
                  'dif_diaria_max': float(dif.abs().max()), 'anio_max_dif': int((anual.iloc[:, 0] - anual.iloc[:, 1]).idxmax()),
                  'dif_anual_max': float((anual.iloc[:, 0] - anual.iloc[:, 1]).max())}
print(R['faltantes'])
fig, ax = plt.subplots(figsize=(10, 3.4))
ax.plot(anual.index, anual.iloc[:, 0], color=C_OBS, marker='o', ms=3.5, label=anual.columns[0])
ax.plot(anual.index, anual.iloc[:, 1], color=C_MOD, marker='o', ms=3.5, ls='--', label=anual.columns[1])
ax.set_ylabel('Pmed anual (mm)'); ax.legend(loc='upper left')
ax.set_title('Precipitación media areal anual según el tratamiento de faltantes', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/faltantes_AB.png', dpi=150); plt.show()
