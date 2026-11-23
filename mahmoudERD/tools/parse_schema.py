"""Parse RescueVision PostgreSQL DDL files into a simple table/column/FK model."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

KEYWORDS = {"NOT", "NULL", "PRIMARY", "REFERENCES", "DEFAULT", "CHECK", "UNIQUE",
            "GENERATED", "CONSTRAINT", "COLLATE"}


@dataclass
class Column:
    name: str
    type: str
    not_null: bool = False
    pk: bool = False
    unique: bool = False
    default: str | None = None
    generated: str | None = None  # "identity" | "stored"
    comment: str | None = None
    ak: list[int] = field(default_factory=list)


@dataclass
class FK:
    table: str
    column: str
    ref_table: str
    ref_column: str
    on_delete: str = "NO ACTION"


@dataclass
class Table:
    name: str
    file: str
    columns: list[Column] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    partition: str | None = None
    unique_indexes: list[str] = field(default_factory=list)

    def col(self, name: str) -> Column:
        return next(c for c in self.columns if c.name == name)


def split_top(body: str) -> list[str]:
    parts, depth, cur, q = [], 0, [], False
    for ch in body:
        if ch == "'":
            q = not q
        if not q:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append("".join(cur).strip())
                cur = []
                continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def strip_comments(sql: str) -> str:
    out = []
    for line in sql.splitlines():
        q = False
        for i, ch in enumerate(line):
            if ch == "'":
                q = not q
            if not q and line[i:i + 2] == "--":
                line = line[:i]
                break
        out.append(line)
    return "\n".join(out)


def tokenize(s: str) -> list[str]:
    toks, depth, cur, q = [], 0, [], False
    for ch in s:
        if ch == "'":
            q = not q
        if not q and ch in "()":
            depth += 1 if ch == "(" else -1
        if ch.isspace() and depth == 0 and not q:
            if cur:
                toks.append("".join(cur))
                cur = []
            continue
        cur.append(ch)
    if cur:
        toks.append("".join(cur))
    return toks


def parse(schema_dir: Path):
    tables: dict[str, Table] = {}
    fks: list[FK] = []
    order: list[str] = []
    for f in sorted(schema_dir.glob("*.sql")):
        raw = f.read_text()
        # column comments from raw lines inside CREATE TABLE bodies
        for m in re.finditer(r"CREATE TABLE (\w+) \(", raw):
            name = m.group(1)
            start = m.end()
            depth, i, q = 1, start, False
            while depth:
                ch = raw[i]
                if ch == "'":
                    q = not q
                elif not q and ch == "(":
                    depth += 1
                elif not q and ch == ")":
                    depth -= 1
                i += 1
            raw_body = raw[start:i - 1]
            tail = raw[i:raw.index(";", i)]
            t = Table(name, f.name)
            comments = {}
            for line in raw_body.splitlines():
                cm = re.match(r"\s*(\w+)\s.*?--\s*(.+)$", line)
                if cm and cm.group(1).upper() not in ("CONSTRAINT", "PRIMARY"):
                    comments[cm.group(1)] = cm.group(2).strip()
            body = strip_comments(raw_body)
            ak_n = 0
            for part in split_top(body):
                part = " ".join(part.split())
                up = part.upper()
                if up.startswith("CONSTRAINT"):
                    m2 = re.match(r"CONSTRAINT (\w+) (.*)", part, re.S)
                    cname, rest = m2.group(1), m2.group(2)
                    if rest.upper().startswith("UNIQUE"):
                        cols = [c.strip() for c in re.search(r"\((.*)\)", rest).group(1).split(",")]
                        ak_n += 1
                        for c in cols:
                            t.col(c).ak.append(ak_n)
                    elif rest.upper().startswith("CHECK"):
                        t.checks.append(cname)
                    continue
                if up.startswith("PRIMARY KEY"):
                    cols = [c.strip() for c in re.search(r"\((.*)\)", part).group(1).split(",")]
                    for c in cols:
                        t.col(c).pk = True
                        t.col(c).not_null = True
                    continue
                toks = tokenize(part)
                cname = toks[0]
                ti = 1
                while ti < len(toks) and toks[ti].upper() not in KEYWORDS:
                    ti += 1
                ctype = " ".join(toks[1:ti])
                ctype = re.sub(r",\s*", ",", ctype)
                col = Column(cname, ctype, comment=comments.get(cname))
                rest = " ".join(toks[ti:])
                ur = rest.upper()
                if "NOT NULL" in ur:
                    col.not_null = True
                if "PRIMARY KEY" in ur:
                    col.pk = True
                    col.not_null = True
                if re.search(r"\bUNIQUE\b", ur):
                    col.unique = True
                    ak_n += 1
                    col.ak.append(ak_n)
                if "GENERATED ALWAYS AS IDENTITY" in ur:
                    col.generated = "identity"
                    col.not_null = True
                elif "GENERATED ALWAYS AS" in ur:
                    col.generated = "stored"
                dm = re.search(r"DEFAULT (\S+)", rest)
                if dm:
                    col.default = dm.group(1)
                rm = re.search(r"REFERENCES (\w+)\((\w+)\)(?: ON DELETE (SET NULL|CASCADE|RESTRICT|NO ACTION))?", rest)
                if rm:
                    fks.append(FK(name, cname, rm.group(1), rm.group(2), rm.group(3) or "NO ACTION"))
                if re.search(r"\bCHECK\b", ur):
                    t.checks.append(f"{cname} check")
                t.columns.append(col)
            pm = re.search(r"PARTITION BY (\w+) \((\w+)\)", tail)
            if pm:
                t.partition = f"{pm.group(1)} ({pm.group(2)})"
            tables[name] = t
            order.append(name)
        clean = strip_comments(raw)
        for m in re.finditer(r"ALTER TABLE (\w+)\s+ADD CONSTRAINT \w+\s+FOREIGN KEY \((\w+)\) REFERENCES (\w+)\((\w+)\)(?: ON DELETE (SET NULL|CASCADE|RESTRICT))?", clean):
            fks.append(FK(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5) or "NO ACTION"))
        for m in re.finditer(r"CREATE UNIQUE INDEX (\w+) ON (\w+) \(([^)]*)\)(.*?);", clean):
            if m.group(2) in tables:
                tables[m.group(2)].unique_indexes.append(f"{m.group(1)} ({m.group(3)}){m.group(4)}")
    # partitions are physical children, not separate entities
    for n in [n for n in order if n.endswith("_default")]:
        pass
    return tables, fks, order


if __name__ == "__main__":
    import sys
    tables, fks, order = parse(Path(sys.argv[1]))
    print(len(tables), "tables", len(fks), "fks")
    for t in order:
        print(t, len(tables[t].columns))
