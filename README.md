# Pronóstico de caudales y alerta de crecidas en el río Tebicuary — Villa Florida

Proyecto Final Integrador (M7) · Diplomado en Machine Learning y Deep Learning Aplicado · FIUNA 2026 · Ing. Jorge Adrián Pereira Oviedo

Repositorio: https://github.com/pereiraadrian1999-psd/Tebicuary_Forecast  
Video: https://studio.youtube.com/video/_cwuALhykE0/edit

## Problema

El río Tebicuary en Villa Florida drena 20 987 km² del centro-sur de Paraguay. Sus crecidas afectan la ruta PY01, zonas productivas y poblaciones ribereñas, y hoy se anticipan con la lectura diaria de la estación y criterio experto. Usuarios: gestores de riesgo (SEN, DINAC/DMH, municipios) y proyectistas de obras viales e hidráulicas.

## Objetivo

Pronosticar el caudal diario en Villa Florida a 1, 3 y 5 días, con intervalos de confianza, y alertar con anticipación la superación del caudal de 10 % de permanencia (Q10 de la curva de permanencia = 823 m³/s), a partir del caudal observado y de la lluvia media de la cuenca.

Métrica de éxito: skill frente a la persistencia, `1 − MSE_modelo / MSE_persistencia` (en un río lento, "mañana igual que hoy" ya da NSE ≈ 0,99), junto con NSE, KGE, RMSE en caudales altos y, para la alerta, crecidas detectadas, anticipación y falsas alarmas.

Machine learning y deep learning: se usa machine learning (LightGBM, gradient boosting), el estado del arte para datos tabulares. No se usa deep learning: una red neuronal densa en el mismo pipeline no mejoró la precisión (skill 0,47 frente a 0,54 a 3 días; `analisis_complementarios/prueba_red_neuronal.py`).

## Datos

| Fuente | Contenido | Período |
|---|---|---|
| DMH (DINAC) | Lluvia diaria de 8 estaciones: Paraguarí, Villarrica, Cnel. Oviedo, Quyquyho, Pilar, San Juan Bautista, Caazapá, Encarnación | 1974–2023 |
| Estación Villa Florida | Caudal diario (m³/s) | 1974–2023 (vacío 2003–2012) |
| Shapefile de cuenca | Cuenca de aporte a Villa Florida | — |

Preprocesamiento: valores `-1` a faltante (nunca 0); Caazapá como faltante en 1974–2016 porque su serie es idéntica a la de Quyquyho en ese período; lluvia media de la cuenca por Thiessen dinámico (pesos recalculados cada día con las estaciones disponibles, sin rellenar series).

`datos_muestra.csv`: 100 días (marzo–junio de 2019, crecida de mayo) con lluvia por estación, Pmed y caudal.

## Modelo

- Variables: log Q en t, t−1, t−2, t−3 y t−7; tendencia a 1 y 3 días; lluvia acumulada de 1, 3, 5, 7, 10, 15 y 30 días; lluvia rezagada; índice de humedad antecedente (API); mes.
- Objetivo: `log Q(t+h) − log Q(t)`; el caudal se reconstruye como `Q(t)·exp(ŷ)`.
- Pipeline: `ColumnTransformer` (imputación por mediana y `StandardScaler`; `OneHotEncoder` para el mes) + modelo. Peso 3 a los días con caudal objetivo mayor al Q10 de permanencia.
- Modelos comparados: persistencia, Ridge, Random Forest, XGBoost y LightGBM. Hiperparámetros con `RandomizedSearchCV` + `TimeSeriesSplit`.
- Validación temporal: entrenamiento 1974–2002, test 2013–2023.
- Intervalos de confianza: regresión cuantílica (P5–P95) con recalibración conformal (2013–2015), evaluada en 2016–2023.
- Crecidas: aviso temprano a 5 días (algún pronóstico supera el umbral) y alerta a 3 días (clasificador LightGBM: probabilidad de superar el umbral).
- Alcance: caudales medios y altos (≥ 112 m³/s, caudal de 75 % de permanencia). Los estiajes no se pronostican: mayor variabilidad relativa, mayor error y un régimen que cambió en el período reciente.

## Resultados (test 2013–2023)

| Horizonte | NSE modelo | NSE persistencia | KGE | Skill | RMSE caudal alto (m³/s) | IC 90 %: cobertura 2016–2023 |
|---|---|---|---|---|---|---|
| 1 día | 0,996 | 0,992 | 0,997 | 0,46 | 54 (persistencia 69) | 90 % |
| 3 días | 0,976 | 0,948 | 0,983 | 0,54 | 120 (persistencia 172) | 88 % |
| 5 días | 0,946 | 0,878 | 0,963 | 0,56 | 173 (persistencia 262) | 86 % |

| Modelo (skill) | h = 1 | h = 3 | h = 5 |
|---|---|---|---|
| Ridge | 0,40 | 0,41 | 0,41 |
| Random Forest | 0,41 | 0,54 | 0,54 |
| XGBoost | 0,46 | 0,54 | 0,56 |
| LightGBM | 0,46 | 0,54 | 0,56 |

Alerta de crecidas (superación de 823 m³/s, 14 crecidas en el test):

| Criterio | Crecidas alertadas | Anticipación media | Falsas alarmas por año |
|---|---|---|---|
| Aviso temprano a 5 días (regresión) | 13 de 14 | 3,1 días | 0,85 |
| Alerta a 3 días (clasificador) | 13 de 14 | 2,5 días | 0,94 |
| Extrapolar la tendencia (referencia, 3 días) | 13 de 14 | 2,3 días | 2,54 |

- Error típico en caudales medios y altos: ~2 % a 1 día, ~5 % a 3 días, ~10 % a 5 días. En las subidas el valor central se queda corto (~10 %) y llega con atraso (1 día a 1–3 días).
- La crecida no detectada (26/10/2015) fue un pico de un día causado por lluvia posterior a la emisión.
- SHAP: la tendencia del caudal y la lluvia de 7–10 días son las variables más influyentes.
- ROI a 5 años (supuestos de referencia, sección 17 del notebook): 0,6 (conservador), 4,9 (base) y 14,4 (optimista).

## Estructura

```
├── README.md
├── notebook_final.ipynb          # pipeline completo, ejecutado
├── model.pkl                     # modelos (h = 1, 3, 5), intervalos y clasificador de alerta
├── datos_muestra.csv             # 100 filas
├── app.py                        # app Streamlit
├── requirements.txt
└── data/raw/                     # datos crudos (lluvia, caudal, cuenca) para ejecutar el notebook

En el repositorio completo, además:
├── docs/                         # memoria de cálculo, presentación, guion del video/exposición y guía de estudio
├── figuras/                      # figuras generadas por el notebook
├── resultados/resultados.json    # métricas usadas en la memoria
├── src/                          # fuentes del notebook, diagramas y memoria
└── analisis_complementarios/     # análisis descartados (Yuty, CHIRPS, GFS, relleno, red neuronal)
```

## Ejecución

```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute notebook_final.ipynb   # requiere data/raw
streamlit run app.py                                             # usa model.pkl y datos_muestra.csv
```

La app recibe un CSV diario (`fecha, Pmed, Q`, al menos 30 días) y muestra el pronóstico a 1, 3 y 5 días con intervalo de confianza, el aviso y la alerta de crecida, las variables del día y las tablas de desempeño y alcance.

## Próximos pasos

1. Definir con la autoridad de gestión de riesgo los umbrales oficiales de alerta.
2. Medir caudal en el Tebicuary-mí y el Pirapó: explican la mayor parte de las crecidas y del atraso residual.
3. Recalibrar anualmente los intervalos y el valor de corte de la alerta.
4. Probar modelos secuenciales (LSTM) con más datos y lluvia subdiaria.
