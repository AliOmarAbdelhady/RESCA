"""Build the Markdown report sections into Main and renumber every citation.

The sections in docs/documentation/sources/ (abstract, Chapter 2, Section 3.1,
Chapter 5 and Appendices A, B and D) are converted to WordprocessingML with the
helpers of chapter5/tools/build_section.py, so they share its typography, table
and caption styles. Each section replaces the text between its heading and the
next one in docs/documentation/main/Project 1 Docs.source, and the previous
insertion is replaced on every run.

Citations are written as [@key] in Markdown (keys in sources/references.md).
After the sections are inserted, every citation in the report, including the
numbered ones that other authors typed in Word, is numbered in order of first
citation and the reference list is rebuilt. Each reference paragraph keeps a
bookmark named ref_<key>, so a later run can tell which source a number means.
Finally the DOCX is rebuilt with build_docx.py.

    python docs/documentation/tools/build_report.py
"""
import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

from lxml import etree
from PIL import Image

DOCS = Path(__file__).resolve().parent.parent
REPO = DOCS.parent.parent
SRC = DOCS / "sources"
DOCX = DOCS / "main" / "Project 1 Docs.docx"
PKG = DOCX.with_suffix(".source") / "package"
DOC_XML = PKG / "word" / "document.xml"
RELS = PKG / "word" / "_rels" / "document.xml.rels"
MEDIA = PKG / "word" / "media"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"

_spec = importlib.util.spec_from_file_location("p5", DOCS / "chapter5" / "tools" / "build_section.py")
p5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(p5)

STAR = ""  # a literal asterisk written as \* in Markdown

# The reference list as numbered before keys were introduced (commit 736ec98).
LEGACY = dict(enumerate(
    "sendai xbd ocha guide guidelines fcn unet resnet efficientnet transformer segformer dinov3 dinov2 "
    "floodnet visdrone heridal bytetrack astar pgrouting nims maxar iso29148 hazus start owasp wcag uml "
    "iso42010 pgrls postgis dijkstra".split(), start=1))

# (name, Markdown source, text of the paragraph after which it starts, text of the paragraph before which it ends)
SECTIONS = [
    ("ABSTRACT", "abstract.md", "ABSTRACT", "TABLE OF CONTENTS"),
    ("CH2", "chapter2.md", "LITERATURE REVIEW AND BACKGROUND", "Chapter Three"),
    ("S31", "section_3_1.md", "3.1 SYSTEM DESCRIPTION", "3.2 USER AND SYSTEM REQUIREMENTS"),
    ("CH5", "chapter5.md", "DISCUSSION, CONCLUSION AND FUTURE WORK", "REFERENCES"),
    ("APPA", None, "Appendix A: Extended Tables", "Appendix B: Contribution Record"),
    ("APPB", "appendix_b.md", "Appendix B: Contribution Record", "Appendix C: SWOT analysis"),
    ("APPD", "appendix_d.md", "Appendix D: Literature Review Shortlist", None),
]


def runs(text, **kw):
    return p5.runs(text.replace("\\*", STAR), **kw).replace(STAR, "*")


def body(text):
    return p5.body(text.replace("\\*", STAR)).replace(STAR, "*")


def heading2(text):
    rpr = f'<w:rPr>{p5.FONT}<w:b/><w:bCs/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>'
    return ('<w:p><w:pPr><w:pStyle w:val="Heading2"/><w:keepNext/><w:numPr><w:ilvl w:val="1"/>'
            '<w:numId w:val="1"/></w:numPr><w:spacing w:before="240" w:line="360" w:lineRule="auto"/>'
            f'<w:ind w:left="580" w:hanging="580"/><w:jc w:val="left"/>{rpr}</w:pPr>'
            f'<w:r>{rpr}<w:t xml:space="preserve">{p5.esc(text)}</w:t></w:r></w:p>')


class Figures:
    """Like build_section.Figures, with its own file prefix and relationship ids."""

    def __init__(self):
        self.rels = []
        self.next_id = 7001

    def add(self, path, cap, alt, max_px=3200):
        target = f"rv_{path.stem}.png"
        image = Image.open(path)
        original_width = image.width
        if image.width > max_px:  # keep the DOCX small; the printed size is unchanged
            image = image.resize((max_px, round(image.height * max_px / image.width)), Image.LANCZOS)
        image.convert("RGB").save(MEDIA / target, optimize=True)
        rid = f"rIdRvFig{self.next_id}"
        self.rels.append((rid, target))
        w, h = image.size
        px_emu = p5.EMU_PER_PX * original_width / w  # figures are drawn at 200 dpi
        scale = min(1.0, p5.MAX_W_EMU / (w * px_emu), p5.MAX_H_EMU / (h * px_emu))
        cx, cy = int(w * px_emu * scale), int(h * px_emu * scale)
        pid = self.next_id
        self.next_id += 1
        a = p5.html.escape(alt, quote=True)
        return (
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
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
            + p5.caption("ReportFigureCaption", cap))


def convert(md, figures, figdirs):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    parts, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("## "):
            parts.append(heading2(line[3:]))
        elif line.startswith("#### "):
            parts.append(p5.heading(4, line[5:]))
        elif line.startswith("### "):
            parts.append(p5.heading(3, line[4:]))
        elif m := re.fullmatch(r"!fig\[([^|]+)\|([^|]+)\|(.+)\]", line):
            name, cap, alt = m.groups()
            path = next((d / name for d in figdirs if (d / name).exists()), None)
            if path is None:
                sys.exit(f"missing figure {name}")
            parts.append(figures.add(path, cap, alt))
        elif m := re.fullmatch(r"!box\[(.+)\]", line):
            parts.append(p5.box(m.group(1)))
        elif line.startswith("Table: "):
            cap, rows = line[7:], []
            i += 1
            while i < len(lines) and lines[i].startswith("|"):
                if not re.fullmatch(r"\|[\s:|-]+\|", lines[i].strip()):
                    rows.append([c.strip().replace("\\*", STAR) for c in lines[i].strip().strip("|").split("|")])
                i += 1
            parts.append(p5.table(cap, rows).replace(STAR, "*"))
            continue
        else:
            parts.append(body(line))
        i += 1
    return "".join(parts)


def appendix_a():
    """Figure A-1 (the full ERD) and the data dictionary as Tables A-1 onwards."""
    md = ["The figures and tables in this appendix extend Section 3.3.3. Figure A-1 shows all 56 tables "
          "of the logical design and their 140 relationships on one page; the per-domain diagrams in Figures "
          "3-6 to 3-14 show the same tables at a readable scale. The full-resolution diagram and its editable "
          "draw.io source are kept in the project repository (folder mahmoudERD). Tables A-1 onwards list the "
          "columns of every table, generated from the implemented database schema. Null states whether the "
          "column accepts empty values; PK marks the primary key, UQ a unique column and FK a foreign key with "
          "its target table.",
          "!fig[page-01.png|Figure A-1: Full entity-relationship diagram of the RescueVision database|"
          "Entity-relationship diagram of all 56 tables and 140 relationships, grouped into nine subject areas: "
          "identity and access, incidents and operations, imagery and analysis, buildings and cost, roads and "
          "routing, persons and cases, hazards and alerts, citizens and media, and field channel, reports and audit.]"]
    dictionary = (DOCS / "chapter5" / "appendix_data_dictionary.md").read_text(encoding="utf-8")
    n, domain = 0, ""
    for block in re.split(r"\n(?=## |### )", dictionary):
        head, _, rest = block.partition("\n")
        if head.startswith("## "):
            domain = head[3:].strip()
            md.append(f"### {domain}")
        elif head.startswith("### "):
            n += 1
            rows = [l.replace("`", "") for l in rest.splitlines() if l.startswith("|")]
            md.append(f"Table: Table A-{n}: Columns of the {head[4:].strip()} table")
            md.extend(rows)
    return "\n\n".join(md[:2]) + "\n\n" + "\n".join(md[2:])


def find_para(xml, text, start=0):
    """Start and end offsets of the first paragraph at or after start whose text node is exactly text."""
    k = xml.index(f">{text}<", start)
    a = max(xml.rfind("<w:p>", 0, k), xml.rfind("<w:p ", 0, k))
    return a, xml.index("</w:p>", k) + len("</w:p>")


def insert_sections(xml):
    figures = Figures()
    figdirs = [SRC / "figures", REPO / "mahmoudERD" / "png"]
    after_front = xml.index(">LIST OF ACRONYMS/ABBREVIATIONS<")
    for name, source, start_text, end_text in SECTIONS:
        md = appendix_a() if name == "APPA" else (SRC / source).read_text(encoding="utf-8")
        new = f"<!-- RV:{name}:START -->{convert(md, figures, figdirs)}<!-- RV:{name}:END -->"
        sm, em = f"<!-- RV:{name}:START -->", f"<!-- RV:{name}:END -->"
        if sm in xml:
            a, b = xml.index(sm), xml.index(em) + len(em)
        else:
            from_ = 0 if name == "ABSTRACT" else after_front
            a = find_para(xml, start_text, from_)[1]
            if end_text is None:
                b = xml.rindex("<w:sectPr")
            else:
                b = find_para(xml, end_text, a)[0]
        xml = xml[:a] + new + xml[b:]
    return xml, figures.rels


# ---------------------------------------------------------------- citations

def para_text_nodes(p):
    return [t for t in p.iter(W + "t")]


def sub_para(p, pattern, repl):
    """Regex substitution over a paragraph's text that keeps the runs and their formatting."""
    nodes = para_text_nodes(p)
    full = "".join(t.text or "" for t in nodes)
    matches = list(pattern.finditer(full))
    if not matches:
        return 0
    spans, pos = [], 0
    for t in nodes:
        spans.append((pos, pos + len(t.text or "")))
        pos += len(t.text or "")
    for m in reversed(matches):
        new, (s, e), first = repl(m), m.span(), True
        for t, (a, b) in zip(nodes, spans):
            if b <= s or a >= e:
                continue
            txt = t.text or ""
            lo, hi = max(s, a) - a, min(e, b) - a
            t.text = txt[:lo] + (new if first else "") + txt[hi:]
            t.set(XML_NS + "space", "preserve")
            first = False
    return len(matches)


def load_references():
    refs = {}
    for line in (SRC / "references.md").read_text(encoding="utf-8").splitlines():
        if m := re.fullmatch(r"([a-z0-9]+) \| (.+)", line.strip()):
            refs[m.group(1)] = m.group(2)
    return refs


def renumber(root, refs):
    body_ = root.find(W + "body")
    paragraphs = list(body_.iter(W + "p"))

    def style(p):
        s = p.find(f"{W}pPr/{W}pStyle")
        return s.get(W + "val") if s is not None else ""

    ref_paras = [p for p in paragraphs if style(p) == "ReportReference"]
    current = {}
    for p in ref_paras:
        text = "".join(t.text or "" for t in para_text_nodes(p))
        m = re.match(r"\[(\d+)\]", text)
        bm = p.find(W + "bookmarkStart")
        if m and bm is not None and bm.get(W + "name", "").startswith("ref_"):
            current[int(m.group(1))] = bm.get(W + "name")[4:]
    if not current:
        current = LEGACY

    num = re.compile(r"\[(\d+)\]")
    key = re.compile(r"\[@([a-z0-9]+)\]")
    order, missing = [], set()
    for p in paragraphs:
        if style(p) == "ReportReference":
            continue
        sub_para(p, num, lambda m: f"[@{current[int(m.group(1))]}]" if int(m.group(1)) in current else m.group(0))
        for m in key.finditer("".join(t.text or "" for t in para_text_nodes(p))):
            k = m.group(1)
            if k not in refs:
                missing.add(k)
            elif k not in order:
                order.append(k)
    if missing:
        sys.exit(f"cited keys missing from references.md: {', '.join(sorted(missing))}")
    number = {k: i for i, k in enumerate(order, start=1)}
    for p in paragraphs:
        if style(p) != "ReportReference":
            sub_para(p, key, lambda m: f"[{number[m.group(1)]}]")

    heading = next(p for p in paragraphs if style(p) == "Heading1"
                   and "".join(t.text or "" for t in para_text_nodes(p)).strip() == "REFERENCES")
    for p in ref_paras:
        p.getparent().remove(p)
    anchor = heading
    for i, k in enumerate(order, start=1):
        xml = (f'<w:p xmlns:w="{W[1:-1]}"><w:pPr><w:pStyle w:val="ReportReference"/></w:pPr>'
               f'<w:bookmarkStart w:id="{90000 + i}" w:name="ref_{k}"/><w:bookmarkEnd w:id="{90000 + i}"/>'
               f'{runs(f"[{i}] {refs[k]}")}</w:p>')
        new = etree.fromstring(xml)
        anchor.addnext(new)
        anchor = new
    unused = sorted(set(refs) - set(order))
    return len(order), unused


def main():
    xml = DOC_XML.read_text(encoding="utf-8").replace("\r\n", "\n")
    xml, rels = insert_sections(xml)

    root = etree.fromstring(xml.encode("utf-8"))
    count, unused = renumber(root, load_references())
    out = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    DOC_XML.write_bytes(out)

    rel_xml = RELS.read_text(encoding="utf-8")
    rel_xml = re.sub(r'<Relationship Id="rIdRvFig\d+"[^>]*/>', "", rel_xml)
    add = "".join(
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
        f'relationships/image" Target="media/{target}"/>' for rid, target in rels)
    RELS.write_text(rel_xml.replace("</Relationships>", add + "</Relationships>"), encoding="utf-8")
    used = {t for _, t in rels}
    for stale in MEDIA.glob("rv_*.png"):
        if stale.name not in used:
            stale.unlink()

    subprocess.run([sys.executable, str(DOCS / "build_docx.py"), "build", str(DOCX)], check=True)
    print(f"{len(SECTIONS)} sections and {len(rels)} figures inserted; {count} references numbered.")
    if unused:
        print("Not cited, left out of the list:", ", ".join(unused))


if __name__ == "__main__":
    main()
