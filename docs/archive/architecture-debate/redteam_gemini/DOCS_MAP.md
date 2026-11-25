# RescueVision — Proposed Repository Documentation Set (`DOCS_MAP.md`)

> **Goal:** Replace today's fragmented, contradictory Markdown files with one clean, non-overlapping documentation hierarchy built specifically so **6 developers and AI coding agents** share the exact same truth.

---

## 1. Master Documentation Inventory

| Document Path | Audience | Purpose & Required Outline |
|---|---|---|
| **`VISION.md`** *(Root)* | All humans & AI agents | **1-page single product & technical story:** Local-First Tactical Digital Twin uniting Damage/Cost, 2D/3D/4D Mapping & Routing, Person Detection/Tracking, Assistance Cases, Compound Hazards (*Electrified Water*), Citizen Channel, and Frozen PDF Reports + 4 core architectural invariants. |
| **`AGENTS.md`** *(Root)* | AI coding agents & engineers | **Authoritative coding contract:** Active tech stack, SWE vs. AI hard boundaries, canonical `make`/`uv`/`pnpm` commands, SQL RLS/transaction rules, OpenAPI/Triton contract rules, testing DoD, and explicit "What NEVER to do" rules. *(Replaces the thesis-editing root `AGENTS.md`.)* |
| **`ARCHITECTURE.md`** *(Root)* | Engineers & thesis authors | **Single system blueprint:** Full Mermaid topology, 8 backend domains, Caddy `forward_auth` + `ST_AsMVT` Redis tiles, `PowerSync` + `NATS JetStream` + `MeshSat` offline architecture, `MapLibre` single-canvas 2D/3D/4D + `PydanticAI` read-only copilot, SQL fixes, and 3 end-to-end data flows. |
| **`REPO_LAYOUT.md`** *(Root)* | AI agents & contributors | **Folder-by-folder directory map:** Every top-level folder and key sub-folder with explicit **What Lives Here** and **What Is Forbidden Here** lines, plus exact interface seams between SWE (`backend/`, `frontend/`, `database/`) and AI (`ai/`, `triton-repo/`, `datasets/`). |
| **`DOCKER.md`** *(Root)* | Engineers & DevOps | **Container & GPU isolation guide:** Every `Dockerfile` path, `core` vs. `gpu` vs. `edge` Compose profiles, network isolation (`ai-internal`), PG 18 PGDG image build, and single-CUDA-context `NVIDIA Triton` packing. |
| **`AI_PIPELINE.md`** *(Root)* | ML engineers & `geo-worker` devs | **End-to-end AI lifecycle:** Canonical dataset curation (`xBD`, `BRIGHT`, `RescueNet`, `LADI v2`, `SARD`, `HERIDAL`, `FloodNet`), model consolidation, Temperature Scaling calibration (`ECE`), DSM pixel-to-GPS raycasting, ONNX/TRT export & `< 1e-4` parity gate, `triton-repo/` versioning, and live Edge RTSP/KLV streaming. |
| **`TESTING.md`** *(Root)* | All engineers & CI | **6-layer quality gate specification:** Static/boundary lint (`import-linter`, RTL checks), unit tests, OpenAPI/Zod/Triton contract checks, PG18 RLS + concurrency integration tests, AI evaluation gates, Playwright + `<60s` SLA E2E tests, and GitHub Actions CI stage DAG. |
| **`CONTRACTS.md`** *(Root or `contracts/README.md`)* | Backend, Frontend, Mobile, AI devs | **Exact seam specifications:** How FastAPI exports `contracts/openapi/openapi.json` → `frontend/packages/api/`, `domain_events` NATS subject catalog (`rv.inc.*`, `rv.sec.*`), `<200 B` LoRa CBOR schema, and Triton tensor shape contracts. |
| **`SECURITY_RLS.md`** *(`database/SECURITY_RLS.md`)* | DB, Backend & Mobile devs | **Zero-trust data isolation manual:** DB roles (`rv_app`, `rv_worker`, `rv_citizen`, `rv_readonly`), mandatory `BEGIN + set_config('app.user_id', ..., true)` pattern, `PgBouncer` transaction-mode rules, `evaluate_hazard_rules()` `SECURITY DEFINER` invariants, `ST_AsMVT` cache scoping, instant WebSocket revocation, and EXIF scrubbing. |

---

## 2. Architecture Decision Records (`docs/adr/`)

Short, immutable 1-page ADRs locking settled debates so AI agents never re-litigate resolved choices:

| ADR File | Decision Recorded |
|---|---|
| `docs/adr/0001-python-modular-monolith-over-nestjs-and-microservices.md` | FastAPI + `psycopg3` + `Procrastinate` + `import-linter` over NestJS or 10+ microservices. |
| `docs/adr/0002-single-triton-server-over-multi-container-litserve.md` | ONE `NVIDIA Triton` (ONNX/TensorRT, shared CUDA context) over 3–5 separate Python/LitServe GPU containers. |
| `docs/adr/0003-maplibre-unified-canvas-over-dual-cesium.md` | Single `MapLibre GL JS` canvas + `maplibre-gl-three` + `3DTilesRendererJS` + `Spark` over CesiumJS. |
| `docs/adr/0004-st-asmvt-proxy-over-direct-martin-rls.md` | Authenticated `ST_AsMVT` + Redis + `TiTiler` + `PMTiles` over unauthenticated `Martin` against PostGIS. |
| `docs/adr/0005-powersync-nats-meshsat-offline-stack.md` | `PowerSync` (`OP-SQLite`) + `NATS JetStream` Outbox/Leaf + `MeshSat`/`Reticulum` LoRa over custom SQLite queues & bare `LISTEN/NOTIFY`. |
| `docs/adr/0006-pg18-pgdg-packaging-and-pg-partman.md` | Custom `database/Dockerfile` (`pgrouting:18-3.6-4.0` + `pgvector` + `pg_partman`) and advisory-locked `SECURITY DEFINER` hazard engine. |
| `docs/adr/0007-consolidated-ai-portfolio-and-uav-domain-adaptation.md` | `SiameseUNetSE`/`ChangeOS` + `Clay`/`HASTE` post-only + `RT-DETR`/`YOLOv8s` + `SegFormer` with `RescueNet` & `LADI v2` adaptation + Temperature Scaling. |
| `docs/adr/0008-readonly-pydanticai-copilot.md` | `PydanticAI` tool-using assistant strictly restricted to `rv_readonly` Postgres role (`D-07`). |

---

## 3. Per-Subsystem Local Agent & Developer Guides

Keep each subsystem self-contained so an AI coding agent working inside a subfolder gets local rules without loading the whole repo:

- `database/AGENTS.md` — Migration order, RLS policy checklist, `pg_partman` rules, how to run `checks.sql`.
- `backend/AGENTS.md` — 8-domain `import-linter` rules, `psycopg3` explicit transaction decorator, `domain_events` emission, `WeasyPrint` RTL PDF rules.
- `frontend/AGENTS.md` — Turborepo workspace rules, `make gen-contracts` rule, RTL logical CSS properties, no CesiumJS/Mapbox rule, Expo Dev Build + `PowerSync` schema rules.
- `edge/AGENTS.md` — `MediaMTX` KLV passthrough config, `YOLOv8s` ONNX tensor contract, `<200 B` LoRa CBOR serialization cap.
- `ai/AGENTS.md` — Event-aware split enforcement, MLflow logging, Temperature Scaling `ECE` calculation, DSM raycasting, ONNX parity `< 1e-4` gate before updating `triton-repo/`.

---

## 4. Model Cards, Experiment Ledger & Thesis Governance (`docs/`)

| Document Path | Outline & Purpose |
|---|---|
| `docs/ai/MODEL_CARDS.md` | Structured model card per active model (`joint_damage`, `post_damage_probe`, `person_sar_hq`, `person_sar_edge`, `flood_road_seg`, `eo_embedder`): architecture, training datasets, domain limits, Temperature Scaling factor, latency, and ethical/false-negative caveats. |
| `docs/ai/EXPERIMENTS.md` | Live reproducible benchmark table (`E1..En`) linked to MLflow run IDs, `splits_event_aware.csv`, exact F1/mAP/ECE/latency numbers (zero unverified claims). |
| `docs/thesis/THESIS_WORKFLOW.md` | *(Moved out of root `AGENTS.md`!)* Contains university graduation report ownership, `.docx` build scripts (`build_docx.py`), IEEE citation rules, and evidence-gating checks—keeping thesis administration strictly separate from software engineering agent instructions. |

---

## 5. Legacy Docs Retirement Checklist (When Adopting This Blueprint)

To eliminate split-brain immediately when the team switches to this documentation set:
1. Move current root `AGENTS.md` thesis instructions into `docs/thesis/THESIS_WORKFLOW.md` and install the new `AGENTS.md` at repo root.
2. Mark `docs/architecture/platform-architecture-plan.md`, `docs/architecture/debate/gemini_proposal.md`, `docs/PROJECT_ANALYSIS.md`, and `docs/SAR_Drone_Simulation_Research.md` with a clear top banner: `> SUPERSEDED by root ARCHITECTURE.md & docs/adr/*`.
3. Update `docs/documentation/chapter5/section_3_3.md` and `docs/superpowers/specs/2026-11-23-rescuevision-database-erd-design.md` to reflect unified `Triton`, `PowerSync`, `NATS JetStream`, `ST_AsMVT`, single-canvas `MapLibre`, and PG 18 PGDG packaging.
