# RescueVision — Contabo Hosting, GPU Tunneling, Backups & Operations (`HOSTING_CONTABO.md`)

> **Reality Anchor:** RescueVision will be hosted on **Contabo (VPS / VDS)**—no managed AWS RDS, no managed S3, and **no managed Kubernetes**. The operational design must stay simple enough for 6 developers to maintain reliably, survive disk/network hiccups, and handle GPU inference cleanly without paying cloud hyperscaler prices.

---

## 1. Orchestration Choice: Docker Compose + Caddy 2 (Why NOT `k3s` or `Kamal`)

| Option | Verdict | Rationale |
|---|---|---|
| **Docker Compose v2 + Caddy 2 + GitHub Actions SSH Deploy** | **CHOSEN (Core)** | Matches `DOCKER.md` identically across laptop dev, CI, staging, and Contabo production. Zero control-plane RAM tax (~1.5 GB saved over `k3s`), effortless debugging (`docker compose logs`), and atomic rollbacks via pinned `ghcr.io` image tags. *(Optionally wrap with lightweight **Coolify** or **Dokploy** ONLY for log viewing/one-click restarts—never replace Compose files with opaque UI-only configs.)* |
| **`k3s` (Lightweight Kubernetes)** | **REJECTED** | Adds etcd/apiserver/kubelet complexity, Ingress/Cert-Manager YAML ceremony, and StatefulSet PostGIS PVC pain on a 1–2 node Contabo setup with zero realistic auto-scaling benefit. |
| **`Kamal`** | **REJECTED** | Great for stateless Rails/web apps, awkward for multi-container stateful geo stacks (`Postgres 18` + `PgBouncer` + `PowerSync` + `NATS` + `MinIO` + `TiTiler` + `MediaMTX`). |

---

## 2. Server Topology: Staging, Production & Hybrid GPU

### 2.1 Recommended Node Layout
1. **Production Node — Contabo Cloud VDS / NVMe VPS (e.g., 6–8 vCPU, 24–32 GB RAM, 300+ GB NVMe):**
   - Runs `docker-compose.yml` (`core` profile): `caddy`, `postgres` (PG18 + `/var/lib/postgresql`), `pgbouncer`, `minio`, `nats`, `redis`, `powersync`, `core-api`, `geo-worker`, `titiler`, `mediamtx`, `web`, `citizen`, plus `prometheus`/`grafana`/`loki`.
2. **Staging Node — Smaller Contabo VPS (e.g., 4 vCPU, 8–12 GB RAM):**
   - Runs identical Compose topology on `staging.rescuevision.<domain>` with smaller Cairo/test datasets and synthetic load tests before any `v*` production tag. *(If budget allows only 1 VPS initially, run staging as a separate Compose project `-p rv-staging` with separate `.env.staging`, Postgres volume, and Caddy subdomain—strictly isolated from prod volumes.)*

### 2.2 GPU Availability Strategy (Crucial for Contabo!)
Standard Contabo VPSs **do not include NVIDIA GPUs**. Design RescueVision so the Contabo server works **with or without an attached GPU**:
- **Mode A — Hybrid WireGuard/Tailscale GPU Tunnel (Recommended for Live Demos & Heavy Surveys):**
  - Contabo CPU VPS joins a private encrypted **Tailscale / WireGuard mesh** (`10.88.0.0/24`).
  - A lab workstation GPU (e.g., RTX 3090/4090) or on-demand rental GPU (RunPod / Vast.ai / Lambda) runs `docker-compose.gpu.yml` (`triton`, `nodeodm`, `opensplat`) bound **only** to the Tailscale interface (`10.88.0.10:8001`).
  - `geo-worker` on Contabo calls `TRITON_GRPC_URL=10.88.0.10:8001` transparently over the encrypted tunnel. Zero public GPU ports exposed!
- **Mode B — Quantized CPU Fallback (Always-On Contabo Safety Net):**
  - Lightweight ONNX models (`yolov8s_sar` INT8, `post_damage_probe` linear head) can run inside `geo-worker` or a CPU Triton instance for light single-tile sanity tests if the external GPU node is powered off—while `NodeODM` gracefully falls back to queued status (`"GPU worker offline"`) without taking down `core-api`, routing, or alerts.
- **AI Training (`kaggle/<feature>/vN/`):** Never runs on Contabo production VPS. Always runs on Kaggle / Colab / lab GPU and pushes validated `.onnx` weights to MinIO (`s3://model-artifacts/`).

---

## 3. Reverse Proxy, TLS & Network Hardening

1. **Ingress (`Caddy 2`):**
   - Hosts ports `80/443` exclusively (plus UDP/TCP `8554`/`8890` for `mediamtx` drone streams and `:7422` TLS for `nats` edge leaf nodes).
   - Automatic **Let's Encrypt TLS 1.3** + HTTP→HTTPS redirect + HSTS + security headers (`CSP`, `X-Content-Type-Options`, `Referrer-Policy`).
   - Route table:
     - `app.<domain>` → `web` SPA + `/api/*`, `/ws/*` → `core-api`
     - `app.<domain>/tiles/vector/*` → Caddy `forward_auth` (`core-api /internal/auth`) → `core-api` `ST_AsMVT`
     - `app.<domain>/tiles/raster/*` → Caddy `forward_auth` → `titiler`
     - `app.<domain>/powersync/*` → `powersync`
     - `app.<domain>/media/*` → `mediamtx` (WHEP/WebRTC)
     - `help.<domain>` → `citizen` Rapid Intake PWA (isolated domain/origin so citizen cookies/storage never touch staff console!)
2. **Host Firewall (`ufw`):** Default deny incoming; allow only `22` (SSH key-only, optional Tailscale-only), `80`, `443`, `7422` (NATS Leaf TLS), `8554/8890` (MediaMTX), and WireGuard/Tailscale UDP. Ports `5432` (Postgres), `6432` (PgBouncer), `9000` (MinIO), `8001` (Triton), `6379` (Redis) are **never bound to `0.0.0.0`**.

---

## 4. Secrets Management (`SOPS + age`)

Never leave plaintext `.env.prod` secrets in Git or scatter passwords across ad-hoc shell histories:
- Store encrypted `infra/secrets/prod.enc.env` and `infra/secrets/staging.enc.env` in Git using **`SOPS` + `age`**.
- CI (`cd-deploy.yml`) holds the `AGE_PROD_KEY` inside **GitHub Environment Protected Secrets**, decrypts on deployment into root-only `chmod 600 /opt/rescuevision/.env.prod`, and triggers `docker compose --env-file .env.prod up -d`.
- Rotate JWT signing keys, MinIO keys, and `rv_*` Postgres passwords per environment (`staging` ≠ `prod`).

---

## 5. Backups & Disaster Recovery (Off-Site First!)

Contabo single-node NVMe RAID is **not** a backup. Everything critical must replicate off-site automatically:

1. **PostgreSQL 18 (`pgBackRest` / `pg_dump` + `restic`):**
   - **Continuous WAL archiving** or hourly `pg_dump -Fc` + daily full physical backup via `pgBackRest` (with custom PG18 entrypoint running inside/beside `postgres`).
   - Encrypted via `restic` / `pgBackRest` AES-256 and synced to an **external S3-compatible bucket** (e.g., Cloudflare R2, Backblaze B2, or separate-region Contabo Object Storage).
   - **RPO:** `<= 15 minutes` (WAL) / `<= 24 hours` (nightly dump). **RTO:** `< 30 minutes` scripted restore into clean VPS.
2. **MinIO Object Storage (`rclone` / `mc mirror`):**
   - Hourly incremental encrypted sync of `reports-pdf`, `cog-products`, `model-artifacts`, and `incident-media` buckets to the same external off-site bucket (`--exclude "citizen-quarantine/*"`).
3. **Monthly Automated Restore Drill:**
   - A scheduled CI/staging cron job restores the latest encrypted prod backup onto the staging Postgres container and runs `database/tests/checks.sql` to prove backups are actually readable!

---

## 6. Monitoring, Logs & Alerting

Run a lightweight observability stack inside `infra/compose/docker-compose.ops.yml`:
- **Metrics (`Prometheus` + `Grafana`):**
  - `postgres_exporter` (connections, deadlocks, RLS query latency, WAL replication lag to `powersync`).
  - `nats_exporter` (JetStream queue depth, edge leaf reconnects).
  - FastAPI OpenTelemetry metrics (`NFR-PF-04` hazard-alert-to-WebSocket p50/p95/p99 latency gauge).
  - `node_exporter` + `cadvisor` (Contabo disk `%`, RAM swap pressure, container OOM kills).
- **Logs (`Loki` + `Promtail` / `Alloy`):** Structured JSON logs correlated by `trace_id`, `incident_id`, and `job_id` (zero citizen PII logged).
- **External Watchdog (`Uptime Kuma` or Healthchecks.io):** Runs outside Contabo (free tier / secondary tiny VPS) pinging `https://app.<domain>/api/v1/health` and verifying nightly backup heartbeat—sending immediate **Telegram / Discord / Email alerts** if Contabo goes unreachable or disk exceeds `80%`.
