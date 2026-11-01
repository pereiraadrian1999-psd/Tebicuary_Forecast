# ## 13. Análisis de extremos
#
# ### Eventos de crecida en test
#
# Picos observados mayores a Q90, separados al menos 20 días. Para cada uno: pico observado, valor pronosticado para ese mismo día (emitido 3 días antes), máximo pronosticado en ±5 días y desfase entre la fecha del máximo pronosticado y la del pico observado.

# %%
from scipy.signal import find_peaks
o = sp.obs.interpolate(limit=3)
picos, _ = find_peaks(o.fillna(0).values, height=Q90, distance=20)
ev = []
for i in picos:
    t = o.index[i]
    win = sp.loc[t - pd.Timedelta(days=5): t + pd.Timedelta(days=5)]
    ev.append(dict(fecha=t.date(), Q_obs=sp.obs[t], Q_mod_mismo_dia=sp['mod'][t], Q_pers_mismo_dia=sp.pers[t],
                   Q_mod_max_5d=win['mod'].max(), desfase_mod_dias=(win['mod'].idxmax() - t).days,
                   desfase_pers_dias=(win.pers.idxmax() - t).days))
eventos = pd.DataFrame(ev)
eventos['error_pico_mod_pct'] = 100 * (eventos.Q_mod_mismo_dia - eventos.Q_obs) / eventos.Q_obs
eventos['error_pico_pers_pct'] = 100 * (eventos.Q_pers_mismo_dia - eventos.Q_obs) / eventos.Q_obs
R['eventos'] = eventos.assign(fecha=eventos.fecha.astype(str)).round(2).to_dict(orient='records')
eventos.round(1)

# %%
fig, ax = plt.subplots(figsize=(7, 3.6))
xx = np.arange(len(eventos))
ax.bar(xx - 0.2, eventos.error_pico_pers_pct, width=0.4, color=C_PERS, label='Persistencia')
ax.bar(xx + 0.2, eventos.error_pico_mod_pct, width=0.4, color=C_MOD, label=f'LightGBM (h={H})')
ax.axhline(0, color='#52514e', lw=0.8)
ax.set_xticks(xx); ax.set_xticklabels([str(f) for f in eventos.fecha], rotation=45, ha='right', fontsize=7)
ax.set_ylabel('Error en el día del pico (%)'); ax.legend()
ax.set_title('Error del pronóstico en el día del pico — eventos > Q90', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/error_picos.png', dpi=150); plt.show()

# %%
t_pico = sp.obs.idxmax()   # fecha del pico observado máximo del test
ventana = slice(t_pico - pd.Timedelta(days=58), t_pico + pd.Timedelta(days=45))
def grafico_evento(ventana, extra=None, fn='evento_pico.png', titulo=None):
    fig, axs = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True, gridspec_kw={'height_ratios': [1, 2.3]})
    pe = serie.Pmed[ventana]
    axs[0].bar(pe.index, pe.values, color=C_P, width=0.8); axs[0].invert_yaxis(); axs[0].set_ylabel('Pmed (mm)')
    e = sp[ventana]
    if extra is not None: extra(axs[1])
    axs[1].plot(e.index, e.obs, color=C_OBS, lw=2, label='Observado')
    axs[1].plot(e.index, e['mod'], color=C_MOD, lw=1.5, label=f'LightGBM (h={H})')
    axs[1].plot(e.index, e.pers, color=C_PERS, lw=1.2, ls='--', label='Persistencia (atraso = 3 días)')
    axs[1].set_ylabel('Q (m³/s)'); axs[1].legend(loc='upper left', fontsize=8)
    axs[0].set_title(titulo or f'Evento de mayor caudal en test (pico observado: {e.obs.max():,.0f} m³/s)', loc='left')
    plt.tight_layout(); plt.savefig(f'{FIG}/{fn}', dpi=150); plt.show()
grafico_evento(ventana)

# %% [markdown]
# ## 14. Desfase temporal (error de fase)
#
# En los hidrogramas el pronóstico aparece desplazado hacia la derecha: las subidas llegan tarde. Para medirlo, la serie pronosticada se desplaza L días y se busca el L que maximiza el NSE contra la observada. La persistencia a h días tiene, por definición, un atraso de h días.

# %%
def curva_desfase(o, s, Ls=range(-2, 6)):
    res = {}
    for L in Ls:
        b = s.shift(-L); m = o.notna() & b.notna()
        res[L] = nse(o[m].values, b[m].values)
    return pd.Series(res)
cd = pd.DataFrame({f'LightGBM h={h}': curva_desfase(SP[h].obs, SP[h]['mod']) for h in [1, 2, 3]})
cd['Persistencia h=3'] = curva_desfase(sp.obs, sp.pers)
atraso = cd.idxmax()
R['desfase'] = {k: int(v) for k, v in atraso.items()}
print('Atraso que maximiza el NSE (días):'); print(atraso)
fig, ax = plt.subplots(figsize=(7.5, 4))
for col, c, ls in zip(cd.columns, ['#9ec5f0', '#5a9be3', C_OBS, C_PERS], ['-', '-', '-', '--']):
    ax.plot(cd.index, cd[col], marker='o', ms=4, color=c, ls=ls, label=col)
ax.set_xlabel('Desplazamiento aplicado al pronóstico L (días)'); ax.set_ylabel('NSE')
ax.set_ylim(0.9, 1.0); ax.legend(fontsize=8)
ax.set_title('Atraso del pronóstico: NSE al desplazar la serie L días', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/desfase.png', dpi=150); plt.show()