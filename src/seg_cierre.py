# %% [markdown]
# ## 17. Retorno de la inversión (ROI) en tres escenarios
#
# El beneficio del sistema proviene de las crecidas alertadas con anticipación (daños evitables: retiro de ganado y bienes de zonas ribereñas, cierre preventivo de accesos, preparación de la ruta PY01), y su costo, de la implementación, la operación anual y las falsas alarmas. Las frecuencias de crecidas alertadas y de falsas alarmas provienen del test (alerta del clasificador, ventana de 3 días). Los valores monetarios son supuestos de referencia, a reemplazar por los de la autoridad de gestión de riesgo; el cálculo queda parametrizado.

# %%
anos_test = TEST.sum() / 365.25
cl3 = T_EV[(T_EV.ventana == 3) & (T_EV.metodo == 'Clasificador (probabilidad)')].iloc[0]
crec_ano, fa_ano = cl3.detectados / anos_test, cl3.falsas_alarmas / anos_test
ESC = pd.DataFrame({
    'Conservador': {'daño evitado por crecida alertada (USD)': 15000, 'costo por falsa alarma (USD)': 3000, 'implementación (USD)': 12000, 'operación anual (USD)': 6000},
    'Base':        {'daño evitado por crecida alertada (USD)': 40000, 'costo por falsa alarma (USD)': 2000, 'implementación (USD)': 12000, 'operación anual (USD)': 4000},
    'Optimista':   {'daño evitado por crecida alertada (USD)': 80000, 'costo por falsa alarma (USD)': 1000, 'implementación (USD)': 12000, 'operación anual (USD)': 3000}}).T
N_ANOS = 5
def roi(e):
    benef = N_ANOS * crec_ano * e['daño evitado por crecida alertada (USD)']
    costo = e['implementación (USD)'] + N_ANOS * (e['operación anual (USD)'] + fa_ano * e['costo por falsa alarma (USD)'])
    return pd.Series({'beneficio 5 años (USD)': benef, 'costo 5 años (USD)': costo, 'beneficio neto (USD)': benef - costo, 'ROI': (benef - costo) / costo})
ROI = ESC.join(ESC.apply(roi, axis=1))
R['roi'] = {'crecidas_alertadas_por_ano': float(crec_ano), 'falsas_alarmas_por_ano': float(fa_ano), 'anos': N_ANOS, 'escenarios': ROI.round(3).to_dict(orient='index')}
print(f'Crecidas alertadas por año: {crec_ano:.2f} · falsas alarmas por año: {fa_ano:.2f}')
ROI.round(2)

# %% [markdown]
# ## 18. Guardado del modelo e inferencia

# %%
resumen_app = {'metricas': metricas_df.round(4).to_dict(orient='index'), 'persistencia': base.round(4).to_dict(orient='index'),
               'comparacion': tab_comp.round(4).to_dict(orient='index'), 'ablacion_skill': tab_skill.round(4).to_dict(orient='index'),
               'shap': R['shap'], 'alcance': R['alcance'], 'cobertura': R['cobertura'], 'desfase': R['desfase'], 'alerta': R['alerta'],
               'corr_retardo': [float(c) for c in cc[:15]], 'Pmed_anual': float(Pmed.resample('YE').sum(min_count=330).mean()),
               'n_train': int(datos_h(3)[1].sum()), 'n_test': int(datos_h(3)[2].sum())}
bundle = {'modelos': finales, 'cuantiles': CUANT, 'alerta': CLASIF, 'resumen': resumen_app, 'features': ALL_COLS, 'ventanas': VENT, 'api_k': API_K,
          'horizontes': HORIZ, 'umbral_Q10_permanencia': float(Q90), 'umbral_estiaje': PERM[75], 'permanencia': PERM,
          'objetivo': 'log Q(t+h) - log Q(t)', 'hiperparametros': MEJORES, 'periodo_train': '1974-2002', 'periodo_test': '2013-2023',
          'area_km2': float(A_KM2), 'pesos_thiessen': w_full.round(4).to_dict()}
joblib.dump(bundle, 'model.pkl', compress=3)
print(f'model.pkl guardado ({os.path.getsize("model.pkl") / 1e6:.2f} MB)')

# %%
# Prueba de carga e inferencia: emisión del 7 de mayo de 2019 (crecida del período de test)
cargado = joblib.load('model.pkl')
t0 = pd.Timestamp('2019-05-07')
hist = serie.loc[t0 - pd.Timedelta(days=60):t0, ['Pmed', 'Q']]
Xh = construir_features(hist).iloc[[-1]][cargado['features']]
q_hoy = hist.Q.iloc[-1]
print(f'Emisión: mañana del {(t0 + pd.Timedelta(days=1)).date()} con datos del {t0.date()} · Q = {q_hoy:,.0f} m³/s')
for h, mdl in cargado['modelos'].items():
    qf = q_hoy * np.exp(mdl.predict(Xh)[0]); cq = cargado['cuantiles'][h]
    lo = q_hoy * np.exp(cq['p05'].predict(Xh)[0] - cq['qhat']); hi = q_hoy * np.exp(cq['p95'].predict(Xh)[0] + cq['qhat'])
    print(f'  t+{h} ({(t0 + pd.Timedelta(days=h)).date()}): {qf:,.0f} m³/s  [IC 90 %: {lo:,.0f} – {hi:,.0f}]  · observado {serie.Q.get(t0 + pd.Timedelta(days=h)):,.0f} m³/s')
for w, c in cargado['alerta'].items():
    p = c['modelo'].predict_proba(Xh)[0, 1]
    print(f'  Probabilidad de superar {Q90:,.0f} m³/s en {w} días: {p:.0%} ({"ALERTA" if p >= c["umbral_prob"] else "sin alerta"})')

# %% [markdown]
# ## 19. Muestra de datos (100 filas)
#
# Ventana de 100 días alrededor de la crecida de mayo de 2019 (período de test): precipitación por estación, Pmed y caudal en Villa Florida (Q). Es el archivo de ejemplo de la aplicación.

# %%
ini = pd.Timestamp('2019-05-15') - pd.Timedelta(days=73)
muestra = serie[['Pmed', 'Q']].join(P).loc[ini:ini + pd.Timedelta(days=99)].round(3)
muestra.to_csv('datos_muestra.csv', index_label='fecha')
print(muestra.shape); muestra.head()

# %%
import json
R['persistencia'] = base.round(4).to_dict(orient='index')
R['comparacion'] = comp.round(4).to_dict(orient='records')
R['ponderacion'] = pond.round(4).to_dict(orient='index')
R['ablacion_skill'] = tab_skill.round(4).to_dict(orient='index')
R['ganancia'] = ganancia.round(4).to_dict(orient='index')
R['optimizacion'] = {'mejores': MEJORES, 'tuned': {k: float(v) for k, v in m_tuned.items()}, 'defecto': m_def.astype(float).round(4).to_dict()}
R['general'] = {'Q90': float(Q90), 'area_km2': float(A_KM2), 'pesos': w_full.round(4).to_dict(), 'combinaciones': len(_cache),
                'Pmed_anual': float(Pmed.resample('YE').sum(min_count=330).mean()), 'corr_retardo': [float(c) for c in cc[:12]],
                'n_train': int(datos_h(3)[1].sum()), 'n_test': int(datos_h(3)[2].sum()), 't_pico': str(t_pico.date()), 'evento_eval': str(ev_eval.date())}
os.makedirs('resultados', exist_ok=True)
json.dump(R, open('resultados/resultados.json', 'w'), indent=1, default=str, ensure_ascii=False)
print('resultados/resultados.json guardado')

# %% [markdown]
# ## 20. Conclusiones
#
# 1. La lluvia media de la cuenca se calcula con Thiessen dinámico, tratando los −1 como faltantes y corrigiendo la duplicación de las series de Quyquyho y Caazapá (1974–2016).
# 2. LightGBM supera a la persistencia, a Ridge, a Random Forest y a la red neuronal profunda (MLP) en los tres horizontes; el deep learning no aporta ventaja con estos datos tabulares.
# 3. El pronóstico a 1, 3 y 5 días reduce el error cuadrático de la persistencia en ~46 %, ~54 % y ~55 %, con error típico de pocos por ciento en caudales medios y altos; en las subidas se queda corto y llega con ~1 día de atraso.
# 4. Los intervalos del 90 %, recalibrados con datos recientes, alcanzan la cobertura nominal en un período independiente.
# 5. Como alerta, el sistema detecta casi todas las crecidas que superan el caudal de 10 % de permanencia, con varios días de anticipación y menos de una falsa alarma por año; el clasificador probabilístico es el criterio recomendado.
# 6. Los estiajes no se pronostican: tienen mayor variabilidad relativa, mayor error y un régimen que cambió en el período reciente.
# 7. La mejora siguiente no depende del algoritmo sino de medir los afluentes intermedios (Tebicuary-mí y Pirapó).
