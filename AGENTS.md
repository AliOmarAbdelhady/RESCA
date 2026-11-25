# AGENTS.md

Read this first. It applies to every AI coding agent and every person working in this repository. Locked: only the owner changes it.

## What RESCA is

RESCA (Real-time Emergency Sensing, Coordination & Assessment) gives police, EMS, fire and government one live picture of a disaster: damage from drone and satellite imagery, people who need help, hazards such as flood water near live power, and safe routes. It is a graduation project held to the standard of a national emergency system. Full picture: [docs/VISION.md](docs/VISION.md).

## System map

```
web (Vite + React) ─┐                          ┌─ ai-damage ─┐
                    ├─ Caddy ── api (FastAPI) ─┤  worker ────┼─ ONNX on CPU, private network
mobile (Expo) ──────┘              │           └─ ai-vision, ai-embed
                     PostgreSQL 18 (PostGIS, pgRouting, pgvector, RLS) + SeaweedFS (S3)
```

REST for commands, SSE for live updates, a Postgres job queue for heavy work, one CPU-only server. Details and the three end-to-end flows: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Why each choice: [docs/DECISIONS.md](docs/DECISIONS.md).

## Where things go

| Folder | What | Read before touching |
|---|---|---|
| `backend/` | FastAPI app and worker (`resca_api`) | [docs/BACKEND.md](docs/BACKEND.md) |
| `frontend/` | web console, Expo app, shared packages | [docs/FRONTEND.md](docs/FRONTEND.md) |
| `database/` | schema, migrations, seeds, self-checks | [docs/DATABASE.md](docs/DATABASE.md) |
| `ai/` | Kaggle experiments, shared ML code, model services | [docs/AI.md](docs/AI.md) |
| `contracts/` | OpenAPI, event and AI-service contracts | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#contracts) |
| `deploy/` | Compose, Caddy, secrets, runbooks | [docs/DEPLOY.md](docs/DEPLOY.md) |
| `docs/documentation/` | the graduation report | [docs/documentation/REPORT_GUIDE.md](docs/documentation/REPORT_GUIDE.md) |
| `docs/archive/` | old research and debate | do not read unless asked |
| `api/`, `scripts/`, `configs/`, `notebooks/`, `dashboard/` | legacy code from before the rebuild | do not extend; replaced by the folders above |
| `mapping/`, `mahmoudERD/` | teammates' prototype evidence | never edit or delete |

Each folder has its own short `AGENTS.md` with its gate and its most-broken rules.

## Every task: before and after

Before you edit:
1. Pull `main` and work on a branch (`<github-user>/<topic>`), never on `main`.
2. Read this file, the folder's `AGENTS.md`, and the area doc. Write a short plan naming the rule IDs and tests you will satisfy.

After you edit, check every item and report each one:
1. No hard-coded colours, sizes or styles; tokens only (W1).
2. No hard-coded user-visible text; English and Arabic keys added together (W3).
3. Reused shared components; nothing copied (W2).
4. No empty `catch`/`except`, no unhandled promise (X1).
5. No N+1 queries; lists paginated; inputs bounded (B9, B3, B2).
6. Every endpoint has allowed and denied authorization tests (B4).
7. Tests added for the changed behaviour; bug fixes have a failing-first test (T1).
8. `make check` passed, or the unrun gates are named.
9. No locked file changed.

## Locked files

Only the owner may change the files in `.github/locked-paths.txt`: all `AGENTS.md` files, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/DEV_WORKFLOW.md`, `docs/RULES_INDEX.md`, `.github/`, `tools/policy/`, the `Makefile`, lint and token configs, and `database/schema/15_security.sql`. CI and a pre-commit hook enforce it. If one of them is wrong, describe the change in your PR text and stop.

## Never

- Push to `main`, force-push a shared branch, or merge your own PR.
- Change architecture, decisions, the workflow, CI, gates or the database security model.
- Add the `owner-approved` label or set `RESCA_LOCKED_CHANGE_APPROVED`.
- Weaken, skip or delete a test; add `eslint-disable`, `noqa` or `type: ignore` to get green (P2).
- Commit secrets, `.env` files, model weights, datasets or notebook outputs.
- Delete or rewrite a teammate's work.
- Show fake data in a screen, or invent results, metrics or citations.
- Let an AI result act without a person confirming it (A6).
- Say something works without having run it (P3).

## Commands

```
make help        list commands
make bootstrap   install git hooks
make check       run every gate (UNRUN lines are gates not built yet)
make check-db    build the schema in a throwaway PostGIS and run its self-checks
```

## Done means

The change does one thing, its gates pass, its tests prove the behaviour, the PR template is filled in (rule IDs, commands run, contract and migration effects, rollback), and nothing above was broken. All rules: [docs/RULES_INDEX.md](docs/RULES_INDEX.md). Git and CI details: [docs/DEV_WORKFLOW.md](docs/DEV_WORKFLOW.md).
