# Database

PostgreSQL 18 with PostGIS 3.6, pgRouting and pgvector. 56 tables in ten domains, row-level security on protected tables, a PL/pgSQL hazard engine. The schema is the best-tested part of the project; protect it. Details of every table: [database/README.md](../database/README.md).

## What lives where

| Path | Purpose |
|---|---|
| `database/schema/00-15_*.sql` | The frozen baseline. Do not edit applied files; add a migration instead. |
| `database/schema/15_security.sql` | Roles and RLS policies. **Locked**: only the owner changes the security model. |
| `database/migrations/` | New forward-only dbmate migrations (`YYYYMMDDHHMMSS_name.sql`). |
| `database/seed/` | `01` reference data (always); `02` fictional demo scenario (demo profile only). |
| `database/tests/checks.sql` | Self-checks run by `build.sh` and `make check-db`. |

Roles: `rescuevision_app` (API, RLS applies), `rescuevision_worker` (jobs), `rescuevision_citizen` (citizen channel), `rescuevision_readonly` (reports and analysis). Migrations run with a separate owner credential.

## Rules

| ID | Rule | Gate |
|---|---|---|
| D1 | Migrations are forward-only and safe to run while the old code is live: expand, backfill, then contract in a later release. Set `lock_timeout` and `statement_timeout`. Never run `build.sh` (it drops the database) against anything but a throwaway database. | Squawk on changed migrations; dbmate up twice from empty and from the last release |
| D2 | Every new table that holds incident, person, location or media data has RLS enabled and policies for each role, tested by logging in as each real role (allowed and denied, active and revoked membership). Check `relrowsecurity`, direct partition access and `SECURITY DEFINER` functions' `search_path`. | Role-matrix tests in `checks.sql` style |
| D3 | Constraints live in the database: `NOT NULL`, foreign keys, unique business keys (including idempotency keys), `CHECK` ranges, geometry type and SRID. Data written directly in SQL must be rejected the same way as through the API. | Direct-insert tests |
| D4 | Index every foreign key and every column used to filter or join at scale; use GiST for geometry and index-aware predicates (`ST_DWithin` on `geography` or a projected SRID, distances in metres). Check `EXPLAIN (ANALYZE, BUFFERS)` on realistic data for new queries. | FK-index check in `checks.sql`; plan review |
| D5 | Protected changes are audited (actor, action, object, time, result). Application roles cannot update or delete audit history. Audit rows never store secrets. | Audit tests |
| D6 | Each data class (GPS tracks, media, events, audit, backups) has an owner-approved retention period; expired data is deleted from the database, object storage and derived copies. | Clock-advance tests |
| D7 | Reference data, the fictional demo scenario and per-test fixtures stay separate. Release builds contain no demo incidents. | Bootstrap twice; release check |

Naming: tables plural `snake_case`; primary keys `id uuid` (UUIDv7, so offline clients can create IDs); timestamps `timestamptz` named `*_at`; enums in `01_types.sql`.

## Known defects to fix first

Found by the architecture review; each fix needs a regression test in `checks.sql`.

1. A field responder's flood report cannot run the hazard engine under RLS (UC-07): the responder holds neither `analysis.run` nor `alert.resolve`. Decide the privilege model (likely a narrow `SECURITY DEFINER` function) with the owner.
2. Closing and reopening overlapping road closures in some orders leaves a road closed permanently.
3. `seed/01_reference_data.sql` marks models active that have no weights or evaluation.
4. `person_detections` has no review state, so a person cannot confirm or reject a detection (A6).
5. New tables needed: `view_presets` (DEC-12), outbox and event log with per-incident cursor (C2), idempotency keys (B5), job leases (B11).
6. 23 actor columns (`created_by`, `reviewed_by`, `acknowledged_by` and similar) are foreign keys without an index; `checks.sql` lists them as a notice. Index the ones used in joins or user deletion, and record why the rest are left (D4).

## Gate

`make check-db` builds the schema and seeds in a throwaway PostGIS 18 container (with pgRouting and pgvector) and runs `checks.sql`. `checks.sql` expects exactly 56 tables, so dbmate's migration table must live in its own schema or the count must be updated by the owner.
