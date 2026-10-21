# RescueVision V4 experiment registry

This registry records the V4 implementation gates separately from model scores. A
passing local test does not imply a Kaggle run, an artifact transfer, or useful
generalization. The laptop remains source-only; the first remote xBD audit has
completed on Kaggle and no training job has started.

**Current execution policy:** the laptop is source-only. Do not run tests, the
CLI, notebooks, downloads or training on its CPU/GPU. K2 onward must execute in
an authenticated Kaggle/Colab runtime and return verifiable artifacts.

| Gate | Scope | Status | Evidence | Decision |
|---|---|---|---|---|
| L1 | Strict experiment/artifact contracts, atomic JSON, SHA-256, resume compatibility | PASS | `python3 -m pytest tests/v4/test_artifacts.py -q` → 6 passed | Proceed to dataset adapter |
| L2 | xBD pair audit, hashed JSONL manifest, polygon target semantics, overlap risks, synchronized loader | PASS | `python3 -m pytest tests/v4/test_data_audit.py tests/v4/test_datasets.py -q` → 6 passed | Proceed to scorer |
| L3 | Official xView2 pixel scorer parity contract | PASS | `python3 -m pytest tests/v4/test_evaluation.py -q` → 7 passed | Training remains locked until real-data audit |
| L4 | Paired CNN model, masked losses and epoch-boundary checkpoint resume | PASS | `python3 -m pytest tests/v4/test_resume.py tests/v4/test_losses.py -q` → 5 passed | Baseline code exists; real training remains locked until K2/K3 |
| L5 | DINOv3 token-grid validation, frozen feature wrapper and native tiled inference | PASS | `python3 -m pytest tests/v4/test_models.py tests/v4/test_tiling.py -q` → 5 passed | Stand-in models only; real DINOv3 load/GPU smoke is NOT RUN |
| L6 | Thin Kaggle wrappers for audit, teacher profile, specialist manifest audit and bundle verification | PASS | `python3 -m pytest tests/v4/test_notebook_wrappers.py -q` → 1 passed; audit wrapper executed as Kaggle kernel version 4 | GPU/model notebooks remain gated on the next remote smoke |
| K0 | Private Kaggle MCP submission specification and V4 CLI surface | PASS | `python3 -m pytest tests/v4/test_submission_spec.py -q` → 2 passed | Spec generation only; no notebook submitted |
| L7 | Frozen DINOv3 7B teacher cache key, projection and masked feature loss | PASS | `python3 -m pytest tests/v4/test_distillation.py -q` → 5 passed | Gated 7B download/profile NOT RUN; no external model bytes |
| L8 | Post-only five-class typology and multi-label visible-defect task contracts | PASS | `python3 -m pytest tests/v4/test_task_adapters.py -q` → 12 passed | Heads/metrics/configs/manifest adapters/label semantics are implemented; public dataset preparation and training NOT RUN |
| L9 | Final inference-bundle integrity and deterministic reference contract | PASS | `python3 -m pytest tests/v4/test_inference_bundle.py -q` → 5 passed | Bundle packaging is tested; final checkpoint selection/evaluation NOT RUN |
| K1 | Kaggle dataset identity and access discovery | PASS | xBD train/test dataset attached to the private audit kernel; remote mount root and file inventory verified | Tier-3 and specialist sources remain separate acquisition gates |
| K2 | Kaggle CPU audit | PASS | Private kernel `aliomarsaleh/rv4-v4-cpu-data-audit`, version 4; status `COMPLETE`; output `rv4_cpu_audit.json` SHA-256 `ddc84dfdafb549538a205e569d9e77263f4a5318f21cd3ee8029ffd37ae79888`; 13,062 files, 7,464 images, 5,598 labels, 1024×1024 PNG and `features.lng_lat` samples | Unlock the one-run GPU smoke gate; do not treat this as model accuracy |
| K3 | Kaggle GPU smoke | PASS | Private kernel `aliomarsaleh/rv4-v4-gpu-smoke`, version 1; status `COMPLETE`; output `rv4_gpu_smoke.json` SHA-256 `14ecb171f9a057011b743a1c5b1eb5ab5199818e7cbcfb7bdaf1be215b931956`; Tesla T4, CUDA available, real xBD pair, finite loss `1.648593`, backward/optimizer step completed | Unlock real DINOv3 ViT-L profiling; gated HF credentials remain a prerequisite |

## Current V4 interfaces

- `rescuevision.v4.contracts`: `ExperimentConfig` and immutable `SampleRecord`.
- `rescuevision.v4.artifacts`: atomic JSON, SHA-256 validation, complete-file manifests and resume compatibility checks.
- `rescuevision.v4.data_audit`: `audit_dataset(root, adapter, out_dir)` for an xBD-shaped raw tree.
- `rescuevision.v4.datasets`: `load_manifest` and `PairedDataset` with separate localization and damage validity masks.
- `rescuevision.v4.evaluation`: `OfficialAccumulator` for the external `0..4` encoding. Internal `255` ignore values must be resolved before scoring.
- `rescuevision.v4.models.distillation`: frozen-teacher wrapper, trainable feature projection, normalized valid-patch loss and cache identity for the DINOv3 7B teacher branch.
- `rescuevision.v4.models.post_only`: five-class post-event typology label map, independent macro-F1 and footprint-conditioned classification head.
- `rescuevision.v4.models.defects`: explicit absent/negative/positive annotation handling, overlapping dense masks and independent sigmoid channels.
- `rescuevision.v4.task_adapters`: grouped structure/photo split-integrity checks shared by specialist datasets.
- `rescuevision.v4.specialist_datasets`: strict post-only and defect JSONL adapters that preserve annotation-unit, footprint-source and missing-label provenance.
- `rescuevision.v4.bundle`: self-contained checkpoint hash, preprocessing identity, label-map/recipe metadata and deterministic reference-prediction digest.

The Kaggle notebooks under `notebooks/kaggle/v4/` are intentionally thin
wrappers. They read environment-provided immutable inputs and call the V4
package; they do not clone moving branches, install hidden dependencies,
submit jobs, tune thresholds or print credentials.

`scripts/v4_submit_spec.py` marks every request as `kaggle_remote` and
`local_execution_allowed: false`; generating or reviewing a request does not
launch it.

All acquired sources are tracked in `configs/v4/dataset_registry.yaml`. They
are combined through task-specific adapters and validity masks according to
`docs/v4_all_dataset_training_policy.md`; incompatible labels are never merged
into one target.

The 7B configuration is a profile-only contract. It deliberately does not
download or invoke the gated Hugging Face checkpoint. A real run must first
resolve the revision, preprocessing, tile cache and device capability on an
authorized Kaggle/Colab GPU, then record the resulting artifact manifest.

The V4 namespace is intentionally separate from the removed legacy package imports
used by the API and old scripts. No API predictor was replaced or silently repaired.
