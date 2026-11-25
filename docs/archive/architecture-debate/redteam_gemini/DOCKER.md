# RescueVision — Docker, Compose Profiles & GPU Isolation Blueprint

> **Goal:** Any developer or AI agent can boot the **Core Platform** on a standard 16 GB CPU laptop (`infra/compose/docker-compose.yml`), add the **Packed GPU AI + Photogrammetry Plane** on a workstation with an NVIDIA GPU (`docker-compose.gpu.yml`), or run the **Disconnected Field Kit** on a drone ground-station laptop (`docker-compose.edge.yml`)—with **zero CUDA context waste** and **strict network isolation**.

---

## 1. Exact Dockerfile Locations & Responsibilities

| Dockerfile Path | Base Image | Target / Purpose | Key Contents & Hard Rules |
|---|---|---|---|
| `database/Dockerfile` | `pgrouting/pgrouting:18-3.6-4.0` | `postgres` (PG 18 + Spatial + Vector + Partitioning) | Installs `postgresql-18-pgvector` and `postgresql-18-partman` from PGDG apt repo. **Mounts volume at `/var/lib/postgresql`** (PG 18 `PGDATA` layout). |
| `backend/Dockerfile` | `python:3.12-slim` (multi-stage with `uv`) | Two build targets: `api` (`core-api`) and `geo-worker` | `api`: FastAPI, `psycopg3`, `shapely`, `nats-py`, `pydantic-ai`, `curl`. `geo-worker`: adds `rasterio`, `pyproj`, `tritonclient[grpc]`, `weasyprint`, `pillow` (EXIF scrub). **Zero PyTorch / CUDA.** |
| `frontend/apps/web/Dockerfile` | `node:22-alpine` → `nginx:alpine` (dev uses Vite HMR) | `web` Command Console | Builds `apps/web` static bundle from `packages/*`; served behind `caddy`. |
| `frontend/apps/citizen/Dockerfile` | `node:22-alpine` → `nginx:alpine` | `citizen` Rapid Intake PWA | Ultra-lean PWA asset image; isolated origin/route prefix in Caddy. |
| `ai/Dockerfile.train` | `nvcr.io/nvidia/pytorch:25.02-py3` (or CUDA 12.x) | Offline training / evaluation / ONNX export only (NOT in prod compose) | Installs `ai/` editable + `torchgeo`, `terratorch`, `torchange`, `ultralytics`, `onnxruntime-gpu`, `mlflow`. |
| `ai/Dockerfile.edge` | `mcr.microsoft.com/onnxruntime/server` or Python 3.12 + `onnxruntime-gpu` | `edge-detector` (Field Drone GCS) | Runs lightweight `YOLOv8s` + `ByteTrack` over MediaMTX RTSP/KLV stream; ~400 MB footprint. |

> **Note on Triton, NodeODM, OpenSplat, MediaMTX, Caddy, PowerSync, TiTiler, NATS, MinIO, Redis, PgBouncer:** Use **pinned official upstream images** (no custom Dockerfiles needed—only checked-in config files under `infra/` and `triton-repo/`).

---

## 2. Container Inventory & Network Isolation

### 2.1 Networks (Least-Privilege Segmentation)
1. **`edge-public`:** Only `caddy` binds host ports `80`/`443` (plus `mediamtx` UDP/TCP `8554`/`8890` for drone ingest and `nats` `:7422` TLS for edge leaf sync).
2. **`app-core`:** `caddy`, `web`, `citizen`, `core-api`, `titiler`, `powersync`, `mediamtx`, `nats`, `redis`, `minio`. Cannot talk directly to Triton or raw Postgres superuser.
3. **`data-internal` (`internal: true`):** `postgres`, `pgbouncer`, `core-api`, `geo-worker`, `powersync`, `redis`, `nats`. Completely unreachable from browser/internet.
4. **`ai-internal` (`internal: true`):** `geo-worker`, `triton`, `nodeodm`, `opensplat`. **AI containers (`triton`, `nodeodm`, `opensplat`) sit ONLY on `ai-internal`**—they have **no internet access**, **no Postgres credentials**, and **cannot be called by `core-api` or `caddy` directly**.

### 2.2 Complete Service Matrix

| Container | Compose Profile | Image | Network(s) | Role & Why It Exists |
|---|---|---|---|---|
| `caddy` | `core` | `caddy:2.9-alpine` | `edge-public`, `app-core` | Single TLS ingress, `forward_auth` verification via `core-api`, routes `/api/*`, `/ws/*`, `/tiles/*`, `/media/*`, `/powersync/*`, `/`, `/citizen/*`. |
| `postgres` | `core` | Custom `database/Dockerfile` | `data-internal` | PG 18 + PostGIS 3.6 + pgRouting 4 + pgvector + `pg_partman`. Single ACID source of truth. WAL level = `logical` for PowerSync. |
| `pgbouncer` | `core` | `edoburu/pgbouncer:1.24` | `data-internal` | Transaction pooling in front of `postgres` for `core-api` (`psycopg3` `prepare_threshold=None`). |
| `minio` | `core` | `minio/minio:RELEASE.2025-...` | `app-core`, `data-internal` | Private S3 buckets (`raw-imagery`, `cog-products`, `3d-artifacts`, `citizen-quarantine`, `reports-pdf`, `model-artifacts`). |
| `nats` | `core` | `nats:2.14.1-alpine` | `edge-public` (`:7422` TLS), `app-core`, `data-internal` | JetStream hub: outbox relay, WebSocket fan-out, instant revocation (`rv.sec.revoked_users`), edge leaf sync. |
| `redis` | `core` | `redis:7.4-alpine` | `app-core`, `data-internal` | Short-TTL cache for RLS-scoped `ST_AsMVT` vector tiles + Caddy rate-limit store. |
| `powersync` | `core` | `journeyapps/powersync-service` | `app-core`, `data-internal` | Streams WAL-replicated subsets to Expo `OP-SQLite` clients; receives offline write batches back through `core-api`. |
| `core-api` | `core` | `backend/Dockerfile` (`api`) | `app-core`, `data-internal` | FastAPI monolith: REST, WS, `ST_AsMVT` tile proxy, `forward_auth`, `PydanticAI` copilot, outbox relay. Connects via `rv_app` / `rv_citizen` / `rv_readonly`. |
| `geo-worker` | `core` | `backend/Dockerfile` (`geo-worker`) | `data-internal`, `ai-internal`, `app-core` | `Procrastinate` (`SKIP LOCKED`) worker (`rv_worker`): `NodeODM` stitching, SAHI tiling, calls `triton` over gRPC, calibration, DSM raycasting, EXIF scrubbing, `WeasyPrint` PDFs. Runs in graceful CPU-mock/no-GPU mode if `gpu` profile is off. |
| `titiler` | `core` | `ghcr.io/developmentseed/titiler` | `app-core` | Streams COG orthomosaics via S3 byte-range requests behind Caddy `forward_auth`. |
| `mediamtx` | `core` | `bluenviron/mediamtx:1.17` | `edge-public`, `app-core` | Low-latency RTSP/SRT/WebRTC WHEP relay passing `SMPTE 336M` KLV drone telemetry unchanged. |
| `web` / `citizen` | `core` | `frontend/apps/*/Dockerfile` | `app-core` | Static SPA/PWA builds (or Vite dev servers in `docker-compose.override.yml`). |
| **`triton`** | **`gpu`** | `nvcr.io/nvidia/tritonserver:25.02-py3` | `ai-internal` | **ONE container, ONE CUDA context** serving `joint_damage`, `post_damage_probe`, `rtdetr_sar`, `yolov8s_sar`, `flood_road_seg`, and `eo_embedder` via C++ ONNX Runtime / TensorRT backends. |
| **`nodeodm`** | **`gpu`** | `opendronemap/nodeodm:gpu` | `ai-internal` | Converts raw drone surveys into orthomosaic COGs, DSM GeoTIFFs, and OGC 3D Tiles. |
| **`opensplat`** | **`gpu-3dgs`** | `ghcr.io/webodm/opensplat` (optional) | `ai-internal` | On-demand 3D Gaussian Splatting (`.rad`/`.spz`) for commander-flagged priority collapse blocks. |
| **`edge-nats` + `edge-mediamtx` + `edge-detector` + `meshsat`** | **`edge`** | Field kit (`docker-compose.edge.yml`) | `edge-lan` | Autonomous field laptop/Jetson stack: live `YOLOv8s` on RTSP+KLV, local `NATS Leaf` store-and-forward, `MeshSat` LoRa relay. |

---

## 3. Compose Topology & GPU Isolation Mechanics

### 3.1 Compose Files (`infra/compose/`)
- `infra/compose/docker-compose.yml` — Base **CPU core** stack (`postgres`, `pgbouncer`, `minio`, `nats`, `redis`, `powersync`, `core-api`, `geo-worker`, `titiler`, `mediamtx`, `caddy`, `web`, `citizen`). Uses named healthchecks (`curl -f` or `pg_isready`) on every service.
- `infra/compose/docker-compose.override.yml` — Local dev DX overrides (bind-mounts `backend/src`, Vite dev servers with HMR, exposes local Grafana/Prometheus/Adminer ports).
- `infra/compose/docker-compose.gpu.yml` — Adds `triton`, `nodeodm`, and optional `opensplat`:
  ```yaml
  services:
    triton:
      image: nvcr.io/nvidia/tritonserver:25.02-py3
      command:
        - tritonserver
        - --model-repository=/models
        - --model-control-mode=poll
        - --repository-poll-secs=30
        - --strict-model-config=true
      volumes:
        - ../../triton-repo:/models:ro
      networks: [ai-internal]
      deploy:
        resources:
          reservations:
            devices:
              - driver: nvidia
                count: 1
                capabilities: [gpu]
      healthcheck:
        test: ["CMD", "curl", "-f", "http://localhost:8000/v2/health/ready"]
        interval: 15s
        retries: 5
  ```
- `infra/compose/docker-compose.edge.yml` — Portable **Disconnected Field Kit** for drone ground stations (`edge-mediamtx`, `edge-nats` leaf pointing to HQ `:7422`, `edge-detector`, `meshsat`).

### 3.2 How AI Is Isolated & Called (Zero Dual-Responsibility)
1. **Why ONE Triton Server instead of 4 Python GPU containers:** Separate FastAPI/LitServe containers spawn 4 OS processes → 4 independent CUDA contexts (`~0.5–1.5 GB` VRAM overhead each) + no shared dynamic batching. Triton's C++ `onnxruntime` and `tensorrt` backends load all models inside **one OS process and one CUDA context**, isolating workloads via concurrent **CUDA streams**, `instance_group`, and `dynamic_batching` in `config.pbtxt`.
2. **Backend Isolation (`NFR-RL-04`):** `core-api` NEVER imports Triton clients and NEVER blocks an HTTP request waiting on GPU inference.
   - `core-api` writes a row to `processing_jobs` (`PENDING`) and returns `202 Accepted`.
   - `geo-worker` polls `processing_jobs` with `FOR UPDATE SKIP LOCKED`, prepares image tiles in Python (`rasterio`), calls `triton:8001` via KServe v2 gRPC (`tritonclient.grpc.aio`), calibrates logits, raycasts against the DSM, and commits results inside an ACID Postgres transaction.
   - If `triton` is crashed, restarting, or absent (CPU-only dev laptop), `core-api`, routing, hazard alerts, PowerSync, and MapLibre keep running with zero downtime; `processing_jobs` cleanly retries or marks `FAILED` with clear diagnostics.
