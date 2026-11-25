# Proposed Repository Documentation Set (`DOCS_INDEX.md`)

Starting tomorrow, six developers and multiple AI coding agents will build RescueVision in parallel. To eliminate ambiguity and stop agents from inventing conflicting architectures, the repository must maintain the following canonical Markdown documentation set.

---

## 1. Root-Level Agent & Engineering Entrypoints

| File Path | Audience | Outline & Required Contents |
|---|---|---|
| `VISION.md` | Everyone + AI agents | 1-page product narrative tying F1–F6, citizens, multi-agency ICS, offline field ops, and Copilot into one loop + 5 non-negotiable invariants. |
| `AGENTS.md` | AI coding agents | Master execution contract: architecture map, strict SWE vs. AI boundaries, canonical commands, DB/RLS rules, codegen rules, Definition of Done, and "What NEVER to do". |
| `ARCHITECTURE.md` | Engineers + AI agents | 5-plane system topology, modular monolith boundaries, RLS + PgBouncer pattern, Martin/TiTiler security, WebSocket/Redis hub, end-to-end data flows. |
| `REPO_TREE.md` & `REPO_LAYOUT.md` | Everyone + AI agents | Canonical target folder tree + explicit "Lives Here / Forbidden Here" rules separating `backend/`, `frontend/`, `database/`, `ai/`, `kaggle/`, and `infra/`. |
| `BRANCHING.md` | Everyone + AI agents | Trunk-based Git flow, branch naming, protection/PR rules, Conventional Commits, SemVer tags, and git worktree isolation for concurrent AI agents. |
| `CI_CD.md` | Engineers + DevOps | GitHub Actions workflows (`ci-fast`, `ci-db-backend`, `ci-e2e`, `ci-ai-eval`, `cd-deploy`), Trivy/gitleaks scans, GHCR publishing, and rollback. |
| `HOSTING_CONTABO.md` | Engineers + DevOps | Contabo VPS deployment (Docker Compose + Caddy TLS + WireGuard burst GPU node), secrets, off-site backups, monitoring, staging vs. prod. |
| `DOCKER.md` | Engineers + AI agents | Container inventory, Dockerfiles, `docker-compose` profiles (CPU-mock vs. GPU vs. observability), `ai-net` isolation, and prod burst GPU model. |
| `AI_PIPELINE.md` | AI & Backend agents | Datasets/training → `ai/eval/gate.py` → `ai_models` registry → `LitServe` containers → `geo-worker` provenance → human review (`D-07`) + Copilot/Edge tracks. |
| `AI_TRAINING_LAYOUT.md` | AI & Research agents | Versioned `kaggle/<feature>/vN/` layout, 7 mandatory artifacts, MinIO weight storage (zero weights in Git), Kaggle CLI/`nbstripout` sync, promotion & rollback. |
| `REPO_CLEANUP.md` | Everyone (Day-1 migration) | Exact audit table (`KEEP | MOVE | ARCHIVE | DELETE`) for cleaning up legacy `dashboard/`, `mahmoudERD/`, `notebooks/kaggle/`, etc. |
| `TESTING.md` | Everyone + AI agents | 6-layer pyramid (lint/import-linter, unit, OpenAPI/Zod contracts, Postgres/RLS integration, AI eval gates, Playwright/Maestro E2E) + CI stages. |
| `CONTRACTS.md` | Backend, AI, Frontend agents | Single reference for: (1) FastAPI `/openapi.json` → `packages/api` codegen, (2) WebSocket Zod event schemas, (3) `LitServe` `/v1/predict` & `/v1/model-info` JSON/binary specs, (4) MinIO S3 key patterns, (5) `Idempotency-Key` offline sync rules. |

---

## 2. Architecture Decision Records (`docs/adr/`)

Short, immutable 1-page Markdown records (`Context → Decision → Consequences`) explaining *why* key choices were made so AI agents do not "helpfully" rewrite them:

* `docs/adr/0001-modular-monolith-over-microservices.md` — Why 8 domains live in one FastAPI app while AI/geo runtimes are isolated containers.
* `docs/adr/0002-postgres-skip-locked-and-redis-pubsub.md` — Why `Procrastinate` (`processing_jobs`) handles durable jobs and Redis handles only ephemeral realtime fan-out.
* `docs/adr/0003-litserve-isolated-ai-containers.md` — Why `LitServe` replaces in-process FastAPI inference and beats Triton/Ray complexity for this team.
* `docs/adr/0004-martin-titiler-pmtiles-geo-stack.md` — How COG raster tiles, Rust MVT vector tiles (with signed RLS incident context), and mobile offline `.pmtiles` work together.
* `docs/adr/0005-tanstack-router-and-expo-dev-builds.md` — Why `apps/web` uses Vite + TanStack Router (not Next.js/plain React Router) and `apps/mobile` requires Expo Dev Builds (not Expo Go).
* `docs/adr/0006-read-only-copilot-and-human-in-the-loop.md` — Why AI and the Commander Copilot can never mutate operational state without human sign-off (`D-07`).

---

## 3. Per-Service Local `README.md` / `AGENTS.md` Files

Each workspace carries a short (<60 lines) local instruction file scoped to agents working inside that folder:

* `database/AGENTS.md` — Never break `checks.sql` 56-table invariants, always add GiST indexes on `geometry(…, 4326)`, always add RLS policies for all 4 roles (`rv_app`, `rv_worker`, `rv_citizen`, `rv_readonly`).
* `backend/api/AGENTS.md` — Module boundary rules, mandatory `SET LOCAL` RLS dependency on every endpoint, OpenAPI schema export command, zero PyTorch imports.
* `backend/workers/AGENTS.md` — Idempotent job handlers, `<30s` progress heartbeat (`NFR-PF-05`), mandatory `inference_runs` provenance linking, calling `evaluate_hazard_rules()` on AI hazards.
* `ai/AGENTS.md` — Event-aware splits only, mandatory `ai/eval/gate.py` pass before updating `weights_uri`, `LitAPI` `/v1/model-info` contract, zero DB imports.
* `frontend/AGENTS.md` — Turborepo rule ("Apps import packages, packages never import apps"), `packages/api` gateway rule, TanStack Router Zod search params (`web`), `src/services/` native wrapper rule (`mobile`), RTL Arabic/English + accessibility (`NFR-US-02` never rely on color alone).

---

## 4. AI Model Cards (`ai/model_cards/`)

One concise card per active `ai_models` entry (`ai/model_cards/<task>_<version>.md`):
* `building_seg_segformer_v1.md`
* `change_detection_siamese_v1.md`
* `damage_cls_dinov2_v1.md`
* `flood_road_segformer_v1.md`
* `person_detect_yolo_bytetrack_v1.md`
* `image_embed_dinov2_v1.md`

Each card outlines: **Task & ERD `model_task`**, **Architecture & Input Shape**, **Training Datasets & Split Policy**, **Evaluation Gate Metrics (per-class F1/mIoU/mAP, calibration ECE)**, **Operational Limits (GSD threshold, cloud/smoke degradation, "does not see through rubble")**, and **SHA-256 / MinIO `weights_uri`**.
