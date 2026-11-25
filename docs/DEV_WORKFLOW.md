# Development workflow

Locked. How every change, by a person or an AI agent, gets from idea to `main`.

## Git

- `main` is protected. Nobody pushes to it directly; changes arrive by pull request with `ci/ok` green.
- Branch from the latest `main`: `<github-user>/<short-topic>`, for example `AliOmarAbdelhady/sos-idempotency`. Pull before you start and before you open the PR.
- One change per PR, about 400 changed lines at most (generated files excluded). Larger needs a reason in the PR.
- Conventional Commits in the PR title (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`). PRs are squash-merged.
- Never commit secrets, `.env` files, model weights, datasets, notebook outputs or large binaries (pre-commit blocks files over 1 MB).
- Never delete or rewrite a teammate's work (`mahmoudERD/`, `mapping/`, `docs/documentation/`); move it with `git mv` only after the owner agrees.

## Contract first

An API, event or AI-service contract change is its own PR and merges before the code that uses it (C1). Generated clients are regenerated, never edited.

## CI

GitHub Actions run **only for `main`**: pull requests into `main` and pushes to `main`. One required check, `ci/ok`, passes only when every gate passed or had nothing to check. A gate whose area has code but no implementation fails (fail closed).

| Gate | Command | Where | Rules |
|---|---|---|---|
| Locked paths | `make check-policy` | pre-commit, CI | G2 |
| Secrets | `make check-secrets` | pre-commit, CI | X4, O3 |
| Python lint and format | `make check-static` | pre-commit, CI | X1, X6, B1 |
| Backend | `make check-api` | CI | B1 to B14 |
| Database | `make check-db` | CI when `database/` changes | D1 to D7 |
| Frontend | `make check-ui` | CI | W1 to W12, M1 to M5 |
| AI | `make check-ml` | CI | A1 to A6 |
| Everything | `make check` | before every PR | all |

Gates that are not built yet print `UNRUN`. Build each one before the first code in its area, and prove it with a deliberately wrong change that fails it. Planned additions as code arrives: auth route matrix, contract drift (`oasdiff breaking`, Schemathesis), events, jobs, browser (Playwright with `--fail-on-flaky-tests`), image (hadolint), restore drill, release.

## Locked files

The list is `.github/locked-paths.txt`: agent guides, `ARCHITECTURE.md`, `DECISIONS.md`, this file, `RULES_INDEX.md`, `.github/`, `tools/policy/`, the Makefile, lint and token configs, and `database/schema/15_security.sql`.

- CI reads the list and the checker from the **base** branch, so a PR cannot unlock itself.
- A PR touching a locked file fails unless the owner adds the `owner-approved` label; CI checks that the owner's account added it.
- Locally, the pre-commit hook blocks commits to locked files. The owner may set `RESCA_LOCKED_CHANGE_APPROVED=1` for an owner change.
- Agents never add the label, never set that variable, never edit the list. If a locked file is wrong, describe the change in the PR text and stop.
- Limit: an agent working with the owner's own GitHub token appears as the owner. Give agents a separate token without label rights where possible.

## Rules for all code

| ID | Rule | Gate |
|---|---|---|
| X1 | Never swallow an error (empty catch/except, catch-all without re-raise, unhandled promise). | Ruff and ESLint rules in BACKEND and FRONTEND |
| X2 | One error format (RFC 9457 problem details) with stable code and correlation ID. | Contract tests |
| X3 | Structured logs with IDs; no personal data, secrets, exact locations or media URLs. | Sentinel-value log tests |
| X4 | Typed configuration validated at startup; missing secrets stop the service; `.env.example` holds placeholders only. | Startup test; gitleaks |
| X5 | Lockfiles with hashes; licence and vulnerability check on dependency changes; weekly updates. | Frozen installs; SBOM scan |
| X6 | One responsibility per module; files under 400 non-blank lines; complexity ≤ 10; no dead code or commented-out code. | Ruff `C90`, `ERA001`, `F401`, `F841`; TS unused checks |
| X7 | Temporary feature flags have a safe default, an owner and an expiry; no flag may switch off authorization or audit. | Flag registry check |

## Testing

| ID | Rule |
|---|---|
| T1 | Test each changed behaviour at the lowest useful level; every bug fix starts with a test that fails before the fix. |
| T2 | At least 80% branch coverage per runtime, and every safety decision tested both ways (allowed and denied, above and below a threshold). |
| T3 | Tests use real PostGIS 18 for database behaviour, fixed clocks and seeds, isolated data, and no network. |
| T4 | A test that fails then passes on retry is a failure. Quarantine needs an owner and at most 7 days; SOS, auth, replay and restore tests are never quarantined. |
| T5 | The three flows in ARCHITECTURE.md run end to end, also with slow network, constrained CPU and the AI services down. |
| T6 | Security-relevant changes map to OWASP ASVS 5 controls and the API Top 10, with the evidence named in the PR. |

## Review and release

| ID | Rule |
|---|---|
| G1 | Small PRs with purpose, risks, tests, contract and migration effects, and rollback (the PR template asks for each). |
| G2 | Locked files change only by the owner (above). |
| G3 | `ci/ok` on the exact commit being merged; skipped or cancelled jobs count as failures. |
| G4 | Third-party actions pinned to full commit SHAs; workflow token read-only by default; PR jobs never see deploy secrets. |
| G5 | Release only a reviewed commit with lockfiles, image and model digests, test results and a rehearsed rollback. |

## How AI agents work here

| ID | Rule |
|---|---|
| P1 | Before editing: read the root and nearest `AGENTS.md`, this file, `DECISIONS.md` and the area doc; write a short plan with the rule IDs and tests you will satisfy. One agent per area at a time; separate worktrees for parallel agents. |
| P2 | Never weaken a test, skip a test, add `eslint-disable`, `noqa` or `type: ignore`, widen a lint exception, edit a locked file, or replace real data with fixtures to make a check pass. |
| P3 | Before handing off, run the gates and report the exact commands and results, including what you did not run and why. Never claim something works that you did not run. |
| P4 | Universal rules live in `AGENTS.md`, area rules in the area doc, and anything a tool can check lives in the tool. Do not copy rules between files; link to [RULES_INDEX.md](RULES_INDEX.md). |
