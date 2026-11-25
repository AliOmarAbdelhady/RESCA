# RescueVision — System Architecture Blueprint (`ARCHITECTURE.md`)

**Status:** Target Implementation Architecture (Single Source of Truth for Engineering & AI Agents)
**Primary Stack:** FastAPI Modular Monolith · PostgreSQL 18 (PostGIS 3.6 + pgRouting 4.0 + pgvector 0.8 + RLS) · Procrastinate (`SKIP LOCKED`) · Redis · MinIO · Martin (Rust MVT) · TiTiler (COG) · NodeODM · LitServe GPU Model Containers · Vite + React + TanStack Router/Query + MapLibre/CesiumJS · Expo Dev Build + Expo Router + MapLibre Native (`PMTiles`) + `OP-SQLite`

---

## 1. Real Design Tensions Resolved from Existing Docs

Before writing application code, this blueprint resolves six concrete architectural contradictions found across the initial repository docs:

1. **Synchronous Prototype (`api/main.py`) vs. Async Queue (`D-03`):** `api/main.py` loads `DisasterPredictor` in-process and blocks `POST /predict`. **Resolution:** Remove all `torch`/model loading from `backend/api`; execute analysis asynchronously via `processing_jobs` (`Procrastinate`) calling isolated `LitServe` Docker containers (`ai-*-svc`).
2. **`15_security.sql` ("AI / Celery pipeline") vs. `section_3_3.md` §3.3.6 ("database lock that skips rows"):** The repo mentions both Celery and Postgres `SKIP LOCKED`. **Resolution:** Standardize on **PostgreSQL `SKIP LOCKED` + `LISTEN/NOTIFY` (`Procrastinate`)** as the sole durable job queue—zero dual-write race conditions and no RabbitMQ/Celery broker needed. Use **Redis** exclusively for ephemeral WebSocket Pub/Sub fan-out, OTP rate limits, and GPS ping coalescing.
3. **Report `D-02` ("small number of services") vs. Owner Requirement ("AI models isolated in Docker behind APIs"):** **Resolution:** Keep all 8 business domains inside **one FastAPI Modular Monolith** (`backend/api`), while separating **runtime boundaries** into `geo-worker`, `nodeodm`, `martin`, `titiler`, and 4 stateless `LitServe` model-family containers.
4. **Two Web Apps (`dashboard/` vs. `frontend/apps/web/`) & Router Choice:** **Resolution:** Deprecate legacy `dashboard/` after porting `RouteMap.tsx` concepts into `frontend/apps/web/`. Upgrade `frontend/apps/web/README.md` from plain React Router to **TanStack Router + TanStack Query** for Zod-validated shareable map URL state.
5. **Martin Direct DB Access vs. Row-Level Security (`D-04`):** If `martin` connects directly to Postgres without per-request user context, any agency could fetch another incident's vector tiles. **Resolution:** Expose only **incident-scoped PostGIS MVT functions** in Martin (`app.mvt_*`) validated with short-lived HMAC/JWT tile tokens (or Caddy `forward_auth` calling `core-api`), executing `SET LOCAL` inside the tile query transaction.
6. **Expo Go Assumption vs. Native Offline Maps (`D-08`):** Offline `MapLibre` (`pmtiles://`) and `OP-SQLite` do not run in Expo Go. **Resolution:** Standardize `apps/mobile` on **Expo Development Builds (Prebuild/CNG + EAS)**.

---

## 2. Five-Plane Runtime Topology

```text
Plane 1: Clients        -> apps/web (TanStack Router + MapLibre + CesiumJS)
                           apps/mobile (Expo Dev Build + MapLibre PMTiles + OP-SQLite + optional Meshtastic BLE)
                           Citizen Phone-OTP Web Form
Plane 2: Edge & Tiles   -> Caddy (TLS, Auth, Routing) + Martin (Rust MVT) + TiTiler (COG Raster Tiles)
Plane 3: App & Realtime -> core-api (FastAPI Modular Monolith: 8 domain modules + WS Hub + Copilot) + Redis Pub/Sub
Plane 4: Async & AI     -> geo-worker (Procrastinate SKIP LOCKED) + NodeODM + 4x LitServe GPU Containers (ai-net)
Plane 5: Data & Files   -> PostgreSQL 18 (PostGIS/pgRouting/pgvector/RLS) + PgBouncer + MinIO (S3)
```

---

## 3. Core Architectural Rules & Patterns

### 3.1 Modular Monolith Boundaries (`backend/api/app/modules/`)
* Eight modules mirror the 8 ERD domains (`identity`, `incidents`, `imagery`, `buildings_cost`, `routing`, `cases`, `hazards`, `field_reports`).
* Cross-module calls go only through each module's `service.py` public interface (enforced via `import-linter`), keeping `D-02` future extraction clean without distributed-transaction overhead today.

### 3.2 Transaction-Scoped RLS + PgBouncer Contract (`D-04`)
Every request handler in `core-api` acquires a DB connection through a mandatory dependency that opens an explicit transaction and binds the acting user/citizen before any query runs:
```sql
BEGIN;
SELECT app.set_session_user($1);  -- or app.set_session_citizen($1)
SET LOCAL ROLE rv_app;            -- or rv_citizen
-- all domain queries & pgRouting calls run here
COMMIT;
```
* **PgBouncer Rule:** Because PgBouncer runs in **transaction mode**, `asyncpg`/`psycopg3` must disable server-side prepared statements (`statement_cache_size=0` / `prepare_threshold=None`) and **never** use session-level `SET`.

### 3.3 Real-Time Channel (`D-10`)
1. High-frequency responder GPS pings arrive over WebSocket or batched REST, are throttled/coalesced in **Redis** (e.g., max 1 DB write every 3s per responder unless SOS), and written to `responder_positions` (updating `responder_last_positions` via trigger).
2. Database-driven events (`compound_alerts`, `routes` invalidations, `processing_jobs` progress) emit Postgres **`NOTIFY`**. A single async listener in `core-api` forwards events to **Redis Pub/Sub** channel `incident:{id}`, and every API replica delivers payloads only to WebSocket sessions whose `incident_agencies` status is still `ACTIVE`.

### 3.4 Offline-First Mobile Sync & Mesh Fallback (`D-08`)
* **Primary Offline Engine:** `apps/mobile` stores assigned missions, offline `.pmtiles` map packs, and an outbox mutation table in **`OP-SQLite`**. Every offline record generates a client **`uuidv7()`** and attaches an **`Idempotency-Key`** header so retries on flaky disaster networks never duplicate `hazards`, `sos_alerts`, or `case_events`.
* **Optional LoRa Mesh Relay (`Meshtastic`):** When cellular coverage is 0%, `apps/mobile` can optionally serialize critical `<200-byte` SOS/Flood-Hazard packets over BLE to a **Meshtastic LoRa radio**, relayed to a command-post USB/BLE gateway that submits them to `core-api`.

### 3.5 Spatial Commander Copilot (Read-Only Tool Calling)
* Located in `backend/api/app/copilot/`, exposed only to `COMMANDER` and `ANALYST` roles.
* Uses structured LLM tool-calling backed exclusively by **RLS-scoped `rv_app` read transactions** (`v_incident_damage_summary`, `v_open_cases`, `pgr_aStar` dry-runs, and `image_embeddings` `pgvector` HNSW cosine similarity).
* **Hard Safety Guard (`D-07`):** The Copilot has **zero write tools**. It cannot confirm cases, resolve alerts, close roads, or assign missions—it produces cited summaries and recommended actions for a human to click.

---

## 4. End-to-End Critical Workflows

### Flow A: Drone Upload → Orthomosaic → Damage Map & Cost Estimates
1. Analyst creates `capture_sessions` (`POST_EVENT`) via `core-api`; `core-api` returns 5-minute pre-signed MinIO `PUT` URLs.
2. Client uploads raw images directly to MinIO (`incidents/{id}/captures/{session}/raw/...`) and calls `POST /v1/captures/{session}/complete` with SHA-256 hashes.
3. `core-api` atomically inserts `processing_jobs` (`STITCH` → `ANALYZE`) via `Procrastinate` (`SKIP LOCKED` + `NOTIFY`) and returns `202 Accepted`.
4. `geo-worker` sends raw frames to `nodeodm`, converts output to a **COG**, uploads to MinIO (`raster_products`), and streams progress via `NOTIFY` → WebSocket. **`TiTiler`** immediately serves the live orthomosaic.
5. `geo-worker` slices aligned pre/post tiles + building crops, sends batches to `ai-damage-svc` & `ai-embed-svc` (`LitServe`), writes `inference_runs`, `building_assessments` (`PENDING`), `cost_estimates` (snapshotted), and `image_embeddings` (`pgvector`).
6. `apps/web` refreshes **`Martin`** MVT building layers shaded by xBD damage grade; Analyst reviews and confirms/corrects assessments (`D-07`).

### Flow B: Field Flood Report → "Electrified Water" Alert → Re-Routing (`<60s` SLA)
1. Responder submits `FLOOD_WATER` report (directly or synced from `OP-SQLite` queue).
2. `core-api` runs in one `rv_app` transaction: inserts `hazards` → executes `SELECT evaluate_hazard_rules(incident_id)`.
3. PostGIS finds energized/unknown `POWER_LINE`/`TRANSFORMER` within 30 m (`ST_DWithin` on `::geography`), creates `compound_alerts` + `danger_zone`, writes `alert_closed_segments` + sets `road_segments.cost = -1`, invalidates intersecting `routes`, and inserts `notifications`.
4. Postgres `NOTIFY` → Redis Pub/Sub → WebSocket pushes `alert-raised` + `route-invalidated` (+ Expo Push for backgrounded devices); `core-api` computes replacement vehicle-safe routes via `pgr_aStar` (or flags `"NO SAFE ROUTE"`).
5. Only a Commander (`alert.resolve`) calls `resolve_compound_alert()`, reopening segments not covered by another active alert (`NFR-SF-03`).

---

## 5. Architecture Decision Records (ADRs to Maintain in `docs/adr/`)

* **ADR-0001:** Domain-Modular Monolith (FastAPI) over Microservices (`D-02` refinement).
* **ADR-0002:** PostgreSQL `SKIP LOCKED` (`Procrastinate`) for Durable Jobs + Redis strictly for Ephemeral Realtime (`D-03` refinement).
* **ADR-0003:** LitServe Stateless GPU Containers per Model Family over In-Process FastAPI / Triton.
* **ADR-0004:** Cloud-Native Geospatial Serving (`Martin` MVT with Signed Incident Context + `TiTiler` COG + `NodeODM`).
* **ADR-0005:** `TanStack Router` + `TanStack Query` (Vite SPA) for Web Console; `Expo Development Builds` + `OP-SQLite` + `PMTiles` for Mobile (`D-08`).
* **ADR-0006:** Read-Only Tool-Using Commander Copilot (`pgvector` + RLS Views) honoring Human-in-the-Loop (`D-07`).
