# Hosting & Production Deployment on Contabo (`HOSTING_CONTABO.md`)

The platform will be hosted on a **Contabo VPS / Dedicated Server** without managed Kubernetes. The deployment design maximizes reliability, TLS security, automated backups, and GPU flexibility while keeping operational overhead realistic for six students.

---

## 1. Orchestration Choice: Docker Compose + Caddy (with Optional Dokploy UI)

| Option | Verdict | Why |
|---|---|---|
| **Docker Compose + Caddy 2 (Recommended)** | **Primary Choice** | Zero control-plane RAM overhead, 100% identical to local dev `infra/docker-compose.yml`, trivial SSH/GitHub Actions rollout, zero vendor lock-in. |
| **Dokploy / Coolify** | **Optional Wrapper** | Nice web dashboard over Docker Compose on a single Contabo VPS (handles env vars, webhooks, logs nicely); choose **Dokploy** only if the team wants a UI—never let it diverge from `infra/docker-compose.yml`. |
| **k3s (Lightweight K8s)** | **Reject for Phase 1** | Wastes ~1.5–2 GB RAM on etcd/control plane, complicates persistent PostGIS/MinIO volumes and ingress for zero gain on a single VPS. |
| **Kamal** | **Reject** | Great for simple Rails/stateless web apps, awkward for multi-container geospatial stacks (PostGIS + PgBouncer + MinIO + Martin + TiTiler + Redis). |

---

## 2. Contabo Topology & The GPU Reality (Split-Plane Hybrid)

Standard Contabo Cloud VPS instances provide high vCPU/RAM/NVMe per euro (**e.g., 8–12 vCPU, 24–48 GB RAM, 400+ GB NVMe**) **but do NOT include NVIDIA GPUs** (and Contabo GPU servers are expensive to keep idle 24/7).

**Solution — Split-Plane Hybrid Hosting:**
1. **Always-On Contabo Server (CPU Core + Data + Tiles):**
   * Runs `caddy` (TLS), `web` (static SPA), `core-api` (2 Uvicorn workers), `geo-worker`, `pgbouncer`, `postgres` (PostgreSQL 18 + PostGIS + pgRouting + pgvector), `minio`, `redis`, `martin`, and `titiler`.
2. **On-Demand Burst GPU Node (RunPod / Lambda / Lab Workstation):**
   * Runs `infra/docker-compose.gpu.yml` (`ai-damage-svc`, `ai-person-track-svc`, `ai-flood-road-svc`, `ai-embed-svc`, `nodeodm`) **only during active incidents, testing, or graduation demos**.
   * Connects to Contabo's `geo-worker` over an encrypted **WireGuard / Tailscale** mesh (`10.88.0.x`), keeping AI containers unreachable from the public internet.
   * **Graceful Degradation (`NFR-RL-04`):** When the GPU node is turned off to save money, the Contabo server stays 100% online—map viewing, routing, SOS, live GPS, citizen OTP, and manual assessments all work normally, while new AI jobs stay `QUEUED` or route to a tiny CPU fallback if configured.

---

## 3. Reverse Proxy, TLS & Security on Contabo

* **Edge Proxy (`Caddy 2`):**
  * Automatically provisions and renews **Let's Encrypt TLS 1.2/1.3** certificates for `app.<domain>`, `api.<domain>`, `tiles.<domain>`, and `minio.<domain>` (for pre-signed browser uploads).
  * Enforces HSTS, gzip/zstd compression, request body limits (small for JSON API, direct-to-MinIO for large rasters), and WebSocket upgrade timeouts.
  * **Martin Vector Tile Auth:** Caddy uses `forward_auth` against `core-api` `/v1/internal/verify-tile-access` (or `core-api`-minted short-lived HMAC tile tokens) so Martin never leaks cross-agency geometries.
* **Host Firewall (`ufw`):** Open **only** `22/tcp` (SSH key-only, Fail2Ban enabled), `80/tcp`, `443/tcp`, and WireGuard UDP (`51820/udp`). Ports `55432` (Postgres), `6379` (Redis), `9000/9001` (MinIO internal admin), and `3000`/`8080` (Martin/TiTiler) stay bound to Docker internal networks or `127.0.0.1`.
* **Secrets Management:**
  * Store encrypted secrets in GitHub Environments (`staging` / `production`) and write `/opt/rescuevision/.env` on Contabo with `chmod 600` (or encrypt in repo via **SOPS + age**).
  * Separate DB passwords for `postgres` (migrations only), `rescuevision_api` (`rv_app`), `rescuevision_worker` (`rv_worker`), `rescuevision_citizen` (`rv_citizen`), and `rescuevision_bi` (`rv_readonly`).

---

## 4. Backups, Disaster Recovery (`NFR-RL-05`) & Monitoring

* **PostgreSQL Backups:**
  * Automated **`pgBackRest`** (or `pg_dump -Fc` + WAL archiving) cron every 6 hours to an **off-site S3-compatible bucket** (Cloudflare R2 / Backblaze B2, encrypted at rest). Never store backups only on the same Contabo disk!
  * Monthly scheduled **restore verification** into an ephemeral container running `./database/tests/checks.sql`.
* **MinIO Object Storage Backups:**
  * Nightly `mc mirror` / `rclone sync` of critical buckets (`models/`, `reports/`, `products/`) to the same off-site bucket.
* **Monitoring & Alerting (Lightweight Self-Hosted Stack):**
  * **Metrics:** `Prometheus` + `Node Exporter` + `cAdvisor` + `postgres_exporter` + `Grafana` (behind WireGuard/Caddy basic-auth). Track disk usage (alert at 75%/85%—rasters fill disks fast!), Postgres connections, `processing_jobs` queue lag, and 5xx rates.
  * **Logs:** Docker `json-file` log rotation (`max-size: 50m`, `max-file: 5`) + optional `Loki`/`Promtail` or `Dozzle` (over SSH/WireGuard).
  * **External Uptime:** `Uptime Kuma` (or Healthchecks.io) pinging `/health` every 60s and alerting team Discord/Telegram on outage.

---

## 5. Staging vs. Production Separation

| Aspect | **Staging** (`staging.<domain>`) | **Production / Demo** (`app.<domain>`) |
|---|---|---|
| **Trigger** | Auto-deployed on merge to `main` | Deployed only on signed Git tag `v*.*.*` + approval |
| **Isolation** | Separate Docker Compose project (`rv-staging`), separate Postgres volume & MinIO bucket (or second smaller Contabo VPS) | Dedicated Contabo VPS (e.g., Cloud VPS M/L) with pinned image digests |
| **Data** | Synthetic Cairo & Kahramanmaras seeds (`seed/02_demo_scenario.sql`) | Live exercise / pilot data + off-site encrypted backups |
| **GPU Endpoint** | Points to `cpu-mock` overlay by default (or dev GPU when testing) | Points over WireGuard to burst GPU node (or fallback CPU mode) |
