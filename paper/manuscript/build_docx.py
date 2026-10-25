#!/usr/bin/env python3
"""
build_docx.py - Build the Word (.docx) version of the preprint from the same source as the PDF.

PLAIN-LANGUAGE NOTE: The Word file is made from preprint.tex, numbers.json, the
compiled preprint.aux (figure, table, section and reference numbers), the
tables/*.tex files and references.tex, so it says exactly what preprint.pdf says.
Nothing is retyped. Figures are the same images. Layout follows the PDF: US Letter,
two columns, single-column title block and abstract, Palatino 10 pt, APS-style
headings, "FIG. n:" and "TABLE n:" captions, full-width figures and tables where the
PDF has them. Run after compiling the PDF. Output: preprint.docx
Usage: python3 build_docx.py
"""
import json
import os
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Emu
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
N = json.load(open(os.path.join(HERE, "numbers.json")))
AUX = open(os.path.join(HERE, "preprint.aux")).read()
CITE = dict(re.findall(r"\\bibcite\{([^}]+)\}\{(\d+)\}", AUX))
LABEL = dict(re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", AUX))
TEX = open(os.path.join(HERE, "preprint.tex")).read()
FONT = "Palatino Linotype"
EMAIL = "abdulwahabfatima43@gmail.com"

# geometry from preprint.tex (inches)
PAGE_W, PAGE_H = 8.5, 11.0
M_TOP, M_BOT, M_SIDE, COL_SEP = 0.85, 0.90, 0.72, 0.26
TEXT_W = PAGE_W - 2 * M_SIDE
COL_W = (TEXT_W - COL_SEP) / 2
BLUE = RGBColor(0x00, 0x00, 0xB3)

# ----------------------------------------------------------------------------- inline LaTeX -> runs
SIMPLE = [(r"\%", "%"), (r"\&", "&"), (r"\_", "_"), (r"\#", "#"), ("~", "\u00a0"), ("``", "\u201c"), ("''", "\u201d"),
          ("---", "\u2014"), ("--", "\u2013"), (r"\,", "\u2009"), (r"\S", "\u00a7"), (r"\ ", " "), ("\\\\", " "),
          (r"\sau{}", r"\textit{S.~aureus}"), (r"\pae{}", r"\textit{P.~aeruginosa}")]
MATH = [(r"\le", "\u2264"), (r"\ge", "\u2265"), (r"\kappa", "\u03ba"), (r"\beta", "\u03b2"), (r"\times", "\u00d7"),
        ("^{a}", "\u1d43"), ("^{*}", "*"), ("\\", "")]


def expand(s):
    s = re.sub(r"\\nv\{([^}]+)\}", lambda m: str(N[m.group(1)]), s)
    s = re.sub(r"\\cite\{([^}]+)\}", lambda m: "[" + cite_nums(m.group(1)) + "]", s)
    s = re.sub(r"\\ref\{([^}]+)\}", lambda m: LABEL.get(m.group(1), "?"), s)
    s = re.sub(r"\\label\{[^}]*\}", "", s)
    s = re.sub(r"\\g\{", r"\\textit{", s)
    return s


def cite_nums(keys):
    ns = sorted(int(CITE[k.strip()]) for k in keys.split(","))
    out, i = [], 0
    while i < len(ns):
        j = i
        while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
            j += 1
        out.append(f"{ns[i]}\u2013{ns[j]}" if j - i >= 2 else ", ".join(str(x) for x in ns[i:j + 1]))
        i = j + 1
    return ", ".join(out)


def match_brace(s, i):
    """s[i] == '{'; return index of the matching '}'."""
    depth = 0
    for k in range(i, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    return len(s) - 1


def runs(s, italic=False, bold=False, mono=False, sup=False, link=None):
    """Return a list of (text, style dict) for an inline LaTeX string."""
    for a, b in SIMPLE:
        s = s.replace(a, b)
    out, i, buf = [], 0, ""

    def flush():
        nonlocal buf
        if buf:
            out.append((buf, dict(italic=italic, bold=bold, mono=mono, sup=sup, link=link)))
            buf = ""
    while i < len(s):
        c = s[i]
        if c == "$":
            j = s.index("$", i + 1)
            m = s[i + 1:j]
            flush()
            if m.strip() == "n":
                out.append(("n", dict(italic=True, bold=bold, mono=mono, sup=sup, link=link)))
            else:
                for a, b in MATH:
                    m = m.replace(a, b)
                out.append((m.replace("{", "").replace("}", ""), dict(italic=italic, bold=bold, mono=mono, sup=sup, link=link)))
            i = j + 1
            continue
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+)\*?", s[i:])
            if m:
                cmd = m.group(1)
                k = i + m.end()
                if k < len(s) and s[k] == "{":
                    e = match_brace(s, k)
                    arg = s[k + 1:e]
                    flush()
                    if cmd in ("textit", "emph"):
                        out += runs(arg, True, bold, mono, sup, link)
                    elif cmd == "textbf":
                        out += runs(arg, italic, True, mono, sup, link)
                    elif cmd == "texttt":
                        out += runs(arg, italic, bold, True, sup, link)
                    elif cmd == "textsuperscript":
                        out += runs(arg, italic, bold, mono, True, link)
                    elif cmd == "url":
                        out.append((arg, dict(italic=False, bold=bold, mono=False, sup=False, link=arg)))
                    elif cmd == "href":
                        k2 = e + 1
                        e2 = match_brace(s, k2)
                        out += runs(s[k2 + 1:e2], italic, bold, mono, sup, arg)
                        e = e2
                    elif cmd in ("MakeUppercase",):
                        out += runs(arg.upper(), italic, bold, mono, sup, link)
                    else:  # unknown command with argument: keep the argument text
                        out += runs(arg, italic, bold, mono, sup, link)
                    i = e + 1
                    continue
                i = k  # bare command (e.g. \par, \noindent): drop
                continue
        if c in "{}":
            i += 1
            continue
        buf += c
        i += 1
    flush()
    # tidy whitespace
    res = []
    for t, st in out:
        t = re.sub(r"[ \t\n]+", " ", t)
        if t:
            res.append((t, st))
    return res


# ----------------------------------------------------------------------------- docx helpers
d = Document()
sec0 = d.sections[0]
sec0.page_width, sec0.page_height = Inches(PAGE_W), Inches(PAGE_H)
sec0.top_margin, sec0.bottom_margin = Inches(M_TOP), Inches(M_BOT)
sec0.left_margin = sec0.right_margin = Inches(M_SIDE)
body = d.element.body
for p in list(body):
    if p.tag == qn("w:p"):
        body.remove(p)


def set_font(rpr_owner, size=None, name=FONT):
    st = rpr_owner
    st.font.name = name
    rpr = st.element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(a), name)
    if size:
        st.font.size = Pt(size)


normal = d.styles["Normal"]
set_font(normal, 10)
normal.paragraph_format.space_after = Pt(0)
normal.paragraph_format.space_before = Pt(0)
normal.paragraph_format.line_spacing = 1.0


def add_hyperlink(par, url, text, st):
    part = par.part
    rid = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                         is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    col = OxmlElement("w:color")
    col.set(qn("w:val"), "0000B3")
    rpr.append(col)
    if st.get("italic"):
        rpr.append(OxmlElement("w:i"))
    if st.get("mono"):
        rf = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            rf.set(qn(a), "Courier New")
        rpr.insert(0, rf)
    r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    h.append(r)
    par._p.append(h)


def write_runs(par, rs, size=None, color=None):
    for t, st in rs:
        if st.get("link"):
            add_hyperlink(par, st["link"], t, st)
            continue
        r = par.add_run(t)
        r.italic = st.get("italic") or None
        r.bold = st.get("bold") or None
        if st.get("sup"):
            r.font.superscript = True
        if st.get("mono"):
            r.font.name = "Courier New"
            r._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:hAnsi"), "Courier New")
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color
        # citation numbers in blue, as in the PDF
    return par


def para(text_tex, size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True, before=0, after=0, italic=False, bold=False):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.first_line_indent = Inches(0.17) if indent else None
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    write_runs(p, runs(text_tex, italic=italic, bold=bold), size)
    return p


def sect_break(par, cols):
    """Put a continuous section break at the end of paragraph `par`; the section ending there has `cols` columns."""
    ppr = par._p.get_or_add_pPr()
    sp = OxmlElement("w:sectPr")
    t = OxmlElement("w:type")
    t.set(qn("w:val"), "continuous")
    sp.append(t)
    pg = OxmlElement("w:pgSz")
    pg.set(qn("w:w"), str(int(PAGE_W * 1440)))
    pg.set(qn("w:h"), str(int(PAGE_H * 1440)))
    sp.append(pg)
    mar = OxmlElement("w:pgMar")
    for k, v in [("top", M_TOP), ("bottom", M_BOT), ("left", M_SIDE), ("right", M_SIDE), ("header", 0.5),
                 ("footer", 0.5), ("gutter", 0)]:
        mar.set(qn(f"w:{k}"), str(int(v * 1440)))
    sp.append(mar)
    c = OxmlElement("w:cols")
    c.set(qn("w:num"), str(cols))
    c.set(qn("w:space"), str(int(COL_SEP * 1440)))
    sp.append(c)
    ppr.append(sp)


def tiny_para():
    p = d.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("")
    p.paragraph_format.line_spacing = Pt(1)
    rpr = p._p.get_or_add_pPr()
    sz = OxmlElement("w:rPr")
    s = OxmlElement("w:sz")
    s.set(qn("w:val"), "2")
    sz.append(s)
    rpr.append(sz)
    return p


def heading(text, level):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.keep_with_next = True
    if level == 1:
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.space_before, pf.space_after = Pt(10), Pt(5)
        write_runs(p, [(t.upper(), dict(st, bold=True)) for t, st in runs(text)], 9)
        p.style = d.styles["Heading 1"] if False else p.style
    elif level == 2:
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pf.space_before, pf.space_after = Pt(8), Pt(4)
        write_runs(p, [(t, dict(st, bold=True)) for t, st in runs(text)], 9)
    else:
        pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
        pf.space_before, pf.space_after = Pt(6), Pt(1)
        write_runs(p, [(t, dict(st, italic=True)) for t, st in runs(text)], 9.5)
    # outline level for navigation pane
    ppr = p._p.get_or_add_pPr()
    ol = OxmlElement("w:outlineLvl")
    ol.set(qn("w:val"), str(level - 1))
    ppr.append(ol)
    return p


def caption(kind, num, text):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = WD_ALIGN_PARAGRAPH.CENTER if len(text) < 200 else WD_ALIGN_PARAGRAPH.JUSTIFY
    pf.space_before, pf.space_after = Pt(3 if kind == "FIG." else 6), Pt(8 if kind == "FIG." else 3)
    if kind == "TABLE":
        pf.keep_with_next = True
    write_runs(p, [(f"{kind} {num}: ", {})] + runs(text), 9)
    return p


def picture(path, width_in):
    p = d.add_paragraph()
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_before = Pt(6)
    w, h = Image.open(path).size
    p.add_run().add_picture(path, width=Inches(width_in))
    return p


def borders(cell, top=None, bottom=None):
    tcpr = cell._tc.get_or_add_tcPr()
    b = tcpr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders")
        tcpr.append(b)
    for side, val in [("top", top), ("bottom", bottom)]:
        if val:
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(val))
            e.set(qn("w:space"), "0")
            e.set(qn("w:color"), "000000")
            b.append(e)


def cell_margins(tbl, lr=50):
    tblpr = tbl._tbl.tblPr
    m = OxmlElement("w:tblCellMar")
    for side, v in [("top", 10), ("bottom", 10), ("left", lr), ("right", lr)]:
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:w"), str(v))
        e.set(qn("w:type"), "dxa")
        m.append(e)
    tblpr.append(m)


def tex_table(path, width_in, size=7.5):
    t = open(os.path.join(HERE, path)).read()
    spec = re.search(r"\\begin\{tabular[x]?\}(?:\{[^}]*\})?\{(.*?)\}\n", t, flags=re.S).group(1)
    spec = re.sub(r"@\{\}", "", spec)
    spec = re.sub(r">\{[^}]*\}", "", spec)
    aligns = re.findall(r"[lrcX]|p\{[^}]*\}", spec)
    inner = t[t.index("\\toprule") + 8:t.rindex("\\bottomrule")]
    note = ""
    after = t[t.rindex("\\bottomrule") + 11:]
    mn = re.search(r"\\multicolumn\{\d+\}\{[^}]*\}\{(.*)\}\\\\", after, flags=re.S)
    if mn:
        note = re.sub(r"\\footnotesize\s*", "", mn.group(1))
    rows, rule_before = [], set()
    for chunk in re.split(r"\\\\", inner):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk.startswith("\\midrule") or "\\midrule" in chunk.split("\n")[0]:
            rule_before.add(len(rows))
            chunk = chunk.replace("\\midrule", "").strip()
        chunk = re.sub(r"\\cmidrule(\([^)]*\))?\{[^}]*\}", "", chunk).strip()
        if not chunk:
            continue
        cells = []
        for c in re.split(r"(?<!\\)&", chunk):
            m = re.match(r"\s*\\multicolumn\{(\d+)\}\{[^}]*\}\{(.*)\}\s*$", c, flags=re.S)
            if m:
                cells.append((int(m.group(1)), m.group(2), "c"))
            else:
                cells.append((1, c.strip(), None))
        rows.append(cells)
    ncol = len(aligns)
    header_rows = 1
    if rows and any(span > 1 for span, _, _ in rows[0]):
        header_rows = 2
    tbl = d.add_table(rows=len(rows), cols=ncol)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    plain = lambda x: "".join(t for t, _ in runs(expand(x)))
    lens, words = [3] * ncol, [3] * ncol
    for cells in rows:
        ci = 0
        for span, text, _ in cells:
            if span == 1 and ci < ncol:
                tx = plain(text)
                lens[ci] = max(lens[ci], min(len(tx), 60))
                words[ci] = max([words[ci]] + [len(w) for w in tx.split()])
            ci += span
    wts = [max(wd + 1.5, L ** 0.8) for L, wd in zip(lens, words)]
    tot = sum(wts)
    colw = [width_in * w / tot for w in wts]
    cell_margins(tbl)
    for ri, cells in enumerate(rows):
        ci = 0
        for span, text, al in cells:
            if ci >= ncol:
                break
            cell = tbl.cell(ri, ci)
            if span > 1:
                cell = cell.merge(tbl.cell(ri, min(ncol - 1, ci + span - 1)))
            p = cell.paragraphs[0]
            p.paragraph_format.first_line_indent = None
            a = al or (aligns[ci] if ci < len(aligns) else "l")
            p.paragraph_format.alignment = {"r": WD_ALIGN_PARAGRAPH.RIGHT, "c": WD_ALIGN_PARAGRAPH.CENTER}.get(
                a[0], WD_ALIGN_PARAGRAPH.LEFT)
            write_runs(p, runs(expand(text)), size)
            ci += span
    # keep each table on one page
    for ri, row in enumerate(tbl.rows):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if ri < len(tbl.rows) - 1:
            for c in row.cells:
                for pp in c.paragraphs:
                    pp.paragraph_format.keep_with_next = True
    # booktabs-style rules
    for ci in range(ncol):
        borders(tbl.cell(0, ci), top=12)
        borders(tbl.cell(header_rows - 1, ci), bottom=6)
        borders(tbl.cell(len(rows) - 1, ci), bottom=12)
        for rb in rule_before:
            if 0 < rb < len(rows) and rb != header_rows:
                borders(tbl.cell(rb, ci), top=4)
    # header rows repeat; width
    for ri in range(header_rows):
        trpr = tbl.rows[ri]._tr.get_or_add_trPr()
        e = OxmlElement("w:tblHeader")
        trpr.append(e)
    for ri in range(len(rows)):
        for ci in range(ncol):
            tbl.cell(ri, ci).width = Inches(colw[ci])
    grid = tbl._tbl.tblGrid
    for gc, cw in zip(grid.findall(qn("w:gridCol")), colw):
        gc.set(qn("w:w"), str(int(cw * 1440)))
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tbl._tbl.tblPr.append(lay)
    tblpr = tbl._tbl.tblPr
    w = OxmlElement("w:tblW")
    w.set(qn("w:w"), str(int(width_in * 1440)))
    w.set(qn("w:type"), "dxa")
    old = tblpr.find(qn("w:tblW"))
    if old is not None:
        tblpr.remove(old)
    tblpr.append(w)
    if note:
        p = para(expand(note), size=7, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=False, before=2)
    sp = d.add_paragraph()
    sp.paragraph_format.space_after = Pt(4)
    return tbl


# ----------------------------------------------------------------------------- front matter
title_block = TEX[TEX.index("{\\large\\bfseries") + 16:TEX.index("\\vspace{10pt}")]
title_lines = [l.replace("\\par", "").strip().rstrip("}") for l in title_block.strip().split("\n")]
title = " ".join(title_lines)
t1, t2 = title.split("? ", 1)
p = d.add_paragraph()
p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(8)
write_runs(p, [(t, dict(st, bold=True)) for t, st in runs(t1 + "?")], 12)
p.add_run().add_break()
write_runs(p, [(t, dict(st, bold=True)) for t, st in runs(t2)], 12)

p = d.add_paragraph()
p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
write_runs(p, [("Fatima Abdulwahab ", {})], 10)
p.add_run().add_picture(os.path.join(HERE, "figures", "orcid_icon.png"), height=Pt(8))
r = p.add_run(" 1,*")
r.font.superscript = True
p = d.add_paragraph()
p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
r = p.add_run("1")
r.font.superscript = True
r.font.size = Pt(9)
r = p.add_run("Independent Researcher, Dallas, Texas, USA")
r.italic = True
r.font.size = Pt(9)
p = d.add_paragraph()
p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(10)
r = p.add_run("*")
r.font.size = Pt(8)
add_hyperlink(p, f"mailto:{EMAIL}", EMAIL, {})
for rr in p.runs:
    rr.font.size = Pt(8)
p.add_run(" \u00b7 ORCID ").font.size = Pt(8)
add_hyperlink(p, "https://orcid.org/0009-0008-2298-8386", "0009-0008-2298-8386", {})

abs_tex = TEX[TEX.index("\\small\n", TEX.index("\\begin{minipage}{0.98")) + 7:TEX.index("\\par\\vspace{4pt}\\noindent")]
kw_tex = TEX[TEX.index("\\textbf{Keywords:}") + 18:TEX.index("\\end{minipage}", TEX.index("\\textbf{Keywords:}"))]
p = para(expand(abs_tex), size=9.5, indent=False)
p.paragraph_format.left_indent = p.paragraph_format.right_indent = Inches(0.75)
p = d.add_paragraph()
p.paragraph_format.left_indent = p.paragraph_format.right_indent = Inches(0.75)
p.paragraph_format.space_before, p.paragraph_format.space_after = Pt(4), Pt(12)
write_runs(p, [("Keywords: ", dict(bold=True))] + runs(expand(kw_tex)), 9.5)
sect_break(p, 1)

# ----------------------------------------------------------------------------- body
start = TEX.index("\\section{Introduction}")
end = TEX.index("\\small\n\\input{references.tex}")
src = expand(TEX[start:end])
src = re.sub(r"(?m)(?<!\\)%.*$", "", src)
src = src.replace("\\addcontentsline{toc}{section}{Data and code availability}", "")

FLOAT = re.compile(r"\\begin\{(figure|table)(\*?)\}(?:\[[^\]]*\])?(.*?)\\end\{\1\2\}", re.S)
TOKEN = re.compile(r"(\\section\*?\{[^}]*\}|\\subsection\*?\{[^}]*\}|\\subsubsection\*?\{[^}]*\}|@@FLOAT\d+@@)")
floats = []


def stash(m):
    floats.append(m)
    return f"\n\n@@FLOAT{len(floats) - 1}@@\n\n"


src = FLOAT.sub(stash, src)
sec_n = sub_n = ssub_n = 0
ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
fig_n = 0
tab_n = 0
pending = []
last_par = None


def emit_float(m):
    global fig_n, last_par
    kind, star, content = m.group(1), m.group(2), m.group(3)
    wide = star == "*"
    cap = re.search(r"\\caption\{", content)
    capt = content[cap.end():match_brace(content, cap.end() - 1)] if cap else ""
    if wide:
        tp = tiny_para()
        sect_break(tp, 2)
    if kind == "figure":
        fig_n += 1
        g = re.search(r"\\includegraphics\[width=([\d.]*)\\(textwidth|linewidth)\]\{([^}]+)\}", content)
        frac = float(g.group(1) or 1)
        path = os.path.join(HERE, g.group(3).replace(".pdf", ".png"))
        w = (TEXT_W if wide else COL_W) * frac
        picture(path, w)
        caption("FIG.", fig_n, capt)
    else:
        tl = re.search(r"\\input\{([^}]+)\}", content).group(1)
        global tab_n
        tab_n += 1
        num = ROMAN[tab_n]
        caption("TABLE", num, capt)
        tex_table(tl, TEXT_W if wide else COL_W, 7 if wide else 6.8)
    if wide:
        tp = tiny_para()
        sect_break(tp, 1)


pieces = TOKEN.split(src)
for piece in pieces:
    if not piece or not piece.strip():
        continue
    m = re.match(r"\\(section|subsection|subsubsection)(\*?)\{(.*)\}$", piece.strip(), flags=re.S)
    if m:
        lvl, star, txt = m.group(1), m.group(2), m.group(3)
        if lvl == "section":
            if star:
                heading(txt, 1)
            else:
                sec_n += 1
                sub_n = ssub_n = 0
                heading(f"{ROMAN[sec_n]}. {txt}", 1)
        elif lvl == "subsection":
            sub_n += 1
            ssub_n = 0
            heading(f"{chr(64 + sub_n)}. {txt}", 2)
        else:
            ssub_n += 1
            heading(f"{ssub_n}. {txt}.", 3)
        continue
    fm = re.match(r"@@FLOAT(\d+)@@", piece.strip())
    if fm:
        pending.append(floats[int(fm.group(1))])
        continue
    for block in re.split(r"\n\s*\n", piece):
        b = block.strip()
        if not b:
            continue
        para(b)
        while pending:
            emit_float(pending.pop(0))
while pending:
    emit_float(pending.pop(0))

# ----------------------------------------------------------------------------- references
heading("References", 1)
refs = open(os.path.join(HERE, "references.tex")).read()
for k, txt in re.findall(r"\\bibitem\{([^}]+)\}\s*(.*?)(?=\n\\bibitem|\n\\end\{thebibliography\})", refs, flags=re.S):
    p = d.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Inches(0.25)
    pf.first_line_indent = Inches(-0.25)
    pf.space_after = Pt(2)
    pf.alignment = WD_ALIGN_PARAGRAPH.LEFT
    write_runs(p, [(f"[{CITE[k]}] ", {})] + runs(expand(txt.strip())), 8.5)

# final section: two columns
sp = d.sections[-1]._sectPr
c = sp.find(qn("w:cols"))
if c is None:
    c = OxmlElement("w:cols")
    sp.append(c)
c.set(qn("w:num"), "2")
c.set(qn("w:space"), str(int(COL_SEP * 1440)))
t = sp.find(qn("w:type"))
if t is None:
    t = OxmlElement("w:type")
    sp.insert(0, t)
t.set(qn("w:val"), "continuous")

# page numbers in footer
footer = d.sections[0].footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
for tag, txt in [("begin", None), (None, "PAGE"), ("end", None)]:
    r = fp.add_run()
    if tag:
        f = OxmlElement("w:fldChar")
        f.set(qn("w:fldCharType"), tag)
        r._r.append(f)
    else:
        it = OxmlElement("w:instrText")
        it.set(qn("xml:space"), "preserve")
        it.text = txt
        r._r.append(it)
    r.font.size = Pt(9)

settings = d.settings.element
ah = OxmlElement("w:autoHyphenation")
ah.set(qn("w:val"), "true")
settings.append(ah)
hz = OxmlElement("w:hyphenationZone")
hz.set(qn("w:val"), "180")
settings.append(hz)
cp = d.core_properties
cp.author = "Fatima Abdulwahab"
cp.title = title.replace("\\&", "&")
cp.subject = "Preprint"
cp.keywords = "test verification; CLIA; reference isolates; AR Isolate Bank; rapid diagnostics"
out = os.path.join(HERE, "preprint.docx")
d.save(out)
print("wrote", out)
