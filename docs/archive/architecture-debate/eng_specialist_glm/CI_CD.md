# CI_CD.md — the pipeline, stage by stage

Part of the Engineering Specialist F blueprint (`docs/architecture/debate/eng_specialist_glm/`).

## 1. Six principles

1. **`make check` is CI.** The same command runs on a laptop and on a runner. There is one
   definition of "passing".
2. **Filter at the job level, never at the workflow level.** A workflow skipped by a path filter
   leaves its checks pending forever and blocks the merge (section 4).
3. **One required check: `ci/ok`.** It is an aggregator that fails if anything that should have run
   did not succeed. Reviewers, branch protection and a future merge queue need to know one name.
4. **No GPU anywhere.** The laptops are source-only, training runs on free Kaggle or Colab GPUs,
   and the demonstration host is a CPU-only Contabo server for one user at a time (the owner's
   constraint). CI verifies the evidence of training (hashes, records, metrics), tests model
   contracts with a fixture bundle on a CPU, and proves that every deployed AI image runs its
   bundle on CPU with ONNX Runtime or OpenVINO.
5. **Every number quoted in the report comes from a CI or run artifact.** No artifact, no number.
6. **Heavy work is precomputed, and a check says so.** Photogrammetry, area-wide analysis and
   embedding builds never run on a request. A demonstration is ready only when `demo-verify` has
   passed on the server (section 10.6).

The repository is public, so "Standard GitHub-hosted runners in public repositories" are free.
Larger runners are not; the pipeline below fits on standard runners.

## 2. Triggers

| Event | Workflows | Note |
|---|---|---|
| `pull_request` | `ci.yml` | the main path |
| `merge_group` | `ci.yml` | for the merge queue, whenever it is switched on (BRANCHING.md, section 4) |
| `push` to `main` | `ci.yml`, `cd-staging.yml` | build, publish, deploy to staging |
| `push` of a tag `v*.*.*` | `cd-release.yml` | build, publish, deploy to production |
| `workflow_dispatch` | `model-promote.yml`, `ai-eval-verify.yml` | manual, with inputs |
| `schedule` (nightly) | `ci.yml` with label `full`, `security.yml` | end-to-end, mobile, full scans |
| `pull_request` with label `e2e` or `mobile` | adds `e2e-web`, `e2e-mobile` jobs | on demand |

Concurrency: one run per pull request; a new push cancels the previous run. `cancel-in-progress`
is **off** for `main` and tags, so a deploy is never half-finished by a later push.

## 3. Stage by stage

```text
pull request ──► [changes]  which areas did this pull request touch?
                 │
                 ├─► [guard]            always · ~1 min · secrets, large files, notebooks, agent files, title
                 ├─► [static-python]    ai/ services/ database/tools tools/ contracts/   · ~3 min
                 ├─► [static-ts]        frontend/ contracts/                               · ~3 min
                 ├─► [db]               database/ services/ contracts/                   · ~4 min
                 ├─► [contracts]        contracts/ services/ frontend/packages/api database/ · ~4 min
                 ├─► [integration]      services/ contracts/ database/                   · ~6 min
                 ├─► [ai-contract]      services/ai/ contracts/openapi/ai-service.yaml   · ~5 min
                 ├─► [ai-perf]          main or nightly · CPU latency of every active bundle · ~5 min
                 ├─► [ai-evidence]      kaggle/ ai/datasets/                               · ~2 min
                 ├─► [docs]             **/*.md docs/ specs/                              · ~1 min
                 ├─► [e2e-web]          label e2e, or main, or nightly                    · ~10 min
                 └─► [e2e-mobile]       label mobile, or nightly                           · ~15 min
                              │
                              └──► [ci-ok]  always · the only required check
```

Times are targets for a warm cache. The pull request path without labels is about eight minutes
end to end because the jobs run in parallel.

## 4. The aggregator, and why

GitHub's documentation on filters: "If a workflow is skipped due to path filtering, branch
filtering, or a commit message, then checks associated with that workflow will remain in a
'Pending' state. A pull request that requires those checks to be successful will be blocked from
merging." So `ci.yml` never has a top-level `paths:` key. Each job decides for itself with `if:`,
and one job at the end reports the result:

```yaml
# .github/workflows/ci.yml  (sketch; the real file is longer)
on:
  pull_request:
  merge_group:
  push:
    branches: [main]
  schedule:
    - cron: "0 2 * * *"
  workflow_dispatch:

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      python: ${{ steps.f.outputs.python }}
      ts: ${{ steps.f.outputs.ts }}
      db: ${{ steps.f.outputs.db }}
      # … one output per area
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }        # Turborepo's affected detection needs history
      - id: f
        env:
          BASE: ${{ github.base_ref || 'main' }}
        run: python3 tools/check_repo.py areas --base "origin/$BASE" >> "$GITHUB_OUTPUT"

  guard:
    runs-on: ubuntu-latest          # always: no `if`
    steps: [ gitleaks, large-file check, nbstripout --verify, make agents-check, PR title ]

  db:
    needs: changes
    if: needs.changes.outputs.db == 'true' || github.ref == 'refs/heads/main' || github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - run: docker build -t rescuevision-db:ci database/     # the same image Compose and production use
      - run: make db-check                                     # tests start rescuevision-db:ci through Testcontainers

  # … static-python, static-ts, contracts, integration, ai-contract, ai-evidence, docs …

  ci-ok:
    # The only required check. Runs always, waits for everything, and fails unless every
    # job that was meant to run succeeded.
    if: always()
    needs: [guard, static-python, static-ts, db, contracts, integration, ai-contract, ai-perf, ai-evidence, docs]
    runs-on: ubuntu-latest
    steps:
      - name: Fail on anything but success or a deliberate skip
        env:
          NEEDS: ${{ toJSON(needs) }}
        run: |
          echo "$NEEDS"
          jq -n 'env.NEEDS | fromjson | to_entries
            | map(select(.value.result != "success" and .value.result != "skipped"))
            | if length > 0 then error("failed: \(map(.key))") else "ok" end'
```

A skipped job is a success for the aggregator (it was filtered out on purpose). A cancelled,
failed or missing job is a failure. With a merge queue, the same workflow runs on the `merge_group`
ref and reports `ci/ok` for the batch.

## 5. What each job does

| Job | Runs when | Steps |
|---|---|---|
| `changes` | always | one script decides the affected areas from the diff against the base; on `main` and nightly everything is affected |
| `guard` | always | gitleaks on the commits; file size over 5 MB; `nbstripout --verify` on notebooks; `make agents-check`; PR title is a Conventional Commit; no `.env` or key-like filename |
| `static-python` | Python areas | `mise install --locked`; `uv sync --frozen --all-packages`; `ruff check`; `ruff format --check`; `mypy` (strict in domain and contract modules); `lint-imports` (Import Linter: Forbidden, Protected, Layers, Independence contracts); `pytest` unit |
| `static-ts` | frontend, contracts | `pnpm install --frozen-lockfile`; `pnpm turbo run lint typecheck test --affected` (Turborepo finds the base by itself on GitHub Actions); ESLint `no-restricted-imports` for the frontend boundaries |
| `db` | database, services, contracts | start the project's database image; `dbmate up`; `checks.sql` (the existing 313-line self-check file); row-level security matrix as four login roles; the safety invariants (section 6); a fresh-from-zero database must equal the baseline |
| `contracts` | contracts, services, frontend API package | export `core-api.json` and `git diff --exit-code`; Spectral; oasdiff breaking against `main`; regenerate TypeScript client, enums and event types and diff; validate schema examples; fail if breaking without `!` in the title |
| `integration` | services, contracts, database | `pytest` with Testcontainers: the project database image, the object store (the same image as production), and the AI template in fixture mode; Schemathesis against core-api with the explicit examples; worker pipeline tests (stitch, analyze, route, report) with the fixture bundle; storage-key test |
| `ai-contract` | AI services, AI template | build each AI image; `/healthz`, `/readyz`, `/v1/model-info` equal the fixture manifest; `POST /v1/tasks` then `GET /v1/tasks/{id}` conforms to the template (Schemathesis); a task submitted twice with the same `job_id` writes once; the FP32 bundle and the quantised bundle both reproduce the golden output within the tolerance recorded in the manifest; the image contains ONNX Runtime or OpenVINO and no PyTorch, CUDA, Triton or TensorRT (dependency and layer audit) |
| `ai-perf` | `main`, nightly | run the active bundles on the golden tile set on the runner; record single-tile latency per model as an artifact and in `docs/ai/evaluations.md`; fail only above twice the recorded baseline. Runner hardware is not the server's (section 10.6) |
| `ai-evidence` | `kaggle/`, `ai/datasets/` | validate every `vN` folder against `_shared/dossier.schema.json`; notebook purity (thin, no credentials, no outputs); `dataset.lock.yaml` hashes present; `metrics.json` hash-linked to a `runs/*.json` record; `submit.json` well formed |
| `docs` | any Markdown | markdownlint; internal link check; decision records have valid frontmatter and status; no broken anchors; trace matrix is current |
| `e2e-web` | label, `main`, nightly | Compose core profile with `up -d --wait`; load the demo scenario; Playwright: sign-in, UC-07 flood report to alert banner, UC-02 upload to job progress, UC-08 report download, Arabic right-to-left, axe accessibility; traces and screenshots uploaded |
| `e2e-mobile` | label, nightly | Android emulator; Expo development build; Maestro flows: one-hand SOS, offline queue and replay, assignment deep link |
| `ci-ok` | always | the aggregator |

**Testcontainers.** Testcontainers Python's Postgres module lives at
`testcontainers.community.postgres` in the current source tree; there is no dedicated PostGIS
module. Tests therefore start **the project's own image** (`rescuevision-db`, built from
`postgis/postgis:18-3.6` plus pgRouting and pgvector), which is also the image Compose and
production use. `postgis/postgis:18-3.6` and `pgvector/pgvector:0.8.7-pg18` exist on Docker Hub
(checked). Nothing is tested against a database that is not the one we run.

## 6. What the database job must prove

These are defects the red-team review found by reading the SQL (`redteam_glm.md`, C4, C5, C8).
They are not fixed by this blueprint, which is about how work gets done. They are listed because
the first pull requests after Day 0 should be these tests, written to fail, followed by the fixes.
The "expected" column is a prediction from reading the SQL; nobody has executed these tests.

| Test | Statement | Expected today |
|---|---|---|
| `test_uc07_responder_can_trigger_alert` | a Field Responder inserts a flood hazard and the hazard is evaluated in the same transaction | fails (the engine runs as the caller, who may not write alerts) |
| `test_alerts_resolve_in_any_order` | after overlapping alerts raised and resolved in random orders, a segment is usable if and only if no live alert covers it | fails in some orders |
| `test_observation_during_closure_wins` | a road observation made during a closure is the condition after the last alert resolves | fails |
| `test_worker_cannot_change_audit_log` | `rv_worker` and `rv_app` cannot update or delete `audit_log` | fails |
| `test_two_reports_one_alert` | concurrent flood reports near one asset produce one alert | untested today |
| `test_active_model_has_evidence` | no `ai_models` row can be active without a weights hash and an evaluation record | fails (the seed marks nine models active and supplies neither) |

The last four words of the report's own standard apply to every one of them: a test that was
written, run and observed.

## 7. AI evaluation gates

There are two gates, and confusing them is how teams end up with numbers nobody can reproduce.

**Gate A: contract and regression, in CI, on a CPU, on every pull request that touches an AI
service.** Proves the service keeps its word: same endpoints, same output schema, probabilities
sum to one, and a fixture bundle produces the golden output within tolerance. Uses
`services/ai/_template`'s fixture bundle and `pytest-regressions`-style stored expectations.

On the CPU-only host the quantised bundle is the one that runs, so it is the one that is tested
next to its FP32 reference: the same class decisions on the golden tiles, and a maximum absolute
difference no larger than the tolerance recorded with the bundle. Precision is chosen per model by
measurement, not by a rule: the feasibility study measured its SegFormer-B2 proxy 4.1 times
slower with dynamic int8 than in FP32.

**Gate B: scientific evaluation, on Kaggle, by a person-approved submission.** Proves a model is
better on the metric of record. CI does not run it; CI **verifies its evidence**:

1. `ai-evidence` checks the folder's structure and hash links.
2. `ai-eval-verify.yml` (manual) re-downloads the run's artifacts named in `runs/<id>.json`,
   recomputes every SHA-256, and compares `metrics.json` with the artifact. A mismatch fails.
3. `model-promote.yml` (manual) requires a run in state `scientifically_reviewed`, a model card,
   and a metric of record at least equal to the current active version on the same frozen split.
   It then opens the promotion pull request (CONTRACTS.md, section 4.1).

Golden tests are stored expectations, not pixel-perfect equality across hardware: compare arrays
with a stated tolerance and compare class decisions exactly. A model that changes its output on a
golden tile set must change it deliberately, in a new `vN` folder.

## 8. Images

| Image | Built from | Runs where |
|---|---|---|
| `rescuevision-db` | `database/Dockerfile` | dev, CI, staging, production |
| `rescuevision-core-api` | `services/core-api/Dockerfile` | dev, staging, production |
| `rescuevision-worker` | `services/worker/Dockerfile` | dev, staging, production |
| `rescuevision-ai-<family>` | `services/ai/<family>/Dockerfile` | dev (fixture), staging, production, all on CPU |
| `rescuevision-web` | `frontend/apps/web` multi-stage build | staging, production |

- Built on every merge to `main`, tagged `sha-<short>` and pushed to `ghcr.io` with BuildKit
  layer caching (`cache-from`/`cache-to`).
- A release tag adds `X.Y.Z` and records the digest in the GitHub release.
- Staging and production deploy **by digest**, so a re-run deploys the same bytes.
- Each image gets an SBOM (Syft) and a Trivy scan; a fixable critical finding fails the release.
- AI images contain ONNX Runtime or OpenVINO and one pinned bundle. They contain no PyTorch, no
  CUDA and no Triton or TensorRT: a dependency and layer audit in `ai-contract` fails the build on
  any of them. There is no GPU image. If a GPU appears one day it is a new image behind an
  accepted decision record (ADR-0003), not a change to these.
- Every service has a memory limit in `infra/compose/docker-compose.prod.yml`, so one inference
  cannot starve PostgreSQL on the single host (section 10.6).
- The feasibility study in `docs/architecture/debate/cpu_demo_feasibility.md` reaches the same
  conclusion from measurements: a single-user demonstration runs on a GPU-less Contabo server
  with ONNX Runtime or OpenVINO when heavy work is precomputed.

## 9. Security scanning on a public repository

| Control | When | Blocks merge |
|---|---|---|
| gitleaks | every push | yes |
| push protection and secret scanning (repository settings; free for public repositories) | always | yes, at push time |
| Dependabot version and security updates (`.github/dependabot.yml`: github-actions, pip/uv, npm, docker) | weekly and on advisory | no; opens pull requests |
| Trivy on filesystem, lock files and images | every pull request, nightly for images | yes for fixable critical in a release |
| Code scanning (CodeQL default setup) for Python and JavaScript | every pull request | yes for high and critical with a fix |
| licence check on new dependencies | every pull request that changes a lock file | review only |

The three repository-level controls (secret scanning and push protection, Dependabot, CodeQL)
were not re-read in GitHub's documentation while this blueprint was written. Enable them under
Settings → Code security on Day 0 and confirm on the billing page that a public repository is not
charged for them.

## 10. Deploy to the Contabo VPS

### 10.1 Choice of orchestrator

| Option | Verdict | Reason |
|---|---|---|
| **Docker Compose + Caddy** (chosen) | use | one set of Compose files for laptop, CI and the server. `docker compose up --wait` "Wait for services to be running\|healthy". Caddy: "Automatic HTTPS by default", "ZeroSSL and Let's Encrypt for public names". No control plane to learn, and nothing in it needs a GPU. |
| **Object store: SeaweedFS in `weed mini` mode** (chosen); RustFS as the alternative | use | MinIO is out: the GitHub API shows its repository archived (last push 24 April 2026, last release October 2025). SeaweedFS is Apache-2.0, at release 4.55, and its README says `weed mini` "is auto-tuned for one node and is fine for single-node production, such as an S3 gateway that issues presigned URLs", which is this deployment. RustFS (Apache-2.0, 1.0.6, "Single Node Mode") is the alternative if a compatibility gap appears. The S3 API is the contract (ADR-0005), so the switch is one Compose service. |
| Kamal | not now | capable, but it deploys over SSH "using root by default", runs its own proxy and expects `GET /up`; on one host that duplicates what Compose and Caddy already do. Revisit only if a second server is ever bought. |
| Coolify or Dokploy | not on the demonstration server | both are open-source self-hosted consoles over Compose: Coolify offers "Dockerfile or Compose, with auto-deploy, PR previews, webhooks, and rollbacks"; Dokploy has "Native support for Docker Compose" and "Automatically integrates with Traefik". Each brings its own proxy and database, which is RAM taken from inference on a CPU-only machine. |
| k3s | no | "half the memory, all in a binary of less than 100 MB", and still a Kubernetes cluster to run, back up and debug for one machine. |
| Traefik instead of Caddy | no | an "open-source Application Proxy" with Docker-provider routing and `RateLimit`, `Headers` middlewares; fine, but Caddy needs no per-container labels and the edge is one service. |
| NVIDIA Triton, TensorRT, a model server of any kind | no | they exist to share a GPU. There is none. Each model family is a small ONNX Runtime or OpenVINO service (CONTRACTS.md, section 3.3). |

### 10.2 Topology

```text
GitHub Actions ──SSH──► Contabo VPS  (CPU only · one user at a time)
                          ├─ caddy            :80/:443  TLS, static web build, reverse proxy
                          ├─ core-api
                          ├─ worker                     queued jobs; one heavy inference at a time
                          ├─ web (static, served by caddy)   the browser draws the map in 2D and 3D
                          ├─ db               rescuevision-db, volume, WAL archive
                          ├─ objects          SeaweedFS (weed mini), S3 API, volume
                          ├─ tiles            raster tiles from cloud-optimised GeoTIFFs
                          ├─ ai-<family> ⚠     ONNX Runtime or OpenVINO on CPU, memory-limited
                          └─ nodeodm          profile `photogrammetry`, off by default (precomputed)
```

PostgreSQL, the object store and the AI services publish no port. Caddy is the only entry. The
SeaweedFS admin interface and WebDAV are not published at all: its README warns that `weed mini`
binds them "even without authentication". ⚠ ADR-0003 to 0006 decide which AI families exist, the
tile server and the transport. The CPU-only host is fixed by the owner.

### 10.3 Environments and secrets

| | Staging | Production (the demonstration) |
|---|---|---|
| Trigger | every merge to `main` after `ci/ok` | tag `vX.Y.Z` and an approval |
| GitHub Environment | `staging` | `production` (required reviewers: two) |
| Secret file | `infra/secrets/staging.enc.env` | `infra/secrets/prod.enc.env` |
| Data | the demo scenario, reloaded on each deploy | the demo scenario plus its precomputed artifacts |
| Migrations | automatic, before the new containers start | automatic, after a verified backup |
| Deploy during a demonstration | refused | refused: `deploy.sh` stops when `DEMO_FREEZE=1` is set |

The budget allows one server. Two Compose projects on it (staging and production, separate volumes
and ports) are acceptable only with the freeze rule above; otherwise staging is the same project
and a deploy never happens while somebody is demonstrating.

Secrets are encrypted with SOPS and age and committed. SOPS "encrypts with AWS KMS, GCP KMS, Azure
Key Vault, HuaweiCloud KMS, age, and PGP", so the age private key is the only secret GitHub holds.
Each environment has its own key and its own database passwords for the four login roles. Doppler
would add a hosted service between the team and its own server; it is not adopted.

Local `.env` files hold no secret: the development database password is a public default, and
nothing in `make up` talks to staging or production.

### 10.4 The deploy script (`infra/scripts/deploy.sh`)

```text
1. preflight     DEMO_FREEZE is not set · disk over 20 % free · docker reachable · image digests resolvable
2. backup        (production) pg_dump -Fc → restic → off-site bucket; refuse to continue on failure
3. decrypt       sops -d infra/secrets/<env>.enc.env > /run/rescuevision/env   (mode 600, tmpfs)
4. pull          docker compose pull      (by digest)
5. migrate       one-off container: dbmate up        (expand only)
6. switch        docker compose up -d --wait --wait-timeout 120 --remove-orphans
7. smoke         /healthz and /readyz of every service · sign in as a demo account · one page
                 (production) make demo-verify: every precomputed artifact present with its hash
8. record        write the release digest to /opt/rescuevision/releases/current
on any failure:  re-point to the previous digest and repeat 6 and 7; then stop and alert
```

Migrations are additive during a live exercise (CONTRACTS.md, expand and contract), so step 8's
rollback never has to undo a schema change.

### 10.5 Backups and the restore drill

The report promises daily backup and a tested restore (NFR-RL-05). The pipeline makes it a check:

| What | Tool and cadence | Proof |
|---|---|---|
| PostgreSQL | pgBackRest ("Full, differential, and incremental backups are supported"; "Checksums are calculated for every file in the backup and rechecked during a restore or verify"), or nightly `pg_dump -Fc` until the team learns it | off-site bucket, encrypted by restic |
| Object storage | nightly `restic` of the store's data directory: "a backup program that is fast, efficient and secure", with de-duplication, writing to "Amazon S3 (or S3-compatible)" | off-site bucket |
| **Restore drill** | monthly, scheduled workflow: restore last night's backup into a throwaway database container and run `checks.sql` plus a row count comparison | a green workflow run named `restore-drill`, linked from the runbook |

A backup that was never restored is a hope. The drill is the evidence.

### 10.6 The CPU-only, single-user demonstration

The owner's constraint: a strong CPU and plenty of RAM, no GPU and no budget to rent one, one user
at a time. Training happens on free Kaggle or Colab GPUs. The server runs the application and CPU
inference. Four rules follow, and each one has something in the repository that enforces it.

**Rule 1: heavy work is precomputed; the request path stays light.**

| Precomputed before a demonstration | Live, in front of the audience |
|---|---|
| photogrammetry (OpenDroneMap): orthomosaic, surface model, 3D tiles | sign-in, map, layer toggles (drawn in the browser) |
| area-wide damage and flood sweeps | inference on one tile or one photo that the user picks |
| the embedding index for similar cases | hazard report, alert, closed roads, a replacement route |
| the demo scenario's building, road and case records | live updates, responder positions, offline sync |

The feasibility study measured the live column on an i5-1135G7 laptop (4 cores): its DINOv2-base
proxy at 84 ms per crop with int8, its YOLOX-S proxy at 66 to 161 ms per frame, its Siamese damage
proxy at 0.63 to 0.85 s per tile. Its estimate for photogrammetry is 12 to 25 minutes for 50 to 80
images, which is why that row is never clicked live. Server figures are estimates until measured
in a rehearsal.

The mechanism: `infra/demo/manifest.yaml` lists every precomputed artifact (name, the job that
produces it, its object key, its SHA-256). `make demo-precompute` runs those jobs as queued jobs
with the `photogrammetry` profile enabled, the evening before. `make demo-verify` checks every
hash; the deploy smoke test and the runbook `run-the-demo.md` both call it.

**Rule 2: one heavy inference at a time, with threads pinned to physical cores.** The same study
found 4 threads faster than 8 on a 4-core laptop (222 ms against 413 ms on its ViT proxy), and
Contabo's EPYC cores expose AVX2 without the AVX-512 the laptop has. `services/ai/AGENTS.md` states
the rule; `bundle.lock.json` records the thread count; every service has a memory limit.

**Rule 3: precision is chosen per model by measurement.** Static int8 for the convolutional and
DETR models, dynamic int8 for the ViT, FP32 where quantisation made a proxy slower. The bundle
manifest records runtime, precision and the parity against FP32 (CONTRACTS.md, section 3.7), and
the `ai-perf` job records the latency.

**Rule 4: nothing large runs on the server except the application.** No language model on the host
(the study puts an 8-billion-parameter model at 4.5 to 5.5 GB and about 11 tokens per second on an
8-vCPU EPYC machine); no server-side 3D reconstruction; no message broker, stream relay or
sync service beyond what ADR-0004 requires for one user. 3D is drawn in the browser from tiles
and footprints the server serves.

**Sizing.** The study recommends Contabo's `Cloud VPS Plus 8` (8 vCPU, 24 GB RAM) for the
demonstration and a dedicated-core plan only if shared-host CPU steal shows in a rehearsal. Its
own budget puts the whole stack at about 5 to 6.5 GB of that. I did not check Contabo's plans or
prices; confirm them before buying.

## 11. Preview environments

The demonstration server is CPU-only and serves one user, so nothing else may run on it during a
demonstration.

1. **Week 1: one staging environment** that follows `main`. Everybody tests there.
2. **Week 2: web previews without a backend.** The web app builds as static files; a preview per
   pull request on any static host, pointed at the staging API with a read-only demo account.
3. **Full-stack previews per pull request are not planned.** Each one needs a PostgreSQL instance
   and a copy of the AI services, which is a second machine. If reviewers are blocked waiting for
   staging, buy that machine first; Coolify's pull request previews or a Compose project per
   pull request (`docker compose -p rv-pr-123`, a wildcard DNS record, Caddy on-demand TLS) both
   work there. Never on the demonstration server.

## 12. What CI refuses

- A notebook with outputs or credentials.
- A file over 5 MB, any weight, raster or dataset file.
- A hand-edited generated file, or one that is stale.
- A breaking contract change without `!` and an owner's approval.
- A migration that edits a merged migration, or drops a column without the expand step on `main`.
- A table without policies for the four roles.
- A pull request whose title is not a Conventional Commit.
- A change to agent configuration without its owner's approval.
- A claim of a metric in `docs/` without a run id.
- PyTorch, CUDA, Triton or TensorRT in a deployed image.
- A request handler that starts photogrammetry, an area-wide sweep or an embedding build (only a
  queued job with the `heavy` flag may).
- An active model bundle with no recorded CPU latency for its golden tile set.
- A deploy while `DEMO_FREEZE=1` is set on the server.

## 13. Order to switch things on (Day 0)

1. Create `.github/` with `ci.yml` containing only `changes`, `guard` and `ci-ok`. Merge it by pull
   request, the first one.
2. Protect `main` with the ruleset (BRANCHING.md, section 5) requiring `ci/ok`.
3. Turn on secret scanning, push protection, Dependabot and CodeQL default setup in repository
   settings.
4. Add `static-python`, `static-ts` and `db` jobs as each workspace gets its first real code.
5. Add the remaining jobs; then `cd-staging.yml` when there is a VPS.

CI grows with the repository. A pipeline full of jobs that have nothing to check yet teaches the
team to ignore red.

## Sources

Checked on 25 November 2026.

- GitHub Actions billing (free standard runners for public repositories):
  https://docs.github.com/en/billing/concepts/product-billing/github-actions
- Workflow syntax and the path-filter warning:
  https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- Merge queue and `merge_group`:
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- Turborepo in CI (`--affected`, shallow clones, remote cache):
  https://turborepo.dev/docs/crafting-your-repository/constructing-ci
- Import Linter: https://import-linter.readthedocs.io/en/stable/readme.html
- nbstripout (`--verify`, `--is-installed`, `.gitattributes`): https://github.com/kynan/nbstripout
- Testcontainers Python source tree (`src/testcontainers/community/postgres`):
  https://github.com/testcontainers/testcontainers-python
- Docker image tags, checked on Docker Hub: `postgis/postgis:18-3.6`, `pgvector/pgvector:0.8.7-pg18`
- Compose `up --wait`: https://docs.docker.com/reference/cli/docker/compose/up/
- Caddy: https://github.com/caddyserver/caddy (README)
- Kamal: https://kamal-deploy.org/docs/installation/
- k3s: https://docs.k3s.io/
- Traefik: https://doc.traefik.io/traefik/
- Coolify: https://github.com/coollabsio/coolify (README); Dokploy: https://github.com/Dokploy/dokploy (README)
- SOPS: https://getsops.io/docs/
- restic: https://github.com/restic/restic (README); pgBackRest: https://github.com/pgbackrest/pgbackrest (README)
- Playwright: https://github.com/microsoft/playwright; Maestro: https://github.com/mobile-dev-inc/maestro
- `pytest-regressions` (stored expectations for data, images and numeric tables):
  https://github.com/ESSS/pytest-regressions
- Red-team findings used in section 6: `docs/architecture/debate/redteam_glm.md` (C4, C5, C8, C10).
- Owner's constraint (CPU-only Contabo server, one user at a time, training on free Kaggle or
  Colab GPUs): message from the coordinator, 25 November 2026.
- CPU feasibility study, its laptop measurements and its Contabo sizing (its estimates are quoted
  as estimates): `docs/architecture/debate/cpu_demo_feasibility.md`.
- Repository status through the GitHub API on 25 November 2026: `minio/minio` archived, last push
  24 April 2026, release `RELEASE.2025-10-15`; `seaweedfs/seaweedfs` Apache-2.0, release 4.55
  (23 November 2026), README quote on `weed mini`; `rustfs/rustfs` Apache-2.0, release 1.0.6;
  `openvinotoolkit/openvino` Apache-2.0, release 2026.4.1; `OpenDroneMap/NodeODM` AGPL-3.0.
- ONNX Runtime: PyPI `onnxruntime` 1.32.0, "MIT License" (its source repository could not be
  located through the GitHub API on that date).
