# Git Branching, Worktrees & Release Workflow (`BRANCHING.md`)

A 10/10 repository for six developers and multiple AI coding agents requires a workflow with **minimal merge conflicts, zero broken `main` builds, and strict isolation between concurrent agent tasks**.

---

## 1. Branching Model: Trunk-Based Development (Short-Lived Branches)

* **Verdict:** Use **Trunk-Based Development** (`main` is always deployable; short-lived branches live 1–3 days max) instead of **GitFlow**.
* **Why not GitFlow?** GitFlow's long-lived `develop` + `release/*` + `hotfix/*` branches create massive merge conflicts when 6 developers + AI agents edit `openapi.json`, `packages/api`, and `database/migrations/` concurrently. In a 1-year graduation project, `main` is the single integration trunk; `staging` deploys automatically from `main`, and `production` deploys from immutable Git tags (`v*.*.*`).

### Branch Naming Convention
Every branch must follow `<type>/<scope>-<short-slug>`:
* `feat/<area>-<slug>` — New feature (`feat/api-electrified-water-ws`, `feat/web-damage-layer`, `feat/mobile-offline-queue`)
* `fix/<area>-<slug>` — Bug fix (`fix/db-rls-pool-reset`)
* `ai/<feature>-<version>` — Model training / eval / serving changes (`ai/damage-assessment-v2`)
* `db/<slug>` — Schema migrations & seeds (`db/add-copilot-read-views`)
* `infra/<slug>` — Docker, Caddy, CI/CD, Contabo (`infra/contabo-backup-cron`)
* `docs/<slug>` — Architecture, ADRs, model cards, report (`docs/adr-0004-geo-tiles`)

---

## 2. Branch Protection & PR Rules (`main`)

Configure GitHub Branch Protection / Rulesets on `main`:
1. **No direct pushes to `main`** (including maintainers and AI agents).
2. **Pull Request required** with **at least 1 approving human review** (and `CODEOWNERS` review when touching `database/`, `infra/`, or `ai/eval/`).
3. **Squash-and-merge only** (keeps `main` history linear and every PR revertible in one commit; delete branch automatically on merge).
4. **Required Status Checks before merge:**
   * `lint-and-boundaries` (`ruff`, `mypy`, `import-linter`, `pnpm lint`, `pnpm typecheck`)
   * `db-and-rls` (`./database/build.sh` + `checks.sql` + RLS isolation suite)
   * `contracts-and-unit` (OpenAPI drift check + `pytest` unit + `vitest`)
   * `security-scan` (`gitleaks` secret check + weight-size check)
5. **Up-to-date branch check:** Require branches to be up to date with `main` (or use GitHub Merge Queue) before merging changes that regenerate `frontend/packages/api/src/generated/`.

---

## 3. Commit Convention & Releases

* **Conventional Commits** (enforced via `commitlint` or PR title check on squash-merge):
  * `feat(api): add idempotent hazard ingestion endpoint`
  * `fix(mobile): flush OP-SQLite outbox in FIFO order`
  * `ai(person-detection): export v2 ONNX checkpoint and eval card`
  * `db(schema): add signed MVT tile helper for Martin`
  * `ci(deploy): add Contabo production tag workflow`
* **Releases & Versioning:**
  * **Platform releases:** Semantic Versioning tags (`v0.1.0`, `v0.2.0`, `v1.0.0`) created from `main` after `staging` soak verification. Tagging triggers the production CD pipeline.
  * **AI model versions:** Independent per-feature tags (`ai/damage-assessment/v1`, `ai/person-detection/v2`) matching `kaggle/<feature>/vN/` and `ai_models.version`.

---

## 4. Safe Multi-Agent Workflow (Git Worktrees + Lockstep Contracts)

When multiple AI coding agents work in parallel:
1. **One Task = One Isolated Git Worktree + One Branch:** Agents must work inside dedicated worktrees (e.g., Orca managed worktrees or `git worktree add ../wt-<slug> -b feat/<area>-<slug> main`)—never sharing one dirty working tree.
2. **Never Edit Generated Artifacts by Hand:** If an agent modifies FastAPI schemas (`backend/api/`), it **must** regenerate `frontend/packages/api/src/generated/` (`pnpm generate:api`) inside the same PR—or keep the PR strictly backend-only with an exported `openapi.json` snapshot check.
3. **Additive Database Migrations Only:** After initial v1 freeze, agents never edit old `database/schema/*.sql` history destructively without updating `checks.sql`; schema evolutions go into numbered forward-only `database/migrations/000N_<slug>.sql`.
4. **Notebook Diff Hygiene:** Any commit touching `kaggle/**/*.ipynb` must pass `nbstripout` (strips cell execution outputs & embedded base64 images) so PR diffs remain readable.
5. **Zero Large Binaries:** Pre-commit + CI reject files `> 5 MB` (`.pt`, `.safetensors`, `.onnx`, `.tif`, `.parquet` > 5 MB) so weights never pollute Git history.
