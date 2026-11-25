# AI Training Workspace Layout & Model Promotion (`AI_PIPELINE` Research Side — `AI_TRAINING_LAYOUT.md`)

Today `notebooks/` and `notebooks/kaggle/` contain 30+ unversioned scripts and notebooks (`rv_*.ipynb`, `rv2_*.ipynb`, `rv3_*.ipynb`) without clear dataset pins, metrics, or promotion rules. This document refines the owner's proposed `kaggle/` structure into a disciplined, reproducible workspace connected cleanly to `ai/`.

---

## 1. Top-Level Name Decision: Keep `kaggle/`

* **Decision:** Keep **`kaggle/`** as the top-level AI research & training workspace (distinct from `ai/`, which owns production evaluation gates and isolated `LitServe` Docker serving containers).
* **Justification:** The team actively trains on Kaggle GPUs (`rv_*` notebooks already target Kaggle). Naming the top-level research folder `kaggle/` matches `kaggle kernels pull/push` 1:1, makes it immediately obvious where notebooks live versus production Docker services (`ai/services/`), and lets CI enforce strict rules (e.g., `nbstripout`, zero imports of `kaggle/` from `backend/` or `ai/services/`).

---

## 2. Refined `kaggle/` Directory Structure

```text
kaggle/
├── README.md                           # How to sync with Kaggle CLI, run locally, and promote a version
├── _shared/                            # Reusable notebook-free Python helpers (event-aware splitters, xBD/FloodNet loaders)
├── damage-assessment/                  # Feature 1: building segmentation, change detection, xBD grading
│   ├── v1/                             # Baseline (e.g., U-Net / Siamese U-Net + DINOv2-base)
│   │   ├── kernel-metadata.json        #   Kaggle CLI metadata (`id`, `dataset_sources`, `enable_gpu`)
│   │   ├── notebook.ipynb              #   Clean, output-stripped training notebook (or train.py)
│   │   ├── config.yaml                 #   Hyperparameters, seed, loss, image_size (replaces scattered configs/)
│   │   ├── dataset.yaml                #   Pinned Kaggle dataset slug/version + split CSV checksum
│   │   ├── metrics.json                #   Recorded validation & held-out test metrics (macro-F1, IoU, ECE)
│   │   ├── model_card.md               #   Dataset scope, class scores, failure modes, min GSD
│   │   └── export.py                   #   Exports checkpoint + writes manifest.json (`weights_sha256`) for serving
│   ├── v2/                             # Next iteration (e.g., SegFormer-B3 + ChangeFormer + calibrated DINOv2)
│   └── v3/
├── person-detection/                   # Feature 3/4: aerial occluded person detection (SARD, VisDrone, POP) + ByteTrack tuning
│   ├── v1/ ...
│   └── v2/ ...
├── flood-road-segmentation/            # Feature 2/5: FloodNet water & obstructed-road segmentation
│   └── v1/ ...
└── scene-embeddings/                   # Retrieval / Copilot RAG: DINOv2 768-d embedding tuning
    └── v1/ ...
```

---

## 3. What Goes in Every `vN/` Folder (Mandatory Checklist)

A version folder `kaggle/<feature>/vN/` is incomplete unless it contains all **7 artifacts**:
1. **`kernel-metadata.json`**: Official Kaggle API config pinning GPU type, internet flag, and dataset slug(s) so any teammate can reproduce the exact Kaggle run.
2. **`notebook.ipynb`** (or `train.py` imported by a thin notebook): Output-stripped via `nbstripout`. Reads `config.yaml`—never hardcodes `/kaggle/input/...` paths in multiple cells.
3. **`config.yaml`**: Seed, backbone, optimizer, augmentations, class weights, and event-aware split path.
4. **`dataset.yaml`**: Exact dataset source (`xview2`, `floodnet`, `sard-visdrone-pop`), version/date, and SHA-256 of `splits_event_aware.csv`.
5. **`metrics.json`**: Machine-readable evaluation output (`macro_f1`, per-class F1, `miou`, `map50`, `ece`, inference latency ms/tile) consumed automatically by `ai/eval/gate.py`.
6. **`model_card.md`**: Human-readable summary (copied/linked to `ai/model_cards/` upon promotion) stating intended use, cloud/smoke limitations, minimum GSD (`gsd_cm`), and known biases.
7. **`export.py`**: Deterministic export script producing `weights.safetensors` (or `.pt` / `.onnx` / `.pte`) + `manifest.json` containing `{ "task", "version", "weights_sha256", "input_spec", "class_map" }`.

---

## 4. Where Weights Live (NEVER in Git)

* **Git Rule:** `.gitignore` + CI `gitleaks`/size-check **forbid** `.pt`, `.pth`, `.bin`, `.safetensors`, `.onnx`, `.pte`, and `.ckpt` files in Git.
* **Authoritative Weight Store — MinIO (`models/`):**
  ```text
  s3://rescuevision/models/
    ├── DAMAGE_CLASSIFICATION/v1/weights.safetensors + manifest.json
    ├── BUILDING_SEGMENTATION/v1/weights.safetensors + manifest.json
    ├── PERSON_DETECTION/v1/weights.pt + manifest.json
    └── ...
  ```
* **Kaggle Output → MinIO Sync:** After a Kaggle run finishes, the developer downloads the output artifacts locally (`kaggle kernels output ...`) and runs `python -m ai.eval.promote --source ./artifacts --feature damage-assessment --version v2`, which:
  1. Verifies `manifest.json` + `sha256`,
  2. Runs `ai/eval/gate.py` against held-out golden tiles,
  3. Uploads weights to MinIO `models/{task}/{version}/`, and
  4. Prints the SQL/migration snippet to register the new row in `ai_models` (`weights_uri`, `metrics`).

---

## 5. Syncing Kaggle Notebooks with the Repository

1. **Install `nbstripout` + `kaggle` CLI** in `.venv` (`nbstripout --install` sets a Git filter so outputs/images are stripped on `git add` automatically).
2. **Pull/Push Loop:**
   * Edit helper code in `kaggle/_shared/` or `config.yaml` locally → push as a lightweight Kaggle utility script/dataset or sync notebook via `kaggle kernels push -p kaggle/<feature>/vN`.
   * After training on Kaggle GPU, pull updated notebook cleanly via `kaggle kernels pull <user>/<slug> -p kaggle/<feature>/vN`, commit cleaned `.ipynb` + `metrics.json` + `model_card.md`, and open a PR (`ai/<feature>-vN`).

---

## 6. Promotion & Instant Rollback Lifecycle

```text
[1. Research] kaggle/<feature>/vN/ (train on Kaggle GPU -> metrics.json + export.py)
       │
       ▼  python -m ai.eval.gate (macro-F1 / mIoU / ECE / golden GeoTIFF)
[2. Register] MinIO models/{task}/{version}/ + SQL migration inserts `ai_models` row (`is_active = false`)
       │
       ▼  Build & push `ai/services/<svc>` Docker image (or mount new weights by `weights_uri`)
[3. Canary / Promote] Verify `GET /v1/model-info` matches `weights_sha256` -> flip `ai_models.is_active = true`
       │
       ▼  Every `geo-worker` result logs `inference_runs.model_id` (full provenance)
[4. Rollback (<30s)] If bad predictions occur in prod -> flip previous `ai_models` row `is_active = true`
                     + redeploy previous immutable container tag `ghcr.io/...:v(N-1)`
```

* Because `ai_models` has `UNIQUE (task) WHERE is_active` and every `building_assessments` / `person_detections` row links to `inference_runs.model_id`, rolling back to `v(N-1)` never corrupts historical predictions and lets analysts immediately filter or re-run jobs produced by the faulty version.
