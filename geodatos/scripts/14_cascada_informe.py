"""Compila el informe técnico de La Cascada en PDF.

Une los textos de estudios/la-cascada/texto/*.md (en orden alfabético) con las figuras de estudios/la-cascada/figuras/.
Markdown admitido: # ## ###, párrafos, listas con «- » o «1. », tablas con «|», **negrita**, *cursiva*, `código`,
[texto](url), figuras ![pie](figuras/archivo.png), «> » para recuadros y la línea [[SALTO]] para saltar de página.

Uso: .venv/bin/python -I scripts/14_cascada_informe.py
"""
import re, json, pathlib, datetime, os
import matplotlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, NextPageTemplate, Flowable)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = pathlib.Path(__file__).resolve().parents[1]
EST = ROOT / "estudios/la-cascada"
TXT, FIG = EST / "texto", EST / "figuras"
OUT = EST / "Informe_La_Cascada_desvio_quebradas.pdf"
import tempfile
TMP = pathlib.Path(tempfile.gettempdir()) / "cascada_fig_recortes"

FD = pathlib.Path(matplotlib.__file__).parent / "mpl-data/fonts/ttf"
for n, f in [("Serif", "DejaVuSerif.ttf"), ("Serif-B", "DejaVuSerif-Bold.ttf"), ("Serif-I", "DejaVuSerif-Italic.ttf"),
             ("Serif-BI", "DejaVuSerif-BoldItalic.ttf"), ("Sans", "DejaVuSans.ttf"), ("Sans-B", "DejaVuSans-Bold.ttf"),
             ("Sans-I", "DejaVuSans-Oblique.ttf"), ("Mono", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(n, str(FD / f)))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-B", italic="Serif-I", boldItalic="Serif-BI")
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-B")

ACENTO = colors.HexColor("#9b1c1c"); GRIS = colors.HexColor("#555555"); FONDO = colors.HexColor("#f3f1ec")
S = {
    "body": ParagraphStyle("body", fontName="Serif", fontSize=9.6, leading=13.6, alignment=TA_JUSTIFY, spaceAfter=5),
    "h1": ParagraphStyle("h1", fontName="Sans-B", fontSize=15, leading=19, textColor=ACENTO, spaceBefore=6, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Sans-B", fontSize=11.5, leading=15, spaceBefore=10, spaceAfter=5),
    "h3": ParagraphStyle("h3", fontName="Sans-B", fontSize=10, leading=13, textColor=GRIS, spaceBefore=7, spaceAfter=3),
    "li": ParagraphStyle("li", fontName="Serif", fontSize=9.6, leading=13.4, leftIndent=14, bulletIndent=4, spaceAfter=2, alignment=TA_LEFT),
    "cap": ParagraphStyle("cap", fontName="Sans", fontSize=7.8, leading=10.2, textColor=GRIS, spaceBefore=3, spaceAfter=10, alignment=TA_LEFT),
    "cell": ParagraphStyle("cell", fontName="Sans", fontSize=7.6, leading=9.6),
    "cellh": ParagraphStyle("cellh", fontName="Sans-B", fontSize=7.6, leading=9.6, textColor=colors.white),
    "box": ParagraphStyle("box", fontName="Sans", fontSize=8.8, leading=12.2, alignment=TA_LEFT),
    "toc1": ParagraphStyle("toc1", fontName="Sans", fontSize=9.5, leading=15, leftIndent=0),
    "toc2": ParagraphStyle("toc2", fontName="Sans", fontSize=8.5, leading=12, leftIndent=14, textColor=GRIS),
}

def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r'<font name="Mono" size="8.4">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?!\w)", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<link href="\2" color="#1f4e79">\1</link>', t)
    t = re.sub(r"(?<![\"'>=])(https?://[^\s<)]+)", r'<link href="\1" color="#1f4e79">\1</link>', t)
    t = re.sub(r"\^(\d+)\^", r"<super>\1</super>", t)
    return t

class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            lvl = 0 if f.style.name == "h1" else 1
            key = f"h{id(f)}"; self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(re.sub("<[^>]+>", "", f.getPlainText()), key, level=lvl)
            self.notify("TOCEntry", (lvl, f.getPlainText(), self.page, key))

class Linea(Flowable):
    def __init__(self, w, c=ACENTO, t=1.2): super().__init__(); self.w, self.c, self.t = w, c, t
    def wrap(self, *a): return self.w, self.t + 2
    def draw(self): self.canv.setStrokeColor(self.c); self.canv.setLineWidth(self.t); self.canv.line(0, 0, self.w, 0)

W, H = A4; M = 2.0 * cm; CW = W - 2 * M
NFIG = [0]; NTAB = [0]

def figura(path, cap):
    p = EST / path if not pathlib.Path(path).is_absolute() else pathlib.Path(path)
    if not p.exists():
        return [Paragraph(f"<i>[Figura no disponible: {path}]</i>", S["cap"])]
    from reportlab.lib.utils import ImageReader
    from PIL import Image as PImage, ImageChops
    im = PImage.open(p).convert("RGB")                      # recorta márgenes blancos de matplotlib
    bb = ImageChops.difference(im, PImage.new("RGB", im.size, "white")).getbbox()
    if bb:
        pad = 12; bb = (max(bb[0] - pad, 0), max(bb[1] - pad, 0), min(bb[2] + pad, im.width), min(bb[3] + pad, im.height))
        TMP.mkdir(exist_ok=True); q = TMP / p.name; im.crop(bb).save(q); p = q
    iw, ih = ImageReader(str(p)).getSize()
    w = CW; h = w * ih / iw
    if h > 13.0 * cm: h = 13.0 * cm; w = h * iw / ih
    NFIG[0] += 1
    return [KeepTogether([Image(str(p), width=w, height=h), Paragraph(f"<b>Figura {NFIG[0]}.</b> {inline(cap)}", S["cap"])])]

def tabla(rows, cap=None):
    rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    n = max(len(r) for r in rows); rows = [r + [""] * (n - len(r)) for r in rows]
    data = [[Paragraph(inline(c), S["cellh"] if i == 0 else S["cell"]) for c in r] for i, r in enumerate(rows)]
    lens = [max(len(re.sub(r"\*|`", "", r[j])) for r in rows) for j in range(n)]
    tot = sum(min(l, 60) + 6 for l in lens); cw = [CW * (min(l, 60) + 6) / tot for l in lens]
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3a3a3a")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                           ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, FONDO]), ("LINEBELOW", (0, -1), (-1, -1), 0.6, GRIS),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    out = [t]
    if cap:
        NTAB[0] += 1; out.insert(0, Paragraph(f"<b>Tabla {NTAB[0]}.</b> {inline(cap)}", S["cap"]))
    return [Spacer(1, 3)] + out + [Spacer(1, 8)]

def recuadro(lines):
    p = [Paragraph(inline(l), S["box"]) for l in lines]
    t = Table([[p]], colWidths=[CW]); t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), FONDO), ("LINEBEFORE", (0, 0), (0, -1), 3, ACENTO),
                                                         ("LEFTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return [Spacer(1, 4), t, Spacer(1, 8)]

def md(text):
    out, lines, i = [], text.splitlines(), 0
    cap_tab = None
    while i < len(lines):
        l = lines[i]; s = l.strip()
        if not s: i += 1; continue
        if s == "[[SALTO]]": out.append(PageBreak()); i += 1; continue
        m = re.match(r"^(#{1,3})\s+(.*)", s)
        if m:
            lv = len(m.group(1)); out.append(Paragraph(inline(m.group(2)), S[f"h{lv}"]))
            if lv == 1: out.append(Linea(CW)); out.append(Spacer(1, 6))
            i += 1; continue
        m = re.match(r"^!\[(.*)\]\((.*)\)$", s)
        if m: out += figura(m.group(2), m.group(1)); i += 1; continue
        m = re.match(r"^Tabla:\s*(.*)", s)
        if m: cap_tab = m.group(1); i += 1; continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"): rows.append(lines[i]); i += 1
            out += tabla(rows, cap_tab); cap_tab = None; continue
        if s.startswith(">"):
            bl = []
            while i < len(lines) and lines[i].strip().startswith(">"): bl.append(lines[i].strip()[1:].strip()); i += 1
            paras, cur = [], []
            for b in bl:
                if b: cur.append(b)
                elif cur: paras.append(" ".join(cur)); cur = []
            if cur: paras.append(" ".join(cur))
            out += recuadro(paras); continue
        m = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)", l)
        if m:
            while i < len(lines):
                m = re.match(r"^(\s*)([-*]|\d+[.)])\s+(.*)", lines[i])
                if not m:
                    if lines[i].strip() and lines[i].startswith("  ") and out: # continuación
                        out[-1] = Paragraph(out[-1].text + " " + inline(lines[i].strip()), out[-1].style, bulletText=out[-1].bulletText); i += 1; continue
                    break
                ind = len(m.group(1)) // 2; bul = "•" if m.group(2) in "-*" else m.group(2)
                st = ParagraphStyle(f"li{ind}", parent=S["li"], leftIndent=14 + 14 * ind, bulletIndent=4 + 14 * ind)
                out.append(Paragraph(inline(m.group(3)), st, bulletText=bul)); i += 1
            out.append(Spacer(1, 4)); continue
        buf = [s]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|!\[|\||>|[-*]\s|\d+[.)]\s|\[\[|Tabla:)", lines[i].strip()):
            buf.append(lines[i].strip()); i += 1
        out.append(Paragraph(inline(" ".join(buf)), S["body"]))
    return out

def portada(c, d):
    meta = json.loads((TXT / "portada.json").read_text())
    c.saveState()
    c.setFillColor(colors.HexColor("#1b1b1b")); c.rect(0, H - 9.5 * cm, W, 9.5 * cm, fill=1, stroke=0)
    c.setFillColor(ACENTO); c.rect(0, H - 9.7 * cm, W, 0.2 * cm, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Sans", 9); c.drawString(M, H - 2.2 * cm, meta["serie"].upper())
    y = H - 4.0 * cm
    for ln in meta["titulo"]:
        c.setFont("Sans-B", 21); c.drawString(M, y, ln); y -= 0.95 * cm
    c.setFont("Sans", 11); c.setFillColor(colors.HexColor("#dddddd"))
    for ln in meta["subtitulo"]:
        y -= 0.1 * cm; c.drawString(M, y, ln); y -= 0.55 * cm
    img = FIG / meta.get("imagen", "f3d_cuenca.png")
    if img.exists():
        from reportlab.lib.utils import ImageReader
        ir = ImageReader(str(img)); iw, ih = ir.getSize(); w = CW; h = w * ih / iw
        if h > 12 * cm: h = 12 * cm; w = h * iw / ih
        c.drawImage(ir, (W - w) / 2, H - 10.3 * cm - h, w, h)
    c.setFillColor(colors.black); y = 6.6 * cm
    for k, v in meta["ficha"]:
        c.setFont("Sans-B", 8.5); c.drawString(M, y, k); c.setFont("Sans", 8.5); c.drawString(M + 4.2 * cm, y, v); y -= 0.5 * cm
    from reportlab.lib.utils import simpleSplit
    c.setFillColor(GRIS); c.setFont("Sans-I", 7.5)
    lines = [l for a in meta["aviso"] for l in simpleSplit(a, "Sans-I", 7.5, CW)]
    for j, ln in enumerate(lines): c.drawString(M, 2.6 * cm - j * 0.36 * cm, ln)
    c.restoreState()

def pie(c, d):
    c.saveState(); c.setFont("Sans", 7.2); c.setFillColor(GRIS)
    c.drawString(M, 1.15 * cm, PIE_TXT); c.drawRightString(W - M, 1.15 * cm, f"{d.page}")
    c.setStrokeColor(colors.HexColor("#cccccc")); c.setLineWidth(0.4); c.line(M, 1.5 * cm, W - M, 1.5 * cm); c.restoreState()

PIE_TXT = ""

def main():
    global PIE_TXT
    meta = json.loads((TXT / "portada.json").read_text()); PIE_TXT = meta["pie"]
    doc = Doc(str(OUT), pagesize=A4, leftMargin=M, rightMargin=M, topMargin=1.8 * cm, bottomMargin=2.0 * cm,
              title=" ".join(meta["titulo"]), author=meta["autor_pdf"], subject=meta["asunto"], creator="geodatos/scripts/14_cascada_informe.py")
    fr = Frame(M, 2.0 * cm, CW, H - 3.8 * cm, id="f")
    doc.addPageTemplates([PageTemplate("portada", [Frame(M, M, CW, H - 2 * M)], onPage=portada),
                          PageTemplate("normal", [fr], onPage=pie)])
    toc = TableOfContents(); toc.levelStyles = [S["toc1"], S["toc2"]]; toc.dotsMinLevel = 0
    story = [NextPageTemplate("normal"), PageBreak(), Paragraph("Contenido", ParagraphStyle("h1toc", parent=S["h1"])), Linea(CW), Spacer(1, 8), toc, PageBreak()]
    for f in sorted(TXT.glob("*.md")):
        story += md(f.read_text())
    doc.multiBuild(story)
    print("PDF:", OUT, f"({NFIG[0]} figuras, {NTAB[0]} tablas)")

if __name__ == "__main__":
    main()
