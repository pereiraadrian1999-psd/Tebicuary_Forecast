const pptxgen = require('pptxgenjs');
const fs = require('fs');
const { applyTheme } = require('/root/.claude/skills/synced/6a1c0c12-174d-411a-bd87-6f89fc8a8985_58f4361c-5dd8-4a58-8cde-0bc6c8c20a58/pptx/scripts/apply_theme.js');

const F = '/home/claude/work/final/figuras/';
const D = '/home/claude/work/final/figs_diag/';
const G = JSON.parse(fs.readFileSync(__dirname + '/guion.json', 'utf8'));
const R = JSON.parse(fs.readFileSync('/home/claude/work/final/resultados/resultados.json', 'utf8'));
const OUT = __dirname + '/Presentacion_Pronostico_Tebicuary.pptx';

const THEME = {
  name: 'Tebicuary', headFontFace: 'Cambria', bodyFontFace: 'Calibri',
  colors: { dk1: '1B2A33', lt1: 'FFFFFF', dk2: '0E4D64', lt2: 'EAF2F4', accent1: '0E4D64', accent2: '1F8A9E', accent3: 'E07A1F',
            accent4: '7FB3C2', accent5: '8A8984', accent6: 'B83A2E', hlink: '1F8A9E', folHlink: '0E4D64' } };
const HX = THEME.colors;

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';            // 13.33 x 7.5 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = 'Pronóstico de caudales y alerta de crecidas — río Tebicuary en Villa Florida';
pres.author = 'Ing. Jorge Adrián Pereira Oviedo';
const C = pres.SchemeColor;
const W = 13.33;

// ------------------------------------------------------------------ layouts
pres.defineSlideMaster({
  title: 'PORTADA', background: { color: HX.dk2 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.8, y: 2.0, w: 11.7, h: 1.9, fontFace: 'Cambria', fontSize: 40, bold: true, color: C.background1, valign: 'bottom' }, text: '' } },
    { placeholder: { options: { name: 'body', type: 'body', x: 0.8, y: 4.1, w: 11.7, h: 1.2, fontFace: 'Calibri', fontSize: 18, color: C.background2, valign: 'top' }, text: '' } },
  ] });
pres.defineSlideMaster({
  title: 'CONTENIDO', background: { color: HX.lt1 },
  margin: [0.5, 0.6, 0.6, 0.6],
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontFace: 'Cambria', fontSize: 30, bold: true, color: C.text2, valign: 'middle', margin: 0 }, text: '' } },
    { text: { text: 'Pronóstico de caudales y alerta de crecidas · río Tebicuary en Villa Florida', options: { x: 0.6, y: 7.0, w: 9, h: 0.3, fontFace: 'Calibri', fontSize: 10, color: C.accent5, margin: 0 } } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontFace: 'Calibri', fontSize: 10, color: C.accent5, align: 'right' } });
pres.defineSlideMaster({
  title: 'CIERRE', background: { color: HX.dk2 },
  objects: [
    { placeholder: { options: { name: 'title', type: 'title', x: 0.6, y: 0.4, w: 12.1, h: 0.9, fontFace: 'Cambria', fontSize: 32, bold: true, color: C.background1, valign: 'middle', margin: 0 }, text: '' } },
  ],
  slideNumber: { x: 12.2, y: 7.0, w: 0.5, h: 0.3, fontFace: 'Calibri', fontSize: 10, color: C.accent4, align: 'right' } });

const nota = (s, n) => { const g = G[n - 1]; s.addNotes(`[${g.bloque} · ${g.tiempo}] ${g.decir}`); };
const img = (s, path, x, y, w, ratio, name) => s.addImage({ path, x, y, w, h: w / ratio, objectName: name });
function stat(s, x, y, w, h, big, small, colorBig, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: C.background2 }, line: { type: 'none' }, rectRadius: 0.12, objectName: name + ' fondo' });
  s.addText(big, { x: x + 0.2, y: y + 0.15, w: w - 0.4, h: h * 0.55, fontFace: 'Cambria', fontSize: 34, bold: true, color: colorBig || C.text2, margin: 0, valign: 'bottom', isTextBox: true, objectName: name + ' valor' });
  s.addText(small, { x: x + 0.2, y: y + 0.15 + h * 0.55, w: w - 0.4, h: h * 0.4 - 0.15, fontFace: 'Calibri', fontSize: 14, color: C.text1, margin: 0, valign: 'top', isTextBox: true, objectName: name + ' etiqueta' });
}
function circulo(s, x, y, num, color) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.55, h: 0.55, fill: { color: color || C.accent2 }, line: { type: 'none' }, objectName: 'icono ' + num });
  s.addText(String(num), { x, y, w: 0.55, h: 0.55, fontFace: 'Calibri', fontSize: 18, bold: true, color: C.background1, align: 'center', valign: 'middle', margin: 0, isTextBox: true, objectName: 'icono texto ' + num });
}
function fila(s, x, y, w, num, titulo, texto, color) {
  circulo(s, x, y, num, color);
  s.addText([{ text: titulo, options: { bold: true, color: C.text2, fontSize: 16, breakLine: true } }, { text: texto, options: { color: C.text1, fontSize: 14 } }],
            { x: x + 0.75, y: y - 0.08, w: w - 0.75, h: 1.0, fontFace: 'Calibri', valign: 'top', margin: 0, paraSpaceAfter: 2, isTextBox: true, objectName: 'fila ' + num });
}
const MF = R.metricas_finales, COB = {};
R.cobertura.forEach(c => { COB[`${c.h}_${c.recalibrada}`] = c; });
const pct = (x, d = 0) => (100 * x).toFixed(d).replace('.', ',') + ' %';

pres.addSection({ title: 'Bloque 1 · Problema' });
// ------------------------------------------------------------------ 1 portada
let s = pres.addSlide({ masterName: 'PORTADA', sectionTitle: 'Bloque 1 · Problema' });
s.addText('Pronóstico de caudales y alerta de crecidas en el río Tebicuary (Villa Florida)', { placeholder: 'title' });
s.addText('Aprendizaje automático con LightGBM · pronóstico a 1, 3 y 5 días con intervalos de confianza · alerta del caudal de 10 % de permanencia', { placeholder: 'body' });
s.addText('Ing. Jorge Adrián Pereira Oviedo · Diplomado en Machine Learning y Deep Learning Aplicado · FIUNA 2026', { x: 0.8, y: 6.3, w: 11.7, h: 0.5, fontFace: 'Calibri', fontSize: 14, color: C.accent4, margin: 0, isTextBox: true, objectName: 'autor' });
nota(s, 1);

// ------------------------------------------------------------------ 2 problema
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 1 · Problema' });
s.addText('Anticipar las crecidas del Tebicuary en Villa Florida', { placeholder: 'title' });
s.addText([
  { text: 'Las crecidas afectan la ruta PY01, zonas productivas y poblaciones ribereñas.', options: { bullet: true, breakLine: true } },
  { text: 'Hoy la anticipación depende de la lectura diaria de la estación y del criterio del operador.', options: { bullet: true, breakLine: true } },
  { text: 'Objetivo: pronosticar el caudal a 1, 3 y 5 días con intervalos de confianza y alertar la superación del caudal de 10 % de permanencia.', options: { bullet: true, breakLine: true } },
  { text: 'Usuarios: gestión de riesgo (SEN, DINAC, municipios) y proyectistas viales e hidráulicos.', options: { bullet: true } }],
  { x: 0.6, y: 1.5, w: 6.4, h: 4.8, fontFace: 'Calibri', fontSize: 18, color: C.text1, paraSpaceAfter: 14, valign: 'top', margin: 0, isTextBox: true, objectName: 'texto problema' });
stat(s, 7.6, 1.5, 5.1, 1.45, '20 987 km²', 'cuenca de aporte a Villa Florida', null, 'cuenca');
stat(s, 7.6, 3.15, 5.1, 1.45, '823 m³/s', 'umbral de crecida: caudal superado el 10 % del tiempo', C.accent3, 'umbral');
stat(s, 7.6, 4.8, 5.1, 1.45, '1974–2023', '8 pluviómetros y caudal diario', null, 'datos');
nota(s, 2);

// ------------------------------------------------------------------ 4 ML vs DL
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 1 · Problema' });
s.addText('Por qué machine learning (y no deep learning)', { placeholder: 'title' });
const card = (x, titulo, lineas, color, name) => {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.5, w: 5.9, h: 4.9, fill: { color: C.background2 }, line: { type: 'none' }, rectRadius: 0.12, objectName: name + ' fondo' });
  s.addText(titulo, { x: x + 0.35, y: 1.75, w: 5.2, h: 0.6, fontFace: 'Cambria', fontSize: 22, bold: true, color: color, margin: 0, isTextBox: true, objectName: name + ' titulo' });
  s.addText(lineas.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < lineas.length - 1 } })),
            { x: x + 0.35, y: 2.45, w: 5.2, h: 2.4, fontFace: 'Calibri', fontSize: 16, color: C.text1, paraSpaceAfter: 10, valign: 'top', margin: 0, isTextBox: true, objectName: name + ' texto' });
};
const cifra = (x, v, t, color, name) => {
  s.addText(v, { x: x + 0.35, y: 4.95, w: 2.0, h: 1.0, fontFace: 'Cambria', fontSize: 44, bold: true, color, margin: 0, valign: 'middle', isTextBox: true, objectName: name + ' cifra' });
  s.addText(t, { x: x + 2.45, y: 4.95, w: 3.1, h: 1.0, fontFace: 'Calibri', fontSize: 14, color: C.text1, margin: 0, valign: 'middle', isTextBox: true, objectName: name + ' cifra texto' });
};
card(0.6, 'Se usa: machine learning', ['Una fila por día, 18 variables: caudal reciente y tendencia, lluvia acumulada de 1 a 30 días, humedad antecedente y mes.',
  '~7 400 días de entrenamiento y pocas crecidas.', 'Gradient boosting (LightGBM): estado del arte para datos tabulares.'], C.text2, 'ML');
card(6.8, 'No se usa: deep learning', ['Red neuronal densa de 3 capas probada en el mismo pipeline.', 'Skill a 3 días: 0,47 frente a 0,54 de LightGBM.',
  'No mejora la precisión: queda como línea futura (LSTM) con más datos.'], C.accent6, 'DL');
cifra(0.6, '0,54', 'skill a 3 días · LightGBM (modelo final)', C.text2, 'ML');
cifra(6.8, '0,47', 'skill a 3 días · red neuronal densa', C.accent6, 'DL');
nota(s, 3);

// ------------------------------------------------------------------ métrica de éxito
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 1 · Problema' });
s.addText('Métrica de éxito: mejorar a la persistencia', { placeholder: 'title' });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.5, w: 6.6, h: 2.3, fill: { color: C.text2 }, line: { type: 'none' }, rectRadius: 0.12, objectName: 'formula fondo' });
s.addText('Skill = 1 − MSE modelo / MSE persistencia', { x: 0.9, y: 1.75, w: 6.0, h: 0.9, fontFace: 'Cambria', fontSize: 22, bold: true, color: C.background1, margin: 0, valign: 'middle', isTextBox: true, objectName: 'formula' });
s.addText('0 = igual que suponer que el caudal no cambia · 0,5 = la mitad del error · 1 = perfecto', { x: 0.9, y: 2.75, w: 6.0, h: 0.8, fontFace: 'Calibri', fontSize: 15, color: C.background2, margin: 0, valign: 'top', isTextBox: true, objectName: 'formula texto' });
s.addText([
  { text: 'Por qué no alcanza el NSE', options: { bold: true, color: C.text2, breakLine: true } },
  { text: 'En un río lento, "mañana igual que hoy" ya da NSE = 0,99 a 1 día: un NSE alto no prueba que el modelo aporte.', options: { breakLine: true } },
  { text: ' ', options: { breakLine: true } },
  { text: 'Para la alerta', options: { bold: true, color: C.text2, breakLine: true } },
  { text: 'Crecidas detectadas, días de anticipación y falsas alarmas por año.', options: {} }],
  { x: 0.6, y: 4.1, w: 6.6, h: 2.6, fontFace: 'Calibri', fontSize: 16, color: C.text1, valign: 'top', margin: 0, paraSpaceAfter: 4, isTextBox: true, objectName: 'explicacion metrica' });
stat(s, 7.7, 1.5, 5.0, 1.6, '0,99', 'NSE de la persistencia a 1 día (test): la vara es alta', C.accent5, 'nse pers');
stat(s, 7.7, 3.3, 5.0, 1.6, '0,54', 'skill del modelo a 3 días: elimina el 54 % del error', null, 'skill 3');
stat(s, 7.7, 5.1, 5.0, 1.6, '13/14', 'crecidas alertadas con anticipación (2013–2023)', C.accent3, 'alerta');
nota(s, 4);

pres.addSection({ title: 'Bloque 2 · Código' });
// ------------------------------------------------------------------ repositorio
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('Repositorio: estructura del proyecto', { placeholder: 'title' });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.45, w: 5.6, h: 5.25, fill: { color: '1B2A33' }, line: { type: 'none' }, rectRadius: 0.1, objectName: 'arbol fondo' });
const arbol = ['tebicuary-pronostico/', '├── README.md', '├── notebook_final.ipynb', '├── model.pkl', '├── app.py', '├── datos_muestra.csv', '├── requirements.txt',
               '├── data/raw/', '├── figuras/', '├── resultados/', '├── docs/', '├── src/', '└── analisis_complementarios/'];
s.addText(arbol.map((t, i) => ({ text: t, options: { breakLine: i < arbol.length - 1, color: i === 0 ? 'E07A1F' : 'EAF2F4' } })),
  { x: 0.9, y: 1.7, w: 5.1, h: 4.8, fontFace: 'Courier New', fontSize: 15, valign: 'top', margin: 0, paraSpaceAfter: 2, isTextBox: true, objectName: 'arbol' });
const desc = [['notebook_final.ipynb', 'Pipeline completo y ejecutado: datos → modelo → evaluación'], ['model.pkl', 'Modelos entrenados (1, 3 y 5 días), intervalos y alerta'],
              ['app.py', 'Aplicación Streamlit de pronóstico y alerta'], ['data/raw', 'Lluvia de 8 estaciones, caudal y cuenca'],
              ['docs', 'Memoria de cálculo, presentación y guion']];
desc.forEach((d, i) => s.addText([{ text: d[0], options: { bold: true, color: C.text2, breakLine: true, fontFace: 'Courier New', fontSize: 14 } }, { text: d[1], options: { color: C.text1, fontSize: 15 } }],
  { x: 6.7, y: 1.5 + i * 1.05, w: 6.0, h: 0.95, fontFace: 'Calibri', valign: 'top', margin: 0, isTextBox: true, objectName: 'desc ' + i }));
nota(s, 5);

// ------------------------------------------------------------------ 3 datos
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('Carga y limpieza de datos', { placeholder: 'title' });
img(s, F + 'mapa_thiessen.png', 0.6, 1.35, 5.4, 1.0, 'mapa Thiessen');
fila(s, 6.6, 1.6, 6.1, 1, 'Faltantes (−1) como faltantes, no como cero', 'Como cero, la lluvia anual de la cuenca habría bajado de 1 668 a 1 565 mm.');
fila(s, 6.6, 3.0, 6.1, 2, 'Series duplicadas Quyquyho = Caazapá (1974–2016)', 'Una fue completada con la otra: Caazapá se trató como faltante en ese período.');
fila(s, 6.6, 4.4, 6.1, 3, 'Thiessen dinámico', 'Los pesos se recalculan cada día solo con las estaciones que midieron (50 combinaciones).');
nota(s, 6);

// ------------------------------------------------------------------ 5 pipeline
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('Preprocesamiento: ColumnTransformer + Pipeline', { placeholder: 'title' });
img(s, D + 'pipeline.png', 0.6, 1.35, 12.1, 2.778, 'pipeline');
const bloques = [['Objetivo', 'Cambio relativo del caudal: log Q(t+h) − log Q(t), con h = 1, 3 y 5 días'],
                 ['Partición', 'Entrenamiento 1974–2002 · test 2013–2023, años que el modelo no vio'],
                 ['Hiperparámetros', 'RandomizedSearchCV con TimeSeriesSplit: siempre hacia adelante en el tiempo']];
bloques.forEach((b, i) => {
  const x = 0.6 + i * 4.1;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.85, w: 3.9, h: 1.0, fill: { color: C.background2 }, line: { type: 'none' }, rectRadius: 0.1, objectName: 'bloque ' + i });
  s.addText([{ text: b[0], options: { bold: true, color: C.text2, breakLine: true } }, { text: b[1], options: { color: C.text1 } }],
            { x: x + 0.15, y: 5.9, w: 3.6, h: 0.9, fontFace: 'Calibri', fontSize: 12, valign: 'middle', margin: 0, isTextBox: true, objectName: 'bloque texto ' + i });
});
nota(s, 7);

// ------------------------------------------------------------------ 6 comparacion (gráfico nativo)
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('Modelo entrenado: LightGBM', { placeholder: 'title' });
const MOD = ['Ridge', 'Random Forest', 'XGBoost', 'LightGBM'];
const sk = (m, h) => R.comparacion.find(c => c.modelo === m && c.h === h).Skill_pers;
s.addChart(pres.charts.BAR, [1, 3, 5].map(h => ({ name: `h = ${h} día${h > 1 ? 's' : ''}`, labels: MOD, values: MOD.map(m => +sk(m, h).toFixed(2)) })),
  { x: 0.6, y: 1.4, w: 8.2, h: 5.3, barDir: 'col', barGrouping: 'clustered', chartColors: [HX.accent4, HX.accent2, HX.dk2],
    showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 11, dataLabelFontFace: '+mn-lt', dataLabelColor: HX.dk1, dataLabelFormatCode: '0.00',
    valAxisMinVal: 0, valAxisMaxVal: 0.7, valAxisLabelFormatCode: '0.0', valAxisLabelFontSize: 11, catAxisLabelFontSize: 13, valAxisLabelFontFace: '+mn-lt', catAxisLabelFontFace: '+mn-lt',
    valAxisLabelColor: HX.accent5, catAxisLabelColor: HX.dk1, valGridLine: { color: 'E4E3DF', size: 0.75 }, catGridLine: { style: 'none' },
    showLegend: true, legendPos: 't', legendFontSize: 12, legendFontFace: '+mn-lt', showTitle: true, title: 'Skill frente a la persistencia (test 2013–2023)', titleFontSize: 14, titleColor: HX.dk1, titleFontFace: '+mn-lt',
    objectName: 'grafico comparacion' });
s.addText([{ text: 'Mismo pipeline para los 4 modelos', options: { bold: true, color: C.text2, breakLine: true } },
           { text: 'XGBoost y LightGBM empatan; se adopta LightGBM por su menor costo de entrenamiento.', options: { breakLine: true } },
           { text: ' ', options: { breakLine: true } },
           { text: 'Hiperparámetros', options: { bold: true, color: C.text2, breakLine: true } },
           { text: 'RandomizedSearchCV + TimeSeriesSplit; un modelo por horizonte (1, 3 y 5 días).', options: {} }],
  { x: 9.2, y: 1.8, w: 3.5, h: 4.4, fontFace: 'Calibri', fontSize: 16, color: C.text1, valign: 'top', margin: 0, paraSpaceAfter: 6, isTextBox: true, objectName: 'comentario' });
nota(s, 8);

// ------------------------------------------------------------------ 7 pronóstico
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('Evaluación sobre test: pronóstico a 1, 3 y 5 días', { placeholder: 'title' });
const ERR = { '1': '~2 %', '3': '~5 %', '5': '~10 %' };
['1', '3', '5'].forEach((h, i) => stat(s, 0.6 + i * 2.15, 1.45, 2.0, 1.75, pct(MF[h].Skill_pers), `menos error que la persistencia a ${h} día${h > 1 ? 's' : ''}`, null, 'skill ' + h));
['1', '3', '5'].forEach((h, i) => stat(s, 0.6 + i * 2.15, 3.4, 2.0, 1.75, ERR[h], `error típico en caudales medios y altos (h = ${h})`, C.accent2, 'error ' + h));
s.addText('En las subidas se queda corto (~10 %) y llega con ~1 día de atraso. Los estiajes (< 112 m³/s) no se pronostican: son más variables.', { x: 0.6, y: 5.45, w: 6.3, h: 0.9, fontFace: 'Calibri', fontSize: 14, italic: true, color: C.text1, margin: 0, valign: 'top', isTextBox: true, objectName: 'limitacion' });
img(s, F + 'hidrograma_test.png', 7.15, 1.4, 5.55, 1.833, 'hidrograma');
s.addText('Caudal observado (azul) y pronosticado a 3 y 5 días (naranja), test 2013–2023', { x: 7.15, y: 4.5, w: 5.55, h: 0.5, fontFace: 'Calibri', fontSize: 11, color: C.accent5, margin: 0, isTextBox: true, objectName: 'pie hidrograma' });
nota(s, 9);

// ------------------------------------------------------------------ 8 intervalos
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('Intervalos de confianza del 90 % calibrados', { placeholder: 'title' });
['1', '3', '5'].forEach((h, i) => stat(s, 0.6 + i * 4.1, 1.45, 3.9, 1.6, pct(COB[`${h}_true`].cobertura), `de los caudales observados dentro del intervalo a ${h} día${h > 1 ? 's' : ''} (2016–2023)`, null, 'cobertura ' + h));
img(s, F + 'intervalos_evento.png', 0.95, 3.3, 11.4, 3.421, 'intervalos 2019');
s.addText('Regresión cuantílica (P5–P95) recalibrada con 2013–2015 y evaluada en 2016–2023 · crecida de mayo de 2019', { x: 0.6, y: 6.68, w: 12.1, h: 0.28, fontFace: 'Calibri', fontSize: 11, color: C.accent5, margin: 0, isTextBox: true, objectName: 'pie intervalos' });
nota(s, 10);

// ------------------------------------------------------------------ 9 alerta
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('Alerta de crecidas: 13 de 14 detectadas', { placeholder: 'title' });
const ev = (w, m) => R.alerta.por_evento.find(e => e.ventana === w && e.metodo === m);
const a5 = ev(5, 'Regresión (valor central)'), a3 = ev(3, 'Clasificador (probabilidad)'), t3 = ev(3, 'Persistencia de la tendencia');
const niv = [['Aviso temprano · 5 días', 'Algún pronóstico supera 823 m³/s', a5, C.accent2], ['Alerta · 3 días', 'Probabilidad del clasificador ≥ 0,30', a3, C.accent3]];
niv.forEach((n, i) => {
  const y = 1.45 + i * 1.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y, w: 5.6, h: 1.3, fill: { color: C.background2 }, line: { type: 'none' }, rectRadius: 0.12, objectName: 'nivel ' + i });
  s.addText([{ text: n[0], options: { bold: true, fontSize: 18, color: n[3], breakLine: true } }, { text: n[1], options: { fontSize: 13, color: C.text1 } }],
            { x: 0.8, y: y + 0.15, w: 3.0, h: 1.0, fontFace: 'Calibri', valign: 'middle', margin: 0, isTextBox: true, objectName: 'nivel texto ' + i });
  s.addText([{ text: `${n[2].detectados}/${n[2].eventos}`, options: { bold: true, fontSize: 26, color: C.text2, breakLine: true } },
             { text: `${n[2].anticipacion_media.toFixed(1).replace('.', ',')} días antes · ${n[2].falsas_por_ano.toFixed(2).replace('.', ',')} falsas/año`, options: { fontSize: 12, color: C.text1 } }],
            { x: 3.8, y: y + 0.15, w: 2.3, h: 1.0, fontFace: 'Calibri', valign: 'middle', margin: 0, isTextBox: true, objectName: 'nivel cifras ' + i });
});
s.addText('La única no detectada (26/10/2015) fue un pico de un día causado por lluvia caída después de la emisión.',
  { x: 0.6, y: 4.6, w: 5.6, h: 1.2, fontFace: 'Calibri', fontSize: 15, italic: true, color: C.text1, valign: 'top', margin: 0, isTextBox: true, objectName: 'no detectada' });
img(s, F + 'alerta_probabilidad.png', 6.5, 1.45, 6.2, 2.895, 'probabilidad 2019');
s.addText('Izquierda: la probabilidad es confiable (sigue a la diagonal). Derecha: en 2019 la alerta se activó el 6 de mayo, tres días antes del cruce.', { x: 6.5, y: 3.65, w: 6.2, h: 0.55, fontFace: 'Calibri', fontSize: 11, color: C.accent5, margin: 0, isTextBox: true, objectName: 'pie alerta' });
stat(s, 6.5, 4.45, 6.2, 1.85, `${t3.falsas_por_ano.toFixed(1).replace('.', ',')} vs ${a3.falsas_por_ano.toFixed(2).replace('.', ',')}`, 'falsas alarmas por año: extrapolar la tendencia frente al modelo, con la misma detección', C.accent6, 'falsas alarmas');
nota(s, 11);

// ------------------------------------------------------------------ inferencia
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 2 · Código' });
s.addText('El modelo cargándose y haciendo inferencia', { placeholder: 'title' });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.45, w: 12.1, h: 2.35, fill: { color: '1B2A33' }, line: { type: 'none' }, rectRadius: 0.1, objectName: 'codigo fondo' });
const cod = ["cargado = joblib.load('model.pkl')", "Xh = construir_features(hist).iloc[[-1]][cargado['features']]",
             "q_t3 = q_hoy * np.exp(cargado['modelos'][3].predict(Xh)[0])", "p_3d = cargado['alerta'][3]['modelo'].predict_proba(Xh)[0, 1]"];
s.addText(cod.map((t, i) => ({ text: t, options: { breakLine: i < cod.length - 1 } })),
  { x: 0.9, y: 1.65, w: 11.5, h: 2.0, fontFace: 'Courier New', fontSize: 16, color: 'EAF2F4', valign: 'middle', margin: 0, paraSpaceAfter: 4, isTextBox: true, objectName: 'codigo' });
s.addText('Salida con datos del 7 de mayo de 2019 (caudal del día: 674 m³/s)', { x: 0.6, y: 4.05, w: 12.1, h: 0.4, fontFace: 'Calibri', fontSize: 15, bold: true, color: C.text2, margin: 0, isTextBox: true, objectName: 'salida titulo' });
[['756 m³/s', 't+1 · observado 775'], ['877 m³/s', 't+3 · observado 1 098'], ['974 m³/s', 't+5 · observado 1 336'], ['65 %', 'probabilidad de superar 823 m³/s en 3 días: ALERTA']].forEach((v, i) =>
  stat(s, 0.6 + i * 3.08, 4.6, 2.9, 1.9, v[0], v[1], i === 3 ? C.accent3 : null, 'salida ' + i));
nota(s, 12);

pres.addSection({ title: 'Bloque 3 · Demo' });
// ------------------------------------------------------------------ 11 app
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 3 · Demo' });
s.addText('Aplicación Streamlit: del modelo a la operación', { placeholder: 'title' });
img(s, F + 'app_pronostico.png', 0.6, 1.35, 8.1, 1.5, 'captura app');
s.addText([
  { text: 'Entrada: CSV diario con fecha, lluvia media y caudal.', options: { bullet: true, breakLine: true } },
  { text: '7/5/2019: 674 m³/s → 756, 877 y 974 a 1, 3 y 5 días, con intervalos.', options: { bullet: true, breakLine: true } },
  { text: 'Aviso temprano activo y 65 % de probabilidad: alerta. El cruce ocurrió el 9/5.', options: { bullet: true, breakLine: true } },
  { text: 'Simula lluvia adicional e indica cuándo el pronóstico es confiable.', options: { bullet: true, breakLine: true } },
  { text: 'model.pkl guarda pipeline, modelos e intervalos.', options: { bullet: true } }],
  { x: 9.0, y: 1.45, w: 3.7, h: 5.2, fontFace: 'Calibri', fontSize: 15, color: C.text1, paraSpaceAfter: 10, valign: 'top', margin: 0, isTextBox: true, objectName: 'texto app' });
nota(s, 13);

// ------------------------------------------------------------------ ROI
s = pres.addSlide({ masterName: 'CONTENIDO', sectionTitle: 'Bloque 3 · Demo' });
s.addText('Retorno de la inversión en tres escenarios', { placeholder: 'title' });
const RI = R.roi.escenarios, KK = ['Conservador', 'Base', 'Optimista'];
s.addChart(pres.charts.BAR, [{ name: 'ROI a 5 años', labels: KK, values: KK.map(k => +RI[k].ROI.toFixed(1)) }],
  { x: 0.6, y: 1.4, w: 6.4, h: 5.3, barDir: 'col', chartColors: [HX.accent2], showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 14, dataLabelFontFace: '+mn-lt',
    dataLabelColor: HX.dk1, dataLabelFormatCode: '0.0', valAxisHidden: true, valGridLine: { style: 'none' }, catGridLine: { style: 'none' }, catAxisLabelFontSize: 14,
    catAxisLabelFontFace: '+mn-lt', catAxisLabelColor: HX.dk1, showLegend: false, showTitle: true, title: 'ROI a 5 años = (beneficio − costo) / costo', titleFontSize: 14,
    titleColor: HX.dk1, titleFontFace: '+mn-lt', objectName: 'grafico roi' });
const usd = v => 'USD ' + String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const filas = [['', 'Conservador', 'Base', 'Optimista'],
  ['Daño evitado por crecida', ...KK.map(k => usd(RI[k]['daño evitado por crecida (USD)']))],
  ['Implementación', ...KK.map(k => usd(RI[k]['implementación (USD)']))],
  ['Operación anual', ...KK.map(k => usd(RI[k]['operación anual (USD)']))],
  ['Costo por falsa alarma', ...KK.map(k => usd(RI[k]['costo por falsa alarma (USD)']))]];
s.addTable(filas.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0 || j === 0, color: i === 0 ? 'FFFFFF' : HX.dk1, fill: { color: i === 0 ? HX.dk2 : (i % 2 ? 'FFFFFF' : HX.lt2) }, fontSize: 12, fontFace: 'Calibri', align: j === 0 ? 'left' : 'center' } }))),
  { x: 7.3, y: 1.6, w: 5.4, colW: [1.9, 1.15, 1.15, 1.2], rowH: 0.45, border: { type: 'solid', pt: 0.5, color: 'C9C8C3' }, objectName: 'tabla supuestos' });
s.addText(`Del test: ${R.roi.crecidas_alertadas_por_ano.toFixed(2).replace('.', ',')} crecidas alertadas y ${R.roi.falsas_alarmas_por_ano.toFixed(2).replace('.', ',')} falsas alarmas por año. Montos: supuestos de referencia a validar con la autoridad de gestión de riesgo.`,
  { x: 7.3, y: 4.25, w: 5.4, h: 1.3, fontFace: 'Calibri', fontSize: 14, color: C.text1, valign: 'top', margin: 0, isTextBox: true, objectName: 'nota roi' });
nota(s, 14);

// ------------------------------------------------------------------ 12 cierre
s = pres.addSlide({ masterName: 'CIERRE', sectionTitle: 'Bloque 3 · Demo' });
s.addText('Conclusiones y próximos pasos', { placeholder: 'title' });
const concl = ['Pronóstico a 1, 3 y 5 días con 46–56 % menos error que la persistencia e intervalos calibrados.',
               '13 de 14 crecidas alertadas con 2 a 3 días de anticipación y menos de una falsa alarma por año.',
               'El atraso en las subidas se debe a afluentes sin medición, no al algoritmo.'];
const pasos = ['Medir el Tebicuary-mí y el Pirapó.', 'Definir con la autoridad los umbrales oficiales.', 'Recalibrar intervalos y alerta cada año.'];
s.addText('Conclusiones', { x: 0.6, y: 1.55, w: 6.6, h: 0.5, fontFace: 'Cambria', fontSize: 20, bold: true, color: C.accent4, margin: 0, isTextBox: true, objectName: 'sub conclusiones' });
s.addText(concl.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < concl.length - 1 } })),
  { x: 0.6, y: 2.2, w: 6.6, h: 4.2, fontFace: 'Calibri', fontSize: 18, color: C.background1, paraSpaceAfter: 14, valign: 'top', margin: 0, isTextBox: true, objectName: 'conclusiones' });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.7, y: 1.55, w: 5.0, h: 4.6, fill: { color: '15607A' }, line: { type: 'none' }, rectRadius: 0.12, objectName: 'fondo pasos' });
s.addText('Próximos pasos', { x: 8.0, y: 1.8, w: 4.4, h: 0.5, fontFace: 'Cambria', fontSize: 20, bold: true, color: C.accent3, margin: 0, isTextBox: true, objectName: 'sub pasos' });
s.addText(pasos.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < pasos.length - 1 } })),
  { x: 8.0, y: 2.45, w: 4.4, h: 3.5, fontFace: 'Calibri', fontSize: 18, color: C.background1, paraSpaceAfter: 14, valign: 'top', margin: 0, isTextBox: true, objectName: 'pasos' });
s.addText('Gracias', { x: 0.6, y: 6.5, w: 6, h: 0.5, fontFace: 'Cambria', fontSize: 22, italic: true, color: C.accent4, margin: 0, isTextBox: true, objectName: 'gracias' });
nota(s, 15);

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log('ok', OUT);
})();
