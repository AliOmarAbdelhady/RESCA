# RescueVision — Ideal Target Repository Tree (`REPO_TREE.md`)

> **Standard:** One complete, unambiguous repository map after clean-up (`REPO_CLEANUP.md`). Every folder has **one purpose** and **explicit forbidden rules** so six engineers and any AI coding agent know immediately where code goes and what never belongs there.

---

## 1. Complete Target Tree

```text
RescueVision/
├── .github/
│   ├── CODEOWNERS                         # Required reviewers for database/schema, contracts, infra, triton-repo
│   └── workflows/                         # GitHub Actions CI/CD (ci-fast, ci-db-integration, ci-security, ci-ai-gate, ci-e2e, cd-deploy)
├── .gitignore                             # Ignores .env*, raw datasets, model binaries (.pt/.onnx/.plan), node_modules, .venv
├── AGENTS.md                              # Root engineering & AI coding agent operating contract (boundaries, commands, DoD, never-dos)
├── ARCHITECTURE.md                        # Canonical Local-First Tactical Digital Twin architecture, SQL fixes & 3 E2E flows
├── CONTRACTS.md                           # Guide to OpenAPI codegen, NATS domain_events schemas, LoRa CBOR & Triton contracts
├── Makefile                               # Canonical entrypoints: up-core, up-gpu, up-edge, db-migrate, db-check, gen-contracts, check-fast
├── pyproject.toml                         # Root uv workspace linking backend/ and ai/ with shared ruff & pytest config
├── VISION.md                              # 1-page unified product & technical story tying every feature into one coherent twin
│
├── contracts/                             # [SEAM] Cross-plane schemas & generated API artifacts
│   ├── openapi/                           # Exported FastAPI openapi.json (drift-checked in CI)
│   ├── events/                            # JSON Schema / AsyncAPI specs for domain_events, NATS subjects & <200B LoRa CBOR packets
│   └── triton/                            # Canonical input/output tensor shapes & label enums shared by ai/ and geo-worker
│
├── database/                              # [SWE] PostgreSQL 18 + PostGIS 3.6 + pgRouting 4 + pgvector + pg_partman
│   ├── Dockerfile                         # Extends pgrouting/pgrouting:18-3.6-4.0 + PGDG pgvector & pg_partman (/var/lib/postgresql)
│   ├── AGENTS.md                          # Local DB rules: migration order, RLS checklist, SECURITY DEFINER rules
│   ├── SECURITY_RLS.md                    # Zero-trust multi-agency RLS manual, PgBouncer rules, revocation & EXIF hygiene
│   ├── build.sh                           # Idempotent schema + migration + seed bootstrap script
│   ├── schema/                            # Ordered baseline DDL (00_extensions.sql .. 16_powersync_outbox.sql)
│   ├── migrations/                        # Forward-only timestamped SQL migrations post-baseline
│   ├── seed/                              # Reference data (roles, hazard_rules, ai_models, cost_profiles) + Cairo demo scenario
│   ├── tests/                             # SQL integrity suite (checks.sql) & pgTAP/RLS test fixtures
│   └── tools/                             # Automated ERD generator script (generate_drawio_erd.py)
│
├── backend/                               # [SWE] Python 3.12+ Platform API & Async Worker (ZERO PyTorch/CUDA)
│   ├── AGENTS.md                          # Modular monolith boundaries, psycopg3 explicit TX helper, domain_events rules
│   ├── Dockerfile                         # Multi-stage targets: `api` (core-api) and `geo-worker` (Procrastinate + rasterio + WeasyPrint)
│   ├── pyproject.toml                     # Backend dependencies (FastAPI, psycopg3, Procrastinate, PydanticAI, import-linter, tritonclient)
│   ├── src/rescuevision/
│   │   ├── api/                           # FastAPI routers (/api/v1/*), WS hub, Caddy forward_auth, ST_AsMVT Redis tile proxy
│   │   ├── domains/                       # 8 strict domain modules (auth_org, incidents, imagery_ingest, damage_cost, hazards_routing, persons_cases, citizens_reports, copilot)
│   │   ├── infra/                         # psycopg3 pool + set_config helper, NATS outbox relay, MinIO signer, Redis cache, OTel
│   │   └── worker/                        # Procrastinate tasks (STITCH, ANALYZE, REROUTE, REPORT_PDF, EXIF_SCRUB), SAHI slicer, Triton gRPC, DSM raycaster
│   └── tests/
│       ├── unit/                          # Pure Python unit tests (cost math, START triage, PowerSync merge, EXIF scrub, copilot)
│       ├── contract/                      # OpenAPI drift, NATS event schema & Triton tensor contract tests
│       └── integration/                   # Live PG18 + PostGIS + PgBouncer + NATS + Redis tests (RLS matrix, hazard lock race, WS revocation)
│
├── frontend/                              # [SWE] pnpm + Turborepo Multi-App Workspace
│   ├── AGENTS.md                          # Turborepo rules, generated API contract rule, RTL CSS rules, Expo Dev Build rules
│   ├── package.json                       # Root Turborepo scripts (lint, typecheck, test, build)
│   ├── pnpm-workspace.yaml                # Workspace packages declaration
│   ├── turbo.json                         # Cached build/lint/typecheck pipeline
│   ├── tooling/                           # OpenAPI->TS codegen script & shared ESLint/TSConfig presets
│   ├── apps/
│   │   ├── web/                           # Command Console SPA (React 19, Vite, TanStack Router/Query, single MapLibre 2D/3D/4D, RTL)
│   │   ├── mobile/                        # Field Responder app (Expo Dev Build, PowerSync + OP-SQLite, MapLibre Native .pmtiles, BLE LoRa)
│   │   └── citizen/                       # Standalone offline-capable Citizen Rapid Intake PWA + shelter QR / SMS OTP flow
│   └── packages/
│       ├── api/                           # Auto-generated @hey-api/openapi-ts client & Zod WS parsers (NEVER hand-edited)
│       ├── map-core/                      # Unified MapLibre style tokens, TiTiler swipe, maplibre-gl-three + 3DTilesRendererJS + Spark 3DGS
│       ├── sync-schema/                   # PowerSync client SQLite schema & deterministic conflict helpers
│       ├── ui/                            # Bilingual EN/AR RTL primitives (logical ms-/me- Tailwind, i18next, colorblind patterns)
│       └── utils/                         # Shared coordinate/formatting/triage constants & Zod validators
│
├── edge/                                  # [SWE+EDGE] Disconnected Field Kit (Drone GCS & Off-Grid Radio)
│   ├── AGENTS.md                          # Edge streaming, KLV geometry & <200B LoRa serialization constraints
│   ├── mediamtx/                          # mediamtx.yml RTSP/SRT/WebRTC WHEP relay preserving SMPTE 336M KLV metadata
│   ├── detector/                          # Lightweight ONNX Runtime / TensorRT YOLOv8s + ByteTrack KLV streamer -> NATS Edge Leaf
│   └── meshsat/                           # MeshSat / Reticulum + Meshtastic LoRa bridge (<200B CBOR SOS & flood beacons)
│
├── infra/                                 # [SWE] Local, Staging & Contabo Production Operations
│   ├── compose/                           # docker-compose.yml (core), docker-compose.gpu.yml, docker-compose.edge.yml, docker-compose.ops.yml
│   ├── caddy/                             # Caddyfile (TLS 1.3, forward_auth, ST_AsMVT/TiTiler/MediaMTX/Citizen routes)
│   ├── powersync/                         # powersync.yaml & sync-rules.yaml (per-agency WAL logical replication buckets)
│   ├── observability/                     # Prometheus, Grafana dashboards (NFR-PF-04 <60s SLA), Loki/Promtail & Uptime Kuma configs
│   ├── scripts/                           # Contabo VPS bootstrap, WireGuard/Tailscale GPU tunnel setup, pgBackRest/restic backup & restore scripts
│   └── secrets/                           # SOPS + age encrypted env files (*.enc.env) — NEVER plaintext secrets
│
├── ai/                                    # [AI] Shared Core ML Package (`rv_ai`) — Training, Calibration, Eval & Export
│   ├── AGENTS.md                          # Event-aware split rules, calibration ECE<=0.05 gate, ONNX parity <1e-4 rule
│   ├── Dockerfile.train                   # Offline NVIDIA PyTorch training/export container (never deployed to production VPS)
│   ├── Dockerfile.edge                    # Lean ONNX/TRT edge detector image
│   ├── pyproject.toml                     # Installs `rv_ai` cleanly for local CLI, CI gates & Kaggle `pip install git+...`
│   ├── src/rv_ai/
│   │   ├── datasets/                      # TorchGeo datamodules (xBD, BRIGHT, RescueNet, LADI v2, SARD, HERIDAL, FloodNet) & GSD transforms
│   │   ├── models/                        # SiameseUNetSE, ChangeOS, Clay/DINOv2 + HASTE probe, RT-DETR, YOLOv8s, SegFormer-B2
│   │   ├── training/                      # Deterministic Lightning/YAML training loops, EMA, SWASoup, MLflow logging
│   │   ├── calibration/                   # Temperature Scaling (ECE) & DSM collinearity raycasting calibration
│   │   ├── eval/                          # Blocking gate runner (XView2PixelScorer, SAHI recall, ECE, temporal LADI v2 split)
│   │   └── export/                        # ONNX / TensorRT exporter + numerical parity verifier (<1e-4) -> triton-repo/
│   └── tests/                             # Loss, GSD, raycasting, calibration & ONNX parity smoke unit tests
│
├── kaggle/                                # [AI] Owner's Versioned Feature Training & Experiment Dossiers
│   ├── README.md                          # MLflow config, Kaggle notebook bootstrap snippet, promotion & rollback workflow
│   ├── damage-assessment/
│   │   ├── v1/                            # Baseline (config.yaml, dataset_ref.json, train.ipynb, eval.ipynb, metrics.json, model_card.md, export.py)
│   │   ├── v2/                            # xBD + BRIGHT + RescueNet multi-GSD + Temperature Scaling
│   │   └── v3/                            # ChangeOS Swin-T + LADI v2 / local DJI AOI fine-tune
│   ├── person-detection/
│   │   ├── v1/                            # SARD + HERIDAL YOLOv8s (edge + baseline)
│   │   └── v2/                            # RT-DETR + SAHI tiled eval (+ optional POP thermal)
│   ├── flood-road-seg/
│   │   ├── v1/                            # SegFormer-B2 FloodNet + RescueNet
│   │   └── v2/
│   └── geo-embeddings/
│       └── v1/                            # Clay v1.5 / DINOv2 embedder + HASTE post-only probe
│
├── triton-repo/                           # [SEAM -> AI] Versioned NVIDIA Triton Model Repository (Weights in MinIO)
│   ├── README.md                          # How MinIO syncs .onnx/.plan artifacts; how Triton live-polls versions
│   ├── joint_damage/                      # config.pbtxt, labels.json, 1/manifest.sha256, 2/manifest.sha256
│   ├── post_damage_probe/                 # config.pbtxt, 1/manifest.sha256
│   ├── person_sar_hq/                     # config.pbtxt, 1/manifest.sha256
│   ├── flood_road_seg/                    # config.pbtxt, 1/manifest.sha256
│   └── eo_embedder/                       # config.pbtxt, 1/manifest.sha256
│
├── datasets/                              # [AI] Dataset Manifests, Checksums & Canonical Event-Aware Splits (NO raw images)
│   ├── README.md                          # Download instructions, licensing & MinIO s3://datasets/ layout
│   ├── splits_event_aware.csv             # Deterministic disaster-event train/val/test partitions
│   └── manifests/                         # SHA-256 checksum manifests for xBD, BRIGHT, RescueNet, LADI v2, SARD, HERIDAL, FloodNet
│
└── docs/                                  # System Documentation, ADRs, AI Cards, Operations & Thesis Workspace
    ├── adr/                               # 0001..0009 immutable Architecture Decision Records
    ├── ai/                                # MODEL_CARDS.md, EXPERIMENTS.md, RESEARCH_NOTES.md, LIMITATIONS_ETHICS.md, DATASET_SETUP.md
    ├── database/                          # Generated ERD HTML/DrawIO diagrams & ERD design spec
    ├── ops/                               # BRANCHING.md, CI_CD.md, DOCKER.md, HOSTING_CONTABO.md, TESTING.md, REPO_LAYOUT.md
    ├── thesis/                            # Graduation report (.docx builder, team-plan, review checklists, THESIS_WORKFLOW.md)
    └── archive/                           # Read-only historical architecture debates & legacy prototype snapshots
```

---

## 2. Hard Cleanliness Rules ("What Is Forbidden Where")

1. **Zero ML Frameworks in `backend/`:** `torch`, `torchvision`, `ultralytics`, `transformers`, and `CUDA` are forbidden in `backend/` and `frontend/`. All inference happens via KServe v2 gRPC to `triton` (or lightweight ONNX Runtime inside `edge/detector/`).
2. **Zero Business/DB/UI Logic in `ai/` or `kaggle/`:** `ai/` and `kaggle/` must never define FastAPI endpoints, PostgreSQL RLS SQL, Caddy rules, or React components.
3. **Zero Raw Datasets or Binary Weights in Git:** Raw images/orthomosaics live in `MinIO s3://datasets/` or local cache; `.pt`/`.onnx`/`.plan` weights live in `MinIO s3://model-artifacts/`. Git stores only manifests (`manifest.sha256`, `dataset_ref.json`), configs, metrics, and `config.pbtxt`.
4. **Zero Hand-Edited API Clients in `frontend/`:** `frontend/packages/api/` is strictly generated by `make gen-contracts` from `contracts/openapi/openapi.json`.
5. **Zero Copy-Pasted Models in `kaggle/*/vN/` Notebooks:** Notebooks import shared architectures/losses exclusively from the pinned `rv_ai` package (`ai/`), guaranteeing 1:1 parity between training, evaluation, and ONNX export.
6. **Zero Thesis Clutter in Code Paths:** Graduation-report `.docx` generation, Word review checklists, and `.pcraft` brand sources stay quarantined under `docs/thesis/` (or external asset storage) so AI coding agents never confuse thesis prose with executable platform contracts.
