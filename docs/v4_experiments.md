# RescueVision V4 experiment registry

This registry records the V4 implementation gates separately from model scores. A
passing local test does not imply a Kaggle run, an artifact transfer, or useful
generalization. No GPU job or model/data download has been started by this entry.

| Gate | Scope | Status | Evidence | Decision |
|---|---|---|---|---|
| L1 | Strict experiment/artifact contracts, atomic JSON, SHA-256, resume compatibility | PASS | `python3 -m pytest tests/v4/test_artifacts.py -q` → 6 passed | Proceed to dataset adapter |
| L2 | xBD pair audit, hashed JSONL manifest, polygon target semantics, overlap risks, synchronized loader | PASS | `python3 -m pytest tests/v4/test_data_audit.py tests/v4/test_datasets.py -q` → 6 passed | Proceed to scorer |
| L3 | Official xView2 pixel scorer parity contract | PASS | `python3 -m pytest tests/v4/test_evaluation.py -q` → 7 passed | Training remains locked until real-data audit |
| L4 | Paired CNN model, masked losses and epoch-boundary checkpoint resume | PASS | `python3 -m pytest tests/v4/test_resume.py tests/v4/test_losses.py -q` → 5 passed | Baseline code exists; real training remains locked until K2/K3 |
| L5 | DINOv3 token-grid validation, frozen feature wrapper and native tiled inference | PASS | `python3 -m pytest tests/v4/test_models.py tests/v4/test_tiling.py -q` → 5 passed | Stand-in models only; real DINOv3 load/GPU smoke is NOT RUN |
| K0 | Private Kaggle MCP submission specification and V4 CLI surface | PASS | `python3 -m pytest tests/v4/test_submission_spec.py -q` → 2 passed | Spec generation only; no notebook submitted |
| L7 | Frozen DINOv3 7B teacher cache key, projection and masked feature loss | PASS | `python3 -m pytest tests/v4/test_distillation.py -q` → 5 passed | Gated 7B download/profile NOT RUN; no external model bytes |
| L8 | Post-only five-class typology and multi-label visible-defect task contracts | PASS | `python3 -m pytest tests/v4/test_task_adapters.py -q` → 9 passed | Heads/configs/label semantics are implemented; public dataset preparation and training NOT RUN |
| K1 | Kaggle dataset identity and access discovery | BLOCKED | Read-only metadata/file searches resolved xBD v3, tier-3 v2 and RescueNet v1; `get_dataset_status` returned `Unauthenticated` | No bytes downloaded or attached; mounted audit required |
| K2 | Kaggle CPU audit | NOT RUN | No notebook submitted | Blocked until execution is explicitly started |
| K3 | Kaggle GPU smoke | NOT RUN | No notebook submitted | Blocked on K2 and execution authorization |

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

The 7B configuration is a profile-only contract. It deliberately does not
download or invoke the gated Hugging Face checkpoint. A real run must first
resolve the revision, preprocessing, tile cache and device capability on an
authorized Kaggle/Colab GPU, then record the resulting artifact manifest.

The V4 namespace is intentionally separate from the removed legacy package imports
used by the API and old scripts. No API predictor was replaced or silently repaired.
