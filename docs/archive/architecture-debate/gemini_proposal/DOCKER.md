# Docker & Container Architecture (`DOCKER.md`)

RescueVision separates **always-on interactive services** (CPU), **geospatial/photogrammetry services** (Martin, TiTiler, NodeODM), and **stateless GPU AI model containers** (LitServe) across explicit Docker Compose profiles.

---

## 1. Design Principles for Containerization

1. **Runtime & Dependency Isolation:** Each AI model family owns its own `Dockerfile` and CUDA/PyTorch pin so `SegFormer`/`DINOv2` upgrades never break `YOLO`/`ByteTrack` or `rasterio`/GDAL in the backend.
2. **Zero-Privilege AI Containers:** AI serving containers sit on an internal-only Docker bridge network (`ai-net`). They have **no database credentials**, **no MinIO root keys** (preferring pre-signed URLs or mounted read-only tile/weight volumes), and **no public port bindings** in production.
3. **Laptop-Friendly Development:** Teammates without an NVIDIA GPU can run the full web, mobile, DB, tile, and job-pipeline stack using `docker-compose.cpu-mock.yml`, which substitutes deterministic lightweight mock/ONNX-CPU model responders implementing the exact LitServe HTTP contract.

---

## 2. Complete Container Inventory

| Service Name | Image / Dockerfile Location | Network(s) | Ports (Dev) | GPU | Role & DB Account |
|---|---|---|---|---|---|
| `proxy` | `caddy:2-alpine` (`infra/caddy/Caddyfile`) | `public-net`, `app-net` | `80`, `443` | No | TLS termination, routes `/api` & `/ws` → `core-api`, `/tiles/vector` → `martin` (auth-checked), `/tiles/raster` → `titiler`. |
| `web` | `frontend/apps/web/Dockerfile` (Nginx static SPA) | `public-net` | `5173` (dev) | No | Serves built Vite + TanStack Router SPA. |
| `core-api` | `backend/api/Dockerfile` | `app-net`, `data-net` | `8000` | No | FastAPI Modular Monolith (`rv_app`, `rv_citizen`). |
| `geo-worker` | `backend/workers/Dockerfile` | `app-net`, `data-net`, `ai-net` | — | No | `Procrastinate` worker (`rv_worker`): COG tiling, NodeODM/LitServe orchestration, PDF reports. |
| `postgres` | `pgvector/pgvector:pg18` + PostGIS 3.6 + pgRouting 4.0 custom `infra/postgres/Dockerfile` | `data-net` | `55432` | No | 56-table relational + spatial + graph + vector database. |
| `pgbouncer` | `edoburu/pgbouncer` | `data-net` | `6432` | No | Transaction-mode connection pooler (prod/staging). |
| `redis` | `redis:7-alpine` | `app-net` | `6379` | No | Ephemeral WebSocket Pub/Sub fan-out, OTP rate limiting, GPS ping coalescing. |
| `minio` | `minio/minio` | `data-net`, `app-net` | `9000`, `9001` | No | Private S3-compatible object store (imagery, COGs, 3D tiles, reports, model weights). |
| `martin` | `ghcr.io/maplibre/martin` | `app-net`, `data-net` | `3000` | No | Rust PostGIS MVT vector tile server (scoped via signed incident token). |
| `titiler` | `ghcr.io/developmentseed/titiler` | `app-net`, `data-net` | `8080` | No | Dynamic Cloud-Optimized GeoTIFF raster tile server reading from MinIO. |
| `nodeodm` | `opendronemap/nodeodm` | `ai-net` | `3001` (internal) | Optional | Headless drone photogrammetry (orthomosaic, DSM, 3D mesh). |
| `ai-damage-svc` | `ai/services/damage/Dockerfile.gpu` | `ai-net` | `8101` (internal) | **Yes** | LitServe: building seg, Siamese/ChangeFormer change, DINOv2 damage grading. |
| `ai-person-track-svc` | `ai/services/person_track/Dockerfile.gpu` | `ai-net` | `8102` (internal) | **Yes** | LitServe: occluded aerial person detection (YOLO) + ByteTrack. |
| `ai-flood-road-svc` | `ai/services/flood_road/Dockerfile.gpu` | `ai-net` | `8103` (internal) | **Yes** | LitServe: FloodNet SegFormer water & road obstruction segmentation. |
| `ai-embed-svc` | `ai/services/embeddings/Dockerfile.gpu` | `ai-net` | `8104` (internal) | **Yes** | LitServe: DINOv2 768-d embeddings for `image_embeddings`. |

---

## 3. Docker Compose Topology & Commands

### Compose File Split (`infra/`)
1. **`infra/docker-compose.yml` (Core Baseline):** Starts `postgres`, `minio`, `redis`, `core-api`, `geo-worker`, `martin`, `titiler`, `proxy`, and `web` (plus `pgbouncer` under `prod` profile).
2. **`infra/docker-compose.gpu.yml` (Real AI + Photogrammetry Overlay):** Adds `nodeodm` and the four `ai-*-svc` GPU services with `deploy.resources.reservations.devices` (`driver: nvidia`, `capabilities: [gpu]`), mounting read-only model weights (`./weights:/models:ro` or pulling pinned SHA-256 weights from MinIO at container startup).
3. **`infra/docker-compose.cpu-mock.yml` (No-GPU Developer Overlay):** Runs lightweight CPU/mock implementations of `ai-*-svc` returning deterministic fixtures on the same ports (`8101`–`8104`), allowing full CI and laptop UI/API testing without CUDA.
4. **`infra/docker-compose.obs.yml` (Observability Overlay):** Adds OpenTelemetry Collector, Prometheus, Grafana, and NVIDIA DCGM exporter.

### Canonical Startup Commands
```bash
# Laptop dev (no GPU required — uses deterministic mock/tiny AI responders)
docker compose -f infra/docker-compose.yml -f infra/docker-compose.cpu-mock.yml up --build

# Full GPU workstation / live graduation demo
docker compose -f infra/docker-compose.yml -f infra/docker-compose.gpu.yml up --build

# Run database schema build & RLS self-checks inside clean Postgres
PGHOST=localhost PGPORT=55432 PGUSER=postgres ./database/build.sh
```

---

## 4. How AI Containers Are Isolated & Invoked

```text
  [geo-worker]  ---(internal Docker network: ai-net, HTTP/2)--->  [ai-damage-svc :8101]
       │                                                                  │
       ├── 1. Reads processing_jobs (SKIP LOCKED, rv_worker)              ├── Zero DB creds
       ├── 2. Fetches COG window / building crops from MinIO              ├── Stateless GPU batching
       ├── 3. POST /v1/predict (binary tiles + metadata JSON)             ├── Model weights pinned by sha256
       └── 4. Records inference_runs + building_assessments in Postgres   └── GET /v1/model-info & /health
```

* **Contract Enforcement:** Every `ai-*-svc` exposes three identical routes powered by `ai/common/` (`LitServe`):
  * `GET /health` → `200 OK` only after weights are loaded on GPU/CPU and a 1-tile warmup pass succeeds.
  * `GET /v1/model-info` → `{ "name": "...", "version": "...", "task": "...", "architecture": "...", "weights_sha256": "..." }`. `geo-worker` checks this against `ai_models` before writing `inference_runs`.
  * `POST /v1/predict` → Accepts `multipart/form-data` or binary tensor/image batch + JSON params; returns structured predictions + per-class probabilities + model execution time.
* **Failure Containment (`NFR-RL-04`):** If `ai-damage-svc` OOMs or restarts, `core-api`, `martin`, `titiler`, routing, and mobile SOS continue serving with zero downtime. `geo-worker` catches the `5xx`/timeout, retries with exponential backoff (up to 3 attempts), or marks the `processing_jobs` row `FAILED` with `error_message` for Analyst retry.

---

## 5. Production Pilot Deployment Strategy

* **Tier 1 — Always-On Core VM (CPU, 8 vCPU / 32 GB RAM / NVMe):** Runs `proxy`, `core-api` (2+ replicas), `pgbouncer`, `postgres` (with daily `pgBackRest`/WAL-G off-site backups per `NFR-RL-05`), `minio` (or managed S3), `redis`, `martin`, `titiler`, and `web` static assets.
* **Tier 2 — On-Demand GPU Burst Node(s):** Provisioned during active incidents or demos (e.g., cloud L4/A10G VM) running `docker-compose.gpu.yml` connected over WireGuard/private VPC to `geo-worker` or running `geo-worker` + `ai-*-svc` co-located to minimize image transfer latency over S3. Shut down when idle to keep pilot operating costs near zero (Table 3-40).
