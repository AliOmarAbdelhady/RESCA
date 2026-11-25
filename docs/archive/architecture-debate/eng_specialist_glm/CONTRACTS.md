# CONTRACTS.md — contract-first development and how a change flows

Part of the Engineering Specialist F blueprint (`docs/architecture/debate/eng_specialist_glm/`).

## 1. Why contracts come first here

Six students and their agents will work in parallel worktrees from day one. The web team cannot
wait for the backend, the backend cannot wait for the model, and nobody can wait for the database.
What lets them work at the same time is agreeing on the **interface** before the **inside**:
a request shape, an event payload, a table, a model bundle.

A contract in this repository is a file that two sides agree on and that a machine checks.
There are seven kinds. Each has exactly one source, generates the types that both sides compile
against, and fails CI when the two sides drift apart.

The rule that follows: **no side implements against a contract that is not merged.** When a
feature needs work on both sides of a contract, the contract is its own small pull request, merged
first. The implementing pull requests branch after it.

## 2. The seven contracts

| # | Contract | Source of truth | Format and tool | Consumers (generated) |
|---|---|---|---|---|
| 1 | Database schema | `database/migrations/*.sql` (forward-only) | plain SQL, dbmate | the database itself; `contracts/db/enums.json`; ERD and data dictionary |
| 2 | Core API | `contracts/openapi/core-api.json`, exported from `services/core-api` by `make gen` | OpenAPI 3.1; Spectral, oasdiff | `frontend/packages/api/src/generated/` (openapi-typescript) |
| 3 | AI service API | `contracts/openapi/ai-service.yaml` (template, design-first) and `services/ai/<family>/openapi.json` (exported) | OpenAPI 3.1 | typed clients in `services/worker/`; Schemathesis tests |
| 4 | Events (live updates and sync) | `contracts/events/catalog.yaml` and one JSON Schema per version | JSON Schema 2020-12 | TypeScript in `frontend/packages/contracts/src/generated/`; Pydantic models in `contracts/python/` |
| 5 | Vocabularies | PostgreSQL enum types after migration | generated JSON by `tools/gen_enums.py` | TypeScript unions, Pydantic enums; checked against contract 4 |
| 6 | Stored files | `contracts/storage-keys.md` | key patterns from the report's Table 3-44 | a test that validates every key the services write |
| 7 | Model bundle | `manifest.json` inside each bundle in object storage | JSON, written by `ai/` export | the AI service loader, the `ai_models` row, the worker's pre-run check |

The error catalogue (`contracts/errors.md`) is part of contracts 2 and 3.

Three properties are required of all seven:

- **One source.** Where two files describe the same thing, one is generated from the other.
- **Committed and reviewed.** Generated files are committed, so a pull request shows the exact
  change every consumer will see.
- **Additive by default.** Adding an optional field, an endpoint or an event is safe. Removing or
  renaming, making optional required, or changing a meaning is breaking and needs `!` in the pull
  request title and an owner's approval.

## 3. Details per contract

### 3.1 Database

- `database/schema/00…15_*.sql` is the current schema and the best asset in the repository. Freeze
  it as baseline migration `0001_baseline.sql`; from then on every change is a new file in
  `database/migrations/`, created with `make new-migration NAME=<slug>`.
- Migrations are plain SQL with an up and a down section and run in a transaction by default
  (dbmate's README: "Migrations are run atomically inside a transaction"). A statement that
  cannot run in a transaction (`CREATE INDEX CONCURRENTLY`) opts out per file.
- A merged migration is never edited. Fix it with a new migration.
- Destructive changes use expand and contract across two releases: add the new column and write
  both, migrate the data, stop reading the old one, and only then drop it.
- Every migration that adds a table adds its row-level security policies for `rv_app`,
  `rv_worker`, `rv_citizen` and `rv_readonly` in the same file, and a test under
  `database/tests/`.
- `database/build.sh` stays as the from-scratch builder for a developer machine and becomes
  "apply all migrations, then seeds, then `checks.sql`".

**Why dbmate and not Atlas or an ORM.** Atlas supports row-level security policies, triggers and
functions only in its paid edition ("Triggers are available only to Atlas Pro users"; the policy
block is listed as Pro). Policies, triggers and functions are the heart of this schema. ORM
autogeneration cannot see them either. Plain SQL in a single static binary is the right tool.

### 3.2 Core API

- FastAPI (or, if ADR-0002 chooses TypeScript, the framework's OpenAPI decorator) is the origin.
  `make gen` starts the application in export mode and writes `contracts/openapi/core-api.json`
  with keys sorted, so the diff shows only real changes.
- Every operation carries `operationId`, a description, and at least one `example` for the
  success response and one per error. The examples are used by the contract tests and by the
  mocks, so they are part of the contract.
- Errors use one shape everywhere (a problem-details document with a stable `code` from
  `contracts/errors.md`). The report's rule that missing information is shown as missing applies
  to the API too: a field whose value is unknown is absent or `null`, never a default that looks
  like a real value.
- The TypeScript client is generated with openapi-typescript ("Generate TypeScript types from
  OpenAPI 3 specs") into `frontend/packages/api/src/generated/`, with `openapi-fetch` as the
  runtime. This is already the rule in `frontend/packages/api/README.md`.
- Lint with Spectral (`extends: ["spectral:oas"]` plus a small project ruleset that requires the
  fields above).

### 3.3 AI service API

The owner's requirement is that every model is isolated from the backend, in Docker, behind an
API. A single template makes "behind an API" mean the same thing for every model.

`contracts/openapi/ai-service.yaml` is written by hand and is the design. Every AI service
implements it. The shape is the one Architect B proposes (`glm_proposal.md`, section 6.2): a long
inference never holds one HTTP request open, and a retried job never writes twice.

| Operation | Purpose |
|---|---|
| `GET /healthz` | the process is alive; no model involved |
| `GET /readyz` | the bundle is loaded, the device is usable, and a self-test tensor gave the expected result |
| `GET /v1/model-info` | service version and image digest; for each model: name, task, version, weights SHA-256, input specification (bands, size, normalisation, ground-resolution range), label map version, published metrics, licence |
| `POST /v1/tasks` | `{ job_id, run_id, inputs: {references}, params }` → `202 { task_id }`. `job_id` is the idempotency key: the same job submitted twice returns the existing task |
| `GET /v1/tasks/{task_id}` | `{ status, progress_pct, outputs: {references}, summary, timings }` |

ADR-0003 may add a synchronous `POST /v1/{task}:predict` for calls well under a second (one crop,
one embedding). It may not remove or rename the five operations above.

Rules:

- The API speaks in the platform's terms ("assess these two rasters", "detect people in this image
  set"), not in tensors: the geospatial steps (tiling, windows of a GeoTIFF, polygonising a mask)
  live inside the service, so the backend stays a backend.
- Inputs and outputs travel **by reference**: object keys in, object keys out, a small summary in
  the response. Outputs go to a deterministic prefix, `incidents/{incident}/runs/{run}/`, so a
  retry overwrites its own partial output and nothing else.
- The service is stateless beyond a small in-memory queue and holds no database credential. If it
  restarts, the worker submits the task again. Durability lives in PostgreSQL and object storage.
- Only the worker writes results.
- A service's exported `openapi.json` must conform to the template (a contract test compares the
  two). It may add operations; it may not change these five.
- The service runs on CPU with ONNX Runtime or OpenVINO. Its image holds no PyTorch, CUDA, Triton
  or TensorRT, because the demonstration host has no GPU (the owner's constraint).
- Whether one container serves one model or one model family is a deployment choice left to
  ADR-0003. Inside a container every model keeps its own identity: its own weights and checksum,
  its own version, its own metrics and its own row in `ai_models`.
- `services/ai/_template` ships with a fixture bundle that answers deterministically on a CPU.
  The worker's tests and the local stack run against it, so no developer needs a GPU.

### 3.4 Events

- One envelope for every live event and every synchronised change, using the attribute names of
  the CloudEvents JSON format (`id`, `source`, `type`, `time`, `subject`, `data`), so that a
  change of transport later does not change the payload.
- The payload is kept small and free of personal data. An event says "case X changed"; the client
  fetches the record itself under the usual access rules.
- Each event has a schema file with a version in its name (`alert.raised.v1.schema.json`) and a
  row in `catalog.yaml`: producer, consumers, the requirement it serves (Table 3-47 of the report
  lists the first seven), and its data class.
- A new field is a new schema version when its meaning changes; adding an optional field is not.
- Every schema has example documents in the catalogue, and a test validates them.

Table 3-47 of the report is the first catalogue: position update, alert raised or resolved,
route invalidated, case changed, assignment, SOS, job progress.

### 3.5 Vocabularies

`database/schema/01_types.sql` holds 57 `CREATE TYPE` statements, mostly enums. They are the product's
vocabulary. After each migration `make gen` reads `pg_enum` and writes `contracts/db/enums.json`; the
TypeScript and Python unions are generated from that file. Nobody types an enum value by hand in a
client. When a feature needs a value that does not exist, the migration comes first.

### 3.6 Stored files

`contracts/storage-keys.md` restates Table 3-44 of the report
(`incidents/{incident}/captures/{session}/raw/{image}` and the others). A unit test in each
service checks every key it writes against the pattern for its table. Keys begin with the
incident so that one incident's files can be listed, copied or removed together.

The keys sit in an S3-compatible store. It is SeaweedFS in `weed mini` mode, with RustFS as the
alternative; MinIO is not used because its repository is archived (CI_CD.md, section 10.1). No
service names the product: the S3 API is the contract (ADR-0005).

### 3.7 Model bundle

A bundle is a folder in object storage: weights, `manifest.json` and the label map. The manifest
is written by the export step in `ai/` and read by three sides, which must agree on every field:

| Field | Checked by |
|---|---|
| `name`, `task`, `version` | the `ai_models` row |
| `weights_sha256` | the loader, before the first request |
| `format`, `runtime`, `precision` | the loader, which refuses a bundle it cannot run |
| `threads` | the service, at start-up (the physical core count) |
| `parity` (largest absolute difference and class changes against the FP32 reference on the golden tiles) | Gate A in CI (CI_CD.md, section 7) |
| `latency_cpu` (per golden tile, with the hardware named) | the `ai-perf` job and the model card |
| `input` (bands, size, normalisation, ground-resolution range) | the worker, which refuses tiles outside the range |
| `labels` and `label_schema_version` | the worker, when it writes results |
| `metrics`, `run_id`, `eval_set_digest` | the promotion gate and the model card |
| `git_commit`, `package_version`, `licence` | the model card and the report |

A bundle without a hash and an evaluation record cannot be made active.

The demonstration host has no GPU, so the bundle that is promoted is the one that was measured
on CPU. An export exists in one runtime (`onnxruntime` or `openvino`) and one precision (`fp32`,
or an int8 variant), both written in the manifest. Quantisation is not a blanket rule: the
feasibility study measured one of its model proxies 4.1 times slower with dynamic int8, so each
model keeps the precision it was measured fastest with, and the FP32 reference stays in the
repository's test fixtures for the parity check.

## 4. The change flow

The same six steps apply to every contract. "Contract PR" and "build PR" are separate.

1. **Describe.** In the feature's spec (`specs/NNNN-slug/spec.md`) write the interface change and
   who consumes it.
2. **Contract PR.** Change the contract source only: a migration, the route's request and response
   models, an event schema, the enum. Run `make gen`. Commit the contract and everything it
   generated. Title it `feat(contracts): …` or `feat(db): …`.
3. **Review the interface, not the code.** The owner of each consuming side approves. For a
   breaking change, `!` in the title and a migration or deprecation note in the description.
4. **Merge, then branch.** Each implementing pull request starts after the contract is on `main`.
   Frontend work runs against generated mocks of the contract, backend work against the generated
   types and the contract tests.
5. **Implement.** Schemathesis runs the contract against the running service: it "generat[es]
   inputs from your schema" on top of Hypothesis, and the examples from the schema are tested
   exactly. The TypeScript build fails if the server's shape and the client's type disagree.
6. **Prove and record.** Contract tests, the requirement tag, and a row in the trace matrix.

### 4.1 Three worked examples

**Adding a field to a response.** Add the optional field to the response model in `services/core-api`.
`make gen` updates `contracts/openapi/core-api.json` and the TypeScript types. oasdiff classifies
it as non-breaking. One pull request, because the change is additive and small.

**A feature that needs a new endpoint, used by web and mobile.**
Pull request 1: `feat(contracts): add hazard report endpoint` (route stub returning `501`, models,
examples, generated client). Pull request 2: the real handler and its tests. Pull request 3 and 4:
web and mobile screens, started while 2 is open, using the mock. If 2 discovers that the contract
was wrong, it stops and opens a new contract pull request; it does not bend the contract.

**A new table.** `make new-migration NAME=zone_access_log` creates the file. Write the table, the
indexes, the policies for four roles and the down section. `make db-reset` applies it and `make
gen` updates the enums and the ERD. `database/tests/` gets the RLS test. One pull request,
approved by the database owner.

**A new model version.** The experiment closes with a verified run (`kaggle/<feature>/vN/`). The
export writes the bundle and its manifest. A `model-promote` workflow run (manual, with the
feature and version as inputs) checks the hashes and the evaluation record, then opens a pull
request that updates `services/ai/<family>/bundle.lock.json` and adds the `ai_models` migration
with `is_active = false`. Activation is a separate, reversible step.

### 4.2 What an agent does when the contract it needs is missing

Stop. Open (or ask for) the contract pull request. Do not create a private type, a second
endpoint "for now", or a hand-written interface. An unmerged contract is not a contract.

## 5. Rules for parallel work

| Situation | Rule |
|---|---|
| Two agents change the same contract | Both regenerate after rebase; neither hand-merges a generated file. `make gen` then `git add` the result. |
| An agent's task says "add endpoint X" and X is not in the contract | The task is a contract task first. |
| A breaking change is unavoidable | `!` in the title, an approval from every consuming side, and a deprecation period of one release where a client exists |
| The frontend needs data the backend will not have for a week | Work from the merged contract with mocks generated from it. The mock is deleted when the real service lands. |
| A model result shape changes | New bundle version, new manifest field set, contract test updated in the same pull request |
| An enum value is missing | Migration first; clients are regenerated |

## 6. Checks

| Check | Where | Fails when |
|---|---|---|
| `make gen-check` | locally and in the `contracts` CI job | any generated file differs from its source |
| Spectral lint | `contracts` CI job | an operation lacks `operationId`, description or examples |
| oasdiff breaking, compared with `main` | `contracts` CI job | a change breaks existing clients and the title has no `!` |
| Template conformance | `ai-contract` CI job | an AI service changed one of the template operations |
| Schema examples | `contracts` CI job | an example does not validate against its schema |
| Schemathesis | `integration` CI job | a server response violates its contract |
| Enum round trip | `db` CI job | a value used in an event schema is not in `enums.json` |
| Storage key test | `integration` CI job | a written key does not match its pattern |
| Bundle manifest test | `ai-contract` CI job | a fixture bundle's manifest is missing a required field |

## 7. Decisions recorded here

- **Schemathesis, not Pact.** Pact checks a consumer's expectations against a provider across
  repositories. This is one repository: the generated client already fails to compile when the
  server's shape changes, and Schemathesis proves the server against the same document. Adopt
  Pact only if a second client outside this repository appears.
- **JSON Schema with a catalogue, not AsyncAPI.** There is no broker; events travel over the live
  channel and the sync endpoint. An AsyncAPI document can be generated from the catalogue later
  if a broker arrives.
- **Committed generated files, not build-time generation.** A pull request must show what
  consumers will get, and CI must not depend on a running service to type-check the frontend
  (already the practice in `frontend/tooling/README.md`).

## Sources

Checked on 25 November 2026.

- dbmate: timestamped plain-SQL migrations, transactional by default, `schema_migrations`:
  https://github.com/amacneil/dbmate
- Atlas object support and its Pro-only triggers, views and policies:
  https://atlasgo.io/atlas-schema/hcl
- openapi-typescript and openapi-fetch: https://github.com/openapi-ts/openapi-typescript
- Spectral ("A flexible JSON/YAML linter for creating automated style guides", `spectral:oas`):
  https://github.com/stoplightio/spectral
- oasdiff ("Command-line tool to compare and detect Breaking changes in OpenAPI specs"):
  https://github.com/oasdiff/oasdiff
- Schemathesis: https://github.com/schemathesis/schemathesis
- CloudEvents JSON format, version 1.0.2 (`application/cloudevents+json`):
  https://github.com/cloudevents/spec/blob/v1.0.2/cloudevents/formats/json-format.md
- Problem details for HTTP APIs (RFC 9457): https://www.rfc-editor.org/rfc/rfc9457
- JSON Schema, draft 2020-12: https://json-schema.org/draft/2020-12
- The report's own tables: `docs/documentation/chapter5/section_3_3.md` (Table 3-44 for storage
  keys, Table 3-47 for live-update events).
- The AI service contract shape and the rule for splitting a model family:
  `docs/architecture/debate/glm_proposal.md`, sections 6.1 to 6.5.

RFC 9457 and the JSON Schema draft are cited from knowledge and were not opened while this
blueprint was written.
- Owner's constraint (CPU-only Contabo server, one user at a time, training on free Kaggle or
  Colab GPUs): message from the coordinator, 25 November 2026.
- Repository status through the GitHub API on 25 November 2026: `minio/minio` archived;
  `seaweedfs/seaweedfs` Apache-2.0, release 4.55; `rustfs/rustfs` Apache-2.0, release 1.0.6.
- Quantisation measured per model: `docs/architecture/debate/cpu_demo_feasibility.md`.
