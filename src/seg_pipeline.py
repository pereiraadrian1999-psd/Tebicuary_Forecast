# %% [markdown]
# ## 6. Pipeline, métricas y línea base
#
# `ColumnTransformer`: numéricas → imputación por mediana + estandarización; mes → One-Hot. El mismo pipeline envuelve a todos los modelos.
#
# Métricas:
# - NSE y KGE: desempeño general del hidrograma.
# - Skill vs persistencia: `1 − MSE_modelo / MSE_persistencia`. La persistencia (Q(t+h) = Q(t)) es muy exigente en ríos de respuesta lenta; un skill > 0 indica valor agregado real.
# - RMSE en caudales altos: error cuando el caudal observado supera el P90 de entrenamiento.
#
# Pesos de muestra: los días cuyo caudal objetivo supera el P90 reciben peso 3 para priorizar el ajuste en crecidas.

# %%
def crear_pipeline(modelo, cols):
    num = [c for c in cols if c != 'mes']
    prep = ColumnTransformer([
        ('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('esc', StandardScaler())]), num),
        ('cat', OneHotEncoder(handle_unknown='ignore'), ['mes'])])
    return Pipeline([('prep', prep), ('modelo', modelo)])

def nse(o, s): return 1 - np.sum((o - s) ** 2) / np.sum((o - o.mean()) ** 2)
def kge(o, s):
    r = np.corrcoef(o, s)[0, 1]
    return 1 - np.sqrt((r - 1) ** 2 + (s.std() / o.std() - 1) ** 2 + (s.mean() / o.mean() - 1) ** 2)

def datos_h(h):
    y = np.log(serie.Q.shift(-h)) - np.log(serie.Q)
    ok = y.notna() & X['lQ_0'].notna()
    return y, ok & TRAIN, ok & TEST

def pesos_muestra(h, idx):
    return np.where(serie.Q.shift(-h)[idx] > Q90, 3.0, 1.0)

def evaluar(h, pipe, idx):
    qo = serie.Q.shift(-h)[idx].values
    q0 = serie.Q[idx].values
    qs = q0 * np.exp(pipe.predict(X.loc[idx]))
    alto = qo > Q90
    return dict(NSE=nse(qo, qs), KGE=kge(qo, qs),
                Skill_pers=1 - np.mean((qo - qs) ** 2) / np.mean((qo - q0) ** 2),
                RMSE=np.sqrt(np.mean((qo - qs) ** 2)),
                RMSE_alto=np.sqrt(np.mean((qo[alto] - qs[alto]) ** 2)),
                PBIAS_alto=100 * (qs[alto].sum() - qo[alto].sum()) / qo[alto].sum()), qs

def entrenar(h, modelo, cols, peso=True):
    y, itr, _ = datos_h(h)
    pipe = crear_pipeline(modelo, cols)
    pipe.fit(X.loc[itr, cols], y[itr], modelo__sample_weight=pesos_muestra(h, itr) if peso else None)
    return pipe

lgbm = lambda: LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=30,
                             subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, random_state=SEED)
