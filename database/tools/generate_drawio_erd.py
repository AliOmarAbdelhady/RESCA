#!/usr/bin/env python3
"""Generate the RescueVision ERD as draw.io XML from the live PostgreSQL catalog.

Reads pg_class / pg_attribute / pg_constraint / pg_index through `psql` (no
Python database driver required) and writes:

    docs/database/rescuevision-erd.drawio

Pages:
    1      Overview        domain map only (fits 1920x1080)
    2-9    D1 .. D5        one page per domain, full columns
    10     Full ERD        all 56 tables, grouped into domain clusters

Layout is hierarchical: foreign-key parents sit above their children, layers are
ordered with barycenter sweeps, and domain pages place cross-domain stubs in a
row above the tables that reference them.

Usage:
    python3 database/tools/generate_drawio_erd.py

Optional:
    ERD_BEFORE=/path/to/previous.drawio  also report crossings for an older file.
"""

from __future__ import annotations

import math
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Connection and output
# --------------------------------------------------------------------------

PG_ENV = {
    "PGHOST": os.environ.get("PGHOST", "localhost"),
    "PGPORT": os.environ.get("PGPORT", "55432"),
    "PGUSER": os.environ.get("PGUSER", "postgres"),
    "PGPASSWORD": os.environ.get("PGPASSWORD", "test"),
    "PGDATABASE": os.environ.get("PGDATABASE", "rescuevision"),
}

OUT_PATH = (
    Path(__file__).resolve().parents[2] / "docs" / "database" / "rescuevision-erd.drawio"
)

# --------------------------------------------------------------------------
# Domains (spec section 4): key, label, fill, stroke, darker edge colour, tables
# --------------------------------------------------------------------------

DOMAINS = [
    ("D1", "D1 \u00b7 Identity & Access", "#dae8fc", "#6c8ebf", "#2f5d8a",
     ["agencies", "roles", "permissions", "role_permissions", "users",
      "user_sessions", "user_devices", "teams", "team_members", "vehicles"]),
    ("D2", "D2 \u00b7 Incidents & Operations", "#d5e8d4", "#82b366", "#3f6b2f",
     ["incidents", "incident_agencies", "zones", "missions",
      "mission_assignments", "mission_status_history"]),
    ("D3", "D3 \u00b7 Imagery & AI Pipeline", "#e1d5e7", "#9673a6", "#654275",
     ["capture_sessions", "images", "raster_products", "ai_models",
      "processing_jobs", "inference_runs"]),
    ("D4a", "D4a \u00b7 F1 Buildings & Cost", "#ffe6cc", "#d79b00", "#9c6a00",
     ["buildings", "building_assessments", "cost_profiles",
      "cost_profile_unit_rates", "cost_profile_repair_ratios", "cost_estimates"]),
    ("D4b", "D4b \u00b7 F2 Roads & Routing", "#fff2cc", "#d6b656", "#8f7620",
     ["road_nodes", "road_segments", "road_condition_observations", "routes",
      "route_segments"]),
    ("D4c", "D4c \u00b7 F3/F4 Persons & Cases", "#f8cecc", "#b85450", "#7f2f2b",
     ["person_tracks", "person_detections", "facilities", "assistance_cases",
      "case_events"]),
    ("D4d", "D4d \u00b7 F5 Hazards & Alerts", "#ffe0f0", "#b5739d", "#7d4566",
     ["infrastructure_assets", "hazards", "hazard_rules", "compound_alerts",
      "compound_alert_sources", "alert_closed_segments"]),
    ("D5", "D5 \u00b7 Field, Citizens, Reports, Audit", "#e6e6e6", "#666666", "#3a3a3a",
     ["responder_positions", "responder_last_positions", "sos_alerts",
      "citizens", "citizen_requests", "media_files", "citizen_request_media",
      "notifications", "reports", "report_shares", "image_embeddings",
      "audit_log"]),
]

DOMAIN_INFO = {d[0]: d for d in DOMAINS}
TABLE_DOMAIN = {t: d[0] for d in DOMAINS for t in d[5]}
DOMAIN_ORDER = [d[0] for d in DOMAINS]

# "Who did it" user links: FK row stays, no edge drawn.
AUDIT_USER_COLUMNS = {
    "created_by", "invited_by", "assigned_by", "changed_by", "uploaded_by",
    "requested_by", "reviewed_by", "verified_by", "acknowledged_by",
    "resolved_by", "approved_by", "generated_by", "shared_by", "reported_by",
    "actor_id", "assessed_by", "uploaded_by_user",
}

# --------------------------------------------------------------------------
# Geometry / typography
# --------------------------------------------------------------------------

HEADER_H = 34
ROW_H = 24
KEY_W = 36
MIN_TABLE_W = 260
MAX_TABLE_W = 380
H_GAP = 120          # horizontal gap between tables in one layer
V_GAP_LAYER = 160    # vertical gap between hierarchy layers
V_GAP_CHUNK = 60     # vertical gap between wrapped rows inside one layer
STUB_W = 220
STUB_H = 30
STUB_GAP = 40
CLUSTER_PAD = 30
CLUSTER_TITLE_H = 48
CLUSTER_GAP_X = 140
CLUSTER_GAP_Y = 180
FULL_MAX_ROW_W = 1500
DOMAIN_MAX_ROW_W = 1500
PAGE_MARGIN = 40

TABLE_STYLE = (
    "shape=table;startSize=34;container=1;collapsible=0;childLayout=tableLayout;"
    "fixedRows=1;rowLines=0;resizeLast=1;html=1;whiteSpace=wrap;strokeWidth=1;"
    "fontStyle=1;fontSize=14;"
)
STUB_STYLE = (
    "shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;"
    "fixedRows=1;rowLines=0;resizeLast=1;html=1;whiteSpace=wrap;strokeWidth=1;"
    "fontStyle=1;fontSize=12;fillColor=#f5f5f5;strokeColor=#9ca3af;"
)
ROW_STYLE = (
    "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;"
    "strokeColor=inherit;top=0;left=0;bottom=0;right=0;collapsible=0;"
    "dropTarget=0;fillColor=none;points=[[0,0.5],[1,0.5]];"
    "portConstraint=eastwest;fontSize=12;"
)
CELL_STYLE = (
    "shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;"
    "strokeColor=inherit;overflow=hidden;top=0;left=0;bottom=0;right=0;"
    "pointerEvents=1;fontSize=12;"
)
KEY_STYLE = CELL_STYLE + "align=center;verticalAlign=middle;fontStyle=1;"
NAME_STYLE = CELL_STYLE + "align=left;verticalAlign=middle;spacingLeft=6;"
TYPE_STYLE = CELL_STYLE + "align=right;verticalAlign=middle;spacingRight=6;fontColor=#6b7280;"

# --------------------------------------------------------------------------
# Catalog
# --------------------------------------------------------------------------


def psql(sql: str) -> list[list[str]]:
    env = os.environ.copy()
    env.update(PG_ENV)
    proc = subprocess.run(
        ["psql", "-X", "-q", "-A", "-t", "-F", "\t", "-v", "ON_ERROR_STOP=1",
         "-d", PG_ENV["PGDATABASE"]],
        input=sql, text=True, capture_output=True, env=env, check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(
            "psql failed (is rescuevision reachable at "
            f"{PG_ENV['PGHOST']}:{PG_ENV['PGPORT']}?)"
        )
    return [line.split("\t") for line in proc.stdout.splitlines() if line.strip()]


PUBLIC = "'public'::regnamespace"


@dataclass
class Column:
    name: str
    type: str
    notnull: bool
    is_pk: bool = False
    is_fk: bool = False
    is_uq: bool = False
    audit_user: bool = False

    @property
    def marker(self) -> str:
        if self.is_pk and self.is_fk:
            return "PK/FK"
        if self.is_pk:
            return "PK"
        if self.is_fk:
            return "FK"
        if self.is_uq:
            return "UQ"
        return ""

    @property
    def display_type(self) -> str:
        return self.type + (" \u2192 users" if self.audit_user else "")


@dataclass
class Table:
    name: str
    oid: str
    columns: list[Column] = field(default_factory=list)
    by_name: dict[str, Column] = field(default_factory=dict)
    width: int = MIN_TABLE_W

    @property
    def height(self) -> int:
        return HEADER_H + max(len(self.columns), 1) * ROW_H


@dataclass
class ForeignKey:
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    nullable: bool
    audit_user: bool = False
    constraint_name: str = ""


def load_catalog() -> tuple[dict[str, Table], list[ForeignKey]]:
    table_rows = psql(f"""
        SELECT c.oid, c.relname
        FROM pg_class c
        WHERE c.relnamespace = {PUBLIC}
          AND c.relkind IN ('r', 'p')
          AND NOT c.relispartition
          AND c.relname <> 'spatial_ref_sys'
        ORDER BY c.relname;
    """)
    tables: dict[str, Table] = {}
    oid_to_name: dict[str, str] = {}
    for oid, name in table_rows:
        tables[name] = Table(name=name, oid=oid)
        oid_to_name[oid] = name

    for oid, name, coltype, notnull in psql(f"""
        SELECT a.attrelid, a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        WHERE c.relnamespace = {PUBLIC}
          AND c.relkind IN ('r', 'p')
          AND NOT c.relispartition
          AND c.relname <> 'spatial_ref_sys'
          AND a.attnum > 0 AND NOT a.attisdropped
        ORDER BY a.attnum;
    """):
        t = tables.get(oid_to_name.get(oid, ""))
        if t is None:
            continue
        col = Column(name=name, type=coltype, notnull=notnull == "t")
        t.columns.append(col)
        t.by_name[name] = col

    for oid, colname in psql(f"""
        SELECT c.conrelid, a.attname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
        WHERE c.contype = 'p' AND t.relnamespace = {PUBLIC}
          AND NOT t.relispartition;
    """):
        t = tables.get(oid_to_name.get(oid, ""))
        if t and colname in t.by_name:
            t.by_name[colname].is_pk = True

    for oid, colname in psql(f"""
        SELECT i.indrelid, a.attname
        FROM pg_index i
        JOIN pg_class t ON t.oid = i.indrelid
        CROSS JOIN LATERAL unnest(i.indkey::int2[]) WITH ORDINALITY AS k(attnum, ord)
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = k.attnum
        WHERE i.indisunique AND NOT i.indisprimary
          AND array_length(i.indkey::int2[], 1) = 1
          AND t.relnamespace = {PUBLIC} AND NOT t.relispartition;
    """):
        t = tables.get(oid_to_name.get(oid, ""))
        if t and colname in t.by_name:
            t.by_name[colname].is_uq = True

    fks: list[ForeignKey] = []
    for src_oid, tgt_oid, src_col, tgt_col, notnull, conname in psql(f"""
        SELECT c.conrelid, c.confrelid, a.attname, fa.attname, a.attnotnull, c.conname
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        CROSS JOIN LATERAL unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
        JOIN pg_attribute fa ON fa.attrelid = c.confrelid AND fa.attnum = c.confkey[k.ord]
        WHERE c.contype = 'f' AND t.relnamespace = {PUBLIC}
          AND NOT t.relispartition
        ORDER BY c.oid, k.ord;
    """):
        src = oid_to_name.get(src_oid)
        tgt = oid_to_name.get(tgt_oid)
        if not src or not tgt:
            continue
        audit = tgt == "users" and src_col in AUDIT_USER_COLUMNS
        if src_col in tables[src].by_name:
            col = tables[src].by_name[src_col]
            col.is_fk = True
            col.audit_user = col.audit_user or audit
        fks.append(ForeignKey(src, src_col, tgt, tgt_col, notnull != "t", audit, conname))

    for table in tables.values():
        table.width = measure_table_width(table)
    return tables, fks


def measure_table_width(table: Table) -> int:
    name_w = max((len(c.name) for c in table.columns), default=8) * 6.6 + 16
    type_w = max((len(c.display_type) for c in table.columns), default=4) * 6.0 + 16
    title_w = len(table.name) * 8.2 + 28
    return int(min(MAX_TABLE_W, max(MIN_TABLE_W, KEY_W + name_w + type_w, title_w)))


# --------------------------------------------------------------------------
# Layered graph layout
# --------------------------------------------------------------------------


def compute_layers(names: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    """Longest-path layers. `edges` are (parent, child); parents are above."""
    parents: dict[str, set[str]] = {n: set() for n in names}
    children: dict[str, set[str]] = {n: set() for n in names}
    for parent, child in edges:
        if parent == child or parent not in parents or child not in children:
            continue
        parents[child].add(parent)
        children[parent].add(child)

    indeg = {n: len(parents[n]) for n in names}
    layer: dict[str, int] = {}
    queue = deque([n for n in names if indeg[n] == 0])
    for n in queue:
        layer[n] = 0
    processed = set(queue)
    while queue:
        parent = queue.popleft()
        for child in children[parent]:
            layer[child] = max(layer.get(child, 0), layer[parent] + 1)
            indeg[child] -= 1
            if indeg[child] == 0:
                queue.append(child)
                processed.add(child)

    remaining = [n for n in names if n not in processed]
    while remaining:
        progressed = False
        for n in list(remaining):
            known = [layer[p] for p in parents[n] if p in layer]
            if known or not parents[n]:
                layer[n] = max(known) + 1 if known else 0
                remaining.remove(n)
                progressed = True
        if not progressed:
            base = max(layer.values(), default=-1) + 1
            for n in remaining:
                layer[n] = base
            break

    count = max(layer.values(), default=0) + 1
    rows: list[list[str]] = [[] for _ in range(count)]
    for n in names:
        rows[layer[n]].append(n)
    for row in rows:
        row.sort()
    return rows


def order_layers(layers: list[list[str]], edges: list[tuple[str, str]], sweeps: int = 4) -> None:
    """Barycenter sweeps; mutates `layers` in place."""
    parents: dict[str, set[str]] = {n: set() for row in layers for n in row}
    children: dict[str, set[str]] = {n: set() for row in layers for n in row}
    for parent, child in edges:
        if parent in parents and child in children and parent != child:
            parents[child].add(parent)
            children[parent].add(child)

    pos: dict[str, int] = {}
    for row in layers:
        for i, n in enumerate(row):
            pos[n] = i

    for _ in range(sweeps):
        for li in range(1, len(layers)):
            row = layers[li]

            def down_key(n: str) -> tuple[float, str]:
                known = [pos[p] for p in parents[n] if p in pos]
                return (sum(known) / len(known) if known else pos[n], n)

            row.sort(key=down_key)
            for i, n in enumerate(row):
                pos[n] = i
        for li in range(len(layers) - 2, -1, -1):
            row = layers[li]

            def up_key(n: str) -> tuple[float, str]:
                known = [pos[c] for c in children[n] if c in pos]
                return (sum(known) / len(known) if known else pos[n], n)

            row.sort(key=up_key)
            for i, n in enumerate(row):
                pos[n] = i


@dataclass
class LayoutResult:
    positions: dict[str, tuple[float, float, float, float]]
    width: float
    height: float
    layers: list[list[str]]


def layered_layout(
    names: list[str],
    tables: dict[str, Table],
    edges: list[tuple[str, str]],
    max_row_width: float,
) -> LayoutResult:
    layers = compute_layers(names, edges)
    order_layers(layers, edges)

    # Greedily wrap each layer into rows that fit max_row_width.
    rows_by_layer: list[list[tuple[list[str], float, float]]] = []
    for row in layers:
        chunks: list[tuple[list[str], float, float]] = []
        current: list[str] = []
        current_w = 0.0
        for name in row:
            w = tables[name].width
            extra = w if not current else w + H_GAP
            if current and current_w + extra > max_row_width:
                chunks.append((current, current_w, 0.0))
                current, current_w = [name], float(w)
            else:
                current.append(name)
                current_w += extra
        if current:
            chunks.append((current, current_w, 0.0))
        rows_by_layer.append(chunks)

    content_w = max((chunk[1] for chunks in rows_by_layer for chunk in chunks), default=0.0)

    positions: dict[str, tuple[float, float, float, float]] = {}
    y = 0.0
    for li, chunks in enumerate(rows_by_layer):
        for ci, (chunk, row_w, _unused) in enumerate(chunks):
            x = (content_w - row_w) / 2.0
            row_h = max(tables[n].height for n in chunk)
            for name in chunk:
                positions[name] = (x, y, tables[name].width, tables[name].height)
                x += tables[name].width + H_GAP
            if ci < len(chunks) - 1:
                y += row_h + V_GAP_CHUNK
            else:
                y += row_h
        if li < len(rows_by_layer) - 1:
            y += V_GAP_LAYER

    return LayoutResult(positions, content_w, max(y, 0.0), layers)


# --------------------------------------------------------------------------
# draw.io helpers
# --------------------------------------------------------------------------


def sub(node, tag, attrib=None, **kwargs):
    attrs = dict(attrib or {})
    attrs.update(kwargs)
    return ET.SubElement(node, tag, attrs)


def add_text(root, cell_id, x, y, w, h, value, size=12, bold=False, color="#000000",
             align="left", vertical="middle"):
    style = (
        f"text;html=1;align={align};verticalAlign={vertical};whiteSpace=wrap;"
        f"fontSize={size};fontColor={color};"
    )
    if bold:
        style += "fontStyle=1;"
    cell = sub(root, "mxCell", id=cell_id, value=value, style=style, vertex="1", parent="1")
    sub(cell, "mxGeometry", x=f"{x:.1f}", y=f"{y:.1f}", width=f"{w:.1f}", height=f"{h:.1f}",
        **{"as": "geometry"})


def add_vertex(root, cell_id, value, style, x, y, w, h):
    cell = sub(root, "mxCell", id=cell_id, value=value, style=style, vertex="1", parent="1")
    sub(cell, "mxGeometry", x=f"{x:.1f}", y=f"{y:.1f}", width=f"{w:.1f}", height=f"{h:.1f}",
        **{"as": "geometry"})
    return cell


def add_table(root, page_tag: str, table: Table, x: float, y: float, fill: str, stroke: str,
              tint: str, row_ids: dict[tuple[str, str], str]) -> str:
    table_id = f"{page_tag}-t-{table.name}"
    add_vertex(
        root, table_id, table.name,
        TABLE_STYLE + f"fillColor={fill};strokeColor={stroke};",
        x, y, table.width, table.height,
    )
    # Distribute width: key fixed, name and type share the rest; name gets 58%.
    rest = table.width - KEY_W
    name_w = int(rest * 0.58)
    type_w = rest - name_w

    for index, col in enumerate(table.columns):
        row_id = f"{table_id}-r{index}"
        row_ids[(table.name, col.name)] = row_id
        row = sub(root, "mxCell", id=row_id, value="", style=ROW_STYLE, vertex="1", parent=table_id)
        sub(row, "mxGeometry", y=str(HEADER_H + index * ROW_H), width=f"{table.width:.1f}",
            height=str(ROW_H), **{"as": "geometry"})
        cells = [
            ("key", col.marker, 0.0, KEY_W, KEY_STYLE),
            ("name", col.name, float(KEY_W), float(name_w),
             NAME_STYLE + ("fontStyle=1;" if col.is_pk else "")),
            ("type", col.display_type, float(KEY_W + name_w), float(type_w), TYPE_STYLE),
        ]
        row_fill = f"fillColor={tint};" if col.is_pk else ""
        for suffix, value, cell_x, width, style in cells:
            cell_id = f"{row_id}-{suffix}"
            cell = sub(root, "mxCell", id=cell_id, value=value, style=style + row_fill,
                       vertex="1", parent=row_id)
            geo = sub(cell, "mxGeometry", x=f"{cell_x:.1f}", width=f"{width:.1f}",
                      height=str(ROW_H), **{"as": "geometry"})
            sub(geo, "mxRectangle", width=f"{width:.1f}", height=str(ROW_H),
                **{"as": "alternateBounds"})
    return table_id


def add_stub(root, page_tag: str, name: str, x: float, y: float) -> str:
    stub_id = f"{page_tag}-stub-{name}"
    add_vertex(root, stub_id, name, STUB_STYLE, x, y, STUB_W, STUB_H)
    return stub_id


def add_edge(root, page_tag: str, fk: ForeignKey, index: int,
             row_ids: dict[tuple[str, str], str], table_ids: dict[str, str],
             positions: dict[str, tuple[float, float, float, float]],
             tables: dict[str, Table]) -> None:
    row_id = row_ids.get((fk.source_table, fk.source_column))
    target_id = table_ids.get(fk.target_table)
    if not row_id or not target_id:
        return
    parent_domain = TABLE_DOMAIN[fk.target_table]
    colour = DOMAIN_INFO[parent_domain][4]
    end_arrow = "ERzeroToOne" if fk.nullable else "ERmandOne"
    base = (
        "rounded=1;jumpStyle=arc;jumpSize=8;html=1;"
        f"startArrow=ERmany;endArrow={end_arrow};startFill=0;endFill=0;"
        f"strokeWidth=1.5;strokeColor={colour};"
    )

    if fk.source_table == fk.target_table:
        tx, ty, tw, th = positions[fk.target_table]
        t = tables[fk.target_table]
        row_index = next((i for i, c in enumerate(t.columns) if c.name == fk.source_column), 0)
        row_y = ty + HEADER_H + row_index * ROW_H + ROW_H / 2.0
        loop_x = tx + tw + 34
        style = (
            "edgeStyle=orthogonalEdgeStyle;rounded=1;jumpStyle=arc;jumpSize=8;html=1;"
            f"startArrow=ERmany;endArrow={end_arrow};startFill=0;endFill=0;"
            f"strokeWidth=1.5;strokeColor={colour};"
            "exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;"
        )
        edge = sub(root, "mxCell", id=f"{page_tag}-e{index}", value="", style=style,
                   edge="1", parent="1", source=row_id, target=target_id)
        geo = sub(edge, "mxGeometry", relative="1", **{"as": "geometry"})
        points = sub(geo, "Array", **{"as": "points"})
        sub(points, "mxPoint", x=f"{loop_x:.1f}", y=f"{row_y:.1f}")
        sub(points, "mxPoint", x=f"{loop_x:.1f}", y=f"{ty + th / 2.0:.1f}")
        return

    style = "edgeStyle=entityRelationEdgeStyle;" + base
    edge = sub(root, "mxCell", id=f"{page_tag}-e{index}", value="", style=style,
               edge="1", parent="1", source=row_id, target=target_id)
    sub(edge, "mxGeometry", relative="1", **{"as": "geometry"})


def new_page(mxfile, page_id: str, name: str):
    diagram = sub(mxfile, "diagram", id=page_id, name=name)
    model = sub(
        diagram, "mxGraphModel", dx="1600", dy="1200", grid="1", gridSize="10",
        guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1",
        pageScale="1", pageWidth="1600", pageHeight="1200", math="0", shadow="0",
    )
    root = sub(model, "root")
    sub(root, "mxCell", id="0")
    sub(root, "mxCell", id="1", parent="0")
    return model, root


def finalize_page(model, width: float, height: float):
    model.set("pageWidth", str(int(math.ceil(max(width, 400)))))
    model.set("pageHeight", str(int(math.ceil(max(height, 400)))))


def blend(hex_colour: str, other: str, amount: float) -> str:
    a = [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(other[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(a, b))


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------


def real_fks(fks: list[ForeignKey]) -> list[ForeignKey]:
    return [fk for fk in fks if not fk.audit_user]


def table_edges(fks: list[ForeignKey], names: set[str], internal_only: bool) -> list[tuple[str, str]]:
    edges: list[tuple[str, str]] = []
    for fk in fks:
        if fk.audit_user or fk.source_table == fk.target_table:
            continue
        if fk.source_table not in names:
            continue
        if internal_only and fk.target_table not in names:
            continue
        if fk.target_table not in names:
            continue
        edges.append((fk.target_table, fk.source_table))  # parent, child
    return edges


def emit_overview(mxfile, tables: dict[str, Table], fks: list[ForeignKey], stats: dict) -> None:
    model, root = new_page(mxfile, "p1", "Overview")
    add_text(root, "p1-title", 40, 26, 1800, 42,
             "RescueVision \u00b7 Domain Map (8 domains, 56 tables)", size=24, bold=True)
    add_text(root, "p1-sub", 40, 70, 1800, 22,
             "Boxes list tables only. Each line is one domain pair that has foreign keys; "
             "the label is the number of FKs (audit \u2018who did it\u2019 links excluded).",
             size=12, color="#555555")

    box_w, box_h = 420, 300
    gap_x, gap_y = 40, 40
    x0, y0 = 40, 128
    box_ids: dict[str, str] = {}
    boxes: list[tuple[float, float, float, float]] = []

    for idx, (key, label, fill, stroke, _dark, names) in enumerate(DOMAINS):
        row, col = divmod(idx, 4)
        x = x0 + col * (box_w + gap_x)
        y = y0 + row * (box_h + gap_y)
        boxes.append((x, y, box_w, box_h))
        table_lines = "<br>".join(names)
        value = (
            f'<b style="font-size:16px">{label}</b>'
            f'<br><span style="font-size:11px;color:#555555">{len(names)} tables</span>'
            f'<br><br><span style="font-size:13px;line-height:1.45">{table_lines}</span>'
        )
        style = (
            "rounded=1;arcSize=3;whiteSpace=wrap;html=1;align=left;verticalAlign=top;"
            f"spacingLeft=14;spacingTop=10;spacingRight=10;fillColor={fill};"
            f"strokeColor={stroke};strokeWidth=2;fontSize=14;"
        )
        box_id = f"p1-domain-{key}"
        box_ids[key] = box_id
        add_vertex(root, box_id, value, style, x, y, box_w, box_h)

    # One edge per unordered domain pair that has FKs.
    pair_counts: dict[tuple[str, str], int] = {}
    for fk in real_fks(fks):
        a = TABLE_DOMAIN[fk.source_table]
        b = TABLE_DOMAIN[fk.target_table]
        if a == b:
            continue
        pair = tuple(sorted((a, b)))
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

    for idx, ((a, b), count) in enumerate(sorted(pair_counts.items()), start=1):
        style = (
            "edgeStyle=entityRelationEdgeStyle;rounded=1;jumpStyle=arc;jumpSize=8;html=1;"
            "endArrow=none;startArrow=none;strokeWidth=1.5;strokeColor=#6b7280;"
            "fontSize=12;labelBackgroundColor=#ffffff;"
        )
        edge = sub(root, "mxCell", id=f"p1-e{idx}", value=str(count), style=style,
                   edge="1", parent="1", source=box_ids[a], target=box_ids[b])
        sub(edge, "mxGeometry", relative="1", **{"as": "geometry"})

    # Boxes must not overlap.
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                raise SystemExit(f"OVERLAP on Overview: {a} vs {b}")

    finalize_page(model, 1920, 1000)
    stats["pages"].append({
        "name": "Overview", "w": 1920, "h": 1000, "tables": len(DOMAINS),
        "edges": len(pair_counts), "audit": 0,
    })


def emit_domain_page(mxfile, page_no: int, domain_key: str, tables: dict[str, Table],
                     fks: list[ForeignKey], stats: dict) -> None:
    _key, label, fill, stroke, _dark, own_names = DOMAIN_INFO[domain_key]
    model, root = new_page(mxfile, f"p{page_no}", label)
    page_tag = f"p{page_no}"
    own_set = set(own_names)

    add_text(root, f"{page_tag}-title", PAGE_MARGIN, 20, 1500, 40, label, size=22, bold=True, color=stroke)
    add_text(root, f"{page_tag}-sub", PAGE_MARGIN, 60, 1500, 22,
             "Full columns. Grey stubs above are referenced tables from other domains; "
             "audit \u2018who did it\u2019 user links are not drawn.", size=11, color="#555555")

    internal_edges = table_edges(real_fks(fks), own_set, internal_only=True)
    layout = layered_layout(own_names, tables, internal_edges, DOMAIN_MAX_ROW_W)

    own_fks = [fk for fk in real_fks(fks) if fk.source_table in own_set]
    external = sorted({fk.target_table for fk in own_fks if fk.target_table not in own_set})

    # Stubs sit in a row above, each centred over the tables that reference it.
    stub_x: dict[str, float] = {}
    for stub in external:
        refs = [fk.source_table for fk in own_fks if fk.target_table == stub]
        centres = []
        for r in refs:
            rx, _ry, rw, _rh = layout.positions[r]
            centres.append(PAGE_MARGIN + rx + rw / 2.0)
        stub_x[stub] = (sum(centres) / len(centres)) - STUB_W / 2.0 if centres else PAGE_MARGIN

    ordered_stubs = sorted(external, key=lambda s: (stub_x[s], s))
    cursor = PAGE_MARGIN
    for stub in ordered_stubs:
        stub_x[stub] = max(stub_x[stub], cursor)
        cursor = stub_x[stub] + STUB_W + STUB_GAP

    stub_label_y = 96
    stub_y = 126
    tables_y = stub_y + STUB_H + 130
    if external:
        add_text(root, f"{page_tag}-stub-label", PAGE_MARGIN, stub_label_y, 900, 24,
                 "Referenced tables (other domains)", size=13, bold=True, color="#4b5563")

    table_ids: dict[str, str] = {}
    row_ids: dict[tuple[str, str], str] = {}
    positions: dict[str, tuple[float, float, float, float]] = {}
    tint = blend(fill, "#ffffff", 0.55)
    for name in own_names:
        lx, ly, w, h = layout.positions[name]
        x = PAGE_MARGIN + lx
        y = tables_y + ly
        positions[name] = (x, y, w, h)
        table_ids[name] = add_table(root, page_tag, tables[name], x, y, fill, stroke, tint, row_ids)

    for stub in external:
        table_ids[stub] = add_stub(root, page_tag, stub, stub_x[stub], stub_y)

    for idx, fk in enumerate(own_fks, start=1):
        add_edge(root, page_tag, fk, idx, row_ids, table_ids, positions, tables)

    canvas_w = max(PAGE_MARGIN + layout.width + PAGE_MARGIN,
                   (max((stub_x[s] + STUB_W for s in external), default=0) + PAGE_MARGIN))
    canvas_h = tables_y + layout.height + PAGE_MARGIN
    finalize_page(model, canvas_w, canvas_h)
    stats["pages"].append({
        "name": label, "w": int(canvas_w), "h": int(canvas_h),
        "tables": len(own_names) + len(external), "edges": len(own_fks),
        "audit": 0,
    })


def domain_layers(fks: list[ForeignKey]) -> list[list[str]]:
    edges: list[tuple[str, str]] = []
    for fk in real_fks(fks):
        sd = TABLE_DOMAIN[fk.source_table]
        td = TABLE_DOMAIN[fk.target_table]
        if sd != td:
            edges.append((td, sd))  # parent domain, child domain
    return compute_layers(DOMAIN_ORDER, edges)


def emit_full_page(mxfile, page_no: int, tables: dict[str, Table], fks: list[ForeignKey],
                   stats: dict) -> None:
    model, root = new_page(mxfile, f"p{page_no}", "Full ERD")
    page_tag = f"p{page_no}"
    add_text(root, f"{page_tag}-title", PAGE_MARGIN, 20, 2000, 40,
             "RescueVision \u00b7 Full ERD (56 tables, grouped by domain)", size=22, bold=True)
    add_text(root, f"{page_tag}-sub", PAGE_MARGIN, 60, 2200, 22,
             "Domain clusters; PK/FK/UQ markers; crow's foot at the child, bar/circle at "
             "the parent. Audit \u2018who did it\u2019 user FKs are shown as rows only.",
             size=11, color="#555555")

    # Internal hierarchical layout per domain, then place clusters by domain layers.
    clusters: dict[str, dict] = {}
    for key, label, fill, stroke, _dark, names in DOMAINS:
        internal = table_edges(real_fks(fks), set(names), internal_only=True)
        layout = layered_layout(names, tables, internal, FULL_MAX_ROW_W)
        cw = layout.width + 2 * CLUSTER_PAD
        ch = CLUSTER_TITLE_H + layout.height + CLUSTER_PAD
        clusters[key] = {"label": label, "fill": fill, "stroke": stroke, "layout": layout,
                         "w": cw, "h": ch}

    layers = domain_layers(fks)
    cluster_pos: dict[str, tuple[float, float]] = {}
    y = 120.0
    for layer in layers:
        x = PAGE_MARGIN
        row_h = 0.0
        for key in layer:
            cw, ch = clusters[key]["w"], clusters[key]["h"]
            if x > PAGE_MARGIN and x + cw > PAGE_MARGIN + 2400:
                y += row_h + CLUSTER_GAP_Y
                x = PAGE_MARGIN
                row_h = 0.0
            cluster_pos[key] = (x, y)
            x += cw + CLUSTER_GAP_X
            row_h = max(row_h, ch)
        y += row_h + CLUSTER_GAP_Y

    table_ids: dict[str, str] = {}
    row_ids: dict[tuple[str, str], str] = {}
    positions: dict[str, tuple[float, float, float, float]] = {}
    cluster_rects: dict[str, tuple[float, float, float, float]] = {}
    title_rects: list[tuple[float, float, float, float]] = []
    table_rects: list[tuple[float, float, float, float, str]] = []

    for key, label, fill, stroke, _dark, names in DOMAINS:
        cx, cy = cluster_pos[key]
        info = clusters[key]
        cw, ch = info["w"], info["h"]
        cluster_rects[key] = (cx, cy, cw, ch)
        bg_style = (
            "rounded=1;arcSize=2;whiteSpace=wrap;html=1;"
            f"fillColor={fill};strokeColor={stroke};strokeWidth=2;"
        )
        add_vertex(root, f"{page_tag}-cluster-{key}", "", bg_style, cx, cy, cw, ch)
        add_text(root, f"{page_tag}-cluster-title-{key}", cx + CLUSTER_PAD,
                 cy + 8, cw - 2 * CLUSTER_PAD, 32, label, size=18, bold=True, color=stroke)
        title_rects.append((cx + CLUSTER_PAD, cy + 8, cw - 2 * CLUSTER_PAD, 32))

        tint = blend(fill, "#ffffff", 0.55)
        layout = info["layout"]
        for name in names:
            lx, ly, w, h = layout.positions[name]
            x = cx + CLUSTER_PAD + lx
            ty = cy + CLUSTER_TITLE_H + ly
            positions[name] = (x, ty, w, h)
            table_rects.append((x, ty, w, h, name))
            table_ids[name] = add_table(root, page_tag, tables[name], x, ty, fill, stroke, tint, row_ids)

    # Geometry checks: clusters, titles and tables must not collide.
    rects = list(cluster_rects.items())
    for i, (ka, ra) in enumerate(rects):
        for kb, rb in rects[i + 1:]:
            if ra[0] < rb[0] + rb[2] and rb[0] < ra[0] + ra[2] and ra[1] < rb[1] + rb[3] and rb[1] < ra[1] + ra[3]:
                raise SystemExit(f"OVERLAP on Full ERD: clusters {ka} and {kb}")
    for i, a in enumerate(table_rects):
        for b in table_rects[i + 1:]:
            if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                raise SystemExit(f"OVERLAP on Full ERD: tables {a[4]} and {b[4]}")
        for title in title_rects:
            if a[0] < title[0] + title[2] and title[0] < a[0] + a[2] and a[1] < title[1] + title[3] and title[1] < a[1] + a[3]:
                raise SystemExit(f"OVERLAP on Full ERD: table {a[4]} and a cluster title")
        # Table must be inside its domain cluster.
        inside = any(
            a[0] >= cr[0] and a[1] >= cr[1] and a[0] + a[2] <= cr[0] + cr[2] and a[1] + a[3] <= cr[1] + cr[3]
            for cr in cluster_rects.values()
        )
        if not inside:
            raise SystemExit(f"TABLE OUTSIDE CLUSTER on Full ERD: {a[4]}")

    drawn = real_fks(fks)
    for idx, fk in enumerate(drawn, start=1):
        add_edge(root, page_tag, fk, idx, row_ids, table_ids, positions, tables)

    canvas_w = max((r[0] + r[2] for r in cluster_rects.values()), default=0) + PAGE_MARGIN
    canvas_h = max((r[1] + r[3] for r in cluster_rects.values()), default=0) + PAGE_MARGIN
    finalize_page(model, canvas_w, canvas_h)
    stats["pages"].append({
        "name": "Full ERD", "w": int(canvas_w), "h": int(canvas_h),
        "tables": len(tables), "edges": len(drawn), "audit": len(fks) - len(drawn),
    })
    stats["full_tables"] = len(tables)
    stats["full_edges"] = len(drawn)
    stats["total_fks"] = len(fks)


# --------------------------------------------------------------------------
# Crossing estimate and validation
# --------------------------------------------------------------------------


def _orient(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _proper_intersection(a, b, c, d) -> bool:
    o1, o2 = _orient(a, b, c), _orient(a, b, d)
    o3, o4 = _orient(c, d, a), _orient(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def page_crossings(root) -> tuple[int, int]:
    """(tables, drawn edges, straight-line centre-to-centre crossings)."""
    cells = root.findall("mxCell")
    by_id = {c.get("id"): c for c in cells}
    table_ids = {
        c.get("id") for c in cells
        if c.get("vertex") == "1" and (c.get("style") or "").startswith("shape=table;")
        and c.get("parent") == "1"
    }

    def resolve(cell_id: str) -> str | None:
        seen = set()
        while cell_id and cell_id not in table_ids and cell_id not in seen:
            seen.add(cell_id)
            cell = by_id.get(cell_id)
            if cell is None:
                return None
            cell_id = cell.get("parent")
        return cell_id if cell_id in table_ids else None

    segments = []
    for cell in cells:
        if cell.get("edge") != "1":
            continue
        s, t = resolve(cell.get("source", "")), resolve(cell.get("target", ""))
        if not s or not t or s == t:
            continue
        sc, tc = by_id.get(s), by_id.get(t)
        if sc is None or tc is None:
            continue
        sg, tg = sc.find("mxGeometry"), tc.find("mxGeometry")
        if sg is None or tg is None:
            continue
        s_centre = (float(sg.get("x")) + float(sg.get("width")) / 2,
                    float(sg.get("y")) + float(sg.get("height")) / 2)
        t_centre = (float(tg.get("x")) + float(tg.get("width")) / 2,
                    float(tg.get("y")) + float(tg.get("height")) / 2)
        segments.append((s, t, s_centre, t_centre))

    crossings = 0
    for i, (s1, t1, a, b) in enumerate(segments):
        for s2, t2, c, d in segments[i + 1:]:
            if s1 in (s2, t2) or t1 in (s2, t2):
                continue
            if _proper_intersection(a, b, c, d):
                crossings += 1
    return len(table_ids), len(segments), crossings


def estimate_file(path: Path) -> dict[str, dict]:
    root = ET.parse(path).getroot()
    out: dict[str, dict] = {}
    for diagram in root.findall("diagram"):
        model = diagram.find("mxGraphModel")
        if model is None:
            continue
        n_tables, n_edges, n_cross = page_crossings(model.find("root"))
        out[diagram.get("name", "")] = {
            "w": int(float(model.get("pageWidth", 0))),
            "h": int(float(model.get("pageHeight", 0))),
            "tables": n_tables, "edges": n_edges, "crossings": n_cross,
        }
    return out


def validate(out_path: Path, tables: dict[str, Table], fks: list[ForeignKey], stats: dict) -> None:
    tree = ET.parse(out_path)
    root = tree.getroot()
    diagrams = root.findall("diagram")
    if len(diagrams) != 10:
        raise SystemExit(f"VALIDATION FAILED: expected 10 pages, found {len(diagrams)}")

    names = [d.get("name") for d in diagrams]
    expected = ["Overview", "Full ERD"] + [d[1] for d in DOMAINS]
    if sorted(names) != sorted(expected):
        raise SystemExit(f"VALIDATION FAILED: unexpected page names {names}")

    full = next(d for d in diagrams if d.get("name") == "Full ERD")
    page_root = full.find("mxGraphModel/root")
    table_cells = [
        c for c in page_root.findall("mxCell")
        if c.get("vertex") == "1" and (c.get("style") or "").startswith("shape=table;")
        and c.get("parent") == "1"
    ]
    edge_cells = [c for c in page_root.findall("mxCell") if c.get("edge") == "1"]
    if len(table_cells) != 56:
        raise SystemExit(f"VALIDATION FAILED: Full ERD has {len(table_cells)} tables, expected 56")
    expected_edges = len(real_fks(fks))
    if len(edge_cells) != expected_edges:
        raise SystemExit(
            f"VALIDATION FAILED: Full ERD has {len(edge_cells)} edges, "
            f"expected {expected_edges} (140 minus {len(fks) - expected_edges} audit FKs)"
        )

    # Geometry: tables must never overlap, on any page. Cluster titles and
    # overview boxes are checked where they exist.
    for diagram in diagrams:
        droot = diagram.find("mxGraphModel/root")
        cells = droot.findall("mxCell")
        rects: list[tuple[float, float, float, float, str]] = []
        title_rects: list[tuple[float, float, float, float, str]] = []
        for cell in cells:
            style = cell.get("style") or ""
            geo = cell.find("mxGeometry")
            if cell.get("vertex") != "1" or geo is None:
                continue
            x, y = float(geo.get("x", 0)), float(geo.get("y", 0))
            w, h = float(geo.get("width", 0)), float(geo.get("height", 0))
            if style.startswith("shape=table;") and cell.get("parent") == "1":
                rects.append((x, y, w, h, cell.get("value") or "?"))
            elif cell.get("id", "").startswith("p1-domain-"):
                rects.append((x, y, w, h, cell.get("value") or "?"))
            if "cluster-title-" in (cell.get("id") or ""):
                title_rects.append((x, y, w, h, cell.get("value") or "?"))
        for i, a in enumerate(rects):
            for b in rects[i + 1:]:
                if a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]:
                    raise SystemExit(f"OVERLAP on {diagram.get('name')}: {a[4]} and {b[4]}")
            for t in title_rects:
                if a[0] < t[0] + t[2] and t[0] < a[0] + a[2] and a[1] < t[1] + t[3] and t[1] < a[1] + a[3]:
                    raise SystemExit(f"OVERLAP on {diagram.get('name')}: {a[4]} and {t[4]}")

    overview = next(d for d in diagrams if d.get("name") == "Overview")
    omodel = overview.find("mxGraphModel")
    if int(float(omodel.get("pageWidth"))) > 1920 or int(float(omodel.get("pageHeight"))) > 1080:
        raise SystemExit("VALIDATION FAILED: Overview does not fit 1920x1080")

    # Crossing estimates (also used by the report).
    for page in stats["pages"]:
        matched = next((d for d in diagrams if d.get("name") == page["name"]), None)
        if matched is None:
            continue
        _t, _e, crossings = page_crossings(matched.find("mxGraphModel/root"))
        page["crossings"] = crossings

    print(f"Validated {len(diagrams)} pages.")
    print(f"  Full ERD: {len(table_cells)} tables, {len(edge_cells)} edges "
          f"({len(fks) - expected_edges} audit-user FKs drawn as rows only, {len(fks)} total FKs)")
    before_path = os.environ.get("ERD_BEFORE")
    before = estimate_file(Path(before_path)) if before_path and Path(before_path).exists() else {}
    if before:
        print("  Crossings before -> after (pages matched by name):")
    for page in stats["pages"]:
        old = before.get(page["name"])
        if old:
            print(f"    {page['name']:<42} {old['crossings']:>4} -> {page.get('crossings', 0):>4}")
        else:
            print(f"    {page['name']:<42}    - -> {page.get('crossings', 0):>4}")
    print(f"  Canvas per page:")
    for page in stats["pages"]:
        print(f"    {page['name']:<42} {page['w']:>5} x {page['h']:<5} "
              f"tables={page['tables']:>3} edges={page['edges']:>3}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main() -> None:
    tables, fks = load_catalog()
    if len(tables) != 56:
        raise SystemExit(f"Expected 56 tables in public schema, found {len(tables)}")
    missing = sorted(set(tables) - set(TABLE_DOMAIN))
    if missing:
        raise SystemExit(f"Tables not assigned to a domain: {missing}")
    unknown = sorted(set(TABLE_DOMAIN) - set(tables))
    if unknown:
        raise SystemExit(f"Domain names absent from the database: {unknown}")

    mxfile = ET.Element("mxfile", host="RescueVision ERD generator")
    stats: dict = {"pages": []}
    emit_overview(mxfile, tables, fks, stats)
    for page_no, (domain_key, *_rest) in enumerate(DOMAINS, start=2):
        emit_domain_page(mxfile, page_no, domain_key, tables, fks, stats)
    emit_full_page(mxfile, 10, tables, fks, stats)

    ET.indent(mxfile, space="  ")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(mxfile, encoding="unicode") + "\n",
        encoding="utf-8",
    )
    validate(OUT_PATH, tables, fks, stats)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
