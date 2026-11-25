# Architecture

Locked. How RESCA fits together, end to end. The reasons are in [DECISIONS.md](DECISIONS.md). Rule IDs (B4, C2…) point to [RULES_INDEX.md](RULES_INDEX.md).

## Containers

```
            browser (web console)          phone (Expo app)
                    │  HTTPS                   │  HTTPS
                    └──────────┬───────────────┘
                            Caddy            TLS, security headers, static web files
                               │
                         api  (FastAPI)      REST /api/v1, SSE /api/v1/incidents/{id}/events
                          │        │
                PostgreSQL 18      SeaweedFS (S3)     data and files
            PostGIS, pgRouting,         ▲
            pgvector, RLS               │ object keys, never bytes through the API
                          │             │
                     worker  (same code base as api, job mode)
                          │  HTTP, private network only
         ai-damage    ai-vision    ai-embed        ONNX Runtime on CPU, no DB credentials
```

| Container | Owns | Never does |
|---|---|---|
| `caddy` | TLS, headers, CORS, serving the built web app, proxying `/api` | Business logic |
| `api` | Every read and command; authorization; transactions with RLS identity; SSE | Run inference; hold files in memory |
| `worker` | Jobs from the Postgres queue: imagery processing, calls to AI services, reports, outbox publishing | Accept user requests |
| `ai-*` | One model family each: load a verified model, run inference on an object key, return results | Touch the database; call each other; accept internet traffic |
| `postgres` | All structured data, the job queue, the event log, RLS | Expose a port outside the server |
| `seaweedfs` | Images, rasters, 3D tiles, PMTiles, reports, model files | Public buckets |

The web app is static files. There is no Node.js server in production.

## How parts talk

1. Clients call the `api` only, over REST for commands and reads and SSE for live updates. Files go straight to SeaweedFS with pre-signed URLs the `api` issues after an authorization check.
2. A command that starts work writes its business rows, a `processing_jobs` row and an outbox event in **one transaction** (B11). The worker claims jobs with `FOR UPDATE SKIP LOCKED` and a lease.
3. The worker calls an AI service with an object key and a deadline (B10, C3). AI services never see the database and never receive files from the internet.
4. Every state change a user can see becomes an event in the incident event log, inside the same transaction as the change. SSE streams events after the client's last event ID; reconnecting clients resume with `Last-Event-ID`, mobile apps call `/events?since=` (B12, C2).
5. One heavy AI job runs at a time across the whole server, so dispatch screens stay fast (B6, A5).

## Three flows, end to end

**1. Drone upload to damage map.** An analyst creates a capture session; the app uploads images with pre-signed URLs; the `api` records them and queues an `ANALYZE` job. The worker checks each file (B7), calls `ai-damage` per tile, stores masks and per-building damage grades with model version and confidence, and computes cost ranges. Results arrive as events; the map shows them as *AI proposed*. An analyst confirms or corrects each building (A6). Area-wide orthomosaics and 3D tiles are prepared before the demo, not live.

**2. Flood report to electrified-water alert and re-route.** A field responder sends a flood report (with an idempotency key, B5). In one transaction the `api` stores it and the hazard engine checks it against power assets; a match creates an `ELECTRIFIED_WATER` alert, closes affected roads and marks active routes invalid. The alert, closures and invalid routes are events, so the commander's map and responders' phones update within seconds. A new route is computed with pgRouting avoiding closed roads, and a person confirms the alert before it is treated as verified.

**3. Offline field report to sync.** Without signal, the mobile app saves the report in local SQLite with its idempotency key and shows it as *not sent* (M2). When signal returns, the app sends queued commands in order; the server applies each once, even if retried, and returns the result. The app then reads `/events?since=` to catch up and clears the *not sent* mark only after the server confirms.

## Contracts

| ID | Rule | Gate |
|---|---|---|
| C1 | OpenAPI generated from FastAPI is the only API source. The web and mobile clients are generated from it; never hand-write API types. A contract change is its own PR, merged before code that uses it. | Regenerate and fail on drift; compile both clients |
| C2 | Events use one versioned envelope: `id` (per-incident cursor), `schema_version`, `incident_id`, `type`, `occurred_at` (UTC), `correlation_id`, typed `payload`. Clients deduplicate by `id` and resync when told their cursor is too old. | Event fixtures replayed on web and mobile |
| C3 | The AI service contract carries job ID, input object key and hash, coordinate system, units, model digest, result provenance, failure reason and deadline. Unknown models, external URLs and unit mismatches are rejected before anything is stored. | Same golden requests run by the service and the worker |
| C4 | Never break the last released API or a queued offline payload: no removed fields, changed enum meanings or changed status semantics while old mobile clients can still reconnect. | `oasdiff breaking` against the released schema; old payload fixtures |

Event cursors must be gap-free in commit order. A Postgres sequence alone is not enough (two transactions can commit out of order); allocate the cursor from a per-incident counter row inside the business transaction.

## CPU-only limits

- No GPU anywhere in production. Models run as ONNX on CPU with threads set to physical cores.
- Heavy batch work (orthomosaic stitching, 3D tiles, area-wide sweeps) is done before the demo and loaded by hash.
- No language model runs on the server.
- One user at a time is the demo target. Budgets in the area docs are measured on the real server before they are trusted.

## What the demo really shows

Label everything not yet built and verified as *proposed* in the report and the UI. Today the verified evidence is the database (56 tables, RLS, hazard engine, routing, with passing self-checks) and the 2D satellite mapping prototype.
