# RescueVision — Target AI System Architecture (`AI_SYSTEM.md`)

**Author:** AI Systems Specialist E (Gemini 4 Hydrogen)
**Date:** 2026-11-25
**Scope:** Feature-by-feature target AI architecture (F1–F6), uncertainty quantification, human-in-the-loop (`D-07`) contracts, database integration (`D3`, `D4a`–`D4d`, `D5`), and genuinely novel contributions.

---

## 1. Core Architectural Thesis

RescueVision's current repository artifacts contain a sharp gap between **database/requirements maturity** (56 PostgreSQL 18 + PostGIS + pgRouting + pgvector tables in `database/schema/`) and **AI configuration fragmentation**:
- `database/seed/01_reference_data.sql` activates 9 models (`is_active = true`) with `NULL` metrics and `NULL` `weights_uri` (`building-seg` U-Net ResNet34, `damage-classifier` DINOv2 + MLP, `change-detector` Siamese U-Net, `person-detector` YOLOv8s, `person-tracker` ByteTrack, `road-condition` SegFormer-B2, `hazard-segmentation` SegFormer-B2, `fire-smoke` YOLOv8s, `scene-embedder` DINOv2 ViT-B/14).
- `configs/inference.yaml` and `notebooks/kaggle/rv3_train_joint_serox50.ipynb` instead implement a joint `SiameseUNetSE` (`se_resnext50_32x4d`, `608px`) model, while `configs/dinov2_damage_classifier.yaml` uses `facebook/dinov2-base` even though `docs/tier1_papers_summary.md` designates **DINOv3** (`SAT-493M`) as the target backbone.
- Zero notebooks or configs exist yet for **F3 (`PERSON_DETECTION`)**, **F4 (`PERSON_TRACKING`)**, or **F5 (`FIRE_SMOKE_DETECTION`)**.

To build an innovative yet realistic system in **one academic year with 6 students**, we replace the sprawling 9-model wish list with **4 consolidated AI model families + 1 optional photogrammetry engine**, bound together by **3 genuinely novel engineering pillars**:
1. **Conformal Set-Valued Triage (`MAPIE` + Temperature Scaling):** Every damage grade and detection emits calibrated probabilities and a guaranteed-coverage prediction set so analysts review ambiguous cases first and HAZUS cost intervals reflect real model uncertainty.
2. **GSD-Gated, DSM-Raytraced Localization & Multi-Azimuth Tracking:** Every aerial detection respects `images.gsd_cm` (`FR-PD-06`), projects pixels onto a surface model (`DSM`/`DEM`) with propagated GPS/gimbal error, and links across frames via Camera-Motion-Compensated tracking.
3. **Dual-Purpose Geospatial Foundation Core (`DINOv3 SAT-493M` / `Clay v1.5`):** One frozen 768-d Earth-observation backbone drives (a) pre-image-free rapid building triage, (b) `pgvector` HNSW historical-case retrieval (`FR-RP-10`), and (c) cosine-distance out-of-distribution (OOD) shift warnings.

---

## 2. System-Wide AI Dataflow

```
  [Imagery Sources] ──► MinIO / S3 (raw JPG/TIF/COG) + capture_sessions / images (SHA-256)
         │
         ├──► [Fast Lane: Single Drone Frame] ──► GSD Gate (images.gsd_cm)
         │       └─► ai-vision-sar (D-FINE + SAHI + BoT-SORT) ──► DEM Raycast
         │             └─► person_detections + person_tracks (provisional, larger error radius)
         │
         └──► [Accurate Lane: Batch / Orthomosaic] ──► Optional NodeODM (ORTHOMOSAIC + DSM COGs)
                 ├─► ai-damage (SiameseUNetSE / ChangeOS) ──► Temperature Scale + MAPIE Conformal Set
                 │       └─► building_assessments (PENDING) + cost_estimates [low, high]
                 ├─► ai-vision-sar (SegFormer-B2 Flood/Road + D-FINE/SAHI)
                 │       └─► hazards (FLOOD_WATER, AI_DETECTED) + road_condition_observations
                 │             └─► PostgreSQL Hazard Engine (ELECTRIFIED_WATER / re-routing)
                 └─► ai-embed (DINOv3 SAT-493M / DINOv2)
                         ├─► image_embeddings (pgvector HNSW)
                         ├─► Post-Only Linear Probe (when pre_raster_id IS NULL)
                         └─► OOD Mahalanobis/Cosine Drift Flag
```

---

## 3. Feature-by-Feature Target AI Architecture

### 3.1 F1 · Building Damage Assessment & Restoration Cost

* **ERD Tables:** `capture_sessions` (`PRE_EVENT`, `POST_EVENT`), `raster_products`, `buildings`, `building_assessments`, `cost_estimates`, `inference_runs`.
* **Two Operating Modes (Addressing Missing Pre-Event Imagery):**
  1. **Primary Mode (`AI_BEFORE_AFTER`) — Joint Localization + 4-Grade Damage:**
     * **Chosen Model:** **`SiameseUNetSE`** (`se_resnext50_32x4d`, `608×608` input, `concat_absdiff` skip fusion + Squeeze-and-Excitation gates, already prototyped in [`notebooks/kaggle/rv3_train_joint_serox50.ipynb`](../../../notebooks/kaggle/rv3_train_joint_serox50.ipynb)) **benchmarked against [`ChangeOS`](https://github.com/Z-Zheng/ChangeOS)** (object-based semantic change detection) and **[`MambaBDA`](https://github.com/innopam/MambaCD)** (state-space spatio-temporal change detector).
     * **Why:** Training one shared Siamese model for building localization (`loc_logits`) and 4-class xBD damage (`dmg_logits`: `NO_DAMAGE`, `MINOR`, `MAJOR`, `DESTROYED`) prevents error cascades between separate `U-Net` + `Siamese` + `EfficientNet` + `DINOv2` stages, reduces VRAM footprint, and directly optimizes the official xView2 harmonic-mean metric ([`DIUx-xView/xView2_scoring`](https://github.com/DIUx-xView/xView2_scoring)). Where OSM or [`GlobalMLBuildingFootprints`](https://github.com/microsoft/GlobalMLBuildingFootprints) polygons exist for the AOI, we snap/aggregate pixel `dmg_logits` inside known footprints rather than relying purely on noisy raster-to-vector polygonization.
     * **Alternatives Considered:**
       * *4-model cascade (`building_seg` -> `change_detector` -> `damage_classifier`)*: Rejected for production because errors compound multiplicatively and 4 models waste VRAM.
       * *[`microsoft/building-damage-assessment`](https://github.com/microsoft/building-damage-assessment)*: Strong open-source reference baseline for comparison, but lacks RescueVision's joint localization + SE skip gating + conformal wrapper.
  2. **Fallback Mode (`AI_POST_ONLY`) — Pre-Image-Free Rapid Triage:**
     * **Chosen Model:** Frozen **`DINOv3` (`SAT-493M` ViT)** ([`facebookresearch/dinov3`](https://github.com/facebookresearch/dinov3), [`arXiv:2508.10104`](https://arxiv.org/abs/2508.10104)) or **[`Clay v1.5`](https://github.com/Clay-foundation/model)** Earth-observation foundation backbone + lightweight logistic/MLP head trained on `RescueNet` ([`BinaLab`](https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation)), `LADI v2` ([`arXiv:2406.02780`](https://arxiv.org/abs/2406.02780)), and xBD post-event crops. (Until `DINOv3 SAT-493M` weights are verified against Kaggle T4 memory limits, `facebook/dinov2-base` remains the baseline check.)
     * **Why:** Pre-disaster imagery is often misaligned, cloudy, or absent during rapid drone deployments. `AI_POST_ONLY` must explicitly flag lower confidence and wider uncertainty sets (`building_assessments.method = 'AI_POST_ONLY'`).
     * **Alternative Considered:** Fine-tuning `Mask2Former` or `SegFormer-B3` end-to-end on post-only xBD; heavier to maintain and prone to overfitting to xBD sensor style compared to a frozen EO foundation probe.
* **Inputs & Outputs:**
  * *Inputs:* Co-registered `pre_raster_id` (optional) + `post_raster_id` COG tiles (`608×608` with 25% overlap) + optional `buildings.footprint` polygons.
  * *Outputs:* `p_no_damage`, `p_minor`, `p_major`, `p_destroyed` (`sum = 1.000`), `damage_grade` (argmin risk or argmax), conformal prediction set `S(x) ⊆ {NO_DAMAGE, MINOR, MAJOR, DESTROYED}` stored in `inference_runs.params` / assessment metadata, and deterministic `cost_estimates` (`[cost_low, cost_high]`) computed by joining `cost_profile_unit_rates` and `cost_profile_repair_ratios` across the conformal set `S(x)`.
* **Uncertainty & Human Review (`D-07`):**
  * Raw logits are divided by scalar temperature $T$ fitted on the validation split (`NLL` minimization), then passed through Split Conformal Prediction via **[`MAPIE`](https://github.com/scikit-learn-contrib/MAPIE)** at $1 - \alpha = 0.90$.
  * **Queue Prioritization:** Buildings with `|S(x)| >= 2` (e.g., `{MAJOR, DESTROYED}`) or high OOD distance go to the top of the Analyst's `PENDING` review queue. Single-class high-confidence assessments (`|S(x)| = 1`) route to batch confirmation. Analysts must supply a reason on `CORRECTED` (`FR-DC-07`).

---

### 3.2 F2 · Orthomosaic / 2D–3D Mapping & Road Damage for Rescue Routing

* **ERD Tables:** `raster_products` (`ORTHOMOSAIC`, `DSM`, `DTM`, `POINT_CLOUD`, `MESH_3D_TILES`, `FLOOD_MASK`), `road_nodes`, `road_segments`, `road_condition_observations`, `routes`, `hazards`.
* **Photogrammetry & 3D Reconstruction:**
  * **Chosen Engine:** **[`OpenDroneMap / NodeODM`](https://github.com/OpenDroneMap/NodeODM)** triggered as an asynchronous `STITCH` job only when raw overlapping drone photos (`>= 70%` front/side overlap) are uploaded. Outputs are converted to **Cloud-Optimized GeoTIFFs (COGs)** (`ORTHOMOSAIC`, `DSM`) and **OGC 3D Tiles** (`MESH_3D_TILES`) rendered on a **unified MapLibre GL JS canvas** via [`NASA-AMMOS/3DTilesRendererJS`](https://github.com/NASA-AMMOS/3DTilesRendererJS) + extruded building footprints (`buildings.height_m`).
  * **Why Not 3D Gaussian Splatting (`3DGS`) in Core MVP?** While [`nerfstudio-project/gsplat`](https://github.com/nerfstudio-project/gsplat) + [`sparkjsdev/spark`](https://github.com/sparkjsdev/spark) deliver photorealistic rubble inspection, 3DGS requires GPU-heavy per-scene optimization, lacks metric DSM elevation products needed for F3 raycasting, and lacks raw multi-angle disaster training imagery in the repo. **Verdict:** Keep `NodeODM` for metric 2D/DSM/3D Tiles; defer `gsplat` + `Spark` to a **Stretch Demo** for a single collapsed priority building.
  * **Licensing Note:** `NodeODM` is `AGPL-3.0`; running it as an isolated container invoked over its REST API keeps core backend licensing clean, while requiring thesis disclosure if distributed as a SaaS product.
* **Road Condition & Flood/Debris Segmentation:**
  * **Chosen Model:** **`SegFormer-B2`** ([`arXiv:2105.15203`](https://arxiv.org/abs/2105.15203), already configured in [`configs/floodnet_segformer.yaml`](../../../configs/floodnet_segformer.yaml)) trained jointly on **`FloodNet`** ([`arXiv:2012.02951`](https://arxiv.org/abs/2012.02951)) + **`RescueNet`** ([`BinaLab`](https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation)), mapping semantic classes to RescueVision's operational ontology: `FLOOD_WATER`, `ROAD_CLEAR`, `ROAD_BLOCKED` (`debris` / `destroyed_road`), and `BUILDING`.
  * **Optional Pretraining / Pavement Distress:** [`RDD2022`](https://github.com/sekilab/RoadDamageDetector) can optionally warm-start surface crack/pothole detection, though disaster routing cares primarily about **passability** (`BLOCKED`, `DEBRIS`, `FLOODED`) rather than hairline asphalt cracks.
  * **Optional Zero-Shot/Prompted Extraction:** [`opengeos/segment-geospatial`](https://github.com/opengeos/segment-geospatial) (`samgeo` with [`SAM 2`](https://github.com/facebookresearch/segment-anything-2), [`arXiv:2408.00714`](https://arxiv.org/abs/2408.00714)) can assist analysts offline in creating clean polygon labels or vectorizing complex debris fields—not run unconditionally in automated high-throughput inference due to latency.
* **Inputs, Outputs & Routing Bridge:**
  * Segmented `FLOOD_WATER` masks are vectorized (`rasterio.features.shapes` + Douglas-Peucker simplification), filtered by minimum area & confidence threshold, and written to `hazards` (`origin='AI_DETECTED'`, `status='SUSPECTED'`).
  * Intersections with `road_segments` write `road_condition_observations` with `confidence`. Segments with low confidence remain traversable in `pgRouting` (`pgr_aStar`) but are flagged **"Unverified — AI uncertain"** on the route planner UI (`UC-04` alt 3b). Only high-confidence `BLOCKED` or `compound_alerts` closures remove edges.

---

### 3.3 F3 · Aerial Person Detection Under Partial Visibility

* **ERD Tables:** `images`, `person_detections` (`visibility`, `occlusion_ratio`, `posture`, `location`, `location_error_m`), `inference_runs`.
* **Honest Physics & Scope Constraint:** RGB/thermal UAV detection finds **visible or partially exposed persons** (head/limbs/torso peeking from rubble, water, or foliage). It **cannot** see victims buried under intact concrete slabs (`docs/graduation_project_research_plan.md`).
* **Chosen Models & Small-Object Pipeline:**
  * **Primary Server (HQ) Detector:** **`D-FINE-S/M`** ([`Peterande/D-FINE`](https://github.com/Peterande/D-FINE), **Apache-2.0** for COCO-only/custom weights; avoid `*_obj365.pth` non-commercial checkpoints) or **`RF-DETR-Small/Medium`** ([`roboflow/rf-detr`](https://github.com/roboflow/rf-detr), **Apache-2.0** for Nano–Large), paired with **[`SAHI` (Slicing Aided Hyper Inference)](https://github.com/obss/sahi)** (`640×640` overlapping slices at `20%` overlap) for 4K/8K UAV frames and orthomosaics.
  * **Why Challenge `YOLOv8s` (`01_reference_data.sql`)?** `ultralytics` (`YOLOv8`–`YOLOv11`) is **AGPL-3.0**, creating copyleft licensing friction if RescueVision's codebase or mobile client embeds it directly without enterprise licensing, and standard single-shot `640px` inference drops tiny `<20px` UAV targets. `D-FINE` / `RT-DETR` ([`lyuwenyu/RT-DETR`](https://github.com/lyuwenyu/RT-DETR), Apache-2.0) / `YOLOX` ([`Megvii-BaseDetection/YOLOX`](https://github.com/Megvii-BaseDetection/YOLOX), Apache-2.0) provide permissive licensing, NMS-free or anchor-free localization, and strong small-object recall under `SAHI`.
  * **Training Mix (Domain-Specific, Not Generic Street Pedestrians):**
    1. **`SARD`** (Search and Rescue Dataset, UAV top-down/oblique victims in rocky/grassy terrain)
    2. **`HERIDAL`** (real-world aerial SAR, tiny humans in wilderness/clutter; benchmarked in [`Accenture/AIR`](https://github.com/Accenture/AIR))
    3. **`SeaDronesSee`** ([`Ben93kie/SeaDronesSee`](https://github.com/Ben93kie/SeaDronesSee), [`arXiv:2105.01922`](https://arxiv.org/abs/2105.01922) — swimmers/floaters in open water, crucial for flood scenarios)
    4. **`POP` (Partially Occluded Person)** (`8,768` labeled UAV thermal images for partial occlusion, if thermal feed is enabled; [`HIT-UAV`](https://github.com/suojiashun/HIT-UAV) as supplemental thermal pretraining)
    5. *VisDrone* ([`VisDrone/VisDrone-Dataset`](https://github.com/VisDrone/VisDrone-Dataset), [`arXiv:1804.07437`](https://arxiv.org/abs/1804.07437)) used **only** for pretraining or hard-negative urban clutter—never as the sole fine-tune, because upright street crowds bias against prone/injured SAR postures.
* **GSD Gate & DSM-Aware Pixel-to-GPS Projection:**
  * **Pre-Inference Gate (`FR-PD-06`):** Reject or warn on images where `images.gsd_cm > 5.0` cm/px (where an exposed human head/shoulder spans `< 4–6 px` and false positives explode).
  * **Collinearity Raycasting (Replacing Flat-Earth Assumption):** Undistort pixel $(u, v)$ using stored camera intrinsics (`exif` / camera profile) $\rightarrow$ rotate through drone/gimbal `(gimbal_pitch, gimbal_yaw, gimbal_roll)` $\rightarrow$ intersect ray with **NodeODM DSM** (falling back to open 30 m Copernicus DEM when DSM is unavailable).
  * **Uncertainty Radius (`person_detections.location_error_m`):**
    $$\rho = \sqrt{\sigma_{\text{GPS}}^2 + (h \cdot \sigma_{\theta} \sec^2\theta)^2 + (k \cdot \text{GSD})^2}$$
    Extending `section_3_3.md` §3.3.8.3 by explicitly adding the angular gimbal/IMU error term $h \cdot \sigma_\theta \sec^2\theta$, because at oblique angles ($\theta > 30^\circ$) even $1^\circ$ of uncalibrated gimbal pitch shifts ground coordinates by metres!
* **Schema Reality Check (`visibility`, `occlusion_ratio`, `posture`):** Public datasets (`SARD`, `HERIDAL`) do not uniformly annotate `HEAD_ONLY` / `LIMBS_ONLY` / `occlusion_ratio`. **Honest Design:** Emit `visibility = 'UNKNOWN'` or train a lightweight secondary crop classifier **only** on the subset/synthetic-occluded crops where ground truth exists; never fabricate precision on unannotated attributes.

---

### 3.4 F4 · Multi-Object Person Tracking & Assistance Case Creation

* **ERD Tables:** `person_tracks` (`tracker_local_id`, `movement_state`, `last_position`, `last_position_error_m`), `person_detections`, `assistance_cases`.
* **Chosen Tracker:** **[`BoT-SORT`](https://github.com/NirAharon/BoT-SORT)** (with Camera Motion Compensation / CMC, no heavy Re-ID branch required for overhead nadir) or **[`ByteTrack`](https://github.com/FoundationVision/ByteTrack)** running **on CPU inside the geospatial worker** (not a separate GPU container!).
* **Why `BoT-SORT` (CMC) Over Plain `ByteTrack` for Drones?** `ByteTrack` assumes a mostly static camera or smooth linear target motion in pixel space. When a UAV yaws, pitches, or translates across rubble, pixel boxes jump violently and `ByteTrack` drops track IDs. `BoT-SORT`'s global frame-to-frame homography/optical-flow CMC aligns the Kalman state across drone motion, preserving track continuity at negligible CPU cost.
* **Cross-View Geo-Clustering for Photo Sequences (`PHOTO` vs `VIDEO_FRAME`):** When a drone uploads discrete overlapping photos rather than 30fps video, pixel tracking fails. We add a **spatial-temporal track linker** in the worker: detections from overlapping images within $\Delta t \le 120\text{ s}$ whose uncertainty circles overlap ($d(\mathbf{x}_i, \mathbf{x}_j) \le \rho_i + \rho_j$) merge into one `person_tracks` row, raising `max_confidence` and reducing static-rubble false positives via multi-azimuth consistency.
* **Human Review (`D-07`):** Tracks **never** auto-dispatch teams or auto-create `CONFIRMED` cases. Stationary tracks (`movement_state = 'STATIONARY'`) are ranked highest in the Analyst review queue alongside their cropped thumbnail, uncertainty circle, and observation age (`IR-UI-06`). Only a human Analyst promotes a track to `assistance_cases` (`VERIFY` / `ASSIGNED`).

---

### 3.5 F5 · Compound Hazard Intelligence & Secondary Hazard Perception

* **ERD Tables:** `hazards`, `infrastructure_assets`, `hazard_rules`, `compound_alerts`, `compound_alert_sources`, `alert_closed_segments`.
* **Core Engine (Deterministic Spatial Rules, Not Black-Box ML):** The flagship **"Electrified Water"** rule (`FLOOD_WATER` within 30 m of non-de-energized `POWER_LINE` / `TRANSFORMER`) MUST remain a **deterministic, auditable PostGIS transaction** (`ST_DWithin(::geography)` inside `evaluate_hazard_rules()`), never replaced by an LLM or opaque classifier.
* **Where AI Augments F5:**
  1. **Automated Hazard Ingestion:** `SegFormer-B2` (`FLOOD_WATER`, `DEBRIS`) and an optional **`D-FINE` / `YOLOX` Fire & Smoke Detector** trained on [`D-Fire`](https://github.com/AlimTleuliyev/wildfire-detection) (`21,000` YOLO-format fire+smoke images) and `FLAME 2` (RGB+IR) insert `hazards` (`origin='AI_DETECTED'`, `status='SUSPECTED'`) inside the database trigger transaction.
  2. **Important Architectural Fix (Alignment with DB Safety):** Ensure `evaluate_hazard_rules()` runs as `SECURITY DEFINER` via statement trigger on `hazards` and `infrastructure_assets` so both `AI_DETECTED` worker writes and `RESPONDER_REPORTED` mobile writes trigger `ELECTRIFIED_WATER` / `FIRE_GAS_EXPLOSION` atomically without RLS `42501` failures.
  3. **Confidence-Weighted Alert Severity:** AI-detected hazards below the high-precision operating point enter as `SUSPECTED` and still trigger precautionary warnings (`NFR-SF-02`: treat uncertain danger as active until cleared by Commander), displaying an explicit *"AI-Detected — Needs Field/Analyst Confirmation"* badge.

---

### 3.6 F6 · Reports, Historical Case Retrieval & Grounded Copilot

* **ERD Tables:** `reports`, `image_embeddings` (`vector(768)` HNSW), `ai_models`, `inference_runs`.
* **Deterministic Frozen Snapshots (Mandatory Core):** Every statistical figure in `reports.stats_snapshot` (building counts, cost totals, case counts, active alerts) is computed **purely by SQL** and stamped with exact `ai_models` versions and mandatory safety disclaimers (`docs/limitations_and_ethics.md`).
* **AI Enhancements:**
  1. **`image_embeddings` (`pgvector`):** `ai-embed` encodes post-disaster building/scene crops with the **same frozen `DINOv3 SAT-493M` (or `DINOv2-base` 768-d)** backbone used by `AI_POST_ONLY` and stores normalized vectors in `image_embeddings`, enabling instant historical precedent lookup (`ORDER BY embedding <=> $1 LIMIT 5`) on historical reference incidents (`incidents.is_historical = true`, e.g., xBD reference events).
  2. **Grounded Commander Copilot (Stretch / High-Value Addition):** Detailed in [`AI_COPILOT.md`](./AI_COPILOT.md) — a strictly read-only [`pydantic/pydantic-ai`](https://github.com/pydantic/pydantic-ai) assistant over `rv_readonly` that drafts bilingual Arabic/English SITREPs and answers spatial/operational queries using verified SQL tools, with programmatic citation verification and zero write permissions (`D-07`).

---

## 4. What Is Genuinely Novel (Graduation Project Defense Summary)

| Innovation | Why It Is Novel & Defensible (Not Hype) | Concrete Mechanism in RescueVision |
|---|---|---|
| **1. Conformal Cost-Linked Uncertainty (`MAPIE`)** | Standard xBD papers report argmax F1; emergency commanders need calibrated risk bounds that flow directly into financial loss ranges. | `SiameseUNetSE` temperature-scaled logits $\rightarrow$ `MAPIE` 90% prediction sets `S(x)` $\rightarrow$ `cost_estimates [low, high]` spans `S(x)` + ambiguity-ranked `D-07` review queue. |
| **2. Single-Backbone Tri-Task EO Core (`DINOv3 SAT-493M`)** | Eliminates redundant encoders across post-only damage, historical search, and domain-shift monitoring. | One `768-d` embedding pass feeds: (a) `AI_POST_ONLY` linear/MLP head, (b) `pgvector` HNSW similar-case lookup, and (c) cosine/Mahalanobis OOD drift warning on new cities. |
| **3. Physics-Aware Aerial SAR Pipeline (`GSD Gate + SAHI + DSM Raycast + CMC`)** | Corrects the naive "YOLO + EXIF GPS" mistake in student drone projects. | Enforces `gsd_cm <= 5.0` gate $\rightarrow$ `SAHI` tiled `D-FINE`/`RF-DETR` $\rightarrow$ `BoT-SORT` CMC tracking + multi-view geo-clustering $\rightarrow$ `NodeODM` DSM raycast with angular error propagation. |
| **4. Dual-Provider CPU/Burst-GPU Serving (`LitServe + ONNX Runtime`)** | Solves the Contabo no-GPU hosting reality without Triton C++ ops overhead or AGPL/CUDA lock-in. | Same `LitServe` + `ONNX Runtime` container runs on Contabo CPU (dev/fallback) and bursts to Modal/RunPod GPUs over Tailscale for large orthomosaic/SAHI jobs. |

---

## 5. Phased AI Roadmap (MVP vs. Stretch)

| Phase | Scope | Deliverables & Exit Criteria | Realistic Team Effort (6 Students, 1 Academic Year) |
|---|---|---|---|
| **Phase 0 · Foundation & Registry Hygiene** | Clean `ai/` package (`rv_ai`), Kaggle `v1` structure, DB evidence constraint on `ai_models` (`is_active = false` until evaluated). | `rv_ai` installable via `uv`/`pip`; official [`xView2_scoring`](https://github.com/DIUx-xView/xView2_scoring) unit-tested; zero weights in Git. | Weeks 1–3 |
| **Phase 1 · MVP Core Vision (F1 + F2 + F3)** | 1) `SiameseUNetSE` on xBD (`v1`→`v2`) + Temperature Scaling + `MAPIE`;<br>2) `SegFormer-B2` on `FloodNet` + `RescueNet` (`FLOOD_WATER`, `ROAD_BLOCKED`);<br>3) `D-FINE-S` (or `YOLOX-S`) + `SAHI` on `SARD` + `HERIDAL` + `SeaDronesSee`;<br>4) `LitServe` + ONNX Runtime CPU containers wired to `processing_jobs`. | End-to-end queued `ANALYZE` job writes calibrated `building_assessments`, `hazards` (triggering `ELECTRIFIED_WATER`), `road_condition_observations`, and `person_detections` into PostgreSQL 18. | Weeks 4–12 |
| **Phase 2 · Mapping, Tracking & Edge Photo Triage (F2 + F4 + Edge)** | 1) `NodeODM` integration (`STITCH` $\rightarrow$ COG + DSM + 3D Tiles);<br>2) DSM raycasting + `BoT-SORT` CMC + multi-view geo-clustering;<br>3) `DINOv3`/`DINOv2` `ai-embed` (`pgvector` + `AI_POST_ONLY` probe + OOD detector);<br>4) Expo Dev Build offline photo person-triage (`onnxruntime-react-native`). | Drone survey produces orthomosaic, DSM-projected tracks, `AI_POST_ONLY` fallback, historical case search, and offline responder photo triage. | Weeks 13–20 |
| **Phase 3 · Burst GPU, Copilot & Optional Stretch** | 1) Tailscale + Modal/RunPod burst GPU profile for `ai-damage` & `NodeODM`;<br>2) Grounded Read-Only `PydanticAI` Commander Copilot (`AI_COPILOT.md`);<br>3) Optional `D-Fire` smoke/fire detector (`F5`) + `POP` thermal branch;<br>4) Stretch only if ahead of schedule: single-building 3DGS (`gsplat` + `Spark`). | Tested burst-GPU demo on Contabo; auditable bilingual SITREP drafts; frozen thesis evaluation tables across held-out disasters + local Cairo test AOI. | Weeks 21–28 |
