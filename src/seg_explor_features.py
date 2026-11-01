# %% [markdown]
# ## 4. Análisis exploratorio

# %%
fig, axs = plt.subplots(2, 1, figsize=(11, 5), sharex=True, gridspec_kw={'height_ratios': [1, 2]})
pm = Pmed.resample('MS').sum()
axs[0].bar(pm.index, pm.values, width=25, color=C_P)
axs[0].set_ylabel('Pmed mensual (mm)')
axs[1].plot(Q.index, Q.values, color=C_OBS, lw=0.8)
axs[1].set_ylabel('Q (m³/s)')
axs[1].axvspan(pd.Timestamp('1974-01-01'), pd.Timestamp('2002-12-31'), color='#2a78d6', alpha=0.05)
axs[1].axvspan(pd.Timestamp('2013-01-01'), pd.Timestamp('2023-12-31'), color='#eb6834', alpha=0.06)
axs[1].text(pd.Timestamp('1976-01-01'), Q.max() * 0.92, 'Entrenamiento', color='#333')
axs[1].text(pd.Timestamp('2014-01-01'), Q.max() * 0.92, 'Test', color='#333')
axs[0].set_title('Precipitación media areal y caudal diario en Villa Florida', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/series.png', dpi=150); plt.show()

print(serie[['Pmed', 'Q']].describe().round(1).T)

# %% [markdown]
# ### Tiempo de respuesta de la cuenca
#
# Correlación entre la lluvia del día *t* y la variación del caudal (Δlog Q) *k* días después. El máximo indica el retardo típico entre lluvia y respuesta en Villa Florida, y orienta las ventanas de acumulación a evaluar.

# %%
dlq = np.log(serie.Q).diff()
lags = range(0, 21)
cc = [serie.Pmed.corr(dlq.shift(-k)) for k in lags]
fig, ax = plt.subplots(figsize=(7, 3))
ax.bar(list(lags), cc, color=C_OBS, width=0.7)
k_max = int(np.argmax(cc))
ax.annotate(f'máx. en {k_max} días', (k_max, cc[k_max]), xytext=(8, 0), textcoords='offset points', color='#333')
ax.set_xlabel('Retardo k (días)'); ax.set_ylabel('corr(Pmed_t, ΔlogQ_t+k)')
ax.set_title('Respuesta del caudal a la lluvia', loc='left')
plt.tight_layout(); plt.savefig(f'{FIG}/correlacion_retardo.png', dpi=150); plt.show()
print('Correlación por retardo:', np.round(cc[:12], 3))

# %% [markdown]
# ## 5. Feature engineering
#
# Momento de emisión: la mañana del día t+1, cuando ya están disponibles la lectura pluviométrica asignada al día t (convención DMH) y el caudal medio del día t. Variables disponibles en ese momento:
#
# | Grupo | Variables |
# |---|---|
# | Caudal | log Q en t, t-1, t-2, t-3, t-7; Δlog Q a 1 y 3 días |
# | Lluvia acumulada | P1, P3, P5, P7, P10, P15, P30 (mm, suma de *k* días hasta t) |
# | Lluvia rezagada | P(t-1), P(t-2) |
# | Humedad antecedente | API (índice de precipitación antecedente, k = 0.9) |
# | Estacionalidad | mes (categórica → One-Hot) |
#
# Objetivo: `y = log Q(t+h) − log Q(t)`. Modelar la variación relativa en lugar del caudal absoluto permite a los árboles generalizar a caudales fuera del rango de entrenamiento; el caudal se reconstruye como `Q(t) · exp(ŷ)`.
#
# No se usa lluvia futura (sin pronóstico meteorológico), de modo que el modelo es operable con datos observados.

# %%
VENT = [1, 3, 5, 7, 10, 15, 30]
API_K = 0.9

def construir_features(df):
    """df: índice diario, columnas Pmed y Q. Devuelve la matriz de features."""
    X = pd.DataFrame(index=df.index)
    lq = np.log(df['Q'])
    for l in [0, 1, 2, 3, 7]:
        X[f'lQ_{l}'] = lq.shift(l)
    X['dlQ_1'] = lq - lq.shift(1)
    X['dlQ_3'] = lq - lq.shift(3)
    for k in VENT:
        X[f'P{k}'] = df['Pmed'].rolling(k, min_periods=k).sum()
    for l in [1, 2]:
        X[f'P_lag{l}'] = df['Pmed'].shift(l)
    p = df['Pmed'].fillna(0).values
    api = np.zeros(len(p))
    for i in range(1, len(p)):
        api[i] = API_K * api[i - 1] + p[i]
    X['API'] = api
    X['mes'] = df.index.month.astype(str)
    return X

X = construir_features(serie)
QCOLS = ['lQ_0', 'lQ_1', 'lQ_2', 'lQ_3', 'lQ_7', 'dlQ_1', 'dlQ_3']
PCOLS = [f'P{k}' for k in VENT] + ['P_lag1', 'P_lag2', 'API']
ALL_COLS = QCOLS + PCOLS + ['mes']

TRAIN = serie.index.year <= 2002
TEST = serie.index.year >= 2013
Q90 = serie.Q[TRAIN].quantile(0.90)
print(f'Umbral de caudal alto (P90 entrenamiento): {Q90:.0f} m³/s')
X.loc[TEST].dropna().head()
