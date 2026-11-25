# Owner decisions log (working draft)

Decisions taken with the owner on 2026-11-25 after the architecture debate. This file feeds the final small decision docs; it is not itself one of them.

| # | Area | Decision | Why |
|---|---|---|---|
| 1 | Backend | FastAPI (Python), one modular monolith with one module per database domain | One server-side language with the AI, geospatial and PDF work; the frontend already generates types from `/openapi.json`; explicit transactions suit row-level security. |
| 2 | Web | Vite + React + TanStack Router (not TanStack Start), TanStack Query/Table/Form, Zod, Zustand, Tailwind v4, shadcn/ui, Motion, Lucide, Sonner, shadcn charts, i18next (Arabic/English, RTL) | Start's extra features are server-side and would compete with FastAPI; Router gives the same typed URL state. Migration to Start later is cheap. |
| 3 | Mobile | Expo + React Native with Expo Router and development builds (never Expo Go); NativeWind + React Native Reusables + Reanimated/Moti | Native offline maps, background GPS and a local SQLite queue need dev builds. |
| 4 | Repo layout | `backend/ frontend/ database/ contracts/ ai/ (kaggle/<feature>/vN, serving/, src/) deploy/ docs/ prototypes/` | Clear software vs AI split; teammates' `mapping/` and `mahmoudERD/` kept under `prototypes/` with history. |
| 5 | AI serving | One FastAPI template per model family, ONNX Runtime or OpenVINO on CPU, int8 only where measured faster, one heavy job at a time | CPU-only Contabo server; benchmarks in `debate/cpu_demo_feasibility.md`. |
| 6 | Live updates | Server-Sent Events from an append-only incident event log in Postgres; mobile catches up with `/events?since=` | Resumable, no Redis. |
| 7 | 3D | MapLibre only (one map engine), building extrusion and precomputed OpenDroneMap 3D Tiles drawn in the browser | Nothing 3D computed on the server during the demo. |
| 8 | Dashboards | Same page renders differently per agency and role through view presets (widgets, positions, agency colour theme, default layers/filters) from a widget registry. Role presets only: users cannot rearrange. Safety colours identical for all roles. Server permissions and RLS remain the guard. | Owner requirement: police, ambulance, fire and others see very different views of the same page. |
| 9 | Name | RESCA in place; owner wants an alternative whose bare .com is unregistered (resca.com is a ~US$1,000 aftermarket domain). Round 3 search running (`docs/brand/naming_round3_glm.md`). | Zero domain budget. |

Consensus defaults not yet confirmed by the owner: PostgreSQL job queue (Procrastinate, `SKIP LOCKED`) plus transactional outbox; SeaweedFS for object storage (MinIO archived); forward-only SQL migrations with dbmate; trunk-based Git on protected `main` with GitHub Actions and one required check; Docker Compose + Caddy on one CPU-only Contabo server; secrets with SOPS + age.
