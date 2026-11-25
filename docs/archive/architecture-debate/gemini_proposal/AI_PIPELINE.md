# End-to-End AI & Geospatial Pipeline (`AI_PIPELINE.md`)

This document traces how AI in RescueVision moves from **offline datasets and training** → **automated evaluation gates** → **versioned model registry** → **isolated LitServe Docker containers** → **background workers** → **verified operational maps and reports**.

---

## 1. Model Portfolio & Mapping to ERD Tasks (`ai_models.task`)

| ERD `model_task` | Model / Architecture | Config Reference | Primary Datasets | Serving Container |
|---|---|---|---|---|
| `BUILDING_SEGMENTATION` | SegFormer-B2 / U-Net (ResNet34) | `configs/segformer_building.yaml`, `building_seg_unet.yaml` | xBD, OSM/Overture | `ai-damage-svc` |
| `CHANGE_DETECTION` | Siamese U-Net / ChangeFormer | `configs/change_siamese_unet.yaml`, `changeformer_xbd.yaml` | xBD (pre/post) | `ai-damage-svc` |
| `DAMAGE_CLASSIFICATION` | DINOv2-base + MLP (4 xBD classes) | `configs/dinov2_damage_classifier.yaml` | xBD building crops | `ai-damage-svc` |
| `IMAGE_EMBEDDING` | DINOv2-base 768-d cosine embeddings | `configs/retrieval.yaml` | xBD + historical events | `ai-embed-svc` |
| `HAZARD_SEGMENTATION` / `ROAD_CONDITION` | SegFormer-B2 (10-class FloodNet) | `configs/floodnet_segformer.yaml` | FloodNet | `ai-flood-road-svc` |
| `PERSON_DETECTION` & `PERSON_TRACKING` | Aerial YOLO (occluded) + ByteTrack | New config under `ai/configs/` | SARD, VisDrone, POP | `ai-person-track-svc` |
| *(Photogrammetry — non-ML)* | SfM / MVS Orthomosaic + DSM + 3D Mesh | NodeODM presets | Raw drone EXIF sets | `nodeodm` |

---

## 2. End-to-End Lifecycle (5 Stages)

### Stage 1: Training & Reproducible Experiments (`ai/training/`)
1. All datasets (`xBD`, `FloodNet`, `SARD`, `VisDrone`, `POP`) use **event-aware splits** (e.g., `splits_event_aware.csv`) so tiles from the same disaster event never leak between train and validation.
2. Training runs read YAML configs from `ai/configs/`, log metrics/hyperparameters, and export checkpoints (`model.pt` / `safetensors`) plus a companion `manifest.json` (`sha256`, input normalization, class mapping, training commit SHA).

### Stage 2: Automated Evaluation Gate (`ai/eval/`) & Model Cards (`ai/model_cards/`)
A model checkpoint **cannot** enter the registry or Docker image until it passes `ai/eval/gate.py`:
* **Accuracy & Calibration Gates:** Minimum per-task thresholds (e.g., macro-F1 on xBD 4-class damage, mIoU on FloodNet water/road masks, mAP@50 on partial-visibility person detection, Expected Calibration Error so `p_no_damage..p_destroyed` reflect true probabilities).
* **Golden GeoTIFF Regression:** Runs on fixed Kahramanmaras Maxar / FloodNet reference chips and verifies output polygon counts, projection stability, and latency budget.
* **Model Card Requirement:** Every promoted version has a Markdown card in `ai/model_cards/<task>_<version>.md` documenting training datasets, per-class F1, cloud/smoke caveats, and minimum GSD requirements (e.g., `gsd_cm <= 5.0` gate for `PERSON_DETECTION` per `FR-PD-06`).

### Stage 3: Model Registry & Container Packaging
1. Approved weights are uploaded to MinIO (`models/{task}/{version}/weights.pt`) with immutable `sha256`.
2. A database migration/seed inserts the version into `ai_models` (`name`, `version`, `task`, `architecture`, `training_datasets`, `metrics`, `weights_uri`) and sets `is_active = true` (enforced unique per `task` by `ai_models_one_active_per_task_uq`).
3. The corresponding **`LitServe`** Docker container (`ai/services/*/Dockerfile.gpu`) packages the exact inference runtime (`LitAPI` subclass) and loads weights matching `weights_sha256`.

### Stage 4: Asynchronous Worker Execution (`backend/workers/`)
1. **Trigger:** User or ingestion pipeline queues a `processing_jobs` row (`STITCH` → `ANALYZE`).
2. **Claim (`SKIP LOCKED`):** `geo-worker` claims the job using `Procrastinate` (`rv_worker` DB role) and updates `progress_pct` every 15–30s (`NFR-PF-05`).
3. **Orthomosaic / COG Prep:** If raw drone frames were uploaded, `geo-worker` runs `nodeodm` → converts output to Cloud-Optimized GeoTIFF (`rasterio`/`gdal`) → uploads to MinIO (`products/orthomosaic.tif`) → inserts `raster_products`.
4. **Windowed Tiling & Batched LitServe Calls:**
   * **F1 Damage:** Aligns pre/post COGs in WGS84, extracts 512×512 overlapping tiles and building crops (`buildings`), batches them to `ai-damage-svc` (`LitServe` dynamic batching packs `batch_size=32`), and records one `inference_runs` row per model invocation.
   * **F2/F5 Flood & Roads:** Sends post-event tiles to `ai-flood-road-svc`; predicted flood polygons insert into `hazards` (`origin='AI_DETECTED'`), and obstructed roads insert into `road_condition_observations` (`road_segments.condition` updated).
   * **F3/F4 Persons:** Filters drone images with `gsd_cm` fine enough for person visibility (`FR-PD-06`), calls `ai-person-track-svc`, projects pixel bounding boxes to WGS84 using camera `PointZ` + gimbal pitch/yaw/roll, computes uncertainty radius $\rho = \sqrt{\sigma_{GPS}^2 + (k \cdot \text{GSD})^2}$, and inserts `person_detections` + `person_tracks`.
   * **Hazard Engine Hook:** Whenever `geo-worker` inserts AI-detected `hazards`, it calls `evaluate_hazard_rules(incident_id)` inside the commit transaction—meaning AI flood detection can trigger **Electrified Water** alerts automatically (`NFR-SF-02`).

### Stage 5: Provenance, Human Review (`D-07`), and UI Delivery
* **Map Streaming:** `TiTiler` streams the COG orthomosaic and AI mask rasters; `Martin` streams PostGIS `buildings`, `person_tracks`, `hazards`, `compound_alerts`, and `road_segments` as MVT vector tiles; `core-api` pushes `job-progress` and `alert-raised` over WebSockets.
* **Mandatory Human-in-the-Loop (`D-07`):**
  * `building_assessments` start as `review_status = 'PENDING'`; Analysts confirm or correct grades (with required reason) before official reconstruction totals finalize.
  * `person_tracks` never auto-dispatch teams; Analysts review stationary tracks (ranked first) with crop + uncertainty circle before creating an `assistance_cases` row.

---

## 3. Unique AI Differentiators (Staged Cleanly on Top of the Core)

1. **Historical Case Retrieval & Spatial Commander Copilot (`pgvector` + Read-Only Tools):**
   * `ai-embed-svc` computes 768-d `DINOv2` embeddings on post-disaster building/scene crops and stores them in `image_embeddings` (`HNSW` index).
   * A **Commander Copilot** inside `backend/api/app/copilot/` equips an LLM with **strictly read-only, RLS-scoped tools**: `query_incident_summary()`, `find_blocked_routes()`, `search_similar_historical_scenes(building_id)` (`ORDER BY embedding <=> $1 LIMIT 5`), and `explain_compound_alert(alert_id)`. It drafts bilingual Arabic/English situation briefs with verifiable record IDs—and has **zero write/dispatch tools** (`D-07`).
2. **Edge Triage Mode (`ai/edge/` → Mobile / Drone Ground Station):**
   * Export the lightweight aerial person detector to **ONNX (`.ort`) / ExecuTorch (`.pte`)** for on-device execution inside `apps/mobile` (`onnxruntime-react-native`) or a field laptop when uplink bandwidth cannot carry raw video. Edge detections sync as compact JSON + cropped thumbnails (`<50 KB`), preserving `inference_runs` provenance via a dedicated `EDGE_ONNX` `ai_models` entry.
3. **Rapid 3D Scene Inspection (Optional 3DGS Track):**
   * Baseline 3D view uses **CesiumJS + extruded building footprints (`buildings.height_m`) + NodeODM 3D Mesh Tiles**. As a targeted research demo, a separate offline `ai/edge/` or GPU job can generate a **3D Gaussian Splat** of a single collapsed priority structure for high-detail rubble inspection without delaying the main operational map.
