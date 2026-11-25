# RescueVision — Git Branching, Worktrees & Release Workflow (`BRANCHING.md`)

> **Goal:** A friction-free Git workflow built for **6 engineers working concurrently alongside multiple AI coding agents**. Zero long-lived integration branches, strict automated guardrails on `main`, and safe parallel worktree isolation.

---

## 1. Branching Model: Short-Lived Trunk-Based Development (GitHub Flow)

We **explicitly reject GitFlow** (`develop`, `release/*`, `hotfix/*`). For a 6-person team + AI agents shipping across 1 academic year, long-lived `develop` branches create massive merge conflicts across `contracts/`, `database/schema/`, and `frontend/packages/api`.

Instead, **all work merges directly into `main` via short-lived PRs (< 48h lifespan)**:

| Branch Type | Naming Convention | Lifetime | Target |
|---|---|---|---|
| **Production Trunk** | `main` | Permanent | Always green, deployable to staging/production. **Direct pushes forbidden.** |
| **Feature / Slice** | `feat/<area>-<short-slug>` (e.g., `feat/api-hazard-engine`) | 1–3 days | `main` |
| **Bugfix** | `fix/<area>-<short-slug>` (e.g., `fix/sql-rls-42501`) | Hours–2 days | `main` |
| **AI Experiment / Model Promotion** | `ai/<feature>-<vN>-<slug>` (e.g., `ai/damage-assessment-v2-rescuenet`) | 1–5 days | `main` |
| **Architecture / Docs / ADR** | `docs/<short-slug>` (e.g., `docs/adr-0009-contabo`) | Hours–1 day | `main` |
| **Infra / CI** | `infra/<short-slug>` (e.g., `infra/ci-triton-gate`) | 1–2 days | `main` |

---

## 2. Branch Protection & PR Rules on `main`

Configure GitHub Branch Protection / Rulesets on `main`:
1. **Require Pull Request before merging** (no direct pushes, not even admins/leads).
2. **Require status checks to pass** before merge:
   - `ci-fast` (ruff, mypy, `import-linter`, `sqlfluff`, pnpm lint/typecheck, `make gen-contracts` zero-diff check, unit tests).
   - `ci-db-integration` (PG 18 PGDG build + `checks.sql` + multi-agency RLS matrix + `evaluate_hazard_rules()` lock tests).
   - `ci-security` (`gitleaks` secrets scan + `trivy` dependency/Docker scan).
   - `ci-ai-gate` (required whenever `ai/`, `kaggle/`, or `triton-repo/` changes).
3. **Require linear history via Squash Merge:** Keeps `main` clean (1 logical Conventional Commit per PR) and makes `git bisect` / rollbacks effortless.
4. **Approvals & CODEOWNERS:**
   - Standard PRs: **1 approving review** (cannot self-approve own PR or an AI agent PR without human/peer verification).
   - High-risk paths (`database/schema/**`, `database/migrations/**`, `infra/**`, `contracts/**`, `triton-repo/**`): require review from designated **Security/DB/AI track owner** via `.github/CODEOWNERS`.
5. **Auto-delete head branches** on merge.

---

## 3. Commit Conventions, Versioning & Releases

### 3.1 Conventional Commits (Required on PR Titles & Squash Merges)
Format: `<type>(<scope>): <imperative summary>`

Allowed types: `feat`, `fix`, `ai`, `perf`, `refactor`, `test`, `docs`, `ci`, `infra`, `chore`.
Allowed scopes: `db`, `api`, `worker`, `web`, `mobile`, `citizen`, `edge`, `ai`, `kaggle`, `triton`, `contracts`, `infra`, `docs`.

Examples:
- `fix(db): convert evaluate_hazard_rules to SECURITY DEFINER with advisory lock`
- `feat(web): add 4D incident time-travel scrubber on MapLibre canvas`
- `ai(damage-assessment): promote v2 SiameseUNetSE trained on xBD+RescueNet`

### 3.2 Semantic Versioning & Release Tagging
- **App / Platform Releases:** Automated by **`release-please`** from Conventional Commits on `main` (`v0.1.0` Milestone 1 → `v0.2.0` Offline Field → `v1.0.0` Defense Release). Every tag builds immutable container images pushed to **GHCR (`ghcr.io/<org>/rescuevision-*:<semver>`)**.
- **AI Model Versions (Independent Cadence):** Tracked per feature via `kaggle/<feature>/vN/` and `triton-repo/<model>/<int_version>/`, mapped in PostgreSQL `ai_models`. Model iteration never blocks platform semver releases.

---

## 4. How AI Coding Agents Work Safely on Branches & Worktrees

When 6 developers launch multiple AI coding agents concurrently (Claude Code, Codex, Gemini, Cursor, Orca workers), collisions happen unless strict isolation rules are enforced:

1. **One Task = One Isolated Git Worktree:**
   - Never run two AI agents in the same checkout directory.
   - Always spawn each agent inside its own worktree and branch:
     ```bash
     git worktree add ../wt/feat-st-asmvt -b feat/api-st-asmvt origin/main
     ```
2. **Strict Path Ownership per Agent Prompt:**
   - Every agent prompt must declare its **allowed write scope** (e.g., *"only touch `backend/src/rescuevision/domains/hazards_routing/` and `backend/tests/`"*) and respect `AGENTS.md` SWE vs. AI boundaries.
3. **Contract Regeneration Discipline:**
   - If an agent modifies FastAPI endpoints/schemas in `backend/`, it MUST run `make gen-contracts` in the **same PR** so `contracts/openapi/openapi.json` and `frontend/packages/api` stay atomic.
   - Frontend agents NEVER hand-edit `frontend/packages/api`; if a backend endpoint does not exist yet, wait for the backend PR or branch from it.
4. **Migration Ordering Guard:**
   - Never reuse or edit an already-merged `database/migrations/*.sql` timestamp file. Always create a new timestamped forward migration, and verify `make db-migrate && make db-check` after rebasing onto `main`.
5. **Pre-PR Mandatory Agent Self-Check:**
   - Rebase onto `origin/main` (`git fetch origin && git rebase origin/main`).
   - Run local CI parity (`make check-fast`) before opening a PR.
   - Never commit `.env`, datasets, `.onnx`/`.pt` weights, or debug artifacts.
