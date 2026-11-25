# RescueVision — Single Product & Technical Vision

> **One-sentence thesis:** RescueVision is a **Local-First Tactical Digital Twin** that turns multi-source satellite, drone, responder, and citizen signals into one shared, permission-scoped, offline-resilient operational picture—automatically stopping responders from driving into lethal compound hazards like *Electrified Water*.

---

## 1. The Product Story: One Incident, One Live Operational Twin

When an earthquake or flash flood hits a dense city, information arrives in fragments across agencies that normally cannot see each other's systems:

1. **Before-and-After Macro Triage (Damage & Cost):** Satellite tiles or an initial drone survey arrive first. RescueVision aligns pre- and post-disaster imagery into Cloud-Optimized GeoTIFFs (COGs) and runs a single calibrated joint damage model (`ChangeOS` / `SiameseUNetSE`, with a `Clay`/`DINOv2` post-only fallback when pre-event imagery is missing) to score every building footprint (`no-damage` → `destroyed`) with calibrated confidence and snapshotted EGP/USD restoration cost estimates (`building_assessments`, `cost_estimates`).
2. **Live Search & Rescue Under Partial Visibility (Person Detection & Tracking):** While orthomosaics stitch, search drones stream live RTSP/SRT video with `SMPTE 336M` KLV telemetry through an edge ground-station detector (`MediaMTX` + `YOLOv8s`), emitting lightweight GPS-projected person sightings (`50 KB` crops + `ByteTrack` tracks + terrain-corrected uncertainty radii) over constrained LTE or NATS Edge Leaf links—backed by high-recall `RT-DETR` + `SAHI` tiled inference on HQ GPUs.
3. **Closed-Loop Triage & Citizen Intake (Assistance Cases & Citizen Channel):** Every AI-detected survivor, responder field discovery, and verified citizen SOS (submitted via a lightweight offline-capable intake PWA or shelter QR/SMS relay with EXIF privacy scrubbing) flows into one deduplicated `assistance_cases` lifecycle (`DETECTED → VERIFIED → ASSIGNED → ON_SCENE → RESCUED`) so teams never double-dispatch or lose a victim report.
4. **The Flagship Brain — Compound Hazard Alerts & Safe Re-Routing (*Electrified Water*):** Mapping, damage, infrastructure assets, and responder telemetry are **never separate dashboards**. The instant a field responder, citizen, or `SegFormer` flood-segmentation run logs `FLOOD_WATER` overlapping or within hazard radius of an energized (or `UNKNOWN`-state) power asset, PostgreSQL's advisory-locked spatial hazard engine (`evaluate_hazard_rules`) atomically raises an **Electrified Water** compound alert, closes overlapping `road_segments`, invalidates unsafe mission `routes`, fans alerts out over NATS JetStream + WebSockets + mobile push, and triggers vehicle-aware `pgr_aStar` re-routing in under **60 seconds**.
5. **Works When the Network Dies (Local-First Mobile + Off-Grid Radio):** Field tablets (`apps/mobile`) run an encrypted local `OP-SQLite` database synchronized via `PowerSync` with pre-cached `.pmtiles` maps. Inside cellular blackouts, responders still view assigned routes, log triage, and raise hazards offline; critical `SOS` and `FLOOD_WATER` alerts automatically fail over across `<200 B` `MeshSat` / `Reticulum` LoRa packets until backhaul returns and `PowerSync` deterministically reconciles every offline write.
6. **One 2D/3D/4D Command Canvas & Auditable Reporting (Mapping, 3D, Copilot & Reports):** Commanders and analysts across Government, Police, EMS, and Fire collaborate inside **one unified MapLibre GL JS canvas** displaying RLS-filtered `ST_AsMVT` operational layers, `TiTiler` before/after imagery swipes, 3D buildings / NodeODM 3D Tiles (`3DTilesRendererJS`), localized rubble 3D Gaussian Splats (`Spark`), a **4D Incident Time-Travel Scrubber**, and a strictly read-only `PydanticAI` Spatial Copilot (`rv_readonly`)—and freeze everything into signed, immutable bilingual (`EN`/`AR`) PDF executive reports (`reports` + `WeasyPrint`) for post-incident command and reconstruction auditing.

---

## 2. How Every Feature Connects (Zero Orphan Modules)

| Feature | Inputs | Shared State Written | Downstream Reaction in RescueVision |
|---|---|---|---|
| **Damage & Cost (F1)** | Pre/post satellite or NodeODM orthomosaic COG + footprints | `raster_products`, `building_assessments` (calibrated `p_*`), `cost_estimates` | Colors 2D/3D buildings on MapLibre, feeds frozen PDF `reports` & `PydanticAI` queries |
| **2D/3D Mapping & Routing (F2/F5)** | `PMTiles`, `TiTiler` COGs, NodeODM DSM/3D Tiles/`OpenSplat`, `road_segments` | `raster_products`, `routes`, `route_segments` | Single MapLibre canvas (`2D` + `3D` + `4D` replay); `pgr_aStar` recalculates around closed/flooded roads |
| **Person Detection & Tracking (F3/F4)** | Live RTSP+KLV stream (edge) or HQ frames + DSM | `person_tracks`, `person_detections` (raycasted GPS + `location_error_m`) | Creates/links `assistance_cases` (`DETECTED`) and alerts analysts in real time |
| **Assistance Cases (F4)** | AI detections, responder sightings, citizen SOS | `assistance_cases`, `case_events` (append-only) | Synced offline via `PowerSync` to field responders; monotone merge on reconnect |
| **Compound Hazard Alerts (F5)** | `hazards` (`FLOOD_WATER`) + `power_assets` (`ENERGIZED`/`UNKNOWN`) | `compound_alerts`, `alert_closed_segments`, `road_segments`, `notifications`, `domain_events` | Closes lethal roads, invalidates `routes`, broadcasts WebSocket + Push + LoRa alerts in `<60s` |
| **Citizen Channel** | Citizen PWA / SMS / shelter QR intake | `citizen_requests` → `assistance_cases` / `hazards` | EXIF-scrubbed media + location queued for analyst triage without exposing internal agency tables |
| **Frozen Reports** | Approved incident snapshot at timestamp `T` | `reports` (`stats_snapshot` + immutable PDF in MinIO) | Bilingual (`EN`/`AR`) `WeasyPrint` PDF frozen forever for audit & cross-agency sharing |

---

## 3. Non-Negotiable Architectural Principles

1. **One Operational Core, Two Cleanly Separated Planes:** Software Engineering (`backend/`, `frontend/`, `database/`, `contracts/`) owns state, RLS security, routing, sync, and UI; AI Engineering (`ai/`, `triton-repo/`, `datasets/`) owns training, calibration, evaluation, and pure ONNX/TensorRT inference artifacts. They communicate **only** through `NVIDIA Triton` KServe v2 gRPC, `geo-worker` jobs, and `contracts/`.
2. **PostgreSQL + PostGIS Is the Single ACID Source of Truth:** Multi-agency Row-Level Security (`app.user_id` + `set_config` in explicit transactions), spatial routing (`pgr_aStar`), and `evaluate_hazard_rules()` advisory locks live in the database—never bypassed by unauthenticated tile servers or split across dual microservice databases.
3. **Human-in-the-Loop Sovereignty:** AI models and the read-only `PydanticAI` copilot **propose and rank**; authenticated human responders and commanders **verify, assign, dispatch, and resolve** (`building_assessments.review_status`, `assistance_cases`, `compound_alerts`).
4. **Honest Calibration & Edge Reality:** Every predicted damage probability and survivor GPS coordinate carries explicit calibrated uncertainty (`ECE`-validated probabilities, DSM-raycasted `location_error_m`). Critical SAR and hazard flows remain functional at `256 kbps` or zero cellular signal.
