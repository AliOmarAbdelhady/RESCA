# AGENTS.md — RescueVision Engineering & AI Agent Contract

> **Read `VISION.md`, `ARCHITECTURE.md`, `REPO_TREE.md`, and `BRANCHING.md` before writing code.**
> This file is the single operational rulebook for every human developer and AI coding agent building RescueVision.
> Always work in a dedicated **git worktree** on a short-lived branch (`feat/...`, `fix/...`, `ai/...`)—never directly on `main`.

---

## 1. Product Vision in One Sentence

RescueVision turns multi-source disaster chaos (drone/satellite imagery, responder GPS/reports, citizen OTP pleas) into **one live, agency-isolated, human-verified spatial map**—where AI proposes and warns, and a single flood report closes lethal roads (e.g., *Electrified Water*) and reroutes rescue vehicles in under 60 seconds.

---

## 2. System Architecture Map (5 Planes, Strict SWE vs. AI Split)

```text
CLIENTS       apps/web (Vite + React + TanStack Router/Query + MapLibre + CesiumJS)
              apps/mobile (Expo Dev Build + Expo Router + MapLibre PMTiles + OP-SQLite)
                 │ HTTPS / WSS / Pre-signed MinIO S3
EDGE & TILES  Caddy (TLS + Auth) ──▶ Martin (Rust PostGIS MVT) · TiTiler (MinIO COG Tiles)
                 │
APP PLANE     backend/api (FastAPI Modular Monolith: 8 domain modules + WS Hub + Read-Only Copilot)
              Redis 7 (ephemeral WS Pub/Sub, GPS coalescing, OTP rate limit ONLY)
                 │ Procrastinate (Postgres SKIP LOCKED + LISTEN/NOTIFY)
ASYNC & AI    backend/workers (geo-worker: COG tiling, NodeODM stitching, PDF snapshots)
                 ├──▶ nodeodm (photogrammetry -> COG / DSM / 3D Mesh)
                 └──▶ ai/services/* (4 isolated LitServe GPU containers on ai-net:
                        damage, person_track, flood_road, embeddings)
                 │
DATA PLANE    PostgreSQL 18 + PostGIS 3.6 + pgRouting 4.0 + pgvector 0.8 (56 tables, RLS) + MinIO
```

---

## 3. Hard Architectural Boundaries (Enforced in CI)

1. **SWE vs. AI Isolation:**
   * `backend/api/` and `backend/workers/` **MUST NEVER** import `torch`, `timm`, `transformers`, `ultralytics`, or load `.pt`/`.onnx` model weights.
   * `ai/services/*/` **MUST NEVER** import `psycopg`, `sqlalchemy`, hold DB credentials, or call `backend/*`. AI containers are stateless HTTP/2 `LitServe` APIs on `ai-net`.
2. **Modular Monolith Boundaries (`backend/api/app/modules/`):**
   * Modules (`identity`, `incidents`, `imagery`, `buildings_cost`, `routing`, `cases`, `hazards`, `field_reports`) may call each other **only** through `module/service.py` public functions (`import-linter` enforced).
3. **Database Security & RLS (`D-04`):**
   * Applications **NEVER** connect as Postgres superuser or schema owner. Use `rv_app` (staff), `rv_citizen` (public), `rv_worker` (pipeline), or `rv_readonly` (BI/Copilot).
   * Every `core-api` DB call **MUST** run inside an explicit transaction executing `SELECT app.set_session_user(...)` (or `set_session_citizen(...)`) — **never** session-wide `SET`. Disable prepared statements (`statement_cache_size=0`) for PgBouncer compatibility.
   * Vector tiles served via `martin` **MUST** pass through signed incident-scoped PostGIS functions or proxy auth—never expose unfiltered incident tables.
4. **Frontend Gateway Rule (`frontend/`):**
   * Apps (`web`, `mobile`) import packages; packages never import apps.
   * **ZERO** direct `fetch`/`axios` calls in `apps/*`. All HTTP/WebSocket traffic goes through `frontend/packages/api` (generated from FastAPI `/openapi.json`).
   * In `apps/mobile`, native modules (`expo-location`, `op-sqlite`, MapLibre, BLE) live **only** behind interfaces in `src/services/`. Never assume Expo Go works—always target **Expo Development Builds**.

---

## 4. Non-Negotiable Domain & Safety Conventions

* **UUIDs & Spatial:** Use PostgreSQL 18 `uuidv7()` for entity IDs (offline mobile generates client IDs safely). Store all geometry in **`SRID 4326`** with GiST indexes. Measure metric distances with **`ST_DWithin(a::geography, b::geography, metres)`** — **never** `ST_Distance(...) < x`.
* **Provenance (`D-03` / `FR-IM-07`):** Every AI-generated row (`building_assessments`, `person_detections`, `hazards`, `road_condition_observations`) must link to `inference_runs` (`model_id` from `ai_models`).
* **Human-in-the-Loop (`D-07`):** AI and the Commander Copilot **propose, rank, and warn only**. Never auto-confirm a person detection, auto-dispatch a team, or auto-resolve a compound alert.
* **Cautious Hazard Defaults (`NFR-SF-02` / `NFR-SF-03`):** Unknown `power_state` counts as `ENERGIZED`. Alert-closed roads are reopened **only** via `resolve_compound_alert()` by an authorized Commander.
* **Offline Idempotency (`D-08`):** Mutating field endpoints (`hazards`, `sos_alerts`, `case_events`, `mission_assignments`) must honor `Idempotency-Key` + client `uuidv7()`.
* **UI Truthfulness & i18n:** Always display uncertainty radius ($\rho$), confidence, review status, and observation age. Never encode severity by color alone. Support English + Arabic RTL (`IR-UI-07`).

---

## 5. Canonical Commands

```bash
# 1. Start core stack (laptop dev with CPU mock AI — no GPU needed)
docker compose -f infra/docker-compose.yml -f infra/docker-compose.cpu-mock.yml up --build

# 2. Start full GPU stack (workstation / demo)
docker compose -f infra/docker-compose.yml -f infra/docker-compose.gpu.yml up --build

# 3. Rebuild & self-check PostgreSQL 18 schema + RLS + Cairo demo
PGHOST=localhost PGPORT=55432 PGUSER=postgres ./database/build.sh

# 4. Backend lint, boundary checks, and tests
pytest backend/ && ruff check backend/ ai/ && lint-imports

# 5. Regenerate typed frontend SDK after ANY FastAPI Pydantic/route change (API running)
cd frontend && pnpm generate:api && pnpm typecheck && pnpm lint && pnpm test
```

---

## 6. Testing Rules & Definition of Done (DoD)

A task or PR is **NOT DONE** until all applicable checks pass:
1. **Schema / DB change:** `./database/build.sh` passes `checks.sql` AND RLS isolation tests prove `rv_app` cannot leak across agencies.
2. **Backend API change:** Unit + PostGIS integration tests pass, `ruff` & `import-linter` pass, AND `pnpm generate:api && pnpm typecheck` passes with updated generated client committed.
3. **AI model / serving change:** Passes `ai/eval/gate.py` thresholds + golden GeoTIFF test, updates `ai/model_cards/*.md`, and passes `/v1/model-info` + `/v1/predict` contract tests.
4. **Frontend change:** `pnpm lint`, `pnpm typecheck`, `pnpm test`, and relevant Playwright/Maestro flow pass in both LTR (EN) and RTL (AR) where UI changed.

---

## 7. What NEVER to Do

* **NEVER** run ML inference or `nodeodm` stitching inside a `core-api` HTTP request handler.
* **NEVER** commit model weights (`.pt`, `.safetensors`, `.onnx`), raw `.tif` orthomosaics, or `.env` secrets to Git (weights live in MinIO).
* **NEVER** use `SELECT *` or bypass `app.set_session_user()` / `rv_app` in API queries.
* **NEVER** replace `Procrastinate` (`processing_jobs`) with an un-transactional in-memory queue that drops jobs on crash.
* **NEVER** hand-write TypeScript types for backend API responses—regenerate via `pnpm generate:api`.
* **NEVER** drop `uncertainty`, `confidence`, `review_status`, or `timestamp` metadata to simplify a UI card.
