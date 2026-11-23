"""Generate the data dictionary appendix (Markdown) from the live catalog.

Tables are grouped by the same domains as Figures 3-6 to 3-14. Run against a
database built from database/schema:

    PGHOST=localhost PGPORT=55432 PGUSER=postgres PGPASSWORD=test \
        python3 docs/documentation/chapter5/tools/gen_data_dictionary.py
"""
import subprocess
from pathlib import Path

from gen_erd_puml import DOMAINS

OUT = Path(__file__).resolve().parent.parent / "appendix_data_dictionary.md"

SQL = r"""
select c.relname, a.attnum, a.attname,
       format_type(a.atttypid, a.atttypmod),
       case when a.attnotnull then 'no' else 'yes' end,
       coalesce(pg_get_expr(d.adbin, d.adrelid), ''),
       coalesce((select string_agg(case k.contype when 'p' then 'PK' when 'u' then 'UQ'
                   when 'f' then 'FK → ' || k.confrelid::regclass::text end, ', ' order by k.contype)
                 from pg_constraint k
                 where k.conrelid = c.oid and a.attnum = any(k.conkey)
                   and k.contype in ('p','u','f')), '')
from pg_class c
join pg_namespace n on n.oid = c.relnamespace and n.nspname = 'public'
join pg_attribute a on a.attrelid = c.oid and a.attnum > 0 and not a.attisdropped
left join pg_attrdef d on d.adrelid = c.oid and d.adnum = a.attnum
where c.relkind in ('r','p') and not c.relispartition and c.relname <> 'spatial_ref_sys'
order by c.relname, a.attnum
"""


def main():
    rows = subprocess.run(["psql", "-d", "rescuevision", "-AtF", "\t", "-c", SQL],
                          check=True, capture_output=True, text=True).stdout.splitlines()
    cols = {}
    for line in rows:
        t, _, name, typ, null, default, keys = line.split("\t")
        cols.setdefault(t, []).append((name, typ, null, default, keys))

    out = ["# Appendix: Data Dictionary",
           "",
           "Generated from the PostgreSQL catalog of the implemented schema "
           "(`database/schema`). Tables are grouped by the information domains of "
           "Section 3.3.3. Null = whether the column accepts NULL; PK primary key, "
           "UQ unique, FK foreign key with its target table.", ""]
    seen = set()
    for _key, title, tables in DOMAINS:
        out += [f"## {title}", ""]
        for t in tables:
            if t not in cols or t in seen:
                continue
            seen.add(t)
            out += [f"### {t}", "", "| Column | Type | Null | Default | Key |", "|---|---|---|---|---|"]
            for name, typ, null, default, keys in cols[t]:
                default = default.replace("|", "\\|")
                out.append(f"| {name} | {typ} | {null} | {default and '`' + default + '`'} | {keys} |")
            out.append("")
    missing = sorted(set(cols) - seen)
    if missing:
        out += ["## Other tables", ""] + [f"- {m}" for m in missing]
    OUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(seen)} tables, {sum(len(cols[t]) for t in seen)} columns -> {OUT}; ungrouped: {missing}")


if __name__ == "__main__":
    main()
