# SDD ledger — plan: docs/building_damage_v4_research_plan.md

Pre-flight: L1 produces run/data contracts consumed by L2–L3; L2 produces validated label/split records consumed by L3; L3 produces the official metric consumed by all training and promotion tasks. Decision: implement these interfaces in the new `rescuevision.v4` namespace and leave the removed legacy package/API untouched, because the plan explicitly calls for the smallest deliberate repair scope.

Ruling: work proceeds on `codex/building-damage-v4` from `f89a61f`; the user explicitly authorized implementation in the RescueVision project, and a feature branch preserves reviewability.

Task L1: complete (tests: `python3 -m pytest tests/v4/test_artifacts.py -q` -> 6 passed). Implemented strict `ExperimentConfig`/`SampleRecord`, SHA-256 verification, atomic finite JSON, complete-file manifests and resume compatibility checks.

Task L2: complete (tests: `python3 -m pytest tests/v4/test_data_audit.py tests/v4/test_datasets.py -q` -> 6 passed). Implemented xBD raw pair auditing, hashed JSONL manifests, polygon rasterization, unknown damage validity, overlap-risk reporting and synchronized paired loading.

Task L3: complete (tests: `python3 -m pytest tests/v4/test_evaluation.py -q` -> 7 passed). Implemented official xView2 pixel-score accumulation and parity fixtures for gating, harmonic damage F1, encoding validation and pooled counts.

