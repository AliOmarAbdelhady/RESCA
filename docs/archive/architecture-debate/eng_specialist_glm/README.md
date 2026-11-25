# Engineering Specialist F blueprint (`eng_specialist_glm/`)

Blueprint folder for the main report [`eng_specialist_glm.md`](../eng_specialist_glm.md).
Author: Engineering Specialist F (GLM-5.4). Date: 25 November 2026.

Scope: how RescueVision gets built correctly and consistently by six students and their AI
coding agents working in parallel worktrees. The product architecture is decided elsewhere; this
folder designs the repository, the contracts, the documents, the workflow and the pipeline, and is
written to hold whichever way those decisions go.

One constraint is the owner's and is not open for a decision: the demonstration runs on a CPU-only
Contabo server, for one user at a time, with no budget to rent a GPU; training happens on free
Kaggle or Colab GPUs, and the server runs the application and CPU inference. Every file that
touches deployment, images or the local stack applies it.

| File | What it gives the team |
|---|---|
| [`AGENTS.md`](AGENTS.md) | The complete draft of the new root agent guide: vision and invariants, repository map, boundaries, vocabulary, commands, change flow, testing rules, Definition of Done, the never list, the report track, and a generated decision index. 199 lines. |
| [`AGENT_FILES.md`](AGENT_FILES.md) | What each agent tool reads (checked), every nested guide and what it must contain, the template, six skills, and eight layers that stop agents from drifting. |
| [`REPO_TREE.md`](REPO_TREE.md) | The full target tree with one purpose per folder, the forbidden-here table, "where does a new file go?", the refined `kaggle/<feature>/vN/` layout, the mapping for the 27 existing notebooks, what changes if a decision goes the other way, and what the CPU-only host adds. |
| [`CONTRACTS.md`](CONTRACTS.md) | The seven contracts, the contract-first change flow with three worked examples, the rules for parallel work, and the checks. |
| [`BRANCHING.md`](BRANCHING.md) | Trunk-based development on a protected `main`, the merge-queue reality for this repository, the ruleset, the pull request template, commit and release rules, code owners, and parallel agent worktrees per tool. |
| [`CI_CD.md`](CI_CD.md) | The pipeline job by job with path filters and the single required check, the database tests to write first, the two AI gates and a CPU latency job, images without PyTorch, security scanning, deployment to a CPU-only Contabo server with SeaweedFS as the object store, precomputed heavy work for the single-user demonstration, backups with a restore drill, and preview environments. |
| [`DEV_ENV.md`](DEV_ENV.md) | `make bootstrap` and `make doctor` for a person or an agent, toolchain pinning, the local stack, seed data, worktrees, Kaggle, secrets, and troubleshooting. |
| [`DOCS_SYSTEM.md`](DOCS_SYSTEM.md) | The documentation set with owners and freshness rules, decision records, feature specs, the evidence documents (including the requirements ledger), runbooks, and where each blueprint file lands. |
| [`REPO_CLEANUP.md`](REPO_CLEANUP.md) | Every current path with keep, move, add, replace or delete and the reason; what is never deleted; the three-phase order of work. |

How to read it: start with the main report. Its section 1.1 lists the thirteen decisions, and each one
names the file here that carries the detail.

Conventions used in every file:

- ⚠ marks a row that a Day-0 decision record still has to fill.
- Quotations in "double quotes" with a URL in the Sources list were read from that page on
  25 November 2026. Statements about this repository come from `git`, `gh` and the files
  themselves, and say so.
- The report's identifiers are reused as they are: `D-01`…`D-10` (Section 3.3, Table 3-39),
  `FR-*`, `NFR-*`, `IR-*` (Section 3.2), `F1`…`F6`, `UC-01`…`UC-10`. `INV-1`…`INV-9` are this
  blueprint's invariants.
- Target times, sizes and limits marked as targets are to be measured on Day 0, not promises.
