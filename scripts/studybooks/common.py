"""Shared helpers for study book PDFs (reportlab). Fonts: DejaVu (Linux; apt fonts-dejavu)."""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                PageBreak, Preformatted, Table, TableStyle, KeepTogether,
                                ListFlowable, ListItem, Image)

FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FD + "DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Bold", FD + "DejaVuSansMono-Bold.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans", boldItalic="Sans-Bold")
pdfmetrics.registerFontFamily("Mono", normal="Mono", bold="Mono-Bold", italic="Mono", boldItalic="Mono-Bold")

INK = colors.HexColor("#1f2933")
ACCENT = colors.HexColor("#1d4ed8")
MUTED = colors.HexColor("#52606d")
CODEBG = colors.HexColor("#f1f5f9")
CODEBORDER = colors.HexColor("#cbd5e1")
NOTEBG = colors.HexColor("#fff7e6")
NOTEBORDER = colors.HexColor("#f59e0b")
OKBG = colors.HexColor("#ecfdf5")
OKBORDER = colors.HexColor("#10b981")
WARNBG = colors.HexColor("#fef2f2")
WARNBORDER = colors.HexColor("#ef4444")

body = ParagraphStyle("body", fontName="Sans", fontSize=9.6, leading=14.2, textColor=INK, alignment=TA_LEFT, spaceAfter=5)
small = ParagraphStyle("small", parent=body, fontSize=8.6, leading=12.4)
h1 = ParagraphStyle("h1", parent=body, fontName="Sans-Bold", fontSize=18, leading=23, textColor=ACCENT, spaceBefore=4, spaceAfter=8)
h2 = ParagraphStyle("h2", parent=body, fontName="Sans-Bold", fontSize=12.5, leading=17, textColor=INK, spaceBefore=11, spaceAfter=5)
h3 = ParagraphStyle("h3", parent=body, fontName="Sans-Bold", fontSize=10.4, leading=14.5, textColor=ACCENT, spaceBefore=7, spaceAfter=3)
title = ParagraphStyle("title", parent=body, fontName="Sans-Bold", fontSize=26, leading=32, textColor=INK, spaceAfter=6)
subtitle = ParagraphStyle("subtitle", parent=body, fontSize=12, leading=17, textColor=MUTED, spaceAfter=14)
cell = ParagraphStyle("cell", parent=body, fontSize=8.6, leading=12, spaceAfter=0)
cellb = ParagraphStyle("cellb", parent=cell, fontName="Sans-Bold")
code = ParagraphStyle("code", fontName="Mono", fontSize=8.2, leading=11.2, textColor=INK)


def esc(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<font name="Mono" size="8.6" color="#9d174d">\1</font>', t)
    return t


def P(t, st=body):
    return Paragraph(esc(t), st)


def H1(t):
    return Paragraph(esc(t), h1)


def H2(t):
    return Paragraph(esc(t), h2)


def H3(t):
    return Paragraph(esc(t), h3)


def bullets(items, st=body):
    return ListFlowable([ListItem(P(i, st), leftIndent=12) for i in items], bulletType="bullet",
                        start="•", leftIndent=14, bulletFontSize=8)


def numbered(items, st=body):
    return ListFlowable([ListItem(P(i, st), leftIndent=14) for i in items], bulletType="1",
                        leftIndent=16, bulletFontName="Sans-Bold", bulletFontSize=9)


CODE_MAX_LINES = 55  # one code box must fit on a page


def CODE(src, caption=None, width_mm=170):
    src = src.strip("\n")
    lines = src.splitlines()
    longest = max((len(l) for l in lines), default=0)
    st = code
    fits = int(92 * width_mm / 170)  # characters that fit at the default font size
    if longest > fits:  # shrink the font so long lines still fit the box (never below 6pt)
        size = max(6.0, code.fontSize * fits / longest)
        st = ParagraphStyle("code_small", parent=code, fontSize=size, leading=size * 1.37)
    out = [P(caption, small)] if caption else []
    chunks = [lines[i:i + CODE_MAX_LINES] for i in range(0, max(len(lines), 1), CODE_MAX_LINES)]
    for n, chunk in enumerate(chunks):
        if n > 0:
            out.append(P("(continued)", small))
        t = Table([[Preformatted("\n".join(chunk), st)]], colWidths=[width_mm * mm])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODEBG), ("BOX", (0, 0), (-1, -1), 0.6, CODEBORDER),
                               ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                               ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        out += [t, Spacer(1, 6)]
    return out


def BOX(text_items, bg, border, label=None):
    flows = []
    if label:
        flows.append(Paragraph(esc(label), ParagraphStyle("lbl", parent=cell, fontName="Sans-Bold", textColor=border)))
        flows.append(Spacer(1, 2))
    for t in text_items:
        flows.append(P(t, cell) if isinstance(t, str) else t)
    t = Table([[flows]], colWidths=[170 * mm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.9, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return [t, Spacer(1, 7)]


def NOTE(items, label="Note"):
    return BOX(items, NOTEBG, NOTEBORDER, label)


def OK(items, label="Remember"):
    return BOX(items, OKBG, OKBORDER, label)


def WARN(items, label="Common mistake"):
    return BOX(items, WARNBG, WARNBORDER, label)


def TABLE(rows, widths, header=True):
    data = []
    for ri, r in enumerate(rows):
        data.append([Paragraph(esc(c), cellb if (header and ri == 0) else cell) for c in r])
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, CODEBORDER), ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
             ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), CODEBG))
    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 8)]


def QA(q, a):
    return [KeepTogether([Paragraph(esc("Q: " + q), ParagraphStyle("q", parent=body, fontName="Sans-Bold", spaceAfter=2)),
                          P(a)])]



class Story(list):
    """List of flowables; `S += x` accepts a single flowable or a list of them."""
    def __iadd__(self, other):
        if isinstance(other, (list, tuple)):
            self.extend(other)
        else:
            self.append(other)
        return self


def build(out_path, story, footer_text, title):
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Sans", 7.8)
        canvas.setFillColor(MUTED)
        canvas.drawString(20 * mm, 11 * mm, footer_text)
        canvas.drawRightString(190 * mm, 11 * mm, "Page %d" % doc.page)
        canvas.restoreState()

    doc = BaseDocTemplate(out_path, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm, topMargin=18 * mm,
                          bottomMargin=20 * mm, title=title, author="Claude Code")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=footer)])
    doc.build(story)


def cover(kicker, title_text, subtitle_text):
    return [Spacer(1, 30),
            Paragraph(kicker, ParagraphStyle("kicker", parent=body, fontName="Sans-Bold", fontSize=11, textColor=ACCENT)),
            Paragraph(title_text, title), Paragraph(subtitle_text, subtitle)]


def IMG(path, width_mm=150, caption=None):
    """An image scaled to width_mm, keeping its aspect ratio, with an optional caption below."""
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    img = Image(path, width=width_mm * mm, height=width_mm * mm * h / w)
    out = [Spacer(1, 4), img]
    if caption:
        out.append(P(caption, small))
    out.append(Spacer(1, 8))
    return [KeepTogether(out)]


def RIDER_BREAKPOINT_TIP(image_path):
    """The breakpoint popup from the user's own Rider (topic 5 screenshot); shared by several study books."""
    return NOTE([
        "**Right-click the red breakpoint dot** to open the **Line breakpoint** popup (your Rider, Topic 5):",
        "**Enabled**: switch the breakpoint off without deleting it.",
        "**Suspend execution**: checked = pause here (normal breakpoint). Unchecked = do not pause; together with a log message in **More** it becomes a "
        "**logpoint / tracepoint** that prints without stopping and without editing code.",
        "**Condition**: a C# expression evaluated at this line; the debugger pauses only when it is `true`, e.g. `task.Id == 158`. "
        "The arrow on the right shows conditions you used before; the expand icon gives a bigger editor.",
        "**More (Shift+Cmd+F8)**: the full breakpoint dialog (hit count, log message, all breakpoints in one list).",
        "**Done** saves it. A conditional breakpoint gets a small mark on its red dot.",
    ], "Rider: the breakpoint popup") + IMG(image_path, 150, "Your Rider: a conditional breakpoint on the codes.Add line, condition task.Id == 158 (Debug Lab A, bug 2).")


def git_show(root, rev, rel):
    """File content at a git revision, so a study book prints the code as it was when its topic finished."""
    import subprocess
    return subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=root, capture_output=True, text=True, check=True).stdout


def method(source, signature):
    """Cut one C# member out of a file: attributes/comments above it, then the signature line to its closing brace.
    Braces are counted only from the signature line on, so route templates like "{id:int}" are not mistaken for blocks."""
    lines = source.splitlines()
    sig = next(i for i, l in enumerate(lines) if signature in l)
    start = sig
    while start > 0 and lines[start - 1].strip().startswith(("[", "//")):
        start -= 1
    indent = len(lines[sig]) - len(lines[sig].lstrip())
    out = [l[indent:] if len(l) >= indent else l for l in lines[start:sig]]
    depth, opened = 0, False
    for l in lines[sig:]:
        out.append(l[indent:] if len(l) >= indent else l)
        depth += l.count("{") - l.count("}")
        opened = opened or "{" in l
        if opened and depth == 0:
            break
    return "\n".join(out)
