# Target Repository Layout (`REPO_LAYOUT.md`)

This document defines the exact folder structure for RescueVision so that software-engineering (SWE) services, AI training/serving pipelines, database migrations, and shared contracts remain cleanly decoupled. **Every AI coding agent and developer must obey the "Lives Here / Forbidden Here" boundary rules.**

---

## 1. Software Engineering vs. AI Separation Principle

```text
  [ AI Side: ai/ ]                                [ SWE Side: backend/ · frontend/ · database/ ]
  ├── datasets & training (PyTorch/CUDA)           ├── database/  (PostgreSQL 18 + PostGIS + RLS)
  ├── evaluation gates & model cards               ├── backend/api/ (FastAPI Modular Monolith, NO PyTorch)
  └── isolated LitServe Docker containers  <=====  ├── backend/workers/ (Procrastinate Geo/AI Orchestrator)
        (HTTP/2 REST/gRPC + MinIO keys)            └── frontend/ (Turborepo: Vite/TanStack + Expo + packages/api)
```

* **Connection Contract:** The SWE side **never** imports `torch`, `timm`, `ultralytics`, or `transformers`, and the AI serving containers **never** import `sqlalchemy`, hold PostgreSQL credentials, or query business tables. They connect exclusively via:
  1. **Versioned Model Artifacts** in MinIO (`models/{task}/{version}/`) registered in `ai_models`,
  2. **Typed LitServe Inference APIs** (`GET /v1/model-info`, `POST /v1/predict`, `GET /health`), and
  3. **Geospatial Raster/Vector Files** in MinIO (`incidents/{incident}/...`) written/read by `backend/workers/`.

---

## 2. Complete Directory Tree & Boundary Rules

```text
RescueVision/
├── VISION.md                       # One-page product story and 5 non-negotiable invariants
├── ARCHITECTURE.md                 # System topology, 5-plane runtime, data flows, security model
├── AGENTS.md                       # Root rules, commands, boundaries, Definition of Done for AI agents
├── REPO_LAYOUT.md                  # This file: canonical directory ownership
├── DOCKER.md                       # Container inventory, compose profiles, AI network isolation
├── AI_PIPELINE.md                  # Training -> eval gate -> registry -> LitServe -> worker -> UI
├── TESTING.md                      # Unit, contract, PostGIS/RLS, AI eval gates, E2E, CI stages
├── CONTRACTS.md                    # OpenAPI, WebSocket Zod events, LitServe schemas, MinIO key layout
├── Makefile                        # Unified shortcuts (`make dev`, `make test`, `make generate-api`)
│
├── database/                       # [SWE] Authoritative PostgreSQL 18 + PostGIS + pgRouting + pgvector schema
│   ├── schema/                     #   Ordered DDL (00_extensions .. 15_security) — NO app Python/TS code
│   ├── migrations/                 #   Forward-only incremental SQL/Alembic migrations post-v1
│   ├── seed/                       #   Reference lookup data & Cairo demo scenario
│   ├── tests/                      #   SQL self-checks & RLS cross-agency isolation tests (`checks.sql`)
│   └── tools/                      #   ERD generator (`generate_drawio_erd.py`)
│
├── backend/                        # [SWE] Core application & async orchestration (NO ML model weights/PyTorch)
│   ├── api/                        #   FastAPI Modular Monolith (evolves root `api/`)
│   │   ├── app/core/               #     Config, psycopg/asyncpg pool (`SET LOCAL` RLS), JWT, WS hub, OTel
│   │   ├── app/modules/            #     8 bounded modules (`identity`, `incidents`, `imagery`, `buildings_cost`,
│   │   │                           #     `routing`, `cases`, `hazards`, `field_reports`) — import-linter checked
│   │   ├── app/copilot/            #     Read-only tool-using Commander Copilot (pgvector + SQL views only)
│   │   └── tests/                  #     Unit + PostGIS/RLS integration tests + OpenAPI snapshot export
│   ├── workers/                    #   Procrastinate (`SKIP LOCKED`) async orchestrator (`rv_worker` DB role)
│   │   ├── jobs/                   #     Stitching (NodeODM), COG tiling, AI batch dispatch, PDF report gen
│   │   ├── clients/                #     Typed HTTP/2 clients to LitServe AI containers & NodeODM
│   │   └── tests/                  #     Worker pipeline tests with mocked/golden LitServe responses
│   └── shared/                     #   Pure Python shared Pydantic schemas, DB queries, MinIO key helpers
│
├── ai/                             # [AI] Everything ML: datasets, training, eval, model cards, Docker serving
│   ├── common/                     #   Shared `LitAPI` server wrapper, `/v1/model-info`, CUDA/CPU device utils
│   ├── services/                   #   Isolated Dockerized LitServe inference containers (stateless, NO DB access)
│   │   ├── damage/                 #     xBD building seg (SegFormer/U-Net), change (Siamese), grade (DINOv2)
│   │   ├── person_track/           #     Aerial occluded person detector (YOLO) + ByteTrack
│   │   ├── flood_road/             #     FloodNet SegFormer water & road-obstruction segmentation
│   │   └── embeddings/             #     DINOv2 768-d crop/tile vector extractor for pgvector retrieval
│   ├── training/                   #   Offline training & dataset prep scripts (xBD, FloodNet, SARD/VisDrone/POP)
│   ├── eval/                       #   Automated evaluation gate suite (macro-F1, mIoU, mAP, ECE, golden GeoTIFFs)
│   ├── edge/                       #   Optional ONNX/ExecuTorch export scripts for mobile/drone edge triage
│   ├── configs/                    #   Model & training YAML configs (migrated from root `configs/`)
│   └── model_cards/                #   One Markdown card per active model (dataset, metrics, failure modes, limits)
│
├── kaggle/                         # [AI RESEARCH] Versioned Kaggle training workspace (NO weights in Git)
│   ├── _shared/                    #   Shared dataset loaders & event-aware splitters
│   └── <feature>/vN/               #   Versioned folders (`damage-assessment/v1`, `person-detection/v1`, etc.)
│                                   #   Each vN/: kernel-metadata.json, notebook.ipynb, config.yaml, dataset.yaml, metrics.json, model_card.md, export.py
│
├── frontend/                       # [SWE] Existing Turborepo + pnpm workspace (NO direct fetch/axios in apps)
│   ├── apps/
│   │   ├── web/                    #   Vite + React + TanStack Router + TanStack Query + MapLibre + CesiumJS
│   │   ├── mobile/                 #   Expo Dev Build + Expo Router + MapLibre Native (PMTiles) + OP-SQLite
│   │   └── citizen/                #   Lightweight Phone-OTP web request app (or scoped route under web)
│   ├── packages/
│   │   ├── api/                    #   THE GATEWAY: `openapi-typescript` + `openapi-fetch` + WS client + hooks
│   │   ├── contracts/              #   Shared TypeScript enums, START triage, damage scales, Zod WS event schemas
│   │   ├── utils/                  #   Pure geo math, coordinate formatting, uncertainty radius helpers
│   │   └── config/                 #   Shared tsconfig, eslint, tailwind presets
│   └── tooling/                    #   `generate-api` OpenAPI codegen script & frontend CI checks
│
├── infra/                          # [OPS] Container orchestration, reverse proxy, tile servers, telemetry
│   ├── docker-compose.yml          #   Core CPU stack (postgres, pgbouncer, minio, redis, api, worker, martin, titiler, web)
│   ├── docker-compose.gpu.yml      #   GPU overlay (ai-damage, ai-person-track, ai-flood-road, ai-embeddings, nodeodm)
│   ├── docker-compose.cpu-mock.yml #   Laptop dev overlay (CPU-only mock/tiny AI containers)
│   ├── caddy/                      #   TLS termination, reverse proxy, forward-auth for Martin vector tiles
│   ├── martin/                     #   Martin Rust vector-tile config + incident-scoped PostGIS tile functions
│   └── observability/              #   OpenTelemetry collector, Prometheus scrape configs, Grafana dashboards
│
├── docs/                           # Architecture specs, ADRs, graduation report sources
│   ├── adr/                        #   Architecture Decision Records (0001..000N)
│   ├── superpowers/                #   Approved DB & ERD specs
│   └── documentation/              #   University graduation report DOCX & Chapter 5 sources
│
└── mapping/                        # [ARCHIVE/RESEARCH] Existing Kahramanmaras Maxar exploration scripts & parquet
```

---

## 3. Folder-by-Folder Ownership & "Forbidden Here" Table

| Folder | What Lives Here | What Is FORBIDDEN Here |
|---|---|---|
| `database/` | DDL SQL (`00`–`15`), migrations, seeds, `checks.sql`, ERD generator. | Python/TS application logic, ML weights, secrets/passwords. |
| `backend/api/` | FastAPI routers, 8 domain services, RLS transaction middleware, WebSocket hub, read-only Copilot tool executor. | `torch`, `tensorflow`, `cv2` model inference, synchronous multi-minute stitching, raw SQL bypassing `app.set_session_*`. |
| `backend/workers/` | `Procrastinate` task handlers, COG window tiling (`rasterio`), NodeODM & LitServe HTTP clients, PDF generation. | Direct PyTorch model loading (`nn.Module`), HTTP endpoints exposed to browsers/mobile. |
| `backend/shared/` | Pydantic DTOs, MinIO key builders, shared DB session helpers. | Business logic tied to one HTTP route or ML framework dependencies. |
| `ai/services/*/` | `LitServe` (`LitAPI`) inference servers, preprocessing/postprocessing tensors, `/v1/model-info`, `Dockerfile.gpu`. | Database drivers (`psycopg`, `sqlalchemy`), user/JWT auth logic, business rules (e.g., hazard rules or cost formulas). |
| `ai/training/` & `ai/eval/` | Training loops, dataset loaders, evaluation gate benchmarks, golden GeoTIFF assertions. | Production serving endpoints, hardcoded local `/home/...` paths, unseeded random splits. |
| `ai/model_cards/` | Standardized Markdown cards documenting training data, metrics, thresholds, and known biases. | Raw binary weights (`.pt`, `.onnx` live in MinIO/LFS, never committed to Git). |
| `frontend/packages/contracts/` | Pure TypeScript enums, constants, and Zod schemas shared by web & mobile. | React components, `fetch`, `localStorage`, `expo-*`, Node APIs. |
| `frontend/packages/api/` | Generated OpenAPI client, TanStack Query hooks, WebSocket typed client. | Platform-specific storage (`localStorage`, `SecureStore`) or UI components. |
| `frontend/apps/web/` | Vite + React + TanStack Router pages, MapLibre/CesiumJS layers, Zustand UI state. | Direct `fetch`/`axios` calls bypassing `@rescuevision/api`, Next.js SSR assumptions, hardcoded API URLs. |
| `frontend/apps/mobile/` | Expo Router screens, `src/services/*` native wrappers, `OP-SQLite` offline queue, `PMTiles` map view. | Direct `fetch`/`axios`, raw native SDK imports inside `src/features/` (must go behind `src/services/`). |
| `infra/` | Compose files, Caddyfile, Martin config, Prometheus/Grafana/OTel configs. | Application source code, committed `.env` secrets or production TLS keys. |
| `mapping/` | Historical Maxar research prototype scripts and parquet index. | New production runtime dependencies (gradually supersede via `backend/workers/` + `TiTiler`). |
