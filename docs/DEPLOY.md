# Deploy

One CPU-only Contabo server runs the whole demo with Docker Compose. Caddy is the only container with a public port. The plan and its price must be confirmed by the owner before renting; the architecture review suggested Contabo's Cloud VPS Plus 8 at about €28 a month (price and specifications not yet verified).

## Layout

```
deploy/
  compose.yaml           all services; profiles: core (default), ai, demo-data, dev
  Caddyfile              TLS, headers, /api proxy, static web files
  secrets/*.enc.yaml     SOPS + age encrypted; decrypted only on the server
  scripts/               deploy.sh, rollback.sh, backup.sh, restore-drill.sh
  runbooks/              restore, rollback, degraded service (one page each)
```

## Rules

| ID | Rule | Gate |
|---|---|---|
| O1 | Images are multi-stage, based on digest-pinned bases, run as a non-root user with a read-only filesystem, `no-new-privileges` and dropped capabilities, and contain no secrets or build tools. | hadolint; image inspection |
| O2 | Every service declares CPU, memory and PID limits, a healthcheck, its networks and a graceful stop. Only Caddy publishes ports; AI services and storage sit on a private network. | `docker compose config` per profile; live checks |
| O3 | Secrets are SOPS + age files mounted per service; the age key is kept off the server's backups and with the owner. Rotating a secret is rehearsed. | Image and bundle secret scans |
| O4 | Daily encrypted backups of PostgreSQL, SeaweedFS objects and their manifest to a separate location; a monthly and pre-release restore drill into a fresh namespace checks data, RLS logins, sample media and event replay. Starting targets: lose at most 24 hours, restore within 2 hours. | `make check-restore` (to build) |
| O5 | Monitoring: request latency and errors, uptime checked from outside the server, outbox age, job queue depth, SSE lag, CPU, memory, disk and backup age. Alerts contain no personal data. Logs have a disk cap. | Fault-injection drill |
| O6 | Every release has image and model digests, the previous compatible set, stop conditions and a rehearsed rollback. A rollback across an incompatible migration is not allowed; fix forward. | Release check |

## Deploy and rollback

1. CI builds images on `main`, records digests and provenance.
2. `deploy/scripts/deploy.sh <release>` on the server pulls the digests, runs migrations (forward-only, D1), restarts services one at a time and checks readiness.
3. If readiness or the smoke test fails, `rollback.sh` returns to the previous digests. If a migration already ran, roll forward with a fix instead.

## When the AI services are down

The rest of RescueVision keeps working: reports, alerts, routing and SOS do not depend on AI. The UI shows "AI unavailable" on affected views; queued analysis resumes when the service returns (B10).
