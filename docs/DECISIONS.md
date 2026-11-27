# Decisions

Locked. Each line is a decision (DEC-nn) the owner took on 25 November 2026. The architecture debate behind them was deleted after these decisions were taken; it remains in Git history at commit `7c1dcde` under `docs/archive/architecture-debate/`. To change one, the owner edits this file in its own pull request. Agents propose changes in PR text only.

| # | Area | Decision | Why | Rejected |
|---|---|---|---|---|
| DEC-01 | Shape | Modular monolith core plus separate AI containers | Fits six students and one database with row-level security; AI isolated behind HTTP | Microservices per domain |
| DEC-02 | Backend | FastAPI (Python 3.12), one package `rescuevision_api`, one module per database domain | One server language with AI, GIS and PDF work; the frontend already generates types from `/openapi.json`; explicit transactions suit RLS | NestJS, Go |
| DEC-03 | Web | Vite + React + TanStack Router, TanStack Query/Table/Form, Zod, Zustand, Tailwind v4, shadcn/ui, Motion, Lucide, Sonner, shadcn charts, i18next | Typed URL state for the map console; logged-in tool needs no server rendering | TanStack Start, Next.js, React Router |
| DEC-04 | Mobile | Expo (React Native) with Expo Router and development builds; NativeWind + React Native Reusables, Reanimated/Moti | Native offline maps, background GPS and SQLite need dev builds; shares API client and types | Expo Go, Flutter |
| DEC-05 | Maps | MapLibre GL (web and mobile) with deck.gl overlays; one map engine | One camera and selection model | CesiumJS |
| DEC-06 | 3D | Building extrusion and precomputed OpenDroneMap 3D Tiles drawn in the browser | Nothing 3D runs on the CPU server during the demo | Server-side 3D, Gaussian splat training |
| DEC-07 | AI serving | One FastAPI + ONNX Runtime (or OpenVINO) template per model family; int8 only where measured faster; one heavy job at a time | CPU-only server; benchmarks in [AI.md](AI.md#cpu-notes) | LitServe, Triton, one container for all models |
| DEC-08 | Live updates | Server-Sent Events from an append-only incident event log; mobile catches up with `/events?since=` | Resumable after a drop, no extra broker | WebSocket + Redis, polling |
| DEC-09 | Jobs | PostgreSQL job queue (Procrastinate, `SKIP LOCKED`) plus a transactional outbox | Job and business write commit together | Celery, RabbitMQ, Kafka |
| DEC-10 | Files | SeaweedFS (S3 API); pre-signed uploads and downloads | Maintained; MinIO's repository is archived | MinIO |
| DEC-11 | Migrations | Plain forward-only SQL with dbmate; current schema files are the frozen baseline | SQL stays the only schema source | ORM-generated migrations |
| DEC-12 | Dashboards | Same page renders per agency and role from view presets (widgets, positions, agency accent, default layers and filters); role presets only, users cannot rearrange; safety colours identical everywhere | Police, EMS, fire and government need different views; predictable in a crisis | Free per-user layouts |
| DEC-13 | Repo | `backend/ frontend/ database/ contracts/ ai/ deploy/ docs/ prototypes/` | Clear software and AI split | `services/` tree |
| DEC-14 | Git | Short branches from `dev`, squash-merged into `dev`; only `dev` merges (merge commit) into protected `main`; one required check `ci/ok` | Owner chose a tested integration branch before `main` (25 November 2026) | Branches straight into `main`, long-lived feature branches |
| DEC-15 | CI | GitHub Actions, run only for `main` (pull requests into main and pushes to main) | Owner rule | CI on every branch push |
| DEC-16 | Hosting | One CPU-only Contabo server, Docker Compose + Caddy, single-user demo | No GPU and no budget | Kubernetes, GPU cloud |
| DEC-17 | Secrets | SOPS + age encrypted files; per-service secret mounts | Secrets never in Git or images | Plain `.env` in the repo |
| DEC-18 | Training | Free Kaggle or Colab GPUs, or teammates' own GPU laptops (local training and testing allowed); notebooks in `ai/kaggle/<feature>/vN/` | Free compute | Training on the server |
| DEC-19 | Agent rules | Strict rules with automatic gates in the area docs; owner-only files listed in `.github/locked-paths.txt` | Written rules alone get broken | Rules in prose only |
| DEC-20 | Name | RescueVision; domain rescuevision.app | No domain budget | |

Defaults that are numbers (rate limits, page sizes, latency budgets, coverage) live in the area docs as starting budgets. Measure on the real server before treating them as final.
