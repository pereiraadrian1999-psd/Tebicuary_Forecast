"""App Streamlit — Pronóstico de caudal a 1, 3 y 5 días y alerta de crecidas en Villa Florida (río Tebicuary).

Ejecutar:  streamlit run app.py
Entrada: CSV diario con columnas fecha, Pmed (mm, precipitación media areal de la cuenca) y Q (m³/s),
con al menos 30 días de historia antes de la fecha de emisión.
"""
import numpy as np
import pandas as pd
import joblib
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.set_page_config(page_title='Pronóstico Tebicuary · Villa Florida', layout='wide')
AZUL, NARANJA, VERDE, GRIS, VIOLETA = '#2a78d6', '#eb6834', '#1baf7a', '#8a8984', '#4a3aa7'
plt.rcParams.update({'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': '#e4e3df',
                     'grid.linewidth': 0.6, 'font.size': 9, 'legend.frameon': False})


# ----------------------------------------------------------------------------- funciones
@st.cache_resource
def cargar_modelo(path='model.pkl'):
    return joblib.load(path)


def construir_features(df, ventanas, api_k):
    """Idéntica a la función del notebook (sección 5)."""
    X = pd.DataFrame(index=df.index)
    lq = np.log(df['Q'])
    for l in [0, 1, 2, 3, 7]:
        X[f'lQ_{l}'] = lq.shift(l)
    X['dlQ_1'] = lq - lq.shift(1)
    X['dlQ_3'] = lq - lq.shift(3)
    for k in ventanas:
        X[f'P{k}'] = df['Pmed'].rolling(k, min_periods=k).sum()
    for l in [1, 2]:
        X[f'P_lag{l}'] = df['Pmed'].shift(l)
    p = df['Pmed'].fillna(0).values
    api = np.zeros(len(p))
    for i in range(1, len(p)):
        api[i] = api_k * api[i - 1] + p[i]
    X['API'] = api
    X['mes'] = df.index.month.astype(str)
    return X


def pronosticar(bundle, hist):
    """Pronóstico a 1, 3 y 5 días: valor central, intervalo de confianza del 90 % y percentil 75; probabilidad de crecida."""
    Xall = construir_features(hist, bundle['ventanas'], bundle['api_k'])
    X = Xall.iloc[[-1]][bundle['features']]
    q0 = hist['Q'].iloc[-1]
    filas = []
    for h, m in bundle['modelos'].items():
        c = bundle['cuantiles'][h]
        filas.append(dict(h=h, fecha=hist.index[-1] + pd.Timedelta(days=h),
                          central=float(q0 * np.exp(m.predict(X)[0])),
                          ic_inf=float(q0 * np.exp(c['p05'].predict(X)[0] - c['qhat'])),
                          ic_sup=float(q0 * np.exp(c['p95'].predict(X)[0] + c['qhat'])),
                          p75=float(q0 * np.exp(c['p75'].predict(X)[0]))))
    prob = {w: float(c['modelo'].predict_proba(X)[0, 1]) for w, c in bundle['alerta'].items()}
    return pd.DataFrame(filas).set_index('h'), prob, Xall.iloc[-1]


def fmt(x, d=0):
    return f'{x:,.{d}f}'.replace(',', ' ')


# ----------------------------------------------------------------------------- datos
bundle = cargar_modelo()
RS = bundle['resumen']; U = bundle['umbral_Q10_permanencia']; U_EST = bundle['umbral_estiaje']
PERM = {int(k): v for k, v in bundle['permanencia'].items()}; QMAX_VAL = RS['alcance']['max_test']

with st.sidebar:
    st.header('1. Datos de entrada')
    archivo = st.file_uploader('CSV diario: fecha, Pmed, Q', type='csv')
    df = pd.read_csv(archivo if archivo else 'datos_muestra.csv', parse_dates=['fecha']).set_index('fecha').asfreq('D')
    if archivo is None:
        st.caption('Usando datos_muestra.csv: crecida de mayo de 2019.')
    faltan = [c for c in ['Pmed', 'Q'] if c not in df.columns]
    if faltan:
        st.error(f'Faltan columnas: {faltan}'); st.stop()
    st.header('2. Fecha de emisión')
    fechas = [d for d in df.index[29:] if pd.notna(df['Q'].get(d))]
    defecto = pd.Timestamp('2019-05-07') if pd.Timestamp('2019-05-07') in fechas else fechas[-1]
    t0 = st.select_slider('Día t (último día con datos)', options=fechas, value=defecto, format_func=lambda d: d.strftime('%Y-%m-%d'))
    st.header('3. Escenario de lluvia')
    extra = st.slider('Lluvia adicional en el día t (mm)', 0, 150, 0, step=5,
                      help='Suma lluvia hipotética a la Pmed del día de emisión para ver la sensibilidad del pronóstico.')

hist = df.loc[:t0, ['Pmed', 'Q']].copy()
hist.iloc[-1, hist.columns.get_loc('Pmed')] = (hist['Pmed'].iloc[-1] if pd.notna(hist['Pmed'].iloc[-1]) else 0) + extra
pr, prob, xhoy = pronosticar(bundle, hist)
q0 = hist['Q'].iloc[-1]; q_ayer = hist['Q'].iloc[-2]
estiaje = q0 < U_EST

st.title('Pronóstico de caudal y alerta de crecidas — río Tebicuary en Villa Florida')
st.caption(f'Cuenca de {fmt(bundle["area_km2"])} km² · LightGBM entrenado con 1974–2002 y evaluado con 2013–2023 · '
           f'emisión: mañana siguiente al día {t0:%d/%m/%Y}, con la lluvia y el caudal medio de ese día')

tab1, tab2, tab3, tab4 = st.tabs(['Pronóstico', 'Datos y proceso', 'Modelo', 'Alcance y parámetros'])

# ----------------------------------------------------------------------------- pestaña 1
with tab1:
    c = st.columns(4)
    c[0].metric(f'Caudal hoy ({t0:%d/%m})', f'{fmt(q0)} m³/s', delta=f'{fmt(q0 - q_ayer)} vs ayer', delta_color='off')
    if estiaje:
        st.info(f'Caudal de estiaje (< {fmt(U_EST)} m³/s, superado más del 75 % del tiempo). Los estiajes tienen mayor variabilidad '
                'relativa y un régimen que cambió en los últimos años; están fuera del alcance del modelo y no se emite pronóstico.')
    else:
        for i, h in enumerate(pr.index):
            r = pr.loc[h]; obs = df['Q'].get(r.fecha)
            c[i + 1].metric(f'{r.fecha:%d/%m} (t+{h})', f'{fmt(r.central)} m³/s',
                            delta=(f'observado {fmt(obs)}' if obs is not None and pd.notna(obs) else None), delta_color='off')
            c[i + 1].caption(f'IC 90 %: {fmt(r.ic_inf)} – {fmt(r.ic_sup)} m³/s · P75: {fmt(r.p75)}')

        st.subheader(f'Crecidas: superación de {fmt(U)} m³/s (caudal de 10 % de permanencia)')
        p3, u3 = prob[3], bundle['alerta'][3]['umbral_prob']
        aviso = pr['central'].max() > U
        ca = st.columns(2)
        ca[0].metric('Aviso temprano (5 días)', 'ya superado' if q0 > U else ('SÍ' if aviso else 'no'),
                     delta=None if q0 > U else f'máximo pronosticado {fmt(pr["central"].max())} m³/s', delta_color='off')
        ca[1].metric('Probabilidad de superar en los próximos 3 días', 'ya superado' if q0 > U else f'{100 * p3:.0f} %',
                     delta=None if q0 > U else ('ALERTA' if p3 >= u3 else 'sin alerta'), delta_color='inverse' if p3 >= u3 else 'off')
        if q0 > U:
            st.error(f'El caudal ya supera {fmt(U)} m³/s.')
        elif p3 >= u3:
            st.error(f'ALERTA: probabilidad de {100 * p3:.0f} % de superar {fmt(U)} m³/s en los próximos 3 días.')
        elif aviso:
            st.warning(f'AVISO TEMPRANO: el pronóstico supera {fmt(U)} m³/s dentro de los próximos 5 días.')
        else:
            st.success('Sin aviso ni alerta de crecida en los próximos 5 días.')
        st.caption(f'Aviso temprano: algún pronóstico (1, 3 o 5 días) supera el umbral. Alerta: la probabilidad estimada por el clasificador supera {u3:.2f} '
                   '(valor de corte elegido en la validación). En 2013–2023 ambos detectaron 13 de 14 crecidas con menos de una falsa alarma por año.')
        avisos = []
        if (q0 / q_ayer > 1.03) or (pr['central'].iloc[-1] > 1.10 * q0):
            avisos.append('Río en ascenso: el valor central tiende a quedarse corto (~10 %) y a llegar con un día de retraso; considerar el percentil 75 o el límite superior del intervalo.')
        if pr['ic_sup'].max() > QMAX_VAL or q0 > QMAX_VAL:
            avisos.append(f'Caudales por encima de {fmt(QMAX_VAL)} m³/s: fuera del rango verificado en el test.')
        if extra:
            avisos.append(f'Incluye un escenario de {extra} mm de lluvia adicional en el día t.')
        for a in avisos:
            st.warning(a)

    fig, axs = plt.subplots(2, 1, figsize=(11, 5.2), sharex=True, gridspec_kw={'height_ratios': [1, 2.4]})
    v = df.loc[t0 - pd.Timedelta(days=25):t0 + pd.Timedelta(days=6)]
    axs[0].bar(v.index, v['Pmed'], color=VERDE, width=0.8)
    if extra:
        axs[0].bar([t0], [hist['Pmed'].iloc[-1]], color='#eda100', width=0.8, label='con escenario'); axs[0].legend()
    axs[0].invert_yaxis(); axs[0].set_ylabel('Pmed (mm)')
    axs[1].plot(v.loc[:t0].index, v.loc[:t0, 'Q'], color=AZUL, lw=2, label='Observado hasta hoy')
    fut = v.loc[t0 + pd.Timedelta(days=1):, 'Q'].dropna()
    if len(fut):
        axs[1].plot(fut.index, fut.values, color=AZUL, lw=1.2, ls=':', label='Observado después (verificación)')
    if not estiaje:
        fx = [t0] + list(pr.fecha)
        axs[1].fill_between(fx, [q0] + list(pr.ic_inf), [q0] + list(pr.ic_sup), color=NARANJA, alpha=0.18, lw=0, label='Intervalo de confianza 90 %')
        axs[1].plot(fx, [q0] + list(pr.central), 'o-', color=NARANJA, lw=1.8, ms=5, label='Pronóstico (valor central)')
        axs[1].plot(fx, [q0] + list(pr.p75), '--', color='#c0392b', lw=1.2, label='Percentil 75')
    axs[1].axhline(U, color=GRIS, lw=0.8, ls='--'); axs[1].text(v.index[0], U * 1.03, f'Q10 de permanencia = {fmt(U)} m³/s', color='#52514e', fontsize=8, ha='left')
    axs[1].axvline(t0, color='#52514e', lw=0.8)
    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    axs[1].set_ylabel('Caudal (m³/s)'); axs[1].legend(loc='upper left', fontsize=8, ncol=2)
    st.pyplot(fig)

    if not estiaje:
        tabla = pr.copy()
        tabla['fecha'] = tabla['fecha'].dt.strftime('%d/%m/%Y')
        tabla['observado'] = [df['Q'].get(d) for d in pr.fecha]
        ren = {'fecha': 'Fecha', 'central': 'Valor central', 'ic_inf': 'IC 90 % inferior', 'ic_sup': 'IC 90 % superior',
               'p75': 'Percentil 75', 'observado': 'Observado (si existe)'}
        st.dataframe(tabla.rename(columns=ren).rename_axis('Horizonte (días)').round(0), width='stretch')

# ----------------------------------------------------------------------------- pestaña 2
with tab2:
    st.subheader('Series del archivo cargado')
    fig, axs = plt.subplots(2, 1, figsize=(11, 4.6), sharex=True, gridspec_kw={'height_ratios': [1, 1.6]})
    axs[0].bar(df.index, df['Pmed'], color=VERDE, width=0.9); axs[0].set_ylabel('Pmed (mm/día)')
    axs[1].plot(df.index, df['Q'], color=AZUL, lw=1.2); axs[1].set_ylabel('Q (m³/s)')
    axs[1].axvline(t0, color='#52514e', lw=0.8); axs[1].axhline(U, color=GRIS, lw=0.8, ls='--'); axs[1].axhline(U_EST, color=GRIS, lw=0.8, ls=':')
    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
    st.pyplot(fig)
    st.caption(f'Línea discontinua: caudal de 10 % de permanencia ({fmt(U)} m³/s). Línea punteada: límite de estiaje ({fmt(U_EST)} m³/s).')
    c1, c2 = st.columns(2)
    with c1:
        st.subheader('Respuesta del caudal a la lluvia')
        st.caption('Correlación entre la lluvia de un día y la variación del caudal k días después (1974–2023).')
        cc = RS['corr_retardo']
        fig, ax = plt.subplots(figsize=(5.5, 3))
        ax.bar(range(len(cc)), cc, color=AZUL); ax.set_xlabel('Retardo (días)'); ax.set_ylabel('Correlación')
        st.pyplot(fig)
    with c2:
        st.subheader('Lluvia acumulada al día de emisión')
        acc = pd.Series({k: xhoy[k] for k in ['P1', 'P3', 'P5', 'P7', 'P10', 'P15', 'P30']})
        fig, ax = plt.subplots(figsize=(5.5, 3))
        ax.bar(acc.index, acc.values, color=VERDE); ax.set_ylabel('mm'); ax.set_xlabel('Ventana de acumulación (días)')
        st.pyplot(fig)
    st.subheader('Variables de entrada del modelo para el día t')
    desc = {'lQ_0': 'log caudal hoy', 'lQ_1': 'log caudal ayer', 'lQ_2': 'log caudal hace 2 días', 'lQ_3': 'log caudal hace 3 días',
            'lQ_7': 'log caudal hace 7 días', 'dlQ_1': 'tendencia 1 día (sube > 0)', 'dlQ_3': 'tendencia 3 días',
            'P1': 'lluvia del día (mm)', 'P3': 'lluvia 3 días (mm)', 'P5': 'lluvia 5 días (mm)', 'P7': 'lluvia 7 días (mm)',
            'P10': 'lluvia 10 días (mm)', 'P15': 'lluvia 15 días (mm)', 'P30': 'lluvia 30 días (mm)',
            'P_lag1': 'lluvia de ayer (mm)', 'P_lag2': 'lluvia de anteayer (mm)', 'API': 'índice de humedad antecedente', 'mes': 'mes'}
    st.dataframe(pd.DataFrame({'Variable': list(desc), 'Descripción': list(desc.values()),
                               'Valor': [str(xhoy[k]) if k == 'mes' else f'{float(xhoy[k]):.3f}' for k in desc]}), width='stretch', hide_index=True)

# ----------------------------------------------------------------------------- pestaña 3
with tab3:
    st.subheader('Cómo se calcula el pronóstico')
    st.markdown(
        '1. Lluvia media de la cuenca (Pmed): 8 pluviómetros ponderados por polígonos de Thiessen, recalculados cada día con las estaciones disponibles.\n'
        '2. Variables: caudal de hoy y de días anteriores, tendencia del caudal, lluvia acumulada de 1 a 30 días, humedad antecedente (API) y mes.\n'
        '3. Modelo: LightGBM (gradient boosting) que predice el cambio relativo del caudal; un modelo por horizonte (1, 3 y 5 días).\n'
        '4. Intervalo de confianza: regresión cuantílica (percentiles 5 y 95) recalibrada con datos recientes (conformal).\n'
        '5. Crecidas: aviso temprano a 5 días con la regresión y alerta a 3 días con un clasificador LightGBM que estima la probabilidad de superar el caudal de 10 % de permanencia.')
    m = pd.DataFrame(RS['metricas']).T
    tab_m = pd.DataFrame({'NSE modelo': m['NSE'], 'NSE persistencia': m['NSE_pers'], 'KGE': m['KGE'], 'Skill vs persistencia': m['Skill_pers'],
                          'RMSE caudal alto (m³/s)': m['RMSE_alto'], 'RMSE alto persistencia': m['RMSE_alto_pers']})
    tab_m.index = [f'{h} día{"s" if str(h) != "1" else ""}' for h in tab_m.index]
    st.subheader('Desempeño en el período de test (2013–2023)')
    st.dataframe(tab_m.round(3), width='stretch')
    st.caption('Persistencia: suponer que el caudal no cambia. Skill 0,5 = la mitad del error cuadrático de la persistencia.')
    c1, c2 = st.columns(2)
    with c1:
        st.subheader('Comparación de modelos')
        tc = pd.DataFrame(RS['comparacion']).T.astype(float)
        tc.columns = [f'h = {h}' for h in tc.columns]
        st.dataframe(tc.round(3), width='stretch')
        st.caption('Skill frente a la persistencia en test. Los modelos de boosting (XGBoost, LightGBM) superan a Ridge y a Random Forest.')
    with c2:
        st.subheader('Variables más influyentes (SHAP, h = 3)')
        sh = pd.Series(RS['shap']).sort_values()
        fig, ax = plt.subplots(figsize=(5.5, 4))
        ax.barh(sh.index, sh.values, color=[VERDE if k.startswith(('P', 'API')) else AZUL for k in sh.index])
        ax.set_xlabel('|SHAP| medio'); ax.set_title('Verde: lluvia · azul: caudal', fontsize=9, loc='left'); ax.grid(axis='y', visible=False)
        st.pyplot(fig)

# ----------------------------------------------------------------------------- pestaña 4
with tab4:
    st.subheader('Error del pronóstico por tramo de la curva de permanencia (test)')
    filas = {}
    for h, lst in RS['alcance']['error_por_tramo'].items():
        for r in lst:
            filas.setdefault(r['tramo'], {})[f'Error típico h={h} (%)'] = r['error_tipico_pct']
    st.dataframe(pd.DataFrame(filas).T.rename_axis('Caudal observado (m³/s)').round(1), width='stretch')
    st.markdown(f'- Alcance: caudales medios y altos (≥ {fmt(U_EST)} m³/s). Los estiajes no se pronostican: mayor variabilidad relativa y régimen cambiante.\n'
                f'- En las subidas el valor central se queda corto (~10 %) y llega con ~1 día de atraso; para alertar se usa la probabilidad de superación.\n'
                f'- No verificado por encima de {fmt(QMAX_VAL)} m³/s (máximo del período de test).')
    st.subheader('Desempeño como alerta (crecidas de 2013–2023)')
    ev = pd.DataFrame(RS['alerta']['por_evento'])
    ev = ev.assign(Ventana=ev.ventana.astype(str) + ' días', Detectadas=ev.detectados.astype(str) + ' de ' + ev.eventos.astype(str))
    ev = ev.rename(columns={'metodo': 'Método', 'anticipacion_media': 'Anticipación media (días)', 'falsas_por_ano': 'Falsas alarmas por año'})
    st.dataframe(ev[['Ventana', 'Método', 'Detectadas', 'Anticipación media (días)', 'Falsas alarmas por año']].round(2), width='stretch', hide_index=True)
    st.subheader('Cobertura del intervalo de confianza del 90 % (evaluación 2016–2023)')
    cob = pd.DataFrame(RS['cobertura'])
    cob = cob.assign(Horizonte=cob.h.astype(str) + ' días', Recalibrado=cob.recalibrada.map({True: 'Sí', False: 'No'}),
                     Cobertura=(100 * cob.cobertura).round(1).astype(str) + ' %', **{'Cobertura en caudal alto': (100 * cob.cobertura_altos).round(1).astype(str) + ' %'},
                     **{'Ancho medio (m³/s)': cob.ancho_medio.round(0)})
    st.dataframe(cob[['Horizonte', 'Recalibrado', 'Cobertura', 'Cobertura en caudal alto', 'Ancho medio (m³/s)']], width='stretch', hide_index=True)
    c1, c2 = st.columns(2)
    with c1:
        st.subheader('Pesos de Thiessen (red completa)')
        NOMBRES = {'Paraguari': 'Paraguarí', 'Coronel_Oviedo': 'Coronel Oviedo', 'San_Juan_Bautista': 'San Juan Bautista', 'Caazapa': 'Caazapá', 'Encarnacion': 'Encarnación'}
        w = pd.Series(bundle['pesos_thiessen']).rename(index=lambda k: NOMBRES.get(k, k)).sort_values()
        fig, ax = plt.subplots(figsize=(5.5, 3.2))
        ax.barh(w.index, 100 * w.values, color=AZUL); ax.set_xlabel('% del área de la cuenca'); ax.grid(axis='y', visible=False)
        st.pyplot(fig)
    with c2:
        st.subheader('Parámetros')
        par = {'Caudal de 10 % de permanencia (umbral de crecida)': f'{fmt(U)} m³/s', 'Límite de estiaje (75 % de permanencia)': f'{fmt(U_EST)} m³/s',
               'Curva de permanencia (caudal superado el k % del tiempo)': ', '.join(f'{k} %: {fmt(v)}' for k, v in sorted(PERM.items())),
               'Lluvia media anual de la cuenca': f'{fmt(RS["Pmed_anual"])} mm',
               'Entrenamiento / test': f'1974–2002 ({fmt(RS["n_train"])} días) / 2013–2023 ({fmt(RS["n_test"])} días)',
               'Objetivo del modelo': bundle['objetivo'], 'Índice de humedad antecedente': f'API(t) = {bundle["api_k"]}·API(t−1) + P(t)',
               'Hiperparámetros LightGBM': ', '.join(f'{k}={v}' for k, v in bundle['hiperparametros'].items())}
        st.markdown('\n'.join(f'- {k}: {v}' for k, v in par.items()))
