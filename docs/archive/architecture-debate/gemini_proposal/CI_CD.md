# CI/CD Pipeline Architecture (`CI_CD.md`)

**Chosen CI/CD Platform:** **GitHub Actions** + **GitHub Container Registry (`ghcr.io`)**.
**Why GitHub Actions?** Native PR status checks, zero extra CI server to maintain on the Contabo VPS, free Linux runners for all CPU/DB/contract stages, native OIDC/SSH deployment secrets, and seamless path-filtered workflows so frontend PRs do not wait on GPU AI builds.

---

## 1. Pipeline Overview (5 Workflows)

```text
PR opened / updated
 ├── [1] ci-fast.yml (Always, ~2-4 min)
 │     ├── Secret & file-size guard (gitleaks + reject >5MB weights/rasters)
 │     ├── Python lint & architecture guard (ruff, mypy, import-linter)
 │     ├── Frontend lint, typecheck & unit tests (pnpm turbo lint typecheck test)
 │     └── OpenAPI-to-TS contract drift gate (export /openapi.json -> pnpm generate:api -> git diff)
 │
 ├── [2] ci-db-backend.yml (Path: database/**, backend/**)
 │     ├── Boot Postgres 18 + PostGIS 3.6 + pgRouting 4.0 + pgvector 0.8 + PgBouncer + Redis
 │     ├── Run ./database/build.sh (56 tables + checks.sql)
 │     ├── Run pytest unit + PostGIS/pgRouting + RLS cross-agency PgBouncer tests
 │     └── Run worker pipeline tests against cpu-mock LitServe contracts
 │
 ├── [3] ci-e2e.yml (PR to main / nightly, Path: frontend/**, backend/**, infra/**)
 │     ├── Boot docker-compose.yml + docker-compose.cpu-mock.yml
 │     └── Run Playwright E2E (UC-02 upload->map, UC-04 route, UC-07 Electrified Water, PDF snapshot)
 │
 └── [4] ci-ai-eval.yml (Path: ai/**, kaggle/**, or workflow_dispatch)
       ├── nbstripout check on kaggle/**/*.ipynb
       ├── Run ai/eval/gate.py on self-hosted/cloud GPU runner (or Kaggle/Modal job)
       ├── Verify ai/model_cards/<task>_<version>.md exists & metrics >= thresholds
       └── Build & push versioned Docker GPU image to ghcr.io/<org>/rv-ai-<svc>:<tag>

Merge to main / Release Tag (v*.*.*)
 └── [5] cd-deploy.yml
       ├── Build & Trivy-scan core images (core-api, geo-worker, web) -> push to ghcr.io
       ├── On merge to main -> Deploy to Contabo STAGING (automated smoke test)
       └── On tag v*.*.* + manual approval -> Deploy to Contabo PRODUCTION (backup -> migrate -> rolling swap -> healthcheck)
```

---

## 2. Detailed Job Specifications

### Stage A: Code Quality & Architectural Boundaries
* **`gitleaks` & Asset Guard:** Blocks API keys, `.env`, `.pem`, `.pt`, `.safetensors`, `.onnx`, or `.tif` files from entering Git.
* **`import-linter` (`.importlinter`):** Enforces that `backend/api` never imports ML frameworks, `ai/services` never imports `psycopg`/`sqlalchemy`, and `backend/api/app/modules/*` never cross-import private internals.
* **OpenAPI Contract Sync:** Boots `core-api` in schema-export mode (`python -m app.export_openapi`), runs `pnpm --filter @rescuevision/api generate`, and fails if `git diff --exit-code` shows uncommitted SDK changes.

### Stage B: Database, PostGIS & RLS Integration
* Uses a custom GHCR base image `ghcr.io/<org>/rv-postgres:18` (PostgreSQL 18 + PostGIS 3.6 + pgRouting 4.0 + pgvector 0.8) so DB startup takes `<10s` instead of compiling extensions per CI run.
* Runs `./database/build.sh` (which executes `database/tests/checks.sql`), then runs `pytest` through **PgBouncer in transaction mode** to prove `SET LOCAL` RLS isolation never leaks across pooled connections.

### Stage C: Security Scanning
* **SAST & Dependencies:** `bandit` / `ruff` security rules + `pip-audit` (Python) + `pnpm audit --audit-level=high` (JS/TS).
* **Container Vulnerability Scan:** `aquasecurity/trivy-action` scans built `core-api`, `geo-worker`, and `web` images (`CRITICAL`/`HIGH` CVEs fail release builds).
* **SBOM Generation:** Attach SPDX SBOMs to `v*.*.*` GitHub Releases.

### Stage D: AI Evaluation Gate & Container Publishing (`ci-ai-eval.yml`)
* Runs on a **self-hosted GPU runner** (or ephemeral cloud GPU runner triggered by GitHub Actions) only when `ai/**` or `kaggle/**` changes, keeping normal web/backend PRs fast.
* Executes `python -m ai.eval.gate --feature <name> --version <vN>`, validating held-out event-aware metrics and golden GeoTIFF outputs before pushing `ghcr.io/<org>/rv-ai-<svc>:sha-<short>`.

### Stage E: Contabo Continuous Deployment (`cd-deploy.yml`)
1. **Pre-deploy Safety Snapshot:** Runs `pg_dump` / `pgBackRest` snapshot on Contabo before touching containers.
2. **Pull & Migrate:** SSH (or Dokploy webhook) pulls pinned image SHA from `ghcr.io`, runs forward-only DB migrations inside a single lock step.
3. **Rolling Health-Checked Swap:** `docker compose up -d --wait` waits for `core-api` (`/health`), `martin`, `titiler`, and `proxy` healthchecks.
4. **Post-Deploy Smoke & Auto-Rollback:** Hits `GET /health`, `GET /v1/tiles/health`, and a read-only DB probe. If any probe fails within 60s, reverts `.env` `IMAGE_TAG` to the previous release tag and runs `docker compose up -d --wait`.
