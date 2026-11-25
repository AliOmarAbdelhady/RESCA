# Docker: containers, images and Compose

*Draft blueprint. It defines every container, where its Dockerfile lives, the Compose files for development and for the server, one optional override for a workstation with a GPU, and how the AI containers are isolated and called. The Contabo server has no GPU and no budget for one: everything the server runs is designed for CPU, for a single-user demonstration.*

## 1. Principles

1. **Everything that runs is a container.** PostgreSQL, the object store, the proxy, the application, the AI services and the tile server all run under Docker Compose. Nothing is installed directly on the host except Docker, Git and a few utilities.
2. **One Dockerfile per buildable unit, next to its code.** No Dockerfile at the repository root.
3. **The design target is CPU.** No image needs a GPU. GPU support exists only as an optional override for a developer workstation. Training itself runs on free Kaggle or Colab GPUs (`AI_TRAINING_LAYOUT.md` §12), so the override is a convenience, not a dependency.
4. **No GPU library in a serving image.** The AI serving images contain an inference runtime and exported model files, not a training framework. That keeps them small and quick to pull on the server.
5. **Nothing is stateful outside volumes.** Application containers are stateless and can be replaced at any time.
6. **Images are pinned.** Development uses tags; `compose.prod.yaml` pins every image by digest.

## 2. Images and Dockerfiles

| Image | Dockerfile | Built from | Contains | Size discipline |
| --- | --- | --- | --- | --- |
| `backend` (targets `api`, `worker`) | `backend/Dockerfile` | `python:3.12-slim` | FastAPI, SQLAlchemy, asyncpg, rasterio, shapely, the `rescuevision` package | Multi-stage; no build tools in the final image |
| `postgres` | `database/Dockerfile` | Official PostgreSQL 18 image | PostGIS, pgRouting and pgvector from the PostgreSQL package repository listed in `database/README.md` | One image for development, CI and the server |
| `infer-base` | `ai/services/base/Dockerfile` | `python:3.12-slim` | ONNX Runtime, OpenVINO, OpenCV, rasterio, shapely, numpy, pydantic, an ASGI server, `ai.libs.serving` | No torch. No database driver |
| `infer-damage` | `ai/services/damage/Dockerfile` | `infer-base` | The service code and the exported, quantised model files for its task | Models copied in at build time and checked against their SHA-256 |
| `infer-people` | `ai/services/people/Dockerfile` | `infer-base` | Same | Same |
| `infer-hazard` | `ai/services/hazard/Dockerfile` | `infer-base` | Same | Same |
| `infer-embed` | `ai/services/embed/Dockerfile` | `infer-base` | Same | Same |
| `web` | `frontend/apps/web/Dockerfile` | Node for the build, a small static server for runtime | The built console bundle | Static files only |
| `citizen` | `frontend/apps/citizen/Dockerfile` | Same | The built citizen page | Static files only |
| `training` (optional) | `ai/training/Dockerfile` | Python with the training stack | torch, the training library | For a workstation only. The notebooks otherwise run on Kaggle or Colab |
| Third-party | Pulled, not built | Traefik, TiTiler, NodeODM (bundle builds only), Prometheus, Grafana, Uptime Kuma | — | Pinned by digest |

Python version: the current releases of `torch` and `onnxruntime` on PyPI require Python 3.11 or newer (checked on 2026-11-25). The repository pins one version, 3.12, everywhere.

The mobile app has no Dockerfile. It is built with Expo's tooling.

## 3. Compose files

All Compose files live in `deploy/compose/`. They are combined with `-f`, which Docker Compose merges according to documented rules [B4]. The Makefile wraps the long commands.

| File | Purpose | Used by |
| --- | --- | --- |
| `compose.yaml` | The base. Networks, volumes, the core services, and the optional services behind profiles. | Every environment |
| `compose.dev.yaml` | Override for development. Bind mounts, hot reload with Compose watch [B3], debugging ports. | `make dev` |
| `compose.prod.yaml` | Override for the server. Image digests, CPU and memory limits, log rotation, restart policies, read-only root file systems. | Staging and production |
| `compose.gpu.yaml` | Override that attaches NVIDIA GPUs [B2] to the AI services and adds a training service. **Only for a workstation that has an NVIDIA GPU. Never applied on the server.** | `make dev-gpu` |
| `compose.observability.yaml` | Profile `observability`: Prometheus, Grafana and Uptime Kuma. | Optional |

Profiles [B1] group services so that `docker compose up` starts only what is needed:

| Profile | Services | When it is used |
| --- | --- | --- |
| none (default) | `proxy`, `web`, `api`, `worker`, `postgres`, `object-store`, `tiler` | Always |
| `models` | `infer-damage`, `infer-people`, `infer-hazard`, `infer-embed` | When on-demand analysis is demonstrated |
| `stitch` | `stitch` (NodeODM) | Only when an evidence bundle is built. Never during a demonstration, which starts from the precomputed bundle |
| `observability` | Metrics, dashboards, uptime checks | Staging and production |

A single-user demo starts the default profile and `models`. The four model containers hold only an inference runtime and the exported weights, about 1.4 to 2.3 GB together once warm, and only one of them computes at any moment. One stack then peaks at about 5 to 6.5 GB, which is why it fits on a 24 GB host (`../cpu_demo_feasibility.md` §3.3, §4.2).

### Skeleton of `compose.yaml`

The names below are the contract between the documents. Values are illustrative until Milestone 1.

```yaml
name: rescuevision                       # overridden per environment: rescuevision-staging, rescuevision-prod

x-logging: &logging
  driver: json-file
  options: { max-size: "20m", max-file: "5" }

services:
  proxy:
    image: traefik:v3                   # pinned by digest in compose.prod.yaml
    ports: ["80:80", "443:443"]
    networks: [edge]
    volumes:
      - letsencrypt:/letsencrypt
      - ../proxy/traefik.yml:/etc/traefik/traefik.yml:ro

  web:
    build: { context: ../../frontend, dockerfile: apps/web/Dockerfile }
    networks: [edge]
    labels: { traefik.enable: "true" }  # full routing labels live in this file

  api:
    build: { context: ../../backend, target: api }
    command: ["uvicorn", "rescuevision.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
    networks: [edge, app, db, storage]
    environment:
      DATABASE_URL_FILE: /run/secrets/db_url_app
      S3_ENDPOINT_URL: http://object-store:9000
      S3_BUCKET: rescuevision
      OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4318
    secrets: [db_url_app, db_url_citizen, s3_credentials]
    depends_on:
      postgres: { condition: service_healthy }
      object-store: { condition: service_started }
    healthcheck: { test: ["CMD", "python", "-m", "rescuevision.app.healthcheck"], interval: 15s }

  worker:
    build: { context: ../../backend, target: worker }
    command: ["python", "-m", "rescuevision.worker"]
    networks: [app, db, storage, infer]
    environment:
      WORKER_CONCURRENCY: "1"           # one job at a time on a CPU host
      INFERENCE_THREADS: "4"            # set to the physical cores given to inference
    secrets: [db_url_worker, s3_credentials]
    depends_on:
      postgres: { condition: service_healthy }

  postgres:
    build: { context: ../../database }
    networks: [db]
    environment: { POSTGRES_DB: rescuevision, POSTGRES_PASSWORD_FILE: /run/secrets/db_admin_password }
    secrets: [db_admin_password]
    volumes: [pgdata:/var/lib/postgresql]
    healthcheck: { test: ["CMD-SHELL", "pg_isready -U postgres -d rescuevision"], interval: 10s }

  object-store:
    image: <s3-store, SeaweedFS by default>:<tag>    # pinned by digest in compose.prod.yaml
    networks: [storage]
    volumes: [objects:/data]
    command: server /data

  tiler:
    image: ghcr.io/developmentseed/titiler:<tag>
    networks: [edge, storage]

  infer-damage:
    build: { context: ../../ai, dockerfile: services/damage/Dockerfile }
    profiles: [models]
    networks: [infer, storage]           # not on `db`: the database is unreachable
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    deploy: { resources: { limits: { cpus: "4", memory: 4g } } }

  # infer-people, infer-hazard, infer-embed: same shape

  stitch:
    image: opendronemap/nodeodm:<tag>
    profiles: [stitch]                 # bundle builds only; never started for a demonstration
    networks: [infer, storage]
    volumes: [odm_data:/data]

networks:
  edge: {}        # proxy to web, api, tiler
  app: {}         # api to worker
  db: {}          # api, worker to postgres
  storage: {}     # api, worker, tiler, AI services to object storage
  infer: {}       # worker to AI services and stitch

volumes:
  pgdata: {}
  objects: {}
  odm_data: {}
  letsencrypt: {}

secrets:
  db_url_app:         { file: ${RV_SECRETS_DIR}/db_url_app }         # outside the repository
  db_url_citizen:     { file: ${RV_SECRETS_DIR}/db_url_citizen }
  db_url_worker:      { file: ${RV_SECRETS_DIR}/db_url_worker }
  db_admin_password:  { file: ${RV_SECRETS_DIR}/db_admin_password }
  s3_credentials:     { file: ${RV_SECRETS_DIR}/s3_credentials }
```

Notes on the skeleton:

- CPU and memory limits use `deploy.resources.limits` from the Compose file reference [B6]. Confirm that the installed Compose version applies them with `docker compose up`; the service-level `cpus` and `mem_limit` keys are the alternative.
- `object-store` publishes only its S3 port, and only on the `storage` network. The SeaweedFS admin interface and WebDAV are reachable without authentication, so Compose exposes them nowhere (`HOSTING_CONTABO.md` §6).
- `stitch` is in the file so that a bundle build uses the same code path as development. It is never started for a demonstration (ADR-009 in `ARCHITECTURE.md`).
- Secrets are files outside the repository, in the directory named by `RV_SECRETS_DIR`. In development they are in `~/.config/rescuevision/`: one copy that every worktree reads (`BRANCHING.md` §9). On the server they are in `/var/lib/rescuevision/<project>/secrets/` (`HOSTING_CONTABO.md` §7). `.env.example` lists every variable with a comment and no value; `make setup` writes a first set from it.
- The skeleton shows the structure and the names. It is not a complete file: the proxy routing labels, the remaining AI services, the object store's own configuration and the resource limits for every service are added in Milestone 1.

## 4. How the AI containers are isolated

| Layer | Rule |
| --- | --- |
| Network | AI services are attached only to `infer` and `storage`. The database is on `db`. A model container cannot open a connection to PostgreSQL even if it were given credentials. |
| Exposure | No port is published and no proxy route exists for an AI service. |
| Credentials | No database credentials. No long-lived storage key. The worker puts short-lived presigned URLs in the task itself. |
| Caller | Only `worker` is on the `infer` network. The `api` never calls a model. |
| Job ticket | Every task carries a signed ticket with the job id and an expiry. The service verifies it before reading any input. A task cannot be replayed for another job. |
| Process | Non-root user, read-only root file system, all Linux capabilities dropped, no privilege escalation, a process limit, CPU and memory limits. |
| Supply chain | The Dockerfile base is pinned. The image is scanned in CI. The model file is checked against its SHA-256 at build time. |

## 5. How the backend calls an AI service

1. The worker claims a job from `processing_jobs`.
2. It reads the active model for the task from `ai_models`.
3. It builds a task: the job id, the run id, references to the inputs in object storage (bucket key, bounding box, presigned download URLs), the parameters, and a job ticket.
4. It calls `POST /v1/tasks` and receives a task id immediately.
5. It polls `GET /v1/tasks/{task_id}` and updates `progress_pct`. Progress is reported at least every 30 seconds.
6. The service reads windows of the input rasters, runs the model, writes its products to object storage under `incidents/{incident}/runs/{run}/`, and returns references and a summary.
7. The worker lands the results in PostgreSQL in one transaction, as `rv_worker`, and records the model name and version in `inference_runs`.

The full contract is in `AI_PIPELINE.md` §7 and `CONTRACTS.md`.

## 6. Development workflow

```bash
make setup          # install dependencies for every part
make dev            # core + models + tiler, hot reload for api, worker and web
make dev-gpu        # same, on a workstation with an NVIDIA GPU
make dev-stitch     # adds NodeODM to develop the stitch step; never part of a demonstration
make logs           # follow the application logs
make ps             # what is running
make down           # stop and remove containers; volumes are kept
make clean          # also remove volumes and generated files
```

- Hot reload uses Compose watch for the Python and TypeScript code [B3]. A change to a model file is a new image, never a live edit.
- To debug one AI service without Docker, run it directly from `ai/services/<name>/` with `uv run uvicorn …`. It reads its configuration from environment variables and never needs the database.
- Each Git worktree uses its own Compose project name (`COMPOSE_PROJECT_NAME=rv-<worktree>`), so two agents can run the stack at the same time on different ports.

## 7. Running on CPU: what is different

| Topic | Decision |
| --- | --- |
| Inference runtime | ONNX Runtime on CPU by default, OpenVINO as the alternative, behind one adapter (`AI_PIPELINE.md` §3). A serving image contains no training framework. |
| Threads | The number of inference threads equals the physical cores allocated to the container. ONNX Runtime exposes this as `intra_op_num_threads` [B22]. In the local benchmark, four physical threads beat eight logical threads on the two heaviest graphs (1.7 to 1.9 times) but not on every graph, so each model is measured (`../cpu_demo_feasibility.md` §2). |
| Instruction set | No build, flag or image may assume AVX-512 or VNNI. The Contabo AMD EPYC hosts expose AVX2 only (`../cpu_demo_feasibility.md` §2). |
| Concurrency | The worker runs one job at a time. Model services run one task at a time. Two model jobs never compete for the same cores. |
| Quantisation | int8 only where a measurement shows that it helps, in accuracy and in latency on the reference CPU (`AI_PIPELINE.md` §3). Calibrated static int8 suits the convolution and detector models. Dynamic int8 suited the embedding model but made a depthwise-convolution segmentation model 4.1 times slower, so that model is not quantised (`../cpu_demo_feasibility.md` §2). |
| Heavy work | The orthomosaic, the surface model, 3D products and area-wide analysis are precomputed into the evidence bundle (`AI_PIPELINE.md` §10). On demand, the analyst draws an area of a few tiles or uploads one photo. |
| Tiles | Raster tiles for large orthomosaics are prebuilt into an archive in the bundle. TiTiler serves small and on-demand rasters. |
| 3D | Rendered in the browser with MapLibre GL JS and deck.gl, from products in the bundle. No server-side 3D reconstruction and no splat training. |
| Language model | Not on the server. It is a stretch feature that calls a hosted model (`AI_PIPELINE.md` §13). |

## 8. Building and tagging images

| Where | What happens |
| --- | --- |
| Developer machine | `make images` builds every first-party image for the local architecture. `make image IMAGE=infer-damage` builds one. |
| Pull request | CI builds the images that the change affects, to prove that they build. Nothing is pushed. |
| `main` | CI builds, scans and pushes images to the container registry tagged with the short commit SHA and `edge`. |
| Release tag `vX.Y.Z` | CI builds and pushes the same images tagged `X.Y.Z` and `X.Y`, attaches a software bill of materials, and records the digests in the release notes. |
| AI image | Tagged with the model version and the commit: `infer-damage:damage-assessment-v3-<sha>`. |

`compose.prod.yaml` references images by digest. A deployment is therefore always a known, immutable set of images.

## 9. Open points for Milestone 0 and Milestone 1

- Confirm that the chosen Compose version applies `deploy.resources.limits` outside Swarm, or switch to `cpus` and `mem_limit`.
- Measure the real memory need of each model container with its exported weights, and set the limits from the measurement.
- Run the compatibility suite on SeaweedFS (`HOSTING_CONTABO.md` §6), starting with presigned multipart upload and range reads, before anything else depends on it.
- If a model service must write many output files, decide between a list of pre-signed upload URLs in the task and short-lived storage credentials. That depends on the store's support for temporary credentials.
- Check which NodeODM options reduce processing time for a bundle build, against the version actually used. On a CPU host, 50 to 80 photos take an estimated 12 to 25 minutes and 100 to 200 need about 16 GB of memory (`../cpu_demo_feasibility.md` §3.2).
- Measure on the server itself. A latency from a development machine with AVX-512 does not transfer to the AVX2 host.
