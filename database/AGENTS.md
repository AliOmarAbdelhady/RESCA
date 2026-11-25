# database/AGENTS.md

PostgreSQL 18 + PostGIS + pgRouting + pgvector. Read [docs/DATABASE.md](../docs/DATABASE.md) and [README.md](README.md) before any change. Locked.

Gate: `make check-db` (builds a throwaway database and runs `tests/checks.sql`).

Most-broken rules here:
1. Editing an applied schema file instead of adding a forward-only migration (D1).
2. A new table with personal, incident or location data and no RLS policies and role tests (D2).
3. A foreign key or filter column without an index; distances in degrees instead of metres (D4).
4. Constraints left to the API instead of the database (D3).
5. Running `build.sh` against a database that is not throwaway: it drops everything (D1).
6. Changing `schema/15_security.sql`: owner only.
