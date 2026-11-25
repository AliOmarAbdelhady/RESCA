"""Insert Section 3.3 System Design into the master report.

Reads section_3_3.md and figures/png/, converts them to WordprocessingML that
matches the report template (Times New Roman 12 pt body, 1.5 spacing, justified;
Report Table/Figure Caption styles; shaded table headers), and replaces
everything between the "3.3 SYSTEM DESIGN" heading and "Chapter Four" in
docs/documentation/main/Project 1 Docs.source. It also appends the new
references. Then it rebuilds the DOCX with build_docx.py.

    python3 docs/documentation/chapter5/tools/build_section.py

Running it again replaces the previous insertion, so the Markdown stays the
single source of the section text.
"""
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent.parent
DOCS = HERE.parent
DOCX = DOCS / "main" / "Project 1 Docs.docx"
PKG = DOCX.with_suffix(".source") / "package"
DOC_XML = PKG / "word" / "document.xml"
RELS = PKG / "word" / "_rels" / "document.xml.rels"
MEDIA = PKG / "word" / "media"
PNG = HERE / "figures" / "png"

START_MARK = "<!-- P5:SECTION-3.3:START -->"
END_MARK = "<!-- P5:SECTION-3.3:END -->"
TEXT_WIDTH_TWIPS = 8900
EMU_PER_PX = 914400 / 200          # figures are rendered at 200 dpi
MAX_W_EMU = 5_562_600              # same maximum width as the Chapter 4 figures
MAX_H_EMU = 7_200_000              # 20 cm, leaves room for the caption

NEW_REFERENCES = [
    "[27] Object Management Group, “OMG Unified Modeling Language (OMG UML), Version 2.5.1,” "
    "OMG Document formal/17-12-05, Dec. 2017. [Online]. Available: https://www.omg.org/spec/UML/2.5.1/",
    "[28] Software, Systems and Enterprise — Architecture Description, ISO/IEC/IEEE 42010:2022, 2022.",
    "[29] The PostgreSQL Global Development Group, “Row Security Policies,” PostgreSQL 18 Documentation. "
    "[Online]. Available: https://www.postgresql.org/docs/18/ddl-rowsecurity.html",
    "[30] PostGIS Project Steering Committee, “PostGIS Manual.” [Online]. Available: https://postgis.net/docs/",
    "[31] E. W. Dijkstra, “A note on two problems in connexion with graphs,” Numerische Mathematik, "
    "vol. 1, no. 1, pp. 269–271, 1959.",
]

# A hyphen inside an identifier (FR-HZ-06, UC-04, 3-39); ordinary compounds may still wrap.
ID_HYPHEN = re.compile(r"(?<=[A-Z0-9])-(?=[A-Z0-9])")

FONT = ('<w:rFonts w:ascii="Times New Roman" w:cs="Times New Roman" '
        'w:eastAsia="Times New Roman" w:hAnsi="Times New Roman"/>')


def esc(text):
    return html.escape(text, quote=False)


def runs(text, size=24, bold=False, nobreak=False):
    """Inline markup: **bold**, *italic*, _{sub}, ^{sup}."""
    out = []
    tokens = re.split(r"(\*\*.+?\*\*|\*[^*]+?\*|_\{[^}]*\}|\^\{[^}]*\})", text)
    for tok in tokens:
        if not tok:
            continue
        b, i, va, t = bold, False, None, tok
        if tok.startswith("**") and tok.endswith("**"):
            b, t = True, tok[2:-2]
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            i, t = True, tok[1:-1]
        elif tok.startswith("_{"):
            va, t = "subscript", tok[2:-1]
        elif tok.startswith("^{"):
            va, t = "superscript", tok[2:-1]
        props = FONT + ("<w:b/><w:bCs/>" if b else "") + ("<w:i/><w:iCs/>" if i else "")
        if va:
            props += f'<w:vertAlign w:val="{va}"/>'
        props += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
        if nobreak:  # IDs such as FR-HZ-06 and "Figures 3-2" must not wrap at a hyphen
            body_ = '<w:noBreakHyphen/>'.join(
                f'<w:t xml:space="preserve">{esc(x)}</w:t>' for x in ID_HYPHEN.split(t))
        else:
            body_ = f'<w:t xml:space="preserve">{esc(t)}</w:t>'
        out.append(f'<w:r><w:rPr>{props}</w:rPr>{body_}</w:r>')
    return "".join(out)


def body(text, center=False, keep=False):
    jc = "center" if center else "both"
    return ('<w:p><w:pPr>' + ('<w:keepNext/>' if keep else '') + '<w:spacing w:after="0" w:before="240" w:line="360" w:lineRule="auto"/>'
            f'<w:ind w:left="0" w:firstLine="0"/><w:jc w:val="{jc}"/>'
            f'<w:rPr>{FONT}<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:pPr>{runs(text)}</w:p>')


def heading(level, text):
    size = {3: 28, 4: 24}[level]
    return (f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/><w:keepNext/>'
            '<w:spacing w:before="240" w:line="360" w:lineRule="auto"/><w:jc w:val="left"/>'
            f'<w:rPr>{FONT}<w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="{size}"/></w:rPr></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b/><w:bCs/><w:color w:val="000000"/><w:sz w:val="{size}"/>'
            f'<w:szCs w:val="{size}"/></w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def caption(style, text):
    size = 20 if style == "ReportFigureCaption" else 24
    keep = "<w:keepNext/>" if style == "ReportTableCaption" else ""
    return (f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{keep}</w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:b/><w:bCs/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


class Figures:
    def __init__(self):
        self.rels = []
        self.next_id = 5001

    def add(self, png, cap, alt):
        src = PNG / png
        if not src.exists():
            sys.exit(f"missing figure {src}")
        target = f"p5_{png}"
        shutil.copyfile(src, MEDIA / target)
        rid = f"rIdP5Fig{self.next_id}"
        self.rels.append((rid, target))
        w, h = Image.open(src).size
        scale = min(1.0, MAX_W_EMU / (w * EMU_PER_PX), MAX_H_EMU / (h * EMU_PER_PX))
        cx, cy = int(w * EMU_PER_PX * scale), int(h * EMU_PER_PX * scale)
        pid = self.next_id
        self.next_id += 1
        a = html.escape(alt, quote=True)
        drawing = (
            '<w:p><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="0" '
            'w:line="240" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            '<wp:inline distB="0" distT="0" distL="114300" distR="114300">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent b="0" l="0" r="0" t="0"/>'
            f'<wp:docPr descr="{a}" id="{pid}" name="{target}"/>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr descr="{a}" id="{pid}" name="{target}"/>'
            '<pic:cNvPicPr preferRelativeResize="0"/></pic:nvPicPr><pic:blipFill>'
            f'<a:blip r:embed="{rid}"/><a:srcRect b="0" l="0" r="0" t="0"/><a:stretch><a:fillRect/></a:stretch>'
            '</pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/>'
            f'<a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"/><a:ln/></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
        return drawing + caption("ReportFigureCaption", cap)


def box(cap):
    return ('<w:p><w:pPr><w:keepNext/><w:keepLines/><w:pBdr>'
            + "".join(f'<w:{s} w:val="single" w:sz="6" w:space="0" w:color="808080"/>'
                      for s in ("top", "left", "bottom", "right"))
            + '</w:pBdr><w:spacing w:before="150" w:after="95" w:line="1800" w:lineRule="exact"/>'
              '<w:ind w:left="1500" w:right="1500"/></w:pPr></w:p>'
            + caption("ReportFigureCaption", cap))


def table(cap, rows):
    header, data = rows[0], rows[1:]
    n = len(header)
    # Each column is at least as wide as its longest word (IDs such as "NFR-DQ-04"
    # or "resca_readonly" must never break), and the remaining width is shared in
    # proportion to the amount of text in the column.
    def plain(t):
        return re.sub(r"\*\*|\*|_\{|\^\{|\}", "", t)

    def floor(c):
        words = [p for r in rows if c < len(r) for w in plain(r[c]).split()
                 for p in re.split(r"(?<=[a-z])-|/", w)]
        longest = min(max((len(w) for w in words), default=1), 16)
        return longest * 150 + 240
    mins = [floor(c) for c in range(n)]
    if sum(mins) > TEXT_WIDTH_TWIPS:
        mins = [int(m * TEXT_WIDTH_TWIPS / sum(mins)) for m in mins]
    load = [sum(len(plain(r[c])) for r in rows if c < len(r)) + 1 for c in range(n)]
    spare = TEXT_WIDTH_TWIPS - sum(mins)
    widths = [mins[c] + int(spare * load[c] / sum(load)) for c in range(n)]
    border = "".join(f'<w:{s} w:color="d9d9d9" w:space="0" w:sz="5" w:val="single"/>'
                     for s in ("top", "left", "bottom", "right"))

    def cell(text, width, head):
        shade = '<w:shd w:fill="e7e6e6" w:val="clear"/>' if head else ""
        return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/><w:tcBorders>{border}</w:tcBorders>{shade}'
                '<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="80" w:type="dxa"/>'
                '<w:bottom w:w="80" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tcMar>'
                f'<w:vAlign w:val="{"center" if head else "top"}"/></w:tcPr>'
                '<w:p><w:pPr><w:spacing w:before="120" w:after="120" w:line="240" w:lineRule="auto"/>'
                f'<w:jc w:val="left"/></w:pPr>{runs(text, 24, bold=head, nobreak=True)}</w:p></w:tc>')

    out = [caption("ReportTableCaption", cap),
           f'<w:tbl><w:tblPr><w:tblW w:w="{TEXT_WIDTH_TWIPS}" w:type="dxa"/><w:jc w:val="center"/>'
           '<w:tblLayout w:type="fixed"/><w:tblLook w:val="0600"/></w:tblPr><w:tblGrid>'
           + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"]
    out.append('<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>'
               + "".join(cell(header[c], widths[c], True) for c in range(n)) + "</w:tr>")
    for r in data:
        r = r + [""] * (n - len(r))
        out.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>'
                   + "".join(cell(r[c], widths[c], False) for c in range(n)) + "</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)


def convert(md):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    figs = Figures()
    parts = []
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("#### "):
            parts.append(heading(4, line[5:]))
        elif line.startswith("### "):
            parts.append(heading(3, line[4:]))
        elif m := re.fullmatch(r"!fig\[([^|]+)\|([^|]+)\|(.+)\]", line):
            parts.append(figs.add(*m.groups()))
        elif m := re.fullmatch(r"!box\[(.+)\]", line):
            parts.append(box(m.group(1)))
        elif line.startswith("Table: "):
            cap = line[7:]
            rows = []
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            parts.append(table(cap, rows))
            continue
        elif line.startswith("$$ "):
            parts.append(body(line[3:], center=True))
        else:
            nxt = next((l for l in lines[i + 1:] if l.strip()), "")
            parts.append(body(line, keep=len(line) < 400 and nxt.startswith("!fig[")))
        i += 1
    return "".join(parts), figs.rels


def main():
    md = (HERE / "section_3_3.md").read_text(encoding="utf-8")
    xml = DOC_XML.read_text(encoding="utf-8")
    new, rels = convert(md)
    new = f"{START_MARK}{new}{END_MARK}"

    if START_MARK in xml:
        a = xml.index(START_MARK)
        b = xml.index(END_MARK) + len(END_MARK)
    else:
        h = xml.index(">3.3 SYSTEM DESIGN<")
        a = xml.index("</w:p>", h) + len("</w:p>")
        c4 = xml.index(">Chapter Four<", a)
        b = max(xml.rfind("<w:p>", a, c4), xml.rfind("<w:p ", a, c4))
    xml = xml[:a] + new + xml[b:]

    # References: append [27] onwards after the last ReportReference paragraph, once.
    if "[27] Object Management Group" not in xml:
        refs = [m.end() for m in re.finditer(r'<w:pStyle w:val="ReportReference"/>.*?</w:p>', xml, re.S)]
        at = refs[-1]
        ref_xml = "".join(
            '<w:p><w:pPr><w:pStyle w:val="ReportReference"/></w:pPr>'
            f'<w:r><w:rPr>{FONT}<w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr>'
            f'<w:t xml:space="preserve">{esc(r)}</w:t></w:r></w:p>' for r in NEW_REFERENCES)
        xml = xml[:at] + ref_xml + xml[at:]
    DOC_XML.write_text(xml, encoding="utf-8")

    rel_xml = RELS.read_text(encoding="utf-8")
    rel_xml = re.sub(r'<Relationship Id="rIdP5Fig\d+"[^>]*/>', "", rel_xml)
    add = "".join(
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        f'relationships/image" Target="media/{target}"/>' for rid, target in rels)
    RELS.write_text(rel_xml.replace("</Relationships>", add + "</Relationships>"), encoding="utf-8")
    used = {t for _, t in rels}
    for stale in MEDIA.glob("p5_*.png"):
        if stale.name not in used:
            stale.unlink()

    subprocess.run([sys.executable, str(DOCS / "build_docx.py"), "build", str(DOCX)], check=True)
    print(f"Section 3.3 inserted: {len(rels)} figures; DOCX rebuilt at {DOCX}")


if __name__ == "__main__":
    main()
