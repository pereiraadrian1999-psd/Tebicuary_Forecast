import json
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
                                Image, PageBreak, KeepTogether, NextPageTemplate, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from PIL import Image as PILImage

FD = '/usr/share/fonts/truetype/dejavu/'
for n, f in [('DV', 'DejaVuSans.ttf'), ('DV-B', 'DejaVuSans-Bold.ttf'), ('DV-I', 'DejaVuSans-Oblique.ttf'), ('DV-BI', 'DejaVuSans-BoldOblique.ttf')]:
    pdfmetrics.registerFont(TTFont(n, FD + f))
addMapping('DV', 0, 0, 'DV'); addMapping('DV', 1, 0, 'DV-B'); addMapping('DV', 0, 1, 'DV-I'); addMapping('DV', 1, 1, 'DV-BI')

FIG = '/home/claude/work/final/figuras/'
FIG2 = '/home/claude/work/final/figs_diag/'
R = json.load(open('/home/claude/work/final/resultados/resultados.json'))
RC = json.load(open('/home/claude/work/proy/resultados/resultados.json'))   # análisis complementarios
OUT = '/mnt/user-data/outputs/Memoria_de_Calculo_Pronostico_Tebicuary_VillaFlorida.pdf'
AZUL = colors.HexColor('#1f5fa8'); GRIS = colors.HexColor('#52514e'); LINEA = colors.HexColor('#c9c8c3')
FONDO = colors.HexColor('#eef4fc'); NOTA = colors.HexColor('#fbf6e9')

def f(x, d=3):
    s = f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', ' ')
    return s.replace('-', '−')
pct = lambda x, d=1: f(100 * x, d) + ' %'

st = {
    'body': ParagraphStyle('body', fontName='DV', fontSize=9.5, leading=13.8, alignment=TA_JUSTIFY, spaceAfter=6),
    'h1': ParagraphStyle('h1', keepWithNext=1, fontName='DV-B', fontSize=14.5, leading=19, textColor=AZUL, spaceBefore=4, spaceAfter=9),
    'h2': ParagraphStyle('h2', keepWithNext=1, fontName='DV-B', fontSize=11.2, leading=14.5, textColor=AZUL, spaceBefore=9, spaceAfter=5),
    'h3': ParagraphStyle('h3', keepWithNext=1, fontName='DV-B', fontSize=9.8, leading=13, textColor=colors.HexColor('#333333'), spaceBefore=6, spaceAfter=3),
    'cap': ParagraphStyle('cap', fontName='DV-I', fontSize=8.2, leading=11, textColor=GRIS, alignment=TA_CENTER, spaceBefore=3, spaceAfter=10),
    'eq': ParagraphStyle('eq', fontName='DV-I', fontSize=10, leading=16, alignment=TA_CENTER, spaceBefore=4, spaceAfter=8),
    'cell': ParagraphStyle('cell', fontName='DV', fontSize=7.8, leading=9.8),
    'cellc': ParagraphStyle('cellc', fontName='DV', fontSize=7.8, leading=9.8, alignment=TA_CENTER),
    'head': ParagraphStyle('head', fontName='DV-B', fontSize=7.8, leading=9.8, textColor=colors.white, alignment=TA_CENTER),
    'bul': ParagraphStyle('bul', fontName='DV', fontSize=9.5, leading=13.8, alignment=TA_JUSTIFY, leftIndent=14, bulletIndent=4, spaceAfter=3),
    'nota': ParagraphStyle('nota', fontName='DV', fontSize=9, leading=13, alignment=TA_JUSTIFY),
    'toc1': ParagraphStyle('toc1', fontName='DV', fontSize=10, leading=15),
    'toc2': ParagraphStyle('toc2', fontName='DV', fontSize=8.8, leading=12.5, leftIndent=16, textColor=GRIS),
    'glos_t': ParagraphStyle('glos_t', fontName='DV-B', fontSize=8.3, leading=10.5),
    'glos_d': ParagraphStyle('glos_d', fontName='DV', fontSize=8.3, leading=10.8, alignment=TA_JUSTIFY),
}

class Doc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=2.3*cm, rightMargin=2.1*cm, topMargin=2.2*cm, bottomMargin=2*cm,
                         title='Memoria de cálculo — Pronóstico de caudales y alerta de crecidas en Villa Florida', author='Ing. Jorge Adrián Pereira Oviedo', **kw)
        fr = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id='f')
        self.addPageTemplates([PageTemplate('portada', [fr], onPage=self.portada), PageTemplate('normal', [fr], onPage=self.deco)])
    def portada(self, c, d):
        c.saveState(); c.setFillColor(AZUL); c.rect(0, A4[1] - 0.9*cm, A4[0], 0.9*cm, fill=1, stroke=0)
        c.rect(0, 0, A4[0], 0.5*cm, fill=1, stroke=0); c.restoreState()
    def deco(self, c, d):
        c.saveState(); c.setFont('DV', 7.5); c.setFillColor(GRIS)
        c.drawString(self.leftMargin, A4[1] - 1.4*cm, 'Pronóstico de caudales y alerta de crecidas — río Tebicuary en Villa Florida')
        c.drawRightString(A4[0] - self.rightMargin, A4[1] - 1.4*cm, 'Memoria de cálculo')
        c.setStrokeColor(LINEA); c.line(self.leftMargin, A4[1] - 1.55*cm, A4[0] - self.rightMargin, A4[1] - 1.55*cm)
        c.drawRightString(A4[0] - self.rightMargin, 1.2*cm, f'{d.page}')
        c.drawString(self.leftMargin, 1.2*cm, 'Diplomado ML/DL Aplicado · FIUNA 2026')
        c.restoreState()
    def afterFlowable(self, fl):
        if isinstance(fl, Paragraph) and fl.style.name in ('h1', 'h2'):
            lvl = 0 if fl.style.name == 'h1' else 1
            key = f'h{id(fl)}'
            self.canv.bookmarkPage(key); self.canv.addOutlineEntry(fl.getPlainText(), key, level=lvl, closed=False)
            self.notify('TOCEntry', (lvl, fl.getPlainText(), self.page, key))

S = []
def P(t, s='body'):
    if s in ('h1', 'h2'): S.append(CondPageBreak(8*cm if s == 'h2' else 9*cm))
    if s == 'h3': S.append(CondPageBreak(5*cm))
    S.append(Paragraph(t, st[s]))
def B(items):
    for t in items: S.append(Paragraph(t, st['bul'], bulletText='•'))
def NOTA_(titulo, texto):
    t = Table([[Paragraph(f'<font name="DV-B">{titulo}</font><br/>{texto}', st['nota'])]], colWidths=[16.4*cm])
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NOTA), ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#e2c98a')),
                           ('LEFTPADDING', (0, 0), (-1, -1), 8), ('RIGHTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    S.append(KeepTogether([Spacer(1, 3), t, Spacer(1, 8)]))
nfig = [0]; ntab = [0]
def FIGURA(fn, caption, width=15.5*cm, base=FIG):
    w, h = PILImage.open(base + fn).size
    nfig[0] += 1
    S.append(KeepTogether([Image(base + fn, width=width, height=width * h / w), Paragraph(f'Figura {nfig[0]}. {caption}', st['cap'])]))
    return nfig[0]
def TABLA(data, widths, caption):
    ntab[0] += 1
    rows = [[Paragraph(str(c), st['head']) for c in data[0]]]
    for r in data[1:]:
        rows.append([Paragraph(str(c), st['cell'] if j == 0 else st['cellc']) for j, c in enumerate(r)])
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), AZUL), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, FONDO]), ('LINEBELOW', (0, -1), (-1, -1), 0.6, AZUL),
                           ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    S.append(KeepTogether([Paragraph(f'Tabla {ntab[0]}. {caption}', st['cap']), t, Spacer(1, 10)]))
    return ntab[0]
import numpy as np
from reportlab.platypus import CondPageBreak

def TABLAT(data, widths, caption):
    """Tabla con todas las columnas alineadas a la izquierda (texto)."""
    ntab[0] += 1
    rows = [[Paragraph(str(c), st['head']) for c in data[0]]] + [[Paragraph(str(c), st['cell']) for c in r] for r in data[1:]]
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), AZUL), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                           ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, FONDO]), ('LINEBELOW', (0, -1), (-1, -1), 0.6, AZUL),
                           ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    S.append(KeepTogether([Paragraph(f'Tabla {ntab[0]}. {caption}', st['cap']), t, Spacer(1, 10)]))
    return ntab[0]

G = R['general']; MF = R['metricas_finales']; PER = R['persistencia']; FAL = R['faltantes']; AC = R['alcance']; AL = R['alerta']
HZ = ['1', '3', '5']
dia = lambda h: f'{h} día{"s" if str(h) != "1" else ""}'
CMP = {(c['modelo'], str(c['h'])): c for c in R['comparacion']}
EVT = {(e['ventana'], e['metodo']): e for e in AL['por_evento']}
cl3 = EVT[(3, 'Clasificador (probabilidad)')]; rc5 = EVT[(5, 'Regresión (valor central)')]; tp3 = EVT[(3, 'Persistencia de la tendencia')]
COB = {(str(c['h']), c['recalibrada']): c for c in R['cobertura']}
DOM = AC['metricas_dominio']; PERM = AC['umbrales_permanencia']
ERR = {h: {r['tramo']: r for r in AC['error_por_tramo'][h]} for h in HZ}
DLT = {'1': (0.464, 0.405), '3': (0.541, 0.474), '5': (0.559, 0.467)}   # prueba complementaria LightGBM vs red neuronal (skill)

# ============================================================ PORTADA
S.append(Spacer(1, 2.4*cm))
S.append(Paragraph('UNIVERSIDAD NACIONAL DE ASUNCIÓN<br/>Facultad de Ingeniería', ParagraphStyle('u', fontName='DV', fontSize=10, leading=14, alignment=TA_CENTER, textColor=GRIS)))
S.append(Paragraph('Diplomado en Machine Learning y Deep Learning Aplicado · Proyecto Final Integrador (M7)', ParagraphStyle('u2', fontName='DV', fontSize=9, leading=13, alignment=TA_CENTER, textColor=GRIS)))
S.append(Spacer(1, 1.8*cm))
S.append(Paragraph('MEMORIA DE CÁLCULO', ParagraphStyle('t0', fontName='DV-B', fontSize=12, leading=16, alignment=TA_CENTER, textColor=GRIS)))
S.append(Spacer(1, 0.4*cm))
S.append(Paragraph('Pronóstico de caudales a 1, 3 y 5 días y alerta de crecidas en el río Tebicuary, estación Villa Florida, mediante aprendizaje automático', ParagraphStyle('t1', fontName='DV-B', fontSize=19, leading=25, alignment=TA_CENTER, textColor=AZUL)))
S.append(Spacer(1, 0.7*cm))
S.append(Paragraph('Thiessen dinámico · Gradient boosting (LightGBM) · Validación temporal · Intervalos de confianza conformales · Alerta probabilística · SHAP', ParagraphStyle('t2', fontName='DV', fontSize=9.5, leading=14, alignment=TA_CENTER, textColor=GRIS)))
S.append(Spacer(1, 1.0*cm))
S.append(Image(FIG + 'mapa_thiessen.png', width=8.3*cm, height=8.3*cm))
S.append(Spacer(1, 0.9*cm))
S.append(Paragraph('Ing. Civil Jorge Adrián Pereira Oviedo', ParagraphStyle('a', fontName='DV', fontSize=10.5, leading=15, alignment=TA_CENTER)))
S.append(Spacer(1, 0.3*cm))
S.append(Paragraph('San Lorenzo, Paraguay · Octubre de 2026', ParagraphStyle('d', fontName='DV', fontSize=9.5, leading=13, alignment=TA_CENTER, textColor=GRIS)))
S.append(NextPageTemplate('normal')); S.append(PageBreak())
S.append(Paragraph('Contenido', ParagraphStyle('ct', fontName='DV-B', fontSize=14, leading=18, textColor=AZUL, spaceAfter=10)))
toc = TableOfContents(); toc.levelStyles = [st['toc1'], st['toc2']]; S.append(toc)
S.append(PageBreak())

# ============================================================ RESUMEN
P('Resumen ejecutivo', 'h1')
P(f'Se desarrolló un sistema de aprendizaje automático que pronostica el caudal diario del río Tebicuary en Villa Florida con 1, 3 y 5 días de anticipación, con intervalos de confianza, y que alerta la superación del caudal de 10 % de permanencia ({f(G["Q90"],0)} m³/s), umbral adoptado para las crecidas. Usa la información disponible cada mañana: el caudal medido y la lluvia media de la cuenca (20 987 km²), calculada con polígonos de Thiessen a partir de ocho pluviómetros.')
P(f'El modelo final es LightGBM (gradient boosting), entrenado con 1974–2002 y evaluado con 2013–2023, años que no participaron del ajuste. Superó a Ridge y a Random Forest, evaluados con el mismo pipeline, y empató con XGBoost. La referencia de comparación es la persistencia (suponer que el caudal no cambia), muy exigente en un río lento.')
TABLA([['Horizonte', 'NSE', 'Mejora sobre la persistencia (skill)', 'Error típico, caudales medios y altos', 'Error en caudal alto: modelo / persistencia (m³/s)', 'Intervalo 90 %: cobertura 2016–2023']] +
      [[dia(h), f(MF[h]['NSE']), pct(MF[h]['Skill_pers'], 0), f'~{f(np.median([ERR[h][k]["error_tipico_pct"] for k in list(ERR[h])[:6]]),0)} %',
        f'{f(MF[h]["RMSE_alto"],0)} / {f(MF[h]["RMSE_alto_pers"],0)}', pct(COB[(h, True)]['cobertura'], 0)] for h in HZ],
      [2*cm, 1.6*cm, 3*cm, 3.2*cm, 3.6*cm, 3*cm], 'Desempeño del pronóstico en el período de test (2013–2023).')
P(f'Para las crecidas se adoptó un esquema de dos niveles: aviso temprano a 5 días, cuando algún pronóstico supera el umbral, y alerta a 3 días, cuando la probabilidad estimada por un clasificador supera el valor de corte. Ambos alertaron {cl3["detectados"]} de las {cl3["eventos"]} crecidas de 2013–2023, con {f(rc5["anticipacion_media"],1)} y {f(cl3["anticipacion_media"],1)} días de anticipación media y {f(cl3["falsas_por_ano"],2)} falsas alarmas por año. La regla simple de extrapolar la tendencia detecta lo mismo con {f(tp3["falsas_por_ano"],1)} falsas alarmas por año.')
P(f'El pronóstico se limita a caudales medios y altos (≥ {f(PERM["75"],0)} m³/s, caudal de 75 % de permanencia). Los estiajes tienen mayor variabilidad relativa, mayor error y un régimen que cambió en el período reciente (el caudal mínimo anual disminuye {f(-AC["qmin7_sen"],1)} m³/s por año, p = {f(AC["qmin7_p"],3)}); se deja constancia y no se pronostican. En las subidas el valor central se queda corto (~10 %) y llega con ~1 día de atraso a 1–3 días: la causa es que la mayor parte de las crecidas llega de afluentes sin medición, no el algoritmo.')
P(f'Con supuestos de referencia, el retorno de la inversión a 5 años es {f(R["roi"]["escenarios"]["Conservador"]["ROI"],1)} (conservador), {f(R["roi"]["escenarios"]["Base"]["ROI"],1)} (base) y {f(R["roi"]["escenarios"]["Optimista"]["ROI"],1)} (optimista). El sistema se entrega como notebook reproducible, modelo serializado y aplicación Streamlit.')

# ============================================================ 1 INTRODUCCIÓN
S.append(PageBreak())
P('1. Introducción', 'h1')
P('1.1 Problema', 'h2')
P('El río Tebicuary drena el centro-sur de la Región Oriental del Paraguay. En Villa Florida cruza la ruta PY01 y atraviesa áreas productivas y poblaciones ribereñas expuestas a crecidas. Saber con algunos días de anticipación si el caudal va a subir, y cuánto, permite activar medidas preventivas; hoy esa estimación se apoya en la lectura diaria de la estación y en el criterio del operador. Usuarios previstos: organismos de gestión de riesgo (SEN, DINAC/DMH, municipios), operadores viales y proyectistas de obras hidráulicas.')
P('1.2 Objetivos', 'h2')
P('Objetivo general: pronosticar el caudal diario en Villa Florida a 1, 3 y 5 días, con intervalos de confianza, y alertar con anticipación la superación del caudal de 10 % de permanencia, a partir del caudal observado y de la lluvia media de la cuenca.')
B(['Calcular la precipitación media areal diaria por Thiessen, tratando correctamente los faltantes y los errores de las series.',
   'Determinar qué ventana de lluvia acumulada aporta más información y en qué horizonte la lluvia agrega valor sobre la persistencia.',
   'Comparar modelos de machine learning bajo un mismo pipeline reproducible y con validación temporal.',
   'Estimar intervalos de confianza calibrados y un criterio de alerta de crecidas evaluado por evento.',
   'Delimitar el alcance del pronóstico, explicar el modelo con SHAP y estimar el retorno de la inversión.',
   'Dejar un prototipo operable: modelo serializado y aplicación Streamlit.'])
P('1.3 Machine learning y deep learning en este trabajo', 'h2')
P('El machine learning (ML) agrupa los métodos que aprenden una relación entre entradas y salidas a partir de ejemplos. El deep learning (DL) es una rama del ML basada en redes neuronales de varias capas, que aprenden representaciones intermedias de los datos; brilla con grandes volúmenes de datos no estructurados (imágenes, texto, señales largas).')
P('En este problema los datos son tabulares: una fila por día con unas 18 variables (caudales recientes, lluvia acumulada, mes) y unos 7 400 días de entrenamiento, con pocas crecidas. Para ese tipo de datos los modelos de árboles con boosting son el estado del arte, y las redes neuronales necesitan muchos más datos para aprender las mismas relaciones. Por eso el trabajo usa machine learning: Ridge (lineal), Random Forest, XGBoost y LightGBM; LightGBM es el modelo final del pronóstico, de los intervalos de confianza y de la alerta.')
P(f'No se usa deep learning. Se verificó con una prueba complementaria: una red neuronal densa de tres capas ocultas (64, 32 y 16 neuronas), en el mismo Pipeline, con las mismas variables y pesos, no mejoró la precisión (skill {f(DLT["3"][1],2)} frente a {f(DLT["3"][0],2)} de LightGBM a 3 días, y {f(DLT["5"][1],2)} frente a {f(DLT["5"][0],2)} a 5 días). El deep learning queda como línea futura (redes recurrentes LSTM) cuando se disponga de más datos y de lluvia subdiaria.')
NOTA_('Criterio de éxito', 'Un NSE alto no alcanza: en un río lento, suponer que mañana el caudal será igual que hoy ya da NSE ≈ 0,99. El modelo aporta valor solo si supera claramente a esa persistencia, por eso la métrica central es el skill frente a la persistencia. Para la alerta, el criterio es detectar las crecidas con anticipación y pocas falsas alarmas.')

# ============================================================ 2 DATOS
P('2. Área de estudio y datos', 'h1')
P('2.1 Cuenca y estaciones', 'h2')
P(f'La cuenca de aporte a Villa Florida se obtuvo del shapefile de subcuencas, disuelto en un único polígono y proyectado a UTM 21S (EPSG:32721): {f(G["area_km2"],0)} km². Se usaron las ocho estaciones pluviométricas con registro diario 1974–2023 (DMH): cuatro dentro de la cuenca y cuatro en su entorno.')
FIGURA('mapa_thiessen.png', 'Cuenca del Tebicuary hasta Villa Florida, estaciones pluviométricas y polígonos de Thiessen con la red completa. Coordenadas UTM 21S (km); norte hacia arriba.', 12*cm)
PW = G['pesos']
TABLA([['Estación', 'Latitud', 'Longitud', 'Ubicación', 'Faltantes (%)', 'Peso Thiessen'],
       ['Caazapá*', '−26,175', '−56,355', 'Dentro', '2,7', pct(PW['Caazapa'])],
       ['Quyquyho', '−26,217', '−56,983', 'Dentro', '2,5', pct(PW['Quyquyho'])],
       ['Villarrica', '−25,754', '−56,438', 'Dentro', '0,7', pct(PW['Villarrica'])],
       ['San Juan Bautista', '−26,670', '−57,134', 'Fuera (4,6 km)', '2,3', pct(PW['San_Juan_Bautista'])],
       ['Coronel Oviedo', '−25,484', '−56,378', 'Dentro', '30,3', pct(PW['Coronel_Oviedo'])],
       ['Encarnación', '−27,226', '−55,837', 'Fuera (38 km)', '1,5', pct(PW['Encarnacion'])],
       ['Paraguarí', '−25,627', '−57,146', 'Fuera (7,4 km)', '40,7', pct(PW['Paraguari'])],
       ['Pilar', '−26,881', '−58,318', 'Fuera (122 km)', '1,3', pct(PW['Pilar'])]],
      [3.4*cm, 2*cm, 2*cm, 3*cm, 2.6*cm, 2.6*cm], 'Estaciones pluviométricas, faltantes 1974–2023 en las series entregadas y peso de Thiessen con la red completa. (*) Idéntica a Quyquyho en 1974–2016 (sección 2.3).')
P('2.2 Caudales', 'h2')
P('La serie de caudal diario de Villa Florida cubre 1974–2023 con 38,6 % de faltantes, concentrados en un vacío continuo entre 2003 y 2012. El caudal medio es 341 m³/s, la mediana 233 m³/s y el máximo registrado 2 836 m³/s (16/10/1996). El vacío define una partición natural: entrenamiento 1974–2002 y test 2013–2023.')
FIGURA('series.png', 'Precipitación media areal mensual y caudal diario en Villa Florida. Sombreado: períodos de entrenamiento y test.')
P('2.3 Control de calidad', 'h2')
B(['El código −1 significa "sin dato". Se convirtió en faltante; en ningún cálculo se tomó como 0 mm. Tomarlo como cero habría subestimado la lluvia media anual de la cuenca de ' + f(FAL['Pmed_anual_A'], 0) + ' a ' + f(FAL['Pmed_anual_B'], 0) + ' mm.',
   'San Juan Bautista tiene un bloque de fechas duplicadas (1 al 10 de enero de 2018) con valores idénticos; se conservó la primera ocurrencia.',
   'Las series de Quyquyho y Caazapá son idénticas día a día entre 1974 y 2016 (15 276 días con dato en ambas, incluidos todos los días de lluvia); desde 2017 se separan. Usarlas así cuenta dos veces la misma lluvia, con 58 % del peso de la cuenca sobre un solo registro. Se trató Caazapá como faltante en 1974–2016 (su área se redistribuye entre las vecinas).',
   'No se rellenaron series con estaciones vecinas: el relleno suaviza los extremos y, ajustado con toda la serie, filtra información del test.'])
TABLA([['Tratamiento de la duplicación', 'P media anual (mm)', 'Skill h = 1', 'Skill h = 3', 'Skill h = 5'],
       ['Series tal como están', '1 641', '0,450 ± 0,004', '0,545 ± 0,002', '0,553 ± 0,001'],
       ['Quyquyho como faltante 1974–2016', '1 643', '0,458 ± 0,005', '0,550 ± 0,003', '0,558 ± 0,004'],
       ['Caazapá como faltante 1974–2016 (adoptado)', '1 668', '0,462 ± 0,003', '0,552 ± 0,002', '0,560 ± 0,002']],
      [6*cm, 2.8*cm, 2.5*cm, 2.5*cm, 2.5*cm], 'Sensibilidad a la duplicación Quyquyho–Caazapá (test 2013–2023; media ± desvío de 3 semillas; análisis complementario).')
FIGURA('disponibilidad.png', 'Disponibilidad anual de datos por estación (fracción de días con dato), con Caazapá como faltante en 1974–2016.')

# ============================================================ 3 METODOLOGÍA
P('3. Metodología', 'h1')
P('El diagrama resume el recorrido completo del cálculo. Todo se implementó en Python (pandas, scikit-learn, LightGBM, XGBoost, SHAP) en un notebook que se ejecuta de principio a fin.')
FIGURA('flujo_metodologico.png', 'Diagrama de flujo de la metodología.', 10.5*cm, base=FIG2)
P('3.1 Precipitación media areal: Thiessen dinámico', 'h2')
P('El método de Thiessen asigna a cada estación el área de la cuenca más cercana a ella; la lluvia media es el promedio ponderado por esas áreas. Como muchos días falta alguna estación, los polígonos se recalculan cada día solo con las estaciones que midieron, de modo que los pesos siempre suman 1:')
P('P<sub>med</sub>(t) = Σ<sub>i ∈ D(t)</sub> w<sub>i</sub><super>D(t)</super> · P<sub>i</sub>(t)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;w<sub>i</sub><super>D(t)</super> = A<sub>i</sub><super>D(t)</super> / A<sub>cuenca</sub>', 'eq')
P(f'D(t) es el conjunto de estaciones con dato el día t. En 1974–2023 aparecen {G["combinaciones"]} combinaciones distintas; los pesos de cada una se calculan una vez y se reutilizan. La lluvia media anual resultante es {f(G["Pmed_anual"],0)} mm y el coeficiente de escorrentía 0,31, valor físicamente consistente para la cuenca.')
FIGURA('thiessen_dinamico.png', 'Thiessen dinámico: red completa, sin Paraguarí ni Coronel Oviedo, y sin Caazapá. Las cruces son estaciones sin dato ese día.', 16.4*cm)
P('3.2 Tiempo de respuesta y variables', 'h2')
cr = G['corr_retardo']
P(f'La correlación entre la lluvia de un día y la variación del caudal k días después es máxima al día siguiente ({f(cr[1])}) y se mantiene por encima de 0,15 hasta el día 5: la cuenca responde a lo largo de una semana. Por eso el tiempo de respuesta no se impone con una fórmula, sino que el modelo lo aprende de varias ventanas de lluvia acumulada.')
FIGURA('correlacion_retardo.png', 'Correlación entre la lluvia media areal del día t y la variación de log Q en t + k.', 10.5*cm)
TV = TABLA([['Grupo', 'Variables', 'Descripción'],
            ['Caudal', 'lQ_0, lQ_1, lQ_2, lQ_3, lQ_7', 'log Q en t, t−1, t−2, t−3 y t−7'],
            ['Tendencia', 'dlQ_1, dlQ_3', 'log Q(t) − log Q(t−1) y log Q(t) − log Q(t−3)'],
            ['Lluvia acumulada', 'P1, P3, P5, P7, P10, P15, P30', 'Suma de P<sub>med</sub> en los últimos k días (mm)'],
            ['Lluvia rezagada', 'P_lag1, P_lag2', 'P<sub>med</sub> en t−1 y t−2'],
            ['Humedad antecedente', 'API', 'API(t) = 0,9 · API(t−1) + P<sub>med</sub>(t)'],
            ['Estacionalidad', 'mes', 'Categórica, codificada One-Hot']],
           [3.2*cm, 5.3*cm, 7.9*cm], 'Variables predictoras (18 columnas), todas disponibles al emitir el pronóstico la mañana siguiente al día t.')
P('La variable objetivo es el cambio logarítmico del caudal, que expresa el cambio relativo y permite generalizar a caudales fuera del rango de entrenamiento:')
P('y = log Q(t+h) − log Q(t)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Q<sub>pron</sub>(t+h) = Q(t) · exp(ŷ)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;h = 1, 3, 5 días', 'eq')
P(f'Entrenamiento 1974–2002 ({f(G["n_train"],0)} días con dato a h = 3) y test 2013–2023 ({f(G["n_test"],0)} días). Los días cuyo caudal objetivo supera el caudal de 10 % de permanencia ({f(G["Q90"],0)} m³/s) reciben peso 3 en el ajuste, para priorizar las crecidas.')
P('3.3 Modelos', 'h2')
P('Ridge es una regresión lineal con penalización de los coeficientes. Un árbol de decisión hace preguntas sucesivas sobre las variables y entrega un valor en cada hoja; Random Forest promedia cientos de árboles entrenados en paralelo. El gradient boosting (XGBoost, LightGBM) entrena los árboles en serie: cada árbol corrige el error que dejaron los anteriores, con un factor pequeño (tasa de aprendizaje).')
FIGURA('arbol_boosting.png', 'a) Esquema de un árbol de decisión (valores ilustrativos). b) Boosting: cada árbol corrige el error residual de los anteriores.', 15.5*cm, base=FIG2)
P('3.4 Pipeline y validación temporal', 'h2')
P('Todos los modelos se envuelven en un Pipeline de scikit-learn: un ColumnTransformer imputa con la mediana y estandariza las variables numéricas y codifica el mes con One-Hot; luego actúa el modelo. El Pipeline se ajusta solo con el entrenamiento y se aplica idéntico en test y en la aplicación, lo que evita fugas de información.')
FIGURA('pipeline.png', 'Pipeline de scikit-learn usado por todos los modelos.', 15.5*cm, base=FIG2)
P('Los hiperparámetros de LightGBM se eligieron con RandomizedSearchCV (15 combinaciones) y TimeSeriesSplit (4 bloques) dentro del entrenamiento: cada bloque de validación es posterior a su bloque de ajuste, sin mezclar días al azar.')
P('3.5 Métricas', 'h2')
P('NSE = 1 − Σ(Q<sub>obs</sub> − Q<sub>pron</sub>)<super>2</super> / Σ(Q<sub>obs</sub> − Q̄<sub>obs</sub>)<super>2</super>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Skill = 1 − MSE<sub>modelo</sub> / MSE<sub>persistencia</sub>', 'eq')
TABLAT([['Métrica', 'Valor perfecto', 'Cómo leerla'],
        ['NSE', '1', '0 = tan bueno como usar siempre el caudal medio.'],
        ['KGE', '1', 'Combina correlación, sesgo y variabilidad.'],
        ['Skill vs persistencia', '1', '0 = igual que la persistencia; 0,5 = la mitad del error cuadrático.'],
        ['RMSE caudal alto', '0 m³/s', 'Error típico en los días con caudal mayor al de 10 % de permanencia.'],
        ['Error típico (%)', '0 %', 'Mediana del error absoluto relativo; se calcula por tramo de la curva de permanencia.'],
        ['Cobertura', '90 %', 'Proporción de observaciones dentro del intervalo del 90 %.'],
        ['Crecidas alertadas, anticipación, falsas alarmas', '—', 'Evaluación por evento de la alerta (sección 3.7).']],
       [4.2*cm, 2.4*cm, 9.8*cm], 'Métricas usadas.')
P('3.6 Intervalos de confianza', 'h2')
P('La regresión cuantílica entrena el modelo para estimar un percentil en lugar del valor medio: un LightGBM estima el percentil 5 y otro el 95 del cambio de caudal, y entre ambos queda el intervalo del 90 %. Como el período reciente es más variable que el de entrenamiento, el intervalo se recalibra con los errores de 2013–2015 (recalibración conformal: se ensancha lo justo para contener el 90 % de las observaciones de ese período) y se evalúa en 2016–2023, años no usados en ninguna etapa del ajuste. También se estima el percentil 75, útil como valor conservador en las subidas.')
FIGURA('concepto_bandas.png', 'Esquema: pronóstico con intervalo de confianza en lugar de un único valor.', 10.5*cm, base=FIG2)
P('3.7 Alerta de crecidas', 'h2')
P('Para alertar no hace falta acertar el caudal de un día exacto: alcanza con saber si el caudal superará el umbral en los próximos días. Se evaluaron, solo en días con el río por debajo del umbral, cuatro criterios: la regresión (algún pronóstico dentro de la ventana supera el umbral), su percentil 75, un clasificador LightGBM que estima directamente la probabilidad de superación (con el mismo Pipeline y variables; el valor de corte de probabilidad se elige con predicciones fuera de muestra dentro del entrenamiento) y, como referencia, la extrapolación de la tendencia del último día.')
P('La evaluación es por evento: cada cruce ascendente del umbral en 2013–2023, con al menos 5 días previos por debajo, es una crecida; se registra si hubo alerta en los días anteriores dentro de la ventana y con cuánta anticipación. Una falsa alarma es un episodio de alerta (días seguidos) sin superación en la ventana siguiente.')
P('3.8 Explicabilidad', 'h2')
P('SHAP reparte cada pronóstico entre las variables, indicando cuánto sumó o restó cada una respecto del valor medio; el promedio del valor absoluto mide la importancia global de cada variable.')

# ============================================================ 4 RESULTADOS
P('4. Resultados', 'h1')
P('4.1 Persistencia y ventanas de lluvia', 'h2')
TABLA([['Horizonte', 'NSE', 'KGE', 'RMSE (m³/s)', 'RMSE caudal alto (m³/s)']] +
      [[dia(h), f(PER[h]['NSE']), f(PER[h]['KGE']), f(PER[h]['RMSE'], 1), f(PER[h]['RMSE_alto'], 1)] for h in HZ],
      [3*cm, 2.5*cm, 2.5*cm, 3*cm, 3.8*cm], 'Desempeño de la persistencia en test (2013–2023).')
P('La persistencia es muy exigente hasta 3 días y pierde capacidad a 5 días; el error en caudales altos crece más rápido que el global: es en las crecidas donde un modelo puede aportar más.')
FIGURA('ablacion_ventanas.png', 'Skill frente a la persistencia en test según las variables de lluvia usadas y el horizonte.', 12.5*cm)
GA = R['ganancia']; AS = R['ablacion_skill']
B([f'Solo con caudal el modelo ya supera a la persistencia (skill {f(min(AS["Q"].values()),2)}–{f(max(AS["Q"].values()),2)}): aprende la recesión.',
   f'La lluvia agrega {f(GA["Q+todas"]["1"],2)}, {f(GA["Q+todas"]["3"],2)} y {f(GA["Q+todas"]["5"],2)} de skill a 1, 3 y 5 días: su aporte crece con el horizonte.',
   'Las ventanas individuales más informativas son las de 7 y 10 días, coherentes con el tiempo de respuesta. Combinar todas da el mejor resultado; el modelo final las usa todas.'])
P('4.2 Comparación de modelos', 'h2')
MOD = ['Ridge', 'Random Forest', 'XGBoost', 'LightGBM']
TABLA([['Modelo', 'Skill h = 1', 'Skill h = 3', 'Skill h = 5', 'NSE h = 3', 'KGE h = 3', 'RMSE caudal alto h = 3 (m³/s)']] +
      [[m] + [f(CMP[(m, h)]['Skill_pers']) for h in HZ] + [f(CMP[(m, '3')]['NSE']), f(CMP[(m, '3')]['KGE']), f(CMP[(m, '3')]['RMSE_alto'], 1)] for m in MOD],
      [4.2*cm, 1.9*cm, 1.9*cm, 1.9*cm, 1.9*cm, 1.9*cm, 2.7*cm], 'Comparación de modelos en test con el mismo Pipeline, variables y pesos.')
FIGURA('comparacion_modelos.png', 'Skill frente a la persistencia de los modelos comparados.', 13*cm)
P('XGBoost y LightGBM quedan prácticamente empatados y superan a Ridge y a Random Forest en los tres horizontes. Se adoptó LightGBM por su desempeño y menor costo de entrenamiento. Ponderar los caudales altos mejora el KGE y el error en crecidas sin penalizar el desempeño global.')
OP = R['optimizacion']; MJ = OP['mejores']
P(f'La optimización eligió {MJ["n_estimators"]} árboles, tasa de aprendizaje {f(MJ["learning_rate"],2)}, {MJ["num_leaves"]} hojas, mínimo {MJ["min_child_samples"]} días por hoja, submuestreo {f(MJ["subsample"],1)}, {pct(MJ["colsample_bytree"],0)} de variables por árbol y regularización L2 = {MJ["reg_lambda"]}: un modelo más regularizado que mejora el KGE y el error en caudales altos, con skill prácticamente igual. El límite lo impone la información disponible, no el ajuste del algoritmo.')
P('4.3 Modelos finales a 1, 3 y 5 días', 'h2')
TABLA([['Horizonte', 'NSE', 'NSE persistencia', 'KGE', 'Skill', 'RMSE (m³/s)', 'RMSE caudal alto (m³/s)', 'Idem persistencia', 'Sesgo caudal alto (%)']] +
      [[dia(h), f(MF[h]['NSE']), f(MF[h]['NSE_pers']), f(MF[h]['KGE']), f(MF[h]['Skill_pers']), f(MF[h]['RMSE'], 1), f(MF[h]['RMSE_alto'], 1), f(MF[h]['RMSE_alto_pers'], 1), f(MF[h]['PBIAS_alto'], 1)] for h in HZ],
      [1.8*cm, 1.4*cm, 1.9*cm, 1.4*cm, 1.4*cm, 1.8*cm, 2.3*cm, 2.1*cm, 2.3*cm], 'Modelos finales (LightGBM optimizado) en test 2013–2023.')
FIGURA('hidrograma_test.png', 'Caudal observado y pronosticado a 3 y 5 días en todo el período de test.')
FIGURA('dispersion.png', 'Caudal observado frente a pronosticado por horizonte (test).')
P('Las curvas de permanencia observada y pronosticada prácticamente se superponen: el modelo reproduce la frecuencia de caudales medios y altos y no "aplana" la serie. La dispersión crece con el horizonte y con el caudal; los desvíos mayores son subestimaciones en las puntas de crecida.')
FIGURA('curva_permanencia.png', 'Curva de permanencia de caudales observados y pronosticados a 3 días (escala logarítmica).', 11.5*cm)

P('4.4 Alcance del pronóstico y exclusión de los estiajes', 'h2')
filas = []
for k in list(ERR['1']):
    filas.append([k, f(ERR['3'][k]['dias'], 0)] + [f(ERR[h][k]['error_tipico_pct'], 1) for h in HZ] + [f(ERR[h][k]['dentro_20pct'], 0) for h in HZ])
TABLA([['Caudal observado, m³/s (permanencia)', 'Días', 'Error típico h=1 (%)', 'h=3 (%)', 'h=5 (%)', 'Días con error < ±20 %: h=1', 'h=3', 'h=5']] + filas,
      [4.3*cm, 1.3*cm, 2*cm, 1.4*cm, 1.4*cm, 2.6*cm, 1.4*cm, 1.4*cm], 'Error del pronóstico por tramo de la curva de permanencia (test 2013–2023).')
ES = AC['estado_h3']; VR = AC['variabilidad']
TABLA([['Estado del río (h = 3)', 'Días', 'Error típico (%)', 'Error < ±20 % (% de días)', 'Sesgo (%)']] +
      [[k, f(v['dias'], 0), f(v['error_tipico_pct'], 1), f(v['dentro_20pct'], 0), f(v['sesgo_pct'], 1)] for k, v in ES.items()],
      [6*cm, 1.6*cm, 2.6*cm, 3.4*cm, 2.2*cm], 'Error del pronóstico a 3 días según el estado del río.')
B([f'Para caudales mayores a {f(PERM["75"],0)} m³/s el error típico es de ~2 % a 1 día, ~5 % a 3 días y ~10 % a 5 días (mediana de los tramos); es mayor entre {f(PERM["75"],0)} y {f(PERM["50"],0)} m³/s. Por encima de {f(PERM["50"],0)} m³/s, a 3 días, más del 89 % de los días queda dentro de ±20 %.',
   f'Por debajo del caudal de 75 % de permanencia ({f(PERM["75"],0)} m³/s) el error típico sube a {f(ERR["3"][list(ERR["3"])[-1]]["error_tipico_pct"],0)} % a 3 días y {f(ERR["5"][list(ERR["5"])[-1]]["error_tipico_pct"],0)} % a 5 días.',
   'Con el río estable o bajando, y en caudal alto sin subida, el pronóstico es preciso. En las subidas el valor central se queda corto (−10 a −12 %): para alertar se usa la probabilidad de superación (sección 4.7).',
   f'El test no incluye caudales mayores a {f(AC["max_test"],0)} m³/s; por encima de ese valor el pronóstico no está verificado.'])
P(f'Los estiajes tienen mayor variabilidad relativa: el cambio diario |Δlog Q| tiene un desvío de {f(VR["Estiaje (< Q75 perm.)"]["std"],3)} en estiaje frente a {f(VR["Medios y altos (>= Q75 perm.)"]["std"],3)} en caudales medios y altos, y su percentil 90 es {f(VR["Estiaje (< Q75 perm.)"]["90%"],3)} frente a {f(VR["Medios y altos (>= Q75 perm.)"]["90%"],3)}. Además, su régimen cambió: el caudal mínimo anual de 7 días disminuye {f(-AC["qmin7_sen"],1)} m³/s por año (Kendall, p = {f(AC["qmin7_p"],3)}) sin que la lluvia anual tenga tendencia, y en 2020–2022 el registro llega a un piso de 0,87 m³/s. Las causas posibles (extracciones para riego, sequía 2020–2022, cambios en la curva altura–caudal en aguas bajas) no pueden separarse con los datos disponibles.')
FIGURA('estiaje_minimos.png', 'Caudal mínimo anual de 7 días en Villa Florida y tendencia de Sen.', 12.5*cm)
NOTA_('Decisión de alcance', f'El pronóstico se emite para caudales medios y altos (caudal del día ≥ {f(PERM["75"],0)} m³/s, superado el 75 % del tiempo). Los estiajes no se pronostican por su mayor variabilidad, mayor error y régimen cambiante; la aplicación informa esa condición y no muestra valores. Dentro de este alcance el skill es {f(DOM["1"]["Skill_pers"],2)}, {f(DOM["3"]["Skill_pers"],2)} y {f(DOM["5"]["Skill_pers"],2)} a 1, 3 y 5 días.')

P('4.5 Crecidas: picos y desfase', 'h2')
EV = R['eventos']
emod = np.mean([abs(e['error_pico_mod_pct']) for e in EV]); eper = np.mean([abs(e['error_pico_pers_pct']) for e in EV])
mejor = sum(abs(e['error_pico_mod_pct']) < abs(e['error_pico_pers_pct']) for e in EV)
P(f'En el test hubo {len(EV)} picos mayores al caudal de 10 % de permanencia. Con el pronóstico emitido 3 días antes, el modelo reduce el error en el día del pico en {mejor} de {len(EV)} eventos; el error absoluto medio en el pico es {f(emod,1)} % frente a {f(eper,1)} % de la persistencia. La mayoría de los errores son subestimaciones: el modelo reconoce la crecida, pero su máximo aparece 1–2 días después.')
FIGURA('error_picos.png', 'Error del pronóstico a 3 días en el día del pico, por evento.', 12.5*cm)
FIGURA('evento_pico.png', 'Crecida de 2014 (pico de 1 788 m³/s, el mayor del test): lluvia media areal, caudal observado, pronóstico a 3 días y persistencia.')
P('En mayo de 2014 la lluvia ya había caído (166 mm en los 10 días previos a la emisión) sobre un río que venía alto; en el entrenamiento esa situación produjo subidas moderadas (10 % en promedio en 3 días) y el modelo subestimó la de 2014 (33 %). En octubre de 2015, en cambio, la crecida respondió a lluvia caída después de la emisión, que no puede anticiparse con datos observados.')
DS = R['desfase']
P(f'Para medir el desfase, la serie pronosticada se desplaza L días y se busca el L con el que mejor coincide con la observada. La persistencia a 3 días tiene un atraso de {DS["Persistencia h=3"]} días; el modelo, de {DS["LightGBM h=1"]} día a 1 y 3 días y de {DS["LightGBM h=5"]} días a 5 días (la persistencia, 5).')
FIGURA('desfase.png', 'NSE al desplazar el pronóstico L días. El máximo indica el atraso efectivo.', 11.5*cm)
EXd = RC['experimentos_desfase']
P(f'En análisis complementarios se intentó reducir ese atraso (sección 4.9): lluvia por zonas, mayor peso a las subidas, lluvia futura perfecta (skill {f(EXd["4. Lluvia futura perfecta"]["Skill_pers"],3)} frente a {f(EXd["1. Base"]["Skill_pers"],3)} a 3 días), la estación aguas arriba Yuty, lluvia satelital y pronóstico meteorológico. Todas mejoran algo la magnitud y ninguna elimina el día de atraso: la mayor parte de las crecidas llega de afluentes sin medición (Tebicuary-mí, Pirapó), y esa información no está en los datos.')

P('4.6 Intervalos de confianza', 'h2')
TABLA([['Horizonte', 'Recalibrado', 'Cobertura total', 'Cobertura caudal alto', 'Ancho medio (m³/s)', 'Ancho medio relativo', 'Ancho medio caudal alto (m³/s)']] +
      [[dia(h), 'Sí' if r else 'No', pct(COB[(h, r)]['cobertura']), pct(COB[(h, r)]['cobertura_altos']), f(COB[(h, r)]['ancho_medio'], 0), pct(COB[(h, r)]['ancho_rel_medio'], 0), f(COB[(h, r)]['ancho_medio_altos'], 0)] for h in HZ for r in [False, True]],
      [1.8*cm, 2*cm, 2.2*cm, 2.6*cm, 2.4*cm, 2.4*cm, 3*cm], 'Cobertura del intervalo de confianza del 90 % en el período de evaluación 2016–2023.')
P(f'Sin recalibrar, el intervalo del 90 % contiene entre el {pct(COB[("5",False)]["cobertura"],0)} y el {pct(COB[("1",False)]["cobertura"],0)} de las observaciones: el período reciente es más variable que el de entrenamiento. Recalibrado con 2013–2015, contiene el {pct(COB[("1",True)]["cobertura"],0)}, {pct(COB[("3",True)]["cobertura"],0)} y {pct(COB[("5",True)]["cobertura"],0)} a 1, 3 y 5 días, cerca del valor nominal, y más del 96 % en caudales altos, donde resulta conservador. El precio es un intervalo más ancho, sobre todo a 5 días.')
FIGURA('intervalos_evento.png', 'Crecida de mayo de 2019 (período de evaluación): pronóstico a 1, 3 y 5 días con intervalo de confianza del 90 % recalibrado.', 16.4*cm)

P('4.7 Alerta de crecidas', 'h2')
filas = []
for w in [3, 5]:
    for m in ['Regresión (valor central)', 'Regresión (percentil 75)', 'Clasificador (probabilidad)', 'Persistencia de la tendencia']:
        e = EVT[(w, m)]
        filas.append([f'{w} días' if m.startswith('Regresión (valor') else '', m, f'{e["detectados"]} de {e["eventos"]}', f(e['anticipacion_media'], 1), f(e['falsas_alarmas'], 0), f(e['falsas_por_ano'], 2)])
TABLA([['Ventana', 'Criterio', 'Crecidas alertadas', 'Anticipación media (días)', 'Falsas alarmas', 'Falsas alarmas por año']] + filas,
      [1.8*cm, 5*cm, 2.4*cm, 2.6*cm, 2.2*cm, 2.4*cm], f'Desempeño como alerta de superación de {f(AL["umbral"],0)} m³/s en 2013–2023 (10,9 años).')
FIGURA('alerta_eventos.png', 'Crecidas alertadas con anticipación, anticipación media y falsas alarmas por año, según ventana y criterio.', 16.4*cm)
B([f'Todos los criterios basados en el modelo alertan {cl3["detectados"]} de las {cl3["eventos"]} crecidas. La no detectada (26/10/2015) fue un pico de un día causado por 46 mm caídos después de la emisión; además, entre el 18 y el 21 de octubre el registro muestra un valor constante de 810 m³/s, lo que sugiere un problema de registro.',
   f'Ventana de 3 días: el clasificador da la mayor anticipación ({f(cl3["anticipacion_media"],1)} días) con {f(cl3["falsas_por_ano"],2)} falsas alarmas por año. La extrapolación de la tendencia alerta lo mismo con {f(tp3["falsas_por_ano"],1)} falsas alarmas por año, tres veces más.',
   f'Ventana de 5 días: el clasificador, con el valor de corte elegido en el entrenamiento ({f(AL["umbral_prob"]["5"],2)}), genera {f(EVT[(5,"Clasificador (probabilidad)")]["falsas_por_ano"],1)} falsas alarmas por año; la regresión da {f(rc5["anticipacion_media"],1)} días de anticipación con {f(rc5["falsas_por_ano"],2)} por año.'])
CF = AL['confiabilidad_3']
TABLA([['Probabilidad pronosticada (media)', 'Frecuencia observada', 'Días']] + [[pct(r['prob_media'], 1), pct(r['frecuencia_obs'], 1), f(r['dias'], 0)] for r in CF],
      [5*cm, 4.5*cm, 3*cm], 'Confiabilidad del clasificador a 3 días (test): cuando dice p %, la crecida ocurre cerca del p % de las veces.')
FIGURA('alerta_probabilidad.png', 'Izquierda: confiabilidad de la probabilidad (la diagonal es la calibración perfecta). Derecha: probabilidad de superar 823 m³/s en 3 y 5 días durante la crecida de mayo de 2019.', 16.4*cm)
P(f'En la crecida de mayo de 2019 la probabilidad a 3 días superó el valor de corte ({f(AL["umbral_prob"]["3"],2)}) el 6 de mayo (0,58), tres días antes de que el caudal cruzara 823 m³/s (9 de mayo), y llegó a 0,97 el día anterior al cruce.')
NOTA_('Esquema operativo adoptado', f'Aviso temprano a 5 días: algún pronóstico de la regresión (1, 3 o 5 días) supera {f(AL["umbral"],0)} m³/s ({rc5["detectados"]} de {rc5["eventos"]} crecidas, {f(rc5["anticipacion_media"],1)} días de anticipación, {f(rc5["falsas_por_ano"],2)} falsas alarmas por año). Alerta a 3 días: la probabilidad del clasificador supera {f(AL["umbral_prob"]["3"],2)} ({cl3["detectados"]} de {cl3["eventos"]}, {f(cl3["anticipacion_media"],1)} días, {f(cl3["falsas_por_ano"],2)} por año). La magnitud se comunica con el pronóstico y su intervalo de confianza.')

P('4.8 Explicabilidad (SHAP)', 'h2')
FIGURA('shap_importancia.png', 'Importancia media absoluta de las variables (SHAP) en test, h = 3. Verde: lluvia; azul: caudal.', 10.5*cm)
P('La variable dominante es la tendencia del último día (dlQ_1): lo primero que el modelo evalúa es si el río sube o baja. Le siguen la lluvia de 10 y 7 días, coherentes con el tiempo de respuesta, y los caudales recientes. El gráfico de resumen muestra el sentido físico esperado: más lluvia acumulada y tendencia positiva empujan el pronóstico hacia arriba; caudales recientes altos lo empujan hacia abajo, porque después de un pico viene la recesión.')
FIGURA('shap_resumen.png', 'Resumen SHAP: cada punto es un día del test; color: valor de la variable (rojo alto, azul bajo); posición: efecto sobre el pronóstico.', 11*cm)

P('4.9 Análisis complementarios', 'h2')
P('Durante el desarrollo se evaluaron fuentes y variantes adicionales. Se documentan aquí sus resultados y la decisión tomada; el detalle está en el notebook de análisis complementarios del repositorio.')
YM = RC['yuty']['metricas']; CH = RC['chirps']['experimentos']; GF = RC['gfs']['experimentos']
TABLAT([['Análisis', 'Resultado', 'Decisión'],
        ['Estación Yuty (aguas arriba, desde 2016), corrección en dos etapas', f'+{f(YM["3"]["E3b Corrección con Yuty"]["Skill_pers"]-YM["3"]["E3a Corrección local sin Yuty"]["Skill_pers"],3)} de skill a 3 días y +{f(YM["5"]["E3b Corrección con Yuty"]["Skill_pers"]-YM["5"]["E3a Corrección local sin Yuty"]["Skill_pers"],3)} a 5 días (2019–2023); no reduce el atraso', 'No adoptado: registro de 7 años con 2 crecidas grandes. Recomendado a futuro'],
        ['Lluvia satelital CHIRPS (1981–2023)', f'+{f(CH["3"]["C. Estaciones + CHIRPS cuenca"]["Skill_pers"]-CH["3"]["A. Estaciones"]["Skill_pers"],3)} a 3 días y +{f(CH["5"]["C. Estaciones + CHIRPS cuenca"]["Skill_pers"]-CH["5"]["A. Estaciones"]["Skill_pers"],3)} a 5 días, dentro de la variación entre semillas', 'No adoptado'],
        ['Pronóstico meteorológico GFS (2016–2023)', f'Skill a 3 días {f(GF["3"]["A. Base"]["Skill_pers"],3)} → {f(GF["3"]["C2. Entrenado con lluvia futura degradada, con GFS"]["Skill_pers"],3)} (2019–2023); atraso igual', 'No adoptado: mejora moderada y dependencia operativa. Recomendado a futuro'],
        ['Lluvia por zonas (alta y baja)', f'Skill a 3 días {f(EXd["2. Lluvia por zonas"]["Skill_pers"],3)} frente a {f(EXd["1. Base"]["Skill_pers"],3)}; atraso igual', 'No adoptado: mejora marginal'],
        ['Red neuronal densa 64-32-16 (deep learning)', f'Skill a 3 días {f(DLT["3"][1],3)} frente a {f(DLT["3"][0],3)} de LightGBM', 'No adoptada: no mejora la precisión'],
        ['Relleno de series en cascada y pesos aprendidos por estación', 'Skill ~0,01 menor y sin mejora, respectivamente', 'No adoptado']],
       [5*cm, 6.6*cm, 4.8*cm], 'Análisis complementarios y decisiones.')

# ============================================================ 5 APP
P('5. Aplicación de pronóstico', 'h1')
P('El modelo se entrega como una aplicación Streamlit (app.py) que carga model.pkl y un CSV diario con fecha, lluvia media de la cuenca (Pmed) y caudal (Q), con al menos 30 días de historia. Se ejecuta con "streamlit run app.py". Muestra el pronóstico a 1, 3 y 5 días con su intervalo de confianza, el aviso temprano y la probabilidad de crecida a 3 días, un escenario de lluvia adicional, las variables del día, el desempeño del modelo y las tablas de alcance. Si el caudal del día está en estiaje, informa que está fuera del alcance y no emite pronóstico.')
FIGURA('app_pronostico.png', 'Aplicación, pestaña Pronóstico: emisión del 7 de mayo de 2019. Pronóstico a 1, 3 y 5 días con intervalo del 90 %, aviso temprano y probabilidad de 65 % de superar 823 m³/s en 3 días (alerta); el cruce ocurrió el 9 de mayo.', 16.4*cm)
FIGURA('app_grafico.png', 'Aplicación: hidrograma con el pronóstico, el intervalo de confianza y la verificación con lo observado.', 16.4*cm)
FIGURA('app_alcance.png', 'Aplicación, pestaña Alcance y parámetros: error por tramo de la curva de permanencia y desempeño como alerta.', 16.4*cm)

# ============================================================ 6 ROI
ROI = R['roi']; EE = ROI['escenarios']; KK = ['Conservador', 'Base', 'Optimista']
P('6. Retorno de la inversión', 'h1')
P(f'El beneficio proviene de las crecidas alertadas con anticipación (daños evitables: retiro de ganado y bienes de zonas ribereñas, cierre preventivo de accesos, preparación de la ruta PY01) y el costo, de la implementación, la operación anual y las falsas alarmas. Las frecuencias salen del test: {f(ROI["crecidas_alertadas_por_ano"],2)} crecidas alertadas y {f(ROI["falsas_alarmas_por_ano"],2)} falsas alarmas por año (alerta a 3 días). Los montos son supuestos de referencia, a reemplazar por los de la autoridad de gestión de riesgo; el cálculo está parametrizado en el notebook.')
P('ROI = (Beneficio − Costo) / Costo&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Beneficio = N · c · D&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Costo = I + N · (O + f · F)', 'eq')
P('N: años (5); c: crecidas alertadas por año; D: daño evitado por crecida; I: implementación; O: operación anual; f: falsas alarmas por año; F: costo por falsa alarma.')
TABLA([['Parámetro / resultado'] + KK] +
      [[k] + [f(EE[e][k], 0) for e in KK] for k in ['daño evitado por crecida (USD)', 'costo por falsa alarma (USD)', 'implementación (USD)', 'operación anual (USD)', 'beneficio 5 años (USD)', 'costo 5 años (USD)', 'beneficio neto (USD)']] +
      [['ROI'] + [f(EE[e]['ROI'], 2) for e in KK]],
      [6.4*cm, 3.3*cm, 3.3*cm, 3.3*cm], 'Retorno de la inversión a 5 años en tres escenarios (supuestos de referencia).')
P('El retorno es positivo en los tres escenarios porque el costo se concentra en la implementación y la operación usa los datos que la red ya produce. El resultado depende sobre todo del daño evitado por crecida, que debe estimarse con la autoridad competente.')

# ============================================================ 7 CONCLUSIONES
P('7. Conclusiones y recomendaciones', 'h1')
P('7.1 Conclusiones', 'h2')
B([f'Se puede pronosticar el caudal en Villa Florida a 1, 3 y 5 días: el modelo reduce el error cuadrático de la persistencia en {pct(MF["1"]["Skill_pers"],0)}, {pct(MF["3"]["Skill_pers"],0)} y {pct(MF["5"]["Skill_pers"],0)}, con error típico de ~2 %, ~5 % y ~10 % en caudales medios y altos.',
   f'Se identifican con anticipación las crecidas: {cl3["detectados"]} de {cl3["eventos"]} superaciones del caudal de 10 % de permanencia alertadas, con aviso a 5 días ({f(rc5["anticipacion_media"],1)} días de anticipación) y alerta a 3 días ({f(cl3["anticipacion_media"],1)} días), con menos de una falsa alarma por año.',
   f'Los intervalos de confianza del 90 %, recalibrados con datos recientes, cubren el {pct(COB[("1",True)]["cobertura"],0)}, {pct(COB[("3",True)]["cobertura"],0)} y {pct(COB[("5",True)]["cobertura"],0)} de las observaciones en un período independiente.',
   'El gradient boosting (LightGBM) es el modelo adecuado para estos datos tabulares: supera a Ridge y a Random Forest, y una red neuronal (deep learning) no mejoró la precisión.',
   'La lluvia acumulada de 7 a 10 días y la tendencia reciente del caudal son la información más útil, en coherencia con el tiempo de respuesta de la cuenca.',
   'Los estiajes no se pronostican: tienen mayor variabilidad relativa, mayor error y un régimen que cambió en el período reciente.',
   'El atraso de ~1 día en las subidas y la subestimación de los picos mayores se deben a información ausente (afluentes sin medición), no al algoritmo; para la alerta el atraso pesa poco.'])
P('7.2 Recomendaciones', 'h2')
B(['Definir con la autoridad de gestión de riesgo los umbrales oficiales y recalibrar con ellos el valor de corte de la alerta.',
   'Medir el caudal del Tebicuary-mí y el Pirapó cerca de su confluencia: es la información que más mejoraría el pronóstico de las crecidas.',
   'Mantener la estación Yuty e incorporarla cuando tenga 10 o más años de registro; evaluar la incorporación operativa del pronóstico meteorológico.',
   'Recalibrar cada año los intervalos de confianza y el valor de corte con los errores recientes.',
   'Revisar con la institución que administra la red las series duplicadas y los valores constantes de caudal.',
   'Probar redes recurrentes (LSTM) cuando se disponga de más datos y de lluvia subdiaria.'])

# ============================================================ ANEXOS
P('Anexo A. Glosario', 'h1')
GLOS = [('Persistencia', 'Pronóstico trivial: el caudal dentro de h días será igual al de hoy.'),
        ('Skill', '1 − error del modelo / error de la persistencia. 0 = igual; 0,5 = la mitad del error.'),
        ('NSE / KGE', 'Eficiencias del hidrograma; 1 es perfecto.'),
        ('Caudal de 10 % de permanencia', f'Caudal superado solo el 10 % del tiempo en el entrenamiento ({f(G["Q90"],0)} m³/s); umbral de crecida.'),
        ('Thiessen dinámico', 'Polígonos de Thiessen recalculados cada día con las estaciones que tienen dato.'),
        ('API', 'Índice de precipitación antecedente: resume la humedad de la cuenca.'),
        ('Gradient boosting', 'Árboles de decisión entrenados en serie, cada uno corrige el error de los anteriores (XGBoost, LightGBM).'),
        ('Pipeline / ColumnTransformer', 'Cadena de transformaciones y modelo que se aplica igual en entrenamiento, test y operación.'),
        ('Validación cruzada temporal', 'Ajuste con un tramo de años y validación con el siguiente, siempre hacia adelante.'),
        ('Regresión cuantílica', 'Modelo que estima un percentil en lugar del valor medio.'),
        ('Recalibración conformal', 'Ajuste del ancho del intervalo para que contenga la proporción prometida de observaciones.'),
        ('Clasificador', 'Modelo que estima la probabilidad de que ocurra un evento (aquí, superar el umbral en 3 días).'),
        ('Confiabilidad', 'Una probabilidad es confiable si los eventos pronosticados con p % ocurren cerca del p % de las veces.'),
        ('SHAP', 'Reparto de cada pronóstico entre las variables que lo produjeron.'),
        ('Desfase', 'Cuando la curva pronosticada tiene la forma correcta pero llega días tarde.')]
rows = [[Paragraph('Término', st['head']), Paragraph('Significado', st['head'])]] + [[Paragraph(a, st['glos_t']), Paragraph(b, st['glos_d'])] for a, b in GLOS]
t = Table(rows, colWidths=[4.3*cm, 12.1*cm], repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), AZUL), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, FONDO]),
                       ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
S.append(t)
P('Anexo B. Reproducibilidad y productos', 'h1')
P('El cálculo completo está en notebook_final.ipynb, que se ejecuta de principio a fin a partir de los datos crudos (data/raw). Todos los valores de esta memoria se leen del archivo resultados/resultados.json que genera el notebook; los de la sección 4.9 provienen del notebook de análisis complementarios.')
TABLAT([['Producto', 'Contenido'],
        ['notebook_final.ipynb', 'Pipeline completo y ejecutado: datos, Thiessen, variables, comparación de modelos, optimización, modelos finales, alcance, intervalos, alerta y SHAP'],
        ['model.pkl', 'Modelos LightGBM (h = 1, 3, 5), modelos cuantílicos (P5, P75, P95) con su recalibración, clasificador de alerta a 3 días con su valor de corte, variables, umbrales, métricas y pesos de Thiessen'],
        ['app.py', 'Aplicación Streamlit de pronóstico y alerta'],
        ['datos_muestra.csv', '100 días (marzo–junio de 2019, crecida de mayo) con lluvia por estación, Pmed y caudal'],
        ['README.md / requirements.txt', 'Descripción del proyecto, resultados, instrucciones y dependencias']],
       [4*cm, 12.4*cm], 'Productos entregados.')
TABLAT([['Componente', 'Detalle'],
        ['Software', 'Python 3.11; numpy 2.4, pandas 3.0, scikit-learn 1.8, LightGBM 4.7, XGBoost 3.2, SHAP 0.51, GeoPandas 1.1, Streamlit 1.64'],
        ['Proyección', 'UTM 21S (EPSG:32721)'], ['Semilla aleatoria', '42'],
        ['Hiperparámetros LightGBM', ', '.join(f'{k} = {v}' for k, v in MJ.items())],
        ['Partición', 'Entrenamiento 1974–2002; test 2013–2023; recalibración de intervalos 2013–2015; evaluación de intervalos 2016–2023'],
        ['Clasificador', 'LightGBM, 300 árboles, 15 hojas; valor de corte por máximo CSI con TimeSeriesSplit (5 bloques) en el entrenamiento']],
       [4*cm, 12.4*cm], 'Configuración del cálculo.')

doc = Doc(OUT)
doc.multiBuild(S)
print('ok', OUT)
