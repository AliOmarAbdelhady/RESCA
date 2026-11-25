"""Generate the per-domain logical ERD figures (PlantUML) for Section 3.3.3.

Reads the live RESCA catalog through psql (standard PG* variables), so
the figures always match database/schema. One .puml per domain is written to
figures/src/. Columns are shown with PK/FK markers and compact types;
references to tables in other domains are written on the column ("→ incidents")
instead of drawn, so each figure shows only the relationships inside its domain.

    PGHOST=localhost PGPORT=55432 PGUSER=postgres PGPASSWORD=... \\
        python3 tools/gen_erd_puml.py
"""
import os
import re
import subprocess
from pathlib import Path

DOMAINS = [
    ("d1", "Identity and Access",
     ["agencies", "roles", "permissions", "role_permissions", "users",
      "user_sessions", "user_devices", "teams", "team_members", "vehicles"]),
    ("d2", "Incidents and Operations",
     ["incidents", "incident_agencies", "zones", "missions",
      "mission_assignments", "mission_status_history"]),
    ("d3", "Imagery and Analysis Pipeline",
     ["capture_sessions", "images", "raster_products", "ai_models",
      "processing_jobs", "inference_runs"]),
    ("d4a", "F1 Buildings and Cost",
     ["buildings", "building_assessments", "cost_profiles",
      "cost_profile_unit_rates", "cost_profile_repair_ratios", "cost_estimates"]),
    ("d4b", "F2 Roads and Routing",
     ["road_nodes", "road_segments", "road_condition_observations", "routes",
      "route_segments", "alert_closed_segments"]),
    ("d4c", "F3/F4 Persons and Cases",
     ["person_tracks", "person_detections", "facilities", "assistance_cases",
      "case_events"]),
    ("d4d", "F5 Hazards and Alerts",
     ["infrastructure_assets", "hazards", "hazard_rules", "compound_alerts",
      "compound_alert_sources"]),
    ("d5a", "Field Operations and Notifications",
     ["responder_positions", "responder_last_positions", "sos_alerts",
      "notifications"]),
    ("d5b", "Citizens, Reports and Audit",
     ["citizens", "citizen_requests", "media_files", "citizen_request_media",
      "reports", "report_shares", "image_embeddings", "audit_log"]),
]
AUDIT = {
    "created_by", "invited_by", "assigned_by", "changed_by", "uploaded_by",
    "requested_by", "reviewed_by", "verified_by", "acknowledged_by",
    "resolved_by", "approved_by", "generated_by", "shared_by", "reported_by",
    "actor_id", "assessed_by", "uploaded_by_user",
}
LTR = {"d5b"}
# Layout hints for tables with no in-domain lines (keeps the figure A4-width).
EXTRA = {"d5b": ["report_shares -[hidden]down- audit_log",
                 "citizen_request_media -[hidden]down- image_embeddings"]}
OUT = Path(__file__).resolve().parent.parent / "figures" / "src"


def q(sql):
    db = os.environ.get("PGDATABASE", "resca")
    r = subprocess.run(["psql", "-X", "-At", "-F", "\t", "-d", db, "-c", sql],
                       check=True, capture_output=True, text=True)
    return [line.split("\t") for line in r.stdout.splitlines() if line]


def short_type(t):
    t = re.sub(r"geometry\((\w+),4326\)", r"geom \1", t)
    t = re.sub(r"geography\((\w+),4326\)", r"geog \1", t)
    t = t.replace("timestamp with time zone", "timestamptz")
    t = t.replace("character varying", "varchar").replace("double precision", "float8")
    return t


cols = {}
for rel, name, typ, notnull in q("""
    SELECT c.relname, a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull
    FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
    WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r','p')
      AND NOT c.relispartition AND c.relname <> 'spatial_ref_sys'
      AND a.attnum > 0 AND NOT a.attisdropped
    ORDER BY c.relname, a.attnum"""):
    cols.setdefault(rel, []).append((name, short_type(typ), notnull == "t"))

pks = {}
for rel, col in q("""
    SELECT c.relname, a.attname FROM pg_constraint k
    JOIN pg_class c ON c.oid = k.conrelid
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY (k.conkey)
    WHERE k.contype = 'p' AND c.relnamespace = 'public'::regnamespace"""):
    pks.setdefault(rel, set()).add(col)

fks = []  # (child, column, parent, notnull)
for child, col, parent in q("""
    SELECT c.relname, a.attname, p.relname FROM pg_constraint k
    JOIN pg_class c ON c.oid = k.conrelid JOIN pg_class p ON p.oid = k.confrelid
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.conkey[1]
    WHERE k.contype = 'f' AND c.relnamespace = 'public'::regnamespace
      AND NOT c.relispartition"""):
    nn = next(n for (cn, _, n) in cols[child] if cn == col)
    fks.append((child, col, parent, nn))
fk_cols = {(c, col): p for c, col, p, _ in fks}

assert sum(len(d[2]) for d in DOMAINS) == len(cols), "domain list out of date"

for key, title, tables in DOMAINS:
    own = set(tables)
    # Lines only inside the domain; references to other domains are noted on the column.
    edges = [f for f in fks if f[0] in own and f[2] in own
             and not (f[1] in AUDIT and f[2] == "users")]
    lines = ["@startuml", "!include _style.iuml", "skinparam linetype ortho",
             *(["left to right direction"] if key in LTR else []),
             *(["skinparam nodesep 16", "skinparam ranksep 34"] if key in LTR
               else ["skinparam nodesep 30", "skinparam ranksep 45"]), ""]
    for t in tables:
        lines.append(f'entity "{t}" as {t} {{')
        for name, typ, nn in cols[t]:
            mark = []
            if name in pks.get(t, ()):
                mark.append("PK")
            if (t, name) in fk_cols:
                mark.append("FK")
            m = ",".join(mark)
            label = f"<b>{name}</b>" if "PK" in mark else name
            parent = fk_cols.get((t, name))
            suffix = f" → {parent}" if parent and parent not in own else ""
            req = "" if nn or "PK" in mark else " <color:#7a8ba0>?</color>"
            lines.append(f"  {('<size:10>' + m + '</size> ') if m else ''}{label} : {typ}{req}"
                         f"{'<color:#7a8ba0>' + suffix + '</color>' if suffix else ''}")
        lines.append("}")
    seen = set()
    for child, col, parent, nn in edges:
        if child == parent:
            arrow = "}o--o|"
        else:
            arrow = "}o--||" if nn else "}o--o|"
        k = (child, parent, col)
        if k in seen:
            continue
        seen.add(k)
        lines.append(f"{child} {arrow} {parent} : {col}")
    lines += EXTRA.get(key, [])
    lines.append("@enduml")
    (OUT / f"fig_erd_{key}.puml").write_text("\n".join(lines) + "\n")
    print(f"fig_erd_{key}.puml: {len(tables)} tables, {len(seen)} relationships drawn")
