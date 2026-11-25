# DOCS_SYSTEM.md — the documentation set, its owners, and how it stays true

Part of the Engineering Specialist F blueprint (`docs/architecture/debate/eng_specialist_glm/`).

## 1. Why this is a system and not a folder

The repository had 96 Markdown files when this blueprint started (53 tracked on `main`, the rest
the architecture debate). Three proposals in that debate describe three different architectures.
The root `README.md` describes a package that `main` deleted in October. The frontend README points
to a document that does not exist (`docs/FRONTEND_ARCHITECTURE.md`). A new reader, human or agent,
cannot tell which file is current.

One vision and one track need the opposite: every statement has **one place**, that place has
**one owner**, and a reader can tell whether it is **true, proposed or historical**. Three rules
produce that:

1. **One job, one owner, per document.** A document that two people may change is changed by
   nobody in particular.
2. **Generate what can be generated; check what cannot.** A table that a script can write is
   never typed.
3. **Decisions are records.** A choice made in a chat is not a decision. A choice made in a
   decision record is the only kind an agent may rely on.

## 2. The set

Status legend: **current** (true now), **proposed** (intended; written as proposed),
**historical** (kept as evidence; never a basis for new work).

### 2.1 Root (the first screen a visitor sees)

| File | Job | Owner | Status | Stays true by |
|---|---|---|---|---|
| `README.md` | What, why, who, the four commands, where to go next | repo owner | current | `docs` CI job checks its commands against `make help` |
| `VISION.md` | One page: the product, the users, the features F1–F6, the invariants INV-1…INV-9, the limits | Person 1 with the team | proposed | changes only with the report's Chapter 1 wording |
| `ARCHITECTURE.md` | The system in one diagram and 40 lines; links to the decision records and to `docs/architecture/repository-layout.md` | repo owner | current | links checked; diagram regenerated from the Compose files |
| `AGENTS.md` | The operating contract for agents (draft: [`AGENTS.md`](AGENTS.md)) | repo owner | current | `make agents-check` |
| `CONTRIBUTING.md` | How a person proposes, branches, reviews, releases; summarises `docs/guides/branching.md` | repo owner | current | reviewed with BRANCHING changes |
| `SECURITY.md` | How to report a problem; what is in scope for a research prototype | repo owner | current | reviewed each semester |
| `CHANGELOG.md` | What changed in each release | release-please | current | generated |
| `LICENSE` | MIT | repo owner | current | never |

### 2.2 `docs/`

| Path | Job | Owner | Status | Stays true by |
|---|---|---|---|---|
| `docs/README.md` | The map: "where do I write X?", one row per document type | repo owner | current | `docs` CI job: every row resolves, every `docs/` top-level folder is listed |
| `docs/adr/` | Decision records, `NNNN-slug.md`, with `README.md` as the index | one owner per record | current or superseded | `make gen` copies the index into `AGENTS.md`; frontmatter checked |
| `docs/architecture/repository-layout.md` | The target tree and the forbidden-here rules (REPO_TREE.md) | repo owner | current | a test that every top-level folder is described |
| `docs/guides/branching.md` | BRANCHING.md, adapted to the repository | repo owner | current | reviewed when the ruleset changes |
| `docs/guides/agent-files.md` | AGENT_FILES.md: which agent files exist and how they stay in sync | repo owner | current | reviewed with `make agents-check` changes |
| `docs/guides/dev-environment.md` | DEV_ENV.md | infra owner | current | `make bootstrap` on a clean machine after each change |
| `docs/testing.md` | Test strategy, layers, the invariant catalogue INV-1…INV-8 → test names | database owner and API owner | current | `make trace` fails if a named test is missing |
| `docs/requirements/requirements.yaml` | The 161 requirement IDs of Section 3.2 with status and evidence | Person 4 | current | extracted once from the report; changed only with Section 3.2 |
| `docs/requirements/trace.md` | Requirement → tests → design element → prototype evidence | generated | current | `make trace` |
| `docs/ai/evaluations.md` | The table of record: every reviewed run's metrics with run id, commit and hashes | AI owner | current | generated from `kaggle/**/metrics.json` and `runs/*.json` |
| `docs/ai/model-cards/<family>-vN.md` | Intended use, data, metric of record, limits, failure examples | AI owner | current | generated from `kaggle/<feature>/vN/model_card.md` on promotion |
| `docs/runbooks/*.md` | Deploy, rollback, backup restore, model promotion, secrets rotation, first thirty minutes of an outage | infra owner | current | `last-tested` date in frontmatter; the `docs` job warns after 90 days |
| `docs/research/` | Paper lists, Tier 1 summaries, simulation research, earlier analyses | Person 2 | historical or proposed | not a basis for build decisions; a banner says so |
| `docs/superpowers/specs/` | The approved database and ERD design (existing path) | database owner | current | changed only with a decision record |
| `docs/database/` | The generated ERD, its overview page, and Mahmoud's ERD (moved from `mahmoudERD/`) | database owner | current | `database/tools/generate_drawio_erd.py` after each migration |
| `docs/brand/` | Identity pack, tokens, app icons | repo owner | current | as needed |
| `docs/architecture/debate/` | The November 2026 architecture debate | repo owner | historical | never edited; cited by the report's design rationale |
| `docs/archive/` | Superseded documents with a banner and a pointer to the replacement | repo owner | historical | never edited |

### 2.3 The graduation report (a track of its own)

| Path | Job | Owner |
|---|---|---|
| `docs/documentation/` | The Project I report: `main/`, `skeleton/`, `chapter5/` sources, `build_docx.py` | Person 6 assembles; chapter owners as in the root `AGENTS.md` ownership table |
| `docs/documentation/AGENTS.md` | The report's working rules. **This is the current root `AGENTS.md`, moved without changes.** | Person 6 |
| `docs/team-plan/` | Ownership, plans, the review folder, the editorial tracker | Person 6 |

Two rules keep the tracks from contaminating each other:

- **Build documents never cite the report as their authority.** The report says what is proposed;
  the repository shows what exists. When the two differ, the repository is the fact and the report
  gets a row in the editorial tracker.
- **The report cites the repository for evidence.** A figure, a metric or a screenshot in Chapter 4
  or 5 names the commit, the workflow run or the `kaggle/` run id it came from.

### 2.4 Next to the code

`contracts/README.md` is the contract-first workflow (CONTRACTS.md). `infra/README.md` is the
pipeline and deployment guide (CI_CD.md). `database/README.md` stays. Every nested `AGENTS.md` is
listed in AGENT_FILES.md.

## 3. Decision records (`docs/adr/`)

**Format.** Nygard's five parts (Title, Status, Context, Decision, Consequences) with MADR's YAML
frontmatter so a script can read the status. Nygard: "The whole document should be one or two
pages long", "All consequences should be listed here, not just the 'positive' ones", and "If a
decision is reversed, we will keep the old one around, but mark it as superseded." MADR names files
`NNNN-title-with-dashes.md`.

```markdown
---
status: proposed        # proposed | accepted | deprecated | superseded by ADR-NNNN
date: 2026-11-26
deciders: [<names>]
consulted: [<names>]
informed: [<names>]
satisfies: [D-02, NFR-RL-04]     # report identifiers, when the decision appears there
---
# NNNN. Short title

## Context and Problem Statement
## Decision Drivers
## Considered Options
## Decision Outcome
### Consequences        (good and bad)
## Pros and Cons of the Options
## More Information
```

**Rules.**

- Numbers are never reused. An accepted record is never edited; it is superseded by a new one
  that links back.
- An agent may draft a record and must never accept one. `status: accepted` requires a named human
  in `deciders`.
- A record answers one question and names the alternative it beat, because that is exactly what
  the report's Table 3-39 needs ("Decision, Alternative considered, Reason and trade-off").
- The index (`docs/adr/README.md`) is generated into `AGENTS.md`, so every agent sees the current
  decisions without opening a file.

**Day 0: the records to accept before any code.** These are the questions on which the three
architecture proposals disagree or stay silent. Each gets a 30-minute slot, one owner and a record
written in the meeting.

| ADR | Question | What the repo already says |
|---|---|---|
| 0001 | One repository, contract-first | three proposals agree |
| 0002 | Core backend language and framework | `frontend/packages/api/README.md` and `frontend/tooling/README.md` generate types from FastAPI's `/openapi.json`; two of three proposals choose Python; the platform plan chooses NestJS |
| 0003 | AI serving: CPU inference with ONNX Runtime or OpenVINO, one container per model family behind an HTTP API | the owner's requirement and the owner's CPU-only constraint; `cpu_demo_feasibility.md` measured it as feasible; the framework around the runtime is open |
| 0004 | Job queue and live-update transport | `15_security.sql` says "Celery"; the report says a database job table with a skipping lock; the proposals add Redis, NATS, an event log |
| 0005 | Object storage: the S3 API is the contract; the store is replaceable | the design documents name MinIO, whose repository is archived; `cpu_demo_feasibility.md` and `redteam_glm.md` recommend replacing it (CI_CD.md names SeaweedFS, with RustFS as the alternative) |
| 0006 | Map engine and tile serving | the report names CesiumJS; the reviews disagree |
| 0007 | Offline synchronisation protocol | "the protocol is a separate design" (ERD specification, section 9) |
| 0008 | Migrations are plain, forward-only SQL | CONTRACTS.md |
| 0009 | `AGENTS.md` is the single agent guide | AGENT_FILES.md |
| 0010 | Branch protection and the merge-queue substitute | BRANCHING.md |

Until a record is accepted, the root `AGENTS.md` shows it as ⚠ proposed and agents treat the
question as closed for debate and open for a decision.

## 4. Feature specs (`specs/`)

A spec says **what and why**, before anyone decides how. GitHub Spec Kit gives the team one
process across all its agents: "Spec Kit is an open source toolkit that gives AI coding agents
structured processes, reusable templates, and documented outcomes", and defines its method as
"Define what to build and why, then turn the specification into a plan, tasks, and working code".
It needs "Python 3.11+, uv, and a supported AI coding agent" and is already installed at user scope
on the owner's machine.

- `specs/NNNN-slug/spec.md`: the requirement in plain words, acceptance scenarios, the requirement
  IDs it serves.
- `specs/NNNN-slug/plan.md` and `tasks.md`: how, and in what order.
- `.specify/memory/constitution.md`: the project principles the specs are checked against. Its
  content is the invariant table of `AGENTS.md` plus the boundaries and the testing rules.
  Spec Kit's constitution command exists for exactly this: "Create principles focused on code
  quality, testing, and maintainability."

**When a spec is required.** A new capability, a change to a contract, anything that crosses two
folders, anything an agent will build without a person watching. **When it is not.** A typo, a
one-line fix, a dependency bump, a document correction. Root `AGENTS.md` section 7 states the
rule; the pull request template links the spec.

A model experiment has its own kind of spec: the experiment card `kaggle/<feature>/vN/README.md`
(hypothesis, change from the previous version, metric that decides).

## 5. Evidence documents

These are generated. Nobody types a number into them.

| Document | Generated from | Used by |
|---|---|---|
| `docs/requirements/trace.md` | `requirements.yaml`, test markers (`req`), spec folders, `docs/` links | Chapter 5's discussion; the examiner's question "how do you know it works?" |
| `docs/ai/evaluations.md` | every `kaggle/**/metrics.json` whose run is `scientifically_reviewed` | Chapter 4 and 5; the model card |
| `docs/ai/model-cards/*.md` | `kaggle/<feature>/vN/model_card.md` at promotion | the report's appendix; the AI service's `/v1/model-info` |
| `docs/database/` ERD and overview | the live database catalogue | Section 3.3; the appendix data dictionary |
| `CHANGELOG.md` | squash commits | releases |
| API reference | `contracts/openapi/core-api.json` | web and mobile developers |
| the decision index in `AGENTS.md` | `docs/adr/` | every agent |

**The requirements ledger.** Section 3.2 has 161 requirement IDs and the team's own review asks
for "a way a future reviewer could judge whether it is met" (review item M2). The ledger answers
it:

1. `tools/extract_requirements.py` reads `docs/documentation/main/Project 1 Docs.source/` once
   and writes `requirements.yaml`: id, text, priority, actor. Person 4 approves that pull request.
2. A test that proves a requirement carries its ID: `@pytest.mark.req("NFR-PF-04")` on a pytest
   test, or `{ tag: ["@req(NFR-PF-04)"] }` in a Playwright test's options.
3. `make trace` writes `trace.md`: for each ID, the tests that claim it, the spec that covers it,
   and one of four states: **no evidence**, **tested**, **verified in staging**, **demonstrated**.
   An ID without a test is listed as "no evidence", in every report chapter that cites it.
4. CI fails on an unknown ID in a marker and regenerates `trace.md`.

This is how the report's rule "do not invent screenshots, experiments or results" becomes a check
instead of an intention.

## 6. Runbooks (`docs/runbooks/`)

| Runbook | Must contain | Proven by |
|---|---|---|
| `deploy-staging.md` | trigger, steps, how to read a failure | a deploy per merge |
| `deploy-production.md` | pre-checks, approval, post-deploy smoke | each release |
| `rollback.md` | image rollback by digest; what is never rolled back (the schema) | a rehearsal before the first field exercise |
| `backup-and-restore.md` | schedule, where backups are, the restore steps | the monthly `restore-drill` workflow run |
| `promote-a-model.md` | the promotion gate, the pull request, activation, rollback to the previous bundle | each promotion |
| `run-the-demo.md` | the evening before (`make demo-precompute`), the morning of (`make demo-verify`, `DEMO_FREEZE=1`), the live steps on the CPU-only server, and what to say about each precomputed result | each rehearsal |
| `rotate-secrets.md` | age keys, database passwords, tokens | once per semester |
| `first-thirty-minutes.md` | what to check, in order, and who to call | a game day |

Every runbook has frontmatter with `last-tested: YYYY-MM-DD` and `tested-by:`. A runbook not
tested for 90 days gets a warning in the `docs` CI job and on `make docs-check`.

## 7. How documentation stays in sync

| Mechanism | What it covers | Where it runs |
|---|---|---|
| generate | trace matrix, evaluations, model cards, ERD, changelog, API reference, decision index, agent adapters | `make gen` |
| check | stale generated files, broken links, missing sections in a nested guide, a rule naming a command that does not exist, a metric in `docs/` without a run id | `make check`, `docs` CI job |
| own | every document has an owner in the table above and in `CODEOWNERS` | pull request review |
| ask | the pull request template: "Documentation: updated `<paths>` / not needed, because …" | every pull request |
| date | runbooks carry `last-tested` | `make docs-check` |
| review | a 30-minute "guide diet" each month for `AGENTS.md` and its nested files; a documentation day at each semester break | the team calendar |

Three habits do more than all of it:

- **Update the document in the pull request that makes it necessary.** Not in a later one.
- **Delete a document when it stops being true.** An outdated file with a reader is worse than no
  file. Move it to `docs/archive/` with a banner if it is evidence.
- **Say "proposed" until it is verified.** It is the report's rule and it is the repository's.

## 8. Writing rules (for every document in the repository)

Taken from the team's own checklist for the report (Person 6's plan), so that code documentation
and the report share one voice:

- One idea per paragraph. Plain academic or plain technical English, no marketing words: avoid
  "delve", "crucial", "pivotal", "seamless", "robust", "leverage".
- A claim with a number names its source or its run.
- Proposed behaviour is written as proposed: "is designed to", "shall", "is proposed".
- A heading says what the section decides or describes.
- A file is as short as its job allows: `VISION.md` one page, an ADR one or two pages, a nested
  `AGENTS.md` under 80 lines.

Optional, once the report is stable: a Vale style that encodes the same list, run on `docs/` by
`make docs-check`.

## 9. Where this blueprint lands

| Blueprint document | Becomes, in the repository |
|---|---|
| `AGENTS.md` | root `AGENTS.md` (after the ⚠ rows are filled) |
| `AGENT_FILES.md` | `docs/guides/agent-files.md`, plus the nested files it lists |
| `REPO_TREE.md` | `docs/architecture/repository-layout.md` |
| `CONTRACTS.md` | `contracts/README.md` and `contracts/AGENTS.md` |
| `BRANCHING.md` | `docs/guides/branching.md`; `CONTRIBUTING.md` summarises it |
| `CI_CD.md` | `infra/README.md` and `infra/AGENTS.md` |
| `DEV_ENV.md` | `README.md` (the quick start) and `docs/guides/dev-environment.md` |
| `DOCS_SYSTEM.md` | `docs/README.md` (the map) and `docs/AGENTS.md` |
| `REPO_CLEANUP.md` | executed in three phases, then kept as `docs/archive/repo-cleanup-2026-11.md` |

## Sources

Checked on 25 November 2026.

- Michael Nygard, "Documenting Architecture Decisions":
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- MADR (Markdown Any/Architectural Decision Records): https://adr.github.io/madr/
- GitHub Spec Kit: https://github.com/github/spec-kit
- Repository facts: the 96 Markdown files present when this blueprint started (53 tracked on
  `main`); the review items in
  `docs/team-plan/review/` (M2 on verification methods); `docs/superpowers/specs/2026-11-23-rescuevision-database-erd-design.md`
  (section 9, on the offline protocol); `database/schema/15_security.sql` ("Celery").
