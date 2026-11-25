# RescueVision — AI Training Layout, Kaggle Sync & Model Lifecycle (`AI_TRAINING_LAYOUT.md`)

**Author:** AI Systems Specialist E (Gemini 4 Hydrogen)
**Date:** 2026-11-25
**Goal:** Refine the repository owner's required `kaggle/<feature-name>/v1, v2, v3...` experiment structure into a reproducible, git-clean, Kaggle-friendly MLOps workflow that prevents weight leaks, code duplication, and unverified model activation.

---

## 1. Critique of the Current Notebook Setup

Inspecting the existing `notebooks/kaggle/` directory (for example [`rv3_train_joint_serox50.ipynb`](../../../notebooks/kaggle/rv3_train_joint_serox50.ipynb)) reveals both strong empirical engineering and severe maintainability risks:
* **What works well in `rv3`:** Event-aware data splitting (`splits_event_aware.csv`), official [`DIUx-xView/xView2_scoring`](https://github.com/DIUx-xView/xView2_scoring) parity, `EMA`/`SWA` weight averaging, OOM-adaptive batch probing, and `malloc_trim` heap guards for 12-hour Kaggle sessions.
* **What breaks at team scale:**
  1. **Flat 28-notebook sprawl:** `rv_*`, `rv2_*`, `rv3_*` notebooks sit in one flat folder with no clear promotion lineage or `v1 → v2 → v3` comparison table.
  2. **Copy-pasted model & loss code:** `SiameseUNetSE`, `MaskedFocalDiceLoss`, and `XView2PixelScorer` are inlined inside notebook cells alongside runtime monkey-patches (`_D.XBDSegmentationDataset.__getitem__ = ...`).
  3. **Broken repo reference:** Notebooks `git clone` `AliOmarAbdelhady/RescueVision.git` and append `src/` to `sys.path`, yet `src/` is absent from the current workspace (`pyproject.toml` points to a non-existent `src/`).
  4. **No calibration, ONNX parity, or registry link:** Checkpoints stay in Kaggle working volumes (`/kaggle/working/`) with no automated export, SHA-256 manifest, or `ai_models` provenance update.

---

## 2. Target Three-Tier Training & Packaging Layout

Separate **shared library code**, **versioned feature experiments**, and **deployment manifests**:

```text
RescueVision/
├── ai/                                  # Shared installable Python package (`rv_ai`)
│   ├── pyproject.toml                   # Locked deps via uv (torch, torchgeo, timm, mapie, onnx)
│   ├── src/rv_ai/
│   │   ├── models/                      # SiameseUNetSE, ChangeOS, SegFormer, D-FINE, DINOv3 probe
│   │   ├── data/                        # Event-aware datamodules (xBD, RescueNet, SARD, FloodNet)
│   │   ├── losses/                      # MaskedFocalDiceLoss, Lovasz, class-weighting helpers
│   │   ├── calibration/                 # Temperature scaling (ECE) + MAPIE conformal calibrator
│   │   ├── geometry/                    # DSM raycasting, GSD gating, uncertainty propagation
│   │   ├── eval/                        # Official xView2_scoring, SAHI AP, mIoU, OOD shift tests
│   │   └── export/                      # PyTorch -> ONNX/INT8/FP16 + numerical parity verifier
│   └── tests/                           # Unit tests for transforms, scorer parity, ONNX export
│
├── kaggle/                              # Owner-mandated versioned experiment tree (NO raw weights!)
│   ├── README.md                        # Kaggle setup guide, MLflow/HF sync, promotion checklist
│   ├── building-damage/                 # F1: Pre/post Siamese + post-only EO probe
│   │   ├── v1/                          # Baseline SiameseUNet (ResNet34, xBD 512px)
│   │   ├── v2/                          # SiameseUNetSE (SE-ResNeXt50, 608px, EMA+SWA, TempScale+MAPIE)
│   │   └── v3/                          # xBD + BRIGHT/RescueNet multi-GSD + ChangeOS/MambaBDA benchmark
│   ├── person-detection/                # F3/F4: Aerial SAR person detection under partial visibility
│   │   ├── v1/                          # YOLOX-S / D-FINE-S on SARD + HERIDAL + SAHI
│   │   ├── v2/                          # + SeaDronesSee + oblique/synthetic occlusion augs + calibration
│   │   └── v3/                          # Multi-spectral RGB + POP thermal branch (optional)
│   ├── flood-road-seg/                  # F2/F5: Floodwater + Clear/Blocked road segmentation
│   │   ├── v1/                          # SegFormer-B2 on FloodNet
│   │   └── v2/                          # SegFormer-B2 joint FloodNet + RescueNet (urban debris)
│   ├── hazard-fire-smoke/               # F5 optional: Fire & smoke detection (D-Fire + FLAME 2)
│   │   └── v1/
│   └── geo-embeddings/                  # F1 post-only + F6 retrieval + OOD drift
│       ├── v1/                          # DINOv2-base 768-d baseline + linear probe
│       └── v2/                          # DINOv3 SAT-493M / Clay v1.5 + HASTE/MLP post-only head
│
└── models/                              # Lightweight deployment registry manifests (NO weights in Git!)
    └── registry/
        ├── building-damage/v2/manifest.json
        ├── person-detection/v2/manifest.json
        ├── flood-road-seg/v2/manifest.json
        └── geo-embeddings/v2/manifest.json
```

---

## 3. Standard Contents of Every `kaggle/<feature-name>/vN/` Directory

Every `vN/` folder is a **self-contained, auditable experiment dossier**. Once promoted or archived, its config and metrics are frozen; new hypotheses always bump to `v(N+1)`.

```text
kaggle/building-damage/v2/
├── README.md            # Hypothesis, delta vs v1, Kaggle hardware (2xT4/P100), MLflow/W&B run URL, status
├── config.yaml          # Exact hyperparameters, pinned rv_ai git SHA, seed, input normalization, GSD band
├── dataset_ref.json     # Dataset IDs (Kaggle slug / HF dataset / MinIO s3://datasets/...), split CSV SHA-256
├── train.ipynb          # Thin notebook (~60 lines): pip install rv_ai@<sha> -> run training + checkpoint resume
├── eval.ipynb           # Thin notebook: frozen test split + calibration (TempScale + MAPIE) -> metrics.json
├── metrics.json         # Machine-readable evaluation output (official scorer, ECE, per-class F1, latency)
├── model_card.md        # Honest limits, sensor/GSD envelope, geographic/disaster biases, D-07 warning
└── export.py            # Exports best/calibrated ckpt -> ONNX, asserts parity <1e-4, computes SHA-256 & uploads
```

### Example `dataset_ref.json` (Zero Raw Data in Git)
```json
{
  "feature": "building-damage",
  "version": "v2",
  "datasets": [
    {
      "name": "xbd",
      "source": "s3://datasets/xbd/processed_xbd_native.tar",
      "kaggle_input_slug": "rescuevision-xbd-native",
      "sha256": "<verified-tar-sha256>",
      "license": "xView2 / CC-BY-NC-SA-4.0 (verify per-event)"
    }
  ],
  "split_manifest": {
    "file": "splits_event_aware.csv",
    "sha256": "<verified-csv-sha256>",
    "policy": "whole-disaster holdout; zero tile overlap between train/val/test"
  },
  "label_schema": {
    "0": "background",
    "1": "no_damage",
    "2": "minor_damage",
    "3": "major_damage",
    "4": "destroyed"
  }
}
```

---

## 4. Where Weights Live (Never in Git)

| Artifact Type | Storage Location | Git Tracking | Rationale |
|---|---|---|---|
| **Source code, YAML configs, `metrics.json`, `model_card.md`, `manifest.json`** | GitHub repository (`main` / PR branches) | Full Git | Lightweight text/JSON; enables code review and CI gates. |
| **Intermediate training checkpoints (`last.pt`, `best.pt`)** | **Hugging Face Hub (private org repo)** or **MinIO/S3 (`s3://model-artifacts/checkpoints/<feature>/<vN>/`)**; during Kaggle runs, auto-synced to a private Kaggle Dataset for 12h resume | **NEVER** (`.gitignore` + pre-commit + `gitleaks`/file-size CI block on `*.pt`, `*.pth`, `*.onnx`, `*.safetensors`, `*.bin`, `*.tar`) | Keeps Git clone < 50 MB and prevents 100 MB+ binary history bloat. |
| **Promoted inference artifacts (`model.onnx`, `model_int8.onnx`, `calibrator.pkl`)** | **MinIO/RustFS S3 (`s3://model-artifacts/serving/<feature>/<vN>/`)** mirrored to **Hugging Face Hub** | Only `models/registry/<feature>/<vN>/manifest.json` (URI + `sha256` + `calibration_temp` + `conformal_qhat`) | Serving containers pull weights by immutable `sha256` at startup or build, guaranteeing cryptographic identity with `ai_models`. |
| **Raw & preprocessed datasets (`xbd`, `RescueNet`, `SARD`, `HERIDAL`, `FloodNet`)** | **DVC** ([`iterative/dvc`](https://github.com/iterative/dvc)) remote on MinIO/S3 (`s3://datasets/`) or **Hugging Face Datasets** + Kaggle private datasets | Only `.dvc` pointer files / `dataset_ref.json` | Reproducible dataset snapshots without duplicating gigabytes across 6 laptops. |

---

## 5. How Kaggle Notebooks Sync Cleanly With the Repository

Free Kaggle GPUs (`2×T4` / `P100`, 12-hour limit) are the team's primary compute engine. To prevent notebook drift and inline copy-paste bugs:

1. **Zero Inline Model Code in Notebooks:** Cell 1 of `kaggle/<feature>/vN/train.ipynb` installs the exact pinned `rv_ai` package from GitHub (or an attached wheel artifact for offline Kaggle kernels):
   ```python
   # Option A: Kaggle Internet ON — pinned exact commit SHA from config.yaml
   !pip install -q "git+https://github.com/<org>/RescueVision.git@<COMMIT_SHA>#subdirectory=ai"
   # Option B: Kaggle Internet OFF (e.g., competition/restricted env) — mount `rv-ai-wheel` dataset
   # !pip install -q --no-index --find-links=/kaggle/input/rv-ai-wheel rv_ai
   ```
2. **Experiment Tracking Sync (`MLflow` or `W&B`):**
   * Use **Weights & Biases** ([`wandb/wandb`](https://github.com/wandb/wandb), free academic tier) OR a self-hosted **MLflow** ([`mlflow/mlflow`](https://github.com/mlflow/mlflow)) server behind Tailscale/HTTPS during Kaggle training so epoch metrics, loss curves, and `last.pt` checkpoints survive unexpected Kaggle kernel preemption.
   * For teams wanting zero external SaaS dependency, keep `rv3`'s `/kaggle/working/_status.json` heartbeat + periodic upload to Hugging Face Hub (`huggingface_hub.HfApi().upload_file(...)`) at the end of every epoch/checkpoint improvement.
3. **Resuming Across 12-Hour Kaggle Limits:** Every training run writes `last.pt` (model + optimizer + EMA + scheduler + epoch) to `/kaggle/working/` and mirrors it to HF Hub / Kaggle Dataset, eliminating manual `RESUME_CKPT` path edits.
4. **Pull-Back PR Workflow (Kaggle → GitHub):**
   * Run `eval.ipynb` on the frozen `val` (for threshold/calibration fitting) and `test` splits, emitting `metrics.json` + `model_card.md` updates.
   * Run `export.py` to generate `model.onnx`, verify PyTorch-vs-ONNX numerical parity (`max_abs_diff < 1e-4`), upload `model.onnx` + `calibrator.pkl` to MinIO (`s3://model-artifacts/`) / HF Hub, and generate `models/registry/<feature>/<vN>/manifest.json`.
   * Strip noisy cell outputs (`nbstripout` or `jupyter nbconvert --clear-output`) except compact summary metrics, commit `kaggle/<feature>/vN/*` + `models/registry/<feature>/vN/manifest.json` on branch `ai/<feature>-vN`, and open a Pull Request.

---

## 6. Version Promotion & Rollback Lifecycle

```
  [1. Train in Kaggle] ──► [2. Calibrate + Eval Gate] ──► [3. ONNX Export + Parity]
           │                         │                             │
     (MLflow/HF ckpt)        (ci-ai-gate passes)          (diff < 1e-4, SHA-256)
                                                                   ▼
  [6. Instant Rollback] ◄── [5. Activate in ai_models] ◄── [4. Upload to S3 + Manifest PR]
```

### Five Mandatory Promotion Steps
1. **CI Evaluation Gate (`ci-ai-gate.yml`):** GitHub Actions reads `kaggle/<feature>/vN/metrics.json` and verifies all required task metrics beat or match the active baseline AND `ece_after <= 0.05` (no broken split, no missing fields, valid `model_card.md`).
2. **ONNX Parity Check:** `export.py` runs identical synthetic & golden-tile batches through PyTorch and `onnxruntime` (`CPUExecutionProvider`), failing if `max(|y_pt - y_onnx|) > 1e-4` or top-1 class flip rate `> 0.1%`.
3. **Immutable Artifact Registration:** `model.onnx` + `calibrator.pkl` upload to MinIO (`s3://model-artifacts/serving/<feature>/<vN>/`) matching the `sha256` inside `models/registry/<feature>/<vN>/manifest.json`.
4. **Database Registry Activation (Alembic Migration or Admin CLI):**
   * Inserts row into `ai_models` (`name`, `version`, `task`, `architecture`, `training_datasets`, `metrics`, `weights_uri`, `weights_sha256`, `calibration_temp`, `conformal_qhat`, `status='validated'`).
   * Flips `is_active = true` atomically in a single SQL transaction (enforced unique per task by `ai_models_one_active_per_task_uq` in `04_imagery_ai.sql`).
5. **Serving Reload / Rollback (`< 30 seconds`):**
   * Model containers check `ai_models` / `manifest.json` on startup (and via `POST /internal/reload` authenticated admin hook) and verify `sha256(local_file) == ai_models.weights_sha256` before marking `/readyz` healthy.
   * **Rollback:** Flip `is_active = true` back to `v(N-1)` in PostgreSQL and trigger container reload (or revert the `manifest.json` tag in Compose). Every historical `building_assessments` and `person_detections` row retains its `inference_run_id → model_id`, enabling selective re-scoring of only affected incidents.
