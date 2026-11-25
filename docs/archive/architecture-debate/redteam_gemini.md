# RescueVision Red-Team Architecture Audit & Unified Blueprint
**Author:** Red-Team Chief Architect C (Gemini)
**Date:** 2026-11-25
**Target File:** `docs/architecture/debate/redteam_gemini.md`
**Documentation Blueprint Folder:** [`docs/architecture/debate/redteam_gemini/`](./redteam_gemini/)

---

## Executive Summary
1. **Verdict on Current Plans:** RescueVision already possesses a rigorous 56-table PostgreSQL schema and serious ML experimentation (`SiameseUNetSE`), **but its planning documents describe three incompatible architectures, leave features disconnected, and lack a single AI-agent-ready implementation blueprint**.
2. **Root `AGENTS.md` Misalignment:** The current root `AGENTS.md` governs graduation-report Word editing rather than software/AI engineering—giving AI coding agents zero rules on repository boundaries, commands, RLS transaction discipline, or interface contracts.
3. **Architecture Split-Brain:** `platform-architecture-plan.md` specifies **NestJS + FastAPI + Martin**, `gemini_proposal.md` specifies **FastAPI + 4 LitServe GPU containers + Procrastinate + Martin + CesiumJS**, `15_security.sql` mentions **Celery**, `claude_view.md` specifies **ROS 2 + Gazebo**, and `SAR_Drone_Simulation_Research.md` pushes **AirSim + UE5**.
4. **Silent RLS & Concurrency Bugs in SQL:** `evaluate_hazard_rules()` (`12_hazard_engine.sql`) runs as `SECURITY INVOKER` without advisory locks, causing `FIELD_RESPONDER` flood reports to fail RLS `42501` checks and exposing concurrent reports to duplicate-alert race conditions.
5. **Broken Map Security in Both Plans:** Both prior architecture plans put Rust `martin` directly in front of PostGIS, yet Martin maintains a static pool and cannot execute per-request `SET LOCAL` RLS transactions—while custom PL/pgSQL HMAC query hacks break caching and auto-publishing.
6. **VRAM Waste & Zero Edge AI:** Spawning 3–4 separate Python GPU containers (`FastAPI` or `LitServe`) duplicates CUDA contexts and weights on a single GPU, while assuming multi-gigabyte drone video uploads over collapsed cellular networks ignores edge RTSP/KLV triage.
7. **AI Config/Seed/Dataset Contradictions:** `01_reference_data.sql` (`U-Net ResNet34` + `DINOv2 + MLP` + `Siamese U-Net`), `configs/inference.yaml` (`joint_damage`), `person2_bela.md` (`DINOv2` vs `DINOv3`), and `rv3_train_joint_serox50.ipynb` (`SiameseUNetSE`) disagree; meanwhile satellite `xBD` lacks UAV oblique/GSD adaptation (`RescueNet`, `LADI v2`, `BRIGHT`), flat-earth projection omits intrinsics/DSM, and raw probabilities lack calibration.
8. **Dual-WebGL Bloat & Unspecified Offline Protocol:** Running both MapLibre and CesiumJS (`~1.2 MB` gzip `@cesium/engine`) duplicates camera/selection state, while `D-08` ("works offline") is left *"out of scope"* in `erd-design.md` §9 with no sync engine, conflict rules, or off-grid radio relay.
9. **Unified Single Vision — Local-First Tactical Digital Twin:** Standardize all teams and AI coding agents onto **one architecture**: **Python `FastAPI` + `psycopg3` modular monolith**, **Transactional Outbox → `NATS JetStream`**, **`PowerSync` + `OP-SQLite` offline-first mobile**, and a **`MeshSat`/`Reticulum` LoRa emergency failover** (`VISION.md`).
10. **Single-Canvas 2D/3D/4D Map:** Retire CesiumJS; run **one unified MapLibre GL JS canvas** extended via `maplibre-gl-three` + NASA `3DTilesRendererJS` for NodeODM 3D Tiles and `Spark` (`maplibre-gl-splat`) for localized 3D Gaussian Splat rubble blocks, backed by authenticated `ST_AsMVT` (Redis-cached), `TiTiler`, and `PMTiles`.
11. **Single-Context GPU Packing + Live Edge Triage:** Consolidate building/change/damage into one calibrated joint model (`SiameseUNetSE`/`ChangeOS`), pack ONNX/TensorRT engines into **one `NVIDIA Triton` container** (shared CUDA context, C++ backends), and run live RTSP + `SMPTE 336M` KLV edge detection (`MediaMTX` + `YOLOv8s`) in the field.
12. **Grounded AI Rigor & Read-Only Spatial Copilot:** Use `Clay v1.5`/`DINOv2` + `microsoft/haste` linear-probe triage for post-only fallback, Temperature Scaling (`ECE`), and DSM raycasting—plus a strictly read-only `PydanticAI` copilot over `rv_readonly` (`D-07`).
13. **Complete AI-Agent Blueprint & Production Operations Plan Delivered:** Fourteen interlocking blueprint files—covering architecture, `AGENTS.md`, `kaggle/<feature>/vN/` training layout, Git worktree/trunk branching, GitHub Actions CI/CD, Contabo VPS + WireGuard GPU hosting, repo clean-up audit, and the ideal 10/10 repo tree—are ready inside [`docs/architecture/debate/redteam_gemini/`](./redteam_gemini/).

---

## 1. Architecture Documentation Blueprint (Ready for AI Coding Agents)

To enable 6 developers and parallel AI coding agents to reset cleanly and build RescueVision end-to-end on **one unified track**, a complete **14-document** blueprint suite has been authored inside [`docs/architecture/debate/redteam_gemini/`](./redteam_gemini/):

| Blueprint File | What It Establishes |
|---|---|
| **[`VISION.md`](./redteam_gemini/VISION.md)** | One-page unified product & technical vision tying damage/cost, 2D/3D/4D mapping & routing, person detection & tracking, assistance cases, compound hazards (*Electrified Water*), citizen intake, and frozen PDF reports into one coherent story. |
| **[`AGENTS.md`](./redteam_gemini/AGENTS.md)** | Full replacement draft for the root `AGENTS.md` designed for AI coding agents: active stack truth, SWE vs. AI hard boundaries, canonical `make`/`uv`/`pnpm` commands, SQL/RLS/geo conventions, testing DoD, and explicit "What NEVER to do" guardrails. |
| **[`ARCHITECTURE.md`](./redteam_gemini/ARCHITECTURE.md)** | Single canonical system topology, 8 modular-monolith backend domains, mandatory SQL/RLS/tile/schema fixes, and three end-to-end flows (Live/Survey AI → Map, Flood → *Electrified Water* `<60s`, Offline Field → LoRa Failover → PowerSync Merge). |
| **[`REPO_TREE.md`](./redteam_gemini/REPO_TREE.md)** | One complete, ideal 10/10 ASCII directory tree of the target repository with a one-line purpose for every folder and strict cleanliness rules ("what is forbidden where"). |
| **[`REPO_LAYOUT.md`](./redteam_gemini/REPO_LAYOUT.md)** | Detailed folder-by-folder boundary matrix (Allowed vs. Forbidden) explicitly separating SWE (`database/`, `backend/`, `frontend/`, `edge/`, `infra/`) from AI (`ai/`, `kaggle/`, `triton-repo/`, `datasets/`) across `contracts/` & `ai_models`. |
| **[`REPO_CLEANUP.md`](./redteam_gemini/REPO_CLEANUP.md)** | Verified path-by-path clean-up verdict table (`KEEP / MOVE / ARCHIVE / DELETE`) auditing `_erd_viewer.html`, `mahmoudERD/`, `dashboard/`, `api/`, `mapping/`, `configs/`, `scripts/`, 33 scattered notebooks, `docs/brand/*.pcraft`, and legacy architecture drafts. |
| **[`BRANCHING.md`](./redteam_gemini/BRANCHING.md)** | Short-lived trunk-based GitHub Flow on protected `main`, branch naming, Conventional Commits, automated `release-please` semver tags, CODEOWNERS, and isolated Git worktree rules for concurrent AI coding agents. |
| **[`CI_CD.md`](./redteam_gemini/CI_CD.md)** | Complete **GitHub Actions** pipeline: fast static/contract drift (`<3m`), PG18 PGDG + RLS matrix + concurrency race (`<6m`), `gitleaks`/`trivy`/`hadolint` security, GPU/CPU AI evaluation & parity gates, Playwright `<60s` E2E, and rollback-safe SSH deploys. |
| **[`HOSTING_CONTABO.md`](./redteam_gemini/HOSTING_CONTABO.md)** | Practical **Contabo VPS/VDS** production & staging architecture (`Docker Compose + Caddy 2` over `k3s`/`Kamal`), WireGuard/Tailscale encrypted tunnel to external GPU nodes, `SOPS + age` secrets, off-site `pgBackRest`/`restic` backups, and Prometheus/Loki/Uptime Kuma monitoring. |
| **[`DOCKER.md`](./redteam_gemini/DOCKER.md)** | Exact container matrix, `Dockerfile` locations (`database/`, `backend/`, `frontend/apps/*`, `ai/`), split Compose profiles (`core`, `gpu`, `edge`), `ai-internal` network isolation, and single-CUDA-context `NVIDIA Triton` packing. |
| **[`AI_PIPELINE.md`](./redteam_gemini/AI_PIPELINE.md)** | End-to-end runtime AI lifecycle: datasets, model consolidation, Temperature Scaling (`ECE`), DSM raycasting, ONNX/TRT export & `< 1e-4` parity gate, Triton versioning, `geo-worker` KServe v2 gRPC contract, and live Edge RTSP/KLV execution. |
| **[`AI_TRAINING_LAYOUT.md`](./redteam_gemini/AI_TRAINING_LAYOUT.md)** | Refined **`kaggle/<feature>/vN/`** experiment workspace (exact files per `vN/` folder), shared `rv_ai` package sync (`pip install git+...@<sha>#subdirectory=ai`), MinIO S3 weight storage (never in Git), promotion gates, backend tensor contracts, and `<30s` rollback. |
| **[`TESTING.md`](./redteam_gemini/TESTING.md)** | Six-layer testing pyramid covering static/boundary lint (`import-linter`, RTL checks), unit tests, OpenAPI/Zod/Triton contract drift, PG18 RLS/concurrency integration tests, AI evaluation gates, and Playwright `<60s` SLA E2E checks. |
| **[`DOCS_MAP.md`](./redteam_gemini/DOCS_MAP.md)** | Full proposed Markdown documentation catalog (`VISION.md`..`SECURITY_RLS.md`, 8 ADRs in `docs/adr/`, per-service `AGENTS.md`, `docs/ai/MODEL_CARDS.md`, `docs/thesis/THESIS_WORKFLOW.md`, and legacy-doc retirement checklist). |

---

## 2. Clinical Audit: Architectural, Security & Design Problems in Existing Docs

*(Note: Because implementation intentionally starts from a clean slate, unimplemented application folders and pending benchmarks are excluded below; only genuine architectural contradictions, security bugs, schema flaws, and suboptimal technology choices are cited.)*

### What Is Genuinely Strong (Retain)
1. **Relational & Spatial Rigor in `database/schema/`:** Enforces hard invariants inside PostgreSQL—`CHECK (num_nonnulls(...) = 1)` for provenance (`database/schema/08_persons_cases.sql:93-95`), sum-to-1 probability checks on `building_assessments` (`06_buildings_cost.sql`), immutable `cost_estimates` and `reports.stats_snapshot` snapshots, non-overlapping road reopening in `resolve_compound_alert()` (`12_hazard_engine.sql:109-125`), `ST_DWithin(...::geography, ...)` index usage, BRIN indexes on append-only telemetry, and the Cairo seed scenario (`database/seed/02_demo_scenario.sql`).
2. **Verification Discipline (`docs/team-plan/`):** `docs/team-plan/person6_plan.md` and `docs/team-plan/review/person2_bela.md` explicitly forbid presenting placeholders or unrun baselines as verified operational claims.
3. **Strong Joint ML Prototype (`notebooks/kaggle/rv3_train_joint_serox50.ipynb`):** `SiameseUNetSE` (`se_resnext50_32x4d`, `MaskedFocalDiceLoss` combining weighted Focal + Dice + Lovász-softmax, `EMA`, `SWASoup`, and official `XView2PixelScorer`) is architecturally superior to the older 4-model cascade still described in `docs/PROJECT_ANALYSIS.md`.

---

### 2.1 Documentation Split-Brain, Architecture Contradictions & Container Overhead

#### [CRITICAL] Root `AGENTS.md` & Specs Lack an Engineering Contract for AI Agents
* **Evidence:** Root `AGENTS.md` covers only thesis Word/XML editing workflows; `docs/PROJECT_ANALYSIS.md` describes an obsolete 4-model cascade and old `src/` layout; `docs/documentation/chapter5/section_3_3.md:51` delegates `"3.1.5 Intended technologies"` to an unwritten Section `3.1` (`docs/team-plan/review/person3_joe.md:5,29`).
* **Consequence:** AI coding agents starting implementation immediately have no canonical single source of truth for folder boundaries, backend language, tile auth, offline sync, or testing gates.

#### [CRITICAL] Three Mutually Contradictory Architectures in the Same Repository
* **Evidence:**
  * `docs/architecture/platform-architecture-plan.md` (§1, §3): **NestJS** (TypeScript) modular monolith + separate **FastAPI** AI containers + `Martin/TiTiler`.
  * `docs/architecture/debate/gemini_proposal.md` (§3 Q2–Q3): **FastAPI** (Python 3.12+) core + 4 **`LitServe`** GPU containers + **`Procrastinate`** + **`Redis`** + `Martin` + `CesiumJS`.
  * `database/schema/15_security.sql:7` & `database/README.md:54`: cites `"the AI / Celery pipeline"`.
  * `docs/claude_view.md:45` vs. `docs/SAR_Drone_Simulation_Research.md:13`: **ROS 2 Jazzy + Gazebo Harmonic + PX4 SITL** vs. **Microsoft AirSim + UE5 + Streamlit**.
* **Consequence:** Any parallel multi-agent build without superseding those docs produces incompatible protocols, schemas, and containers.

#### [MAJOR] Unnecessary Container Sprawl (`platform-architecture-plan.md` & `gemini_proposal.md`)
* **Evidence:** `platform-architecture-plan.md` (§3) defines 9+ containers including 3 separate Python AI APIs; `gemini_proposal.md` (§4.2) expands to 14 containers including 4 separate `LitServe` GPU containers.
* **Consequence:** Maintaining separate GPU serving runtimes, duplicated CUDA contexts, and multi-language serialization contracts drains scarce lab VRAM and multiplies operational failure points.

---

### 2.2 Backend Language, Hazard Engine Security & Stream Schema Flaws

#### [MAJOR] NestJS Dual-Language Split-Brain (`platform-architecture-plan.md`)
* **Evidence:** `docs/architecture/platform-architecture-plan.md` (§6) advocates TypeScript/NestJS for Core API while keeping Python strictly inside AI/worker containers.
* **Consequence:** RescueVision's core domain is heavily geospatial and document-centric (collinearity raycasting, COG raster bounds via `rasterio`/`pyproj`/`shapely`, `pgr_aStar` topology prep, `WeasyPrint` RTL PDFs). NestJS forces awkward cross-language duplication or pushes core business logic into Python workers anyway.

#### [CRITICAL] `evaluate_hazard_rules()` Privilege Crash (`42501`) & Race Condition (`12_hazard_engine.sql` + `15_security.sql`)
* **Evidence:**
  * `database/schema/12_hazard_engine.sql:10-27`: `evaluate_hazard_rules(p_incident uuid)` is `SECURITY INVOKER` with no `pg_advisory_xact_lock`, looping over rules/hazards and writing `compound_alerts`, `compound_alert_sources`, `alert_closed_segments`, `road_segments`, `routes`, and `notifications`.
  * `database/seed/01_reference_data.sql:48-50`: `FIELD_RESPONDER` holds `hazard.report` but **not** `analysis.run` or `alert.resolve`.
  * `database/schema/15_security.sql:403,415,449-463`: `road_segments_write`, `routes_plan`, `compound_alerts_engine`, `compound_alert_sources_engine`, and `alert_closed_segments_engine` ALL require `app.has_permission('analysis.run') OR app.has_permission('alert.resolve')`.
* **Consequence:**
  1. **Privilege Failure:** When a Field Responder logs a `FLOOD_WATER` hazard under `rv_app` + `app.set_session_user()`, calling `evaluate_hazard_rules()` in the same transaction raises PostgreSQL error **`42501` (RLS violation)**.
  2. **TOCTOU Race Condition:** Concurrent flood reports pass `CONTINUE WHEN EXISTS` (`12_hazard_engine.sql:24-27`) simultaneously without `pg_advisory_xact_lock`, creating duplicate compound alerts and risking row-lock deadlocks on `road_segments`.

#### [MAJOR] Static Frame Ingestion Schema Breaks Live Drone Video (`01_types.sql` & `08_persons_cases.sql`)
* **Evidence:** `01_types.sql:33` restricts `media_kind` to `('PHOTO', 'VIDEO_FRAME')`, and `08_persons_cases.sql:25` enforces `person_detections.image_id uuid NOT NULL REFERENCES images(id)` (where `images` carries `UNIQUE (sha256)`).
* **Consequence:** Live 30 fps drone video person tracking cannot record streaming detections (`SMPTE 336M` KLV timestamps + crop keys) without writing thousands of individual frame files and `images` rows per sortie.

#### [MINOR] Fragile Bare `LISTEN/NOTIFY` Event Fan-Out (`gemini_proposal.md`)
* **Evidence:** `gemini_proposal.md` (§3 Q3) relies directly on Postgres `LISTEN/NOTIFY` → Redis Pub/Sub without a durable transactional outbox table.
* **Consequence:** `NOTIFY` drops events if API listeners reconnect/restart and truncates payloads at 8 KB, risking missed alerts and missed WebSocket revocations.

---

### 2.3 AI Architecture: Model/Config Contradictions, VRAM Waste, Domain Gap & Geometry

#### [CRITICAL] Model, Config, Seed & Notebook Contradictions
* **Evidence:** `database/seed/01_reference_data.sql:93-102` seeds a 3-stage pipeline (`U-Net ResNet34`, `DINOv2 + MLP`, `Siamese U-Net`); `configs/inference.yaml:4-13` selects `joint_damage` (`608px`); `docs/team-plan/review/person2_bela.md:20` flags `DINOv2` vs. `DINOv3`; and `notebooks/kaggle/rv3_train_joint_serox50.ipynb` implements `SiameseUNetSE` (`se_resnext50_32x4d`) while still cloning old `src/` paths.
* **Consequence:** Without consolidating on one canonical model registry (`joint_damage`, `post_damage_probe`, `person_sar_*`, `flood_road_seg`, `eo_embedder`), AI training, Triton export, and `ai_models` database records will contradict each other.

#### [CRITICAL] Single-GPU VRAM Exhaustion from Multi-Container Python Serving
* **Evidence:** Both `platform-architecture-plan.md` (3 FastAPI GPU containers) and `gemini_proposal.md` (4 `LitServe` GPU containers) isolate models in separate Python processes.
* **Consequence:** Each Python/PyTorch OS process creates an independent CUDA context (~0.5–1.5 GB VRAM overhead each) and cannot share CUDA streams or cross-model memory pools on a single GPU.

#### [CRITICAL] Severe Satellite-to-Drone Domain Shift & Dataset Mismatches
* **Evidence:**
  * `database/seed/01_reference_data.sql:93-102` ties building damage to `xBD` (0.3–3.0 m/px nadir satellite) + `RescueNet`, flood to `FloodNet`, and persons to `SARD` + `VisDrone` + `POP`.
  * `docs/team-plan/review/person2_bela.md:21` highlights `VisDrone` is a general urban benchmark, not a disaster dataset; `docs/claude_view.md:11,29` notes severe `GSD` and oblique parallax divergence between `xBD` and `1–3 cm` DJI imagery.
* **Consequence:** Untransformed `xBD` models fail on oblique DJI roofs/facades (`LADI v2` / `RescueNet` needed); `FloodNet`-only models fail on dense Middle Eastern urban concrete; and mixing `VisDrone` upright traffic pedestrians degrades tiny prone survivor recall on `SARD`/`HERIDAL`.

#### [CRITICAL] Zero Edge AI & Broken Flat-Earth Pixel-to-GPS Geometry
* **Evidence:** Existing plans require uploading raw imagery to MinIO before any AI runs, and `section_3_3.md` §3.3.8.3 projects detections using flat `altitude_agl_m` without storing camera intrinsics (`fx, fy, cx, cy`, distortion) in `04_imagery_ai.sql:25-33` or intersecting terrain DSMs.
* **Consequence:** Degraded disaster links stall post-flight uploads, while oblique `-45°` gimbal projections over uneven terrain/rubble shift survivor GPS pins by **10–40 metres**.

#### [MAJOR] Uncalibrated Damage Probabilities (`06_buildings_cost.sql`)
* **Evidence:** `building_assessments` stores `p_no_damage..p_destroyed` (`numeric(4,3)`) and `section_3_3.md` Table 3-45 commits to *"Show uncertainty openly"*, yet no Temperature Scaling (`ECE`) calibration step exists in the pipeline.
* **Consequence:** Out-of-distribution drone predictions emit overconfident `0.99` softmax scores, misleading responders and skewing expected restoration budgets.

---

### 2.4 Database, RLS, Tiles & Vector Choices

#### [CRITICAL] `Martin` Vector Tile Server Bypasses Row-Level Security (`D-04`)
* **Evidence:** Both `platform-architecture-plan.md` and `gemini_proposal.md` route vector tiles through `Martin`; verified against `maplibre/martin` issues `#78` & `#3369`, Martin uses a static `deadpool-postgres` pool with **no per-request `SET LOCAL` / JWT propagation**, and `IMMUTABLE` tile functions cannot execute `SET LOCAL`.
* **Consequence:** Direct Martin queries bypass multi-agency RLS (`D-04`), while query-string HMAC SQL hacks break tile caching and Martin auto-publishing.

#### [CRITICAL] PostgreSQL 18 Packaging Lock-In for `uuidv7()` (`00_extensions.sql`)
* **Evidence:** `00_extensions.sql:11-15` hard-aborts `< 180000`, `erd-design.md:3` still states `PostgreSQL 16`, and no single upstream Docker image ships PG 18 + PostGIS 3.6 + pgRouting 4 + `pgvector` + `pg_partman` together (`pgrouting/pgrouting:18-3.6-4.0` omits `pgvector` and `pg_partman`, and PG 18 changes the default volume mount to `/var/lib/postgresql`).
* **Consequence:** Without an explicit checked-in `database/Dockerfile` extending `pgrouting/pgrouting:18-3.6-4.0` via PGDG packages (or a PG 17 fallback), environment setup breaks inconsistently.

#### [MAJOR] `array_agg` RLS Scans, `PgBouncer` Safety, Fixed Partitions & Static `vector(768)`
* **Evidence:** `15_security.sql:74-121` runs nested `EXISTS` + `array_agg` helpers (`visible_incident_ids()`), `database/README.md:97-101` requires `BEGIN; ... COMMIT;`, `11_field_reports_audit.sql` hardcodes 24 monthly partitions ending Dec 2027 without `pg_partman`, and `image_embeddings` hardcodes `vector(768)`.
* **Consequence:** Unprepared-statement-unsafe drivers under `PgBouncer` fail or leak session state; post-2027 telemetry spills into unpartitioned default tables; and embedding upgrades to `1024-d` break schema compatibility.

---

### 2.5 Frontend Web, Mobile Offline, Citizen Channel & Security Hygiene

#### [CRITICAL] Dual-Engine MapLibre + CesiumJS Bloat (`erd-design.md` §1, `gemini_proposal.md` §4)
* **Evidence:** Plans mandate syncing both MapLibre (`~293 kB` gzip) and `@cesium/engine` (`~4.4 MB` min / `~1.2 MB` gzip).
* **Consequence:** Duplicates WebGL contexts, camera state, selection handlers, and bundle weight unnecessarily when `MapLibre GL JS` + `maplibre-gl-three` + `NASA-AMMOS/3DTilesRendererJS` + `maplibre-gl-splat` (`Spark`) handles 2D, 3D buildings, 3D Tiles, and localized 3DGS inside **one canvas**.

#### [CRITICAL] Unspecified Offline Sync Protocol & Off-Grid Failover (`D-08`)
* **Evidence:** `erd-design.md` §9 explicitly defers offline conflict resolution as *"out of scope"*, and `gemini_proposal.md` leaves `PowerSync` vs. custom SQLite unresolved without an emergency radio relay.
* **Consequence:** Simultaneous responder edits overwrite each other on reconnect, and zero-cell field sectors cannot transmit life-safety `SOS`/`FLOOD_WATER` beacons.

#### [MAJOR] Unspecified Citizen Channel, WebSocket Revocation & EXIF Privacy Holes
* **Evidence:** Citizen intake lacks hosting/app isolation and carrier-down shelter fallback (`05_citizens_media.sql:6` requires SMS OTP); `15_security.sql` revokes suspended users only "on the next request" (leaving active WebSockets open); citizen uploads lack an EXIF PII scrubbing stage.
* **Consequence:** Suspended accounts keep receiving live coordinates over open sockets, citizen photos leak device PII, and SMS outages lock citizens out.

---

## 3. Hard Research: Verified Open-Source Building Blocks

1. **Microsoft HASTE (`https://github.com/microsoft/haste`) & `microsoft/building-damage-assessment` (`https://github.com/microsoft/building-damage-assessment`):** Footprint-pooled foundation embeddings + logistic regression for rapid post-only building damage triage without pre-event imagery.
2. **ChangeOS / `torchange` (`https://github.com/Z-Zheng/ChangeOS`, `https://github.com/Z-Zheng/pytorch-change-models`):** Joint object-based building localization + 4-grade xView2 damage prediction in one forward pass (`ResNet` / `Swin-T`).
3. **TorchGeo (`https://github.com/torchgeo/torchgeo`), TerraTorch (`https://github.com/torchgeo/terratorch`), Clay v1.5 (`https://github.com/Clay-foundation/model`) & Prithvi-EO-2.0 (`https://github.com/NASA-IMPACT/Prithvi-EO-2.0`):** Standardized `xBD`/`BRIGHT` datamodules + VHR GeoFM embeddings (`Clay v1.5`).
4. **UAV & SAR Datasets (`RescueNet`: `https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation`, `LADI v2`: `https://github.com/LADI-Dataset/ladi-overview`, `https://arxiv.org/abs/2406.02780`, plus `SARD`/`HERIDAL`/`POP`):** Close the satellite-to-UAV oblique/GSD and tiny-victim recall gaps.
5. **NVIDIA Triton Inference Server (`https://github.com/triton-inference-server/server`) vs. `LitServe` (`https://github.com/Lightning-AI/LitServe`) / `BentoML` (`https://github.com/bentoml/BentoML`):** Triton C++ ONNX Runtime / TensorRT backends run all models in **one CUDA context** with dynamic batching and concurrent CUDA streams (avoiding multi-process Python VRAM duplication).
6. **MediaMTX (`https://github.com/bluenviron/mediamtx`) & OpenTAKServer (`https://github.com/brian7704/OpenTAKServer`):** Zero-transcode RTSP/SRT/WebRTC relay preserving `SMPTE 336M` KLV drone telemetry (`v1.17.0+`).
7. **ONNX Runtime (`https://github.com/microsoft/onnxruntime`):** Server/edge ONNX execution (`onnxruntime-react-native` `1.24.3` requires Gradle 9 patch `#27385` if used on mobile; `YOLOv8s` avoids RT-DETR NPU op gaps).
8. **PowerSync (`https://github.com/powersync-ja/powersync-js`) vs. ElectricSQL (`https://github.com/electric-sql/electric`) vs. Zero (`https://github.com/rocicorp/mono`):** Zero rejects offline writes; ElectricSQL requires manual write wrappers; **PowerSync + `@op-engineering/op-sqlite`** provides filtered Postgres WAL sync + encrypted SQLite offline writes + outbox out of the box.
9. **NATS Leaf (`https://github.com/nats-io/nats-server` `>= 2.14.1`) + Reticulum (`https://github.com/markqvist/Reticulum`) + Meshtastic (`https://github.com/meshtastic/firmware`) + MeshSat (`https://github.com/meshsat/meshsat-hub`):** Store-and-forward edge sync plus encrypted `<200 B` LoRa failover.
10. **MapLibre GL JS (`https://maplibre.org/maplibre-gl-js/docs/examples/`), `NASA-AMMOS/3DTilesRendererJS` (`https://github.com/NASA-AMMOS/3DTilesRendererJS`), `NodeODM` (`https://github.com/OpenDroneMap/NodeODM`), `OpenSplat` (`https://github.com/WebODM/OpenSplat`), `Spark` (`https://github.com/sparkjsdev/spark`), `SuperSplat` (`https://github.com/playcanvas/supersplat`), `maplibre-gl-splat` (`https://github.com/opengeos/maplibre-gl-splat`):** Unified single-canvas 2D + 3D Tiles + localized 3DGS without CesiumJS.
11. **TiTiler (`https://github.com/developmentseed/titiler`), `PMTiles` (`https://github.com/protomaps/PMTiles`), `maplibre-react-native` (`https://github.com/maplibre/maplibre-react-native`), & Martin RLS issues (`https://github.com/maplibre/martin/issues/78`, `https://github.com/maplibre/martin/issues/3369`):** Confirmed `ST_AsMVT` + Caddy `forward_auth` + Redis caching for RLS vector layers.
12. **Procrastinate (`https://github.com/procrastinate-org/procrastinate`) & PydanticAI (`https://github.com/pydantic/pydantic-ai`):** Postgres `SKIP LOCKED` job execution and typed read-only spatial tool calling.

---

## 4. Phased Implementation Roadmap (Capability Tracks — No Named Assignments)

Organize the 6-student build around **four parallel vertical architectural tracks**, integrated end-to-end across three phases (MVP → Field Calibration → Flagship Differentiators):

| Architectural Track | Scope & Deliverables |
|---|---|
| **Track 1: Data, Security & Core API** | PG 18 PGDG Docker (`database/Dockerfile`), RLS/hazard-engine SQL fixes (`12_hazard_engine.sql`, `15_security.sql`), `pg_partman`, `domain_events` outbox + `NATS JetStream`, 8-domain `FastAPI` + `psycopg3` core, authenticated `ST_AsMVT` Redis tile gateway, `Caddy`, `PydanticAI` read-only copilot. |
| **Track 2: AI Training, Triton & Photogrammetry** | Event-aware dataset curation (`xBD`, `BRIGHT`, `RescueNet`, `LADI v2`, `SARD`, `HERIDAL`, `FloodNet`), `SiameseUNetSE`/`ChangeOS` + `Clay`/`HASTE` + `RT-DETR`/`YOLOv8s` + `SegFormer-B2`, Temperature Scaling (`ECE`), DSM raycasting, ONNX parity + single-context `NVIDIA Triton` repo, `Procrastinate` `geo-worker` + `NodeODM`/`TiTiler`/`WeasyPrint`. |
| **Track 3: Web Digital Twin & Citizen Channel** | `pnpm` Turborepo `packages/api` (`openapi-ts`), unified `MapLibre` canvas (`2D` vectors + `TiTiler` swipe + `3DTilesRendererJS` + `Spark` 3DGS), 4D Incident Time-Travel Scrubber, RTL Arabic/English `i18next`, `apps/citizen` intake PWA + shelter QR flow. |
| **Track 4: Mobile Offline & Tactical Edge** | `apps/mobile` Expo Development Build (`@powersync/react-native` + `op-sqlite` + `@maplibre/maplibre-react-native` `.pmtiles`), offline merge rules, `MediaMTX` RTSP+`SMPTE 336M` KLV relay, Edge `YOLOv8s` + `NATS Leaf`, `MeshSat`/`Reticulum` LoRa `<200 B` failover. |

### Phase 1: Foundational Spine & Core Demo Loop (MVP)
- Checked-in `database/Dockerfile` + patched `12_hazard_engine.sql`/`15_security.sql` + Layer 4 RLS/concurrency CI gates.
- `core-api` (FastAPI + `psycopg3` + outbox → NATS + `ST_AsMVT` tiles) + auto-generated `frontend/packages/api`.
- Single `NVIDIA Triton` container serving parity-tested ONNX models (`joint_damage`, `flood_road_seg`, `person_sar_hq`, `eo_embedder`).
- `apps/web` MapLibre 2D + `fill-extrusion` 3D console with `TiTiler` swipe, damage verification, `pgr_aStar` routing, and `<60s` *Electrified Water* WebSocket alert flow.

### Phase 2: Offline Field Sync, UAV Calibration & Reports
- `apps/mobile` Expo Dev Build with `PowerSync` + `OP-SQLite` + `.pmtiles`, live GPS, START triage, and deterministic reconnect reconciliation.
- `NodeODM` orthomosaic/DSM/3D Tiles integration + `RescueNet`/`LADI v2` UAV adaptation + Temperature Scaling (`ECE <= 0.05`) + DSM pixel-to-GPS raycasting.
- `apps/citizen` intake PWA with EXIF PII scrubbing + frozen bilingual `WeasyPrint` PDF reports + instant NATS WebSocket revocation + Prometheus/Grafana SLA dashboard.

### Phase 3: Flagship Differentiators (Graduation Defense Modules)
1. **Live Drone Stream + Edge Triage (`MediaMTX` + KLV + Edge `YOLOv8s`):** Real-time WebRTC feed + `2 KB` detection / `50 KB` crop streaming over NATS Leaf.
2. **Off-Grid LoRa Failover (`MeshSat` + `Reticulum` + ESP32 Meshtastic):** Live zero-cell *Electrified Water* / `SOS` relay demo.
3. **4D Time-Travel Scrubber + Read-Only `PydanticAI` Spatial Copilot (`rv_readonly` + `pgvector`).**
4. **Localized 3D Gaussian Splats (`OpenSplat` + `Spark` inside MapLibre)** for priority collapse inspection.

---

## 5. Required Updates to Existing Repository Files (Migration Checklist)

| Existing File(s) | Current Problem | Required Update |
|---|---|---|
| Root `AGENTS.md` | Contains graduation-report Word workflow instead of engineering instructions. | Move thesis workflow to `docs/thesis/THESIS_WORKFLOW.md`; replace root `AGENTS.md` with [`docs/architecture/debate/redteam_gemini/AGENTS.md`](./redteam_gemini/AGENTS.md). |
| `docs/architecture/platform-architecture-plan.md`, `docs/architecture/debate/gemini_proposal.md`, `docs/PROJECT_ANALYSIS.md` | Describe contradictory NestJS / 4-LitServe / Martin / CesiumJS / 4-model-cascade architectures. | Mark superseded; promote [`VISION.md`](./redteam_gemini/VISION.md), [`ARCHITECTURE.md`](./redteam_gemini/ARCHITECTURE.md), [`REPO_LAYOUT.md`](./redteam_gemini/REPO_LAYOUT.md), [`DOCKER.md`](./redteam_gemini/DOCKER.md), [`AI_PIPELINE.md`](./redteam_gemini/AI_PIPELINE.md), [`TESTING.md`](./redteam_gemini/TESTING.md), and `docs/adr/*`. |
| `docs/documentation/chapter5/section_3_3.md` & `docs/superpowers/specs/2026-11-23-rescuevision-database-erd-design.md` | §3.1.5 unresolved; §3.3.8.3 omits intrinsics/DSM; references CesiumJS, PG 16, and omits offline sync resolution. | Align with unified Triton, PowerSync + NATS outbox, `ST_AsMVT`, single-canvas MapLibre 2D/3D/3DGS, DSM raycasting, and PG 18 PGDG packaging. |
| `database/schema/00_extensions.sql`, `11_field_reports_audit.sql`, `12_hazard_engine.sql`, `15_security.sql` | No `database/Dockerfile`; manual 2027 partitions; `evaluate_hazard_rules()` `SECURITY INVOKER` `42501` bug + missing advisory lock; mentions `"Celery"`. | Add `database/Dockerfile` (`pgrouting:18-3.6-4.0` + `pgvector` + `pg_partman` + `/var/lib/postgresql`), automate partitions, make `evaluate_hazard_rules()` `SECURITY DEFINER` + `pg_advisory_xact_lock`, update comment. |
| `database/schema/04_imagery_ai.sql` & `08_persons_cases.sql` | `media_kind` lacks streams/KLV; `capture_sessions` lacks intrinsics; `person_detections.image_id` is `NOT NULL`. | Add `STREAM_CLIP`/`EDGE_CROP`, intrinsic columns, and nullable `image_id` + `stream_ref` + `frame_pts_ms` for live RTSP/KLV detections. |
| `database/seed/01_reference_data.sql`, `configs/inference.yaml`, `docs/research_papers.md`, `notebooks/kaggle/*` | Contradictory model entries (`U-Net + DINOv2 + Siamese` vs `SiameseUNetSE`); `VisDrone` misframed; notebooks import old GitHub `src/`. | Standardize on canonical `ai_models` (`joint_damage`, `post_damage_probe`, `person_sar_hq`, `person_sar_edge`, `flood_road_seg`, `eo_embedder`), add `RescueNet` + `LADI v2`, and point notebooks cleanly to `ai/` package. |
| `docs/claude_view.md` & `docs/SAR_Drone_Simulation_Research.md` | Competing UE5/AirSim vs. Gazebo simulator proposals. | Mark simulation strictly optional (Phase 3 headless validation only); drop AirSim/Streamlit tracks. |

---

## 6. Verified Sources

1. Microsoft AI for Good Lab — **HASTE (`microsoft/haste`)** & **Building Damage Assessment**: https://github.com/microsoft/haste , https://github.com/microsoft/building-damage-assessment
2. HOT **fAIr**: https://github.com/hotosm/fAIr | UN OCHA **`ds-geospatial-impact-estimates`**: https://github.com/OCHA-DAP/ds-geospatial-impact-estimates
3. **ChangeOS** & **TorchChange**: https://github.com/Z-Zheng/ChangeOS , https://github.com/Z-Zheng/pytorch-change-models
4. **TorchGeo**, **TerraTorch**, **Clay**, **Prithvi-EO-2.0**: https://github.com/torchgeo/torchgeo , https://github.com/torchgeo/terratorch , https://github.com/Clay-foundation/model , https://github.com/NASA-IMPACT/Prithvi-EO-2.0
5. **RescueNet** & **LADI v2**: https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation , https://github.com/LADI-Dataset/ladi-overview , https://arxiv.org/abs/2406.02780
6. **NVIDIA Triton**, **LitServe**, **BentoML**, **ONNX Runtime**: https://github.com/triton-inference-server/server , https://github.com/Lightning-AI/LitServe , https://github.com/bentoml/BentoML , https://github.com/microsoft/onnxruntime
7. **MediaMTX** & **OpenTAKServer**: https://github.com/bluenviron/mediamtx , https://github.com/brian7704/OpenTAKServer
8. **PowerSync**, **ElectricSQL**, **Rocicorp Zero**: https://github.com/powersync-ja/powersync-js , https://github.com/electric-sql/electric , https://github.com/rocicorp/mono
9. **NATS Server**, **Reticulum**, **Meshtastic**, **MeshSat**: https://github.com/nats-io/nats-server , https://github.com/markqvist/Reticulum , https://github.com/meshtastic/firmware , https://github.com/meshsat/meshsat-hub
10. **MapLibre GL JS**, **3DTilesRendererJS**, **Spark**, **SuperSplat**, **OpenSplat**, **NodeODM**, **`maplibre-gl-splat`**: https://maplibre.org/maplibre-gl-js/docs/examples/ , https://github.com/NASA-AMMOS/3DTilesRendererJS , https://github.com/sparkjsdev/spark , https://github.com/playcanvas/supersplat , https://github.com/WebODM/OpenSplat , https://github.com/OpenDroneMap/NodeODM , https://github.com/opengeos/maplibre-gl-splat
11. **TiTiler**, **PMTiles**, **MapLibre React Native**, **Martin RLS Limitations**: https://github.com/developmentseed/titiler , https://github.com/protomaps/PMTiles , https://github.com/maplibre/maplibre-react-native , https://github.com/maplibre/martin/issues/78 , https://github.com/maplibre/martin/issues/3369
12. **Procrastinate** & **PydanticAI**: https://github.com/procrastinate-org/procrastinate , https://github.com/pydantic/pydantic-ai
