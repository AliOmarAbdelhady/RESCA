# Backend

FastAPI, Python 3.12, SQLAlchemy 2 (async) with asyncpg, Pydantic v2. One package `backend/src/rescuevision_api`, run as `api` (HTTP) or `worker` (jobs). Read [ARCHITECTURE.md](ARCHITECTURE.md) first.

## Layout

```
backend/src/rescuevision_api/
  core/            settings, db session, auth, errors, logging, rate limits (imports no domain)
  <domain>/        identity, incidents, imagery, citizens, buildings, roads, cases, hazards, routing, reports
    router.py      HTTP only: parse, call one service function, return the response model
    service.py     business rules and the transaction; the only module other domains may import
    repository.py  SQLAlchemy queries, parameterized; no commits
    schemas.py     Pydantic request and response models
  events/          event log, outbox publisher, SSE endpoint
  jobs/            worker entry points
backend/tests/     unit/, api/, db/ (real PostGIS), fixtures/
```

Domains match `database/schema/02` to `11`. `.importlinter` enforces the layers (router → service → repository) and that domains use each other only through `service`.

## Rules

Each rule has a gate. "Review" means no tool can check it, so the PR reviewer must.

| ID | Rule | Gate |
|---|---|---|
| X1 | **Never swallow an error.** No empty `except`, no `except: pass`, no `except Exception` that does not re-raise. Raise typed errors with `raise ... from err`. Only the outer HTTP or job boundary turns an error into a response, after logging it once. | Ruff `E722`, `BLE001`, `S110`, `S112`, `B904`, `TRY` |
| B1 | Routers are thin; services own the transaction; repositories own queries. No raw SQL built from strings; no `session.commit()` in a repository. | `lint-imports`; Ruff `S608`; review |
| B2 | Every endpoint is under `/api/v1`, with separate input and output models. Inputs use `extra="forbid"` and bounded fields (lengths, ranges, list sizes). Filters and sorts come from an allowlist. | Contract tests; unknown-field test per endpoint |
| B3 | Lists are paginated with opaque cursors, stable order plus a unique tie-breaker, default 25, maximum 100. Never return a whole table. | API tests: equal timestamps, last page, invalid cursor |
| B4 | **Deny by default.** Identity comes from the verified session only. Every operation checks the action, incident membership, the object and writable fields. A test lists every OpenAPI operation and fails if one has no allowed and no denied case (other agency, citizen, suspended user, expired session). | `make check-auth` route matrix |
| B5 | Retryable commands (SOS, field reports, uploads) take an `Idempotency-Key`. The key is bound to the user, the operation and a hash of the body; the result is stored with the effect in one transaction. Same key, different body: 409. | Concurrent and replay tests |
| B6 | **Rate limits** per account and per trusted client IP, plus limits on request size, open SSE streams, queue depth and heavy jobs. Over the limit: 429 with `Retry-After`; saturated: 503. SOS keeps reserved capacity. Trust client IPs only from Caddy. | Load tests per quota |
| B7 | Uploads go to a private quarantine. Check declared and real type, dimensions, decoded size and owner before any processing. Object keys are generated, never taken from the client. | Bad-file fixtures |
| B8 | One transaction per unit of work. Set the RLS identity with `SET LOCAL` from the authenticated user before touching protected rows. Never share an `AsyncSession` between tasks. The app never connects as the table owner or with `BYPASSRLS`. | DB tests reuse one connection for two users |
| B9 | **No N+1 queries.** All relationships use `lazy="raise"`; load what you need with `selectinload`/`joinedload` or one query. Every list endpoint has a test that the query count is the same for 1 and 25 rows and under its budget (starting budget 6). | Query-count test per list route |
| B10 | Calls to AI services and other dependencies have connect, read and total deadlines; retry only transient, idempotent work, at one layer, with jitter, at most twice; open a circuit after repeated failures and report "AI unavailable" while the rest of the API keeps working. | Fake-clock job tests |
| B11 | Business state, outbox entry and job row are written in one transaction. Jobs have leases, a maximum attempt count, a visible terminal failure, and effects that are safe to repeat. | Kill-and-restart job tests |
| B12 | SSE is per incident, from the durable event cursor; it re-checks membership while streaming, sends heartbeats, bounds buffers and resumes from `Last-Event-ID`. | Event tests through Caddy |
| B13 | Status codes mean one thing: 201 created, 202 queued (with a status URL), 401 no valid session, 403 forbidden or 404 for objects the user may not know exist, 409 conflict, 422 invalid input, 429 limited. Under one heavy job, p95 reads stay under 500 ms and SOS is durably accepted in under 1 s. | API and load tests |
| B14 | Caddy sets TLS, explicit CORS origins, `nosniff`, a frame policy and `Cache-Control: no-store` on sensitive responses. | Edge test on real responses |

## Patterns

**Errors.** One error format for every failure: RFC 9457 problem details with a stable `code`, the HTTP status, a safe message key the client translates, and the `correlation_id`. Never send stack traces or SQL errors to clients.

```python
# Wrong: the failure disappears.
try:
    await repo.save(report)
except Exception:
    pass

# Right: expected failures are typed; everything else propagates to the boundary.
try:
    await repo.save(report)
except UniqueViolation as err:
    raise DuplicateReport(report.idempotency_key) from err
```

**Queries.**

```python
# Wrong: one extra query per incident (N+1), and with lazy="raise" it fails loudly.
incidents = (await session.scalars(select(Incident))).all()
names = [i.lead_agency.name for i in incidents]

# Right: one round trip for the relationship.
stmt = select(Incident).options(selectinload(Incident.lead_agency)).limit(page.size)
```

**Authorization.** Every route declares its permission through one dependency; RLS is the second wall, never the only one.

```python
@router.get("/incidents/{incident_id}/cases", response_model=CasePage)
async def list_cases(incident_id: UUID, page: PageParams = Depends(),
                     user: User = Depends(require("incident.view"))) -> CasePage:
    return await cases_service.list_for_incident(user, incident_id, page)
```

**Logging.** Structured JSON with operation, duration, outcome and request, job and trace IDs. Never log tokens, passwords, phone numbers, names, exact locations or media URLs (X3).

## Definition of done for a backend change

- Gates pass: `make check-static check-api check-db`.
- New endpoint: allowed and denied tests (B4), unknown-field test (B2), query-count test if it lists (B9), status codes from the table (B13), and its OpenAPI change merged first (C1).
- New job: lease, retry and restart tests (B11), deadline tests if it calls a service (B10).
- No new `# noqa`, `type: ignore` or skipped test. If a rule seems wrong, say so in the PR; do not work around it.
