# RescueVision — Testing, AI Evaluation & CI Pipeline Blueprint (`TESTING.md`)

> **Rule:** AI coding agents and developers must never rely on manual "looks fine on my laptop" demos. Every architectural boundary—RLS security, hazard engine concurrency, OpenAPI-to-TypeScript contracts, ONNX numerical parity, model calibration, and `<60s` hazard SLA—has an automated test gate.

---

## 1. The Six-Layer Testing Pyramid

```
        [ Layer 6: E2E Playwright + Real <60s SLA + MediaMTX Smoke ]
       [ Layer 5: AI Eval Gates (xView2 F1, ECE <= 0.05, SAHI, Parity) ]
      [ Layer 4: PG18 + PostGIS + pgRouting + RLS + Concurrency Integration ]
     [ Layer 3: Contract Drift (OpenAPI -> TS/Zod, NATS Schemas, Triton PB) ]
    [ Layer 2: Fast Unit Tests (pytest: Geo/Calibration/Cost, vitest: UI/Sync) ]
   [ Layer 1: Static & Boundary Gates (ruff, mypy, import-linter, tsc, sqlfluff) ]
```

---

## 2. Layer-by-Layer Specification

### Layer 1: Static Analysis & Boundary Enforcement (Fastest, Every Save / PR)
- **Python Lint & Types:** `uv run ruff check backend ai` + `uv run mypy backend/src` (strict mode on domain & infra modules).
- **Modular Monolith Boundaries:** `uv run lint-imports` enforces that the 8 modules in `backend/src/rescuevision/domains/` never cross-import internal models/SQL queries and that `backend/src/rescuevision/api/` **never** imports `torch`, `ultralytics`, or `transformers`.
- **SQL Lint:** `sqlfluff lint database/schema/` ensuring idempotent DDL and explicit `SET search_path` on all `SECURITY DEFINER` functions.
- **TypeScript & RTL Lint:** `pnpm -r typecheck` + `eslint` rule banning directional Tailwind classes (`ml-`, `mr-`, `pl-`, `pr-`, `left-`, `right-`) in `frontend/packages/ui` and `apps/web` in favor of logical RTL properties (`ms-`, `me-`, `ps-`, `pe-`, `start-`, `end-`).

### Layer 2: Unit Tests (`pytest` & `vitest` — Zero Docker Required)
- **`backend/tests/unit/`:**
  - Cost estimation formulas & snapshotting invariants.
  - START triage state machine & monotone PowerSync conflict-resolution reducers.
  - Citizen EXIF scrubber verifying GPS/camera serial stripping from sample JPEG buffers.
  - `PydanticAI` tool schema & read-only prompt-injection guard tests.
- **`ai/tests/`:**
  - `MaskedFocalDiceLoss` gradient & mask-ignoring (`label == 255`) tests.
  - Temperature Scaling `NLL` solver & `ECE` computation on synthetic logits.
  - DSM pixel-to-GPS raycaster verifying known flat/sloped elevation targets and `location_error_m` propagation.
- **`frontend/` (`vitest`):**
  - Zod schema validation for offline queue entries, Arabic RTL formatting, and 4D time-travel timeline state reducers.

### Layer 3: Contract Tests (Eliminating Backend/Frontend/AI Drift)
- **OpenAPI ↔ TypeScript Sync (`make gen-contracts` check in CI):**
  - Export FastAPI `openapi.json`, regenerate `frontend/packages/api/`, and fail CI if `git diff --exit-code contracts/openapi frontend/packages/api` is non-empty.
- **Async Event & LoRa Binary Contracts (`contracts/events/`):**
  - Validate every `domain_events` payload emitted by `backend/` and `edge/meshsat/` CBOR codec round-trips (`< 200 B` hard byte-length cap for LoRa packets).
- **Triton Tensor Contract (`contracts/triton/`):**
  - Assert that `geo-worker`'s preprocessing tensor shapes/dtypes match `triton-repo/*/config.pbtxt` input/output declarations.

### Layer 4: Database, PostGIS & RLS Integration Tests (`backend/tests/integration/` + `database/tests/`)
Runs against a **real `database/Dockerfile` (PG 18 + PostGIS 3.6 + pgRouting 4 + pgvector + `pg_partman`)** container (+ `pgbouncer`, `redis`, `nats`):
1. **Schema & Seed Integrity (`database/tests/checks.sql`):** All constraints, partition creation (`pg_partman`), `pgvector` HNSW search, and Cairo demo seed pass.
2. **Multi-Agency RLS Matrix (`D-04`):** Automatically runs queries as Agency A Commander, Agency B Analyst, Field Responder, Uninvited Agency, Citizen (`rv_citizen`), and Copilot (`rv_readonly`), asserting `0` leaked cross-agency rows on tables AND on `/tiles/vector/{z}/{x}/{y}.mvt` responses.
3. **Hazard Engine Privilege & Concurrency Proof:**
   - Assert `FIELD_RESPONDER` (`rv_app`) submitting `POST /hazards` (`FLOOD_WATER`) near an `ENERGIZED` or `UNKNOWN` power asset **succeeds** (`201`, no `42501` error) and creates `compound_alerts` + closes `road_segments` + invalidates `routes`.
   - Fire **10 concurrent async `FLOOD_WATER` submissions** against the same incident in parallel coroutines and assert `pg_advisory_xact_lock` produces **exactly 1** active compound alert with zero deadlocks.
4. **PgBouncer Transaction Pooling Test:** Verify prepared statements are cleanly disabled (`prepare_threshold=None`) and pooled connections never leak `app.user_id` across requests.
5. **WebSocket Revocation Test:** Suspend an active user in Postgres → verify `domain_events` → NATS `rv.sec.revoked_users` terminates the live WebSocket within `< 2s`.

### Layer 5: AI Model Evaluation & Export Parity Gates (`ai/eval/gate_check.py`)
Must pass before any model version is promoted to `triton-repo/`:
1. **Numerical Parity Gate:** Compare PyTorch checkpoint vs. exported `model.onnx` on 16 random + real validation patches (`max_abs_diff < 1e-4`, pixel argmax agreement `>= 99.9%`).
2. **Event-Held-Out Generalization Gate:** Evaluate strictly on unseen disasters (`splits_event_aware.csv` + `LADI v2` temporal split + local DJI AOI split)—never random tile leakage:
   - `joint_damage`: Report official `XView2PixelScorer` $F_1^{\text{loc}}$, $F_1^{\text{clf}}$, and overall harmonic $F_1^{\text{overall}}$.
   - `calibration`: Assert post-Temperature-Scaling $\text{ECE} \le 0.05$ on held-out calibration split.
   - `person_sar_*`: Evaluate `SARD` + `HERIDAL` with `SAHI` tiling; report AP@50, Recall@tiny (`< 32×32 px`), and Jetson/CPU latency (`ms/frame`).
   - `flood_road_seg`: Report mIoU per class (`Water`, `Road-Clear`, `Road-Blocked`) separately on `FloodNet` AND `RescueNet`.
3. **Triton Smoke Test:** Boot `tritonserver --model-repository=triton-repo` and verify `/v2/health/ready` + sample gRPC inference returns calibrated non-NaN tensors within VRAM budget.

### Layer 6: End-to-End & Latency SLA Tests
- **Playwright Web E2E (`frontend/apps/web/e2e/`):**
  1. Commander logs in, views Cairo MapLibre 2D/3D buildings, swipes `TiTiler` before/after COG.
  2. Responder submits `FLOOD_WATER` hazard via API → verify WebSocket **Electrified Water** alert banner + closed road segment + updated safe `pgr_aStar` route appear on map and **total end-to-end latency is `< 60s`** (`NFR-PF-04`).
  3. Toggle Arabic RTL locale (`ar`) and verify layout & bilingual PDF report generation (`WeasyPrint`).
- **Offline Sync & Edge E2E:**
  - Simulate PowerSync offline queue replay (`case_events` + `assistance_cases` status merge) verifying zero overwrites of simultaneous responder updates.
  - Replay recorded RTSP + `SMPTE 336M` KLV `.ts` clip through `MediaMTX` → `edge-detector` → assert `person_detections` row created with non-null `stream_ref` and `location_error_m`.

---

## 3. CI/CD Pipeline Stages (GitHub Actions)

| Stage | Trigger | Runner | Jobs Executed |
|---|---|---|---|
| **Stage 1: Fast Static & Contracts** | Every PR (`< 3 min`) | Ubuntu CPU | `ruff`, `mypy`, `lint-imports`, `sqlfluff`, `pnpm typecheck/lint`, `make gen-contracts` drift check, Layer 2 unit tests (`pytest` + `vitest`). |
| **Stage 2: DB, RLS & Core Integration** | Every PR (`< 6 min`) | Ubuntu CPU + Docker | Build `database/Dockerfile`, run `checks.sql`, RLS cross-agency matrix, concurrent `evaluate_hazard_rules()` test, PgBouncer + NATS + `ST_AsMVT` integration tests. |
| **Stage 3: Build & Web E2E** | PR to `main` (`< 10 min`) | Ubuntu CPU + Docker | Boot `docker-compose.yml` (`core` profile), run Playwright E2E + `<60s` *Electrified Water* latency check + `WeasyPrint` PDF smoke. |
| **Stage 4: AI Parity & Triton Gate** | PR touching `ai/` or `triton-repo/` | Self-hosted / GPU Runner (or ONNX CPU fallback) | ONNX parity (`< 1e-4`), Triton `config.pbtxt` validation, `ai.eval.gate_check` metrics report posted as PR comment. |
| **Stage 5: Nightly Full Eval & Edge Kit** | Nightly / Release Tag | GPU Runner | Full `LADI v2` / `RescueNet` / `HERIDAL` benchmark ledger update + `MediaMTX` KLV edge replay test. |
