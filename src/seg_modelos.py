# %% [markdown]
# ## 8. Comparación de modelos de machine learning y deep learning
#
# Todos los modelos usan el mismo `Pipeline` (mismo `ColumnTransformer`, mismas variables y mismos pesos para caudales altos) y se evalúan en el mismo test:
#
# - Ridge: regresión lineal regularizada (referencia lineal).
# - Random Forest: promedio de árboles entrenados en paralelo.
# - XGBoost y LightGBM: gradient boosting (árboles en serie que corrigen el error de los anteriores).
# - Red neuronal profunda (MLP, deep learning): tres capas ocultas (64, 32 y 16 neuronas, activación ReLU), optimizador Adam, regularización L2 y parada temprana con el 15 % final del entrenamiento como validación.

# %%
from sklearn.neural_network import MLPRegressor
modelos = {
    'Ridge': lambda: Ridge(alpha=1.0),
    'Random Forest': lambda: RandomForestRegressor(n_estimators=300, min_samples_leaf=5, n_jobs=-1, random_state=SEED),
    'XGBoost': lambda: XGBRegressor(n_estimators=400, learning_rate=0.03, max_depth=5, subsample=0.8, colsample_bytree=0.8, random_state=SEED, n_jobs=2),
    'LightGBM': lgbm,
    'Red neuronal MLP (DL)': lambda: MLPRegressor(hidden_layer_sizes=(64, 32, 16), activation='relu', alpha=1e-3, learning_rate_init=1e-3,
                                                 max_iter=300, early_stopping=True, validation_fraction=0.15, n_iter_no_change=20, random_state=SEED)}
comp = []
for h in HORIZ:
    _, _, ite = datos_h(h)
    for n, f_ in modelos.items():
        m, _ = evaluar(h, entrenar(h, f_(), ALL_COLS), ite)
        comp.append(dict(h=h, modelo=n, **m))
comp = pd.DataFrame(comp)
tab_comp = comp.pivot(index='modelo', columns='h', values='Skill_pers').loc[list(modelos)]
print('Skill frente a la persistencia (test):'); print(tab_comp.round(3))
comp[comp.h == 3].set_index('modelo').drop(columns='h').round(3)

# %%
fig, ax = plt.subplots(figsize=(8, 3.6)); wb = 0.16
cols_m = ['#c9c8c3', '#8a8984', '#2a78d6', C_MOD, '#4a3aa7']
for i, (n, c) in enumerate(zip(tab_comp.index, cols_m)):
    ax.bar(np.arange(len(HORIZ)) + (i - 2) * wb, tab_comp.loc[n], width=wb, color=c, label=n)
ax.set_xticks(range(len(HORIZ))); ax.set_xticklabels([f'h = {h} día{"s" if h > 1 else ""}' for h in HORIZ])
ax.set_ylim(0, 0.65); ax.set_ylabel('Skill vs persistencia (test)'); ax.legend(fontsize=7.5, ncol=3, loc='upper left')
ax.set_title('Comparación de modelos de machine learning y deep learning', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/comparacion_modelos.png', dpi=150); plt.show()

# %%
# Efecto de ponderar los caudales altos (LightGBM, h = 3)
_, _, ite = datos_h(3)
pond = pd.DataFrame({f'Peso 3 a Q > Q90: {p}': evaluar(3, entrenar(3, lgbm(), ALL_COLS, p), ite)[0] for p in [False, True]}).T
pond.round(3)

# %% [markdown]
# Los modelos de boosting superan al resto en los tres horizontes. La red neuronal densa supera a la persistencia y a Ridge, pero queda por debajo de los árboles: con ~7 000 días de entrenamiento, variables tabulares heterogéneas y pocas crecidas, los árboles aprovechan mejor la información que una red, que necesita más datos para aprender las mismas relaciones no lineales. Se adopta LightGBM por su desempeño y menor costo de entrenamiento.

# %% [markdown]
# ## 9. Optimización de hiperparámetros (LightGBM, validación cruzada temporal)
#
# `RandomizedSearchCV` con `TimeSeriesSplit` (4 bloques, 15 combinaciones) sobre el período de entrenamiento, para h = 3: cada bloque de validación es posterior a su bloque de entrenamiento, sin fuga de información futura.

# %%
H = 3
y, itr, ite = datos_h(H)
busqueda = RandomizedSearchCV(
    crear_pipeline(LGBMRegressor(verbose=-1, random_state=SEED, subsample_freq=1, n_jobs=2), ALL_COLS),
    param_distributions={
        'modelo__n_estimators': [200, 400, 600],
        'modelo__learning_rate': [0.01, 0.02, 0.03, 0.05],
        'modelo__num_leaves': [15, 31, 63],
        'modelo__min_child_samples': [10, 20, 30, 50],
        'modelo__subsample': [0.7, 0.8, 0.9],
        'modelo__colsample_bytree': [0.6, 0.8, 1.0],
        'modelo__reg_lambda': [0, 1, 5]},
    n_iter=15, cv=TimeSeriesSplit(n_splits=4), scoring='neg_mean_squared_error', random_state=SEED, n_jobs=1)
busqueda.fit(X.loc[itr, ALL_COLS], y[itr], modelo__sample_weight=pesos_muestra(H, itr))
MEJORES = {k.replace('modelo__', ''): v for k, v in busqueda.best_params_.items()}
mk = lambda **kw: LGBMRegressor(verbose=-1, random_state=SEED, subsample_freq=1, n_jobs=2, **{**MEJORES, **kw})
print('Mejores hiperparámetros:', MEJORES)
m_tuned, _ = evaluar(H, busqueda.best_estimator_, ite)
m_def = comp.query('modelo == "LightGBM" and h == 3').iloc[0][['NSE', 'KGE', 'Skill_pers', 'RMSE', 'RMSE_alto', 'PBIAS_alto']]
pd.DataFrame({'LightGBM por defecto': m_def, 'LightGBM optimizado': pd.Series(m_tuned), 'Persistencia': base.loc[H]}).round(3)

# %% [markdown]
# ## 10. Modelos finales (h = 1, 3 y 5 días)
#
# Un modelo LightGBM optimizado por horizonte, entrenado con todas las variables (caudales recientes y tendencias, P1 a P30, lluvia rezagada, API y mes).

# %%
finales, metricas = {}, {}
for h in HORIZ:
    finales[h] = entrenar(h, mk(), ALL_COLS)
    _, _, ite_h = datos_h(h)
    metricas[h], _ = evaluar(h, finales[h], ite_h)
metricas_df = pd.DataFrame(metricas).T
metricas_df.index.name = 'h'
metricas_df = metricas_df.join(base[['NSE', 'RMSE_alto']].rename(columns={'NSE': 'NSE_pers', 'RMSE_alto': 'RMSE_alto_pers'}))
R['metricas_finales'] = metricas_df.round(4).to_dict(orient='index')
metricas_df.round(3)

# %%
def serie_pronostico(h, pipe):
    """Observado, modelo y persistencia indexados por la FECHA OBJETIVO (t + h)."""
    _, _, ite_h = datos_h(h)
    idx = ite_h[ite_h].index
    q0 = serie.Q[idx].values
    d = pd.DataFrame({'obs': serie.Q.shift(-h)[idx].values, 'mod': q0 * np.exp(pipe.predict(X.loc[idx])), 'pers': q0},
                     index=idx + pd.Timedelta(days=h))
    return d.asfreq('D')
SP = {h: serie_pronostico(h, finales[h]) for h in HORIZ}
sp = SP[H]

# %% [markdown]
# ## 11. Evaluación de la serie completa (test 2013–2023)

# %%
fig, axs = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
for ax, h in zip(axs, [3, 5]):
    ax.plot(SP[h].index, SP[h].obs, color=C_OBS, lw=1.2, label='Observado')
    ax.plot(SP[h].index, SP[h]['mod'], color=C_MOD, lw=0.9, label=f'Pronóstico a {h} días')
    ax.axhline(Q90, color='#8a8984', lw=0.8, ls='--'); ax.text(SP[h].index[20], Q90 * 1.03, f'Q10 de permanencia = {Q90:.0f} m³/s', color='#52514e')
    ax.set_ylabel('Q (m³/s)'); ax.legend(loc='upper right')
axs[0].set_title('Pronóstico en Villa Florida — período de test', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/hidrograma_test.png', dpi=150); plt.show()

# %%
fig, axs = plt.subplots(1, 3, figsize=(12, 4.2), sharex=True, sharey=True)
for ax, h in zip(axs, HORIZ):
    d = SP[h].dropna()
    ax.scatter(d.obs, d['mod'], s=6, color=C_OBS, alpha=0.35, edgecolors='none')
    lim = [0, 2000]
    ax.plot(lim, lim, color='#52514e', lw=1); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_title(f'h = {h} día{"s" if h > 1 else ""} · NSE {metricas[h]["NSE"]:.3f}', loc='left')
    ax.set_xlabel('Q observado (m³/s)')
axs[0].set_ylabel('Q pronosticado (m³/s)')
plt.tight_layout(); plt.savefig(f'{FIG}/dispersion.png', dpi=150); plt.show()

# %%
d = sp.dropna()
exc = np.arange(1, len(d) + 1) / (len(d) + 1) * 100
fig, ax = plt.subplots(figsize=(7.5, 4))
ax.plot(exc, np.sort(d.obs.values)[::-1], color=C_OBS, lw=2, label='Observado')
ax.plot(exc, np.sort(d['mod'].values)[::-1], color=C_MOD, lw=1.4, ls='--', label=f'Pronóstico a {H} días')
ax.set_yscale('log'); ax.set_xlabel('Porcentaje del tiempo en que se iguala o supera (%)'); ax.set_ylabel('Q (m³/s)')
ax.axhline(Q90, color='#8a8984', lw=0.8, ls=':')
ax.legend(); ax.set_title('Curva de permanencia de caudales — test', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/curva_permanencia.png', dpi=150); plt.show()

# %% [markdown]
# ## 12. Alcance del pronóstico: dónde es confiable y por qué se excluyen los estiajes
#
# Se calcula el error relativo por tramo de la curva de permanencia (entrenamiento) y por estado del río, para cada horizonte.

# %%
q_tr = serie.Q[TRAIN].dropna()
PERM = {p: float(q_tr.quantile(1 - p / 100)) for p in [2, 5, 10, 25, 50, 75]}
cortes = [0, PERM[75], PERM[50], PERM[25], PERM[10], PERM[5], PERM[2], np.inf]
etq = ['< 112 (superado > 75 % del tiempo)', '112–263 (50–75 %)', '263–500 (25–50 %)', '500–823 (10–25 %)', '823–993 (5–10 %)', '993–1 180 (2–5 %)', '> 1 180 (< 2 %)']
etq = [e.replace('112', f'{PERM[75]:.0f}').replace('263', f'{PERM[50]:.0f}').replace('500', f'{PERM[25]:.0f}').replace('823', f'{PERM[10]:.0f}').replace('993', f'{PERM[5]:.0f}') for e in etq]
def resumen_err(g):
    return pd.Series({'dias': len(g), 'error_tipico_pct': 100 * g.err.abs().median(), 'dentro_20pct': 100 * (g.err.abs() <= 0.20).mean(),
                      'sesgo_pct': 100 * (g['mod'].sum() - g.obs.sum()) / g.obs.sum()})
VAL = {}
for h in HORIZ:
    dv = SP[h].dropna().copy(); dv['err'] = (dv['mod'] - dv.obs) / dv.obs
    dv['tramo'] = pd.cut(dv.obs, cortes, labels=etq)
    VAL[h] = dv.groupby('tramo', observed=True).apply(resumen_err).iloc[::-1]
val_perm = pd.concat({f'h={h}': VAL[h][['error_tipico_pct', 'dentro_20pct']] for h in HORIZ}, axis=1)
val_perm.insert(0, 'dias', VAL[3]['dias'])
dv = SP[H].dropna().copy(); dv['err'] = (dv['mod'] - dv.obs) / dv.obs; dv['subiendo'] = dv.obs / dv.pers > 1.10
val_estado = pd.DataFrame({'Río estable o bajando': resumen_err(dv[~dv.subiendo]), 'Río subiendo (> 10 % en 3 días)': resumen_err(dv[dv.subiendo]),
                           'Caudal alto (> Q10 perm.) y subiendo': resumen_err(dv[dv.subiendo & (dv.obs > Q90)]),
                           'Caudal alto (> Q10 perm.) sin subida': resumen_err(dv[~dv.subiendo & (dv.obs > Q90)])}).T
display(val_perm.round(1)); display(val_estado.round(1))

# %%
# Variabilidad de los estiajes y desempeño dentro del alcance (Q(t) >= caudal de 75 % de permanencia)
lq = np.log(serie.Q)
var_rel = pd.DataFrame({'Estiaje (< Q75 perm.)': lq.diff()[serie.Q.shift(1) < PERM[75]].abs().describe(percentiles=[0.5, 0.9]),
                        'Medios y altos (>= Q75 perm.)': lq.diff()[serie.Q.shift(1) >= PERM[75]].abs().describe(percentiles=[0.5, 0.9])}).T
from scipy import stats
qmin7 = serie.Q.rolling(7).mean().resample('YE').min()[serie.Q.resample('YE').count() > 330]
kt = stats.kendalltau(qmin7.index.year, qmin7.values); sen = stats.theilslopes(qmin7.values, qmin7.index.year)[0]
print(f'Cambio diario relativo |Δlog Q|: mediana {var_rel.loc["Estiaje (< Q75 perm.)", "50%"]:.3f} en estiaje frente a {var_rel.loc["Medios y altos (>= Q75 perm.)", "50%"]:.3f} en caudales medios y altos')
print(f'Caudal mínimo anual de 7 días: tendencia de Sen {sen:.2f} m³/s/año (Kendall p = {kt.pvalue:.3f})')
filas = []
for h in HORIZ:
    _, _, ite_h = datos_h(h)
    dom = ite_h & (serie.Q >= PERM[75])
    m_dom, _ = evaluar(h, finales[h], dom)
    filas.append(dict(h=h, dias=int(dom.sum()), **{k: m_dom[k] for k in ['NSE', 'KGE', 'Skill_pers', 'RMSE_alto']}))
dominio = pd.DataFrame(filas).set_index('h')
R['alcance'] = {'umbrales_permanencia': PERM, 'max_test': float(sp.obs.max()), 'error_por_tramo': {str(h): VAL[h].reset_index().round(2).to_dict(orient='records') for h in HORIZ},
                'estado_h3': val_estado.round(2).to_dict(orient='index'), 'variabilidad': var_rel.round(4).to_dict(orient='index'),
                'qmin7_sen': float(sen), 'qmin7_p': float(kt.pvalue), 'metricas_dominio': dominio.round(4).to_dict(orient='index')}
fig, ax = plt.subplots(figsize=(8, 3.4))
ax.bar(qmin7.index.year, qmin7.values, color=C_OBS, width=0.8)
x0 = qmin7.index.year.values; ax.plot(x0, np.median(qmin7.values - sen * x0) + sen * x0, color=C_MOD, lw=1.3, label=f'Tendencia de Sen: {sen:.1f} m³/s por año (p = {kt.pvalue:.3f})')
ax.set_ylabel('Q mínimo de 7 días (m³/s)'); ax.legend(fontsize=8); ax.set_title('Caudal mínimo anual en Villa Florida', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/estiaje_minimos.png', dpi=150); plt.show()
dominio.round(3)

# %% [markdown]
# El error relativo crece al bajar el caudal: por debajo del caudal de 75 % de permanencia supera el 15 %, los cambios diarios relativos son más bruscos y el caudal mínimo anual muestra una tendencia descendente significativa que no se explica por la lluvia (posibles extracciones, cambios en la curva altura–caudal en aguas bajas). Por eso el pronóstico se limita a caudales medios y altos: la aplicación no emite pronóstico cuando el caudal del día es menor que el de 75 % de permanencia.

# %% [markdown]
# ## 13. Análisis de extremos y desfase
#
# Picos observados mayores al caudal de 10 % de permanencia, separados al menos 20 días. Para cada uno: pico observado, valor pronosticado para ese día (emitido 3 días antes), máximo pronosticado en ±5 días y desfase.
