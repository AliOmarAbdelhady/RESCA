# RESCA ERD (draw.io)

Entity-relationship diagram of the RESCA PostgreSQL schema
(`database/schema`): 56 tables, 140 foreign keys, 9 subject areas.

| File | Contents |
|---|---|
| `resca-erd.drawio` | Editable diagram (open in draw.io / diagrams.net) |
| `resca-erd.pdf` | All pages as one PDF |
| `png/page-00.png` … `page-10.png` | High-resolution page exports |
| `tools/gen_erd.py`, `tools/parse_schema.py` | Generator: parses the SQL and rebuilds the diagram |

## Pages

- **00 · Overview & Legend**: subject-area cards, cross-domain FK matrix, notation
- **01 · Full ERD**: every table and relationship, grouped by subject area
- **02–10**: one page per subject area with full columns; tables from other
  areas appear as dashed "keys only" stubs, tagged with their page number

## Notation

- Crow's foot: `||` exactly one (FK NOT NULL), `o|` zero or one, `o<` zero or many
- `PK` primary key · `FK` foreign key · `AKn` unique constraint group · `NN` NOT NULL
- Purple italic types are enums; green types are PostGIS / pgvector
- Hover a table, column or relationship in draw.io for ON DELETE rules,
  defaults, CHECK constraints and column comments

## Regenerate

```bash
python3 mahmoudERD/tools/gen_erd.py database/schema mahmoudERD/resca-erd.drawio
```
