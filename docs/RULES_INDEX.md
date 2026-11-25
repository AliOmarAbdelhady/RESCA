# Rules index

Locked. Every rule ID, the one document that defines it, and how it is enforced. Rules are not copied between documents; link here instead. The research behind them is in [archive/architecture-debate/rules_research_codex.md](archive/architecture-debate/rules_research_codex.md).

| IDs | Area | Defined in | Main gate |
|---|---|---|---|
| X1 to X7 | All code: errors, error format, logging, config and secrets, dependencies, structure, flags | [DEV_WORKFLOW.md](DEV_WORKFLOW.md#rules-for-all-code) | `make check-static`, `make check-ui`, gitleaks |
| B1 to B14 | Backend: layers, API shape, pagination, authorization, idempotency, rate limits, uploads, transactions and RLS, N+1, deadlines, jobs, SSE, status codes, headers | [BACKEND.md](BACKEND.md#rules) | `make check-api` |
| D1 to D7 | Database: migrations, RLS, constraints, indexes, audit, retention, seed data | [DATABASE.md](DATABASE.md#rules) | `make check-db` |
| W1 to W12 | Web: tokens, reuse, translations, data states, forms, state, maps, accessibility, performance, error boundaries, browser security, role dashboards | [FRONTEND.md](FRONTEND.md#rules) | `make check-ui` |
| M1 to M5 | Mobile: dev builds and tokens, offline queue, location, secure storage, performance | [FRONTEND.md](FRONTEND.md#mobile-expo) | `make check-ui` |
| A1 to A6 | AI: reproducibility, splits, promotion, ONNX parity, serving template, human confirmation | [AI.md](AI.md#rules) | `make check-ml` |
| C1 to C4 | Contracts: OpenAPI, events, AI service, compatibility | [ARCHITECTURE.md](ARCHITECTURE.md#contracts) | contract gate (to build) |
| T1 to T6 | Testing | [DEV_WORKFLOW.md](DEV_WORKFLOW.md#testing) | every gate |
| G1 to G5 | Review, locked files, CI, supply chain, release | [DEV_WORKFLOW.md](DEV_WORKFLOW.md#review-and-release) | `make check-policy`, `ci/ok` |
| P1 to P4 | How AI agents work | [DEV_WORKFLOW.md](DEV_WORKFLOW.md#how-ai-agents-work-here) | review, `make check-policy` |
| O1 to O6 | Docker, secrets, backups, monitoring, release and rollback | [DEPLOY.md](DEPLOY.md#rules) | image, edge and restore gates (to build) |
| DEC-01 to DEC-20 | Owner decisions | [DECISIONS.md](DECISIONS.md) | owner review |

## The 12 rules agents break most

1. Hard-coded colour, size or style instead of a token (W1).
2. Hard-coded English text instead of `t()` with English and Arabic keys (W3).
3. A copied component instead of a shared one with a variant (W2).
4. An empty `catch`/`except` or an unhandled promise (X1).
5. An N+1 query: a relationship loaded inside a loop (B9).
6. An endpoint without an allowed and a denied authorization test (B4).
7. A retryable command without an idempotency key (B5).
8. Fake data on a screen, or a missing loading, empty or error state (W4).
9. A list without pagination or an input without bounds (B2, B3).
10. A weakened, skipped or deleted test, or a new lint suppression (P2).
11. An edit to a locked file (G2).
12. "Done" without having run the gates (P3).
