# RescueVision — Single Product Vision

> **One Incident. Live Spatial Truth. Human-Accountable Rescue.**

## 1. The Core Problem We Solve

In the first 72 hours after a flood, earthquake, or urban collapse, four agencies—**Government, Police, Ambulance (EMS), and Fire**—share the same disaster zone while operating blind across fragmented tools. Drone teams hold raw imagery on SD cards; GIS analysts manually draw damage polygons hours too late; field paramedics drive toward roads that have silently flooded or lie within 30 metres of an energized downed power line; citizens text unverified pleas into overloaded hotlines; and command writes static reports whose numbers drift the moment someone edits a spreadsheet.

**RescueVision exists to turn raw multi-source chaos (drone/satellite imagery, responder GPS/reports, and citizen OTP requests) into one live, agency-isolated, human-verified operational map—where a single flood report closes lethal roads and reroutes rescue teams in under 60 seconds.**

---

## 2. One Coherent Operational Loop (How Every Feature Connects)

RescueVision is **not** six disconnected AI demos bolted onto a CRUD app. Every feature feeds **one shared incident truth** stored in a single spatial core (PostgreSQL 18 + PostGIS + pgRouting + pgvector):

1. **Capture & Stream (`F2 · Situational Mapping`):** Drones and satellites capture pre- and post-disaster imagery; photogrammetry (`NodeODM`) stitches drone frames into Cloud-Optimized GeoTIFFs (COGs) and 3D products streamed instantaneously (`TiTiler`) into a synchronized **2D MapLibre / 3D CesiumJS Command Console** and **offline-capable Expo Field App** (`PMTiles`).
2. **Assess Structural Impact & Cost (`F1 · Damage & Restoration`):** Isolated AI vision models (`SegFormer`, `Siamese U-Net`, `DINOv2`) segment building footprints, grade damage on the 4-class **xBD scale** (*No Damage, Minor, Major, Destroyed*), attach per-grade probabilities, and calculate transparent low–high **HAZUS-style restoration cost estimates**—while indexing scene crops into `pgvector` so commanders can retrieve visually similar historical collapses.
3. **Find & Track Survivors (`F3/F4 · Detection, Tracking & Assistance Cases`):** Under partial visibility (debris, occlusion, oblique drone angles), aerial detectors locate people with explicit **metres-of-uncertainty circles** and link detections across frames into **ByteTrack movement tracks**. Stationary or endangered tracks are surfaced to Analysts, who verify and promote them—or merge them with **Citizen Phone-OTP Requests** and **Field Reports**—into accountable **Assistance Cases** with START triage tags.
4. **Prevent Secondary Fatalities (`F5 · Compound Hazard Intelligence`):** Individual hazards (*Floodwater, Fire, Gas Leak, Collapse Risk, Downed Power Line*) are evaluated continuously in PostGIS against utility assets. When two dangers intersect in space—flagship rule **Electrified Water** (floodwater within 30 m of an energized or unknown-state power line/transformer)—the rule engine atomically:
   - draws an explicit **No-Entry Danger Zone**,
   - closes intersecting `road_segments` (`cost = -1`),
   - invalidates active `routes` passing through the zone, and
   - pushes priority warnings to responders inside or routed through it.
5. **Dispatch & Re-Route (`F2 · Vehicle-Aware Routing` + `Field App`):** When a Commander assigns a mission, **pgRouting (`pgr_aStar`)** computes primary and alternative routes tailored to the assigned vehicle's physical limits (e.g., 4x4 vs. ambulance `max_water_depth_cm`)—or explicitly warns **"No Safe Route"** rather than guessing. Responders execute missions offline-first via local SQLite queues (and optional **Meshtastic LoRa mesh** fallback), send live GPS/SOS, and update case triage on scene.
6. **Command Copilot & Frozen Accountability (`F6 · Reports` + `Copilot`):** Every AI result carries its exact `ai_models` version, `inference_runs` provenance, uncertainty, and age; **no AI output ever dispatches a team or closes a road without human accountability (`D-07`)**. A read-only tool-using **Spatial Commander Copilot** answers cross-layer questions in Arabic/English with verified database citations, and **Reports** freeze cost and casualty snapshots at approval time for inter-agency sharing and after-action replay.

---

## 3. Non-Negotiable Product Invariants

Every line of code and every AI model in this repository must uphold five invariants:

1. **One Shared Incident, Strict Agency Isolation:** Agencies join one incident (`LEAD` or `SUPPORT`) so everyone sees the same facts, while PostgreSQL Row-Level Security (`D-04`) guarantees zero cross-agency leaks.
2. **Propose & Warn, Never Auto-Act (`D-07`):** AI proposes damage grades, detections, and alerts; only accountable humans confirm cases, dispatch teams, or resolve road closures.
3. **Show Uncertainty & Age Openly:** Never render a raw point without its error radius, an AI grade without confidence/review status, or a 10-minute-old GPS ping as live.
4. **Offline-First & Field-Resilient (`D-08`):** Disasters break cell towers. The mobile field app must work without signal (local SQLite queue + offline `.pmtiles` maps) and degrade gracefully to low-bandwidth relays.
5. **Full Provenance & Frozen History:** Every prediction points to `inference_runs`; every state change writes append-only history (`audit_log`, `case_events`, `mission_status_history`), enabling minute-by-minute incident replay and reproducible PDF reports.
