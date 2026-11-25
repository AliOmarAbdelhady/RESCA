# Target repository tree

*Draft for the blueprint. This is the full tree the repository should have after Milestone 0, with one line on what lives in each folder, and the rules that keep it clean. The clean-up from the current tree is in `REPO_CLEANUP.md`.*

## 1. The shape

The repository has three kinds of top-level folders:

- **Software engineering side**: `backend/`, `frontend/`, `database/`, `contracts/`.
- **AI side**: `ai/`.
- **Shared**: `deploy/`, `tools/`, `specs/`, `scenarios/`, `fixtures/`, `docs/`, `.github/`.

The two sides touch in exactly three places:

1. **`contracts/`**: the OpenAPI documents of the AI services, which the backend's worker consumes through a generated client.
2. **`ai/registry/`**: which model version is active for each task, which the worker reads from the `ai_models` table at run time.
3. **Object storage**: AI services read inputs and write products there; the backend hands out the references.

Nothing else crosses. The backend has no model code, and the AI services have no database access.

## 2. The tree

```
rescuevision/
├── AGENTS.md                      How AI coding agents work in this repository. Read first.
├── VISION.md                      One page: what RescueVision is and why.
├── ARCHITECTURE.md                The system: containers, modules, data, flows, decisions.
├── CONTRACTS.md                   Index of every contract and the rules for changing one.
├── TESTING.md                     Test layers, gates, and which tests a change needs.
├── CONTRIBUTING.md                For people: setup, branches, pull requests, review.
├── SECURITY.md                    Security model in brief, and how to report a problem.
├── README.md                      What this is, how to run it in five minutes, where to read next.
├── LICENSE                        License of the project's own code.
├── THIRD_PARTY_NOTICES.md         License register of bundled and vendored components.
├── Makefile                       The single entry point for every command (`make help`).
├── .editorconfig                  One editor style for every file type.
├── .gitattributes                 Line endings, linguist overrides, diff settings.
├── .gitignore                     What never enters Git. Includes every model weight format.
├── .env.example                   Every variable, with a comment; no real values.
│
├── .github/                       GitHub configuration only.
│   ├── workflows/                 Continuous integration and deployment.
│   ├── CODEOWNERS                 Which paths need a review from which area.
│   ├── dependabot.yml             Dependency updates.
│   ├── PULL_REQUEST_TEMPLATE.md   The checklist every pull request fills in.
│   └── ISSUE_TEMPLATE/            Bug, feature, model-version and documentation issue forms.
│
├── backend/                       SOFTWARE: the application core (Python). One package, two run modes.
│   ├── AGENTS.md                  Rules for agents working here.
│   ├── README.md                  How to run, test and debug the backend.
│   ├── pyproject.toml             Dependencies and tool settings. No AI or GPU dependencies.
│   ├── uv.lock                    Locked dependencies.
│   ├── Dockerfile                 Multi-stage. Targets: `api`, `worker`.
│   ├── src/rescuevision/
│   │   ├── app/                   Composition root: settings, middleware, routers, live channel.
│   │   ├── platform/              Shared infrastructure: database pools, transactions, storage,
│   │   │                          auth, outbox, job runner, telemetry, tiles.
│   │   ├── modules/               One package per database domain. Ten modules.
│   │   │   ├── identity/          api.py, service.py, repo.py, schemas.py, events.py
│   │   │   ├── operations/        … same file set
│   │   │   ├── imagery/
│   │   │   ├── damage/
│   │   │   ├── routing/
│   │   │   ├── persons/
│   │   │   ├── hazards/
│   │   │   ├── field/
│   │   │   ├── citizens/
│   │   │   └── reporting/
│   │   └── worker/                Entry point, pipeline definitions, the landing steps.
│   └── tests/
│       ├── unit/                  No services, fast.
│       ├── integration/           Real PostgreSQL and object storage.
│       ├── contract/              The public API against its OpenAPI document.
│       └── rls/                   The generated row-level-security matrix.
│
├── frontend/                      SOFTWARE: everything that runs in a browser or on a phone (TypeScript).
│   ├── AGENTS.md                  Rules for agents working here.
│   ├── README.md                  How to run web, mobile and citizen apps.
│   ├── package.json               Turborepo scripts only.
│   ├── pnpm-lock.yaml             Locked dependencies.
│   ├── pnpm-workspace.yaml
│   ├── turbo.json
│   ├── apps/
│   │   ├── web/                   The command console. Vite single-page app, TanStack Router.
│   │   ├── mobile/                The field app. Expo React Native, Expo Router.
│   │   └── citizen/               The citizen request page. Small responsive web app.
│   └── packages/
│       ├── api/                   Generated client, typed hooks, WebSocket client. The only network code.
│       ├── contracts/             Domain types, enums and zod schemas. No I/O.
│       ├── ui/                    Shared components, design tokens, brand assets used by apps.
│       ├── config/                Shared TypeScript, lint and formatting presets.
│       └── utils/                 Pure helpers.
│
├── database/                      SOFTWARE: PostgreSQL. The only place the schema exists.
│   ├── AGENTS.md                  Rules for agents working here.
│   ├── README.md                  How to build, seed and test a database.
│   ├── build.sh                   Fresh build from the schema files (development and tests).
│   ├── Dockerfile                 PostgreSQL 18 with PostGIS, pgRouting and pgvector.
│   ├── schema/                    The schema, in numbered SQL files. Source of truth.
│   ├── migrations/                Ordered changes for long-lived environments.
│   ├── seed/                      Reference data and the fictional demo scenario.
│   ├── tests/                     Self-checks and the RLS matrix generator.
│   ├── tools/                     The ERD generator.
│   └── erd/
│       ├── rescuevision-erd.drawio, erd-overview.html   Generated. Never edited by hand.
│       └── mahmoudERD/            A teammate's multi-page ERD with its own generator. Kept as delivered.
│
├── contracts/                     The seam between the two sides. Reviewed like code.
│   ├── AGENTS.md                  Rules: what a breaking change is and what it requires.
│   ├── README.md
│   ├── openapi/                   One file per service: backend.yaml, infer-damage.yaml, …
│   ├── events/                    Event catalogue: names, payloads, audience, version.
│   ├── model-io/                  Input and output schemas per AI task.
│   └── storage-keys.md            The object-storage key layout.
│
├── ai/                            AI: models, training, evaluation, serving. The owner's "kaggle" folder lives here.
│   ├── AGENTS.md                  Rules for agents working here.
│   ├── README.md                  How the AI side is organised and how it connects to the backend.
│   ├── pyproject.toml             Training dependencies. Torch lives here only.
│   ├── uv.lock
│   ├── libs/
│   │   ├── modelkit/              Shared training utilities: datasets, metrics, seeds, logging.
│   │   └── serving/               Shared serving library: health, task queue, tracing, GeoTIFF windows.
│   ├── services/                  One folder per serving container.
│   │   ├── base/                  The CPU runtime image: Python, ONNX Runtime, OpenVINO, geospatial libraries.
│   │   ├── damage/                Dockerfile and code for `infer-damage`.
│   │   ├── people/                Dockerfile and code for `infer-people`.
│   │   ├── hazard/                Dockerfile and code for `infer-hazard`.
│   │   └── embed/                 Dockerfile and code for `infer-embed`.
│   ├── training/                  One folder per feature, one sub-folder per model version.
│   │   ├── _template/             Copy of this starts every new version.
│   │   ├── LEDGER.md              One table: every version, its metrics and its status.
│   │   ├── damage-assessment/     v1/, v2/, …
│   │   ├── hazard-segmentation/   v1/, …
│   │   ├── person-detection/      v1/, …
│   │   └── image-embedding/       v1/, …
│   ├── registry/                  Desired state in Git: the active version per feature, and the gates.
│   │   ├── <feature>.yaml         One per feature, for example damage-assessment.yaml.
│   │   └── policy.yaml            The gates of AI_PIPELINE.md §4.
│   ├── benchmarks/                CPU latency budgets and the benchmark script.
│   └── datasets/                  Dataset manifests only. No data.
│
├── deploy/                        Everything the server needs. Managed by Git, applied by CI.
│   ├── README.md                  How a deployment works, and how to undo one.
│   ├── compose/                   compose.yaml, compose.dev.yaml, compose.prod.yaml,
│   │                              compose.gpu.yaml, compose.observability.yaml
│   ├── proxy/                     Traefik static and dynamic configuration.
│   ├── bin/                       deploy.sh, backup.sh, restore.sh, healthcheck.sh
│   └── server/                    First-day server setup script and hardening checklist.
│
├── tools/                         Developer tools. Run through `make`.
│   ├── README.md
│   ├── pyproject.toml
│   └── src/rv_tools/              docs_check, repo_check, scenario, kaggle, bundle.
│
├── specs/                         The single track. One folder per feature.
│   ├── README.md                  Roadmap and the order of work.
│   └── <feature>/                 spec.md (what and why), plan.md (how), tasks.md (steps).
│
├── scenarios/                     Scenarios as code, replayed through the public API.
│   ├── README.md
│   └── <scenario>/                timeline.yaml, manifest.yaml, expected.yaml, README.md
│
├── fixtures/                      Small test data, committed. Size-limited.
│   ├── rasters/                   Tiny GeoTIFFs and COGs.
│   ├── network/                   A miniature road network for pgRouting tests.
│   ├── imagery/                   A handful of small drone and satellite images.
│   └── models/                    Tiny models with the same input and output contract as the real ones.
│
└── docs/                          Human documentation that is not one of the root files.
    ├── README.md                  Index and reading paths.
    ├── adr/                       Architecture decision records. Numbered, immutable once accepted.
    ├── architecture/              Deep dives: live channel, offline sync, hazard engine, security model.
    ├── runbooks/                  Deploy, rollback, backup, restore drill, model rollback, demo day.
    ├── research/                  Papers, datasets, earlier analyses. Background, not instructions.
    ├── documentation/             The graduation report and its evidence. Kept in place. Has its own AGENTS.md.
    └── team-plan/                 The report work plan, figures and review notes. Kept in place.
```

## 3. Rules that keep it clean

These rules are checked by `make repo-check` in CI. A rule that cannot be checked automatically is written as a review checklist item in the folder's `AGENTS.md`.

| Where | What is forbidden | Checked by |
| --- | --- | --- |
| Root | Any file or folder that is not in the tree above. | Allowlist in `rv_tools/repo_check.py`. |
| `backend/` | Importing a model, torch or anything from `ai/`. | Dependency list and Import Linter. |
| `backend/src/…/modules/` | Importing another module's internals. SQL that names a table the module does not own or declare as readable. | Import Linter; table-ownership test. |
| `backend/` | Creating, altering or dropping tables. | Text scan for DDL outside `database/`. |
| `ai/services/` | Database drivers, SQLAlchemy, `psycopg`, or importing `rescuevision`. Training code. Torch in the image. | Dependency scan; container image scan. |
| `ai/libs/serving/` | Code that knows about one particular model. | Review checklist. |
| `ai/training/` | Model weights, datasets, outputs, caches. | `.gitignore` plus a scan for weight file extensions. |
| `ai/training/<feature>/vN/` | A version folder without the required files. | `repo-check` schema. |
| `frontend/apps/*` | `fetch`, axios, or WebSocket code outside `packages/api`. Native module use outside `src/services/`. | Lint rules. |
| `frontend/packages/*` | Importing from `apps/`. | Lint rules. |
| `frontend/apps/web/` | Importing `expo-*` or React Native modules. | Lint rules. |
| `database/schema/` | An edit without a matching migration. A fresh build that differs from a migrated database. | CI: fresh build equals migration path. |
| The generated files in `database/erd/`, `contracts/`, `frontend/packages/api/src/generated/` | Hand edits. | `make contracts-check`; regenerated files must match. |
| `database/erd/mahmoudERD/`, `docs/documentation/`, `docs/team-plan/` | Deleting a file. A move that is not a pure `git mv`. | `repo-check` protected list (`REPO_CLEANUP.md` §1) |
| `deploy/` | Secrets, real hostnames in code, image tags without a digest in `compose.prod.yaml`. | Secret scan; `repo-check`. |
| `docs/adr/` | Editing an accepted record. | New record supersedes the old one. |
| `scenarios/`, `fixtures/` | Files above the size limit. Personal data. Real citizen data. | Size scan; review checklist. |
| `.github/workflows/` | An action pinned by a tag instead of a full commit SHA. Secrets available to pull requests from forks. | Lint; review checklist. |
| Anywhere | `.env` files, keys, `kaggle.json`, weights (`.pt`, `.pth`, `.onnx`, `.gguf`, `.tflite`, `.safetensors`, `.bin`), rasters (`.tif`). | `.gitignore`; secret and weight scans in CI. |

## 4. Where a new thing goes

| You are adding… | It goes in |
| --- | --- |
| An endpoint | `backend/src/rescuevision/modules/<module>/api.py`, plus `contracts/openapi/backend.yaml` regenerated |
| A table or column | `database/schema/` plus a migration, plus the RLS matrix, plus the ERD regenerated |
| A domain rule that must always hold | The database (constraint, trigger or function) |
| A map layer | `frontend/apps/web/src/features/<feature>/`, plus the layer spec in `frontend/packages/contracts` |
| An event pushed to clients | `contracts/events/`, an outbox trigger in `database/`, the schema in `frontend/packages/contracts` |
| A new AI model version | `ai/training/<feature>/vN/` from the template |
| A new AI task | `ai/services/<new>/`, `contracts/openapi/<new>.yaml`, `contracts/model-io/<task>/`, an ADR |
| A change to what the server runs | `deploy/compose/`, then CI deploys it |
| A demonstration or test scenario | `scenarios/<name>/` |
| A decision | `docs/adr/NNNN-title.md` |
| Work to be done | `specs/<feature>/tasks.md` |
| Research notes | `docs/research/` |

## 5. Size discipline

The repository must stay quick to clone. Three rules:

1. **Nothing generated or regenerable is committed**, except contract snapshots that must be reviewed.
2. **Binary files in `fixtures/` and `scenarios/` stay small.** A per-file limit and a folder budget are set in Milestone 0 and checked in CI.
3. **Large artifacts have a home outside Git**: model weights in release assets or the model store, datasets in versioned dataset storage, the evidence bundle in object storage, each pinned by a manifest with checksums inside Git.
