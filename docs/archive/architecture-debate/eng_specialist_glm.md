# RescueVision: how the repository, contracts, documents, workflow and CI should be built

**Role:** Engineering Specialist F (GLM-5.4)
**Date:** 25 November 2026
**Status:** proposal for the coordinator and the Day-0 decision meeting
**Revision 2** (25 November 2026, evening): the owner's constraint applied throughout, that the
demonstration runs on a CPU-only Contabo server for one user at a time. What it changed is in
sections 1.1 (decision 13), 1.2 (finding 8), 5.7 and 5.10.
**Blueprint folder:** [`eng_specialist_glm/`](eng_specialist_glm/README.md): nine blueprint documents
and an index
**Scope:** how RescueVision gets built correctly and consistently, by six students and their AI
coding agents (Claude Code, Codex, Gemini and Antigravity, GLM and ZCode, dispatched through Orca)
working in parallel git worktrees. Other architects decide the product; this report decides how
the work is organised so that every person and every agent stays on one vision and one track.

No existing file was edited, moved or deleted. Nothing was committed, installed or deployed. All
new content is in `docs/architecture/debate/eng_specialist_glm.md` (this file) and the folder next
to it.

---

## 1. Summary

The repository is a good database, an honest report, and almost no engineering around them. There
is no `AGENTS.md` for building (the one at the root explains how to edit a Word document), no
branch protection, no CI, no pull request template, no licence file, and 45 import statements in
11 Python files that refer to a package deleted five weeks ago. Six agents turned loose on this
tomorrow would each invent their own RescueVision.

The blueprint fixes that with one agent guide, one contract pipeline, one task list, one required
check and one command that prepares any machine. Each is short enough to read and checked by a
machine, because text alone does not hold an agent to a vision.

### 1.1 The thirteen decisions

| # | Decision | Where |
|---|---|---|
| 1 | **`AGENTS.md` is the single agent guide**, with a nested guide per folder and generated one-line adapters for the tools that need one. Every tool the team uses reads `AGENTS.md` natively in November 2026. | `AGENTS.md`, `AGENT_FILES.md` |
| 2 | The root guide carries the **vision, ten invariants, a repository map, boundaries, vocabulary, commands, the change flow, a Definition of Done and a never list**, in 199 lines. Decisions live in records and their index is generated into it. | `AGENTS.md` |
| 3 | Target tree: `services/` (everything deployed), `ai/` and `kaggle/` (training), `database/`, `frontend/`, `contracts/` (the seam), `infra/`, `docs/`, `specs/`, `tools/`, and `prototypes/` (frozen evidence). The owner's `kaggle/<feature-name>/v1, v2, v3 …` is kept and refined. | `REPO_TREE.md` |
| 4 | **Contract first, with seven contracts**: migrations, core API, AI service template, events, vocabularies, stored-file keys and the model bundle. Each has one source, generates the types both sides compile against, and fails CI on drift. A contract change is its own small pull request, merged first. | `CONTRACTS.md` |
| 5 | Migrations are **plain, forward-only SQL with dbmate**. The existing 16 schema files become the frozen baseline. | `CONTRACTS.md` |
| 6 | The training layout is refined around the practice already on the unmerged `codex/building-damage-v4` branch: thin notebooks, a package pinned by commit, inputs locked by hash, a reviewed submission specification, a record for every run, weights never in Git. The 27 existing notebooks are filed under version folders: twenty under `building-damage/v1` to `v3`, seven under `flood-road-segmentation/v1`. | `REPO_TREE.md` §6 |
| 7 | **Trunk-based development on a protected `main`**, squash merges, the pull request title as the only commit-message gate, and rules that work for agents that name their own branches. | `BRANCHING.md` |
| 8 | CI filters **at the job level** and reports **one required check**, `ci/ok`. CI never needs a GPU: it tests AI contracts with a fixture bundle and verifies the evidence of training done on Kaggle. | `CI_CD.md` |
| 9 | Deployment is **Docker Compose and Caddy on the Contabo VPS**, images by digest, secrets encrypted with SOPS and age, and a **monthly restore drill** as the proof of the backup the report promises. | `CI_CD.md` §10 |
| 10 | A new developer or agent runs **`make bootstrap`, then `make doctor`**. The same four commands work for people and agents, on any OS, with no GPU. | `DEV_ENV.md` |
| 11 | Documentation is a system with owners: one page per job, decision records, feature specs, and **generated evidence documents**, including a ledger that links each of the report's 161 requirement IDs to the tests that prove it. | `DOCS_SYSTEM.md` |
| 12 | Cleanup in **three phases**, where nothing tracked is deleted. `mahmoudERD/`, `mapping/` and `docs/documentation/` are kept, the first two moved with their history. | `REPO_CLEANUP.md` |
| 13 | **The demonstration is CPU-only** (the owner's constraint): one Contabo server, one user at a time, inference with ONNX Runtime or OpenVINO, heavy work precomputed and checked by hash, 3D drawn in the browser, and SeaweedFS instead of MinIO, whose repository is archived. | `CI_CD.md` §10, `REPO_TREE.md` §10 |

### 1.2 Eight findings that change the plan

These are facts about the repository or its hosting, each checked on 25 November 2026.

1. **The GitHub repository is public and owned by a personal account.** GitHub's merge queue is
   documented for public repositories owned by an organization. It is not available as things
   stand. The blueprint uses strict up-to-date checks plus auto-merge now, writes the workflows
   with `merge_group` so a later transfer to a free organization needs no CI change, and says so
   (BRANCHING.md §4).
2. **`main` has no protection and no CI.** The API answers "Branch not protected"; the ruleset list
   is empty; there is no `.github/` directory. Thirty commits, four merges, one pull request.
3. **The worktree this blueprint was written in is checked out on `main`.** An Orca worker started
   with `--worktree current` in such a workspace can commit to the trunk. Hence `make doctor` and a
   ruleset that blocks direct pushes even for administrators.
4. **A required check that is skipped blocks every merge.** GitHub's documentation: "If a workflow
   is skipped due to path filtering … then checks associated with that workflow will remain in a
   'Pending' state." Two of the three competing blueprints make path-filtered jobs required.
5. **Testcontainers Python has no PostGIS module in its current source tree** (the Postgres module
   is at `testcontainers.community.postgres`). Tests should start the project's own database image,
   which is also what Compose and production run. The image tags exist: `postgis/postgis:18-3.6`
   and `pgvector/pgvector:0.8.7-pg18`.
6. **Atlas supports row-level security policies, triggers and functions only in its paid edition.**
   Those are the heart of this schema, which rules out Atlas and ORM-generated migrations.
7. **`.gitignore` ignores `kaggle.json`** (the Kaggle credential). With a top-level `kaggle/`
   folder, a project file of that name anywhere would be silently ignored. Worth a line in the
   guide.
8. **MinIO, named in the report's design documents and in two proposals, is archived.** The GitHub
   API shows `minio/minio` archived, last push 24 April 2026, last release October 2025. The
   blueprint uses SeaweedFS in `weed mini` mode, whose README names exactly this use ("fine for
   single-node production, such as an S3 gateway that issues presigned URLs"), with RustFS as the
   alternative. Both are Apache-2.0 with releases this month.

---

## 2. How this was checked

Four kinds of evidence, not equal in weight:

| Kind | Meaning |
|---|---|
| **ran** | a read-only command on this machine: `git`, `gh api`, Docker Hub, a JSON parse of notebooks, `find`, `grep` |
| **read** | a repository file, at the stated path |
| **fetched** | a documentation page read on 25 November 2026; the URL is in section 11 |
| **observed** | this session's own harness: the Orca 1.4.268 orchestration guide, the ZCode configuration guide, the Kaggle MCP tool list |

Two limits are stated where they matter. The sentence on merge-queue availability is quoted by the
search index from two GitHub documentation pages and matches GitHub's changelog post; my own
fetch of the page did not return it. A few well-known standards are cited from knowledge and are
marked as such in section 11. Where the other proposals contain a number I could not confirm, I
do not repeat it.

What this report does **not** decide: the core backend language, the AI serving framework, the job
queue and live-update transport, the map engine, the offline protocol. Those are the product
architects' questions. Every document here is written to hold whichever way they go (REPO_TREE.md
§9 lists the rows that change). Two things the owner has fixed are not open: the host has no GPU
(section 5.10), and training runs on free Kaggle or Colab GPUs.

---

## 3. The repository today

| Area | What is there | Evidence |
|---|---|---|
| Agent guidance | a 93-line root `AGENTS.md` about editing the graduation report; nothing about building | read |
| Protection and CI | none | ran: `gh api` ("Branch not protected", rulesets `[]`), no `.github/` on `main` |
| History | 30 commits on `main` from four authors (two wrote 23); 4 merges, 1 pull request | ran: `git shortlog`, `git log` |
| Branches | five naming patterns; `codex/building-damage-v4` is 24 ahead and 28 behind `main`, never reviewed | ran: `git rev-list --left-right --count` |
| Database | 2,911 lines of schema, seed and self-checks; 57 type definitions; RLS on every table | ran: `wc`, `grep -c` |
| Python | 11 files with 45 module-level imports of `rescuevision.*`, a package deleted in `f89a61f` (21 October 2026) | ran: `git grep` |
| Notebooks | 34 notebooks, zero saved outputs; the 27 Kaggle ones clone an unpinned repository | ran: JSON parse, read |
| Frontend | 23 README files and 6 configuration files; no code; a link to a document that does not exist | ran: `git ls-files`, `find` |
| Documentation | 96 Markdown files (53 tracked) with at least four architecture positions | ran: `find`, `git ls-files` |
| Licensing | `pyproject.toml` says MIT; there is no `LICENSE` file; GitHub reports no licence for this public repository | ran: `gh api` (`licenseInfo: null`) |
| Size | about 106 MiB in the pack, mostly brand images and the report | ran: `git count-objects` |

The best assets are the database, the report's review discipline (`docs/team-plan/review/`), and
the engineering on the unmerged V4 branch. The blueprint is built to keep all three and to make
the V4 branch's practice the rule.

---

## 4. What is fixed and what is still to decide

**Fixed by the owner or already common ground:** one repository; a modular core with separately
deployed AI containers, each behind an API; PostgreSQL 18 with PostGIS, pgRouting and pgvector and
row-level security; pnpm and Turborepo for the frontend (web and Expo mobile); training on Kaggle
in `kaggle/<feature-name>/vN`; Compose on a Contabo VPS; and, since the evening of 25 November, a
CPU-only demonstration server for one user at a time with no budget for a GPU (the feasibility
study in `cpu_demo_feasibility.md` reaches the same conclusion from measurements).

**To accept on Day 0, before any code** (DOCS_SYSTEM.md §3 lists them with what the repository
already says about each): ADR-0001 one repository and contract-first; 0002 core backend language;
0003 AI serving on CPU; 0004 job queue and live updates; 0005 object storage, with MinIO excluded;
0006 map engine and tiles; 0007 offline synchronisation; 0008 plain-SQL migrations; 0009
`AGENTS.md` as the single guide; 0010 protection of `main`. Until a record is accepted, the root
guide shows it as ⚠ proposed.

---

## 5. The decisions in detail

### 5.1 One agent guide, many adapters

**What.** `AGENTS.md` is written by a person. Everything else is a nested `AGENTS.md` for one
folder, or a generated adapter: a two-line `CLAUDE.md` and `GEMINI.md` containing `@AGENTS.md`, a
`.gemini/settings.json` naming `AGENTS.md` as a context file, and forwarding `SKILL.md` files.
`make gen` writes them; `make check` fails when they are stale.

**Why.** Checked against each tool's documentation (AGENT_FILES.md §2): Codex concatenates
`AGENTS.md` files from the Git root down to the current directory; Claude Code reads `AGENTS.md`
natively since v2.1.277; Cursor "supports `AGENTS.md` in the project root and subdirectories";
OpenCode, GitHub Copilot and Antigravity's managed agents read it; Gemini CLI reads it once its
`context.fileName` setting names it. agents.md reports adoption by "over 60k open-source projects"
and gives the conflict rule the design relies on: "The closest AGENTS.md to the edited file wins".

**The detail that matters.** ZCode loads only the file found from the working directory upward,
and a root-started Codex session sees no nested file. So the root guide must carry the index
("read this before editing that"). And Codex stops at 32 KiB of combined instructions, so budgets
are enforced: root ≤ 14 KiB and 200 lines, nested ≤ 6 KiB and 80 lines.

**Against drift.** Eight layers, in order: one source; the root index; decision records; checks
for every rule a machine can test ("If something has to happen every time, make it a hook, a deny
rule, or a managed setting", Claude Code best practices); `make doctor` at session start; budgets;
"when an agent errs, fix the rule"; a monthly diet. Agent configuration is treated as an
executable surface: it is owned by the repository owner in `CODEOWNERS`, and workspace-level MCP
servers stay empty, because ZCode connects them automatically.

### 5.2 A short guide with long teeth

The draft `AGENTS.md` states the product in the report's own vocabulary, then ten invariants:
nine taken from the report's Table 3-39 and its requirements, and one from the owner. A person
decides (D-07), access is enforced in the database (D-04), one shared incident (D-01), analysis
is queued (D-03), unknown is never shown as safe (NFR-SF-02), every AI result names its model
version (FR-IM-07), snapshots are frozen (D-06), metres on WGS 84 (D-09), nothing is described as
done that was not run, and the demonstration needs no GPU, no paid service and no second server.

Its Definition of Done requires evidence: "`make check` passes on the pushed commit", tests tagged
with requirement IDs, contracts regenerated, and a human approval. This follows the guidance in
Claude Code's documentation ("Claude stops when the work looks done. Give Claude something it can
run that comes back pass or fail") and the DORA 2025 report, which finds that "AI adoption does
continue to have a negative relationship with software delivery stability" and that "AI doesn't
fix a team; it amplifies what's already there." METR's field study is the reason evidence is
demanded over impressions: experienced developers "take 19% longer to complete issues" with AI
tools while believing they were faster (the page carries a banner saying the results are out of
date; the lesson about self-reported speed still stands).

### 5.3 The tree

Six rules decide where a file goes (REPO_TREE.md §1). The two that matter most:

- **Group by what is deployed.** `services/core-api`, `services/worker`, `services/ai/<family>`.
  The boundary "the backend never imports a model framework, an AI service never holds a database
  credential" becomes a path rule that `make check` enforces.
- **Frozen evidence is a folder, not a memory.** `prototypes/mapping` (the Chapter 4 prototype),
  `prototypes/dashboard`, `prototypes/legacy-ml`. An agent can read them and cannot mistake them
  for the product.

Tooling stays small: pnpm and Turborepo for JavaScript, one `uv` workspace ("the workspace shares a
single lockfile"), `mise` for toolchain versions (`mise.lock` records "the download URL and
checksum for each platform you lock"), a `Makefile` as the only task list. Nx, Moon and Bazel are
not adopted: two package managers do not need a third task graph.

### 5.4 Contract first

Seven contracts, one source each (CONTRACTS.md §2). The flow is always the same: describe, contract
pull request, review the interface, merge, then the implementing pull requests branch and work
against generated mocks and generated types. Three worked examples show what this means for an
added field, a new endpoint used by web and mobile, a new table and a new model version.

The AI service template adopts Architect B's shape (`glm_proposal.md` §6.2): `GET /healthz`,
`GET /readyz`, `GET /v1/model-info`, `POST /v1/tasks` returning `202`, `GET /v1/tasks/{id}`, with
`job_id` as the idempotency key and inputs and outputs by reference. "A long inference never holds
one HTTP request open." It is better engineering than the synchronous call in my first draft.

### 5.5 The training layout

`kaggle/<feature-name>/vN/` keeps the owner's structure and adds eight rules that make a version
folder worth having (REPO_TREE.md §6.1). All of them are already practice on the V4 branch:
submission specifications that are reviewed before upload, "no credentials in notebook source",
run records with SHA-256 for each artifact, and "the laptop is source-only". The layout turns that
practice into the rule for every feature and maps the 27 notebooks into `v1` (`rv_`), `v2` (`rv2_`),
`v3` (`rv3_`) and `kaggle/flood-road-segmentation/v1`, with `v4` from the branch.

Two evaluation gates, kept apart on purpose. Gate A runs in CI on a CPU: the service keeps its
contract and the fixture bundle reproduces its golden output. Gate B runs on Kaggle and is
verified, not re-run: CI recomputes the hashes of a recorded run and compares `metrics.json` with
the artifact. Promotion needs a run in state `scientifically_reviewed`.

### 5.6 Branching

One trunk, branches of two days at most, squash merges, releases by tag through release-please
("We highly recommend that you use squash-merges when merging pull requests"). Because Claude Code
creates branches named `worktree-<name>` and Orca pushes `<user>/<workspace>`, naming is a
convention and the **pull request title is the gate**. The ruleset, the pull request template, the
reviewer's five questions, a code-owner draft (report ownership confirmed, code ownership
proposed), and per-tool worktree rules are in BRANCHING.md.

### 5.7 CI and deployment

Fourteen jobs, one required check, filtering at job level with an aggregator that treats a
deliberate skip as success and anything else as failure (CI_CD.md §4). The first pull requests
after Day 0 should be six database tests written to fail, because the red-team review predicts
defects in the hazard engine by reading the SQL (CI_CD.md §6). Nobody has executed those tests yet;
the column says so.

Deployment: Compose and Caddy ("Automatic HTTPS by default"), images by digest, SOPS with age,
Kamal and k3s considered and declined with the reason. The backup is a check: pgBackRest or restic
off-site, and a scheduled restore drill whose green run is the evidence for NFR-RL-05. Preview
environments are web-only; a full-stack preview needs a second machine and is not planned.

### 5.8 Documentation as a system

One job and one owner per document (DOCS_SYSTEM.md §2). Decision records in Nygard's five parts
with MADR frontmatter. Feature specs through GitHub Spec Kit, which is already installed at user
scope. Evidence documents are generated: the trace matrix, the evaluations table, model cards, the
ERD, the API reference, the decision index.

The **requirements ledger** is the piece built for this project. Section 3.2 has 161 requirement
IDs and the team's review asks for "a way a future reviewer could judge whether it is met". One
script extracts the IDs from the report; tests carry their ID as a marker; `make trace` writes the
matrix with one of four states per ID. Chapter 5 can then cite it, and the rule "do not invent
screenshots, experiments or results" becomes something CI can check.

The graduation report keeps its own guide, moved unchanged to `docs/documentation/AGENTS.md`, and
stays where it is: `.gitignore` has six rules tied to those paths, and the team edits those files
now.

### 5.9 Cleanup

Every current path has a verdict and a reason (REPO_CLEANUP.md §2). The only deletions are an
untracked scratch viewer and a local cache. Everything else is kept, moved with `git mv`, or
replaced with its old content preserved. The work is ordered so that nothing in the report's way
moves before the report is submitted.

### 5.10 The CPU-only, single-user demonstration

The owner's constraint: a strong CPU and plenty of RAM on one Contabo server, no GPU and no budget
to rent one, one user at a time. Training happens on free Kaggle or Colab GPUs. Four rules follow,
and each has something in the repository that enforces it (CI_CD.md §10.6).

| Rule | What enforces it |
|---|---|
| Heavy work is precomputed; the request path stays light | `infra/demo/manifest.yaml` lists every artifact with its hash; `make demo-verify` runs in the deploy smoke test and in the runbook; CI refuses a request handler that starts photogrammetry or an area-wide sweep |
| One heavy inference at a time, threads pinned to physical cores | `services/ai/AGENTS.md`; `bundle.lock.json`; a memory limit on every service in the production Compose file |
| Precision is chosen per model by measurement, not by a rule | the bundle manifest records runtime, precision and parity against FP32; the `ai-contract` job tests the quantised bundle; `ai-perf` records CPU latency |
| Nothing large runs on the server except the application | no PyTorch, CUDA, Triton or TensorRT in a deployed image (layer audit); no language model on the host; no server-side 3D, which is drawn in the browser |

What the numbers say, with their source. The feasibility study measured, on a 4-core i5-1135G7
laptop: about 84 ms per building crop for a DINOv2-base proxy with int8, 66 to 161 ms per frame for
a small detector proxy, 0.63 to 0.85 s per tile for a damage proxy, and 4 threads faster than 8 on
every heavy model. It estimates 12 to 25 minutes on CPU for 50 to 80 drone images of photogrammetry,
which is why that step is precomputed the evening before. Its sizing is Contabo's `Cloud VPS Plus 8`
(8 vCPU, 24 GB RAM), with a dedicated-core plan only if shared-host CPU steal shows in a rehearsal.
Its measurements are that study's; I did not repeat them, and I did not check Contabo's plans or
prices. Server latencies are estimates until a rehearsal measures them.

The object store is the one component this constraint changes outright. MinIO is named in the
report's design documents and in two proposals; the GitHub API shows its repository archived. Two
maintained, Apache-2.0 replacements have releases this month:

| Candidate | Status (GitHub API, 25 November 2026) | Fit |
|---|---|---|
| **SeaweedFS, `weed mini` mode** (chosen) | not archived; release 4.55; README: `weed mini` "is auto-tuned for one node and is fine for single-node production, such as an S3 gateway that issues presigned URLs" | one process, one volume; named for exactly this use; its README also warns that the admin interface and WebDAV bind "even without authentication", so the Compose file publishes only the S3 port |
| **RustFS** (alternative) | not archived; release 1.0.6; README: "Single Node Mode" available, "broad S3 API compatibility for supported features" | closest to MinIO in behaviour and console; its container runs as a non-root user, so bind mounts need matching permissions |
| MinIO | archived; last push 24 April 2026; last release October 2025 | not a candidate |
| Garage | not archived; AGPL-3.0 | not needed: the two above are Apache-2.0 |

Because the S3 API is the contract (ADR-0005), the choice is reversible with one Compose service.
What must be proven on Day 1, in the integration job, against the real store: a presigned upload
from the browser, a byte-range read for the raster tiles, a resumable multipart upload, and CORS
from the console's origin.

---

## 6. Day 0 (26 November 2026)

| Time | Step | Done when |
|---|---|---|
| 09:00 | `git tag pre-rebuild-2026-11-26`. Decide whether to transfer the repository to a free organization (enables the merge queue). | tag exists |
| 09:15 | Pull request 1: `.github/` with `ci.yml` holding `changes`, `guard`, `ci-ok`; `CODEOWNERS`; pull request and issue templates. Protect `main`. Turn on the repository security settings. | the first real pull request merges through `ci/ok` |
| 09:45 | Decision meeting, part 1: ADR-0002, 0003, 0004, 0005, 0006, 25 minutes each | five records `accepted`, each with a named decider |
| 12:00 | Pull request 2: `Makefile`, `mise.toml`, `.pre-commit-config.yaml`, `.gitattributes`, `.editorconfig`, `.dockerignore`, `.worktreeinclude`, `LICENSE` | `make bootstrap` works on two machines |
| 13:00 | Pull request 3: the root `AGENTS.md` (⚠ rows filled), the nested guides, the adapters; the report guide moved to `docs/documentation/AGENTS.md` | each tool loads the context (AGENT_FILES.md §8) |
| 14:00 | Pull request 4: merge `codex/building-damage-v4` | branch is 0 ahead of `main` |
| 14:30 | Decision meeting, part 2: ADR-0001, 0007, 0008, 0009, 0010 | index in `AGENTS.md` shows no ⚠ |
| 15:15 | Pull requests 5 to 8: the moves (legacy code, mapping prototype, notebooks, Mahmoud's ERD) | link check green; `git log --follow` works on a moved file |
| 16:30 | Smoke test: an Orca worker in a new child worktree, spec "run `make bootstrap`, `make doctor`, `make check`; paste the output" | it passes with no further setup |
| 17:00 | Rewrite `README.md`. Measure and record the bootstrap, `up` and `check` times in `DEV_ENV.md`. | a classmate who has never opened the repository gets the stack running |
| 17:30 | Choose and order the Contabo server. The feasibility study recommends `Cloud VPS Plus 8` (8 vCPU, 24 GB RAM); confirm the current plans and prices, which I did not check. | server ordered |

Two things are deliberately absent from Day 0: application code, and any schema change. The day
buys the track; the train leaves on day 1.

---

## 7. The first two weeks, in order

Each item is a pull request or a short series, with its proof.

| Week | Step | Proof |
|---|---|---|
| 1 | Six database tests that fail today, then the fixes (CI_CD.md §6) | `db` job green with the six tests present |
| 1 | `database/Dockerfile`; dbmate baseline; `make db-reset` | the same image runs locally, in CI and in Compose |
| 1 | `contracts/openapi/ai-service.yaml`, `services/ai/_template` with a fixture bundle | `ai-contract` job green |
| 1 | The object store in Compose and in tests: presigned upload, byte-range read, multipart, CORS | the `integration` job runs against the same store image as the server |
| 1 | A core-api skeleton that boots and exports its OpenAPI; the generated TypeScript client | `contracts` job green |
| 1 | The staging VPS: `cd-staging.yml`, SOPS, the first backup, the first restore drill | a green `restore-drill` run |
| 2 | One vertical slice in staging: a hazard report leads to an alert, a live event and a banner, with the latency measured | a trace from hazard insert to event sent (NFR-PF-04) |
| 2 | The requirements ledger: 161 IDs extracted, markers on existing tests | `docs/requirements/trace.md` generated |
| 2 | `kaggle/building-damage/v4` in place; `kaggle-check` and `ai-evidence` in CI | the folder validates; `runs/` records verify |
| 2 | First "guide diet" and a retrospective on agent mistakes | rules added or removed, with the pull requests that asked for them |

---

## 8. Where this blueprint meets the others

The debate folder holds three architecture proposals, two red-team reviews and three specialist
reports. On the engineering questions they overlap. The table states the position taken here and
what still needs one decision.

| Topic | Others | Here | To decide |
|---|---|---|---|
| Root agent file | all three blueprints replace the root `AGENTS.md` | agrees, and adds generated adapters and budgets | nothing |
| Top-level names | Architect A: `backend/`, `ai/`, `infra/`; Red-team C: `backend/`, `ai/`, `triton-repo/`, `edge/`; Architect B: `backend/`, `models/`, `deploy/` | `services/`, `ai/`, `kaggle/`, `contracts/`, `infra/`, `prototypes/` | choose **one** vocabulary before the first folder exists; every later rename is a move pull request and broken links |
| AI training folder | AI Specialist E: `ai/` with `rv_ai`, `kaggle/<feature>/vN/`; Red-team C: `rv_ai`; Architect B: `models/tasks/` | `ai/` with `rescuevision_ai`, `kaggle/<feature>/vN/` (the owner's layout) | package name: `rv_ai` or `rescuevision_ai`; two minutes |
| Version numbers | AI Specialist E trains `building-damage/v2` (SiameseUNetSE) | `v1`–`v3` are the `rv_`, `rv2_`, `rv3_` notebooks and `v4` is the owner's branch | do not renumber: the owner's own branch is `v4` |
| AI service contract | Architect B: two-step tasks; A and C: synchronous `:predict` | Architect B's shape | ADR-0003 |
| One container per model or per family | owner's words: per model; Architect B and Red-team D: per family; AI Specialist E: three containers | neutral: one folder per deployed service | ADR-0003 |
| Required CI checks | A: four checks; C: four, one of them only when AI paths change | one aggregator, `ci/ok` | nothing; the documented pending-check behaviour settles it |
| CI and GPUs | A and C assume a self-hosted or cloud GPU runner | never; evidence is verified, contracts tested on CPU | nothing; follows from CPU-first |
| Report documents | A: keep in place; C: move to `docs/thesis/` | keep in place; guide moved to `docs/documentation/AGENTS.md` | nothing before submission |
| `mahmoudERD/`, `mapping/` | A: merge and delete, archive; C: archive and delete, remove generated files | moved and preserved | confirm the move with Mahmoud |
| Migrations | Red-team D: Alembic; A and C: "forward-only SQL" with no tool | dbmate | ADR-0008 |
| Worker | Architect B and Red-team D: same image as the core, second entry point | separate folder, merges into the core if ADR-0004 says so | ADR-0004 |
| CPU or GPU at the centre | the platform plan, Architect A and Red-team C assume GPUs, a rented GPU node or Triton; AI Specialist E and the feasibility study: CPU first with ONNX Runtime or OpenVINO | CPU only, by the owner's constraint: no GPU image, no model server, heavy work precomputed, 3D in the browser | nothing: fixed by the owner on 25 November |
| Object store | the platform plan, Architect A and Red-team C: MinIO; Red-team D: RustFS or SeaweedFS; the feasibility study: RustFS, SeaweedFS or Garage | SeaweedFS in `weed mini` mode, RustFS as the alternative; MinIO excluded (repository archived) | ADR-0005 confirms the default; the four S3 checks in section 5.10 prove it on Day 1 |

One disagreement with a sibling is worth naming because it would cost real work. AI Specialist E
numbers the first trained joint model `building-damage/v2`. The repository already has three
generations of notebooks and a branch called V4. Renumbering would break the owner's own record.
The mapping in REPO_TREE.md §6.2 keeps the owner's numbers.

---

## 9. Risks, and what would change my mind

| Risk | Mitigation in the blueprint | Would change my mind if |
|---|---|---|
| The team reads none of it | the guide is 199 lines; `make doctor` is the first command; CI refuses what the guide forbids | agents keep breaking a rule that has no check (then write the check) |
| A merge queue is wanted and the account stays personal | strict up-to-date checks and auto-merge; workflows already carry `merge_group` | integration failures on `main` appear more than weekly |
| Standard runners are too small for end-to-end tests | end-to-end runs on a label, on `main` and nightly, not on every pull request | a pull request path takes longer than 15 minutes |
| Agents flood the review queue | about four concurrent workers per person; one approval; 400-line target | reviews wait more than a day |
| The contract step slows small changes | additive changes go in one pull request; only new or cross-team interfaces need the separate step | nobody uses the mocks, or every change becomes two pull requests |
| The requirements ledger goes stale | it is generated, and CI fails on an unknown ID | Section 3.2 is renumbered (then extract again) |
| The report and the build pull the team apart | the report keeps its own guide and its own review rhythm; build changes that touch a report claim add a tracker row | — |
| `make bootstrap` drifts from what agents actually run | it is the setup command Orca runs for a new worktree, and the smoke test on Day 0 | a fresh worktree needs a manual step twice |
| CI runners are not the server: Contabo's EPYC has AVX2 but not the laptop's AVX-512 | `ai-perf` records latency and fails only on a gross regression; the runbook measures on the server in each rehearsal | a model passes in CI and misses its latency on the server |
| One server serves staging and the demonstration | `deploy.sh` refuses while `DEMO_FREEZE=1` is set; a tag and two approvals gate production | a deploy interrupts a rehearsal, or two environments prove too little isolation |
| The chosen object store fails one of the four S3 checks | the S3 API is the contract; RustFS is one Compose service away | a presigned upload, a byte-range read, multipart or CORS fails on SeaweedFS and passes on RustFS |
| A live step in the demonstration turns out too slow on the server | every heavy step is precomputed and checked by hash the evening before; the runbook says what is precomputed | in a rehearsal, the presenter has to wait for a user-triggered inference (set the threshold at the first rehearsal) |

---

## 10. Limits of this report

- **Not executed.** The six database tests in CI_CD.md §6 are predicted from reading the SQL. The
  `ci.yml` is a sketch: the real file is longer and will need the jobs' steps.
- **Not measured.** All times and sizes marked as targets are to be measured on Day 0.
- **Product decisions left open.** Seven records are proposed, not accepted. The tree tolerates
  every outcome; REPO_TREE.md §9 lists the rows that change.
- **Code ownership is a proposal.** Only the report ownership is confirmed. GitHub handles other
  than the repository owner's are not known here and are marked `@<handle>`.
- **Two hosting questions are open.** Whether to transfer the repository to an organization, and
  which Contabo plan to buy (the feasibility study recommends `Cloud VPS Plus 8`; I did not check
  Contabo's plans or prices).
- **The CPU-only design is reasoned, not run.** I did not start SeaweedFS, RustFS, an ONNX Runtime
  or OpenVINO service, or OpenDroneMap. The latency figures are the feasibility study's
  measurements on its laptop, quoted as such; server latencies are its estimates. The four S3
  checks in section 5.10 are the first thing to run on Day 1.
- **Some sources are cited from knowledge** and marked so in section 11.
- **Repository security settings** (secret scanning, Dependabot, CodeQL) were not re-read in
  GitHub's documentation; enable them on Day 0 and confirm the billing page.

---

## 11. Sources

All pages were read on 25 November 2026 unless marked.

### Agent instruction files

| Source | Used for |
|---|---|
| https://agents.md | format, adopters, "closest AGENTS.md wins" |
| https://learn.chatgpt.com/docs/agent-configuration/agents-md | Codex discovery order, nesting, 32 KiB limit |
| https://code.claude.com/docs/en/memory | Claude Code: native `AGENTS.md`, lazy nested files, imports, 200-line target, `.claude/rules/` |
| https://code.claude.com/docs/en/best-practices | short `CLAUDE.md`; "Give Claude something it can run that comes back pass or fail"; hooks; `/batch`; a second session as reviewer |
| https://code.claude.com/docs/en/worktrees | `-w`, `.claude/worktrees/`, `worktree-<name>`, `.worktreeinclude`, fresh checkouts |
| https://code.claude.com/docs/en/sandbox-environments | cloud sessions; dev containers |
| https://geminicli.com/docs/cli/gemini-md | Gemini CLI context files, `context.fileName`, just-in-time loading |
| https://cursor.com/docs/context/rules | Cursor: native `AGENTS.md`, `.mdc` rules, "under 500 lines" |
| https://opencode.ai/docs/rules/ | OpenCode lookup order |
| https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions | Copilot: nearest `AGENTS.md` wins |
| https://aistudio.google.com/docs/antigravity-agent.md and https://aistudio.google.com/docs/custom-agents.md | Antigravity managed agents: `.agents/AGENTS.md`, `.agents/skills/` |
| https://agentskills.io/specification and https://agentskills.io/integrate-skills | Agent Skills format and the `.agents/skills/` convention |
| ZCode `zcode-configuration-guide` skill (0.3.0), read on this machine | workspace `AGENTS.md`, skills and commands directories, hooks, MCP auto-connect |
| Orca `orchestration` guide printed by Orca 1.4.268 | workers, child worktrees, `--setup run`, task-spec standard, concurrency |

### Workflow evidence

| Source | Used for |
|---|---|
| https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report | 90% use AI; stability still negatively related; "AI doesn't fix a team; it amplifies what's already there" |
| https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/ | 19% slower, believed faster (page marked out of date) |
| https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | context rot; "find the smallest set of high-signal tokens" |
| https://github.com/github/spec-kit | spec-driven development; requirements; constitution command |
| https://trunkbaseddevelopment.com/ | trunk-based development rules |
| https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions | ADR format, size, superseding |
| https://adr.github.io/madr/ | MADR frontmatter, statuses, file naming |
| https://github.com/googleapis/release-please | squash recommendation; type to version mapping |
| https://www.conventionalcommits.org | commit format (cited from knowledge, not opened) |

### Tooling

| Source | Used for |
|---|---|
| https://mise.jdx.dev/ | tool pinning, `mise.lock`, idiomatic version files |
| https://docs.astral.sh/uv/concepts/projects/workspaces/ | one lock file per workspace |
| https://turborepo.dev/docs/crafting-your-repository/constructing-ci | `--affected`, history requirements, remote cache |
| https://containers.dev/ | Dev Container Specification |
| https://github.com/kynan/nbstripout | `--verify`, `--is-installed`, `.gitattributes` |
| https://import-linter.readthedocs.io/en/stable/readme.html | contract types, `lint-imports` |
| https://github.com/amacneil/dbmate | timestamped SQL migrations, transactions, `schema_migrations` |
| https://atlasgo.io/atlas-schema/hcl | Pro-only policies, triggers and views |
| https://github.com/openapi-ts/openapi-typescript | TypeScript types from OpenAPI; `openapi-fetch` |
| https://github.com/stoplightio/spectral | `spectral:oas` |
| https://github.com/oasdiff/oasdiff | breaking-change detection |
| https://github.com/schemathesis/schemathesis | property-based API testing on Hypothesis |
| https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/formats/json-format.md | event envelope attribute names |
| https://www.rfc-editor.org/rfc/rfc9457 and https://json-schema.org/draft/2020-12 | problem details; JSON Schema (both cited from knowledge, not opened) |
| https://github.com/testcontainers/testcontainers-python (through `gh api`) | module layout: `src/testcontainers/community/postgres`, no PostGIS module |
| Docker Hub tags API | `postgis/postgis:18-3.6`, `pgvector/pgvector:0.8.7-pg18` |
| https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels_metadata.md | `kernel-metadata.json` fields |
| https://github.com/microsoft/playwright and https://github.com/mobile-dev-inc/maestro | browser and mobile end-to-end tests |
| https://github.com/ESSS/pytest-regressions | stored expectations for data, images and numeric tables |

### GitHub and deployment

| Source | Used for |
|---|---|
| https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions | path filters and the pending-check warning |
| https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue | `merge_group` requirement, limits |
| https://github.blog/changelog/2023-07-12-pull-request-merge-queue-is-now-generally-available | availability: public repositories owned by an organization (URL confirmed through search; the page was not fetched) |
| https://docs.github.com/en/billing/concepts/product-billing/github-actions | free standard runners for public repositories |
| https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners | code owners (cited from knowledge, not opened) |
| https://docs.docker.com/reference/cli/docker/compose/up/ | `--wait`, `--wait-timeout`, `--remove-orphans` |
| https://github.com/caddyserver/caddy | "Automatic HTTPS by default" |
| https://kamal-deploy.org/docs/installation/ | root SSH, registry, kamal-proxy |
| https://docs.k3s.io/ | "half the memory, all in a binary of less than 100 MB" |
| https://doc.traefik.io/traefik/ | providers, middlewares |
| https://github.com/coollabsio/coolify and https://github.com/Dokploy/dokploy | self-hosted deployment consoles |
| https://getsops.io/docs/ | SOPS formats and key services |
| https://github.com/restic/restic and https://github.com/pgbackrest/pgbackrest | backups and verification |

### Owner constraint and CPU-only hosting

| Source | Used for |
|---|---|
| Coordinator's message of 25 November 2026 (owner constraint) | CPU-only Contabo server, one user at a time, no budget for a GPU, training on free Kaggle or Colab GPUs |
| `docs/architecture/debate/cpu_demo_feasibility.md` (the performance and MLOps engineer's study) | laptop measurements, thread-pinning rule, quantisation per model, photogrammetry times, Contabo plan recommendation; all quoted as that study's |
| GitHub API on 25 November 2026: `minio/minio` (archived, last push 24 April 2026, release `RELEASE.2025-10-15`); `seaweedfs/seaweedfs` (Apache-2.0, release 4.55); `rustfs/rustfs` (Apache-2.0, release 1.0.6); `deuxfleurs-org/garage` (AGPL-3.0); `openvinotoolkit/openvino` (Apache-2.0, release 2026.4.1); `OpenDroneMap/NodeODM` (AGPL-3.0) | which stores and runtimes are maintained |
| SeaweedFS README (`weed mini` quote and its warning on unauthenticated admin and WebDAV); RustFS README (single-node mode, non-root user) | https://github.com/seaweedfs/seaweedfs and https://github.com/rustfs/rustfs |
| PyPI: `onnxruntime` 1.32.0, "MIT License" | ONNX Runtime version and licence (its source repository could not be located through the GitHub API on that date) |
| Docker Hub tags: `rustfs/rustfs` 1.0.6, `chrislusf/seaweedfs` | both stores ship official images |

### Repository evidence

`git log`, `git shortlog`, `git rev-list`, `git grep`, `git ls-files`, `git count-objects`,
`gh api repos/AliOmarAbdelhady/RescueVision` (owner type, visibility, licence, protection,
rulesets), `gh api repos/testcontainers/testcontainers-python`, and the files under `docs/`,
`database/`, `frontend/`, `notebooks/` and the `codex/building-damage-v4` branch. The sibling
reports used for reconciliation: `platform-architecture-plan.md`, `gemini_proposal.md`,
`redteam_gemini.md`, `redteam_glm.md`, `glm_proposal.md`, `ai_specialist_gemini.md`,
`cpu_demo_feasibility.md`.
