# RescueVision Platform Architecture Plan

Status: proposal for team review, 25 November 2026. Nothing here is built yet.

## 1. Decision summary

| Question | Decision |
|---|---|
| Full microservices (one service per domain)? | No. Too much operational cost for a six-person student team, and it contradicts decision D-02 in the report (Section 3.3, Table 3-39). |
| What instead? | A **service-based architecture**: one modular core backend, plus separately deployed AI services and workers, each in its own Docker container. |
| Are the AI models isolated from the backend? | Yes. Every model runs in its own Python container. The core backend never imports a model; it talks to the AI services only through an internal HTTP API and a job queue. |
| AI service framework | **FastAPI** for each AI service, with the model behind a stable internal contract. BentoML or Triton can replace the inside of a service later without changing the contract. |
| Core backend | **NestJS** (TypeScript) modular monolith, one module per data domain. |
| Web frontend | **React + Vite SPA with TanStack Router and TanStack Query** (not TanStack Start, not Next.js). |
| Mobile | **Expo (React Native)**, as already set up in `frontend/apps/mobile`. |
| Database | PostgreSQL 18 with PostGIS, pgRouting and pgvector, row-level security (already built in `database/`). |

## 2. Why not full microservices

The sources agree on a rule of thumb: below roughly 15 to 20 engineers, microservices cost more than they return, because every service adds network calls, separate deploys, distributed debugging and its own monitoring. The common recommendation is a modular monolith with firm internal boundaries, extracting a service only when one part has a different scaling, runtime or release need.

RescueVision has exactly one part with a different need: the AI. It needs Python, GPUs, large model files and long-running jobs, while the rest of the platform is ordinary web traffic. So the split is made there and nowhere else:

- **Split out (different runtime, hardware and scaling):** AI inference, imagery processing (orthomosaic stitching), map tile serving.
- **Kept together (same runtime, shared transactions):** incidents, missions, cases, hazards, routing, reports, users. These share one database and many transactions; for example, a compound alert closes roads and invalidates routes in one step. Splitting them would turn one database transaction into a distributed saga.

This matches what the report already says. Decision D-02 chose "a modular application with background workers, deployed as a small number of services" over "many independent microservices". Decision D-03 chose "analysis runs as queued background jobs". The plan below is that design made concrete, so the code and the graduation report stay consistent.

## 3. Containers

```
                         ┌───────────────────────────── clients ─────────────────────────────┐
                         │  Web console (React SPA)   Mobile app (Expo)   Citizen channel     │
                         └───────────────┬───────────────────────────────────────────────────┘
                                         │ HTTPS + WebSocket
                                 ┌───────▼────────┐
                                 │ edge (Caddy)   │  TLS, routing, rate limits
                                 └───┬────────┬───┘
                     REST + WS       │        │  tiles
                 ┌───────────────────▼──┐  ┌──▼──────────────┐
                 │ core-api (NestJS)    │  │ tiles (Martin / │
                 │ modules per domain,  │  │ TiTiler)        │
                 │ auth, RLS context,   │  └──┬──────────────┘
                 │ realtime gateway     │     │
                 └──┬─────────┬─────────┘     │
        SQL (RLS)   │         │ internal REST │
     ┌──────────────▼──┐  ┌───▼──────────────────────────────────────────────┐
     │ PostgreSQL 18   │  │ AI services (Python, FastAPI, one container each)│
     │ PostGIS,        │◄─┤  ai-damage     building damage grades (F1)       │
     │ pgRouting,      │  │  ai-person     person detection + tracking (F3/4)│
     │ pgvector        │  │  ai-embed      image embeddings for pgvector     │
     │ job queue table │  │  imagery-worker orthomosaic / DSM / 3D (F2)      │
     └─────────────────┘  └───┬──────────────────────────────────────────────┘
                              │ read/write files
                       ┌──────▼──────────┐
                       │ object storage  │  MinIO (S3 API)
                       └─────────────────┘
```

| Container | Language | Responsibility | Scales by |
|---|---|---|---|
| `edge` | Caddy | TLS, reverse proxy, request limits | 1 instance |
| `core-api` | NestJS | All business modules (identity, incidents, missions, cases, hazards, routing, reports, citizens), authentication, setting the RLS session user, WebSocket gateway, enqueuing AI jobs | CPU, replicas |
| `ai-damage` | Python, FastAPI | Damage classification of building crops (F1) | GPU |
| `ai-person` | Python, FastAPI | Person detection and tracking (F3, F4) | GPU |
| `ai-embed` | Python, FastAPI | Image embeddings for similarity search | GPU or CPU |
| `imagery-worker` | Python | Orthomosaic, surface models and 3D mesh (for example OpenDroneMap) | CPU, long jobs |
| `tiles` | Martin or TiTiler | Vector and raster map tiles straight from PostGIS and the orthomosaics | CPU |
| `db` | PostgreSQL 18 | All data, spatial queries, routing, job queue | 1 primary |
| `storage` | MinIO | Images, rasters, report PDFs | disk |

Each AI service is one model family, so a model can be retrained, versioned and redeployed without touching the others, and the core backend keeps working when an AI service is down (requirement NFR-RL-04).

## 4. How the backend talks to the AI models

Two paths, chosen by how long the work takes.

**Asynchronous jobs (most AI work).** Analysis of a drone flight takes minutes, so it is never done inside a user's request.

1. `core-api` inserts a row in `processing_jobs` (already in the schema) and returns at once.
2. A worker inside the AI container claims the next job with `SELECT ... FOR UPDATE SKIP LOCKED`, so two workers never take the same job.
3. The worker reads the images from object storage, runs the model, writes results (detections, assessments, masks) to the database with the model version (FR-IM-07), and updates job progress.
4. `core-api` hears the change through Postgres `LISTEN/NOTIFY` and pushes progress to the user over WebSocket.

This uses the database as the queue, so there is no extra broker to run. If the volume of jobs ever outgrows it, swap in Redis Streams or RabbitMQ behind the same job interface.

**Synchronous calls (short work).** For quick operations, such as embedding one image for a search or re-scoring one detection, `core-api` calls the AI service's internal REST endpoint directly, with a timeout and a fallback message if the service is unavailable.

**Contracts.** Each AI service publishes an OpenAPI document (FastAPI generates it). Requests and responses are versioned (`/v1/...`). The core backend generates a typed client from it, the same way the frontend already generates its client with `pnpm generate:api`.

## 5. AI serving framework

| Option | Strength | Weakness for us | Verdict |
|---|---|---|---|
| FastAPI | Simplest; full control of pre- and post-processing; the team already uses it in `api/` | No built-in batching or GPU scheduling | **Use now** |
| BentoML | Python-first packaging, adaptive batching, model store | Another framework to learn | Optional later, inside the same service contract |
| NVIDIA Triton | Fastest GPU serving, dynamic batching, many model formats on one GPU | Model export (ONNX/TensorRT), heavier operations | Only if live video detection needs low latency |
| Ray Serve | Multi-model pipelines across a cluster | Cluster to operate | Not needed at this scale |
| TorchServe | | Repository archived | Avoid |

Our AI workload is mostly batch jobs on uploaded imagery, so raw request latency matters less than reliability and traceability. FastAPI is enough. Because the backend talks only to the service contract, a service can move to BentoML or Triton internally without any change in `core-api`.

## 6. Core backend: NestJS

NestJS is chosen for the core because:

- its module system maps one to one to the eight data domains, which keeps the monolith modular;
- it is TypeScript, so request and event types can be shared with the web and mobile apps through `frontend/packages/contracts`;
- it has first-class WebSockets, guards for roles and permissions, and a microservices transport layer, so a module can later be extracted into its own service without rewriting it.

Keeping Python only in the AI containers gives a clean line: TypeScript for the platform, Python for the models.

## 7. Frontend

**Web: React + Vite SPA, TanStack Router and TanStack Query.** The command console sits behind a login, has no public pages and needs no search-engine indexing, so server-side rendering adds cost and no benefit. TanStack Router gives fully typed routes and URL search parameters (useful for map filters and selected incidents), and TanStack Query handles caching, retries and WebSocket-driven cache updates. This fits the existing `frontend/apps/web` (React + Vite).

- TanStack Start (the full-stack framework) reached 1.0 only recently and its strengths (server functions, SSR) are not needed here.
- Next.js centres on server components and is strongest on Vercel; also not needed for a logged-in dashboard.

**Mobile: Expo.** The React Native documentation recommends a framework for new apps and names Expo as the one it recommends. The mobile app shares `packages/api` and `packages/contracts` with the web app.

## 8. Repository layout

```
backend/
  core-api/            NestJS modular monolith (modules per domain)
  services/
    ai-damage/         FastAPI + model, Dockerfile, OpenAPI
    ai-person/
    ai-embed/
    imagery-worker/
  contracts/           OpenAPI and event schemas shared by all services
database/              existing schema, seeds, tests
frontend/              existing Turborepo: apps/web, apps/mobile, packages/*
deploy/
  docker-compose.yml   local stack (all containers)
  docker-compose.gpu.yml
```

## 9. Rules that keep it professional

- One database owner: only `core-api` and the workers write, through the roles already defined (`rv_app`, `rv_worker`). AI services never use the admin role.
- Every container has a health endpoint, structured JSON logs with a request ID, and OpenTelemetry traces, so one request can be followed from the web app to the AI service.
- Every AI result stores the model version and inference run (already in the schema).
- Images are passed by object-storage key, never as large request bodies.
- Secrets come from environment variables or Docker secrets, never from the repository.
- CI builds and tests each container separately and runs the database checks in `database/tests/checks.sql`.

## 10. When to split further

Extract another service from `core-api` only when one of these is true, and record the reason as a new design decision:

- one module needs to scale very differently (for example, responder position ingestion at high frequency);
- one module needs a different release cycle or a different team;
- a failure in one module keeps taking down the others.

## Sources

- Encore, "Monolith vs microservices": https://encore.dev/articles/monolith-vs-microservices
- M. Jovanović, "Modular Monolith vs Microservices: How to Choose": https://milanjovanovic.tech/blog/modular-monolith-vs-microservices.md
- DevX, "Microservices vs Monolith: How to Choose in 2026": https://www.devx.com/development/microservices-vs-monolith-how-to-choose-2026/
- K. Grzybek, modular-monolith-with-ddd (GitHub reference architecture): https://github.com/kgrzybek/modular-monolith-with-ddd
- Google Cloud, microservices-demo (GitHub reference microservices system): https://github.com/GoogleCloudPlatform/microservices-demo
- .NET eShop (GitHub reference application): https://github.com/dotnet/eShop
- Model serving comparison (Triton, TorchServe, BentoML, KServe): https://neelmishra.github.io/blog/mlops/model-serving/serving-comparison.html
- PyTorch deployment stacks compared: https://markaicode.com/best/best-pytorch-deployment-stack/
- Node.js and Python AI microservices integration (REST, gRPC, queues): https://www.technetexperts.com/grpc-vs-rabbitmq-nodejs-python-ai/
- ML serving through a message queue (GitHub template): https://www.github.com/gasparian/ml-serving-template
- NestJS microservices guide: https://encore.dev/resources/nestjs-microservices-guide
- TanStack Start comparison: https://tanstack.com/start/latest/docs/framework/react/comparison
- Netlify, TanStack Start vs Next.js: https://www.netlify.com/knowledge-base/tanstack-start-vs-nextjs/
- The New Stack, Next.js vs React Router vs TanStack: https://thenewstack.io/next-js-react-router-tanstack-when-to-use-each/
- React Native, "Use a framework to build React Native apps": https://reactnative.dev/blog/2024/06/25/use-a-framework-to-build-react-native-apps
