# Branching and workflow

*Draft blueprint for `CONTRIBUTING.md` and the branch rules in GitHub. It covers the branch model, naming, protection rules, pull requests, commits, releases and versioning, and how AI coding agents work on branches and worktrees without putting the repository at risk.*

## 1. The model: trunk-based development

- **`main` is always releasable.** Every commit on `main` has passed the full pull-request pipeline and can be deployed to staging, which happens automatically.
- **Branches are short-lived.** A branch lives for hours or days, never weeks. It exists to deliver one small change.
- **Changes are small.** A pull request that is easy to review is one that fits in one sitting.
- **Unfinished work does not sit on a branch.** A feature that takes longer is merged in pieces behind a flag or as an unused module.

This is the "short-lived feature branches" style. The trunk-based development site [B48] has sections with that title and with the title "Trunk-Based Development For Smaller Teams". GitFlow, with its long-lived develop and release branches, adds ceremony that a team of six with continuous deployment does not need. If a sustained maintenance period with several supported versions ever begins, a release branch can be added then.

## 2. Branch names

```
<type>/<scope>-<short-summary>
```

| Part | Values | Examples |
| --- | --- | --- |
| `type` | `feat`, `fix`, `perf`, `refactor`, `test`, `docs`, `infra`, `ai`, `spec`, `chore`, `exp` | `feat`, `fix`, `ai` |
| `scope` | The area: `backend`, `web`, `mobile`, `citizen`, `db`, `contracts`, `ai-damage`, `ai-people`, `ai-hazard`, `ai-embed`, `deploy`, `ci`, `docs`, `repo` | `web`, `db`, `ai-damage` |
| `short-summary` | Two to five words, lower case, hyphenated | `alert-banner`, `rls-matrix` |

Examples: `feat/web-alert-banner`, `fix/db-hazard-engine-privilege`, `ai/ai-damage-v4`, `docs/adr-live-channel`, `exp/ai-people-edge-cascade`.

`ai` is for training versions and serving changes. `spec` is for specification work. `exp` marks an experiment that is not meant to be merged as it is.

People and agents use the same names. A reader should not need to know who or what wrote a branch.

## 3. Rules on `main`

Configured once as a GitHub ruleset [B42] or as classic branch protection [B41]:

| Rule | Setting | Why |
| --- | --- | --- |
| Changes to `main` | Only through a pull request | Every change is seen by a second pair of eyes |
| Required status check | `check` (the single job that summarises the pipeline) | One name to maintain; CI decides what it includes |
| Approvals | One, and a code owner's review for protected paths | Knowledge stays with the people who own an area |
| Protected paths (`CODEOWNERS`) [B43] | `database/schema/`, `database/migrations/`, `contracts/`, `deploy/`, `.github/workflows/`, `ai/registry/`, `docs/adr/`, `AGENTS.md` | These files can break everything or change what agents are told |
| History | Linear. Squash and merge | One change, one commit, a readable history |
| Force pushes and deletions | Blocked | History is shared |
| Conversation | All review threads resolved before merging | A question left open is a decision not taken |
| Up to date | The branch must be current with `main` before merging | The pipeline result is for the code that merges |
| Linked work | The description names a task in `specs/` | Nothing lands that was not asked for |

## 4. Pull requests

**Title**: a Conventional Commits line, for example `fix(db): let a field report trigger the hazard engine`. It becomes the commit message on squash, and commitlint [B52] checks the format.

**Description** answers four questions in order:

1. **What changes**, in one or two sentences.
2. **Why**, with the task or issue it closes.
3. **How it was tested**, naming the tests from `TESTING.md` §3.
4. **What can go wrong and how to undo it.**

**Size**: aim for a few hundred changed lines. Larger changes are split into a series of pull requests, each one useful on its own.

**Agent-made pull requests** add two lines: which tool wrote the change, and which specification it followed. They carry the label `ai-assisted`. A person reviews every line as if a colleague had written it.

## 5. Commits

- Conventional Commits format, as enforced by commitlint [B52]. (The specification's own site could not be reached from the author's machine while this was written, so the tool's documentation is the reference.)
- The subject is an imperative sentence of at most 72 characters. The body explains why.
- Trailers link the work: `Refs: RV-<feature>-<task-number>`, and `Assisted-by: <tool>` when an agent contributed.
- Commits on a branch may be untidy. Squash and merge turns them into one clean commit.

## 6. Releases and versioning

| Thing | Scheme | Example |
| --- | --- | --- |
| The product | Semantic versioning [B51], tags `vX.Y.Z` | `v0.3.0` |
| Pre-releases (optional) | Suffix | `v0.4.0-rc.1` |
| Images from `main` | Commit SHA and `edge` | `api:a1b2c3d`, `api:edge` |
| Images from a release | `X.Y.Z` and `X.Y` | `api:0.3.0` |
| A model version | Tag `model-<feature>-v<N>` | `model-damage-assessment-v3` |
| An AI serving image | Feature, version, commit | `infer-damage:damage-assessment-v3-a1b2c3d` |
| Database migrations | Timestamp prefix | `20261201120000_add_detection_review.sql` |

Until the first public demonstration the product version stays below 1.0. Breaking changes are allowed in a 0.x series but still need a decision record.

## 7. Hotfixes

1. Branch from the affected release tag: `fix/<scope>-<summary>`.
2. Open a pull request against `main`. It passes the same pipeline.
3. After it merges, tag the next patch version from `main` and deploy it.
4. Only if `main` already contains changes that must not be released yet, create a temporary `release/x.y` branch from the tag, cherry-pick the fix, and tag from there. Delete the branch after the release.

## 8. Long work and experiments

- **A long feature** is merged in steps. Each step is a pull request that keeps `main` working, possibly behind a flag or as code that nothing calls yet.
- **An experiment** lives on an `exp/` branch and, for model experiments, in a version folder. It is not merged until it becomes a real change.
- **A stale branch** is deleted. Branches are removed automatically after their pull request merges. A pull request with no activity for two weeks is closed with a comment; reopening it is cheap.

## 9. How AI coding agents work safely

Agents work exactly like people: on a branch, through a pull request, never on `main`. The difference is that several agents may work at the same time, so each one gets its own **worktree**.

### Worktrees

A Git worktree [B49] is a second checkout of the same repository in another folder. Each agent gets one, so agents never share a working directory.

```bash
make wt NAME=feat/web-alert-banner     # create branch + worktree, install dependencies
make wt-sync                           # inside a worktree: bring it up to date with main
make wt-pr                             # inside a worktree: run make check, push, open the pull request
make wt-list                           # every worktree and its branch
make wt-remove NAME=feat/web-alert-banner
```

Rules for worktrees:

- Worktrees live outside the main clone, in `../rescuevision-wt/<name>`. The main clone stays on `main` and is used only for review and releases.
- One agent per worktree. One task per worktree.
- Each worktree has its own dependencies and its own Compose project name (`rv-<name>`), so two agents can run the stack at the same time on different ports.
- Each worktree uses its own database name, so tests never collide.
- Secrets are read from a folder outside the repository (`~/.config/rescuevision/`) and are never copied into a worktree.
- The target `make wt-pr` runs the complete check before pushing. If it fails, nothing is pushed.

### What an agent must never do

- Commit to `main`, merge its own pull request, or approve its own pull request.
- Force-push, rewrite the history of a pushed branch, or delete a branch it did not create. Rebasing its own unmerged branch is allowed.
- Touch another worktree.
- Run a destructive command on a shared database or a shared volume.
- Write a secret, a token or `kaggle.json` into the repository, or print one into a log.
- Deploy to staging or production, or change anything on the server.
- Weaken a test or a rule to make its change pass.
- Change `AGENTS.md`, the workflows, the deployment files or the schema without the task saying so.

### What an agent should do when the task is unclear

Stop and ask. The question goes into the task in `specs/`, or into the pull request as a comment. An agent that guesses and builds the wrong thing costs more than one that waits.

## 10. Where the work comes from

Every branch starts from a task in `specs/<feature>/tasks.md`. The task says what to build, where it lives in the architecture, and which tests prove it. The specification, the plan and the tasks are written and reviewed before implementation starts, in the same pull-request flow.

The sequence is **specify → plan → tasks → implement**. A task without a specification is a guess with a number.

## 11. Settings to apply in Milestone 0

1. Create the ruleset for `main` from the table in §3.
2. Create `CODEOWNERS` with the protected paths.
3. Enable the pull request template and the label `ai-assisted`.
4. Set squash and merge as the only merge strategy, with the pull request title as the default commit message.
5. Turn on automatic deletion of merged branches.
6. Add the commitlint check to `static`.
7. Choose how the version number is bumped (one version file is the simplest).
