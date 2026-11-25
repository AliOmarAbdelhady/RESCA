# AGENTS.md — RescueVision

**You are an AI coding agent or a new teammate.** This file is the operating contract for this repository.
Read all of it before your first change (about two minutes). Subfolders add rules in their own `AGENTS.md`.
When two files disagree, the one closest to the file you are editing wins, and an accepted decision record
in `docs/adr/` beats both.

**Status:** draft for the Day-0 decision meeting. Rows marked ⚠ are filled in by the decision record named
in the row. The graduation report has its own guide: see section 10.

## 1. Start of every session

1. Run `make doctor`. It fails with instructions if you are on `main`, in a stale worktree, without tools, or without hooks installed. Fix what it reports first.
2. Work in your own worktree on your own branch: **one task, one worktree, one branch, one pull request.**
   Never commit on `main`. `make bootstrap` prepares a fresh worktree.
3. Before changing behaviour, read three things: the task's spec in `specs/`, the decision index at the
   end of this file, and the nested guide for the folder (section 3).
4. If a task contradicts a decision record or section 2, **stop and ask**. Do not re-decide the
   architecture inside a feature task.

## 2. What we are building, and what is never negotiable

RescueVision is a proposed disaster-response platform for four agency types (Government, Police, Emergency
Medical Services (EMS), Fire) and for citizens who request help. Agency staff use the web command console,
Field Responders use the mobile field application, and citizens use the citizen request channel. All three
work on one shared incident.

| ID | Feature (the report's names) | Main users |
|---|---|---|
| F1 | Before/After Damage Assessment and Restoration Cost | Analyst, Commander |
| F2 | 2D/3D Mapping and Rescue Route Planning | Analyst, Commander, Field Responder |
| F3 | Aerial Person Detection under Partial Visibility | Analyst |
| F4 | Multi-Object Person Tracking and Assistance Cases | Analyst, Commander, Field Responder |
| F5 | Compound Hazard Alerts ("Electrified Water") | all staff |
| F6 | General Reports | Analyst, Commander |

The platform is **decision support**. It proposes, ranks and warns; a person decides. **Where it runs:**
the demonstration host is one CPU-only server, for one user at a time. Training runs on free Kaggle or
Colab GPUs; the server runs the application and CPU inference (ONNX Runtime or OpenVINO).

A change that breaks an invariant is wrong even if every test passes:

| # | Invariant | Source |
|---|---|---|
| INV-1 | A person confirms a detection, closes a case, dispatches a team or resolves an alert. AI never does. | D-07 |
| INV-2 | Access is enforced in the database with row-level security. The API only records who is asking, inside the request's transaction. | D-04 |
| INV-3 | One shared incident. An agency sees it only while its participation is `ACTIVE`. | D-01 |
| INV-4 | Heavy analysis runs as a queued job, never inside a user's request. | D-03 |
| INV-5 | Unknown is never shown as safe: an unknown power state counts as energised; stale or missing data is labelled, never filled in. | NFR-SF-02, IR-UI-06 |
| INV-6 | Every AI result records the model version and the inference run that produced it. | FR-IM-07 |
| INV-7 | A published report or cost estimate is a frozen snapshot. | D-06 |
| INV-8 | Coordinates are WGS 84 (`SRID 4326`) and distances are metres on the ellipsoid. | D-09 |
| INV-9 | Docs, comments, tests and the report state only what was run and observed. Proposed behaviour is written as proposed. | team review rule |
| INV-10 | The demonstration needs no GPU, no paid service and no second server: no PyTorch, CUDA, Triton or TensorRT in a deployed image; 3D is drawn in the browser. | owner constraint |

`D-nn`, `FR-*`, `NFR-*` and `IR-*` are the report's identifiers (Section 3.2 and Table 3-39). `INV-n` are ours.

## 3. Repository map

| Path | What it is | Read before editing |
|---|---|---|
| `services/core-api/` | The core backend: one module per information domain | `services/core-api/AGENTS.md` |
| `services/worker/` | Job consumers: stitch, analyze, route, report | `services/worker/AGENTS.md` |
| `services/ai/<family>/` | One AI container per model family, CPU inference (ONNX Runtime or OpenVINO) | `services/ai/AGENTS.md` |
| `ai/` | Training, evaluation and export code (`rescuevision_ai`) | `ai/AGENTS.md` |
| `kaggle/<feature>/vN/` | Versioned training experiments (thin notebooks) | `kaggle/AGENTS.md` |
| `database/` | Schema, migrations, seeds, database tests | `database/AGENTS.md` |
| `contracts/` | The seam between services and clients | `contracts/AGENTS.md` |
| `frontend/` | pnpm + Turborepo: `apps/web`, `apps/mobile`, `packages/*` | `frontend/AGENTS.md` |
| `infra/`, `.github/` | Compose files, edge proxy, deploy scripts, CI workflows | `infra/AGENTS.md` |
| `docs/` | Decisions, runbooks, testing, research, report | `docs/AGENTS.md` |
| `specs/<NNNN-slug>/` | What and why for one feature (spec, plan, tasks) | the folder itself |
| `prototypes/` | Frozen evidence (mapping prototype, legacy code) | `prototypes/AGENTS.md` |

## 4. Boundaries

| Folder | May | Must never |
|---|---|---|
| `services/core-api/`, `services/worker/` | call AI services over HTTP | import a model framework or load weights |
| `services/ai/<family>/` | serve one model bundle on CPU | hold database credentials or write operational tables |
| `ai/`, `kaggle/` | train, evaluate, export | be imported by anything that runs in production |
| `frontend/apps/*` | import `packages/*` | call `fetch` or a native SDK directly (use `packages/api`, `src/services/`) |
| `database/` | SQL only | contain application code |
| `prototypes/` | be read and referenced | be imported, fixed or extended |
| any folder | pass object keys, not file bodies | put datasets, weights, rasters or secrets in Git |

`make check` enforces the import rules. The rest is your responsibility.

## 5. Vocabulary (use exactly these words)

Agencies: Government, Police, Emergency Medical Services (EMS), Fire. Roles: Platform Administrator,
Agency Administrator, Commander, Analyst, Field Responder; Citizen through the citizen channel. A hospital
coordinator is a stakeholder, not a user role. One shared incident; a lead agency invites other agencies; each
agency runs its own missions, assigned to teams or individuals. "Assistance case", "hazard", "compound alert", "response status". Do not introduce a synonym (victim, casualty, operator, coordinator) in code, UI or docs.

## 6. Commands

`make help` lists every target with one line each. These are the ones you need.

| Command | When |
|---|---|
| `make bootstrap` | once per clone or worktree |
| `make doctor` | start of every session |
| `make up` · `make up-ai` · `make down` | run the local stack (CPU only; `up-ai` loads real model bundles) |
| `make db-reset` | rebuild the dev database from migrations and the demo scenario |
| `make gen` | after changing an API, event, enum or agent file (regenerates every derived file) |
| `make check` | before every commit: what CI runs, minus end-to-end |
| `make demo-verify` | before a demonstration: every precomputed artifact is present with the right hash |
| `make test-e2e` · `make test-mobile` | when a flow or a screen changed |
| `make new-ai-service NAME=<family>` | scaffold a new AI container from the template |
| `make new-migration NAME=<slug>` | create a forward migration |

Use `make`, not the underlying tools, unless a nested guide says otherwise. Never pass `--no-verify`. If a target is slow, say so in the pull request instead of skipping it.

## 7. How a change flows

1. **Spec.** Non-trivial work starts from a spec in `specs/` (what, why, acceptance criteria). No spec, no
   code; ask for one.
2. **Contract first.** If the change touches an API, an event, an enum or a table, the contract changes in
   the same pull request (or in an earlier one) and `make gen` is run. Clients are generated, never written.
3. **Small steps.** One vertical slice, a test first where practical, commit often. One pull request solves
   one concern: target 400 changed lines or fewer, not counting generated or moved files.
4. **Verify.** Run `make check`. It must pass on the commit you push. If you cannot run it, say so in the
   pull request; do not describe untested work as done.
5. **Pull request.** Title in Conventional Commits form. Fill the template, including "Requirement IDs"
   and "Evidence". Request a human review.

## 8. Testing rules and Definition of Done

Tests prove the invariants first. Each of INV-1 to INV-8 has a named test that `database/` or `services/`
owns; find them with `make trace`. A new behaviour needs a test that fails without it. A bug fix needs a
regression test. Tag tests with the requirement they prove (`pytest.mark.req("NFR-PF-04")`, Playwright `@req`).

Real services, not mocks, for anything spatial or secure: tests run against the project's own PostgreSQL
image with PostGIS, pgRouting and pgvector. SQLite and an in-memory fake are not substitutes for a schema test.

A pull request is **done** only when all of these hold:

1. It matches its spec and no accepted decision record, or it supersedes that record itself.
2. `make check` passes on the pushed commit and the required CI check is green.
3. Tests were added as above and requirement IDs are tagged.
4. Contract files are regenerated and committed; a breaking change is marked `!` in the title.
5. The matching document, runbook or decision record is updated, or the pull request says why not.
6. Unfinished parts fail loudly (`501 Not Implemented`, an "unavailable" state in the UI), never silently
   return a placeholder.
7. A human approved it. An agent's review of its own work does not count.

## 9. Never

- Commit to `main`, force-push a shared branch, or work in a worktree someone else is using.
- Run inference or stitching inside an API request handler, or put photogrammetry, an area-wide analysis or
  an embedding build on the request path: these are precomputed ahead of a demonstration.
- Query the database as the owner or a superuser, skip `app.set_session_user()`, or add a table without
  row-level security policies for all four roles.
- Edit a migration that has been merged, or make a destructive change without an expand and contract plan.
- Hand-edit a generated file (`**/generated/`, `contracts/openapi/*.json`, the block between the
  `generated:` markers below).
- Present a proposed capability as working, in code, UI, docs or the report.
- Add a dependency without pinning it and recording why in the pull request.
- Commit secrets, `.env`, datasets, weights (`.pt`, `.onnx`, `.safetensors`), rasters, or a notebook with
  outputs or credentials.
- Edit agent configuration (`.claude/`, `.zcode/`, `.gemini/`, `.agents/`, `.cursor/`) or `CODEOWNERS`
  without a human owner's approval in the pull request.
- Copy code from `prototypes/` into `services/` or `frontend/` to save time.

## 10. The graduation report (a second track in the same repository)

The Project I report lives in `docs/documentation/` and `docs/team-plan/`. It has different rules (Word build,
IEEE citations, "proposed" wording, evidence before claims). **Before editing anything under those two
folders, read `docs/documentation/AGENTS.md`.** If a build change makes a statement in the report untrue, add
a row to the editorial tracker in `docs/team-plan/review/` in the same pull request.

## 11. Keeping this file true

- This file is for what cannot be found by reading the code. A rule a checker can verify belongs in a checker.
- When an agent makes a mistake that a rule would have prevented, fix the rule or add the check in the same
  pull request. When a rule is wrong, change it; do not work around it.
- Keep this file under 200 lines and each nested `AGENTS.md` under 80. `make gen` refreshes the decision index
  and the tool copies (`CLAUDE.md`, `GEMINI.md`); `make check` fails if they are stale. A decision changes
  only through a new decision record (`docs/adr/README.md`).

## Decision index

<!-- generated: decisions:start (source: docs/adr/README.md, refreshed by `make gen`) -->

| ADR | Decision | Status |
|---|---|---|
| 0001 | One repository, contract-first | proposed |
| 0002 | Core backend language and framework ⚠ | proposed |
| 0003 | AI serving: CPU inference, one container per model family, behind an HTTP API | proposed |
| 0004 | Job queue and live-update transport ⚠ | proposed |
| 0005 | Object storage: the S3 API is the contract; MinIO is not a candidate | proposed |
| 0006 | Map engine and tile serving ⚠ | proposed |
| 0007 | Offline synchronisation protocol ⚠ | proposed |
| 0008 | Migrations are plain, forward-only SQL | proposed |
| 0009 | `AGENTS.md` is the single agent guide | proposed |
| 0010 | `main` is protected; one required check; squash merges only | proposed |

<!-- generated: decisions:end -->
