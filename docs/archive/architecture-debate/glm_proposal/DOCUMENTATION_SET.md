# The documentation set

*Draft blueprint. It lists every Markdown file the repository should have, with an outline of each, and the rules that keep the documents true. The purpose: six people and any number of AI coding agents build from the same documents, and a check fails when a document and the code disagree.*

## 1. Principles

1. **One source per truth.** Each fact lives in exactly one file. Other files link to it. A duplicated fact is a future contradiction.
2. **Written for two readers.** A person new to the project, and an AI coding agent with no memory. Both need the same things: what this is, where things are, what I may change, how I check my work.
3. **Short on purpose.** A root document is a map, not a book. Details live in the folder they describe.
4. **Instructions sit next to the code they govern.** Every top-level folder has a `README.md` (what and why) and an `AGENTS.md` (rules for working there). The AGENTS.md convention recommends exactly this for monorepos: agents "automatically read the nearest file in the directory tree, so the closest one takes precedence" [B50].
5. **Generated where possible, checked always.** What can be generated is generated (contract snapshots, the ledger, the ERD, the folder map). What is written by hand is checked in CI.
6. **Changed with the code.** A pull request that changes behaviour changes the document in the same pull request.

## 2. The map

| Document | Reader | Purpose | Draft in this blueprint |
| --- | --- | --- | --- |
| `README.md` | Everybody, first | What RescueVision is, five-minute start, where to read next | Outline below |
| `VISION.md` | Everybody | One page: the product story and the principles | `VISION.md` |
| `ARCHITECTURE.md` | People and agents who build | The system and its decisions | `ARCHITECTURE.md` |
| `AGENTS.md` (root) | AI coding agents, and people who review them | How to work in this repository | `AGENTS.md` |
| `CONTRACTS.md` | People and agents who change an interface | Index of contracts and the rules | `CONTRACTS.md` |
| `TESTING.md` | People and agents who write a change | What must be proven, and how | `TESTING.md` |
| `CONTRIBUTING.md` | People | Setup, branches, pull requests, review | From `BRANCHING.md` |
| `SECURITY.md` | Everybody; outsiders who find a problem | Security model in brief; how to report | Outline below |
| `THIRD_PARTY_NOTICES.md` | Owner, lawyers, examiners | Licence register | Outline below |
| `<folder>/README.md` | Anybody who opens the folder | What lives here, why, how to run it | Outline below |
| `<folder>/AGENTS.md` | Agents working in the folder | Rules, commands, definition of done for that folder | §7 below |
| `docs/README.md` | Everybody | Index of the deeper documentation and reading paths | Outline below |
| `docs/adr/README.md` and `docs/adr/NNNN-title.md` | People and agents who need a decision | Architecture decision records | §6 below |
| `docs/architecture/*.md` | People and agents who build that part | Deep dives: live channel, offline sync, hazard engine, security model, database design, API guidelines, map architecture | Outlines below |
| `docs/runbooks/*.md` | Whoever operates the server | Step-by-step procedures | Outlines below |
| `ai/training/LEDGER.md` | Everybody on the AI side | Every model version and its status | `AI_TRAINING_LAYOUT.md` §6 |
| `ai/training/<feature>/README.md` | People and agents on that feature | The feature's problem, data, metric and history | Outline below |
| `ai/training/<feature>/vN/MODEL_CARD.md` | Reviewers, examiners, future users of the model | What one model version can and cannot do | `AI_TRAINING_LAYOUT.md` §4 |
| `specs/README.md` | Everybody | The single track: the order of work | Outline below |
| `specs/<feature>/spec.md`, `plan.md`, `tasks.md` | People and agents who build the feature | What, how, and in which steps | `BRANCHING.md` §10 |
| `docs/research/README.md` | People writing the AI side or the report | Background: papers, datasets, earlier analyses | Outline below |
| `docs/documentation/AGENTS.md` | Agents helping with the graduation report | The current report rules, moved from the root. The report folder stays where it is | Existing content |

## 3. Outlines

### `README.md`

1. One paragraph: what RescueVision is, with a link to `VISION.md`.
2. A picture: the map with an alert.
3. Five-minute start: `make setup`, `make dev`, open the console, sign in with the demo account.
4. What is in the repository: the eight top-level folders in one table each.
5. Where to read next, by role: I want to use it, build in it, train a model, deploy it, write the report.
6. Status: which milestone the repository is in, linked to `specs/README.md`.
7. Licence.

### `SECURITY.md`

1. The security model in ten lines: one database, access decided inside it, AI proposes and people decide.
2. What is sensitive: citizen phone numbers, responder positions, imagery.
3. The rules that protect it, each linked to where it is enforced and tested.
4. How to report a vulnerability, and what happens next.
5. What is explicitly out of scope for this demonstration.

### `THIRD_PARTY_NOTICES.md`

A table: component, version, licence, where it is used, what the licence requires of us. The AGPL components (OpenDroneMap, NodeODM, Ultralytics if used) get a line explaining that they run as separate, unmodified services. It is generated from the dependency lists and the image scans where possible.

### `<folder>/README.md` (the same outline everywhere)

1. What lives in this folder, in two sentences.
2. Why it is a separate folder: what it owns and what it must not do.
3. How to run its tests and its tools.
4. The main files and folders, one line each.
5. Where to read more.

### `docs/README.md`

1. The documentation map in one page.
2. Reading paths (§4).
3. How to add a document, and where it goes.
4. How documentation is checked.

### `docs/architecture/*.md`

| File | Covers |
| --- | --- |
| `database-erd-design.md` | The approved database design (moved from its current place) |
| `live-channel.md` | Outbox, notification, the listener connection, authorisation at send time, resume by sequence |
| `offline-sync.md` | The operation queue, idempotent replay, conflict rules, the SMS fallback |
| `hazard-engine.md` | The rules, the privilege path, the transaction, the dry-run mode |
| `security-model.md` | Roles, row-level security, tokens, job tickets, upload checks |
| `api-guidelines.md` | Naming, filtering, pagination, errors, versions |
| `map-and-3d.md` | Tile sources, layers, the scene store, 3D rendering in the browser |

Each one states the problem, the decision, the mechanism and the tests that protect it.

### `docs/runbooks/*.md`

| Runbook | Covers |
| --- | --- |
| `deploy.md` | What a deployment does, how to watch it |
| `rollback.md` | Undo a deployment, a migration or a model version |
| `backup-and-restore.md` | What is backed up, where, and the full restore procedure with its timing |
| `model-rollback.md` | Reverting to the previous model version |
| `rotate-secrets.md` | Replacing each secret without downtime |
| `bench.md` | Running the CPU benchmark on the server and recording the result |
| `demo-day.md` | The hour before a demonstration: checks, the replay command, what to do if something fails |

Every runbook is a numbered list of commands that has been executed exactly as written.

### `ai/training/<feature>/README.md`

1. The problem the feature solves for the product, and which serving container uses it.
2. The datasets and the metric, with the floor from the policy.
3. The CPU budget for the task.
4. The history: one short paragraph per version, with a link to the folder.
5. What to try next, as hypotheses, not promises.

### `specs/README.md`

1. The milestones from `ARCHITECTURE.md` §11, with their exit criteria.
2. One table of features: name, milestone, status, links to `spec.md`, `plan.md`, `tasks.md`.
3. The rule for starting work: specify, plan, tasks, then implement.

## 4. Reading paths

| If you are… | Read, in this order |
| --- | --- |
| A person, on the first day | `README.md` → `VISION.md` → `ARCHITECTURE.md` → `CONTRIBUTING.md` → the `README.md` of the folder you will work in → `specs/README.md` |
| An AI coding agent, before the first task | `AGENTS.md` → the `AGENTS.md` of the folder named in the task → the task's `spec.md` and `tasks.md` → the part of `ARCHITECTURE.md` the task touches |
| A reviewer | `CONTRIBUTING.md` → `TESTING.md` §3 → the pull request's linked specification |
| Whoever operates the server | `HOSTING_CONTABO.md` content in `docs/runbooks/` → `CI_CD.md` content in `docs/runbooks/deploy.md` |
| Whoever trains a model | `ai/AGENTS.md` → `ai/training/README.md` → `AI_TRAINING_LAYOUT.md` content in `ai/training/README.md` |
| Whoever writes the graduation report | `docs/documentation/AGENTS.md` |

## 5. How the documents stay true: `make docs-check`

| Check | What fails |
| --- | --- |
| Links | A link to a file or heading that does not exist |
| Required files | A top-level folder without a `README.md` and an `AGENTS.md`; a version folder without a model card |
| Commands | A `make …` command written in a document that the Makefile does not know |
| Folder map | The list of folders in `AGENTS.md` compared with the real tree |
| Contracts of words | A table named in `ARCHITECTURE.md` that the schema does not have; a service named there that Compose does not define |
| Decision records | A number used twice; an accepted record edited in a pull request |
| Model cards | A required heading missing |
| Stale markers | A `TBD` older than the date next to it |
| Size | A root document above its length limit, which is a sign that detail should move into a folder |

## 6. Decision records

A decision record is one page that answers: what did we decide, what were the alternatives, why this one, and what are the consequences. One is written when a choice is hard to undo or would surprise a newcomer: the architecture style, the queue, the object store, the runtime, the branching model.

The process is small: propose in a pull request with the status "proposed"; accept in the same pull request or a later one by changing the status to "accepted"; never edit an accepted record. To change a decision, write a new record that supersedes the old one and add a line to the old one pointing forward. The four questions in this section are the template; `docs/adr/README.md` repeats them.

## 7. What goes into an `AGENTS.md`, and what does not

| Belongs | Does not belong |
| --- | --- |
| What this folder owns and what it must never do | Tutorials and explanations that belong in `README.md` |
| The exact commands to run, check and build | Commands that do not exist yet |
| The boundaries: what may import what, which tables, which contracts | A copy of the root rules |
| The tests a change here must bring | General testing theory |
| The definition of done for this folder | Task lists, which live in `specs/` |
| The three mistakes most often made here | Personal notes |

Length limit: the root `AGENTS.md` is under 170 lines and a folder file is under 60. `make docs-check` fails above them. A file that reaches its limit is carrying detail that belongs in the document that owns it.

## 8. Files to write first

In Milestone 0, in this order, because everything else links to them: `VISION.md`, `ARCHITECTURE.md`, root `AGENTS.md`, `README.md`, `Makefile`, the eight folder `README.md` and `AGENTS.md` files, `docs/README.md`, `specs/README.md`, the first decision records. The drafts in this blueprint are the starting text.
