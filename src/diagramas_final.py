import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np, os
OUT = '/home/claude/work/final/figs_diag'; os.makedirs(OUT, exist_ok=True)
AZ, AZC, NAR, VER, GR, TX = '#2a78d6', '#eef4fc', '#eb6834', '#1baf7a', '#8a8984', '#0b0b0b'
plt.rcParams.update({'font.size': 9, 'font.family': 'DejaVu Sans'})

def caja(ax, x, y, w, h, txt, fc=AZC, ec=AZ, fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle='round,pad=0.02,rounding_size=0.08', fc=fc, ec=ec, lw=1.2))
    ax.text(x, y, txt, ha='center', va='center', fontsize=fs, color=TX, fontweight='bold' if bold else 'normal', wrap=True)
def flecha(ax, x1, y1, x2, y2, c=GR):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=12, color=c, lw=1.3))

# 1. Diagrama de flujo metodológico
fig, ax = plt.subplots(figsize=(8, 10.5)); ax.set_xlim(0, 10); ax.set_ylim(0, 14); ax.axis('off')
pasos = [
    (13.1, 'DATOS DE ENTRADA', '8 pluviómetros DMH (1974–2023) · Caudal Villa Florida · Shapefile de la cuenca', '#f4f3ef', '#52514e'),
    (11.6, '1. Control de calidad', '-1 → faltante · fechas duplicadas · Caazapá = Quyquyho 1974–2016 → Caazapá faltante · sin rellenar', AZC, AZ),
    (10.1, '2. Precipitación media areal', 'Thiessen dinámico: pesos recalculados cada día con las estaciones disponibles', AZC, AZ),
    (8.6, '3. Variables predictoras', 'Caudales recientes y tendencias · lluvia acumulada 1–30 días · API · mes', AZC, AZ),
    (7.1, '4. Partición temporal', 'Entrenamiento 1974–2002 · Test 2013–2023 (nunca se mezclan)', AZC, AZ),
    (5.6, '5. Modelado', 'Persistencia · Ridge · Random Forest · XGBoost · LightGBM · ventanas de lluvia', AZC, AZ),
    (4.1, '6. Optimización y modelo final', 'Búsqueda aleatoria con validación cruzada temporal · un modelo por horizonte (1, 3 y 5 días)', AZC, AZ),
    (2.6, '7. Evaluación', 'Serie completa → alcance → extremos y desfase → intervalos de confianza → alerta de crecidas → SHAP', '#fdf0ea', NAR),
    (1.1, 'PRODUCTOS', 'model.pkl · notebook · app Streamlit · memoria de cálculo', '#e9f7f1', VER)]
for y, t, d, fc, ec in pasos:
    caja(ax, 5, y, 8.6, 1.05, '', fc=fc, ec=ec)
    ax.text(5, y + 0.2, t, ha='center', va='center', fontsize=9.5, fontweight='bold', color=TX)
    ax.text(5, y - 0.22, d, ha='center', va='center', fontsize=7.8, color='#333')
for (y1, *_), (y2, *_) in zip(pasos[:-1], pasos[1:]):
    flecha(ax, 5, y1 - 0.53, 5, y2 + 0.53)
plt.tight_layout(); plt.savefig(f'{OUT}/flujo_metodologico.png', dpi=170); plt.close()

# 2. Pipeline scikit-learn
fig, ax = plt.subplots(figsize=(10, 3.6)); ax.set_xlim(0, 20); ax.set_ylim(0, 7); ax.axis('off')
caja(ax, 2, 3.5, 3.2, 3.6, 'Tabla de\nvariables\n(un día por fila)\n\n18 columnas', fc='#f4f3ef', ec='#52514e')
ax.add_patch(FancyBboxPatch((4.6, 0.4), 9.4, 6.2, boxstyle='round,pad=0.02,rounding_size=0.15', fc='none', ec=AZ, lw=1.2, ls='--'))
ax.text(9.3, 6.25, 'ColumnTransformer', ha='center', fontsize=9, fontweight='bold', color=AZ)
caja(ax, 7.2, 4.4, 4.2, 1.5, 'Numéricas (17)\nImputación por mediana\n→ Estandarización', fs=8)
caja(ax, 7.2, 1.9, 4.2, 1.3, 'Categórica: mes\n→ One-Hot (12 columnas)', fs=8)
caja(ax, 11.8, 3.2, 3.2, 2.4, 'Matriz\ntransformada\n(29 columnas)', fc='white', fs=8)
caja(ax, 16.2, 3.5, 3.0, 2.6, 'Regresor\n(LightGBM)\n\nŷ = Δlog Q', fc='#fdf0ea', ec=NAR, fs=8.5)
caja(ax, 19.1, 3.5, 1.6, 2.2, 'Q(t+h) =\nQ(t)·exp(ŷ)', fc='#e9f7f1', ec=VER, fs=7.5)
for a in [(3.6, 3.9, 5.1, 4.4), (3.6, 3.1, 5.1, 1.9), (9.3, 4.4, 10.2, 3.5), (9.3, 1.9, 10.2, 2.9), (13.4, 3.3, 14.7, 3.4), (17.7, 3.5, 18.3, 3.5)]:
    flecha(ax, *a)
ax.text(10, -0.1, 'Pipeline: todas las transformaciones se ajustan solo con el período de entrenamiento y se aplican igual en test y en la app.', ha='center', fontsize=7.8, color='#333')
plt.tight_layout(); plt.savefig(f'{OUT}/pipeline.png', dpi=170); plt.close()

# 3. Árbol de decisión y boosting (esquema)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={'width_ratios': [1.1, 1]})
ax = axs[0]; ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.axis('off')
ax.set_title('a) Un árbol de decisión', loc='left', fontsize=9.5)
caja(ax, 5, 7, 4.2, 0.9, '¿P10 > 60 mm?', fs=8.5)
caja(ax, 2.5, 4.8, 4.2, 0.9, '¿dlQ_1 > 0 (sube)?', fs=8.5)
caja(ax, 7.5, 4.8, 3.6, 0.9, '¿P10 > 20 mm?', fs=8.5)
for x, t in [(1.1, 'sube\n+25 %'), (3.9, 'sube\n+8 %'), (6.3, 'estable\n−2 %'), (8.8, 'baja\n−9 %')]:
    caja(ax, x, 2.4, 2.2, 1.2, t, fc='#fdf0ea', ec=NAR, fs=8)
for a in [(4.2, 6.55, 2.9, 5.25), (5.8, 6.55, 7.1, 5.25), (1.8, 4.35, 1.2, 3.0), (3.2, 4.35, 3.8, 3.0), (7.0, 4.35, 6.4, 3.0), (8.0, 4.35, 8.7, 3.0)]:
    flecha(ax, *a)
for x, y, t in [(3.2, 6.1, 'sí'), (6.8, 6.1, 'no'), (1.1, 3.8, 'sí'), (3.9, 3.8, 'no'), (6.3, 3.8, 'sí'), (8.8, 3.8, 'no')]:
    ax.text(x, y, t, fontsize=7.5, color=GR, ha='center')
ax.text(5, 1.0, 'Cada hoja entrega un cambio de caudal. Valores ilustrativos.', ha='center', fontsize=7.5, color='#333')
ax = axs[1]
rng = np.random.default_rng(3); x = np.linspace(0, 10, 120); yv = np.sin(x / 1.6) * 2 + 0.25 * x + rng.normal(0, 0.35, x.size)
ax.scatter(x, yv, s=7, color=GR, alpha=0.6, label='Datos')
pred = np.full_like(x, yv.mean()); cols = ['#c7dcf5', '#86b3ec', AZ, NAR]
for i, n in enumerate([1, 3, 10, 60]):
    pred = np.full_like(x, yv.mean())
    for _ in range(n):
        r = yv - pred; best = None
        for s in np.linspace(0.5, 9.5, 40):
            l, rr = r[x <= s].mean(), r[x > s].mean(); e = ((r - np.where(x <= s, l, rr)) ** 2).sum()
            if best is None or e < best[0]: best = (e, s, l, rr)
        pred += 0.3 * np.where(x <= best[1], best[2], best[3])
    ax.plot(x, pred, color=cols[i], lw=1.8, label=f'{n} árbol{"es" if n > 1 else ""}')
ax.set_title('b) Boosting: cada árbol corrige el error de los anteriores', loc='left', fontsize=9.5)
ax.legend(fontsize=7.5, frameon=False); ax.spines[['top', 'right']].set_visible(False); ax.set_xticks([]); ax.set_yticks([])
plt.tight_layout(); plt.savefig(f'{OUT}/arbol_boosting.png', dpi=170); plt.close()

# 4. Concepto de persistencia y desfase
t = np.arange(0, 30); q = 200 + 900 * np.exp(-((t - 14) / 4.0) ** 2) * (t >= 8) + 900 * np.exp(-((t - 14) / 4.0) ** 2) * (t < 8)
q = 200 + 900 * np.exp(-((t - 14) / 4.0) ** 2)
fig, ax = plt.subplots(figsize=(8, 3.4))
ax.plot(t, q, color=AZ, lw=2.2, label='Observado')
ax.plot(t + 3, q, color=GR, lw=1.6, ls='--', label='Persistencia a 3 días (misma curva, 3 días tarde)')
ax.plot(t + 1, 200 + 820 * np.exp(-((t - 14) / 4.3) ** 2), color=NAR, lw=1.6, label='Modelo: atraso ≈ 1 día y pico algo menor')
ax.annotate('', xy=(17, 1100), xytext=(14, 1100), arrowprops=dict(arrowstyle='<->', color=TX, lw=1))
ax.text(15.5, 1130, '3 días', ha='center', fontsize=8)
ax.set_xlabel('Días'); ax.set_ylabel('Q (m³/s)'); ax.set_ylim(100, 1250); ax.set_xlim(0, 32)
ax.spines[['top', 'right']].set_visible(False); ax.legend(frameon=False, fontsize=7.8, loc='upper right')
ax.set_title('Esquema: qué significa el desplazamiento de la curva pronosticada', loc='left')
plt.tight_layout(); plt.savefig(f'{OUT}/concepto_desfase.png', dpi=170); plt.close()

# 5. Concepto de bandas: cuantiles
fig, ax = plt.subplots(figsize=(7.5, 3.3))
from scipy.stats import lognorm
xs = np.linspace(600, 1800, 400); dist = lognorm(s=0.17, scale=1100); pdf = dist.pdf(xs)
ax.plot(xs, pdf, color=NAR, lw=1.8)
for lo, hi, a, lab in [(0.05, 0.95, 0.15, 'P5–P95: 90 % de probabilidad'), (0.25, 0.75, 0.35, 'P25–P75: 50 %')]:
    m = (xs >= dist.ppf(lo)) & (xs <= dist.ppf(hi)); ax.fill_between(xs[m], 0, pdf[m], color=NAR, alpha=a, lw=0, label=lab)
ax.axvline(dist.ppf(0.5), color=TX, lw=1); ax.text(dist.ppf(0.5) + 10, pdf.max() * 0.95, 'P50 (mediana)', fontsize=8)
ax.set_yticks([]); ax.set_xlabel('Caudal pronosticado para t+3 (m³/s)'); ax.spines[['top', 'right', 'left']].set_visible(False)
ax.legend(frameon=False, fontsize=8); ax.set_title('Esquema: un pronóstico con bandas en lugar de un solo valor', loc='left')
plt.tight_layout(); plt.savefig(f'{OUT}/concepto_bandas.png', dpi=170); plt.close()
print('ok')

# 6. Modelo en dos etapas (corrección con Yuty)
fig, ax = plt.subplots(figsize=(10, 3.6)); ax.set_xlim(0, 20); ax.set_ylim(0, 7); ax.axis('off')
caja(ax, 2.3, 5.0, 3.8, 1.6, 'Villa Florida y lluvia\n(caudales, P1–P30, API, mes)', fc='#f4f3ef', ec='#52514e', fs=8)
caja(ax, 2.3, 1.8, 3.8, 1.6, 'Yuty (aguas arriba)\ncaudal, variaciones,\nrelación con Villa Florida', fc='#efedf9', ec='#4a3aa7', fs=8)
caja(ax, 7.6, 5.0, 3.8, 1.8, 'Etapa 1: modelo base\nLightGBM 1974–2002\n→ Δlog Q base', fc=AZC, ec=AZ, fs=8)
caja(ax, 12.6, 3.2, 3.8, 2.2, 'Etapa 2: corrección\nLightGBM pequeño 2016–…\naprende el error del base\n→ ajuste', fc='#efedf9', ec='#4a3aa7', fs=8)
caja(ax, 17.6, 3.2, 3.6, 2.0, 'Pronóstico final\nΔlog Q = base + ajuste\nQ(t+h) = Q(t)·exp(·)', fc='#e9f7f1', ec=VER, fs=8)
for a in [(4.2, 5.0, 5.7, 5.0), (9.5, 4.6, 10.7, 3.8), (4.2, 1.8, 10.7, 2.8), (4.2, 4.5, 10.7, 3.3), (14.5, 3.2, 15.8, 3.2)]:
    flecha(ax, *a)
ax.text(10, 6.6, 'El modelo base aprovecha 30 años de registro; la corrección usa los 7 años en que existe Yuty.', ha='center', fontsize=8, color='#333')
plt.tight_layout(); plt.savefig(f'{OUT}/dos_etapas.png', dpi=170); plt.close()
print('ok2')
