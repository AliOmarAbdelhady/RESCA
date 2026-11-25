# Contracts

*Draft of the repository's `CONTRACTS.md`: an index of every contract between the parts of RescueVision, and the rules for changing one. A contract is a promise that two sides can be built independently and still work together.*

## 1. The contracts

| Contract | Between | Source of truth | Generated into | Read by |
| --- | --- | --- | --- | --- |
| **Backend API** | Clients and the backend | `backend/src/rescuevision/**` (FastAPI code), exported to `contracts/openapi/backend.yaml` | `frontend/packages/api/src/generated/` | Web console, field app, citizen page, tools |
| **Event catalogue** | Backend and live clients | `contracts/events/*.yaml` | Schemas in `frontend/packages/contracts` and the backend's event module | Live channel, web console, field app |
| **Model service API** | Worker and each AI service | `ai/services/<name>/` code, exported to `contracts/openapi/infer-<name>.yaml` | The worker's typed client [B55] | Worker |
| **Model input and output** | Training and serving of one task | `contracts/model-io/<task>/{input,output}.json` | Validation code on both sides | `ai/training/**/export.py`, `ai/services/**`, tests |
| **Database** | Everything that stores data | `database/schema/*.sql` | ERD in `database/erd/` | Backend, tools, people |
| **Object-storage keys** | Writers and readers of files | `contracts/storage-keys.md` | Key builders in the platform package | Backend, AI services, tile server |
| **Scenario expectations** | The product and its tests | `scenarios/<name>/expected.yaml` | Nothing; read by the replay tool | End-to-end tests, demonstration |

## 2. Rules

1. **A contract is generated from code, never typed twice.** The OpenAPI document is exported from the service's code and committed as a snapshot. Clients are generated from the snapshot. `make contracts` regenerates everything; `make contracts-check` fails if the committed files are stale.
2. **Changing a contract is a separate, small change.** A pull request that changes a contract does nothing else, so that the other side can be updated in time.
3. **Version in the path.** `/v1` for the backend API and `/v1` for each model service.
4. **Additive changes are free.** A new optional field, a new endpoint, a new event type: allowed inside a version. Consumers must ignore fields and event types they do not know.
5. **A breaking change needs a plan.** Removing or renaming a field, changing a type, making an optional field required, changing a meaning: all breaking. They require a new major version, a decision record, both versions served until every consumer has moved, and a removal date.
6. **Breaking changes are detected automatically.** CI compares the committed OpenAPI document with the one on `main` and fails if it finds a breaking change (oasdiff provides such a check [B54]).
7. **Every error has a stable code.** Clients branch on the code, never on the text. The response shape is `{ "error": { "code": "...", "message": "...", "retryable": false, "details": {} } }`.
8. **One shape for time, space and identifiers everywhere.** Timestamps are ISO 8601 in UTC. Geometry is WGS 84 (SRID 4326) and distances are metres. Identifiers are UUIDv7 in lower-case text. Money carries its currency code.

## 3. The backend API

- Base path `/api/v1`. The live channel is `/ws/v1`.
- Authentication with a short-lived bearer token. The citizen channel uses the same mechanism with a narrower token.
- Lists are cursor-paginated with a maximum page size.
- Every write that comes from a mobile device carries the client's operation identifier, so that a retry has no second effect.
- Endpoints are grouped by module. Each module's `api.py` is the only place its endpoints are defined.

## 4. Events

An event is a small, durable statement that something changed. It never carries a large geometry; it carries an identifier and a summary, and the client fetches the record if it needs more.

| Field | Meaning |
| --- | --- |
| `seq` | Global sequence number. Clients resume with "everything after this". |
| `incident_id` | The incident the event belongs to |
| `type` | Name in the catalogue, for example `alert.raised` |
| `audience` | `incident` (everyone who may see the incident) or `user` (one user) |
| `entity` | Table name and identifier of the changed record |
| `payload` | A small summary |
| `occurred_at` | Server time |

The catalogue in `contracts/events/` lists every type with its payload schema and its audience. Adding a type is adding one file; both clients learn it through the generated schemas.

## 5. Model services

The four resources every service exposes (`/healthz`, `/readyz`, `/v1/meta`, `/v1/tasks`), the task states and the job ticket are defined in `AI_PIPELINE.md` §7. Two rules are repeated here because they are the most often broken:

- **Data travels by reference, never in the request body.**
- **The job id is the idempotency key.**

## 6. Model input and output

For each AI task, `contracts/model-io/<task>/` defines what one task receives (references, parameters, bounding box) and what it produces (the list of output files and the summary fields). Training validates its export against this definition; serving validates its answers against it. The tiny models in `fixtures/models/` obey the same contract, which is how the whole pipeline is tested on CI without a real model.

## 7. Storage keys

Defined once in `contracts/storage-keys.md`:

| Content | Key |
| --- | --- |
| Raw imagery | `incidents/{incident}/captures/{session}/raw/{image}` |
| Rasters | `incidents/{incident}/captures/{session}/products/{product}` |
| AI products | `incidents/{incident}/runs/{run}/{product}` |
| Field and citizen media | `incidents/{incident}/media/{media}` |
| Reports | `incidents/{incident}/reports/{report}/report.pdf` |
| Prebuilt tiles | `incidents/{incident}/tiles/{layer}/{z}/{x}/{y}` inside one archive file |
| Evidence bundle | `bundles/{scenario}/{version}/…` |

Rules: no slashes inside a segment; lower-case; file names never reused for different content; a key is built only with the helpers in the platform package.

## 8. Where to read more

- `ARCHITECTURE.md` for how the parts fit together.
- `AI_PIPELINE.md` for the full model-service contract and the registry.
- `docs/architecture/api-guidelines.md` (to be written in Milestone 1) for naming, filtering and errors in the backend API.
