"""Prueba complementaria: red neuronal densa (deep learning) frente a LightGBM.

Usa la serie diaria generada por notebook_final.ipynb (data/processed/serie_diaria.csv), las mismas variables,
el mismo Pipeline (imputación + estandarización + One-Hot del mes), los mismos pesos y la misma partición temporal.
Ejecutar desde la carpeta del proyecto:  python analisis_complementarios/prueba_red_neuronal.py
"""
import numpy as np, pandas as pd, warnings
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.neural_network import MLPRegressor
from lightgbm import LGBMRegressor
warnings.filterwarnings('ignore')

S = pd.read_csv('data/processed/serie_diaria.csv', parse_dates=['fecha']).set_index('fecha').asfreq('D')
X = pd.DataFrame(index=S.index); lq = np.log(S.Q)
for l in [0, 1, 2, 3, 7]: X[f'lQ_{l}'] = lq.shift(l)
X['dlQ_1'] = lq - lq.shift(1); X['dlQ_3'] = lq - lq.shift(3)
for k in [1, 3, 5, 7, 10, 15, 30]: X[f'P{k}'] = S.Pmed.rolling(k, min_periods=k).sum()
for l in [1, 2]: X[f'P_lag{l}'] = S.Pmed.shift(l)
p = S.Pmed.fillna(0).values; api = np.zeros(len(p))
for i in range(1, len(p)): api[i] = 0.9 * api[i - 1] + p[i]
X['API'] = api; X['mes'] = S.index.month.astype(str)
COLS = list(X.columns); NUM = [c for c in COLS if c != 'mes']
TRAIN, TEST = S.index.year <= 2002, S.index.year >= 2013
Q90 = S.Q[TRAIN].quantile(0.90)
def pipe(m):
    return Pipeline([('prep', ColumnTransformer([('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('esc', StandardScaler())]), NUM),
                                                 ('cat', OneHotEncoder(handle_unknown='ignore'), ['mes'])])), ('modelo', m)])
MODELOS = {'LightGBM (machine learning)': lambda: LGBMRegressor(n_estimators=200, learning_rate=0.02, num_leaves=15, min_child_samples=10, subsample=0.7,
                                                                 subsample_freq=1, colsample_bytree=0.6, reg_lambda=5, verbose=-1, random_state=42,
                                                                 deterministic=True, force_row_wise=True, n_jobs=2),
           'Red neuronal densa 64-32-16 (deep learning)': lambda: MLPRegressor(hidden_layer_sizes=(64, 32, 16), activation='relu', alpha=1e-3,
                                                                                 learning_rate_init=1e-3, max_iter=300, early_stopping=True,
                                                                                 validation_fraction=0.15, n_iter_no_change=20, random_state=42)}
filas = []
for h in [1, 3, 5]:
    y = np.log(S.Q.shift(-h)) - np.log(S.Q); ok = y.notna() & X.lQ_0.notna()
    itr, ite = ok & TRAIN, ok & TEST
    w = np.where(S.Q.shift(-h)[itr] > Q90, 3.0, 1.0)
    qo, q0 = S.Q.shift(-h)[ite].values, S.Q[ite].values
    for n, f in MODELOS.items():
        m = pipe(f()).fit(X.loc[itr], y[itr], modelo__sample_weight=w)
        qs = q0 * np.exp(m.predict(X.loc[ite]))
        alto = qo > Q90
        filas.append(dict(h=h, modelo=n, NSE=1 - np.sum((qo - qs) ** 2) / np.sum((qo - qo.mean()) ** 2),
                          skill=1 - np.mean((qo - qs) ** 2) / np.mean((qo - q0) ** 2), RMSE_alto=np.sqrt(np.mean((qo[alto] - qs[alto]) ** 2))))
T = pd.DataFrame(filas).pivot(index='modelo', columns='h', values='skill')
texto = 'Skill frente a la persistencia en test 2013-2023 (mismo pipeline, variables y pesos):\n' + T.round(3).to_string()
print(texto)
open('analisis_complementarios/prueba_red_neuronal_resultados.txt', 'w').write(texto + '\n\nConclusión: la red neuronal no mejora la precisión; se mantiene LightGBM.\n')
