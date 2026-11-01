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
