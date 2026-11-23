# RescueVision Database

PostgreSQL schema for the RescueVision multi-agency disaster-response platform:
56 tables in 8 domains, built on PostGIS (maps), pgRouting (rescue routes) and
pgvector (similar past cases). Design rationale:
[`docs/superpowers/specs/2026-11-23-rescuevision-database-erd-design.md`](../docs/superpowers/specs/2026-11-23-rescuevision-database-erd-design.md).

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
./database/build.sh             # schema + reference data + demo scenario + self-checks
./database/build.sh --no-demo   # schema + reference data only
DB_NAME=rv_test ./database/build.sh
```

`build.sh` **drops and recreates** the target database (default `rescuevision`).
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
| `seed/01_reference_data.sql` | roles, permissions, hazard rules, cost profile, model registry |
| `seed/02_demo_scenario.sql` | fictional Downtown Cairo scenario exercising every feature |
| `tests/checks.sql` | self-checks run by `build.sh` |

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
