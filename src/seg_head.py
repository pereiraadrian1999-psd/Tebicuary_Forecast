# %% [markdown]
# # Pronóstico de caudales altos en el río Tebicuary — estación Villa Florida
#
# Diplomado en Machine Learning y Deep Learning Aplicado — FIUNA · Proyecto Final Integrador (M7)
#
# Objetivo: pronosticar el caudal diario en Villa Florida con 1, 3 y 5 días de anticipación, con intervalos de confianza, y alertar la superación del caudal de 10 % de permanencia (Q10 de la curva de permanencia = 823 m³/s), a partir del caudal observado y de la precipitación media areal antecedente de la cuenca.
#
# Machine learning y deep learning en este trabajo: el modelo final es de machine learning (gradient boosting, LightGBM), que es el estado del arte para datos tabulares. El deep learning se evalúa con una red neuronal profunda densa (perceptrón multicapa de tres capas ocultas) dentro del mismo pipeline y bajo las mismas condiciones; en este problema queda por debajo del boosting, por lo que no se adopta.
#
# Alcance: el pronóstico se emite para caudales medios y altos. Los estiajes (caudal superado más del 75 % del tiempo, < 112 m³/s) tienen mayor variabilidad relativa y un régimen que cambió en el período reciente; se deja constancia de ello y no se pronostican.
#
# Flujo del notebook:
# 1. Datos, control de calidad y precipitación media areal por Thiessen dinámico.
# 2. Análisis exploratorio, variables y partición temporal (entrenamiento 1974–2002, test 2013–2023).
# 3. Línea base (persistencia), ventanas de lluvia y comparación de modelos de ML y DL.
# 4. Optimización con validación cruzada temporal y modelos finales a 1, 3 y 5 días.
# 5. Evaluación: serie completa, alcance, extremos y desfase.
# 6. Intervalos de confianza (regresión cuantílica con recalibración conformal).
# 7. Alerta de crecidas: probabilidad de superar el caudal de 10 % de permanencia.
# 8. Explicabilidad (SHAP), retorno de la inversión, guardado del modelo y muestra de datos.
