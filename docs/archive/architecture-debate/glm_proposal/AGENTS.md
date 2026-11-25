# RescueVision: guide for AI coding agents

*Draft of the new root `AGENTS.md`, for AI coding agents and for the people who review them. It replaces the current root file, whose report rules move to `docs/documentation/AGENTS.md` (`REPO_CLEANUP.md` §1). The italic lines are removed when the file is installed.*

Read in this order before the first task: this file, the `AGENTS.md` of the folder the task names, the task's `spec.md` and `tasks.md` in `specs/`, then the part of `ARCHITECTURE.md` the task touches.

## What is being built

RescueVision turns drone and satellite imagery, field reports and citizen requests into one shared, live picture of a disaster that several agencies act on together. **AI proposes and people decide.** The flagship is the compound-hazard rule: a flood polygon near a power asset raises an alert, closes roads and warns responders in one database transaction. `VISION.md` tells the whole story in one page.

Four facts about the machine shape every change:

- **The server is CPU-only.** One Contabo host, no GPU and no budget for one, running a demonstration for one user at a time. Training and model export happen on free Kaggle or Colab GPUs.
- **Inference is CPU-friendly.** Serving containers run ONNX Runtime or OpenVINO. int8 is used only where a measurement shows it helps.
- **Heavy work is precomputed.** The orthomosaic, 3D products and area-wide analysis come from an evidence bundle. A request may analyse a small area of interest or one photo, and nothing larger.
- **Storage is the S3 API only.** The store is SeaweedFS by default. MinIO is not used: its repository is archived.

## The system in brief

| Part | What it is | What to remember |
| --- | --- | --- |
| `backend/` | One Python package, `rescuevision`, deployed twice: `api` and `worker`. Ten domain modules over one PostgreSQL. | Only the `worker` calls a model. Every request runs in a transaction that sets the acting user. |
| PostgreSQL | The only database: records, geometry, row-level security, the job queue, the event outbox and the rule engine. | No second database, queue or broker. |
| Object store | Every large file, reached by key and by presigned URL. | Image bytes never pass through the backend. |
| `ai/services/` | Four containers: `infer-damage`, `infer-people`, `infer-hazard`, `infer-embed`. One HTTP/JSON contract, one task at a time. | No database access and no training framework inside. |
| `frontend/` | Web console (Vite, TanStack Router and Query, MapLibre GL JS, deck.gl), field app (Expo), citizen page. | All network code is in `packages/api`. All 3D is drawn in the browser. |
| `deploy/` | Compose files, proxy configuration, deploy and backup scripts. | Change it only when the task says so. |

Three flows to know by heart are in `ARCHITECTURE.md` §7: imagery to map, report to alert, offline to online.

## Folders and their boundaries

| Folder | Owns | Never |
| --- | --- | --- |
| `backend/` | The application: `platform/`, the ten `modules/`, `worker/`. | Model code, torch, anything from `ai/`. SQL that creates or alters a table. |
| `frontend/` | `apps/web`, `apps/mobile`, `apps/citizen`, and `packages/`: `api`, `contracts`, `ui`, `config`, `utils`. | `fetch`, axios or WebSocket code outside `packages/api`. |
| `database/` | The schema in numbered SQL files, migrations, seed data, tests, the ERD. | An edit to `schema/` without a migration. |
| `contracts/` | OpenAPI documents, the event catalogue, model input and output, storage keys. | Hand edits to a generated file. |
| `ai/` | `training/` (one folder per feature, one per version), `services/`, `libs/`, `registry/`, `benchmarks/`. | Database drivers in `ai/services/`. Weights, data or notebook outputs in Git. |
| `deploy/` | Compose files, proxy, `bin/`, server setup. | Secrets. An image without a digest in `compose.prod.yaml`. |
| `tools/` | `rv_tools`: `docs_check`, `repo_check`, scenario, kaggle, bundle. Run through `make`. | Business logic, or a database connection that bypasses the public API. |
| `specs/` | One folder per feature: `spec.md`, `plan.md`, `tasks.md`. The single track of work. | Work that has no task here. |
| `scenarios/`, `fixtures/` | Scenarios replayed through the public API. Small test data and tiny models. | Personal data. Files above the size limit. |
| `docs/` | Decision records, deep dives, runbooks, research, and the graduation report in `documentation/` and `team-plan/`. | Editing an accepted decision record. Deleting report material. |
| `.github/` | Workflows, `CODEOWNERS`, issue and pull request templates. | An action pinned by a tag. Secrets for pull requests from forks. |

| You are adding | It goes in |
| --- | --- |
| An endpoint | `backend/src/rescuevision/modules/<module>/api.py`, then `make contracts` |
| A table or column | `database/schema/` with a migration, the RLS matrix and the ERD |
| A rule that must always hold | The database: a constraint, a trigger or a function |
| An event for clients | `contracts/events/`, its outbox trigger, its schema in `packages/contracts` |
| A map layer | `frontend/apps/web/src/features/<feature>/` |
| A model version | `ai/training/<feature>/vN/`, from `_template/` |
| A decision | `docs/adr/NNNN-title.md` |
| A fix for anything in the graduation report | `docs/documentation/`, by its own `AGENTS.md` |

The root is an allowlist. A file or folder that is not in the tree cannot be added without changing the allowlist, which is a reviewed change.

## Commands

```bash
make help            # every command, with one line each
make setup           # install the dependencies
make dev             # core stack, models and tiler, with hot reload
make test-fast       # static checks and unit tests
make test-db         # database build, self-checks, row-level-security matrix
make test-integration  # backend against real PostgreSQL and object storage
make test-contract   # API, model and event contracts
make test-e2e        # one scenario through the full stack
make contracts       # regenerate every contract and client
make check           # what CI requires: tests, docs and repository checks
make wt NAME=<branch>  # your own branch and worktree
make wt-pr           # inside the worktree: make check, push, open the pull request
make bench           # CPU latency; a result counts only on the server
```

## Conventions

- Python 3.12 with `uv`. TypeScript with pnpm and Turborepo. Versions are pinned in the lock files.
- Branch names follow `<type>/<scope>-<short-summary>`, as `CONTRIBUTING.md` describes. The commit and the pull request title follow Conventional Commits, for example `fix(db): let a field report trigger the hazard engine`.
- A branch name or commit message never says who or what wrote it. An agent-made pull request carries the label `ai-assisted`, two lines in its description (the tool, and the specification followed), and an `Assisted-by:` trailer.
- A pull request is small: a few hundred changed lines. Bigger work is a series of pull requests, each useful on its own.
- Match the style, naming and comment density of the surrounding code.
- Timestamps are ISO 8601 in UTC. Geometry is WGS 84 (SRID 4326) with distances in metres. Identifiers are lower-case UUIDv7. Money carries its currency.
- An endpoint is defined only in its module's `api.py`. The schema exists only in `database/schema/`.

## Contracts first

- A contract is generated from code and committed as a snapshot. It is never typed twice and never edited by hand. `make contracts` regenerates; `make contracts-check` fails on a stale file.
- A pull request that changes a contract does nothing else.
- Additive changes are free inside a version: a new optional field, endpoint or event type. Consumers ignore what they do not know.
- A breaking change needs a new major version, a decision record, both versions served until every consumer has moved, and a removal date. CI fails on a breaking change inside a version.
- Every error has a stable code. Clients branch on the code, never on the message.
- A model service receives and returns references, never bytes. The job id is the idempotency key. The contract is in `CONTRACTS.md`.

## Tests and the definition of done

- A change that cannot say which tests prove it is not finished. `TESTING.md` §3 lists them for each kind of change.
- Write the test with the code. Never leave it for later.
- Never weaken, skip or delete a test to make a change pass. If a test is wrong, change it and say why in the pull request.
- Never mock the database in an integration test.
- Anything that touches permissions, money, routing or alerts is tested on its failure paths, not only on the happy one.
- A new table fails the row-level-security matrix until its expected row is written.
- No test needs a GPU, a network service or a real credential. Use the tiny models in `fixtures/models/`.

A change is done when all of this is true:

1. It does what its task in `specs/` asks and nothing more. An unrelated problem is reported, not fixed in the same pull request.
2. The tests from `TESTING.md` §3 exist and pass.
3. Every contract it touched is regenerated, and the other side still passes its tests.
4. `make check` passes locally.
5. The documents below are updated in the same pull request.
6. A decision that changed has a new record in `docs/adr/`.
7. The pull request description answers four questions: what changes, why, how it was tested, and what can go wrong and how to undo it.

## Branches and worktrees

- Never work on `main`. Work in a worktree that `make wt` created. Worktrees live in `../rescuevision-wt/<name>`.
- One agent per worktree and one task per worktree. Never touch another worktree.
- Each worktree has its own dependencies, its own Compose project (`rv-<name>`) and its own database name, so two agents can work at the same time.
- Secrets are read from `~/.config/rescuevision/` and are never copied into a worktree.
- `make wt-sync` brings a worktree up to date with `main`. `make wt-pr` runs the complete check first; if it fails, nothing is pushed.
- A person reviews every line and merges. The branch must be current with `main` and all review threads resolved.

## Never

- Commit to `main`, merge your own pull request or approve it.
- Force-push, rewrite the history of a pushed branch, or delete a branch you did not create. Rebasing your own unmerged branch is allowed.
- Deploy to staging or production, or change anything on the server.
- Write a secret, a token or `kaggle.json` into the repository, or print one into a log.
- Weaken a test or a rule to make a change pass.
- Change an `AGENTS.md`, the workflows, `deploy/` or `database/schema/` when the task does not say so.
- Add a GPU dependency, torch or a training framework to `backend/` or to a serving image.
- Put stitching, area-wide analysis, 3D reconstruction or a language model inside a request, or on the server at all for the last two.
- Depend on a feature of one object store. The product uses the S3 API only.
- Import another module's internals, call a model from `api`, or create a table from application code.
- Commit weights, rasters, datasets or notebook outputs. Edit a notebook instead of its script.
- Edit `metrics.json`, `latency.json`, `weights.yaml` or a version folder that already has results. Create a new version.
- Delete a file under `docs/documentation/`, `docs/team-plan/` or `database/erd/mahmoudERD/`. The graduation report and a teammate's diagram are kept with their history.
- Let code confirm a person, close a case, dispatch a team or resolve an alert. Only a person does that.

When the task is unclear, stop and ask in the task or in the pull request. An agent that guesses and builds the wrong thing costs more than one that waits.

## Keep the documents true

A pull request that changes behaviour changes the documents in the same pull request.

| You changed | Update |
| --- | --- |
| A container, a module, a table, a flow or a decision | `ARCHITECTURE.md` |
| An endpoint, an event, a model service or a storage key | The contract, then `make contracts` |
| The schema | A migration, the RLS matrix and the ERD, as `database/AGENTS.md` says |
| A command | The Makefile and every document that names it |
| An operating step | The runbook in `docs/runbooks/`, written as it was executed |
| A model version | The version folder, `ai/training/LEDGER.md` and `ai/registry/` |
| What a folder allows or forbids | That folder's `AGENTS.md` |

- One source per truth. Link to a fact. Never copy it into a second file.
- `make docs-check` fails on a broken link, a `make` command that does not exist, a folder named in this file that does not exist, a table or a container named in `ARCHITECTURE.md` that does not exist, a missing required file, an edited accepted decision record, or a document over its length limit.
- An `AGENTS.md` holds rules, commands, boundaries and the tests a change must bring. It holds no tutorials and no task lists. The root file stays under 170 lines and a folder file under 60.
- If a document and the code disagree and the task does not say which is right, stop and ask. If a document is wrong outside your task, say so in the pull request.
