# %% [markdown]
# El pronóstico reconoce todas las crecidas, pero en la subida llega con un atraso de ~1 día (la persistencia, h días). En análisis complementarios se probó reducirlo con lluvia por zonas, mayor peso a las subidas, lluvia futura (perfecta y del pronóstico meteorológico GFS), la estación aguas arriba Yuty y lluvia satelital CHIRPS: todas mejoran algo la magnitud y ninguna elimina el atraso, que se debe a los afluentes sin medición (Tebicuary-mí, Pirapó). Para la alerta el atraso pesa poco (sección 15).

# %% [markdown]
# ## 14. Intervalos de confianza
#
# Regresión cuantílica: dos modelos LightGBM estiman los percentiles 5 y 95 del cambio de caudal y forman la banda del 90 %. Como el período de test es más variable que el de entrenamiento, la banda se recalibra con los errores de 2013–2015 (recalibración conformal: se ensancha lo justo para cubrir el 90 % en ese período) y se evalúa en 2016–2023, años no usados en el ajuste ni en la recalibración. También se estima el percentil 75, usado como valor conservador en las subidas.

# %%
CUANT, filas = {}, []
for h in HORIZ:
    y_h, itr_h, ite_h = datos_h(h)
    qm = {a: crear_pipeline(mk(objective='quantile', alpha=a), ALL_COLS).fit(X.loc[itr_h, ALL_COLS], y_h[itr_h]) for a in [0.05, 0.75, 0.95]}
    ical = ite_h & (serie.index.year <= 2015); iev = ite_h & (serie.index.year >= 2016)
    yc = y_h[ical].values
    E = np.maximum(qm[0.05].predict(X.loc[ical, ALL_COLS]) - yc, yc - qm[0.95].predict(X.loc[ical, ALL_COLS]))
    qhat = float(np.quantile(E, min(1, np.ceil((len(E) + 1) * 0.9) / len(E))))
    CUANT[h] = {'p05': qm[0.05], 'p95': qm[0.95], 'p75': qm[0.75], 'qhat': qhat}
    qo_, q0_ = serie.Q.shift(-h)[iev].values, serie.Q[iev].values; alto = qo_ > Q90
    for recal in [False, True]:
        qh = qhat if recal else 0.0
        lo = q0_ * np.exp(qm[0.05].predict(X.loc[iev, ALL_COLS]) - qh); hi = q0_ * np.exp(qm[0.95].predict(X.loc[iev, ALL_COLS]) + qh)
        cov = (qo_ >= lo) & (qo_ <= hi)
        filas.append(dict(h=h, recalibrada=recal, cobertura=cov.mean(), cobertura_altos=cov[alto].mean(), ancho_medio=(hi - lo).mean(),
                          ancho_rel_medio=np.mean((hi - lo) / q0_), ancho_medio_altos=(hi - lo)[alto].mean()))
cobertura = pd.DataFrame(filas)
R['cobertura'] = cobertura.round(4).to_dict(orient='records'); R['qhat'] = {h: CUANT[h]['qhat'] for h in HORIZ}
cobertura.round(3)

# %%
def bandas(h, idx):
    q0_ = serie.Q[idx].values; Xb = X.loc[idx, ALL_COLS]; c = CUANT[h]
    return pd.DataFrame({'obs': serie.Q.shift(-h)[idx].values, 'mod': q0_ * np.exp(finales[h].predict(Xb)),
                         'lo': q0_ * np.exp(c['p05'].predict(Xb) - c['qhat']), 'hi': q0_ * np.exp(c['p95'].predict(Xb) + c['qhat'])},
                        index=idx + pd.Timedelta(days=h)).asfreq('D')
ev_eval = SP[3][SP[3].index.year >= 2016].obs.idxmax()
v2 = slice(ev_eval - pd.Timedelta(days=45), ev_eval + pd.Timedelta(days=35))
fig, axs = plt.subplots(1, 3, figsize=(13, 3.8), sharey=True)
for ax, h in zip(axs, HORIZ):
    b = bandas(h, datos_h(h)[2][datos_h(h)[2]].index)[v2]
    ax.fill_between(b.index, b.lo, b.hi, color=C_MOD, alpha=0.18, lw=0, label='Intervalo 90 %')
    ax.plot(b.index, b.obs, color=C_OBS, lw=2, label='Observado'); ax.plot(b.index, b['mod'], color=C_MOD, lw=1.3, label='Pronóstico')
    ax.axhline(Q90, color='#8a8984', lw=0.8, ls='--'); ax.set_title(f'h = {h} día{"s" if h > 1 else ""}', loc='left')
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m'))
axs[0].set_ylabel('Q (m³/s)'); axs[0].legend(fontsize=7.5, loc='upper left')
plt.suptitle(f'Crecida de {ev_eval:%m/%Y}: pronóstico con intervalo de confianza del 90 % (recalibrado)', x=0.01, ha='left', fontsize=10)
plt.tight_layout(); plt.savefig(f'{FIG}/intervalos_evento.png', dpi=150); plt.show()

# %% [markdown]
# ## 15. Alerta de crecidas: ¿se superará el caudal de 10 % de permanencia?
#
# Para alertar no hace falta acertar el caudal de un día exacto: alcanza con saber si el caudal superará el umbral (Q10 de permanencia = 823 m³/s) en los próximos 3 o 5 días. Se comparan, solo en días con el río por debajo del umbral:
#
# - Regresión, valor central: alguno de los pronósticos dentro de la ventana supera el umbral.
# - Regresión, percentil 75: ídem con el percentil 75.
# - Clasificador: LightGBM (mismo Pipeline y variables) que estima la probabilidad de superar el umbral en la ventana. El valor de corte de probabilidad se elige con predicciones fuera de muestra dentro del entrenamiento (`TimeSeriesSplit`), sin mirar el test.
# - Persistencia de la tendencia: extrapolar la subida del último día (regla simple de referencia).
#
# Evaluación por evento: cada cruce ascendente del umbral en 2013–2023 (con al menos 5 días previos por debajo) es una crecida; se registra si hubo alerta en los días previos (dentro de la ventana) y con cuánta anticipación. Una falsa alarma es un episodio de alerta sin superación en la ventana siguiente.

# %%
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score, brier_score_loss
U = Q90
PC = dict(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=20, subsample=0.8, subsample_freq=1,
          colsample_bytree=0.7, reg_lambda=5, verbose=-1, random_state=SEED, n_jobs=2)
def contingencia(o, a):
    h_ = (a & (o == 1)).sum(); fa = (a & (o == 0)).sum(); mi = ((~a) & (o == 1)).sum()
    return dict(POD=h_ / max(h_ + mi, 1), FAR=fa / max(h_ + fa, 1), CSI=h_ / max(h_ + fa + mi, 1))
def max_futuro(w): return pd.concat([serie.Q.shift(-k) for k in range(1, w + 1)], axis=1).max(1, skipna=False)
okx = X['lQ_0'].notna()
REG_C = pd.DataFrame({h: serie.Q * np.exp(finales[h].predict(X[ALL_COLS])) for h in HORIZ}).where(okx)
REG_75 = pd.DataFrame({h: serie.Q * np.exp(CUANT[h]['p75'].predict(X[ALL_COLS])) for h in HORIZ}).where(okx)
VENT_AL = [3, 5]
CLASIF, PROB_AL, filas_dia = {}, {}, []
for w in VENT_AL:
    fm = max_futuro(w); ev = (fm > U).astype(float).where(fm.notna())
    ok = ev.notna() & okx & (serie.Q <= U); itr_, ite_ = ok & TRAIN, ok & TEST
    oof = pd.Series(np.nan, index=serie.index); it = np.where(itr_)[0]
    for a, b in TimeSeriesSplit(5).split(it):
        m_ = crear_pipeline(LGBMClassifier(**PC), ALL_COLS).fit(X.iloc[it[a]][ALL_COLS], ev.iloc[it[a]])
        oof.iloc[it[b]] = m_.predict_proba(X.iloc[it[b]][ALL_COLS])[:, 1]
    mo = oof.notna(); us = np.round(np.arange(0.1, 0.81, 0.05), 2)
    u = float(us[np.argmax([contingencia(ev[mo].values, oof[mo].values >= x)['CSI'] for x in us])])
    clf = crear_pipeline(LGBMClassifier(**PC), ALL_COLS).fit(X.loc[itr_, ALL_COLS], ev[itr_])
    pr = pd.Series(clf.predict_proba(X.loc[okx, ALL_COLS])[:, 1], index=serie.index[okx]).reindex(serie.index)
    CLASIF[w] = {'modelo': clf, 'umbral_prob': u}; PROB_AL[w] = pr
    o = ev[ite_].values; clim = ev[itr_].mean(); hs = [h for h in HORIZ if h <= w]
    r = dict(ventana=w, dias=int(len(o)), dias_con_superacion=int(o.sum()), AUC=roc_auc_score(o, pr[ite_]),
             BSS=1 - brier_score_loss(o, pr[ite_]) / np.mean((o - clim) ** 2), umbral_prob=u)
    for nom, a in [('Clasificador', pr[ite_].values >= u), ('Regresión central', (REG_C.loc[ite_, hs].max(1) > U).values),
                   ('Regresión P75', (REG_75.loc[ite_, hs].max(1) > U).values)]:
        r.update({f'{nom} {k}': v for k, v in contingencia(o, a).items()})
    filas_dia.append(r)
T_DIA = pd.DataFrame(filas_dia).set_index('ventana')
T_DIA.round(3)

# %%
def eventos_cruce(U):
    c = serie.Q[(serie.Q > U) & (serie.Q.shift(1) <= U) & TEST]
    return [t for t in c.index if (serie.Q[t - pd.Timedelta(days=5):t - pd.Timedelta(days=1)] <= U).all()]
def evaluar_alerta(alarma, U, W):
    evs = eventos_cruce(U); ant = []
    for c in evs:
        a = [c - pd.Timedelta(days=k) for k in range(W, 0, -1) if alarma.get(c - pd.Timedelta(days=k), False)]
        ant.append((c - a[0]).days if a else 0)
    dias_al = alarma[alarma].index; falsos = n_ep = 0
    if len(dias_al):
        grupo = (pd.Series(dias_al).diff().dt.days != 1).cumsum().values
        for _, g in pd.Series(dias_al).groupby(grupo):
            n_ep += 1
            falsos += int(not (serie.Q[g.iloc[0] + pd.Timedelta(days=1): g.iloc[-1] + pd.Timedelta(days=W)] > U).any())
    anos = TEST.sum() / 365.25
    return dict(eventos=len(evs), detectados=int((np.array(ant) > 0).sum()), anticipacion_media=float(np.mean([a for a in ant if a > 0])),
                episodios=n_ep, falsas_alarmas=falsos, falsas_por_ano=falsos / anos, anticipacion=ant, fechas=[str(e.date()) for e in evs])
filas_ev = []
base_ok = TEST & okx & (serie.Q <= U)
for w in VENT_AL:
    hs = [h for h in HORIZ if h <= w]
    alarmas = {'Regresión (valor central)': (REG_C[hs].max(1) > U) & base_ok, 'Regresión (percentil 75)': (REG_75[hs].max(1) > U) & base_ok,
               'Clasificador (probabilidad)': (PROB_AL[w] >= CLASIF[w]['umbral_prob']) & base_ok,
               'Persistencia de la tendencia': (serie.Q * (serie.Q / serie.Q.shift(1)).clip(lower=1) ** w > U) & base_ok}
    for nom, a in alarmas.items():
        filas_ev.append(dict(ventana=w, metodo=nom, **evaluar_alerta(a, U, w)))
T_EV = pd.DataFrame(filas_ev)
R['alerta'] = {'umbral': float(U), 'umbral_prob': {w: CLASIF[w]['umbral_prob'] for w in VENT_AL},
               'por_dia': T_DIA.round(4).reset_index().to_dict(orient='records'), 'por_evento': T_EV.round(3).to_dict(orient='records')}
T_EV.drop(columns=['anticipacion', 'fechas']).round(2)

# %%
fig, axs = plt.subplots(1, 3, figsize=(12.5, 3.5))
met_cols = {'Regresión (valor central)': C_MOD, 'Regresión (percentil 75)': '#c0392b', 'Clasificador (probabilidad)': '#4a3aa7', 'Persistencia de la tendencia': C_PERS}
for ax, (col, tit) in zip(axs, [('detectados', 'Crecidas alertadas con anticipación'), ('anticipacion_media', 'Anticipación media (días)'), ('falsas_por_ano', 'Falsas alarmas por año')]):
    for i, (m, c) in enumerate(met_cols.items()):
        d_ = T_EV[T_EV.metodo == m]
        vals = d_[col] / d_.eventos if col == 'detectados' else d_[col]
        ax.bar(np.arange(len(VENT_AL)) + (i - 1.5) * 0.2, vals, width=0.2, color=c, label=m)
    ax.set_xticks(range(len(VENT_AL))); ax.set_xticklabels([f'Ventana de {w} días' for w in VENT_AL]); ax.set_title(tit, loc='left')
axs[0].set_ylim(0.8, 1.02); axs[0].yaxis.set_major_formatter(plt.matplotlib.ticker.PercentFormatter(1.0))
axs[2].legend(fontsize=7, loc='upper left')
plt.tight_layout(); plt.savefig(f'{FIG}/alerta_eventos.png', dpi=150); plt.show()

# %%
ev3 = (max_futuro(3) > U).astype(float).where(max_futuro(3).notna()); ite_ = ev3.notna() & okx & (serie.Q <= U) & TEST
pr, o = PROB_AL[3][ite_], ev3[ite_]
g = pd.cut(pr, [0, 0.02, 0.1, 0.3, 0.5, 0.7, 1.0], include_lowest=True)
conf = pd.DataFrame({'prob_media': pr.groupby(g).mean(), 'frecuencia_obs': o.groupby(g).mean(), 'dias': o.groupby(g).size()})
R['alerta']['confiabilidad_3'] = conf.reset_index(drop=True).round(4).to_dict(orient='records')
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8), gridspec_kw={'width_ratios': [1, 1.9]})
axs[0].plot([0, 1], [0, 1], color=C_PERS, lw=0.8, ls='--'); axs[0].plot(conf.prob_media, conf.frecuencia_obs, 'o-', color='#4a3aa7')
for _, r_ in conf[conf.prob_media > 0.1].iterrows():
    axs[0].annotate(f'{int(r_.dias)} d', (r_.prob_media, r_.frecuencia_obs), xytext=(6, -12), textcoords='offset points', fontsize=7, color='#52514e')
axs[0].set_xlabel('Probabilidad pronosticada'); axs[0].set_ylabel('Frecuencia observada'); axs[0].set_title('Confiabilidad (ventana de 3 días, test)', loc='left')
v_ = slice('2019-04-15', '2019-06-10'); ax = axs[1]; ax2 = ax.twinx()
ax.plot(serie.Q[v_].index, serie.Q[v_], color=C_OBS, lw=2, label='Caudal observado'); ax.axhline(U, color=C_PERS, ls='--', lw=0.8)
for w, c, dx in [(3, '#4a3aa7', -0.2), (5, '#b9b2ee', 0.2)]:
    pv = PROB_AL[w][v_].where(serie.Q[v_] <= U)
    ax2.bar(pv.index + pd.Timedelta(hours=24 * dx), pv, color=c, width=0.4, label=f'Probabilidad de superar en {w} días')
ax2.set_ylim(0, 1); ax2.set_ylabel('Probabilidad'); ax2.grid(False)
ax.set_ylabel('Q (m³/s)'); ax.set_title('Crecida de mayo de 2019', loc='left'); ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d/%m'))
h1_, l1_ = ax.get_legend_handles_labels(); h2_, l2_ = ax2.get_legend_handles_labels(); ax.legend(h1_ + h2_, l1_ + l2_, fontsize=7.5, loc='upper left')
plt.tight_layout(); plt.savefig(f'{FIG}/alerta_probabilidad.png', dpi=150); plt.show()
pd.DataFrame({'Q': serie.Q['2019-05-02':'2019-05-10'], 'prob_3d': PROB_AL[3]['2019-05-02':'2019-05-10'], 'prob_5d': PROB_AL[5]['2019-05-02':'2019-05-10']}).round(3)

# %% [markdown]
# Las alertas basadas en el modelo detectan casi todas las crecidas con 2 a 4 días de anticipación y pocas falsas alarmas; la regla de extrapolar la tendencia detecta lo mismo con varias veces más falsas alarmas. El clasificador entrega probabilidades confiables (las frecuencias observadas siguen a las probabilidades) y la mayor anticipación; se usa para decidir la alerta, y la regresión para estimar la magnitud con su intervalo.
