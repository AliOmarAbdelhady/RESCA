# RescueVision — AI Training Workspace, Kaggle Sync & Model Lifecycle (`AI_TRAINING_LAYOUT.md`)

> **Goal:** Refine the owner's `kaggle/<feature>/vN/` training workflow into an industrial-grade, reproducible pipeline where **six developers and AI agents can iterate rapidly on Kaggle/Colab**, never lose experiment metrics, never commit large weights to Git, and cleanly promote parity-checked models into **NVIDIA Triton** and the live RescueVision backend.

---

## 1. Refined AI Training Layout (`kaggle/` + `ai/` + `triton-repo/`)

Instead of 26 unorganized notebooks dumped flat in `notebooks/kaggle/` or fragile notebooks cloning deleted `src/` folders, split the AI side cleanly into **three synchronized tiers**:

1. **`ai/` (Shared Python Package `rv_ai`):** Reusable architectures (`SiameseUNetSE`, `ChangeOS`, `RT-DETR`, `YOLOv8s`, `SegFormer`), losses, TorchGeo datamodules, Temperature Scaling calibrator, DSM raycaster, evaluation gate (`XView2PixelScorer`, `ECE`), and ONNX exporter. **Notebooks NEVER copy-paste model classes—they `pip install` `rv_ai` at a pinned Git commit!**
2. **`kaggle/` (Owner's Versioned Feature Experiment Workspace):** Every AI capability lives under `kaggle/<feature-name>/v<N>/`, making model lineage immediately readable:
   ```
   kaggle/
   ├── README.md                        # How to run on Kaggle/Colab, MLflow URI, promotion checklist
   ├── damage-assessment/               # Pre+Post Joint Building Localization & 4-Class Damage + Post-Only Probe
   │   ├── v1/                          # Baseline (e.g. SiameseUNetSE on xBD)
   │   ├── v2/                          # xBD + BRIGHT + RescueNet multi-GSD + Temperature Scaling
   │   └── v3/                          # ChangeOS Swin-T benchmark + LADI v2 / Local DJI AOI fine-tune
   ├── person-detection/                # Aerial SAR Victim Detection & Tracking (HQ RT-DETR + Edge YOLOv8s)
   │   ├── v1/                          # SARD + HERIDAL baseline (YOLOv8s)
   │   └── v2/                          # RT-DETR + SAHI tiled eval + optional POP thermal
   ├── flood-road-seg/                  # Flood Water + Road Clear/Blocked Segmentation
   │   ├── v1/                          # FloodNet baseline (SegFormer-B2)
   │   └── v2/                          # FloodNet + RescueNet urban generalization
   └── geo-embeddings/                  # EO Foundation Embeddings (Clay v1.5 / DINOv2 + HASTE post-only head)
       └── v1/
   ```
3. **`triton-repo/` (Production Serving Registry):** Contains ONLY `config.pbtxt`, `labels.json`, and `manifest.sha256` pointing to MinIO binary `.onnx`/`.plan` engines for **active production versions**.

---

## 2. Exact Contents of Every `kaggle/<feature>/vN/` Folder

Every `vN/` directory is an **immutable, self-contained experiment dossier** once promoted or archived:

| File inside `kaggle/<feature>/vN/` | Purpose & Rules |
|---|---|
| `README.md` | 10-line experiment card: hypothesis, exact delta vs `v(N-1)`, hardware used (`2×T4` / `P100` / `A100`), status badge (`DRAFT` / `CANDIDATE` / `PROMOTED` / `ARCHIVED`), and MLflow Run URL. |
| `config.yaml` | Declarative hyperparameters: `rv_ai` git commit SHA, backbone, `input_size`, loss weights, GSD sampling bands, augmentation flags, and seed. |
| `dataset_ref.json` | Exact dataset identifiers (Kaggle dataset slugs / MinIO `s3://datasets/...`), `splits_event_aware.csv` SHA-256 hash, and class mapping. **Zero raw images here.** |
| `train.ipynb` | Thin Kaggle/Colab training runner (~50–100 lines): installs pinned `rv_ai`, loads `config.yaml` + `dataset_ref.json`, trains, fits Temperature Scaling $T$, saves checkpoint to Kaggle Output / MinIO. |
| `eval.ipynb` | Thin deterministic evaluation & calibration runner: evaluates strictly on held-out event splits, generates `metrics.json`, reliability diagram, and confusion matrix. |
| `metrics.json` | Machine-readable canonical metrics committed to Git (`xview2_f1`, `loc_f1`, `clf_f1`, `ece_before`, `ece_after`, `calibration_temp`, `sahi_ap50`, `miou_floodnet`, `miou_rescuenet`, `onnx_max_abs_diff`). |
| `model_card.md` | Honest limitations, domain-shift caveats (e.g., rural vs. urban flood performance), failure examples, and ethical/calibration disclaimers (`D-07`). |
| `export.py` *(or `export_config.yaml`)* | Thin wrapper invoking `rv_ai.export.to_triton` to produce `model.onnx` / `.plan`, verify `< 1e-4` numerical parity, upload weights to MinIO, and emit `manifest.sha256` + `config.pbtxt` snippet. |

---

## 3. Weight Storage & Kaggle ↔ Repo Synchronization (Never Weights in Git!)

1. **Where Weights Live:**
   - **NEVER** commit `.pt`, `.pth`, `.ckpt`, `.safetensors`, `.onnx`, `.plan`, or `.tar.gz` weight files into Git (guarded by `.gitignore` + CI file-size check).
   - **Primary Store (Training Checkpoints & Production ONNX/TRT):** MinIO S3 bucket **`s3://model-artifacts/`**:
     - Training checkpoints: `s3://model-artifacts/checkpoints/<feature>/<vN>/best.pt`
     - Promoted Triton engines: `s3://model-artifacts/triton-repo/<triton_model_name>/<int_version>/model.onnx`
   - **Optional Mirror (Public Kaggle Weights):** Kaggle Models / Hugging Face private hub, mirrored to MinIO with matching SHA-256 recorded in `triton-repo/<model>/<ver>/manifest.sha256`.
2. **How Kaggle Notebooks Sync Cleanly With GitHub:**
   - **Step 1 (Notebook Bootstrap Cell):** Never `git clone` old `src/`. Cell 1 installs the exact package commit:
     ```python
     # Pinned to exact commit or branch of RescueVision
     !pip install -q "git+https://github.com/<org>/RescueVision.git@<commit_sha>#subdirectory=ai"
     ```
   - **Step 2 (Train & Log):** Notebook runs `rv_ai` training using `kaggle/<feature>/vN/config.yaml`, logs checkpoints/metrics to MLflow (or downloads outputs at end of Kaggle session).
   - **Step 3 (Pull Back to Git PR):** Developer downloads `metrics.json`, `confusion_matrix.png`, and updates `train.ipynb`/`eval.ipynb` (with outputs cleared or lightweight summary plots only, via `nbstripout` optional), uploads `.pt`/`.onnx` to MinIO, and opens an `ai/<feature>-<vN>` PR.

---

## 4. Promotion to Production, Backend Contract & Instant Rollback

### 4.1 Promotion Gate Checklist (Research → Production)
A version `kaggle/<feature>/vN/` moves to production **only through these 5 steps**:
1. **Evaluation Gate (`ci-ai-gate`):** `metrics.json` beats or equals current active version on event-held-out validation (`XView2` / `SAHI` / `mIoU`) AND Temperature Scaling `ECE <= 0.05`.
2. **ONNX/TensorRT Parity Gate:** `rv_ai.export.to_triton` proves `max(|PyTorch - ONNX|) < 1e-4` and `< 0.1%` class flips.
3. **Artifact Upload:** Validated `model.onnx` pushed to MinIO `s3://model-artifacts/triton-repo/<triton_name>/<ver_int>/model.onnx` with SHA-256 recorded in Git `triton-repo/<triton_name>/<ver_int>/manifest.sha256`.
4. **DB Registry Migration:** Add SQL seed/migration row in PostgreSQL `ai_models`:
   - `(id, model_slug, triton_name, triton_version, kaggle_ref, calibration_temp, embedding_dim, is_active)`
   - Example: `('joint_damage', 'joint_damage', 2, 'kaggle/damage-assessment/v2', 1.38, NULL, true)`.
5. **Zero-Downtime Triton Activation:** `geo-worker` (or deploy script) syncs `triton-repo/` from MinIO; `tritonserver --model-control-mode=poll` loads version `2` live inside the single shared CUDA context without restarting `core-api`.

### 4.2 AI ↔ Backend Contract (`contracts/triton/`)
Every model served in Triton obeys a strict schema defined in `contracts/triton/<triton_name>.json` and `triton-repo/<triton_name>/config.pbtxt`:

| Triton Model Name | Input Tensor(s) | Output Tensor(s) | Backend Consumer (`geo-worker` / `edge`) | DB Side Effect |
|---|---|---|---|---|
| `joint_damage` | `pre_rgb: FP32 [B,3,608,608]`, `post_rgb: FP32 [B,3,608,608]` | `bld_logits: FP32 [B,2,608,608]`, `dmg_logits: FP32 [B,5,608,608]` | `geo-worker` slices COGs, calls Triton `:8001`, divides `dmg_logits` by `ai_models.calibration_temp` | `building_assessments` + `cost_estimates` |
| `post_damage_probe` | `embedding: FP32 [B,768]` | `dmg_probs: FP32 [B,2]` | `geo-worker` when pre-event COG is null | `building_assessments` (`is_post_only=true`) |
| `person_sar_hq` | `rgb_tile: FP32 [B,3,640,640]` | `boxes: FP32 [B,300,4]`, `scores: FP32 [B,300]` | `geo-worker` (`SAHI` tiles + `ByteTrack` + DSM raycast) | `person_tracks`, `person_detections`, `assistance_cases` |
| `person_sar_edge` | `frame_rgb: FP16 [1,3,640,640]` | `det_out: FP16 [1,84,8400]` | `edge-detector` on `MediaMTX` RTSP+KLV stream | NATS Leaf → `person_detections` (`stream_ref`) |
| `flood_road_seg` | `rgb_tile: FP32 [B,3,512,512]` | `seg_logits: FP32 [B,4,512,512]` | `geo-worker` vectorizes `Water` / `Road-Blocked` polygons | `hazards` (`FLOOD_WATER`) → `evaluate_hazard_rules()` |
| `eo_embedder` | `crop_rgb: FP32 [B,3,224,224]` | `embedding: FP32 [B,768]` | `geo-worker` + `PydanticAI` query encoder | `image_embeddings` (`pgvector` HNSW) |

### 4.3 Instant Rollback (`< 30 seconds`)
If a newly promoted model (`version = 2`) misbehaves on live imagery:
1. Run one SQL transaction flipping `ai_models`: `is_active = false` on `v2`, `is_active = true` on `v1` (or set Triton `version_policy: { specific: { versions: [1] } }`).
2. `geo-worker` immediately queries `triton_version = 1` on the next batch, and any assessments tagged with `model_version_id = v2` remain auditable and queryable for re-scoring (`processing_jobs` replay). **Zero Docker rebuilds or API downtime.**
