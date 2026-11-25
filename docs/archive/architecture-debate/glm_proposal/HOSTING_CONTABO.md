# Hosting on a Contabo server

*Draft blueprint for `deploy/` and `docs/runbooks/`. The platform will run on a Contabo server with **no GPU and no budget for one**, as a demonstration for one user at a time. Training happens on free Kaggle or Colab GPUs, and inference runs on CPU with ONNX Runtime or OpenVINO. Everything below is designed for that.*

## 1. What the server has to do

| It does | It does not |
| --- | --- |
| Run the application, the database, the object store, the tile server and the AI services in containers | Train models |
| Serve the console, the field app's API and the citizen page over HTTPS | Run Kubernetes |
| Run AI inference on CPU | Rent or attach a GPU |
| Serve the orthomosaic, 3D products and area-wide analysis that were precomputed | Produce them during a demonstration |
| Analyse a small area of interest on demand | Run a language model |
| Take backups and send them somewhere else | Host more than one site |
| Run staging and production side by side | Be highly available |

The honest limit: one server is one point of failure. Backups and a rehearsed restore are what make that acceptable for a demonstration.

## 2. Options compared

| Option | What it is | Fit for this host |
| --- | --- | --- |
| **Docker Compose, files in Git, applied by GitHub Actions** | The container orchestrator that Docker ships. One file describes every service; files can be merged [B4] and grouped into profiles [B1]. | **Recommended.** Transparent: everything the server runs is in a file that was reviewed. An AI agent can read and change it. |
| k3s [B14] | A lightweight Kubernetes distribution. | Not a good fit. No managed Kubernetes is available, so the team would operate a cluster, its manifests and its upgrades for a single-node, single-user demonstration. |
| Coolify [B11] | "An open-source, self-hostable platform for deploying any application, database, or service on your own servers." | A reasonable convenience layer. Its installation requires root access [B11]. Judgment: deployment state lives partly in its own database and user interface, which is harder for an agent to reproduce from the repository than a file under review. |
| Dokploy [B12] | "A free, self-hostable Platform as a Service" with "native support for Docker Compose". | Same trade-off as Coolify. |
| Kamal [B13] | "Deploy web apps anywhere with zero downtime", originally for Rails, for any app that can be containerised. | A good tool for one web application and its accessories. This platform is a set of cooperating containers with shared networks and volumes, which Compose describes more directly. |

**Decision: Docker Compose, with the files reviewed in Git and applied by the delivery pipeline.** The deployment itself is a file in the repository, not a series of clicks. If the team later wants a user interface, Coolify or Dokploy can be put in front of the same Compose files; that is a later convenience decision and not part of the architecture.

## 3. The host

```
                     Internet
                        │
              ┌─────────┴──────────┐
              │  ports 80 and 443  │
              │      Traefik       │  one proxy for the whole host, automatic TLS
              └─────────┬──────────┘
        ┌───────────────┼───────────────────┐
        │               │                   │
  rescuevision-   rescuevision-        monitoring
  STAGING         PRODUCTION           (profile)
  api, worker     api, worker          uptime checks
  postgres        postgres             metrics
  object store    object store         dashboards
  AI services     AI services
  tiles           tiles
        │               │
        └───────┬───────┘
                │
         /var/lib/rescuevision/          volumes: database, objects
                │
         nightly backup, encrypted
                │
         off-site: Contabo Object Storage (S3) [B17] or a second location
```

One Ubuntu server with Docker Engine and the Compose plugin. A user named `deploy` owns the deployment. Nothing else runs on the machine.

**Plan.** The CPU feasibility study (`../cpu_demo_feasibility.md` §4) recommends **Cloud VPS Plus 8**: 8 shared AMD EPYC vCPUs, 24 GB of memory and 450 GB NVMe, at about €28 net per month. Its alternative is **Cloud VDS M** (8 dedicated EPYC cores, 32 GB, about $65 per month at the promotional price), worth the extra money only if rehearsals show that other tenants' load makes live inference erratic. The choice is the owner's. The resource limits in `compose.prod.yaml` are set after the first benchmark on the real machine.

## 4. Staging and production on one host

| | Staging | Production |
| --- | --- | --- |
| Compose project | `rescuevision-staging` | `rescuevision-prod` |
| What runs | Every commit from `main` | Release tags only |
| Who triggers | The pipeline, automatically | The pipeline, after a person's approval |
| Data | The demo scenario, rebuilt often | The demo scenario plus anything worth keeping |
| Secrets | Its own set | Its own set |
| Address | `staging.<domain>` | `<domain>` |
| Resources | Smaller limits | Larger limits |

The two projects share nothing except the proxy and the host: separate volumes, separate networks, separate database passwords. The proxy attaches to both through one external network and routes by host name.

Resource limits in `compose.prod.yaml` make sure that a runaway staging container cannot starve production.

Memory is why two stacks fit on the recommended plan: one stack peaks at about 5 to 6.5 GB with one model active (`../cpu_demo_feasibility.md` §4.2). The processor is shared, so staging's `models` profile runs only during the replay that follows a deployment and is stopped afterwards. Only production runs inference during a demonstration.

## 5. Reverse proxy and TLS

**Traefik** is the only process with public ports.

- **Certificates.** Traefik's ACME resolver obtains and renews Let's Encrypt certificates [B7].
- **Routing.** Each container declares its routes with labels, which Traefik's Docker provider reads [B8].
- **WebSocket.** The live channel is routed to `api`; the proxy passes the upgrade.
- **Hardening.** HSTS, security headers, a request body size limit, and a rate limit on the public endpoints of the citizen channel.
- **Static files.** The console bundle is served by its own small container behind the proxy, with the fallback to `index.html` that a single-page app needs.

Caddy is an equal alternative: it provisions certificates automatically [B10] and has a Docker-integration plugin. Traefik is chosen because its label-based routing for several Compose projects on one host is the simpler fit here. Choose one and write it down.

## 6. Object storage: use the S3 API, choose the store by a test

The approved database design says that files live in MinIO "S3 API". That has to be read as "an S3-compatible object store", because **the open-source MinIO repository is no longer maintained**: its README says so, and the GitHub API showed the repository archived on 2026-11-25, with the last push on 24 April 2026 and the last release in October 2025 [B15].

**Rule: the product depends on the S3 API only.** No feature specific to one store.

Maintained candidates that were confirmed to exist and to be active on 2026-11-25 [B16]:

| Candidate | Licence | What its README says |
| --- | --- | --- |
| RustFS | Apache-2.0 | "combines the simplicity of MinIO with the memory safety and raw performance of Rust"; tracks an S3 compatibility matrix; a young project |
| SeaweedFS | Apache-2.0 | A distributed file system with an S3 object store. Its `weed mini` mode runs it as one process for one node |
| Garage | AGPL-3.0 | "S3-compatible distributed object storage service" that "focuses on being lightweight, easy to operate" |
| VersityGW | Apache-2.0 | "Turn your local filesystem into an S3 server with a single command" |

The MinIO README also names the vendor's own free community edition. Its licence terms were not examined.

**Recommendation: SeaweedFS in its `weed mini` mode**, with RustFS as the alternative. Both are Apache-2.0 and had a release in November 2026 (4.55 and 1.0.6). SeaweedFS is the older project, and its README names this exact use: `weed mini` "is auto-tuned for one node and is fine for single-node production, such as an S3 gateway that issues presigned URLs". It is one process with one volume. RustFS is the closest match to MinIO in behaviour and console, but it is a young project at 1.0.6, and its container runs as a non-root user, so bind mounts need matching permissions. Garage is light but AGPL-3.0, like MinIO. The vendor's community edition is not recommended here, because its licence terms were not examined. The feasibility study budgets 80 to 300 MB of memory for SeaweedFS in single-binary form, inside the budget of one stack (`../cpu_demo_feasibility.md` §3.1). The release numbers and README quotes are as checked against the GitHub API on 2026-11-25 and recorded in `../eng_specialist_glm.md`; neither store has been run.

**One safety rule for `weed mini`.** Its README warns that the admin interface and WebDAV are reachable "even without authentication". The Compose file therefore attaches the S3 port to the `storage` network only, and exposes the admin interface and WebDAV nowhere. Only the proxy has public ports.

**How to choose, in Milestone 0.** Run the compatibility suite below against SeaweedFS first, and against RustFS only if a test fails. A store is chosen when it passes everything:

1. Presigned multipart upload from a browser and resumable upload after an interruption.
2. Presigned upload with a maximum size condition, and presigned download.
3. `HEAD`, byte-range reads (needed for cloud-optimised GeoTIFF), and listing with prefixes.
4. Correct behaviour with the checksum headers the pipeline uses.
5. Runs as a single container with one volume, inside a memory limit, and starts in seconds.
6. Backup with an S3 client, to a different S3 endpoint.

The same suite runs in CI against the chosen store, so the application is never tested against a different store than it runs on.

## 7. Secrets

| Secret | Used by | How it is created |
| --- | --- | --- |
| Database passwords, one per role (`rv_app`, `rv_citizen`, `rv_worker`, `rv_readonly`, administrator) | `api`, `worker`, `postgres` | Generated once on the server with a password generator |
| Object-store credentials | `api`, `worker`, the store | Generated once |
| Signing keys for tokens and job tickets | `api`, `worker`, AI services (public part only) | Generated once; rotated in pairs |
| SMS gateway and push service keys | `api`, `worker` | From each provider |

Rules:

- Secrets are files in `/var/lib/rescuevision/<project>/secrets/`, readable only by `deploy`. Compose mounts them as secrets. They are never environment variables in a committed file.
- The repository holds `.env.example` with every name and a comment, and no value.
- GitHub holds only the SSH key that deploys, and any value the pipeline itself needs.
- A copy of the secrets is kept encrypted outside the server. Losing the signing keys means losing access to the data they protect.
- A rotation procedure exists in `docs/runbooks/rotate-secrets.md` and is exercised once.

## 8. Backups

| What | How | How often | Kept |
| --- | --- | --- | --- |
| PostgreSQL | pgBackRest [B18], with write-ahead-log archiving so that the database can be restored to a chosen moment (confirm the exact feature names against its documentation) | Full weekly, incremental daily, log continuously | 7 daily, 4 weekly, 12 monthly restore points |
| Before every deployment | A plain database dump taken by `deploy.sh` | Each deployment | The last 10 |
| Object storage | A nightly sync with an S3 client, encrypted before it leaves the server | Nightly | 7 daily, 4 weekly |
| Secrets | Encrypted copy | On change | Current and previous |
| Deployment files | Git | Always | Forever |

**Where.** On the server's second disk if there is one, and off the server: Contabo sells S3-compatible object storage [B17], which is the natural second location. Any other machine works too.

**The restore is tested, not assumed.** Every night the pipeline restores the previous night's backup into an empty database on a runner and runs the database self-checks. Once a month, and before the demonstration, a person performs the full restore procedure from the runbook on a scratch machine and times it.

The two numbers to write down after the first drills are the recovery point objective (how much data can be lost) and the recovery time objective (how long the restore takes). They are measured, not promised.

## 9. Monitoring and alerting

| Need | Tool | Weight |
| --- | --- | --- |
| "Is the site up?" from outside | Uptime Kuma [B19], checking the public pages and one API endpoint | Light |
| "Is anything about to break?" | Disk space, memory, certificate expiry, container restarts, the age of the oldest queued job | Light |
| "How fast is the alert path?" | The metrics described in the proposal (§13), collected by a small Prometheus and shown in Grafana | Optional profile |
| Logs | JSON logs written by Docker with a size limit, read with the Compose log command | Built in |

Alerts go to one chat channel that the whole team reads. For a single-user demonstration the light setup is enough; the metrics stack is optional.

## 10. Running AI on this CPU host

| Decision | Detail |
| --- | --- |
| Runtime | ONNX Runtime on CPU by default, OpenVINO as the alternative, behind one adapter (`AI_PIPELINE.md` §3). No training framework on the server |
| Concurrency | One inference task at a time. Threads equal the physical cores allocated. The host has AVX2 only, so nothing may assume AVX-512 (`DOCKER.md` §7) |
| Quantisation | int8 only where it is faster on the server's own processor and within the accuracy policy (`AI_PIPELINE.md` §3) |
| Heavy work | The orthomosaic, surface model, 3D products and area-wide analysis are precomputed into the evidence bundle. On demand: a small area of interest or one photo (`AI_PIPELINE.md` §10) |
| Stitching | Never during a demonstration. NodeODM runs only when a bundle is built (`DOCKER.md` §3) |
| Tiles | Prebuilt for large rasters. TiTiler for small and on-demand rasters. |
| 3D | Rendered by the browser from products in the bundle. No 3D reconstruction on the server |
| Language model | Not on the server (`AI_PIPELINE.md` §13) |
| Measurement | `make bench` runs after each deployment and records the latency of every AI task on the real hardware. Those numbers are the evidence in the report. |

The first benchmark on the server fills in the budgets in `ai/benchmarks/budgets.yaml`. Until then, no design decision may quote a latency number. The estimates to plan by are in the CPU feasibility study (`../cpu_demo_feasibility.md` §3): a single damage tile at 1.5 to 4 seconds and 16 tiles at 25 to 65 seconds, before any measurement on the real host.

## 11. First day on the server

The script `deploy/server/setup.sh` and the checklist `deploy/server/HARDENING.md` cover:

1. A current Ubuntu LTS, with automatic security updates.
2. SSH with keys only. No root login. No password login.
3. A firewall that allows 22 (restricted to the team where possible), 80 and 443, and nothing else.
4. Docker Engine and the Compose plugin from Docker's official repository. The Docker daemon is not reachable from the network.
5. A `deploy` user that can use Docker, and the folder layout under `/var/lib/rescuevision/`.
6. Time synchronisation, a swap file, log rotation, and container log limits.
7. Login-attempt protection on SSH.
8. DNS records for both host names, so that the first certificate can be issued.
9. The first secrets, generated on the server.
10. A first deployment from the pipeline.

## 12. GPU: not on this host

There is no GPU and no budget for one. The design does not need one. `compose.gpu.yaml` exists only for a developer workstation. If a GPU were ever required at run time, it would be a second host on a private network with the AI services moved to it; the contract between worker and AI services would not change. That is a contingency, not a plan.

## 13. What was not verified, and what to ask Contabo

- Which plan the owner buys (the recommendation is in §3), and that plan's disk count and type. The resource limits are set after the first benchmark on it.
- Whether the plan includes Contabo Object Storage, snapshots or an additional backup space is a question for the account. The public pages confirm that object storage is offered [B17]; everything else should be confirmed in the customer panel.
- Whether the host firewall is Contabo's cloud firewall, the server's own, or both.
- Upload bandwidth for the first image pull and for restoring a backup.
- The licence terms of any commercial product named here.
