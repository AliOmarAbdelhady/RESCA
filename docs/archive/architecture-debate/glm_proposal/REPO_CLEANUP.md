# Repository clean-up: what to keep, move, archive or delete

*Draft blueprint. It lists every path in the repository today and gives a verdict. **Nothing has been deleted or edited.** These are recommendations to apply through reviewed pull requests.*

The project has not started, so most of the code in the repository today is research or a prototype. That is normal and not a finding. The question here is only: once the whole application is built in this repository, what belongs where?

## 1. Verdicts

"Move" means `git mv`, so that the history follows the file. "Archive" means: give the current state a tag (for example `archive/prototype-api`) so that it stays reachable in Git, and then remove it from `main`. Only prototypes get the second treatment. The report and diagram material in the first table of §1 is never removed from `main` at all.

### Material that is never deleted

Four folders are kept, with their history, whatever else is cleaned up. The owner confirmed this on 2026-11-25.

| Path | What it is | Verdict | Target |
| --- | --- | --- | --- |
| `mahmoudERD/` | A teammate's ERD of the schema: a draw.io file, a PDF, 11 PNG pages and its own generator (about 17 MB, all tracked) | **Move with history** | `database/erd/mahmoudERD/` |
| `mapping/` | Prototype evidence for Chapter 4 of the graduation report, and the scripts that regenerate it | **Move with history** | `docs/documentation/evidence/mapping/` |
| `docs/documentation/` | The graduation report: the two Word snapshots, their source packages, the chapter sources and tools (119 tracked files) | **Keep in place** | Same path |
| `docs/team-plan/` | The report work plan, figures and review notes | **Keep in place** | Same path |

Rules for these four:

- **Move only with `git mv`, in a pull request that changes nothing else.** Git then records a pure rename and `git log --follow` keeps working. Never copy the files and delete the originals.
- **A pull request that deletes a file under one of these paths fails `make repo-check`.** The paths are on a protected list in `rv_tools/repo_check.py`. Replacing a file's content, such as a new Word export, is not a deletion.
- **A history rewrite must leave them untouched.** If the owner rewrites the history to drop the brand binaries (§3), the filter names `docs/brand/` only, and the first check afterwards is `git log --follow` on one file from each of the four folders.

Why the two report folders stay where they are, and are not tidied into a new `docs/report/`:

- Six rules in `.gitignore` are anchored to the exact path `docs/documentation/` (`/docs/documentation/skeleton/*` and its two exceptions, the same for `main/`). After a move they would stop matching, and every local Word export that is ignored today would show up as a file to commit.
- `git mv` carries tracked files only. In every other clone on the team, the ignored local exports would stay behind in the old folder after the pull.
- The chapter tools, the team plan and the review notes link to these paths, and six people are editing the report now.

Why the other two move:

- `mahmoudERD/` at the root would break the root allowlist in `REPO_TREE.md` §3. Inside `database/erd/` it sits next to the generated diagram, as a kept deliverable with its own generator. Its scripts take the schema and output paths as arguments, so only the regenerate command in its README changes.
- `mapping/` is report evidence, not product code, so it belongs with the report. Its scripts build their paths from their own location, so they work unchanged. The pull request updates the six `mapping/` lines in `.gitignore` and the paths in its README, and whoever holds the ignored rasters and page images moves them by hand.

### Root files

| Path | Verdict | Target | Reason |
| --- | --- | --- | --- |
| `AGENTS.md` | **Move and replace** | Current content → `docs/documentation/AGENTS.md` by `git mv`, so its history stays; then a new root `AGENTS.md` | The current file tells an agent how to edit the graduation report. The root file must tell an agent how to build the system. The report rules stay with the report, where they apply. |
| `README.md` | **Rewrite** | New `README.md`; the old text → `docs/research/prototype-readme.md` | The current text describes the 2026 prototype pipeline. A reader must find the product and a five-minute start. |
| `.env.example` | **Rewrite** | Same path | It lists the prototype's variables. |
| `.gitignore` | **Keep and extend** | Same path | Good rules exist for checkpoints, rasters and secrets. Add every exported model format (`.onnx`, `.gguf`, `.tflite`, `.ort`, OpenVINO IR) and the new generated folders. Re-anchor the six `mapping/` lines when that folder moves. Leave the `docs/documentation/` rules as they are. |
| `pyproject.toml`, `requirements.txt` | **Move** | `backend/pyproject.toml` and `ai/pyproject.toml` | The application and the AI side have different dependencies. The root has none. |
| `Dockerfile` | **Archive, then delete** | `backend/Dockerfile`, `database/Dockerfile`, `frontend/apps/*/Dockerfile`, `ai/services/*/Dockerfile` | One Dockerfile per buildable unit, next to its code. |
| `docker-compose.yml` | **Archive, then delete** | `deploy/compose/` | The Compose files describe the whole platform and are reviewed in Git. |
| `.claude/launch.json` | **Delete** | — | A local launch configuration for the mapping server. It is not part of the product. |
| `opencode.json` (not tracked) | **Keep as it is** | — | A local tool setting. It is already ignored. |
| `_erd_viewer.html` (not tracked) | **Delete** | — | A generated viewer; `database/erd/` replaces it. |
| `LICENSE` | **Add** | `LICENSE` | The package metadata says MIT, but there is no licence file at the root. The owner decides the licence. |

### Code and prototypes

| Path | Verdict | Target | Reason |
| --- | --- | --- | --- |
| `api/` | **Archive, then delete** | Tag `archive/prototype-api` | A prototype. Its endpoints are a useful list of what the product needs, which goes into the specifications. |
| `dashboard/` | **Archive, then delete** | Tag `archive/prototype-dashboard` | The console replaces it. |
| `scripts/train_*.py`, `scripts/prepare_*.py` | **Move** | The matching `ai/training/<feature>/…` folders, shared parts into `ai/libs/modelkit/` | These are the scripts behind the notebooks. |
| `scripts/build_retrieval_index.py`, `scripts/run_inference.py`, `scripts/export_report.py` | **Archive, then delete** | With the prototype | They belong to the prototype's file-based pipeline. |
| `scripts/setup_env.sh` | **Delete** | `make setup` | One entry point for commands replaces a script. It names `mapping/`, which moves. |
| `configs/` | **Move** | The matching version folders as the first `config.yaml` | They are the first configurations of each model. |
| `notebooks/` | **Move** | See the mapping in `AI_TRAINING_LAYOUT.md` §11 | Real research history. The Kaggle notebooks already carry version prefixes (`rv_`, `rv2_`, `rv3_`) that map onto versions. |
| `frontend/` | **Keep** | Same path | The layout is the plan: two apps and four packages. Add the code, a third app (`apps/citizen`), and the files the READMEs already promise. |
| `database/` | **Keep** | Same path, plus `migrations/`, `Dockerfile`, `erd/` | It is the approved design and it works. |

### Documentation

| Path | Verdict | Target | Reason |
| --- | --- | --- | --- |
| `docs/brand/` | **Move out of Git** | A separate brand repository or release assets; only the optimised files that the apps use → `frontend/packages/ui/assets/brand/` | About 100 MB of design sources and exports. Every clone pays for them. |
| `docs/documentation/`, `docs/team-plan/` | **Keep in place** | Same path | See the first table of §1. |
| `docs/superpowers/specs/…database-erd-design.md` | **Move** | `docs/architecture/database-erd-design.md` | It is an architecture document, not report material. |
| `docs/superpowers/` (after that) | **Delete** | — | Empty. |
| `docs/database/` | **Move** | `database/erd/` | Generated next to the generator that produces it. |
| `docs/model_cards.md` | **Split** | The `MODEL_CARD.md` of the matching version folders | It is already a set of model cards. |
| `docs/PROJECT_ANALYSIS.md`, `docs/claude_view.md`, `docs/api_usage.md` | **Move and label** | `docs/research/`, with a first line saying they describe the 2026 prototype | Useful history that would otherwise be read as current. |
| `docs/SAR_Drone_Simulation_Research.md`, `docs/graduation_project_research_plan.md`, `docs/research_papers.md`, `docs/tier1_papers_summary.md`, `docs/limitations_and_ethics.md`, `docs/experiments.md`, `docs/dataset_setup.md` | **Move** | `docs/research/` | Background knowledge for the AI side and the report. |
| `docs/architecture/platform-architecture-plan.md` (not tracked) | **Reconcile, then archive** | Its content → `ARCHITECTURE.md` and `docs/adr/` | There must be one architecture document. I have not read this file, as the debate rules require. The owner decides which of the two plans is canonical. |
| `docs/architecture/debate/` (not tracked) | **Archive after the debate** | A tag or `docs/architecture/debate-archive/` | The debate is how the decision was reached. It is worth keeping, not worth keeping in the working tree. |

## 2. Order of work

Each step is one small pull request. After each one `make repo-check` and `make docs-check` must pass.

1. **Create the new tree and the root documents** (Milestone 0 of `ARCHITECTURE.md`). Nothing is removed yet. `make repo-check` gets its protected list.
2. **Move the kept folders** with `git mv`: `mahmoudERD/` and `mapping/`, one pull request each. Nothing breaks because nothing depends on the new paths yet; the old paths are updated in the same pull requests.
3. **Move the research documents** with `git mv`. The report folders stay where they are.
4. **Move the AI material** (notebooks, scripts, configs, model cards) into `ai/training/`. Confirm the mapping with the author of the experiments.
5. **Archive the prototypes** with a tag each, then delete them from `main`.
6. **Replace the root files** (`AGENTS.md`, `README.md`, `.env.example`, `.gitignore`).
7. **Move the brand assets out**, and decide on history.

## 3. One decision for the owner: the size of the history

Moving or deleting a file does not make the repository smaller: the old blobs stay in the history. Today the repository has 30 commits, about 165 MB of tracked files under `docs/`, and a team of six. That is the moment at which rewriting the history to drop the brand binaries is cheap. Later it is not.

Two honest options:

- **Rewrite once, now**, with a tool designed for it, in a coordinated hour: everyone pushes, the history is rewritten, everyone re-clones. Open branches must be rebased. The filter names `docs/brand/` only. The four protected folders (first table of §1) must come through unchanged; check with `git log --follow` before anyone pushes the rewritten history.
- **Do not rewrite.** The clone stays at roughly its current size forever. The large files are added only once, so it does not grow further.

Either is defensible. What is not defensible is deciding nothing and discovering the question after the first release.

## 4. Rules that keep it clean afterwards

- The root allowlist in `REPO_TREE.md` §3: a file that is not in the tree cannot be added without changing the allowlist, which is a reviewed change.
- The protected list in `make repo-check`: no pull request deletes a file under the four folders named at the start of §1.
- Size limits for `fixtures/` and `scenarios/`, checked in CI.
- A generated file is committed only when it has to be reviewed, and it is regenerated by `make contracts`.
- Large artifacts follow the table in `AI_TRAINING_LAYOUT.md` §7.
- `make repo-check` runs on every pull request and reports the size of each top-level folder, so growth is visible before it becomes a problem.

## 5. What this table does not decide

- The licence of the project's own code.
- Which architecture plan is canonical (the reconcile step above).
- The mapping of the notebooks, which needs the experiments' author.
- Whether the graduation report material should live in this repository at all long term. It does for now, at `docs/documentation/` and `docs/team-plan/`, because the team's documentation plan and the university template are tied to it.
