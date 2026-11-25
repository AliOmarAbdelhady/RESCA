# REPO_CLEANUP.md — every current path: keep, move, archive or delete

Part of the Engineering Specialist F blueprint (`docs/architecture/debate/eng_specialist_glm/`).
Nothing in this table has been done. Every row is a recommendation with its reason.

## 1. What is never deleted

The task for this blueprint names three paths that must be preserved or moved, never deleted. They
are kept, and they are kept with their history (`git mv`, so `git log --follow` still works).

| Path | What it is | What happens to it |
|---|---|---|
| `mahmoudERD/` | Mahmoud's draw.io ERD of the schema: 56 tables, 140 foreign keys, 9 subject areas, 11 page exports, and its own generator that parses the SQL | moved to `docs/database/mahmoud-erd/`, whole, with his README |
| `mapping/` | the Chapter 4 prototype: Kahramanmaraş before and after maps from Maxar imagery, the evidence for Figures 4-1 to 4-6 | moved to `prototypes/mapping/`, whole |
| `docs/documentation/` | the graduation report: Skeleton and Main Word exports, their editable sources, the builder | kept exactly where it is |

Two other proposals in the debate merge `mahmoudERD/` into another diagram and retire `mapping/`
from the repository. This blueprint does not: a teammate's contribution is not a duplicate to be
pruned, and the report cites these files by name.

The same protection applies to `docs/team-plan/`, `docs/brand/`, `database/`, the 27 Kaggle
notebooks and `docs/architecture/` (the debate itself, which the report's design rationale can
cite). The only deletions in the whole plan are two untracked scratch items.

## 2. The table

Verdicts: **keep** (stays, maybe edited) · **move** (`git mv` to the target) · **add** (does not
exist yet) · **replace** (same path, new content; old content kept elsewhere) · **delete**.

### 2.1 Root

| Current path | Verdict | Target | Reason |
|---|---|---|---|
| `AGENTS.md` | replace | report rules → `docs/documentation/AGENTS.md` (verbatim); new root file from [`AGENTS.md`](AGENTS.md) | it is a guide for editing the report and says nothing about building software; every agent reads it first |
| `README.md` | replace | same path, rewritten; its safety disclaimer goes to `VISION.md` and `SECURITY.md` | it documents a `src/rescuevision` package and commands that have not worked since commit `f89a61f` (21 October 2026) |
| `LICENSE` | add | `/LICENSE` | `pyproject.toml` and the README say MIT; there is no licence file, and GitHub reports none for this public repository |
| `Dockerfile` | move | `prototypes/legacy-ml/Dockerfile` | builds the deleted package; its start command needs `uvicorn`, which `requirements.txt` does not list |
| `docker-compose.yml` | move | `prototypes/legacy-ml/docker-compose.yml` | two services (the dead API and the old dashboard); new files under `infra/compose/` |
| `pyproject.toml` | move | `prototypes/legacy-ml/pyproject.toml`; a new root file is the `uv` workspace root | `packages.find where = ["src"]` and there is no `src/` on `main` |
| `requirements.txt` | move | `prototypes/legacy-ml/requirements.txt` | mixes training, serving and test dependencies with lower bounds only |
| `.env.example` | keep | same path, extended | add Compose project name, object store, environment name; still no secrets |
| `.gitignore` | keep | same path, edited | see section 3 |
| `opencode.json` | keep | same path | one model preference for one tool. Owner decides whether the team shares it; otherwise it moves to untracked local configuration |
| `_erd_viewer.html` | delete | — | **untracked** scratch viewer for the generated ERD. Nothing in Git is lost; `docs/database/erd-overview.html` already exists |
| `Makefile`, `mise.toml`, `.pre-commit-config.yaml`, `.gitattributes`, `.editorconfig`, `.dockerignore`, `.worktreeinclude` | add | root | DEV_ENV.md |
| `VISION.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CLAUDE.md`, `GEMINI.md` | add | root | DOCS_SYSTEM.md; the last two are generated |
| `.devcontainer/` | add | root | DEV_ENV.md, section 10 |
| `.github/` | add | root | BRANCHING.md, CI_CD.md: workflows, `CODEOWNERS`, pull request and issue templates, `dependabot.yml` |

### 2.2 Code that no longer runs

Eleven Python files on `main` import `rescuevision.*` in 45 module-level statements (`git grep`).
The package was deleted in `f89a61f`. None of these files can start today.

| Current path | Verdict | Target | Reason |
|---|---|---|---|
| `api/` (9 files) | move | `prototypes/legacy-ml/api/` | the old single-analyst prototype; no authentication, synchronous inference in the request, `allow_origins=["*"]` |
| `scripts/` (11 files) | move | `prototypes/legacy-ml/scripts/` | dataset preparation and training entry points for the deleted package; `setup_env.sh` is replaced by `make bootstrap` |
| `configs/` (12 YAML files) | move | `prototypes/legacy-ml/configs/` | the four-model cascade; its `device: "cuda"` default has no CPU path |
| `notebooks/01…07_*.ipynb` (7 files) | move | `prototypes/legacy-ml/notebooks/` | tutorials for the same cascade; zero saved outputs |
| `dashboard/` (18 files) | move | `prototypes/dashboard/` | the legacy Vite app. Person 6's plan lists its components as possible report evidence (item P-6) and `frontend/apps/web/README.md` says components are ported from it, so it is kept, frozen |
| `prototypes/README.md`, `prototypes/AGENTS.md` | add | `prototypes/` | says what each prototype is evidence of and that nothing in it is imported or fixed |

Deleting these instead would lose nothing that Git history does not hold. They are moved rather
than deleted for two reasons: the report may still cite them, and a frozen folder with a loud
README is safer for agents than code that vanished and left dangling references in the frontend
READMEs.

### 2.3 AI training

| Current path | Verdict | Target | Reason |
|---|---|---|---|
| `notebooks/kaggle/*.ipynb` (27 files) | move | `kaggle/building-damage/v1`, `v2`, `v3` and `kaggle/flood-road-segmentation/v1`, by the mapping in REPO_TREE.md, section 6.2 | the team's real experiment history; today all 27 clone an unpinned repository and import the deleted package |
| `notebooks/kaggle/v4/*` (on `codex/building-damage-v4`) | move | `kaggle/building-damage/v4/` | already thin wrappers over a package pinned by commit |
| `src/rescuevision/v4/`, `tests/v4/`, `configs/v4/`, `scripts/v4_*.py` (same branch) | move | `ai/` (`src/rescuevision_ai/core`, `tasks/building_damage`, `tests`, `ai/datasets/registry.yaml`) | the most mature engineering in the repository; merge the branch first (it is 24 commits ahead and 28 behind `main`) |
| `ai/`, `kaggle/` | add | root | REPO_TREE.md, section 6 |
| `docs/model_cards.md` | keep, then supersede | same path until the Project I report is submitted; then `docs/ai/model-cards/` takes over | it describes nine models, none trained; the review flags "configured" being read as "trained" |
| `docs/experiments.md` | keep | same path until the report is submitted | the honest record that all 11 experiments are pending; cited by Person 6's plan and two review documents |
| `docs/dataset_setup.md` | keep, then supersede | then `ai/datasets/README.md` | its commands call the deleted scripts |

### 2.4 Database, contracts, infrastructure

| Current path | Verdict | Target | Reason |
|---|---|---|---|
| `database/schema/*.sql` (16 files), `seed/`, `tests/checks.sql`, `tools/`, `README.md`, `build.sh` | keep | same paths; `schema/` becomes the frozen baseline | the best asset in the repository: 2,911 lines of schema, seed and self-checks |
| `database/migrations/`, `database/Dockerfile`, `database/AGENTS.md`, `database/tests/rls/`, `database/tests/safety/` | add | `database/` | CONTRACTS.md, CI_CD.md |
| `database/README.md` | keep | same path, two edits | "AI / Celery pipeline" describes a queue the design does not use; the default port stays 55432 |
| `docs/database/` | keep | same path, plus `mahmoud-erd/` | the generated ERD and its overview page |
| `mahmoudERD/` (16 files) | move | `docs/database/mahmoud-erd/` | section 1. Its README's regenerate command gets the new path. Confirm with Mahmoud first: it is his contribution, merged in pull request #1 |
| `contracts/` | add | root | CONTRACTS.md |
| `infra/` | add | root | CI_CD.md, section 10: Compose for a CPU-only Contabo server, with SeaweedFS as the object store (MinIO's repository is archived) and no GPU image |
| `infra/demo/manifest.yaml`, `tools/demo_check.py` | add | `infra/`, `tools/` | the precomputed artifacts a single-user demonstration needs, checked by hash |
| `services/`, `tools/`, `specs/`, `.specify/` | add | root | REPO_TREE.md |

### 2.5 Frontend

| Current path | Verdict | Target | Reason |
|---|---|---|---|
| `frontend/` (pnpm workspace, `turbo.json`, `apps/web`, `apps/mobile`, `packages/*`, `tooling/`) | keep | same path | the right skeleton: 23 README files and 6 configuration files, no code yet |
| `frontend/README.md` | keep | same path, edited | it links to `docs/FRONTEND_ARCHITECTURE.md`, which does not exist; replace the link with `frontend/AGENTS.md` and a real architecture note |
| `frontend/packages/api/README.md`, `frontend/tooling/README.md` | keep | same path, edited | the contract pipeline is right; the example command `uvicorn api.main:app` refers to the dead API |
| 14 feature `README.md` files under `frontend/apps/*/src/features/` | keep | same paths, rewritten when each feature starts | they describe the old single-analyst tool (roles `COMMANDER / ANALYST / RESPONDER`, "victim" events) and contradict the report's vocabulary |
| `frontend/.npmrc`, `frontend/.gitignore`, `frontend/.env.example`, `frontend/package.json` | keep | same paths | already correct for an Expo monorepo; generated API types are committed |

### 2.6 Documentation

| Current path | Verdict | Target | Reason |
|---|---|---|---|
| `docs/documentation/` | keep | same path, plus `AGENTS.md` | the report; `.gitignore` has six rules tied to these exact paths |
| `docs/team-plan/` | keep | same path | ownership, plans and the review; fix five `mapping/` paths in `person6_plan.md` after the move |
| `docs/architecture/` (untracked today) | keep, then extend | same path; add `repository-layout.md`; the debate stays as evidence | three proposals, two red-team reviews and the specialist reports are the "alternatives considered" for the report |
| `docs/adr/` | add | `docs/` | DOCS_SYSTEM.md, section 3 |
| `docs/README.md`, `docs/AGENTS.md`, `docs/guides/`, `docs/testing.md`, `docs/requirements/`, `docs/ai/`, `docs/runbooks/` | add | `docs/` | DOCS_SYSTEM.md |
| `docs/superpowers/specs/` | keep | same path | the approved ERD design; linked from `database/README.md` and the review index |
| `docs/research_papers.md`, `docs/tier1_papers_summary.md`, `docs/limitations_and_ethics.md` | keep, then move | in phase 2 to `docs/research/` | used by the report's authors now: all three are cited from `docs/team-plan/review/`, and the first two also from the root `AGENTS.md` |
| `docs/claude_view.md`, `docs/PROJECT_ANALYSIS.md`, `docs/graduation_project_research_plan.md`, `docs/SAR_Drone_Simulation_Research.md` | move (phase 2) | `docs/research/`, each with a status banner | research notes that contradict the decisions: two simulators, two backends, "a complete product, not a prototype" |
| `docs/api_usage.md` | move | `prototypes/legacy-ml/docs/` | documents seven endpoints of the API that no longer starts |
| `docs/brand/` (102 files) | keep | same path | the identity pack; the app icons are needed by web and mobile. Its 13 MB `.pcraft` sources stay: history already contains them, and removing them from `main` would not shrink a clone |
| `docs/archive/` | add | `docs/` | superseded documents, with a banner |

### 2.7 Agent configuration

| Current path | Verdict | Target | Reason |
|---|---|---|---|
| `.agents/skills/`, `.gemini/skills/` (empty) | keep | `.agents/skills/` is the canonical skills folder | the directories already exist and are what ZCode and Antigravity scan |
| `.claude/launch.json` | keep | same path, edited after the move | it serves `mapping/output` on port 8000; the path becomes `prototypes/mapping/output` |
| `.gemini/settings.json`, `.zcode/config.json`, `.claude/settings.json`, `.claude/skills/` | add | root | AGENT_FILES.md, section 3.1 |

## 3. `.gitignore`: what changes

| Change | Why |
|---|---|
| replace the six `mapping/...` rules with `prototypes/mapping/...` | the folder moves |
| add `*.onnx`, `*.pte`, `*.ckpt`, `*.plan` to the weights rules | the current list stops at `.pt`, `.pth`, `.bin`, `.safetensors` |
| add `.claude/worktrees/` | Claude Code's own recommendation for its worktree folder |
| add `CLAUDE.local.md`, `AGENTS.override.md` | personal agent overrides are never committed |
| add `infra/secrets/*.env` while keeping `!infra/secrets/*.enc.env` | plaintext secrets never land; encrypted ones do |
| keep every report rule exactly as it is | the negations are tied to the report's paths |
| leave `kaggle.json` in place, and never name a project file `kaggle.json` | it is the Kaggle credential; a file of that name anywhere, including inside `kaggle/`, is silently ignored |

## 4. Order of work: three phases

### Phase 0 — Day 0, before the first agent runs (add, plus two replacements)

1. `git tag pre-rebuild-2026-11-26` on `main`. Everything below can be found from this tag.
2. Merge `codex/building-damage-v4` through a pull request, or decide its fate explicitly.
3. Add `.github/` with the minimal `ci.yml` (`changes`, `guard`, `ci-ok`), `CODEOWNERS`, the pull
   request template; add the ruleset on `main`.
4. Add `Makefile`, `mise.toml`, `.pre-commit-config.yaml`, `.gitattributes`, `.editorconfig`,
   `.dockerignore`, `.worktreeinclude`, `LICENSE`.
5. Add `contracts/`, `infra/`, `tools/`, `services/`, `ai/`, `kaggle/`, `specs/`, `.specify/`,
   `docs/adr/` with the first ten records in `proposed`.
6. Move the root `AGENTS.md` to `docs/documentation/AGENTS.md` unchanged; install the new root
   `AGENTS.md` and its nested files; generate `CLAUDE.md`, `GEMINI.md`, the settings stubs.
7. Rewrite `README.md`.
8. Run the Day-0 decision meeting; set each record to `accepted`; fill the ⚠ rows.
9. Protect `main`; turn on the repository security settings.

Nothing existing is removed in this phase, so it can be done in small pull requests on the first
morning while the report work continues undisturbed.

### Phase 1 — Day 1 to Day 2: one "move" pull request per group

| Pull request | Moves | Links to fix |
|---|---|---|
| `chore(repo): move legacy prototypes out of the root` | `api/`, `scripts/`, `configs/`, `notebooks/01…07`, root `Dockerfile`, `docker-compose.yml`, `pyproject.toml`, `requirements.txt`, `docs/api_usage.md` → `prototypes/legacy-ml/`; `dashboard/` → `prototypes/dashboard/` | `frontend/packages/api/README.md`, `frontend/tooling/README.md` |
| `chore(repo): move the mapping prototype` | `mapping/` → `prototypes/mapping/` | `.gitignore`, `.claude/launch.json`, `docs/team-plan/person6_plan.md`, any `AGENTS.md` link |
| `chore(repo): file the Kaggle notebooks under kaggle/` | the 27 notebooks, by the mapping table | none (nothing links to them) |
| `docs(db): file Mahmoud's ERD with the database documents` | `mahmoudERD/` → `docs/database/mahmoud-erd/` | its README command, `docs/database/` index |
| `chore(ai): fold the V4 package into ai/` | `src/rescuevision/v4`, `tests/v4`, `configs/v4` → `ai/` | the V4 notebooks' import lines |

Each is one `git mv` per file, with no other change, so the reviewer sees only renames. After each
merge: `make docs-check` (no broken link) and `make doctor` in every open worktree.

### Phase 2 — after the Project I report is submitted

1. Move the research notes into `docs/research/` with status banners; fix the links in
   `docs/team-plan/review/` and the root `AGENTS.md`.
2. Archive what the decision records supersede, under `docs/archive/`.
3. Delete directories left empty by the moves (Git does not track empty directories, so this is a
   local `rmdir`).
4. Retire `docs/model_cards.md`, `docs/experiments.md` and `docs/dataset_setup.md` in favour of
   `docs/ai/` once real evaluations exist.

Phase 2 waits for the report because three of those files are cited by the report's review
documents today, and a link that breaks during submission week costs more than a tidy folder.

## 5. Rules for whoever executes the plan

- `git mv`, never delete-and-add. Confirm with `git log --follow <new path> | head`.
- One group per pull request, renames only. A rename mixed with an edit hides both from review.
- Every pull request ends with the link check green and a note of the links it fixed.
- Nothing tracked is deleted. If a row seems to call for it, the file goes to `prototypes/` or
  `docs/archive/` instead.
- A teammate's folder (`mahmoudERD/`) moves only after that teammate has been told.
- The tag from phase 0 stays forever. It is how the report can cite the state of the repository
  at the start of the build.

## Sources

Checked on 25 November 2026 against the repository at `main` (`c947db4`) and the unmerged branch
`codex/building-damage-v4`.

- `git ls-files`, `git grep`, `git log`, `git count-objects`, `gh api repos/AliOmarAbdelhady/RescueVision`.
- Dead imports: `git grep -E '^(from|import) rescuevision' -- '*.py'` → 45 statements in 11 files.
- Notebook outputs: a JSON parse of all 34 notebooks → zero saved outputs.
- Report references to the protected folders: `docs/team-plan/person6_plan.md` (items P-1 to P-8),
  `docs/team-plan/review/README.md`, `docs/documentation/chapter5/section_3_3.md`.
- `docs/architecture/debate/`: `gemini_proposal/REPO_CLEANUP.md` and `redteam_gemini/REPO_CLEANUP.md`
  (the two proposals this table disagrees with on `mahmoudERD/` and `mapping/`).
