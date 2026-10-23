# RescueVision V4 experiment registry

This registry records the V4 implementation gates separately from model scores. A
passing local test does not imply a Kaggle run, an artifact transfer, or useful
generalization. The laptop remains source-only; the first remote xBD audit, a bounded
DINOv3 ViT-L D0 smoke, and one full-coverage D0 epoch have completed on Kaggle.
The resumable two-epoch smoke also completed on Kaggle. This is still an
implementation/coverage gate, not a benchmark accuracy result or production
training run.

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
| K4 | Kaggle DINOv3 ViT-L SAT-493M profile | PASS | Private kernel `aliomarsaleh/rv4-v4-dinov3-vit-l-profile`, version 5; xBD + packaged DINOv3 repository + pinned Kaggle PyTorch weight attached; Tesla T4; real 512×512 xBD pair; `x_norm_patchtokens` shape `[1, 1024, 1024]`; output `rv4_dinov3_vitl_profile.json` SHA-256 `511c09e51a99d990e42f5e120f50da1cf88f2741a5b7efa3ec3f3ec2ee3ef250` | Unlock the gated DINOv3 7B teacher profile; training remains blocked until the 7B memory gate and remaining dataset gates pass |
| K5 | Kaggle DINOv3 7B teacher capability profile | BLOCKED_INSUFFICIENT_MEMORY | Private kernel `aliomarsaleh/rv4-v4-dinov3-7b-teacher-profile`, version 2; completed cleanly on a Tesla T4 with all six LVD1689M proxy shards mounted; 15,526,068,224 bytes free, 15,636,037,632 bytes total, 14,000,000,000-byte fp16/bf16 weight estimate, 23,194,967,296-byte conservative runtime projection, `load_attempted: false`; output `rv4_dinov3_teacher_profile.json` SHA-256 `cf779357d306c8cedf4904d2168b3bf33b2736183a8e17680588c62d967b5bf5` | Do not load the 7B teacher on the T4; use an A100-class or larger GPU, or run a separately validated compression/offload experiment; keep the SAT493M teacher identity separate from the LVD proxy |
| K6 | Kaggle DINOv3 ViT-L D0 bounded smoke | PASS | Private kernel `aliomarsaleh/rv4-v4-dinov3-vit-l-d0-remote-smoke`, version 2; Tesla T4; real ViT-L SAT-493M weights; event-grouped xBD split with 2,660 train records available; 8 optimizer steps and 2 validation samples; finite train loss mean `0.0663678797`, validation loss mean `0.0297637898`; checkpoint SHA-256 `368f740c0ff927b885604c93d4208929a9b50361f89971b62a1c561a27617e27`; report SHA-256 `2d5fe0c23924dbb81a17497117e17f032c2051e752951f6aac8852ca36080740` | Unlock the full-coverage remote D0 run over the audited xBD training split; do not treat smoke losses as benchmark accuracy |
| K7 | Kaggle DINOv3 ViT-L D0 full coverage | PASS | Private kernel `aliomarsaleh/rv4-v4-dinov3-vit-l-d0-full-coverage`, version 1; status `COMPLETE`; Tesla T4; one epoch over all 2,660 event-grouped training records with 2,660 optimizer steps and all 139 validation records; finite train loss mean `0.0005021374753`, validation loss mean `0.0000047025923`; elapsed `3546.4283s`; checkpoint SHA-256 `6c282773a94c826082188285605294fd0c250f8dc0a7c758d15ab0c51abfe220`; report SHA-256 `73f4683a63ff5f208dd67a3bbe1bb2fdf850c109c844ca6a936a5768612a9c8f` | Preserve the checkpoint as a remote coverage artifact; next step is resumable multi-epoch training plus official held-out scoring, not an accuracy claim from these losses |
| K8 | Kaggle DINOv3 ViT-L resumable D0 smoke | PASS | Private kernel `aliomarsaleh/rv4-resumable-d0-smoke`, version 3; status `COMPLETE`; Tesla T4; bounded event-grouped xBD subset with 8 train and 2 validation records; 2 epochs, 16 optimizer steps, two epoch-boundary checkpoints, and `self_resume_test: true`; validation loss decreased from `0.0297637898` to `0.0135776633`; epoch-2 checkpoint SHA-256 `6871001bacf995e37c307a4e5fea4dd8c8b0eb09a2158dcddcd67abff742a3f0`; report SHA-256 `f61345efd86c2f3d184b9c7674b7fab0b743af0586ed83e45c46e311fba19fc9` | Unlock the all-record resumable multi-epoch run; preserve epoch checkpoints and validate official held-out scores separately |

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
