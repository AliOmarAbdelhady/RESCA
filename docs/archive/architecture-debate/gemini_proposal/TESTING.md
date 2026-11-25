# Testing & CI Pipeline (`TESTING.md`)

RescueVision operates in a safety-critical disaster domain where a silent RLS leak, broken pgRouting cost, or uncalibrated AI damage grade can misdirect rescuers. Every PR must pass automated **Unit, Contract, Database/RLS Integration, AI Gate, and End-to-End** stages.

---

## 1. Five-Layer Testing Pyramid

### Layer 1: Static Analysis & Architectural Boundary Tests (Fast, Every Save/PR)
* **Python (`backend/`, `ai/`):** `ruff check`, `ruff format --check`, `mypy` (strict on `backend/shared` and `backend/api/app/core`).
* **Boundary Guard (`import-linter`):** Fails CI immediately if:
  * `backend/api` or `backend/workers` imports `torch`, `timm`, `transformers`, or `ultralytics`.
  * `ai/services/*` imports `psycopg`, `sqlalchemy`, or `backend.*`.
  * Any module in `backend/api/app/modules/<x>` reaches into private internals of module `<y>` instead of its public interface.
* **TypeScript (`frontend/`):** `pnpm lint`, `pnpm typecheck` across all Turborepo packages (`contracts`, `api`, `utils`, `web`, `mobile`).
* **Frontend Boundary Check:** ESLint `no-restricted-imports` forbids `fetch`, `axios`, or `expo-*` inside `frontend/apps/*/src/features/*` (all network calls must go through `@rescuevision/api`; all native SDKs through `apps/mobile/src/services/*`).

### Layer 2: Unit Tests
* **Backend (`backend/*/tests/unit/`):** Pure domain logic tested with `pytest`—HAZUS restoration cost math (`cost_low`/`cost_high`), uncertainty radius calculation $\rho$, START triage ordering, vehicle water-depth eligibility, and `Idempotency-Key` handling.
* **AI Services (`ai/services/*/tests/`):** `LitAPI` `decode_request` / `predict` / `encode_response` unit tests with synthetic tensors verifying exact JSON output schemas, probability sum tolerances ($\sum p = 1.0$), and `/v1/model-info` metadata.
* **Frontend (`frontend/`):** `vitest` for `@rescuevision/utils` geo math, `@rescuevision/contracts` Zod schemas, and TanStack Router `validateSearch` URL parameter parsers.

### Layer 3: Contract Tests (Preventing Drift Across SWE ↔ AI ↔ Frontend)
1. **Backend → Frontend OpenAPI Drift Gate:**
   * Export FastAPI's `/openapi.json` cleanly in CI (no live GPU needed), run `pnpm generate:api`, and execute `git diff --exit-code frontend/packages/api/src/generated/`. If a backend Pydantic schema changed without regenerating the frontend SDK, CI fails.
2. **WebSocket Event Contract Gate:**
   * Backend WebSocket event serializers and `frontend/packages/contracts/src/events.ts` Zod schemas are validated against shared JSON fixture payloads (`position`, `sos`, `job-progress`, `alert-raised`, `route-invalidated`, `case-changed`).
3. **Worker ↔ LitServe Contract Gate:**
   * `backend/workers/clients/` tests run against the real `ai-*-svc` containers (running under `docker-compose.cpu-mock.yml`) to prove request/response serialization matches `/v1/predict` and `/v1/model-info`.

### Layer 4: Database, Spatial, & RLS Integration Tests (Real PostgreSQL 18)
Run against an ephemeral **PostgreSQL 18 + PostGIS 3.6 + pgRouting 4.0 + pgvector 0.8** container (never SQLite mocks):
1. **Schema & Spatial Invariants (`database/tests/checks.sql`):**
   * Verifies all 56 tables exist, every geometry column has a GiST index, `CHECK` constraints fire (e.g., team XOR user assignment), and the Cairo demo scenario fires `ELECTRIFIED_WATER` idempotently, closes `road_segments`, invalidates active `routes`, and restores roads via `resolve_compound_alert()` only when no overlapping alert remains.
2. **Multi-Agency Row-Level Security (RLS) Isolation Suite (`backend/api/tests/integration/test_rls.py`):**
   * Connects exclusively as `rv_app`, `rv_citizen`, and `rv_readonly` (never superuser).
   * Verifies `SET LOCAL` inside `PgBouncer` transaction mode: two concurrent interleaved requests for `EMS` (joined) and `FIRE` (not joined or withdrawn) **never leak rows or session state** across pooled connections.
   * Verifies suspended users (`status = 'SUSPENDED'`) are blocked on the very next request, `users.password_hash` raises permission denied, and `rv_citizen` sees only its own requests.
3. **pgRouting & pgvector Tests:**
   * Verifies `pgr_aStar` excludes `cost < 0` and segments exceeding `vehicle.max_water_depth_cm`, returns `"NO_SAFE_ROUTE"` cleanly when cut off, and `image_embeddings` HNSW queries return deterministic nearest neighbors (`ORDER BY embedding <=> $1 LIMIT k`).

### Layer 5: AI Model Evaluation Gates (`ai/eval/gate.py`)
Triggered on changes to `ai/training/`, `ai/configs/`, or model checkpoints (runs on self-hosted GPU runner or manual promotion workflow):
* **Quantitative Thresholds:** Each task checks minimum validation scores on **event-aware held-out splits** (e.g., macro-F1 for xBD 4-class damage, mIoU for FloodNet, mAP@50 for partial-visibility SARD/VisDrone/POP, calibration ECE).
* **Golden GeoTIFF End-to-End Check:** Runs a full `STITCH`/`ANALYZE` chip from Kahramanmaraş and verifies bounding-box CRS (`SRID 4326`), non-empty building detections, valid probability simplex, and inference latency within budget.
* **Promotion Rule:** Only passing models receive `is_active = true` in `ai_models` and a matching card in `ai/model_cards/`.

### Layer 6: End-to-End (E2E) Workflow Tests
Using `docker-compose.yml` + `docker-compose.cpu-mock.yml` + seeded Cairo & Kahramanmaraş demo data:
* **Web Console (`Playwright`):**
  1. Login as Analyst → upload pre/post fixture images → watch `job-progress` WebSocket reach 100% → verify damage polygons render → confirm a building assessment (`D-07`).
  2. Login as Responder/API → submit `FLOOD_WATER` report within 30 m of energized power line → verify non-dismissible **Electrified Water** banner appears within `<5s`, affected road turns closed, and route status updates (`UC-07`).
  3. Generate PDF report → verify frozen snapshot does not change after editing `cost_profile_unit_rates`.
* **Mobile Field App (`Maestro` against Expo Dev Build):**
  * Toggle network offline → record field hazard report & SOS → verify `OFFLINE_QUEUED` indicator → restore network → verify single-delivery sync without duplicate `hazards` rows (`Idempotency-Key` + `uuidv7()`).

---

## 2. CI Pipeline Stages (`.github/workflows/ci.yml`)

| Stage | Trigger | Runner | What Runs |
|---|---|---|---|
| **1. Lint & Boundaries** | Every PR | Ubuntu CPU | `ruff`, `mypy`, `import-linter`, `pnpm lint`, `pnpm typecheck`, feature-import guard. |
| **2. DB & RLS Verification** | Every PR | Ubuntu + Postgres 18 service | `./database/build.sh` (`checks.sql`) + `pytest test_rls.py` (including PgBouncer transaction pool mode). |
| **3. Contract & Unit Suite** | Every PR | Ubuntu CPU | OpenAPI drift check (`pnpm generate:api` + `git diff`), backend unit tests, frontend `vitest`, LitServe contract mocks. |
| **4. Full-Stack E2E Smoke** | PR to `main` | Ubuntu CPU + Docker Compose | Boots `core` + `cpu-mock` stack, runs Playwright UC-02 / UC-04 / UC-07 flows. |
| **5. AI Eval & GPU Build** | Changes in `ai/**` or release tag | GPU Runner (self-hosted/cloud) | Builds `Dockerfile.gpu` images, runs `ai/eval/gate.py` against golden GeoTIFFs, publishes image digests. |
