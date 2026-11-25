# Final Target Repository Tree (`REPO_TREE.md`)

This is the single canonical target tree for the RescueVision repository—designed so six developers and AI coding agents know **instantly** where every file belongs and **what is forbidden** in every directory.

---

## 1. Ideal Target Repository Tree

```text
RescueVision/
├── VISION.md                                 # 1-page single product story & 5 non-negotiable operational invariants
├── AGENTS.md                                 # Master AI-agent & developer contract (commands, boundaries, DoD, never-dos)
├── ARCHITECTURE.md                           # 5-plane system topology, RLS/PgBouncer, Martin/TiTiler, data flows
├── REPO_TREE.md                              # This canonical tree + folder boundary rules
├── DOCKER.md                                 # Container inventory, Compose overlays (cpu-mock/gpu/obs), ai-net isolation
├── AI_PIPELINE.md                            # Training -> eval gate -> registry -> LitServe -> geo-worker -> UI review
├── AI_TRAINING_LAYOUT.md                     # Versioned `kaggle/<feature>/vN/` workflow, weight storage, promotion/rollback
├── BRANCHING.md                              # Trunk-based Git flow, worktrees for AI agents, PR/commit/release rules
├── CI_CD.md                                  # GitHub Actions pipelines (lint, DB/RLS, contracts, AI gates, GHCR, Contabo)
├── HOSTING_CONTABO.md                        # Contabo VPS + Caddy TLS + backups + monitoring + WireGuard burst GPU
├── TESTING.md                                # 6-layer test pyramid (boundaries, unit, OpenAPI/Zod, PostGIS/RLS, eval, E2E)
├── CONTRACTS.md                              # OpenAPI, WS Zod schemas, LitServe API spec, MinIO keys, Idempotency-Key
├── Makefile                                  # Standard entrypoints (`make dev`, `make test`, `make db`, `make gen-api`)
├── .importlinter                             # Enforces SWE vs. AI and Modular Monolith import boundaries in CI
├── .env.example                              # Template for local dev & staging environment variables (zero real secrets)
├── .gitignore                                # Blocks weights (*.pt, *.onnx, *.safetensors), rasters (*.tif), .env, outputs
│
├── .github/
│   ├── CODEOWNERS                            # Required review ownership for database/, infra/, ai/eval/
│   ├── PULL_REQUEST_TEMPLATE.md              # Checklist: tests, OpenAPI regen, RLS check, no weights in Git
│   └── workflows/                            # GitHub Actions: ci-fast, ci-db-backend, ci-e2e, ci-ai-eval, cd-deploy
│
├── database/                                 # [SWE] Authoritative PostgreSQL 18 + PostGIS 3.6 + pgRouting 4.0 + pgvector 0.8
│   ├── AGENTS.md                             # DB-specific agent rules (GiST indexes, RLS on all 4 roles, checks.sql)
│   ├── build.sh                              # Rebuilds clean DB + security + seeds + runs checks.sql
│   ├── schema/                               # Ordered baseline DDL (`00_extensions.sql` .. `15_security.sql`)
│   ├── migrations/                           # Forward-only incremental SQL migrations post-v1
│   ├── seed/                                 # Reference lookups (`roles`, `hazard_rules`) & Cairo demo scenario
│   ├── tests/                                # `checks.sql` + SQL invariant & RLS checks
│   └── tools/                                # Live catalog ERD generator (`generate_drawio_erd.py`)
│
├── backend/                                  # [SWE] Application & orchestration layer (FORBIDDEN: torch / ML weights)
│   ├── api/                                  # FastAPI Modular Monolith (`rv_app` & `rv_citizen` DB roles)
│   │   ├── AGENTS.md                         # API agent rules (`SET LOCAL` RLS, module public services, OpenAPI export)
│   │   ├── Dockerfile                        # CPU-only slim Python 3.12 image
│   │   ├── pyproject.toml                    # FastAPI, psycopg3/asyncpg, Pydantic v2, OpenTelemetry (NO PyTorch)
│   │   ├── app/
│   │   │   ├── main.py                       # FastAPI entrypoint, lifespan, health, OpenAPI export
│   │   │   ├── core/                         # Config, DB pool (`statement_cache_size=0`), RLS tx context, JWT, WS Hub
│   │   │   ├── copilot/                      # Read-only tool-calling Spatial Commander Copilot (pgvector + RLS views)
│   │   │   └── modules/                      # 8 bounded domain modules matching ERD (`identity`, `incidents`, `imagery`,
│   │   │                                     # `buildings_cost`, `routing`, `cases`, `hazards`, `field_reports`)
│   │   └── tests/                            # Unit tests + real PostGIS/PgBouncer RLS integration tests
│   ├── workers/                              # Procrastinate (`SKIP LOCKED`) async orchestrator (`rv_worker` DB role)
│   │   ├── AGENTS.md                         # Worker rules (idempotency, <30s progress, `inference_runs` provenance)
│   │   ├── Dockerfile                        # CPU worker image with GDAL/rasterio + ReportLab/WeasyPrint
│   │   ├── pyproject.toml                    # Procrastinate, rasterio, shapely, httpx, reportlab (NO PyTorch)
│   │   ├── jobs/                             # `stitch_job`, `analyze_job`, `route_job`, `report_job`
│   │   ├── clients/                          # Typed HTTP/2 clients for LitServe AI containers & NodeODM
│   │   └── tests/                            # Pipeline & contract tests against cpu-mock LitServe
│   └── shared/                               # Shared Python DTOs, MinIO key builders, geometry/config helpers
│
├── ai/                                       # [AI SERVING & EVAL] Production inference & gates (FORBIDDEN: DB creds/psycopg)
│   ├── AGENTS.md                             # AI serving rules (stateless LitAPI, `/v1/model-info`, zero DB imports)
│   ├── common/                               # Shared `LitServe` wrapper, health warmup, SHA-256 verification, OTel
│   ├── services/                             # Isolated Dockerized GPU inference containers on `ai-net`
│   │   ├── damage/                           # `Dockerfile.gpu` + `LitAPI` for building seg, change det, xBD DINOv2 grading
│   │   ├── person_track/                     # `Dockerfile.gpu` + `LitAPI` for occluded aerial YOLO + ByteTrack
│   │   ├── flood_road/                       # `Dockerfile.gpu` + `LitAPI` for FloodNet SegFormer water/road masks
│   │   └── embeddings/                       # `Dockerfile.gpu` + `LitAPI` for DINOv2 768-d `pgvector` retrieval vectors
│   ├── eval/                                 # `gate.py` & golden GeoTIFF regression fixtures (must pass before promotion)
│   ├── edge/                                 # ONNX / ExecuTorch export scripts for optional mobile/drone edge triage
│   ├── configs/                              # Production serving YAML configs & class-color maps
│   └── model_cards/                          # Standardized Markdown model card per active `ai_models` version
│
├── kaggle/                                   # [AI RESEARCH & TRAINING] Versioned Kaggle notebook workspace (NO weights in Git)
│   ├── README.md                             # Kaggle CLI pull/push workflow, `nbstripout`, promotion command
│   ├── _shared/                              # Reusable dataset loaders & event-aware split utilities
│   ├── damage-assessment/                    # `v1/`, `v2/`, `v3/` (each: kernel-metadata, notebook, config, dataset, metrics, card, export)
│   ├── person-detection/                     # `v1/`, `v2/` (SARD/VisDrone/POP occluded person detection + tracking tuning)
│   ├── flood-road-segmentation/              # `v1/` (FloodNet segmentation experiments)
│   └── scene-embeddings/                     # `v1/` (DINOv2 retrieval embedding experiments)
│
├── frontend/                                 # [SWE] Existing Turborepo + pnpm monorepo (FORBIDDEN: raw fetch/axios in apps)
│   ├── AGENTS.md                             # Gateway rule, TanStack Router search params, Expo Dev Build native boundary
│   ├── package.json & turbo.json             # Workspace scripts (`dev:web`, `dev:mobile`, `generate:api`, `build`, `test`)
│   ├── apps/
│   │   ├── web/                              # Vite + React + TanStack Router + TanStack Query + MapLibre GL JS + CesiumJS
│   │   └── mobile/                           # Expo Dev Build + Expo Router + MapLibre Native (`PMTiles`) + `OP-SQLite`
│   ├── packages/
│   │   ├── api/                              # THE GATEWAY: generated `openapi-typescript` SDK + `openapi-fetch` + WS client + hooks
│   │   ├── contracts/                        # Pure TS enums, damage scales, START triage, Zod WebSocket event schemas
│   │   ├── utils/                            # Pure geo math, uncertainty radius formatting, i18n helpers
│   │   └── config/                           # Shared tsconfig, ESLint (import guards), Tailwind presets
│   └── tooling/                              # `generate-api` OpenAPI codegen script & E2E harnesses (Playwright / Maestro)
│
├── infra/                                    # [OPS] Docker Compose stacks, reverse proxy, tile servers, Contabo ops
│   ├── docker-compose.yml                    # Core CPU stack (`postgres`, `pgbouncer`, `minio`, `redis`, `core-api`, `geo-worker`, `martin`, `titiler`, `web`, `proxy`)
│   ├── docker-compose.gpu.yml                # GPU overlay (`ai-damage-svc`, `ai-person-track-svc`, `ai-flood-road-svc`, `ai-embed-svc`, `nodeodm`)
│   ├── docker-compose.cpu-mock.yml           # Laptop dev/CI overlay mocking `ai-*-svc` contracts without CUDA
│   ├── docker-compose.obs.yml                # Prometheus, Grafana, Node/Postgres/DCGM exporters, OTel Collector
│   ├── postgres/                             # Custom Dockerfile combining PostgreSQL 18 + PostGIS 3.6 + pgRouting 4.0 + pgvector 0.8
│   ├── caddy/                                # `Caddyfile` (TLS 1.2/1.3, `/api`, `/ws`, `forward_auth` for Martin tiles)
│   ├── martin/                               # Martin Rust config & signed incident-scoped MVT SQL functions
│   └── scripts/                              # Contabo backup (`pgBackRest`/`rclone`), restore verification, deploy helper
│
└── docs/                                     # Documentation, ADRs, specs, and university graduation report
    ├── adr/                                  # Immutable Architecture Decision Records (`0001`..`000N`)
    ├── database/                             # Live-generated `rescuevision-erd.drawio`
    ├── specs/                                # Approved design specs (database ERD spec, SRS references)
    ├── research/                             # Literature papers, Tier-1 summaries, ethics & limitations
    ├── report/                               # Graduation report DOCX, Chapter 5 sources, team plans
    └── archive/                              # Historical prototypes (`mapping-prototype/`, old research notes)
```

---

## 2. Cleanliness Enforcement Rules (What Is Forbidden Where)

| Boundary | Rule | Enforced By |
|---|---|---|
| **`backend/` vs. `ai/`** | `backend/` never imports `torch`, `timm`, `transformers`, `ultralytics`; `ai/services/` never imports `psycopg`, `sqlalchemy`, or holds DB credentials. | `.importlinter` + separate Dockerfiles |
| **`kaggle/` vs. Runtime** | `kaggle/` never imported by `backend/`, `ai/services/`, or `frontend/`. Only exported `weights + manifest.json` in MinIO cross into `ai/eval/` and `ai/services/`. | `.importlinter` + CI path check |
| **Git vs. Heavy Artifacts** | Zero `.pt`, `.pth`, `.safetensors`, `.onnx`, `.tif`, `.tiff`, `.env`, or unstripped notebook outputs in Git. Weights & rasters live in MinIO. | `.gitignore` + `nbstripout` + CI >5 MB check |
| **`frontend/apps/*` vs. Network** | Apps never call `fetch`/`axios` directly; all traffic flows through `@rescuevision/api`. | ESLint `no-restricted-imports` |
| **`apps/mobile/src/features/*` vs. Native** | Features never import `expo-*`, `op-sqlite`, or MapLibre directly; native SDKs sit behind `src/services/*`. | ESLint `no-restricted-imports` |
| **`database/` vs. App Logic** | Only SQL DDL/migrations/seeds/checks live in `database/`. No application Python/TS code; all tables enforce RLS for all 4 roles. | `checks.sql` + RLS integration suite |
