# AGENT_FILES.md — which agent files exist, what each contains, and how they stay in sync

Part of the Engineering Specialist F blueprint (`docs/architecture/debate/eng_specialist_glm/`).
Companion to `AGENTS.md` in this folder, which is the complete draft of the new root guide.

## 1. The rule this file is built on

**One source of truth, many adapters.** `AGENTS.md` is the only file a person writes. Every other
agent file in the repository is either a nested `AGENTS.md` with rules for one folder, or a
generated adapter that points back at it. `make gen` writes the adapters and `make check` fails
when they are stale.

Why this works in November 2026: every agent the team uses reads `AGENTS.md` without help (table
in section 2). That was not true a year ago, and two of the three competing blueprints still
assume a `CLAUDE.md`-only world.

## 2. What each tool actually reads (checked on 25 November 2026)

| Tool | Reads root `AGENTS.md`? | Nested `AGENTS.md` | Size limit | Also reads |
|---|---|---|---|---|
| OpenAI Codex | Yes, natively | Yes. Walks from the Git root down to the current directory, at most one file per directory, joined root-first. Files closer to the current directory override earlier ones. | Stops adding files at 32 KiB combined by default (`project_doc_max_bytes`) | `AGENTS.override.md` per directory; fallback names from `project_doc_fallback_filenames` |
| Claude Code | Yes, since v2.1.277, when no `CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or above it. A project setting can load both. | Nested **`CLAUDE.md`** files load on demand, the first time Claude reads or edits a file in that subdirectory. Nested `AGENTS.md` behaviour is not stated in the memory page: confirm with `/context all` before relying on it. | "Target under 200 lines per CLAUDE.md file"; `@` imports resolve up to four hops | `.claude/rules/*.md` with a `paths:` frontmatter glob; `.claude/skills/`; `.claude/settings.json` (hooks, permissions) |
| Cursor | Yes, natively | Yes. "Supports `AGENTS.md` in the project root and subdirectories"; nested files apply when working with files in that directory or its children. | "Keep rules under 500 lines" | `.cursor/rules/*.mdc` (`description`, `globs`, `alwaysApply`) |
| Gemini CLI | Not by default. Add it with `context.fileName: ["AGENTS.md", "GEMINI.md"]` in `.gemini/settings.json`. | Files are found in the workspace, its parents, and just in time when a tool touches a directory or file: "the CLI automatically scans for `GEMINI.md` files in that directory and its ancestors up to a trusted root". | Not stated on the page read | `GEMINI.md` at `~/.gemini/`; `@file.md` imports |
| Antigravity (managed agents) | Yes: "The agent automatically loads `.agents/AGENTS.md` (or `/.agents/AGENTS.md`) from the environment as system instructions on startup." | Not stated in the page read | Not stated | Skills under `.agents/skills/<name>/SKILL.md` |
| ZCode | Yes: the workspace `AGENTS.md`, found by searching upward from the working directory to the project root. | Not loaded on demand. Only the file found from the current directory upward is read, so a session started at the repository root does not see a nested file unless the root file points to it. | Not stated | Skills in `.zcode/skills/` and `.agents/skills/`, scanned from the current directory up to the repository root; commands in `.zcode/commands/`, `.agents/commands/`; hooks and MCP servers in `.zcode/config.json` |
| OpenCode | Yes | Yes, discovered as the agent explores; "A directory's `AGENTS.md` always wins over its `CLAUDE.md`, so a symlink between the two loads once." | Not stated | `~/.config/opencode/AGENTS.md` |
| GitHub Copilot | Yes: "the nearest `AGENTS.md` file in the directory tree will take precedence" | Yes | "must be no longer than 2 pages" for `copilot-instructions.md` | `.github/copilot-instructions.md`; `.github/instructions/*.instructions.md` with `applyTo:` globs |

The agents.md site lists Codex, Jules, Cursor, Gemini CLI, GitHub Copilot, opencode, Amp, Zed,
Windsurf and others as adopters and reports use by "over 60k open-source projects". Its conflict
rule is the one this blueprint relies on: "The closest AGENTS.md to the edited file wins; explicit
user chat prompts override everything."

Two consequences drive the design:

1. ZCode and a root-started Codex session never see nested files by themselves, so the **root
   `AGENTS.md` must carry the index** ("read this before editing that"). Tools that do load nested
   files get the same content twice, which is harmless.
2. Codex stops at 32 KiB for the whole chain, so budgets matter: root ≤ 14 KiB, each nested file
   ≤ 6 KiB, and the root plus the largest nested file must stay under 32 KiB.

## 3. The complete inventory

### 3.1 Root files

| File | Written by | Contents |
|---|---|---|
| `AGENTS.md` | person | The contract. Draft in [`AGENTS.md`](AGENTS.md). |
| `CLAUDE.md` | `make gen` | Two lines: a comment saying it is generated, then `@AGENTS.md`. Works on every Claude Code version, including the ones before native `AGENTS.md` support. |
| `GEMINI.md` | `make gen` | The same two lines with `@AGENTS.md`. |
| `.gemini/settings.json` | `make gen` | `{"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}` so Gemini CLI finds nested `AGENTS.md` files too. |
| `CLAUDE.local.md`, `AGENTS.override.md` | nobody | Never committed. Listed in `.gitignore`. |
| `README.md` | person | For humans: what, why, three-command start, where to go next. It links to `AGENTS.md` and does not duplicate it. |
| `.claude/settings.json` | repo owner only | Permissions allow-list for routine commands (`make`, `pnpm`, `uv`) and the `Stop` hook that runs `make check-fast`. Review it like code: see section 7. |
| `.zcode/config.json` | repo owner only | Same idea for ZCode (hooks need `hooks.enabled: true`). Keep `mcp.servers` empty at workspace scope. |
| `.github/copilot-instructions.md` | `make gen` | One paragraph: "Read `AGENTS.md` at the repository root and the nearest `AGENTS.md` to the files you edit." |

Nothing else is needed for Cursor, OpenCode, Codex or Antigravity. Do not add a `.cursorrules`
file or a second copy of the rules in `.cursor/rules/`: two copies drift.

### 3.2 Nested guides (one per place an agent could go wrong)

Each nested file is under 80 lines and has the same five sections, in this order: **Read first**,
**Commands**, **Rules**, **Done when**, **Never**. The table says what its Rules section must
contain.

| File | Must contain |
|---|---|
| `services/core-api/AGENTS.md` | One module per information domain (D1 to D5). Cross-module calls go through a module's public service functions; `make check` enforces it. Every request runs in one transaction that calls `app.set_session_user()` or `app.set_session_citizen()` first. Endpoints are exported to `contracts/openapi/core-api.json` by `make gen`. ⚠ Framework follows ADR-0002. |
| `services/worker/AGENTS.md` | Job handlers are idempotent and resumable: each step writes its output under a deterministic key. Progress is reported at least every 30 seconds (NFR-PF-05). Only the worker writes AI results, always with `inference_run_id`. The worker checks the AI service's `/v1/model-info` against the `ai_models` row before the first request of a run. |
| `services/ai/AGENTS.md` | Every service is created from `services/ai/_template/` and implements `contracts/openapi/ai-service.yaml`: two-step tasks, inputs and outputs by reference, `job_id` as the idempotency key. No database driver, no credentials. Each service loads one pinned bundle (`bundle.lock.json`) and reports its image digest in `/v1/model-info`. The runtime is CPU only, ONNX Runtime or OpenVINO: the image has no PyTorch, CUDA, Triton or TensorRT, inference threads are pinned to the physical core count, and one heavy inference runs at a time (the CPU feasibility study measured both rules). |
| `services/ai/_template/AGENTS.md` | Copied into each new service by `make new-ai-service`. Says which files to rename and which tests must exist before the first pull request. |
| `ai/AGENTS.md` | Training, evaluation and export code. Splits are grouped by disaster event; the test split is never used to choose a model, threshold or recipe. Metrics come from the official scorer. Export is verified for numerical parity before it leaves this folder. |
| `kaggle/AGENTS.md` | The versioned experiment layout and its rules (REPO_TREE.md, section 6): thin notebooks, pinned package commit, locked datasets, submission spec reviewed before any upload, no credentials, `metrics.json` linked by hash to a run record. |
| `database/AGENTS.md` | Migrations are forward-only plain SQL (ADR-0008). Every table has row-level security policies for `rv_app`, `rv_worker`, `rv_citizen` and `rv_readonly`, a GiST index on every geometry column, and a test in `database/tests/`. Applications never connect as the owner. `SECURITY DEFINER` functions set `search_path`. |
| `contracts/AGENTS.md` | What counts as a contract, how a change flows through it (CONTRACTS.md, section 5), and the rule that generated files are committed and never hand-edited. |
| `frontend/AGENTS.md` | Apps import packages; packages never import apps. All HTTP and live traffic goes through `packages/api`. Map state lives in validated URL search parameters. English and Arabic with right-to-left layout from the first sprint. |
| `frontend/apps/web/AGENTS.md` | Feature-slice layout (`src/features/*`), one nested `README.md` per feature (the convention already in the repository), state rules (server state in TanStack Query only), the requirement that every uncertain or missing value has an explicit on-screen state, and the rule that 3D is drawn in the browser: the server serves tiles and footprints and renders nothing. |
| `frontend/apps/mobile/AGENTS.md` | Native modules only behind `src/services/`. Development builds, never Expo Go. Every write carries a client-generated UUIDv7 and an idempotency key. The offline indicator and queued-item count are always visible. |
| `infra/AGENTS.md` | Compose profiles, pinned image digests, secrets only through SOPS-encrypted files, and the CI workflow rules (CI_CD.md): filtering at job level, one required check. The demonstration host is a CPU-only Contabo server for one user at a time: every service has a memory limit in the production Compose file, the `photogrammetry` profile is off by default, `deploy.sh` refuses to run while `DEMO_FREEZE=1` is set, and `make demo-verify` runs before a demonstration. |
| `docs/AGENTS.md` | Where each kind of document goes (DOCS_SYSTEM.md, section 3), the decision record format, and the freshness rules. |
| `docs/documentation/AGENTS.md` | The graduation report guide. This is the **current root `AGENTS.md` moved unchanged**: report versions, DOCX build and extract, margins, citations, figure rules, team ownership and the progress checklists. |
| `prototypes/AGENTS.md` | "Frozen evidence. Do not fix, import or extend. Copy an idea, rewrite the code." Maps each prototype to what it is evidence of. |
| `tools/AGENTS.md` | Repository scripts: every script has `--help`, is idempotent, and is called from the `Makefile`. |

### 3.3 Per-feature READMEs (already a convention in `frontend/`)

The repository already has `README.md` in each `frontend/apps/*/src/features/<name>/`. Keep them
as **human** documentation of a feature (what it is for, what it contains). They do not carry
agent rules. When a feature needs a rule that an agent must follow, add it to the parent
`AGENTS.md`, not to the README.

The 14 existing feature READMEs describe the old single-analyst tool (roles
`COMMANDER / ANALYST / RESPONDER`, events `position, sos, job-progress, victim`, "cases" that are
assessment outputs). They must be rewritten against the report's vocabulary before any frontend
work starts; until then `frontend/AGENTS.md` carries a warning that they are a sketch.

## 4. Template for a nested guide

```markdown
# <folder>/AGENTS.md

Read the root `AGENTS.md` first. This file adds rules for `<folder>` only.

## Read first
- `docs/adr/NNNN-<slug>.md` — <what it decides>

## Commands
- `make <target>` — <what it does and how long it takes>

## Rules
1. <A rule an agent would otherwise break. Say why in one clause.>

## Done when
- <The check that proves the work, e.g. "`make db-check` passes">

## Never
- <The one mistake that would be expensive>
```

Write rules as instructions with a reason, not as descriptions: "Call `app.set_session_user()`
before the first query, because pooled connections cannot carry a user between requests."

A guide links downward as well as up. If the folder has guides below it (for example
`frontend/apps/web/AGENTS.md` under `frontend/`), the parent lists them under **Read first**, so an
agent that loads only the parent still knows they exist.

## 5. Skills and commands (procedures that are too long for a guide)

Agent Skills is an open format: a folder with a `SKILL.md` whose YAML frontmatter has `name`
(lowercase, hyphens, at most 64 characters, equal to the folder name) and `description` (at most
1024 characters, saying what the skill does and when to use it). The body loads only when the
skill is activated, and the specification advises keeping it under 500 lines. The integrate guide
names `.agents/skills/` as the cross-tool location, next to each client's own directory.

The repository keeps its skills in `.agents/skills/<name>/SKILL.md`, which ZCode and Antigravity
scan. `make gen` writes a forwarding `SKILL.md` with the same frontmatter into
`.claude/skills/<name>/`. Ship six, no more:

| Skill | When it is used | What it encodes |
|---|---|---|
| `new-endpoint` | adding or changing an API route | contract-first steps, `make gen`, breaking-change rule, requirement tagging |
| `new-migration` | any schema change | dbmate create, RLS checklist, index checklist, test to add, expand and contract |
| `new-ai-service` | standing up a model family | copy the template, pin the bundle, contract tests, compose profile |
| `kaggle-experiment` | starting or promoting a `kaggle/<feature>/vN` | the dossier checklist, submission-spec review, run record, promotion gate |
| `report-edit` | touching `docs/documentation/` | routes to `docs/documentation/AGENTS.md`, DOCX build and extract, citation order, "proposed" wording |
| `release` | cutting a release | changelog, tag, deploy, post-deploy smoke, rollback |

Slash commands live in `.agents/commands/` with the same names. ZCode reads them from
`.agents/commands/` and joins nested names with a colon (`review/code.md` becomes `/review:code`).

## 6. How agents are stopped from drifting

Text alone does not hold an agent to a vision. Each layer below catches what the previous one
misses.

| Layer | Mechanism | Catches |
|---|---|---|
| 1 | One canonical file and generated adapters | two tools reading two different rulebooks |
| 2 | The root file indexes every nested guide | tools that do not load nested files (ZCode, root-started Codex) |
| 3 | A decision record for every settled choice, with the index generated into `AGENTS.md` | an agent re-deciding architecture inside a task |
| 4 | "If something has to happen every time, make it a hook, a deny rule, or a managed setting" (Claude Code best practices): `make check` and CI hold every rule a machine can test | an agent that read the rule and broke it anyway |
| 5 | `make doctor` at session start | commits on `main`, stale worktrees, missing hooks |
| 6 | Budgets enforced in CI | a guide that grows until nothing reads it |
| 7 | Cursor advises updating the rules when the agent errs; Claude Code advises recording "Anything you've had to correct twice already". The pull request template asks "Did an agent repeat a mistake? Fix the rule here." | mistakes recurring |
| 8 | A monthly 30-minute "guide diet": delete any line that a reader could have found in the code | slow rot |

Three rules make these layers work in practice.

- **Judgement goes in text; enforcement goes in tools.** A rule that can be a lint, a test or a
  check is written as one, and `AGENTS.md` only says that it exists.
- **Agent files are code.** They are reviewed by the same owner as the folder they govern, they
  are tested by `make check`, and they change only through pull requests.
- **No rule without a reason.** Every "never" line states the failure it prevents, so an agent
  faced with a new situation can apply the intent.

## 7. Agent configuration is an executable surface

Settings files can run commands and load tools without asking. ZCode's configuration guide says
hooks need `hooks.enabled: true`, and that workspace-scoped MCP servers "are trusted and
auto-connected by default", with the warning "only open workspaces you trust". The same applies
to Claude Code hooks and to skills, which an agent loads and follows.

For a public repository this means:

1. `.claude/`, `.zcode/`, `.gemini/`, `.agents/`, `.cursor/` and `.github/CODEOWNERS` are owned by
   the repository owner in `CODEOWNERS`. A change needs that owner's approval, given by a person.
2. Workspace-level MCP servers stay empty. The Kaggle MCP server that the owner already uses is
   configured at user scope, never committed.
3. An agent never edits these files on its own initiative. Root `AGENTS.md` section 9 says so.
4. Skills are reviewed like code before they are committed: a `SKILL.md` is an instruction that
   every agent will follow.

## 8. Confirming that a tool loaded the right context

Run these once on Day 0, after the files exist, and record the result in the Day-0 notes:

| Tool | Check |
|---|---|
| Claude Code | `/context all`, then look under "Memory files" for `AGENTS.md` through `CLAUDE.md`. Open a file under `database/` and confirm the nested guide loads. If it does not, generate `.claude/rules/database.md` with `paths: ["database/**"]` from the same source. |
| Gemini CLI | Run `/memory refresh`, then ask it to quote the first rule of `database/AGENTS.md`. |
| Codex | Ask it to quote the first rule of `database/AGENTS.md` with the working directory set to `database/`, then from the repository root. |
| ZCode | Ask for the repository map from section 3 of the root file, then ask it to read `database/AGENTS.md` and list that folder's rules. |
| Orca | Start a throwaway worker in a new child worktree with the spec "run `make doctor` and paste the output". It must pass without further setup. |

## 9. The check

`make agents-check` (part of `make gen-check`, which is part of `make check`) fails when:

- `CLAUDE.md`, `GEMINI.md`, `.gemini/settings.json`, `.github/copilot-instructions.md` or any
  forwarding `SKILL.md` differs from what `make gen` would write;
- a generated block in `AGENTS.md` differs from its source;
- the root file exceeds 14 KiB or 200 lines, a nested file exceeds 6 KiB or 80 lines, or the root
  plus the largest nested file exceeds 32 KiB;
- a nested `AGENTS.md` is missing a section, or a folder named in the root index has no nested
  file;
- a rule, check or command named in a guide does not exist (`make help` and the file tree are
  the reference);
- an unauthorised path is listed in `CODEOWNERS`, or an agent configuration file was changed in
  a pull request without the owner's approval.

The last item is why the guides can stay short: a command or rule that is named is a command or
rule that works.

## Sources

Checked on 25 November 2026.

- AGENTS.md format, adopters and the "closest file wins" rule: https://agents.md
- Codex instruction chain, nesting and the 32 KiB default: https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Claude Code memory: native `AGENTS.md` support since v2.1.277, lazy nested files, imports, the
  200-line target, `.claude/rules/`: https://code.claude.com/docs/en/memory
- Claude Code best practices (short `CLAUDE.md`, hooks for things that must always happen, the
  `Stop` hook): https://code.claude.com/docs/en/best-practices
- Gemini CLI context files and `context.fileName`: https://geminicli.com/docs/cli/gemini-md
- Cursor rules and native `AGENTS.md`: https://cursor.com/docs/context/rules
- OpenCode rules: https://opencode.ai/docs/rules/
- GitHub Copilot repository instructions: https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions
- Antigravity managed agents (`.agents/AGENTS.md`, `.agents/skills/`): https://aistudio.google.com/docs/custom-agents.md
- Agent Skills specification and integration guide: https://agentskills.io/specification and
  https://agentskills.io/integrate-skills
- ZCode configuration (workspace `AGENTS.md`, skills and commands directories, hooks, MCP
  auto-connect): the `zcode-configuration-guide` skill shipped with ZCode 0.3.0, read on this
  machine on 25 November 2026.
- Orca worker and worktree conventions: the `orchestration` guide printed by Orca 1.4.268 on this
  machine, and the repository's own worktree and branch list.
