# RescueVision — End-to-End AI Pipeline Blueprint (`AI_PIPELINE.md`)

> **Goal:** Define one reproducible, calibrated, edge-capable AI lifecycle—from curated disaster datasets and event-aware training all the way to a single packed **NVIDIA Triton** container, **Edge MediaMTX**, **PostgreSQL**, and **MapLibre** UI.

---

## 1. End-to-End Flow at a Glance

```
Datasets (xBD + BRIGHT + RescueNet + LADI v2 | SARD + HERIDAL | FloodNet + RescueNet)
  └─> Event-Aware Training & Augmentation (ai/src/rv_ai/training/)
        └─> Calibration (Temperature Scaling -> ECE) & Evaluation Gate (ai/src/rv_ai/eval/)
              └─> ONNX / TensorRT Export + Parity Check (< 1e-4 max diff)
                    └─> Versioned Triton Repo (triton-repo/<model>/<ver>/) + ai_models SQL Row
                          ├─> HQ Path: geo-worker -> Triton gRPC (:8001) -> DSM Raycast -> PostGIS
                          └─> Edge Path: MediaMTX (RTSP+KLV) -> YOLOv8s ONNX/TRT -> NATS Leaf -> PostGIS
                                └─> ST_AsMVT + TiTiler + WebSocket -> MapLibre Web & PowerSync Mobile
```

---

## 2. Authoritative Model Portfolio (Eliminating Redundancy)

Retire the fragile 4-model cascade (`U-Net → Siamese → EfficientNet → DINOv2`) and standardize on **four task-focused models + one foundation embedder**:

| Registry Slug (`ai_models`) | Architecture | Training Datasets | Role in Platform | Serving Target |
|---|---|---|---|---|
| `joint_damage` | **`SiameseUNetSE` (`se_resnext50_32x4d`, `608px`) benchmarked vs. `ChangeOS` (`Swin-T`)** | `xBD` + `BRIGHT` + `RescueNet` (multi-GSD `0.05–1.0 m/px` + oblique augmentation) | Primary pre/post building localization + 4-grade damage (`no-damage`, `minor`, `major`, `destroyed`) in **one forward pass** | HQ Triton (`onnxruntime` / `tensorrt`) |
| `post_damage_probe` | **`Clay v1.5` / `DINOv2` frozen backbone + `HASTE` logistic/MLP linear probe** | `RescueNet` + `LADI v2` + `xBD` post-tiles | **Pre-image-free rapid triage** when pre-disaster imagery is unavailable | HQ Triton (`onnxruntime`) |
| `person_sar_hq` / `person_sar_edge` | **HQ:** `RT-DETR` + `SAHI` tiled slicing (`ByteTrack` linking)<br>**Edge:** `YOLOv8s` (`640px` FP16/INT8) | `SARD` + `HERIDAL` (+ optional `POP` thermal; `VisDrone` excluded or pretrain-only) | Aerial survivor detection under partial visibility (`edge` runs live at 5–10 fps on RTSP+KLV) | `person_sar_hq`: HQ Triton<br>`person_sar_edge`: Field GCS / Jetson |
| `flood_road_seg` | **`SegFormer-B2`** | `FloodNet` + `RescueNet` (`Water`, `Road-Clear`, `Road-Blocked`) | Flood polygon extraction + road blockage segmentation feeding `hazards` and `road_segments` | HQ Triton (`onnxruntime`) |
| `eo_embedder` | **`Clay v1.5` / `DINOv2-base` (`768-d`)** | Pretrained EO/vision foundation weights | Generates `image_embeddings` (`pgvector` HNSW) for `PydanticAI` similar-collapse search & `post_damage_probe` | HQ Triton (`onnxruntime`) |

---

## 3. Dataset Curation & Domain-Gap Mitigation (`datasets/`)

1. **No Raw Media in Git:** `datasets/` stores download scripts, SHA-256 checksums, and deterministic `splits_event_aware.csv`. Actual `.tif`/`.png`/`.jpg` datasets sit in MinIO (`s3://datasets/`) or local cache (`/data/datasets/`).
2. **Satellite → Drone GSD Bridge:** Because `xBD` (`0.3–3.0 m/px` nadir satellite) differs dramatically from DJI UAV orthomosaics (`0.01–0.05 m/px` oblique/nadir):
   - Always resample/normalize drone orthomosaics to target GSD bands (`0.15 m/px`–`0.5 m/px`) before `joint_damage` inference.
   - Mix **`RescueNet`** (high-res Mavic Pro UAV) and **`LADI v2`** (10k oblique aerial disaster images) into training & **event/year-held-out** validation splits so models are directly tested on low-altitude oblique UAV viewpoints.
   - Add a **team-flown local DJI AOI dataset** (annotated locally) as the final domain-adaptation validation split before thesis defense.
3. **SAR Victim Realism:** Do not dilute small prone-victim recall with upright street pedestrians (`VisDrone`). Train primary detectors on `SARD` + `HERIDAL`, evaluating strictly on `SAHI` sliced `4000×3000` scenes.

---

## 4. Training, Calibration & Physical Geometry (`ai/src/rv_ai/`)

### 4.1 Reproducible Training & Tracking
- Configs live in `ai/configs/*.yaml` (zero hardcoded Kaggle paths or `git clone` steps; notebooks install `ai/` via `pip install -e .`).
- Every run logs hyperparameters, dataset split SHA-256, confusion matrices, and checkpoints to **MLflow**.

### 4.2 Mandatory Calibration (`ECE`)
- Raw neural softmax probabilities on out-of-distribution drone imagery are systematically overconfident and cannot responsibly drive `D-07` human triage or restoration budgets.
- `ai/src/rv_ai/calibration/temperature_scale.py` fits a scalar temperature $T > 0$ on held-out validation logits (`NLL` minimization), asserts Expected Calibration Error ($\text{ECE} \le 0.05$), and stores $T$ in `ai_models.calibration_temp`.
- `geo-worker` divides Triton raw logits by $T$ before writing calibrated `p_no_damage`, `p_minor`, `p_major`, `p_destroyed` (`sum = 1.000`) to `building_assessments`.

### 4.3 DSM-Aware Pixel-to-GPS Raycasting
- Replace flat-earth `altitude_agl_m` projection with full collinearity raycasting (`ai/src/rv_ai/calibration/raycast.py`, wrapped for runtime in `backend/.../worker/geometry.py`):
  1. Undistort pixel $(u, v)$ using stored `capture_sessions` camera intrinsics (`fx, fy, cx, cy, k1..k3`).
  2. Transform optical ray from camera frame → gimbal `(roll, pitch, yaw)` → ENU world frame.
  3. Intersect ray with **NodeODM DSM** GeoTIFF (falling back to Copernicus 30 m DEM if DSM is not yet stitched).
  4. Propagate GPS accuracy ($\sigma_{\text{GPS}}$), IMU angular jitter ($\sigma_{\theta}$), and terrain slope error into `person_detections.location_error_m`.

---

## 5. Export, Triton Packing & Version Promotion (`triton-repo/`)

1. **ONNX / TensorRT Export:**
   - `uv run python -m ai.export.to_onnx --model joint_damage --ckpt <mlflow_uri> --version 1`
   - Generates `triton-repo/joint_damage/1/model.onnx` (or `.plan` TensorRT engine for target GPU) + validated `config.pbtxt`.
2. **Numerical Parity Gate (Blocking):**
   - Runs identical inputs through PyTorch checkpoint and `onnxruntime` CPU/GPU; fails export if `max(|pytorch - onnx|) > 1e-4` or top-1 class flip rate `> 0.1%`.
3. **Single-CUDA-Context Packing in Triton:**
   - All models run inside **one `tritonserver` process** using C++ `onnxruntime` / `tensorrt` backends (NOT Triton's Python backend, which forks separate Python CUDA processes).
   - `config.pbtxt` assigns `dynamic_batching { max_queue_delay_microseconds: 5000 }` and explicit `instance_group [{ count: 1, kind: KIND_GPU }]` so concurrent `ANALYZE` and `HAZARD` batches interleave safely in shared VRAM without OOM crashes.
4. **Database Registry Sync:**
   - Binary `.onnx`/`.plan` weights upload to MinIO `s3://model-artifacts/triton-repo/...`; Git commits only `config.pbtxt`, `labels.json`, `manifest.sha256`, and the corresponding migration/seed row in `ai_models` (`name`, `version`, `calibration_temp`, `is_active`).

---

## 6. Runtime Execution: Cloud vs. Edge

### 6.1 Cloud / HQ Batch & Tiled Pipeline (`geo-worker` → `triton`)
1. `geo-worker` pulls `processing_jobs` (`ANALYZE`) via `FOR UPDATE SKIP LOCKED`.
2. Reads orthomosaic COG + pre-event COG windows (`608×608` with `25%` overlap) via `rasterio`.
3. Streams normalized FP32/FP16 tensors to `triton:8001` via async KServe v2 gRPC.
4. Merges overlapping predictions, scales logits by `ai_models.calibration_temp`, maps damage grades to `cost_profiles` (`cost_estimates`), writes `hazards` (`FLOOD_WATER`) + `road_segments` observations, triggers `evaluate_hazard_rules(incident_id)`, and writes `domain_events` → NATS → WebSockets → MapLibre (`ST_AsMVT` + `TiTiler`).

### 6.2 Edge Live Tactical SAR (`MediaMTX` → `edge-detector` → `NATS Leaf`)
1. Drone streams H.264/H.265 MPEG-TS with embedded **`SMPTE 336M` KLV** telemetry over SRT/RTSP into local **`MediaMTX`**.
2. `edge-detector` samples frames at 5–10 Hz, runs quantized **`YOLOv8s`** (`onnxruntime-gpu` / TensorRT), tracks identities via **`ByteTrack`**, extracts synchronized KLV gimbal/GPS pose, and projects coordinates via DEM raycasting.
3. Instead of uploading gigabytes of raw video over degraded cellular, `edge-detector` publishes **`~2 KB` JSON detections + `~50 KB` WebP/JPEG person crops** to **NATS Edge Leaf (`:4222`)**, while relaying live video to command HQ over WebRTC (`WHEP`) when bandwidth permits.
4. HQ `geo-worker` stores detections in `person_tracks` / `person_detections` (`image_id = NULL`, `stream_ref` + `frame_pts_ms` set) and raises `DETECTED` `assistance_cases` in real time.
