# backend/AGENTS.md

FastAPI app and worker, package `src/resca_api`. Read [docs/BACKEND.md](../docs/BACKEND.md) before any change. Locked.

Gate: `make check-static check-api` (and `make check-db` if SQL changes).

Most-broken rules here:
1. Empty or catch-all `except` that hides an error. Raise typed errors with `from err` (X1).
2. A relationship read in a loop (N+1). Relationships are `lazy="raise"`; load with `selectinload` and add a query-count test (B9).
3. An endpoint without `Depends(require("..."))` and without allowed and denied tests (B4).
4. A retryable command without an `Idempotency-Key` (B5).
5. Unbounded input or an unpaginated list (B2, B3).
6. Business logic in a router, or a commit in a repository (B1).
7. Personal data, tokens or exact locations in logs (X3).
