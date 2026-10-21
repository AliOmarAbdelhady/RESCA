# RescueVision V4 experiment registry

This registry records the V4 implementation gates separately from model scores. A
passing local test does not imply a Kaggle run, an artifact transfer, or useful
generalization. No GPU job or model/data download has been started by this entry.

| Gate | Scope | Status | Evidence | Decision |
|---|---|---|---|---|
| L1 | Strict experiment/artifact contracts, atomic JSON, SHA-256, resume compatibility | PASS | `python3 -m pytest tests/v4/test_artifacts.py -q` → 6 passed | Proceed to dataset adapter |
| L2 | xBD pair audit, hashed JSONL manifest, polygon target semantics, overlap risks, synchronized loader | PASS | `python3 -m pytest tests/v4/test_data_audit.py tests/v4/test_datasets.py -q` → 6 passed | Proceed to scorer |
| L3 | Official xView2 pixel scorer parity contract | PASS | `python3 -m pytest tests/v4/test_evaluation.py -q` → 7 passed | Training remains locked until real-data audit |
| K2 | Kaggle CPU audit | NOT RUN | No notebook submitted | Blocked until execution is explicitly started |
| K3 | Kaggle GPU smoke | NOT RUN | No notebook submitted | Blocked on K2 and execution authorization |

## Current V4 interfaces

- `rescuevision.v4.contracts`: `ExperimentConfig` and immutable `SampleRecord`.
- `rescuevision.v4.artifacts`: atomic JSON, SHA-256 validation, complete-file manifests and resume compatibility checks.
- `rescuevision.v4.data_audit`: `audit_dataset(root, adapter, out_dir)` for an xBD-shaped raw tree.
- `rescuevision.v4.datasets`: `load_manifest` and `PairedDataset` with separate localization and damage validity masks.
- `rescuevision.v4.evaluation`: `OfficialAccumulator` for the external `0..4` encoding. Internal `255` ignore values must be resolved before scoring.

The V4 namespace is intentionally separate from the removed legacy package imports
used by the API and old scripts. No API predictor was replaced or silently repaired.
