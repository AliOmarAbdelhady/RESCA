#!/usr/bin/env python3
"""Generate a multi-page, publication-quality draw.io ERD for RESCA.

Usage: python3 -I gen_erd.py <schema_dir> <out.drawio>
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).parent))
from parse_schema import parse  # noqa: E402

SCHEMA = Path(sys.argv[1])
OUT = Path(sys.argv[2])
COMMIT = sys.argv[3] if len(sys.argv) > 3 else ""

tables, fks, order = parse(SCHEMA)
ENUMS = set(re.findall(r"CREATE TYPE (\w+)\s+AS ENUM", (SCHEMA / "01_types.sql").read_text()))

# ---------------------------------------------------------------- domains
DOMAINS = [
    ("D1", "Identity & Access", "#1F5FAD", "#EDF3FB",
     "Agencies, roles & permissions, users, sessions, devices, teams and vehicles.",
     ["agencies", "roles", "permissions", "role_permissions", "users", "user_sessions",
      "user_devices", "teams", "team_members", "vehicles"]),
    ("D2", "Incidents & Operations", "#B3261E", "#FCEFEE",
     "One shared incident per disaster (ICS). Lead agency invites others; each agency runs its own missions.",
     ["incidents", "incident_agencies", "zones", "missions", "mission_assignments", "mission_status_history"]),
    ("D3", "Imagery & AI Pipeline", "#6B3FA0", "#F4EFFA",
     "Provenance backbone: every AI output traces back to an inference run, its model version and input imagery.",
     ["capture_sessions", "images", "ai_models", "processing_jobs", "raster_products", "inference_runs"]),
    ("D4a", "Buildings, Damage & Cost", "#7A5230", "#F6F0EA",
     "F1 · cost = floor area × unit rate(occupancy, construction) × repair ratio(damage grade), as a low–high range.",
     ["buildings", "building_assessments", "cost_profiles", "cost_profile_unit_rates",
      "cost_profile_repair_ratios", "cost_estimates"]),
    ("D4b", "Road Network & Routing", "#3F5566", "#EEF1F4",
     "F2 · pgRouting edge graph, road condition observations and computed rescue routes.",
     ["road_nodes", "road_segments", "road_condition_observations", "routes", "route_segments"]),
    ("D4c", "Persons & Assistance Cases", "#2E7D32", "#EDF6EE",
     "F3/F4 · AI detection → track (same person across frames) → assistance case a human decided needs help.",
     ["person_tracks", "person_detections", "facilities", "assistance_cases", "case_events"]),
    ("D4d", "Hazards & Compound Alerts", "#D35400", "#FEF3EA",
     "F5 · Hazards + infrastructure feed a rule engine; interacting hazards open compound alerts that close roads.",
     ["infrastructure_assets", "hazards", "hazard_rules", "compound_alerts",
      "compound_alert_sources", "alert_closed_segments"]),
    ("D5a", "Citizens & Media", "#00796B", "#E8F5F3",
     "Public citizen app: verified phone identities, uploaded media and help requests auto-matched to incidents.",
     ["citizens", "media_files", "citizen_requests", "citizen_request_media"]),
    ("D5b", "Field Channel, Reports & Audit", "#A3195B", "#FBEEF4",
     "Live GPS (partitioned), SOS, notifications, reports, similar-case embeddings and the audit trail (partitioned).",
     ["responder_positions", "responder_last_positions", "sos_alerts", "notifications",
      "reports", "report_shares", "image_embeddings", "audit_log"]),
]
DOM = {d[0]: d for d in DOMAINS}
TDOM = {t: d[0] for d in DOMAINS for t in d[5]}
assert set(TDOM) == set(tables), set(tables) ^ set(TDOM)

FONT = "Helvetica"
MONO = "Courier New"
ROW_H = 22
HDR_H = 32
INK = "#1D2733"
MUTED = "#6B7785"
GRID = "#D5DBE3"
PK_C = "#B7791F"
FK_C = "#2563A8"
AK_C = "#7A4BB0"

# ---------------------------------------------------------------- helpers
fk_by_col = {(f.table, f.column): f for f in fks}
fks_by_table = defaultdict(list)
for f in fks:
    fks_by_table[f.table].append(f)


def x(s: str) -> str:
    return escape(s, {'"': "&quot;", "\n": "&#xa;"})


def key_label(t, c) -> str:
    parts = []
    if c.pk:
        parts.append("PK")
    if (t.name, c.name) in fk_by_col:
        parts.append("FK")
    for n in c.ak:
        parts.append(f"AK{n}")
    return " ".join(parts)


def type_label(c) -> str:
    s = c.type
    if c.generated == "identity":
        s += " ID"
    elif c.generated == "stored":
        s += " GEN"
    return s


def ordered_cols(t, keys_only=False, only=None):
    cols = [c for c in t.columns if c.pk] + [c for c in t.columns if not c.pk]
    if only is not None:
        cols = [c for c in cols if c.pk or c.name in only]
    elif keys_only:
        cols = [c for c in cols if c.pk or (t.name, c.name) in fk_by_col or c.ak]
    return cols


def text_w(s: str, px: float) -> float:
    w = 0.0
    for ch in s:
        if ch in "il.,:;'|!()[] ":
            w += px * 0.30
        elif ch in "mwMW":
            w += px * 0.86
        elif ch.isupper() or ch in "_":
            w += px * 0.66
        else:
            w += px * 0.56
    return w


class Box:
    """A positioned table."""

    def __init__(self, t, cols, stub=False):
        self.t, self.cols, self.stub = t, cols, stub
        self.key_w = 56 if any(len(key_label(t, c)) > 6 for c in cols) else 44
        self.name_w = max([text_w(c.name, 11) + 18 for c in cols] + [60])
        self.type_w = max([len(type_label(c)) * 6.05 + 16 for c in cols] + [50])
        self.nn_w = 30
        self.w = round(max(self.key_w + self.name_w + self.type_w + self.nn_w,
                           text_w(t.name, 13) * 1.12 + 40))
        if self.w > self.key_w + self.name_w + self.type_w + self.nn_w:
            self.type_w = self.w - self.key_w - self.name_w - self.nn_w
        self.h = HDR_H + ROW_H * len(cols)
        self.x = self.y = 0.0

    def row_y(self, col):
        names = [c.name for c in self.cols]
        return self.y + HDR_H + ROW_H * names.index(col) + ROW_H / 2

    def has(self, col):
        return any(c.name == col for c in self.cols)

    @property
    def cx(self):
        return self.x + self.w / 2


# ---------------------------------------------------------------- XML emitters
class Page:
    def __init__(self, pid, name):
        self.pid, self.name = pid, name
        self.bg, self.edges, self.fg = [], [], []
        self.n = 0
        self.maxx = self.maxy = 0

    def nid(self, p="c"):
        self.n += 1
        return f"{self.pid}-{p}{self.n}"

    def track(self, x0, y0, w, h):
        self.maxx = max(self.maxx, x0 + w)
        self.maxy = max(self.maxy, y0 + h)

    def rect(self, x0, y0, w, h, style, value="", layer="bg", tooltip=None):
        i = self.nid("r")
        geo = f'<mxGeometry x="{x0:.0f}" y="{y0:.0f}" width="{w:.0f}" height="{h:.0f}" as="geometry"/>'
        if tooltip:
            cell = (f'<UserObject label="{x(value)}" tooltip="{x(tooltip)}" id="{i}">'
                    f'<mxCell style="{style}" vertex="1" parent="1">{geo}</mxCell></UserObject>')
        else:
            cell = f'<mxCell id="{i}" value="{x(value)}" style="{style}" vertex="1" parent="1">{geo}</mxCell>'
        getattr(self, layer).append(cell)
        self.track(x0, y0, w, h)
        return i

    def text(self, x0, y0, w, h, value, size=11, color=INK, bold=False, italic=False,
             align="left", layer="fg", valign="middle", extra=""):
        fs = (1 if bold else 0) | (2 if italic else 0)
        st = (f"text;html=1;strokeColor=none;fillColor=none;align={align};verticalAlign={valign};"
              f"whiteSpace=wrap;overflow=hidden;fontFamily={FONT};fontSize={size};fontColor={color};"
              f"fontStyle={fs};spacing=0;{extra}")
        return self.rect(x0, y0, w, h, st, value, layer)

    def table(self, b: Box, color, show_domain_tag=None):
        t = b.t
        tid = f"{self.pid}-t-{t.name}"
        if b.stub:
            st = (f"shape=table;startSize={HDR_H};container=1;collapsible=0;childLayout=tableLayout;"
                  f"fixedRows=1;rowLines=0;fontStyle=1;align=left;spacingLeft=10;resizeLast=1;html=1;"
                  f"fillColor={color};strokeColor={color};fontColor=#FFFFFF;fontSize=12;fontFamily={FONT};"
                  f"swimlaneFillColor=#FFFFFF;dashed=1;dashPattern=4 3;opacity=100;textOpacity=100;"
                  f"fillOpacity=55;strokeOpacity=100;")
        else:
            st = (f"shape=table;startSize={HDR_H};container=1;collapsible=0;childLayout=tableLayout;"
                  f"fixedRows=1;rowLines=0;fontStyle=1;align=left;spacingLeft=10;resizeLast=1;html=1;"
                  f"fillColor={color};strokeColor={color};fontColor=#FFFFFF;fontSize=13;fontFamily={FONT};"
                  f"swimlaneFillColor=#FFFFFF;shadow=0;strokeWidth=1.2;")
        tip = [f"{t.name}  ·  {DOM[TDOM[t.name]][0]} {DOM[TDOM[t.name]][1]}",
               f"source: database/schema/{t.file}"]
        if t.partition:
            tip.append(f"PARTITION BY {t.partition}, monthly partitions")
        if t.checks:
            tip.append("CHECK: " + ", ".join(t.checks))
        if t.unique_indexes:
            tip.append("UNIQUE INDEX: " + "; ".join(t.unique_indexes))
        label = t.name if not b.stub else f"{t.name}"
        out = [f'<UserObject label="{x(label)}" tooltip="{x(chr(10).join(tip))}" id="{tid}">'
               f'<mxCell style="{st}" vertex="1" parent="1">'
               f'<mxGeometry x="{b.x:.0f}" y="{b.y:.0f}" width="{b.w}" height="{b.h}" as="geometry"/>'
               f'</mxCell></UserObject>']
        npk = sum(1 for c in b.cols if c.pk)
        for ri, c in enumerate(b.cols):
            rid = f"{tid}--{c.name}"
            sep = 1 if (c.pk and ri == npk - 1 and ri < len(b.cols) - 1) else 0
            zebra = "#F6F8FB" if ri % 2 else "#FFFFFF"
            rst = (f"shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;"
                   f"fillColor={zebra};collapsible=0;dropTarget=0;points=[[0,0.5],[1,0.5]];"
                   f"portConstraint=eastwest;top=0;left=0;right=0;bottom={sep};strokeColor={color};"
                   f"strokeWidth={1.2 if sep else 0};html=1;")
            fk = fk_by_col.get((t.name, c.name))
            rtip = [f"{t.name}.{c.name} : {c.type}" + ("  NOT NULL" if c.not_null else "  NULL")]
            if c.generated == "identity":
                rtip.append("GENERATED ALWAYS AS IDENTITY")
            elif c.generated == "stored":
                rtip.append("GENERATED ALWAYS AS (…) STORED")
            if c.default:
                rtip.append(f"DEFAULT {c.default}")
            if fk:
                rtip.append(f"→ {fk.ref_table}.{fk.ref_column}  ON DELETE {fk.on_delete}")
            if c.comment:
                rtip.append(f"“{c.comment}”")
            out.append(f'<UserObject label="" tooltip="{x(chr(10).join(rtip))}" id="{rid}">'
                       f'<mxCell style="{rst}" vertex="1" parent="{tid}">'
                       f'<mxGeometry y="{HDR_H + ri * ROW_H}" width="{b.w}" height="{ROW_H}" as="geometry"/>'
                       f'</mxCell></UserObject>')
            kl = key_label(t, c)
            kcol = PK_C if c.pk else (FK_C if "FK" in kl else AK_C)
            name_style = 5 if c.pk else 0  # bold+underline for PK
            ctype = type_label(c)
            is_enum = c.type in ENUMS
            tcol = AK_C if is_enum else ("#2F7A4F" if c.type.startswith(("geometry", "vector")) else MUTED)
            cells = [
                (kl, b.key_w, f"fontColor={kcol};fontStyle=1;fontSize=9.5;align=center;spacingLeft=0;"),
                (c.name, b.name_w, f"fontColor={INK};fontStyle={name_style};fontSize=11;align=left;spacingLeft=4;"),
                (ctype, b.type_w, f"fontColor={tcol};fontStyle={2 if is_enum else 0};fontSize=10;"
                                  f"fontFamily={MONO};align=left;spacingLeft=4;"),
                ("NN" if c.not_null and not c.pk else "", b.nn_w,
                 f"fontColor={MUTED};fontStyle=1;fontSize=8.5;align=center;spacingLeft=0;"),
            ]
            xx = 0
            for ci, (val, w, sx) in enumerate(cells):
                w = round(w) if ci < 3 else b.w - xx
                cst = (f"shape=partialRectangle;connectable=0;fillColor=none;top=0;left=0;bottom=0;"
                       f"right=0;overflow=hidden;whiteSpace=nowrap;html=1;fontFamily={FONT};"
                       f"verticalAlign=middle;{sx}")
                out.append(f'<mxCell id="{rid}-{ci}" value="{x(val)}" style="{cst}" vertex="1" parent="{rid}">'
                           f'<mxGeometry x="{xx}" width="{w}" height="{ROW_H}" as="geometry">'
                           f'<mxRectangle width="{w}" height="{ROW_H}" as="alternateBounds"/></mxGeometry></mxCell>')
                xx += w
        self.fg.extend(out)
        self.track(b.x, b.y, b.w, b.h)
        if t.partition and not b.stub:
            self.text(b.x, b.y + b.h + 3, b.w, 16,
                      f"⊞ partitioned by {t.partition.lower().replace('range', 'range')} · monthly",
                      size=9.5, color=MUTED, italic=True)
        if show_domain_tag:
            d = DOM[TDOM[t.name]]
            self.text(b.x, b.y - 17, b.w, 15, f"{d[0]} · {d[1]}  ·  p.{[x[0] for x in DOMAINS].index(d[0]) + 2:02d}", size=9.5, color=color, italic=True)

    def edge(self, f, src_id, dst_id, color, exit_x, entry_x, points=(), width=1.3,
             opacity=100, child_unique=False, entry_y=0.5):
        c = tables[f.table].col(f.column)
        parent_end = "ERmandOne" if c.not_null else "ERzeroToOne"
        child_end = "ERzeroToOne" if child_unique else "ERzeroToMany"
        es = "edgeStyle=none;" if points else "edgeStyle=orthogonalEdgeStyle;"
        st = (f"{es}rounded=1;arcSize=10;orthogonalLoop=1;html=1;"
              f"endArrow={parent_end};endFill=0;endSize=9;startArrow={child_end};startFill=0;startSize=9;"
              f"strokeColor={color};strokeWidth={width};opacity={opacity};jumpStyle=arc;jumpSize=7;"
              f"exitX={exit_x};exitY=0.5;exitDx=0;exitDy=0;exitPerimeter=0;"
              f"entryX={entry_x:.3f};entryY={entry_y};entryDx=0;entryDy=0;entryPerimeter=0;")
        card = ("1" if c.not_null else "0..1") + " : " + ("0..1" if child_unique else "0..*")
        tip = (f"{f.table}.{f.column} → {f.ref_table}.{f.ref_column}\n"
               f"cardinality (parent : child) {card}\nON DELETE {f.on_delete}")
        pts = "".join(f'<mxPoint x="{px:.0f}" y="{py:.0f}"/>' for px, py in points)
        arr = f'<Array as="points">{pts}</Array>' if points else ""
        i = self.nid("e")
        self.edges.append(
            f'<UserObject label="" tooltip="{x(tip)}" id="{i}">'
            f'<mxCell style="{st}" edge="1" parent="1" source="{src_id}" target="{dst_id}">'
            f'<mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell></UserObject>')

    def xml(self):
        w, h = self.maxx + 80, self.maxy + 80
        cells = "".join(self.bg + self.edges + self.fg)
        return (f'<diagram id="{self.pid}" name="{x(self.name)}">'
                f'<mxGraphModel dx="1400" dy="900" grid="0" gridSize="10" guides="1" tooltips="1" '
                f'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{w:.0f}" '
                f'pageHeight="{h:.0f}" background="#FFFFFF" math="0" shadow="0">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{cells}</root></mxGraphModel></diagram>')


def unique_fk(f):
    c = tables[f.table].col(f.column)
    t = tables[f.table]
    pk_cols = [k for k in t.columns if k.pk]
    if c.pk and len(pk_cols) == 1:
        return True
    return any(len([k for k in t.columns if n in k.ak]) == 1 for n in c.ak)


# ---------------------------------------------------------------- layered layout
def layered(names, boxes, gap_x=150, gap_y=46, max_col_h=1500, x0=0.0, y0=0.0):
    """Parents to the left; children aligned to the parent row they reference."""
    s = set(names)
    parents = {n: {f.ref_table for f in fks_by_table[n] if f.ref_table in s and f.ref_table != n}
               for n in names}
    # break cycles (raster_products <-> inference_runs): drop the edge added via ALTER
    if "raster_products" in s and "inference_runs" in s:
        parents["raster_products"].discard("inference_runs")
    rank = {}

    def r(n, seen=()):
        if n in rank:
            return rank[n]
        ps = [p for p in parents[n] if p not in seen]
        rank[n] = 0 if not ps else 1 + max(r(p, seen + (n,)) for p in ps)
        return rank[n]

    for n in names:
        r(n)
    layers = defaultdict(list)
    for n in names:
        layers[rank[n]].append(n)
    # split over-tall layers into sub-columns
    cols = []
    for k in sorted(layers):
        cur, h = [], 0
        for n in layers[k]:
            if cur and h + boxes[n].h > max_col_h:
                cols.append(cur)
                cur, h = [], 0
            cur.append(n)
            h += boxes[n].h + gap_y
        cols.append(cur)
    # x positions
    xx = x0
    col_of = {}
    col_bounds = []
    for ci, col in enumerate(cols):
        w = max(boxes[n].w for n in col)
        for n in col:
            boxes[n].x = xx + (w - boxes[n].w) / 2 if False else xx
            col_of[n] = ci
        col_bounds.append((xx, xx + w))
        xx += w + gap_x
    # y positions: column 0 stacked, then align children to their parents' rows
    for ci, col in enumerate(cols):
        want = {}
        for n in col:
            ys = []
            for f in fks_by_table[n]:
                if f.ref_table in s and f.ref_table != n and col_of.get(f.ref_table, 99) < ci:
                    pb = boxes[f.ref_table]
                    ys.append(pb.row_y(f.ref_column) - (HDR_H + ROW_H * [c.name for c in boxes[n].cols].index(f.column) + ROW_H / 2))
            want[n] = sum(ys) / len(ys) if ys else None
        # keep input order for unanchored, sort anchored by wanted y
        seq = sorted(col, key=lambda n: (want[n] if want[n] is not None else 1e9 + col.index(n)))
        y = y0
        for n in seq:
            target = want[n] if want[n] is not None else y
            boxes[n].y = max(y, target, y0)
            y = boxes[n].y + boxes[n].h + gap_y + (20 if boxes[n].t.partition else 0)
    return col_of, col_bounds


# ---------------------------------------------------------------- pages
pages = []


def header_band(p, x0, y0, w, title, subtitle, color):
    p.rect(x0, y0, 8, 64, f"rounded=0;fillColor={color};strokeColor=none;", layer="fg")
    p.text(x0 + 22, y0, w, 36, title, size=24, bold=True, color=INK)
    p.text(x0 + 22, y0 + 36, w, 28, subtitle, size=12.5, color=MUTED)


def legend(p, x0, y0):
    w, h = 330, 286
    p.rect(x0, y0, w, h, f"rounded=1;arcSize=3;fillColor=#FFFFFF;strokeColor={GRID};", layer="bg")
    p.text(x0 + 16, y0 + 10, w - 32, 22, "NOTATION", size=11, bold=True, color=INK,
           extra="fontStyle=1;spacingLeft=0;")
    rows = [("PK", PK_C, "Primary key (bold, underlined)"),
            ("FK", FK_C, "Foreign key"),
            ("AK1", AK_C, "Alternate key / UNIQUE (n = constraint group)"),
            ("NN", MUTED, "NOT NULL"),
            ("enum", AK_C, "Enumerated type (italic)"),
            ("geom", "#2F7A4F", "PostGIS geometry / pgvector type"),
            ("ID · GEN", MUTED, "Identity column · generated stored column")]
    yy = y0 + 38
    for k, c, d in rows:
        p.text(x0 + 16, yy, 60, 18, k, size=9.5, bold=True, color=c, align="center")
        p.text(x0 + 84, yy, w - 100, 18, d, size=10, color=INK)
        yy += 20
    yy += 6
    ends = [("ERmandOne", "Exactly one (FK NOT NULL)"),
            ("ERzeroToOne", "Zero or one (FK nullable / unique)"),
            ("ERzeroToMany", "Zero or many")]
    for sym, d in ends:
        a = p.rect(x0 + 16, yy + 4, 2, 10, "fillColor=none;strokeColor=none;", layer="fg")
        b = p.rect(x0 + 70, yy + 4, 2, 10, "fillColor=none;strokeColor=none;", layer="fg")
        i = p.nid("e")
        p.edges.append(f'<mxCell id="{i}" style="endArrow={sym};endFill=0;endSize=10;startArrow=none;'
                       f'html=1;strokeColor={INK};strokeWidth=1.3;" edge="1" parent="1" source="{a}" target="{b}">'
                       f'<mxGeometry relative="1" as="geometry"/></mxCell>')
        p.text(x0 + 84, yy, w - 100, 18, d, size=10, color=INK)
        yy += 22
    p.text(x0 + 16, yy + 2, w - 32, 30,
           "Hover any table, column or relationship for DDL details (ON DELETE, defaults, CHECKs).",
           size=9, color=MUTED, italic=True, valign="top")


# ---------- Page: cover
def cover():
    p = Page("cover", "00 · Overview & Legend")
    header_band(p, 40, 40, 1500, "RESCA · Database Entity-Relationship Model",
                f"PostgreSQL 18 · PostGIS 3.6 · pgRouting 4.0 · pgvector 0.8   —   {len(tables)} tables · "
                f"{len(fks)} foreign keys · {len(ENUMS)} enum types · {len(DOMAINS)} subject areas   —   "
                f"generated from database/schema{(' @ ' + COMMIT) if COMMIT else ''}", "#1D2733")
    # domain cards
    cw, ch, gx, gy = 410, 250, 28, 28
    x0, y0 = 40, 140
    for i, (k, name, col, tint, desc, tl) in enumerate(DOMAINS):
        cx = x0 + (i % 3) * (cw + gx)
        cy = y0 + (i // 3) * (ch + gy)
        p.rect(cx, cy, cw, ch, f"rounded=1;arcSize=3;fillColor={tint};strokeColor={col};strokeWidth=1.2;", layer="bg")
        p.rect(cx, cy, cw, 40, f"rounded=1;arcSize=12;fillColor={col};strokeColor={col};", layer="fg")
        p.rect(cx, cy + 20, cw, 20, f"rounded=0;fillColor={col};strokeColor={col};", layer="fg")
        p.text(cx + 14, cy, cw - 80, 40, f"{k} · {name}", size=13.5, bold=True, color="#FFFFFF")
        p.text(cx + cw - 76, cy, 62, 40, f"{len(tl)} tables", size=10.5, color="#FFFFFF", align="right")
        p.text(cx + 14, cy + 48, cw - 28, 44, desc, size=10, color=INK, italic=True, valign="top")
        half = (len(tl) + 1) // 2
        for j, tn in enumerate(tl):
            colx = cx + 14 + (j // half) * (cw / 2 - 8)
            p.text(colx, cy + 98 + (j % half) * 21, cw / 2 - 20, 18, f"▪ {tn}", size=10.5, color=INK,
                   extra=f"fontFamily={MONO};")
    # dependency matrix
    mx, my = x0 + 3 * (cw + gx) + 20, y0
    keys = [d[0] for d in DOMAINS]
    cnt = defaultdict(int)
    for f in fks:
        cnt[(TDOM[f.table], TDOM[f.ref_table])] += 1
    cs = 46
    p.text(mx, my - 2, 600, 22, "CROSS-DOMAIN DEPENDENCIES", size=11, bold=True)
    p.text(mx, my + 18, 600, 18, "Number of foreign keys from the child domain (row) to the parent domain (column)",
           size=9.5, color=MUTED, italic=True)
    gx0, gy0 = mx + 60, my + 50
    mxv = max(cnt.values())
    for j, k in enumerate(keys):
        p.text(gx0 + j * cs, gy0, cs, 22, k, size=10, bold=True, color=DOM[k][2], align="center")
    for i, rk in enumerate(keys):
        p.text(mx, gy0 + 24 + i * cs, 56, cs, rk, size=10, bold=True, color=DOM[rk][2], align="right")
        for j, ck in enumerate(keys):
            v = cnt.get((rk, ck), 0)
            if i == j:
                fill = "#E9EDF2"
            elif v:
                a = 0.15 + 0.85 * (v / mxv)
                fill = DOM[ck][2]
            else:
                fill = "#FFFFFF"
            op = f"fillOpacity={int((0.15 + 0.85 * v / mxv) * 100)};" if v and i != j else ""
            p.rect(gx0 + j * cs, gy0 + 24 + i * cs, cs, cs,
                   f"rounded=0;fillColor={fill};strokeColor=#FFFFFF;strokeWidth=2;{op}"
                   f"fontFamily={FONT};fontSize=12;fontStyle=1;fontColor={'#FFFFFF' if v / mxv > 0.45 and i != j else INK};",
                   value=str(v) if v else "", layer="fg")
    p.text(mx, gy0 + 24 + len(keys) * cs + 8, cs * 9 + 60, 30,
           "Diagonal = FKs inside the same domain. Identity (D1) and Incidents (D2) are the shared backbone.",
           size=9.5, color=MUTED, italic=True, valign="top")
    legend(p, mx + 60 + cs * 9 + 40, my)
    pages_index = ["01 · Full ERD — all tables & relationships"] + \
                  [f"{i + 2:02d} · {d[0]} {d[1]}" for i, d in enumerate(DOMAINS)]
    p.text(mx + 60 + cs * 9 + 40, my + 300, 330, 22, "PAGES", size=11, bold=True)
    for i, s in enumerate(pages_index):
        p.text(mx + 60 + cs * 9 + 40, my + 324 + i * 19, 330, 18, s, size=10, color=INK)
    return p


# ---------- Page: full ERD
def full_erd():
    p = Page("full", "01 · Full ERD")
    header_band(p, 40, 40, 2000, "RESCA · Full Entity-Relationship Diagram",
                f"All {len(tables)} tables and {len(fks)} relationships grouped by subject area. "
                "Links into users / incidents (shared backbone) are drawn lighter.", "#1D2733")
    boxes = {n: Box(tables[n], ordered_cols(tables[n])) for n in tables}
    rows = [["D1", "D2", "D5a", "D3"], ["D4a", "D4b", "D4c"], ["D4d", "D5b"]]
    pad, title_h = 36, 44
    y = 150
    for row in rows:
        xcur = 40
        rowh = 0
        for k in row:
            d = DOM[k]
            col_of, cb = layered(d[5], boxes, gap_x=110, gap_y=40, max_col_h=1250,
                                 x0=xcur + pad, y0=y + title_h + pad)
            bx1 = max(boxes[n].x + boxes[n].w for n in d[5]) + pad
            by1 = max(boxes[n].y + boxes[n].h + (20 if boxes[n].t.partition else 0) for n in d[5]) + pad
            p.rect(xcur, y, bx1 - xcur, by1 - y,
                   f"rounded=1;arcSize=1;fillColor={d[3]};strokeColor={d[2]};strokeWidth=1.5;dashed=0;", layer="bg")
            p.text(xcur + 18, y + 8, bx1 - xcur - 36, 30, f"{k} · {d[1]}", size=17, bold=True, color=d[2], layer="bg")
            rowh = max(rowh, by1 - y)
            xcur = bx1 + 70
        y += rowh + 70
    for n in tables:
        p.table(boxes[n], DOM[TDOM[n]][2])
    for f in fks:
        cb, pb = boxes[f.table], boxes[f.ref_table]
        src = f"{p.pid}-t-{f.table}--{f.column}"
        dst = f"{p.pid}-t-{f.ref_table}--{f.ref_column}"
        backbone = f.ref_table in ("users", "incidents") and TDOM[f.table] != TDOM[f.ref_table]
        color = "#9AA5B1" if backbone else DOM[TDOM[f.ref_table]][2]
        if f.table == f.ref_table:
            ex, en = 1, 1
        elif pb.x + pb.w < cb.x:
            ex, en = 0, 1
        elif cb.x + cb.w < pb.x:
            ex, en = 1, 0
        else:
            ex = en = 0 if pb.cx < cb.cx else 1
        p.edge(f, src, dst, color, ex, en, width=1.0 if backbone else 1.4,
               opacity=70 if backbone else 100, child_unique=unique_fk(f))
    legend(p, p.maxx + 60, 150)
    return p


# ---------- Domain pages
def domain_page(idx, d):
    k, name, color, tint, desc, tl = d
    p = Page(f"p{k}", f"{idx:02d} · {k} {name}")
    s = set(tl)
    ext_refs = defaultdict(set)
    for n in tl:
        for f in fks_by_table[n]:
            if f.ref_table not in s:
                ext_refs[f.ref_table].add(f.ref_column)
    boxes = {n: Box(tables[n], ordered_cols(tables[n])) for n in tl}
    stub_boxes = {n: Box(tables[n], ordered_cols(tables[n], only=cols), stub=True)
                  for n, cols in ext_refs.items()}
    stub_h = max([b.h for b in stub_boxes.values()] + [0])
    top = 130
    body_y = top + (stub_h + 110 + 9 * len(ext_refs) if stub_boxes else 40)
    col_of, cbounds = layered(tl, boxes, gap_x=170, gap_y=50, max_col_h=1400, x0=60, y0=body_y)
    main_w = cbounds[-1][1] - 60
    # stub band, ordered by mean x of referencing columns
    def mean_x(n):
        xs = [boxes[f.table].cx for t in tl for f in fks_by_table[t] if f.ref_table == n]
        return sum(xs) / len(xs)
    sorder = sorted(stub_boxes, key=mean_x)
    total = sum(stub_boxes[n].w for n in sorder) + 40 * max(len(sorder) - 1, 0)
    sx = 60 + max(0, (main_w - total) / 2)
    for n in sorder:
        b = stub_boxes[n]
        b.x, b.y = sx, top + 50
        sx += b.w + 40
    if stub_boxes:
        bw = max(main_w, total)
        p.rect(40, top, bw + 40, stub_h + 70,
               "rounded=1;arcSize=2;fillColor=#F7F8FA;strokeColor=#DDE2E8;dashed=1;dashPattern=6 4;", layer="bg")
        p.text(58, top + 8, 900, 20, "REFERENCED TABLES FROM OTHER SUBJECT AREAS (keys only)", size=10,
               bold=True, color=MUTED, layer="bg")
    header_band(p, 40, 36, 1600, f"{k} · {name}",
                f"{desc}   ·   {len(tl)} tables", color)
    # domain body background
    bx1 = max(b.x + b.w for b in boxes.values()) + 30
    by1 = max(b.y + b.h + (20 if b.t.partition else 0) for b in boxes.values()) + 30
    p.rect(40, body_y - 30, bx1 - 40, by1 - body_y + 30,
           f"rounded=1;arcSize=1;fillColor={tint};strokeColor={color};strokeWidth=1.2;", layer="bg")
    for n in tl:
        p.table(boxes[n], color)
    for n in sorder:
        p.table(stub_boxes[n], DOM[TDOM[n]][2], show_domain_tag=True)
    # routing with gutter lanes
    lanes = defaultdict(int)

    def lane(key, base, direction):
        i = lanes[key]
        lanes[key] += 1
        return base + direction * (28 + (i % 10) * 9)

    ncols = len(cbounds)
    stub_in = defaultdict(list)
    for n in tl:
        for f in fks_by_table[n]:
            if f.ref_table not in s:
                stub_in[f.ref_table].append(f)
    for k2 in stub_in:
        stub_in[k2].sort(key=lambda f: (boxes[f.table].cx, boxes[f.table].row_y(f.column)))
    stub_seen = defaultdict(int)
    for f in sorted((f for n in tl for f in fks_by_table[n]),
                    key=lambda f: (f.ref_table in s, boxes[f.table].cx, boxes[f.table].row_y(f.column))):
        cb = boxes[f.table]
        ci = col_of[f.table]
        src = f"{p.pid}-t-{f.table}--{f.column}"
        dst = f"{p.pid}-t-{f.ref_table}--{f.ref_column}"
        ry = cb.row_y(f.column)
        if f.ref_table not in s:
            pb = stub_boxes[f.ref_table]
            si = sorder.index(f.ref_table)
            chy = top + 50 + stub_h + 34 + si * 9
            inc = stub_in[f.ref_table]
            kpos = inc.index(f)
            rel = (kpos + 1) / (len(inc) + 1)
            entry_x = pb.x + rel * pb.w
            if entry_x < cb.cx:
                gxp = lane(("L", ci), cbounds[ci][0], -1)
                ex = 0
            else:
                gxp = lane(("R", ci), cbounds[ci][1], +1)
                ex = 1
            st_id = f"{p.pid}-t-{f.ref_table}"
            p.edge(f, src, st_id, DOM[TDOM[f.ref_table]][2], ex, rel, [(gxp, ry), (gxp, chy), (entry_x, chy)],
                   width=1.2, child_unique=unique_fk(f), entry_y=1)
            continue
        pb = boxes[f.ref_table]
        pc = col_of[f.ref_table]
        py = pb.row_y(f.ref_column)
        if f.table == f.ref_table:
            gxp = lane(("R", ci), cbounds[ci][1], +1)
            p.edge(f, src, dst, color, 1, 1, [(gxp, ry), (gxp, py)], width=1.5, child_unique=False)
        elif pc < ci:
            gxp = lane(("L", ci), cbounds[ci][0], -1)
            p.edge(f, src, dst, color, 0, 1, [(gxp, ry), (gxp, py)], width=1.5, child_unique=unique_fk(f))
        elif pc > ci:
            gxp = lane(("R", ci), cbounds[ci][1], +1)
            p.edge(f, src, dst, color, 1, 0, [(gxp, ry), (gxp, py)], width=1.5, child_unique=unique_fk(f))
        else:
            gxp = lane(("L", ci), cbounds[ci][0], -1)
            p.edge(f, src, dst, color, 0, 0, [(gxp, ry), (gxp, py)], width=1.5, child_unique=unique_fk(f))
    legend(p, bx1 + 50, body_y - 30)
    return p


pages.append(cover())
pages.append(full_erd())
for i, d in enumerate(DOMAINS):
    pages.append(domain_page(i + 2, d))

OUT.write_text('<mxfile host="Electron" agent="RESCA ERD generator" version="24.7.17" pages="'
               f'{len(pages)}">' + "".join(p.xml() for p in pages) + "</mxfile>")
print("wrote", OUT, len(pages), "pages")
