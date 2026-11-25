# RESCA Database

PostgreSQL schema for the RESCA multi-agency disaster-response platform:
56 tables in 8 domains, built on PostGIS (maps), pgRouting (rescue routes) and
pgvector (similar past cases). Design rationale:
[`docs/superpowers/specs/2026-11-23-resca-database-erd-design.md`](../docs/superpowers/specs/2026-11-23-resca-database-erd-design.md).

## Requirements

| Component  | Version tested |
|------------|----------------|
| PostgreSQL | 18.7 (18.x required: uses native `uuidv7()`) |
| PostGIS    | 3.6.4 |
| pgRouting  | 4.0.2 |
| pgvector   | 0.8.7 |

Ubuntu 26.04 setup (official PostgreSQL apt repository):

```bash
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
sudo apt update
sudo apt install -y postgresql-18 postgresql-18-postgis-3 postgresql-18-pgvector postgresql-18-pgrouting
sudo -u postgres createuser --superuser "$USER"     # local development only
```

## Build

```bash
./database/build.sh             # schema + security + reference data + demo scenario + self-checks
./database/build.sh --no-demo   # schema + reference data only
DB_NAME=resca_test ./database/build.sh
```

`build.sh` **drops and recreates** the target database (default `resca`).
It uses the standard libpq variables (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`).

## Layout

| Path | Contents |
|---|---|
| `schema/00_extensions.sql` | postgis, pgrouting, vector, citext, pgcrypto; `set_updated_at()` trigger |
| `schema/01_types.sql` | all enum types |
| `schema/02_identity_access.sql` | D1: agencies, roles, permissions, users, sessions, devices, teams, members, vehicles |
| `schema/03_incidents_operations.sql` | D2: incidents, incident_agencies, zones, missions, assignments, status history |
| `schema/04_imagery_ai.sql` | D3: capture sessions, images, rasters, model registry, jobs, inference runs |
| `schema/05_citizens_media.sql` | citizens, media files, citizen requests (auto-matched to an incident) |
| `schema/06_buildings_cost.sql` | F1: buildings, damage assessments, cost profiles, cost estimates |
| `schema/07_roads.sql` | F2: pgRouting nodes/edges, road condition observations |
| `schema/08_persons_cases.sql` | F3/F4: tracks, detections, facilities, assistance cases, case events |
| `schema/09_hazards_alerts.sql` | F5: infrastructure, hazards, hazard rules, compound alerts |
| `schema/10_routing.sql` | F2: routes, route segments, alert-closed segments |
| `schema/11_field_reports_audit.sql` | GPS (partitioned), SOS, notifications, reports, embeddings, audit log (partitioned) |
| `schema/12_hazard_engine.sql` | `evaluate_hazard_rules()`, `resolve_compound_alert()` |
| `schema/13_views.sql` | dashboard read models |
| `schema/14_fk_indexes.sql` | supporting indexes for joined / cascading foreign keys |
| `schema/15_security.sql` | app roles, session context, Row-Level Security on all 56 tables, column guards, audit trail |
| `seed/01_reference_data.sql` | roles, permissions, hazard rules, cost profile, model registry |
| `seed/02_demo_scenario.sql` | fictional Downtown Cairo scenario exercising every feature |
| `tests/checks.sql` | self-checks run by `build.sh` |

## Security model

`15_security.sql` turns on Row-Level Security for **every** table (default
deny) and adds 4 group roles. Applications never connect as the owner.

| Role | Used by | Sees |
|---|---|---|
| `resca_app` | the API, acting for a signed-in agency user | only incidents their agency has **actively joined** (Platform Admin: all); rules per role/permission below |
| `resca_worker` | AI / Celery pipeline | everything (service account, no user context) |
| `resca_citizen` | public citizen app | only that citizen's own profile, requests and uploads |
| `resca_readonly` | analytics / BI | operational data read-only; no credentials, sessions, citizens or audit log |

What the policies enforce (all derived from `users.role_code` →
`role_permissions`, re-checked on every request, so a suspended user is locked
out immediately):

- **Incident isolation:** an agency sees an incident, its buildings, roads,
  cases, alerts, routes, imagery and reports only while its
  `incident_agencies` row is `ACTIVE`. Invited agencies see the incident header
  and answer with `app.respond_to_invitation()`.
- **Who may write:** commanders create/manage their own agency's missions;
  responders update only missions they are assigned to; analysts run analysis
  and review assessments; only `alert.resolve` holders resolve alerts.
- **Column guards:** without the managing permission a user may change only
  safe columns (a responder can set a mission's status, not its target; a user
  can edit their name/phone, not their role or agency).
- **Private data:** notifications, sessions and devices are visible to their
  owner only; draft reports stay inside the authoring agency until approved or
  shared; password hashes are unreadable by every app role (sign-in goes
  through `app.get_login()`); partitions cannot be queried directly.
- **Audit trail:** inserts/updates/deletes on 27 key tables are written to
  `audit_log` with the acting user, by a `SECURITY DEFINER` trigger.

Create the login roles once per server (choose your own passwords):

```sql
CREATE ROLE resca_api      LOGIN PASSWORD '...' IN ROLE resca_app;
CREATE ROLE resca_worker   LOGIN PASSWORD '...' IN ROLE resca_worker;
CREATE ROLE resca_citizen  LOGIN PASSWORD '...' IN ROLE resca_citizen;
CREATE ROLE resca_bi       LOGIN PASSWORD '...' IN ROLE resca_readonly;
GRANT CONNECT ON DATABASE resca TO resca_app, resca_worker, resca_citizen, resca_readonly;
```

Per request the API sets who is acting, inside the request's transaction
(the setting is transaction-local, so pooled connections cannot leak it):

```sql
BEGIN;
SELECT app.set_session_user('<users.id from the JWT>');     -- staff
-- or SELECT app.set_session_citizen('<citizens.id>');      -- citizen app
SELECT * FROM v_open_cases;                                  -- RLS-filtered
COMMIT;
```

Try it in `psql` as the demo paramedic:

```sql
BEGIN;
SELECT app.set_session_user((SELECT id FROM users WHERE email = 'para1@ems.demo'));
SET LOCAL ROLE resca_app;
SELECT count(*) FROM incidents;          -- 1: their agency joined it
SELECT count(*) FROM notifications;      -- only their own
SELECT password_hash FROM users;         -- ERROR: permission denied
ROLLBACK;
```

## Regenerating the ERD

`docs/database/resca-erd.drawio` is generated from the live catalog (not
hand-written). With a built database reachable through the usual libpq variables
(defaults: `localhost:55432`, user `postgres`, database `resca`):

```bash
python3 database/tools/generate_drawio_erd.py
```

The generator reads tables, columns, primary keys, unique columns and foreign
keys from `pg_class` / `pg_attribute` / `pg_constraint` / `pg_index` using
`psql`, then writes a 10-page draw.io file:

1. **Overview**: the 8 domains with their table names and one labelled link per
   pair of related domains (fits one screen; start here).
2. **Pages 2-9**: one per domain, full columns, parents above children; tables
   from other domains appear as grey stubs above the tables that use them.
3. **Full ERD**: all 56 tables grouped in domain clusters.

"Who did it" columns that point at `users` (`created_by`, `approved_by`, ...)
are shown as `FK → users` rows instead of lines, so the real relationships stay
readable. Lines are coloured by the parent table's domain. The generator checks
the XML, the table/FK counts, and that no boxes overlap; a non-zero exit means
generation failed.

## Try the demo

```sql
-- damage + cost totals
SELECT * FROM v_incident_damage_summary;

-- the Electrified Water alert and the roads it closed
SELECT a.title, a.status, count(c.segment_id) AS roads_closed
FROM compound_alerts a LEFT JOIN alert_closed_segments c ON c.alert_id = a.id
GROUP BY a.id;

-- the rescue route that was cut, and who was warned
SELECT status, invalidated_by_alert_id FROM routes;
SELECT u.full_name, n.body FROM notifications n JOIN users u ON u.id = n.user_id;

-- the power company cuts the line: resolve the alert, roads re-open
SELECT resolve_compound_alert(id, NULL, 'Power cut by utility')
FROM compound_alerts WHERE title LIKE 'Electrified Water%';
```
