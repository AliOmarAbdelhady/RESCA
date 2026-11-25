# BRANCHING.md — branches, protection, pull requests, commits, releases, parallel agent worktrees

Part of the Engineering Specialist F blueprint (`docs/architecture/debate/eng_specialist_glm/`).

## 1. Where the repository is today

Facts, read on 25 November 2026 (`git` and the GitHub API on `AliOmarAbdelhady/RescueVision`):

| Fact | Consequence |
|---|---|
| `main` has 30 commits from four authors. Four are merge commits; exactly one is a pull request (#1). The rest were merged or pushed locally. | A required pull request will be a new habit for most of the team. Keep it to one approval. |
| `main` is not protected (the API answers "Branch not protected"; the ruleset list is empty). There is no `.github/` directory, so there is no CI, no code owners and no pull request template. | Any agent in a worktree checked out on `main` can push to `main` today. This happened to be the state of the worktree this blueprint was written in. |
| The repository is public and owned by a personal account, not an organization. | GitHub's merge queue is documented for public repositories owned by an organization (and for private repositories on Team or Enterprise Cloud). It is not available here as it stands (section 4). |
| Branch names follow five different patterns: `AliOmarAbdelhady/database`, `docs/research-papers`, `feature/mapping-routing`, `mahmoudERD`, `codex/building-damage-v4`. | Naming cannot be the gate. Tools also name branches themselves (section 3). |
| `codex/building-damage-v4` is 24 commits ahead of `main` and 28 behind. It has never had a pull request. | Merge it first, on Day 0, before anything else branches from `main`. |

## 2. The model: trunk-based development

One long-lived branch, `main`, always releasable. Everything else is short-lived and merged by
squash.

- trunkbaseddevelopment.com describes the model as collaborating "on code in a single branch called
  'trunk'", asks teams to "commit to trunk at least once every 24 hours", and is blunt about the
  alternative: "Shared branches off mainline/main/trunk are bad at any release cadence."
- A branch lives **two days at most**. If the work is not finished, it is still merged behind a
  flag, split, or shrunk. A branch older than three days is rebased and reviewed the same day.
- No `develop`, no `release/*`, no long-lived `staging` branch. Staging is an environment that
  tracks `main`. Releases are tags.
- Work that is not ready is hidden by a flag or an empty UI state, not by a branch. The report's
  own rule applies: unfinished means visibly unavailable.

The trunk is protected by two things that do not depend on anybody's discipline: the ruleset in
section 5 and the single required check in CI_CD.md.

## 3. Branches

| Type | Name | Lives | Merges to |
|---|---|---|---|
| feature | `feat/<area>-<short-slug>` (`feat/web-offline-indicator`) | ≤ 2 days | `main` |
| fix | `fix/<area>-<short-slug>` (`fix/db-alert-restore-order`) | hours | `main` |
| contract | `feat(contracts)` or `feat(db)` titles on a `feat/` or `db/` branch | ≤ 1 day | `main` |
| database | `db/<short-slug>` | ≤ 1 day | `main` |
| AI experiment or promotion | `ai/<feature>-v<N>-<short-slug>` | ≤ 3 days | `main` |
| infrastructure and CI | `infra/<short-slug>` | ≤ 1 day | `main` |
| documentation | `docs/<short-slug>` | ≤ 1 day | `main` |
| report | `report/<person>-<short-slug>` | ≤ 3 days | `main` |
| experiment, never merged | `exp/<short-slug>` | any | nothing; deleted |
| hotfix | `fix/<area>-<short-slug>` from the release tag | hours | `main` |

`<area>` is one of the commit scopes in section 7.

**Naming is a convention, not a check.** The tools name branches themselves: Claude Code creates
"a new branch named `worktree-<name>`", and Orca pushes workspace branches as `<github-user>/<workspace>`.
So the gate is the **pull request title**, which becomes the commit message on squash. When you
choose a worktree name, use `feat-web-offline-indicator` so the generated branch still reads well.

## 4. Merging in order without a merge queue

A merge queue tests each pull request on top of the ones queued before it. GitHub's queue needs
`merge_group` in every workflow: "You **must** use the `merge_group` event to trigger your GitHub
Actions workflow"; without it, "The merge will fail as the required status check will not be
reported." It also "cannot be enabled with branch protection rules that use wildcard characters".

The workflows in CI_CD.md are written with `on: [pull_request, merge_group]` from day one. Until the
queue can be switched on, two settings give most of its benefit:

1. **Require branches to be up to date before merging** (strict status checks). A pull request
   cannot merge until it contains `main`'s tip and its checks passed on that commit.
2. **Auto-merge** (`gh pr merge --auto --squash`). The author enqueues once; GitHub updates the
   branch, re-runs the checks and merges when they pass.

Two options put a real queue in place; both take minutes:

- **Transfer the repository to an organization** (free for public repositories), then tick
  "Require merge queue" in the ruleset. Nothing in the workflows changes.
- **Or keep the account and add a third-party queue** (Mergify, Graphite, Aviator). Not
  recommended: a second system to learn for a six-person team.

## 5. Protection of `main` (one ruleset)

| Rule | Setting | Why |
|---|---|---|
| Restrict deletions | on | the trunk is not deleted |
| Block force pushes | on | history is not rewritten |
| Require a pull request before merging | on | no direct pushes, including repository admins |
| Required approvals | 1; "Dismiss stale pull request approvals when new commits are pushed" on | one human, on the final commit |
| Require review from Code Owners | on | contracts, database and agent configuration get their owner |
| Require status checks to pass | `ci/ok`, strict | one check, the same command as `make check` |
| Require conversation resolution | on | no open review thread |
| Require signed commits | off | agents and students sign inconsistently; not worth the friction |
| Require linear history | on | squash only |
| Allowed merge methods | squash only; "Automatically delete head branches" on | one conventional commit per pull request |
| Require branches to be up to date | on | section 4 |
| Bypass list | the Repository admin role only | for a broken ruleset, never for a broken build; every use is announced |

Apply the same ruleset to release tags (`v*`): no deletion, no rewrite.

## 6. The pull request

### 6.1 Template (`.github/PULL_REQUEST_TEMPLATE.md`)

```markdown
## What and why
<!-- One paragraph. Link the spec: specs/NNNN-slug/spec.md. -->

## Requirement IDs
<!-- FR-…, NFR-…, IR-…, UC-… that this change serves or proves. "none" is an answer. -->

## Contract changes
<!-- API, event, enum, migration, bundle. "none", or "breaking: …" -->

## Evidence
<!-- The exact command you ran and its result: `make check` output, a test name, a screenshot.
     If you could not run something, say so here. -->

## Documentation
<!-- Updated: <paths>. Or: not needed, because … -->

## Agent notes
<!-- Was this written by an agent? Did it repeat a mistake? Which rule or check did you fix? -->

## Checklist
- [ ] `make check` passes on this commit
- [ ] tests added or updated, requirement IDs tagged
- [ ] generated files regenerated (`make gen`), none hand-edited
- [ ] no secrets, datasets, weights or notebook outputs
- [ ] title is a Conventional Commit
```

### 6.2 Size and shape

- One concern per pull request. Target: 400 changed lines or fewer, not counting generated or
  moved files. A mechanical change across many files is split into several pull requests, the way
  Claude Code's `/batch` splits work "into 5 to 30 units".
- Generated files are committed in the same pull request as their source.
- The description is written for the reviewer, not for the author.

### 6.3 Review

- Approvals are human, and from someone other than the author. An agent's summary of its own work
  is not a review.
- A pull request written by an agent carries the `agent` label. Its reviewer reads the diff as if
  a new teammate wrote it: a contract pull request is reviewed by its interface, a build pull
  request by its tests and its evidence block.
- The reviewer's five questions: Does it do what the spec says? Is every claim in "Evidence"
  something that ran? Does it cross a boundary in `AGENTS.md` section 4? Is it small enough to
  understand? Is the matching document updated?
- A second agent session is a useful first pass and is never the approval. Claude Code's
  documentation puts it plainly: "A second session is also the easiest independent reviewer you
  can get."

## 7. Commits and titles

Squash merges turn the pull request title into the one commit on `main`, so the title must match
Conventional Commits:

```text
<type>(<scope>)!?: <imperative summary, at most 72 characters>
```

| Type | Use | Release |
|---|---|---|
| `feat` | a new capability | minor |
| `fix` | a bug fix | patch |
| `perf`, `refactor` | same behaviour, faster or cleaner | patch |
| `test`, `docs`, `ci`, `build`, `chore` | no behaviour change | none |
| `revert` | undo a merged change | patch |

Scopes: `api`, `worker`, `ai`, `kaggle`, `web`, `mobile`, `db`, `contracts`, `infra`, `docs`,
`report`. `!` marks a breaking change.

Examples, taken from defects the red-team review found:

```text
fix(db): let a Field Responder trigger hazard evaluation
feat(api)!: rename case status RESCUED to ON_SCENE
feat(contracts): add hazard report endpoint
ai(building-damage): record v4 full-coverage run
docs(adr): supersede ADR-0004 with the event log
report(ch4): map prototype figures to Section 3.2 identifiers
```

`tools/check_pr_title.py` runs in the `guard` CI job, so a wrong title fails `ci/ok` before a
reviewer spends time. Commit messages inside a branch are not checked; they are squashed away.

## 8. Releases

- **Versioning.** Semantic versions, `vX.Y.Z`, cut from `main`.
- **Automation.** release-please reads the squash commits and opens a release pull request that
  updates the version and `CHANGELOG.md`. Its README states the mapping (`feat` is a minor, `fix`
  a patch, `!` a major) and recommends exactly this flow: "We highly recommend that you use
  squash-merges when merging pull requests."
- **Images.** Every merge to `main` builds images tagged with the commit and pushes them to the
  registry. A release tag rebuilds with the version tag and a digest recorded in the release.
- **Deploy.** Staging follows `main`. Production follows a tag and an approval (CI_CD.md).
- **Model versions are not releases.** A model is versioned by its bundle and its experiment folder
  (`kaggle/<feature>/vN`), and promoted or rolled back by a change of `bundle.lock.json`, without
  a platform release.
- **Hotfix.** Branch from the tag, merge to `main` through a pull request, release `vX.Y.Z+1`.
  Never patch a tag.

## 9. Code owners

Report ownership is confirmed (root `AGENTS.md`). Code ownership is proposed here and must be
confirmed at the Day-0 meeting; GitHub handles other than the repository owner's are not known to
this blueprint and are marked `@<handle>`.

```gitignore
# .github/CODEOWNERS  (draft; one owner per path)

# Agent configuration and ownership are executable surfaces: the repository owner only.
/.claude/            @AliOmarAbdelhady
/.zcode/             @AliOmarAbdelhady
/.gemini/            @AliOmarAbdelhady
/.agents/            @AliOmarAbdelhady
/.github/            @AliOmarAbdelhady
/AGENTS.md           @AliOmarAbdelhady
/tools/agent_files.py @AliOmarAbdelhady

# Code (proposed)
/database/           @<db-owner>
/contracts/          @<api-owner>
/services/core-api/  @<api-owner>
/services/worker/    @<api-owner>
/services/ai/        @<ai-owner>
/ai/                 @<ai-owner>
/kaggle/             @<ai-owner>
/frontend/           @<web-owner>
/frontend/apps/mobile/ @<mobile-owner>
/infra/              @<infra-owner>

# Frozen evidence: corrections to README files only
/prototypes/         @AliOmarAbdelhady

# Graduation report (confirmed chapter ownership)
/docs/documentation/            @<mesbah>
/docs/documentation/chapter5/   @AliOmarAbdelhady
/docs/team-plan/                @<mesbah>
```

One owner per path, so "required" means one named person. The owner of a path wrote or maintains
it; the owner of a pull request asked that person to review it.

## 10. Parallel agents in worktrees

### 10.1 The rules

1. **One task, one worktree, one branch, one pull request.** Two agents never share a working
   directory.
2. **Let the tool create the worktree.** It puts it in the right place, names the branch and sets
   the base. Do not run `git worktree add` by hand inside a session that a tool manages.
3. **Bootstrap every new worktree** with `make bootstrap`, then `make doctor`. Claude Code's
   documentation says the same thing in its own terms: "A worktree is a fresh checkout, so
   initialize your development environment there." A fresh worktree has no `node_modules`, no
   virtual environment and no `.env`.
4. **One local stack per machine.** A second worktree uses `make check` (which starts throwaway
   containers on random ports) or its own Compose project name and ports (DEV_ENV.md).
5. **Rebase, do not merge `main` into the branch.** Before opening the pull request and after any
   conflict: `git fetch origin && git rebase origin/main`.
6. **Regenerate, do not hand-merge.** After a rebase that touches a lock file, an OpenAPI document,
   an enum file or a generated client: `make gen`, then commit the result. Two agents that changed
   the same contract both regenerate.
7. **Migrations are timestamped**, so two agents never collide on a number. Rebase and run
   `make db-reset` to prove the two migrations apply in order.
8. **Cap concurrency.** About four agents at once per person (Orca's own guidance: "up to about 4
   at once"). More than that and the queue of pull requests outgrows the reviewers.
9. **Finish or hand over.** A worktree with an open pull request is finished work. A worktree with
   no pull request after a day is a question to its owner, not a branch to build on.
10. **Never in a worktree:** `git push --force` to a shared branch, `git add -A` with untracked
    files you did not create, `git commit --no-verify`, or work in a worktree whose current branch
    is `main`. `make doctor` fails on the last one; the ruleset blocks the push.

### 10.2 What each tool does

| Tool | Starting a worker | Where the worktree goes | Branch it creates | Set-up hook |
|---|---|---|---|---|
| Orca | `orca orchestration worker-start --worktree new-child --name <short-name> --agent <agent>` | a child worktree under the current one; `new-top-level` for one without a parent | `<github-user>/<workspace>` (as observed: `AliOmarAbdelhady/team-review`) | `--setup run` can run the workspace setup; point it at `make bootstrap` |
| Claude Code | `claude --worktree feature-x` (or `-w`) | `.claude/worktrees/<name>/` | `worktree-<name>` | `.worktreeinclude` lists ignored files to copy; it "uses `.gitignore` syntax" and "copies rather than links" |
| Codex | local sessions in a folder the person chooses; cloud tasks run in their own sandbox | — | — | `make bootstrap` in the first message of the spec |
| Cursor, Antigravity, ZCode | the person opens the worktree folder | — | — | `make bootstrap` in the first message |
| any tool | — | — | — | `make doctor` at the start of every task |

Give `.worktreeinclude` one line, `.env`, and nothing else. It contains no secret (DEV_ENV.md).

### 10.3 The task spec an agent receives

Orca's guide sets the standard, and it is the right one for every tool: "Make each spec
self-contained: the target, the change, constraints, what the worker may edit, and the evidence
that proves it is done."

```text
Target: POST /v1/incidents/{id}/hazards (spec 0012-hazard-report).
Change: add the contract, the handler and the RLS test for a Field Responder's report.
May edit: contracts/, services/core-api/src/hazards/, database/tests/rls/.
Must not touch: database/migrations/, frontend/, docs/documentation/.
Done when: `make check` passes; test test_uc07_responder_can_trigger_alert passes;
           the pull request lists NFR-PF-04 and FR-HZ-04 under Requirement IDs.
A non-zero exit from a command means the task failed; paste the output in the report.
```

### 10.4 When two pull requests collide

| Collision | Resolution |
|---|---|
| both regenerate `contracts/openapi/core-api.json` | the second rebases, runs `make gen`, commits |
| both add a dependency to a lock file | the second rebases, `uv lock` or `pnpm install`, commits; never edit a lock file by hand |
| both add a migration | timestamps order them; the second runs `make db-reset` after rebasing |
| both add an event with the same name | the contract pull request that merged first wins; the other is renamed in its spec |
| both touch `AGENTS.md` | the second rebases; conflicts in a guide are settled by the repository owner |
| both add a row to the same seed file | one of them moves its rows to a new numbered seed file |

## 11. Work that takes longer than two days

- **Behind a flag.** Merge the safe part, hide the rest behind a setting or an empty state.
- **Branch by abstraction.** Add the new path beside the old one, switch callers in small pull
  requests, remove the old path last.
- **`exp/` branches.** For a spike whose code will not merge. The finding is written to the spec or
  a decision record; the branch is deleted.
- **Never:** a long-lived `develop`, a "integration" branch that people merge into, or a release
  branch that receives features.

## 12. Undoing a merge

A bad merge is reverted with a new pull request titled `revert: <original title>`, reviewed like
any other. On production the deploy is rolled back to the previous image digest (CI_CD.md); the
database is never rolled back by re-running a down migration on live data (CONTRACTS.md, expand
and contract).

## Sources

Checked on 25 November 2026.

- Trunk-based development: https://trunkbaseddevelopment.com/
- Merge queue mechanics and the `merge_group` requirement:
  https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue
- Merge queue availability (organization-owned public repositories; GitHub changelog, 12 July 2023):
  https://github.blog/changelog/2023-07-12-pull-request-merge-queue-is-now-generally-available
- Workflow path filters and pending required checks:
  https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions
- Code owners: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- release-please (squash recommendation, type to version mapping): https://github.com/googleapis/release-please
- Conventional Commits: https://www.conventionalcommits.org
- Claude Code worktrees (`-w`, `.claude/worktrees/`, `.worktreeinclude`, fresh checkouts):
  https://code.claude.com/docs/en/worktrees
- Claude Code best practices (`/batch`, a second session as reviewer): https://code.claude.com/docs/en/best-practices
- Orca worker and worktree conventions: the `orchestration` guide printed by Orca 1.4.268 on this
  machine.
- Repository facts: `git log`, `git branch`, and `gh api repos/AliOmarAbdelhady/RescueVision`
  (owner type, visibility, branch protection, rulesets) on 25 November 2026.
