# DEV_ENV.md — one command for a new developer or a new agent

Part of the Engineering Specialist F blueprint (`docs/architecture/debate/eng_specialist_glm/`).

## 1. The promise

From a fresh clone, or from a fresh worktree that a tool just created:

```bash
make bootstrap    # once: tools, dependencies, local env, git hooks
make doctor       # every session: am I ready, and am I in a safe place to work?
make up           # the local stack, CPU only
make check        # everything CI checks, locally
```

Four commands, the same for a person and for an agent, on Linux, macOS or WSL2. **No GPU
anywhere.** Not on the laptop, where training never runs (the team already works that way on its
`codex/building-damage-v4` branch: "the laptop is source-only"). Not on the server: the
demonstration host is a CPU-only Contabo machine for one user at a time (the owner's constraint),
training happens on free Kaggle or Colab GPUs, and the server runs the application and CPU
inference with ONNX Runtime or OpenVINO. So what you run locally is what runs in the
demonstration. No step needs `sudo`, and nothing is written outside the repository and the user's
caches.

Targets to measure on Day 0 and write into this file: `bootstrap` under 15 minutes cold and
under 5 minutes warm; `up` under 3 minutes; `check` under 10 minutes cold and under 3 minutes
warm.

## 2. Prerequisites (the only things installed by hand)

| Requirement | Why | How |
|---|---|---|
| Git | worktrees | system |
| Docker Engine or Docker Desktop with Compose v2 | the stack and every test that touches PostgreSQL | system |
| `mise` | installs every other tool at the pinned version | `curl https://mise.run | sh` |
| 16 GB RAM, 20 GB free disk | two or three containers plus a build | hardware |

Windows runs through WSL2, with Docker attached to the WSL engine. Native Windows is not
supported in week 1: the geospatial Python wheels and the shell scripts assume a POSIX system, and
six people cannot debug two environments at once.

Everything else comes from `mise.toml`, which pins the version, and `mise.lock`, which records the
"download URL and checksum for each platform you lock". `mise install --locked` installs exactly
that. mise reads idiomatic version files too ("A project that already has `.nvmrc` or
`.python-version` can keep it"), so the repository keeps one `.python-version` for editors and no
second copy of the version.

| Tool | Pinned in | Used for |
|---|---|---|
| Node LTS, pnpm | `mise.toml` (pnpm equal to `packageManager` in `frontend/package.json`) | frontend |
| Python 3.12, uv | `mise.toml` | every Python workspace member |
| dbmate | `mise.toml`, or `tools/bootstrap.sh` from its release with a checksum | migrations |
| jq | `mise.toml` | scripts and CI |
| SOPS, age | `mise.toml` or the bootstrap script | secrets for staging and production |
| pre-commit, nbstripout | a `uv tool` install in the bootstrap script | hooks |
| gitleaks, Spectral, oasdiff | run by pre-commit and CI in their own environments | no local install needed |

## 3. What `make bootstrap` does

`tools/bootstrap.sh` is idempotent. Running it twice changes nothing the second time.

1. Check the prerequisites and print what is missing with its install command.
2. `mise install --locked`.
3. `uv sync --frozen --all-packages` (one lock file for the whole Python workspace).
4. `pnpm install --frozen-lockfile` in `frontend/`.
5. If `.env` is absent, copy `.env.example` to `.env` and set `COMPOSE_PROJECT_NAME` to
   `rv-<user>-<worktree-name>`. Never overwrite an existing `.env`.
6. `pre-commit install --hook-type pre-commit --hook-type commit-msg` and
   `nbstripout --install --attributes .gitattributes`.
7. Pull the base images for the stack and build `rescuevision-db`.
8. Run `make doctor` and print the summary: versions, paths, the next command.

It does not start the stack, touch a global configuration, or ask for a password.

## 4. What `make doctor` checks

`doctor` is the first command in root `AGENTS.md`. It exits non-zero on any item marked ✗.

| Check | ✗ means |
|---|---|
| current branch is not `main` | switch to a task branch before editing anything |
| `origin/main` is reachable and the branch is less than a day behind it | rebase |
| no uncommitted change in a file you did not create (with a list) | ask before you continue |
| every tool in `mise.toml` is installed at the pinned version | `mise install --locked` |
| lock files are current (`uv lock --check`, `pnpm install --frozen-lockfile`) | regenerate |
| hooks are installed (`pre-commit`, `nbstripout --is-installed`) | `make bootstrap` |
| Docker is running and Compose v2 is present | start Docker |
| `.env` exists and contains no value that looks like a secret | fix `.env` |
| at least 10 GB free disk | free space; rasters and images fill a disk |
| the Kaggle CLI, if installed, reads its token from outside the repository | move `kaggle.json` |
| no other worktree on this machine is running the local stack | use `make check`, or stop the other stack |

## 5. Running the stack

```bash
make up            # core profile: db, object store, core-api, worker, web, caddy, tiles, ai (fixture mode)
make up-ai         # the same, with the real model bundles on CPU (ONNX Runtime or OpenVINO)
make up-ai-mock    # the same as `make up`, stated explicitly: AI services answer from the fixture bundle
make up-photo      # add the `photogrammetry` profile (OpenDroneMap on CPU: slow, for precomputing only)
make down          # stop; volumes are kept
make down-clean    # stop and delete volumes (destroys the local database)
make logs          # follow the logs
make db-reset      # drop, migrate, seed reference data and the demo scenario
make db-shell      # psql into the development database
```

| Service | Host port (default, from `.env.example`) | Where it comes from |
|---|---|---|
| web (Vite dev server) | 5173 | existing `frontend/.env.example` |
| core-api | 8000 | existing `.env.example` and `frontend/.env.example` |
| PostgreSQL | 55432 | existing default in `database/README.md` |
| object store (S3 API) | 9000 | `.env.example` (the host port; the container's own port is set in the Compose file) |
| web and API through the edge proxy | 8080 | `.env.example`, for production-like testing |

⚠ The service list depends on ADR-0003 to 0006 (which AI families, which tile server, what
transport exists). The ports and the command names do not. Two things are fixed by the owner: the
host is CPU-only, and MinIO is not used (its repository is archived), so the object store is
SeaweedFS in `weed mini` mode, with RustFS as the alternative (CI_CD.md, section 10.1).

The AI services run in **fixture mode** by default: the template container loads a tiny bundle and
answers deterministically. A developer gets a complete flow, from upload to a damage layer, in
seconds, with obviously synthetic results and a banner in the UI that says so. `make up-ai`
instead loads the real quantised bundles on the CPU: the feasibility study measured, on a
4-core laptop, about 84 ms per building crop for its DINOv2-base proxy and 0.63 to 0.85 s per tile
for its damage proxy, which is fast enough to try a single tile live and too slow for an
area-wide sweep. That is why heavy work is precomputed (CI_CD.md, section 10.6), and why
`make up-ai` starts one inference worker at a time.

## 6. Seed data

| Seed | Purpose | Loaded by |
|---|---|---|
| `database/seed/01_reference_data.sql` | roles, permissions, hazard rules, a cost profile, the model registry | every environment, by migration and seed step |
| `database/seed/02_demo_scenario.sql` | the fictional Downtown Cairo scenario that exercises every feature, with demo staff such as `analyst@gov.demo` and `para1@ems.demo` | development and staging only, by `make db-reset` and the staging deploy |
| `database/seed/03_golden_scenario.sql` (to write) | a small fixed scenario for end-to-end and golden tests, with known answers | CI only |

Production is never seeded with demo people. `make seed` refuses to run when `APP_ENV=production`.

## 7. Worktrees

A new worktree is an empty checkout: no `node_modules`, no virtual environment, no `.env`. Claude
Code's documentation says it directly: "A worktree is a fresh checkout, so initialize your
development environment there."

- Run `make bootstrap` in every new worktree. With warm caches it takes a few minutes.
- **Caches are shared by all worktrees**: the pnpm store, the uv cache and pre-commit's cache are
  global; Turborepo's cache is pointed at one directory through `[env]` in `mise.toml`.
- **Git hooks are installed once per repository**. The hook files live in the common Git directory
  that every worktree shares. `make doctor` still checks in each worktree.
- **One local stack per machine.** Each worktree has its own Compose project name, so two stacks
  would start, but they would fight for the ports above. In a second worktree, use `make check`,
  which starts throwaway containers on random ports and removes them.
- **`.worktreeinclude`** contains `.env`, so Claude Code copies it into a worktree it creates.
  It is safe because `.env` holds no secret (section 9).
- **In Orca**, point the workspace setup at `make bootstrap` (`worker-start … --setup run`), so a
  new child worktree is ready before the worker's first message.

## 8. Kaggle (training)

- Training never runs on a laptop or in CI. It runs on Kaggle, from a `kaggle/<feature>/vN`
  folder (REPO_TREE.md, section 6).
- The Kaggle credential lives outside the repository: `~/.kaggle/kaggle.json` (already in
  `.gitignore`) or `KAGGLE_API_TOKEN` in the environment. The Kaggle MCP server that the owner
  uses is configured at user scope, never in a committed `.zcode/config.json` or `.mcp.json`.
- Before planning a run, check the weekly accelerator quota (the Kaggle MCP server exposes a
  quota tool; the CLI shows the same in account settings).
- A notebook is prepared locally, checked by `make kaggle-check`, approved as a submission
  specification, and then uploaded by a person or by an agent acting on that approval.

## 9. Secrets, and what is not a secret

| Value | Where it lives | In Git? |
|---|---|---|
| local development defaults (database password `postgres`, object-store root credentials for a throwaway container) | `.env`, generated from `.env.example` | `.env.example` yes; `.env` no |
| staging and production secrets | `infra/secrets/*.enc.env`, encrypted with SOPS and age | yes, encrypted |
| the age private keys | `~/.config/sops/age/` on each owner's machine, and GitHub Environment secrets | never |
| Kaggle token | `~/.kaggle/` or an environment variable | never |
| any API key for a model provider | environment variable or the secret store | never |

The test is simple: if a value leaked, could somebody reach a database that matters or spend
money? If yes, it is a secret and it is encrypted. Everything else belongs in `.env.example` so
that a new worktree works without asking anybody.

## 10. Dev container (optional)

`.devcontainer/devcontainer.json` and its Dockerfile give the same environment to an editor that
supports the Dev Container Specification and to GitHub Codespaces. It contains Docker CLI with the
host socket mounted, `mise`, and nothing pre-installed: `make bootstrap` still runs inside, so the
container and the host follow the same steps.

Use it if your editor offers "Reopen in Container". Agents managed by Orca run on the host. Do not
depend on a cloud agent's sandbox reading the dev container: Claude Code's documentation describes
its cloud sessions as running "in an isolated, Anthropic-managed virtual machine" and does not say
they use `.devcontainer/`. The bootstrap command is the portable part.

## 11. First message to a new agent

Paste this at the start of a task, in any tool:

```text
Work in this worktree only. Read AGENTS.md at the repository root, then the nested AGENTS.md of
every folder you edit.
1. Run `make bootstrap` if this worktree is new, then `make doctor`. Paste both outputs.
2. Read the spec: specs/NNNN-slug/spec.md. Read the decision index at the end of AGENTS.md.
3. Do the task: <target, change, what you may edit, what you must not touch>.
4. Before you report: run `make check` and paste the result. Add tests with requirement IDs.
5. Report: what you changed, the commands you ran and their output, what you could not do.
Do not commit to main. Do not commit if doctor fails. Stop and ask if the task contradicts a
decision record.
```

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `make up` fails on "port is already allocated" | another worktree's stack is running | `make doctor` names it; stop it or use `make check` |
| `pnpm install` fails after a rebase | lock file changed | `pnpm install`, then commit `pnpm-lock.yaml` |
| a test cannot reach PostgreSQL | Docker is not running, or an old `rescuevision-db` image | start Docker; `docker build -t rescuevision-db:ci database/` |
| `nbstripout --is-installed` exits 1 | hooks not installed in this repository | `make bootstrap` |
| a notebook diff is unreadable | the diff driver is not configured | the same: `.gitattributes` and `nbstripout --install --attributes .gitattributes` |
| `make doctor` says the branch is behind | `main` moved | `git fetch origin && git rebase origin/main`, then `make gen` |
| the object store container keeps restarting | an old volume with other credentials, or (RustFS) a bind mount not writable by its non-root user | `make down-clean` (destroys local data); for RustFS make the data directory writable by UID 10001 |
| an AI container is slow or uses far more CPU than expected | inference threads set to logical instead of physical cores, or two heavy inferences at once | set `AI_THREADS` to the physical core count; run one heavy job at a time |
| `make up-ai` runs out of memory | several real bundles loaded on a small laptop | stay in fixture mode (`make up`), or load one family |
| an agent says a check "should pass" without running it | it did not run it | the pull request template's Evidence block must contain the command and its output |

## 13. The task list (`make help`)

| Target | What it does |
|---|---|
| `help` | every target with one line |
| `bootstrap`, `doctor` | section 3 and section 4 |
| `up`, `up-ai`, `up-ai-mock`, `up-photo`, `down`, `down-clean`, `logs`, `ps` | the local stack, all on CPU |
| `demo-precompute`, `demo-verify` | run the heavy jobs listed in `infra/demo/manifest.yaml`; check every precomputed artifact by hash |
| `db-reset`, `db-shell`, `db-check`, `seed` | the database |
| `gen`, `gen-check`, `agents-check` | regenerate derived files; fail if stale |
| `fmt`, `lint` | format and lint everything |
| `test` | unit and integration (needs Docker) |
| `check-fast` | format, lint, types, boundaries, generated files: about two minutes |
| `check` | `check-fast` plus unit, integration, database and contracts: what CI runs |
| `test-e2e`, `test-mobile` | Playwright and Maestro |
| `kaggle-check`, `docs-check`, `trace` | experiment folders, documentation links, the requirement matrix |
| `new-ai-service`, `new-migration` | scaffolds |
| `clean` | remove build output and caches inside the repository |

Recipes contain no logic: each one calls a package manager or a script in `tools/`.

## Sources

Checked on 25 November 2026.

- mise ("Dev tools, env vars, and tasks in one CLI"; `mise.lock`; idiomatic version files):
  https://mise.jdx.dev/
- uv workspaces ("the workspace shares a single lockfile"): https://docs.astral.sh/uv/concepts/projects/workspaces/
- Dev Containers: https://containers.dev/
- Claude Code worktrees (fresh checkouts, `.worktreeinclude`): https://code.claude.com/docs/en/worktrees
- Claude Code sandbox environments (cloud sessions, dev containers):
  https://code.claude.com/docs/en/sandbox-environments
- nbstripout (`--install`, `--is-installed`, `--verify`): https://github.com/kynan/nbstripout
- Compose `up --wait`: https://docs.docker.com/reference/cli/docker/compose/up/
- Expo monorepo notes already applied in `frontend/.npmrc` (`node-linker=hoisted`):
  `frontend/.npmrc` and `frontend/package.json` in this repository.
- Existing local defaults: `.env.example`, `frontend/.env.example`, `database/README.md`.
- Kaggle kernel metadata (`enable_gpu`, `enable_internet`, `machine_shape`, `dataset_sources`):
  https://github.com/Kaggle/kaggle-api/blob/main/docs/kernels_metadata.md
- "The laptop is source-only": `codex/building-damage-v4:docs/v4_experiments.md`.
- Orca worktree setup (`--setup run`): the `orchestration` guide printed by Orca 1.4.268.
- Owner's constraint (CPU-only Contabo server, one user at a time, training on free Kaggle or
  Colab GPUs): message from the coordinator, 25 November 2026.
- CPU latency figures are the feasibility study's measurements on an i5-1135G7:
  `docs/architecture/debate/cpu_demo_feasibility.md`.
- Object stores, through the GitHub API on 25 November 2026: `minio/minio` archived;
  `seaweedfs/seaweedfs` Apache-2.0, release 4.55, README quote on `weed mini`;
  `rustfs/rustfs` Apache-2.0, release 1.0.6, README note on its non-root user (UID 10001).
