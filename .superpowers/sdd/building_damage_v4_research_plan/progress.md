# SDD ledger — plan: docs/building_damage_v4_research_plan.md

Pre-flight: L1 produces run/data contracts consumed by L2–L3; L2 produces validated label/split records consumed by L3; L3 produces the official metric consumed by all training and promotion tasks. Decision: implement these interfaces in the new `rescuevision.v4` namespace and leave the removed legacy package/API untouched, because the plan explicitly calls for the smallest deliberate repair scope.

Ruling: work proceeds on `codex/building-damage-v4` from `f89a61f`; the user explicitly authorized implementation in the RescueVision project, and a feature branch preserves reviewability.

Task L1: complete (tests: `python3 -m pytest tests/v4/test_artifacts.py -q` -> 6 passed). Implemented strict `ExperimentConfig`/`SampleRecord`, SHA-256 verification, atomic finite JSON, complete-file manifests and resume compatibility checks.

Task L2: complete (tests: `python3 -m pytest tests/v4/test_data_audit.py tests/v4/test_datasets.py -q` -> 6 passed). Implemented xBD raw pair auditing, hashed JSONL manifests, polygon rasterization, unknown damage validity, overlap-risk reporting and synchronized paired loading.

Task L3: complete (tests: `python3 -m pytest tests/v4/test_evaluation.py -q` -> 7 passed). Implemented official xView2 pixel-score accumulation and parity fixtures for gating, harmonic damage F1, encoding validation and pooled counts.

Task L4: complete (tests: `python3 -m pytest tests/v4/test_resume.py tests/v4/test_losses.py -q` -> 5 passed). Implemented the shared paired CNN baseline, masked losses, effective-batch step boundary, atomic checkpoint state and RNG restoration.

Task L5: complete (tests: `python3 -m pytest tests/v4/test_models.py tests/v4/test_tiling.py -q` -> 5 passed). Implemented explicit DINOv3 token-grid extraction/frozen wrapper and native overlap-tiled pair inference with TTA inversion. Real model loading and GPU smoke remain NOT RUN.

Task K0: complete (tests: `python3 -m pytest tests/v4/test_submission_spec.py -q` -> 2 passed). Implemented the private no-submit Kaggle request specification, unknown-state retry policy, audit CLI surface and one thin CPU-audit notebook wrapper.

Task K1: blocked (read-only Kaggle MCP discovery and local audit). Canonical xBD train/test v3, xBD tier-3 v2 and RescueNet v1 identities were recorded; dataset-status calls returned `Unauthenticated`, and the corrected local CLI reaches `/home/ali/RescueVision/data/raw/xbd` but finds no `split/images` directories. No bytes were downloaded or attached; continue with local code work while preserving K2 as blocked on mounted-input verification.

Task L7: complete (tests: `python3 -m pytest tests/v4/test_distillation.py -q` -> 5 passed). Implemented a frozen DINOv3 7B teacher wrapper, trainable student-to-teacher projection, normalized valid-patch feature loss and a stable cache key containing input, revision, preprocessing, tile and layer identities. The gated 7B checkpoint was not downloaded or profiled; the configuration is profile-only until an authorized GPU environment is available.

Task L8: complete (tests: `python3 -m pytest tests/v4/test_task_adapters.py -q` -> 9 passed). Implemented separate five-class post-only typology labels/metric/head, multi-label visible-defect target builders that preserve absent versus explicit-negative supervision, dense overlapping defect channels, grouped structure/photo split checks and specialist configs. Public dataset preparation, expert-label validation and specialist training remain NOT RUN.

Task L9: complete (tests: `python3 -m pytest tests/v4/test_inference_bundle.py -q` -> 5 passed). Implemented a self-contained inference bundle with immutable model/preprocessing/label metadata, copied checkpoint SHA-256 verification, tamper detection and deterministic reference-prediction hashing. Final checkpoint selection, calibration, external evaluation and deployment remain NOT RUN.

