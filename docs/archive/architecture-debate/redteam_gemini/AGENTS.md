# RescueVision — Engineering & AI Agent Guide (`AGENTS.md` Blueprint)

> **Purpose:** This file is the authoritative operating manual for **AI coding agents and developers** building the RescueVision platform end-to-end. Every change—code, SQL, AI model, or UI—must conform to the single architecture defined here. Read [VISION.md](./VISION.md), [ARCHITECTURE.md](./ARCHITECTURE.md), and [REPO_LAYOUT.md](./REPO_LAYOUT.md) before modifying files.

---

## 1. System Vision & Architectural Track (One Truth)

RescueVision is built as a **Local-First Tactical Digital Twin**:
- **Core Backend:** **Python 3.12+ (`FastAPI` + `psycopg3` + `Pydantic v2`)** modular monolith + **`Procrastinate`** (`SKIP LOCKED`) async geo/AI worker. *Never introduce NestJS, Celery, or multi-database microservices.*
- **Database:** **PostgreSQL 18 + PostGIS 3.6 + pgRouting 4 + pgvector + pg_partman** (custom PGDG image extending `pgrouting/pgrouting:18-3.6-4.0`) + **`PgBouncer`** (transaction pooling).
- **Messaging & Sync:** **Transactional Outbox (`domain_events`) -> `NATS JetStream`** (real-time WebSocket fan-out, revocation, edge leaf sync) + **`PowerSync`** (WAL logical replication ↔ mobile `OP-SQLite`) + **`MeshSat`/`Reticulum`** (optional LoRa failover).
- **AI Serving & Photogrammetry:** **ONE `NVIDIA Triton Inference Server`** (C++ ONNX Runtime / TensorRT backends sharing a single CUDA context) + **`NodeODM`** (+ optional `OpenSplat`). *Never spawn separate FastAPI or LitServe Python GPU servers per model.*
- **Edge Streaming:** **`MediaMTX`** (RTSP/SRT + `SMPTE 336M` KLV → WebRTC/WHEP) + edge `YOLOv8s` ONNX/TensorRT runner.
- **Mapping & Frontends:**
  - `frontend/apps/web`: React 19 + Vite + TanStack Router/Query + **ONE `MapLibre GL JS` canvas** (`maplibre-gl-three` + `3DTilesRendererJS` + `maplibre-gl-splat`/`Spark`). *Never add CesiumJS.*
  - `frontend/apps/mobile`: **Expo Development Build** + `@maplibre/maplibre-react-native` (`.pmtiles`) + `@powersync/react-native` (`op-sqlite`). *Never target Expo Go.*
  - `frontend/apps/citizen`: Lightweight mobile-first PWA for rapid intake + shelter QR fallback.
- **Tiles & Ingress:** **`Caddy 2`** (`forward_auth` + TLS) → authenticated FastAPI **`ST_AsMVT` + Redis** vector tile gateway + **`TiTiler`** dynamic COG raster server + static **`PMTiles`**. *Never connect unauthenticated `Martin` directly to RLS-protected PostGIS tables.*

---

## 2. SWE vs. AI Hard Boundaries

| Plane | Owned Folders | Allowed Responsibilities | Forbidden Crossovers |
|---|---|---|---|
| **Software Engineering** | `database/`, `backend/`, `frontend/`, `contracts/`, `infra/` | Auth/RLS, REST/WS APIs, OpenAPI generation, `ST_AsMVT` tiles, `pgr_aStar`, hazard engine, `PowerSync` sync, `WeasyPrint` PDFs, UI/UX, `geo-worker` job orchestration (`NodeODM`, tiling, gRPC client calls to Triton). | **NO** PyTorch/Lightning/MMSeg/training loops, **NO** `.pt`/`.pth`/`.ckpt`/`.onnx` weight loading inside `core-api`, **NO** dataset downloads in `backend/`. |
| **AI & Data Science** | `ai/`, `triton-repo/`, `datasets/` | PyTorch training, dataset curation, calibration (Temperature Scaling), evaluation gates, ONNX/TensorRT export & numerical parity checks, `config.pbtxt` Triton configs, model cards. | **NO** FastAPI HTTP servers, **NO** PostgreSQL RLS/SQL migrations, **NO** frontend React/Expo code, **NO** unversioned weight dumps outside `triton-repo/<model>/<version>/`. |

**How they meet (the 3 legal seams):**
1. **`triton-repo/` + `contracts/triton/`:** `ai/` exports parity-tested `.onnx`/`.plan` artifacts + `config.pbtxt`; `geo-worker` calls Triton solely via KServe v2 gRPC (`:8001`).
2. **`database/seed/` & `ai_models` Registry:** Every promoted Triton model version receives an explicit row in `ai_models` (`name`, `version`, `calibration_temp`, `embedding_dim`).
3. **`contracts/` Schemas:** Detection/assessment JSON & NATS Protobuf/JSON payloads live in `contracts/` and are validated at both worker ingestion and API serialization.

---

## 3. Standard Commands

Run these exact targets (configured in root `Makefile` / `pyproject.toml` / `frontend/package.json`):

```bash
# Infrastructure & Local Stack
make up-core              # Boot PG18, PgBouncer, MinIO, NATS, Redis, PowerSync, TiTiler, Caddy, core-api, geo-worker, web
make up-gpu               # Boot core + NVIDIA Triton + NodeODM (requires NVIDIA Container Toolkit)
make up-edge              # Boot Edge Field Kit (MediaMTX + NATS Leaf + Edge YOLOv8s + MeshSat)
make db-migrate           # Apply database/schema/*.sql + database/seed/*.sql idempotently
make db-check             # Run database/tests/checks.sql + RLS multi-agency isolation tests

# Backend (Python 3.12+ / uv)
uv run ruff check backend ai
uv run mypy backend/src
uv run lint-imports       # Enforces modular monolith boundaries in backend/
uv run pytest backend/tests/unit
uv run pytest backend/tests/integration   # Uses live Postgres/PostGIS container

# Contracts & Frontend (pnpm Turborepo)
make gen-contracts        # Exports FastAPI OpenAPI -> frontend/packages/api + Zod schemas
pnpm --filter @rv/web test
pnpm --filter @rv/web typecheck
pnpm --filter @rv/mobile typecheck
pnpm --filter @rv/citizen build

# AI Pipeline & Gate Checks
uv run pytest ai/tests/                   # Geometry raycaster, tiling, calibration & ONNX parity tests
uv run python -m ai.eval.gate_check       # Verifies xBD/RescueNet/SARD metrics & ECE thresholds
```

---

## 4. Mandatory Coding & Design Conventions

### 4.1 Database & RLS Security Rules
1. **Every request/worker transaction touching operational tables MUST run inside an explicit transaction with session context:**
   ```python
   async with conn.transaction():
       await conn.execute("SELECT set_config('app.user_id', %s, true)", (str(user_id),))
       ...
   ```
   Use `psycopg3` with `prepare_threshold=None` whenever routing through `PgBouncer` in transaction mode. Never call `app.set_session_user()` outside `BEGIN ... COMMIT` or leak pooled connections without `true` (`is_local=true`).
2. **Never bypass RLS in endpoints or tiles:** Vector tile queries (`ST_AsMVT`) MUST go through `core-api`'s authenticated tile endpoint using `set_config` and Redis cache keys scoped by `(incident_id, role_scope, filter_hash, z, x, y)`.
3. **Hazard Engine Concurrency:** `app.evaluate_hazard_rules(p_incident)` MUST remain `SECURITY DEFINER` (explicit `SET search_path = public, pg_temp`), verify caller permission (`hazard.report` OR `analysis.run`), and acquire `pg_advisory_xact_lock(hashtext(p_incident::text))` before reading or mutating alerts/roads/routes.
4. **Citizen Privacy & Revocation:** Any media uploaded by `rv_citizen` or field reporters MUST pass through `geo-worker`'s EXIF GPS/device PII scrubber before switching status to public/shared. User suspension or agency withdrawal MUST write to `domain_events` to evict active WebSockets immediately via NATS `rv.sec.revoked_users`.

### 4.2 Backend & Domain Module Rules
1. Enforce strict **8-module domain boundaries** inside `backend/src/rescuevision/domains/` (`auth_org`, `incidents`, `imagery_ingest`, `damage_cost`, `hazards_routing`, `persons_cases`, `citizens_reports`, `copilot`) via `import-linter`. Cross-domain calls go through explicit domain service interfaces or `domain_events`, never raw cross-module ORM/SQL table reaching.
2. All mutations creating asynchronous work or real-time UI changes MUST write a `domain_events` row in the **same SQL transaction** as the domain state change. Never dual-write directly to NATS/Redis outside the transaction.
3. The `PydanticAI` Spatial Copilot MUST connect **only** as read-only PostgreSQL role `rv_readonly` (`SET TRANSACTION READ ONLY`) and may never trigger dispatches, hazard resolutions, or case assignments.

### 4.3 Frontend & Bilingual UX Rules
1. **Contract-First:** Never hand-write API TypeScript interfaces or fetch URLs inside `apps/web`, `apps/mobile`, or `apps/citizen`. Always regenerate `frontend/packages/api` from FastAPI's OpenAPI spec (`make gen-contracts`).
2. **One Map Canvas:** All web 2D vectors, COG raster swipes, 3D building extrusions, NodeODM 3D Tiles, and `Spark` Gaussian Splats render inside the single `MapLibre GL JS` instance in `packages/map-core`.
3. **Bilingual RTL & Accessibility:** Every component in `packages/ui` and `apps/*` MUST use logical Tailwind CSS properties (`ms-*`, `me-*`, `ps-*`, `pe-*`, `text-start`, `text-end`), `i18next` translation keys (`en` + `ar`), and pattern + color coding for damage grades (`NFR-US-02`).

### 4.4 AI & Geometry Rules
1. **No Raw Uncalibrated Confidence:** All multi-class damage outputs written to `building_assessments` MUST apply the Temperature Scaling factor recorded in `ai_models.calibration_temp` and assert `sum(p_*) = 1.000`.
2. **No Flat-Earth Projection:** Pixel-to-GPS survivor/hazard projection MUST use stored camera intrinsics (`focal_length_px`, `cx`, `cy`, distortion) intersected with NodeODM DSM (fallback: Copernicus 30 m DEM) and propagate attitude + GPS + terrain sigma into `location_error_m`.
3. **Event-Aware Splits & Parity:** Training configs MUST split by disaster event (`splits_event_aware.csv`), never random tile shuffling. A model may not enter `triton-repo/` unless PyTorch vs. ONNX Runtime numerical parity passes `< 1e-4` max absolute diff and passes the evaluation gate in `TESTING.md`.

---

## 5. Testing Rules & Definition of Done (DoD)

A PR or agent task is **DONE** only when ALL applicable checks pass:
1. **Boundary & Lint:** `ruff`, `mypy`, `import-linter`, `tsc`, and `eslint` pass with zero errors.
2. **Contract Sync:** If any FastAPI route/Pydantic model changed, `make gen-contracts` ran cleanly and `git diff frontend/packages/api` matches.
3. **Database & RLS Proof:** Any SQL change passes `make db-check` AND includes an explicit test proving cross-agency denial (`D-04`) and concurrency safety where applicable.
4. **AI Gate:** Any change to `ai/` passes geometry/calibration unit tests + ONNX parity test + `ai.eval.gate_check`.
5. **No Fake Stubs:** Never mark unimplemented endpoints or mock tensors as verified production results. Unfinished capabilities must fail explicitly (`501 Not Implemented` or explicit UI unavailable badge).

---

## 6. What NEVER to Do

- **NEVER** import `torch`, `ultralytics`, `transformers`, or `mmseg` inside `backend/src/rescuevision/api/`.
- **NEVER** execute SQL queries without an explicit `BEGIN` + `set_config('app.user_id', ..., true)` when acting on behalf of a user.
- **NEVER** mount `Martin` directly against RLS-protected PostGIS tables or skip `Caddy` `forward_auth`.
- **NEVER** install `CesiumJS`, `Celery`, `NestJS`, or spawn per-model `LitServe`/FastAPI GPU containers.
- **NEVER** write a custom hand-rolled mobile SQLite sync queue—use `@powersync/react-native` + `@op-engineering/op-sqlite`.
- **NEVER** commit raw datasets, model weights (`.onnx`, `.pt`, `.pth`, `.trt`), `.env` secrets, or unrendered Kaggle notebooks with hardcoded tokens.
- **NEVER** trust raw smartphone/citizen EXIF metadata or display unreviewed AI detections as confirmed ground truth without explicit `UNREVIEWED` / confidence indicators.
