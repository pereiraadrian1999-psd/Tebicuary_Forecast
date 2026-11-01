// Renderizador genérico: node render_docx.js contenido.json salida.docx
const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, ShadingType, LevelFormat, AlignmentType, BorderStyle, Footer, PageNumber } = require('docx');
const [, , IN, OUT] = process.argv;
const D = JSON.parse(fs.readFileSync(IN, 'utf8'));
const AZ = '0E4D64', TEAL = '1F8A9E', NAR = 'E07A1F', TX = '1B2A33', GR = '555555';
const FULL = 9026;
const runs = (t, o = {}) => {
  // **negrita** simple dentro del texto
  const parts = String(t).split(/(\*\*[^*]+\*\*)/g).filter(Boolean);
  return parts.map(p => p.startsWith('**') ? new TextRun({ text: p.slice(2, -2), bold: true, font: 'Calibri', size: 22, color: TX, ...o })
                                          : new TextRun({ text: p, font: 'Calibri', size: 22, color: TX, ...o }));
};
const P = (t, o = {}, po = {}) => new Paragraph({ spacing: { after: 110, line: 290 }, ...po, children: runs(t, o) });
const cell = (t, w, head, fill) => new TableCell({ width: { size: w, type: WidthType.DXA },
  shading: head ? { type: ShadingType.CLEAR, fill: AZ, color: 'auto' } : (fill ? { type: ShadingType.CLEAR, fill, color: 'auto' } : undefined),
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  children: String(t).split('\n').map(l => new Paragraph({ children: runs(l, { size: 19, bold: !!head, color: head ? 'FFFFFF' : TX }) })) });
const out = [];
for (const b of D.bloques) {
  if (b.t === 'titulo') out.push(new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: b.x, font: 'Cambria', color: AZ })] }));
  else if (b.t === 'sub') out.push(P(b.x, { color: GR }));
  else if (b.t === 'h1') out.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: !!b.salto, spacing: { before: 280, after: 120 }, children: [new TextRun({ text: b.x, font: 'Cambria', color: AZ })] }));
  else if (b.t === 'h2') out.push(new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 80 }, children: [new TextRun({ text: b.x, font: 'Cambria', color: AZ }), ...(b.tiempo ? [new TextRun({ text: '   ' + b.tiempo, font: 'Calibri', size: 21, color: TEAL })] : [])] }));
  else if (b.t === 'p') out.push(P(b.x));
  else if (b.t === 'etq') out.push(new Paragraph({ spacing: { after: 100, line: 280 }, children: [new TextRun({ text: b.e + ': ', bold: true, font: 'Calibri', size: 21, color: b.c || NAR }), ...runs(b.x, { size: 21, italics: !!b.i, color: b.i ? GR : TX })] }));
  else if (b.t === 'decir') out.push(new Paragraph({ spacing: { after: 120, line: 300 }, indent: { left: 280 }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: TEAL, space: 8 } }, children: runs(b.x, { size: 23 }) }));
  else if (b.t === 'lista') b.x.forEach(t => out.push(new Paragraph({ numbering: { reference: 'vinetas', level: 0 }, spacing: { after: 60, line: 280 }, children: runs(t) })));
  else if (b.t === 'num') b.x.forEach(t => out.push(new Paragraph({ numbering: { reference: 'numeros' + (b.ref || ''), level: 0 }, spacing: { after: 60, line: 280 }, children: runs(t) })));
  else if (b.t === 'codigo') b.x.forEach(t => out.push(new Paragraph({ spacing: { after: 0 }, shading: { type: ShadingType.CLEAR, fill: 'EAF2F4', color: 'auto' }, indent: { left: 200 }, children: [new TextRun({ text: t, font: 'Courier New', size: 19, color: TX })] })));
  else if (b.t === 'tabla') {
    const w = b.w.map(x => Math.round(x * FULL / b.w.reduce((a, c) => a + c, 0)));
    w[w.length - 1] = FULL - w.slice(0, -1).reduce((a, c) => a + c, 0);
    out.push(new Table({ width: { size: FULL, type: WidthType.DXA }, columnWidths: w,
      rows: b.filas.map((r, i) => new TableRow({ tableHeader: i === 0, children: r.map((c, j) => cell(c, w[j], i === 0, i > 0 && i % 2 === 0 ? 'F3F7F8' : null)) })) }));
    out.push(P(''));
  }
}
const numeros = Array.from({ length: 20 }, (_, i) => ({ reference: 'numeros' + (i ? i : ''), levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 500, hanging: 300 } } } }] }));
const doc = new Document({ creator: 'Ing. Jorge Adrián Pereira Oviedo', title: D.titulo,
  styles: { default: { document: { run: { font: 'Calibri', size: 22 } } } },
  numbering: { config: [{ reference: 'vinetas', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 500, hanging: 280 } } } }] }, ...numeros] },
  sections: [{ properties: { page: { margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: D.pie + ' · ', size: 16, color: GR, font: 'Calibri' }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GR, font: 'Calibri' })] })] }) },
    children: out }] });
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log('ok', OUT); });
