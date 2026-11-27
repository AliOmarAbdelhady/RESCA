# Building Damage V4 — Luna 5.6 Implementation Plan

> **For Luna 5.6:** Read the research specification and this handoff before making changes. When implementation is separately authorized, use `superpowers:executing-plans` to work task by task. All checkboxes below are future work, not completed work. Do not start because this document exists.

**Goal:** Implement a reproducible building-damage research pipeline, operate its training through Kaggle MCP, and deliver verified model artifacts and local inference.

**Architecture:** Thin Kaggle notebooks execute an immutable Python package and configuration. A paired CNN establishes the baseline; paired DINOv3 satellite features, multiscale decoding and later teacher distillation are controlled experiments. Post-only typing, close-up defects and 3D evidence are separate subsequent capabilities.

**Tech stack:** Python 3.10+, PyTorch, a verified DINOv3-compatible implementation, segmentation-models-pytorch for the CNN reference, NumPy, raster/geometry tools where necessary, pytest and Kaggle MCP. Resolve exact compatible versions against the assigned Kaggle runtime and lock them; the current broad requirements are not a verified environment.

**Specification:** [Building Damage V4 Research Plan](building_damage_v4_research_plan.md), including section 13's K0–K8 operational gates. This document supplies technical implementation decisions; read both.

## Global constraints

**Execution boundary:** the RescueVision laptop is source-only for this project.
Do not run pytest, the V4 CLI, notebooks, model downloads, data audits, or
training on its CPU/GPU. Runtime validation and all accelerator work must run
in an authenticated Kaggle or Colab session, with outputs returned as hashed
artifacts. Local edits and static review are allowed; a local test command is
not evidence for a remote gate.

- Current request is **instructions only**. Do not implement, install, submit notebooks, start training, upload datasets or message another chat until the user separately authorizes the relevant execution.
- Work from `/home/ali/RescueVision`. Inspect current status and applicable instructions again at execution time; multiple people/agents may change this checkout. Preserve their edits and existing output artifacts.
- Use a `codex/` branch when branch creation is appropriate. Do not reset the repository, resurrect all deleted source, push, publish or deploy without task-scoped authorization.
- Kaggle/Colab are the available compute platforms. Accuracy takes priority over elapsed time; GPU memory remains a real constraint. Do not assume account pooling or manufacture quota availability.
- DINOv3 is required. Approved model: `facebook/dinov3-vit7b16-pretrain-sat493m`. Satellite ViT-L is the primary adaptable candidate; test its access separately.
- Preserve original evaluation labels. Historical test exposure stays disclosed. Reserve an independent grouped audit set before new tuning.
- No accuracy claim from a completed job alone. No world-record claim from crossing 0.82. The earlier 80–84% forecast is speculative, not an acceptance criterion or guaranteed outcome.
- Product output must distinguish observed damage, unobservable surfaces and uncertainty. No structural-safety certification from an image classifier.

## Review focus

1. Missing/corrupt/mismatched image pairs must fail with an audit record, not silently reduce evaluation coverage. Owned by L2.
2. Unknown damage label 255 must not automatically become positive localization or a no-damage negative. Owned by L2/L3.
3. Different preprocessing, source versions or data splits must prevent incompatible checkpoint/cache reuse. Owned by L1/L4.
4. Interrupted training or uncertain submission state must not reset schedules or create duplicate GPU runs. Owned by L4/L6.
5. Native-size tiling must cover edges and preserve output coordinates on odd-sized images. Owned by L5/L9.

## First actions once implementation is authorized

Read repository instructions, `git status`, `pyproject.toml`, current configs, the research document, and this file. Confirm whether `src/rescuevision_ai` is still absent. Inspect relevant history without restoring it automatically. Create a short status entry listing what is present, missing, already running, and safe to reuse. Discover Kaggle tools and current schemas again. Start with L1–L3 locally; do not jump straight to the 7B model or a full GPU run.

## Proposed files and boundaries

Keep all new research code under `src/rescuevision_ai/v4/`, with minimal package initializers. Existing CLI/API imports refer to removed legacy modules; implementing V4 does not justify silently faking those modules or claiming the whole API is repaired.

| File | Responsibility |
|---|---|
| `contracts.py` | Typed configuration, manifest, checkpoint and prediction contracts |
| `artifacts.py` | Hashing, atomic writes and provenance/compatibility checks |
| `data_audit.py` | Raw inventories, dataset adapters, pair and overlap checks |
| `datasets.py` | Paired/typology/defect sample loading and task validity masks |
| `transforms.py` | Synchronized spatial augmentation and model-specific normalization |
| `evaluation.py` | Streaming official pixel counts and separate object/defect metrics |
| `training.py` | Optimizer updates, validation, stopping and deterministic resume |
| `models/cnn.py` | Strong paired CNN baseline |
| `models/dinov3.py` | DINOv3 loading, token-grid validation and multiscale neck |
| `models/paired.py` | Temporal fusion, localization and damage heads |
| `models/distillation.py` | Feature distillation and separately configured task-logit distillation |
| `inference.py` | Native-resolution overlap inference and packaged-model loading |
| `cli.py` | Auditable stage entry points |
| `scripts/v4_submit_spec.py` | Generate notebook/submission payloads; never implicitly execute them |
| `configs/v4/` | Versioned data adapters, experiment settings and final recipe |
| `tests/v4/` | Consequential behavior checks tied to tasks below |
| `ai/kaggle/building-damage/v4/` | Eight thin wrappers listed in research section 10 |
| `ai/kaggle/building-damage/v4/notes/v4_experiments.md` | Experiment registry, results, failures and decisions |

## L1 — Establish shared contracts and artifact integrity

**Files:** create `contracts.py`, `artifacts.py`, package initializers and `tests/v4/test_artifacts.py`.

**Interfaces:** `load_experiment(path: Path) -> ExperimentConfig`; `sha256_file(path: Path) -> str`; `validate_artifact(path: Path, expected_sha256: str) -> None`; `validate_resume(checkpoint_meta: dict, run_meta: dict) -> None`.

Define `ExperimentConfig` with schema version, experiment/parent IDs, task, model ID and revision, train/validation/audit manifest hashes, normalization ID, resolution policy, loss, optimizer/scheduler, effective batch, seed, selection metric and output directory. Reject unknown fields and impossible task/model combinations. Paths are resolved explicitly relative to the configuration or supplied root, not the process's accidental working directory.

Run artifacts contain `run_manifest.json`, `artifact_manifest.json`, `progress.json`, `metrics.json`, logs, checkpoints and optional probabilities. Include actual hardware/environment and the reason a run stopped. JSON must reject NaN/Infinity. Write checkpoints/manifests through a temporary sibling then atomic rename; list only complete files in the artifact manifest.

- [ ] Write checks for corrupted hashes, incompatible split/normalization/model revisions and partial artifact writes. Run them and observe the expected failure before implementing.
- [ ] Implement the interfaces and required field validation.
- [ ] Run `python3 -m pytest tests/v4/test_artifacts.py -q`; require PASS. Review the diff and record the task's result before advancing.

## L2 — Build dataset adapters, manifests and a valid sample loader

**Files:** create `data_audit.py`, `datasets.py`, `transforms.py`, `configs/v4/data_xbd.yaml`, `tests/v4/test_data_audit.py` and `tests/v4/test_datasets.py`.

**Interfaces:** `audit_dataset(root: Path, adapter: str, out_dir: Path) -> AuditResult`; `load_manifest(path: Path) -> list[SampleRecord]`; `PairedDataset(manifest: Path, split: str, transform: Callable | None)`.

A `SampleRecord` contains sample ID, source dataset/version, original image/photo IDs, pre/post paths and hashes, event/scene/group IDs, split and label paths/hashes. Record physical-building groups where available. Keep a list of unresolved overlap risk when identity is unavailable; do not fabricate identifiers that imply verified uniqueness.

A paired sample returns `pre`, `post` as float tensors `[3,H,W]`; `loc_target` and `loc_valid` as `[H,W]`; `damage_target` as `[H,W]` with internal class IDs 0–3; `damage_valid` as `[H,W]`; sample ID and original dimensions. Build localization from independently valid building annotations. Unknown-grade buildings can have valid localization and invalid damage. All true void pixels must be excluded from the corresponding loss.

Spatial transforms act jointly on images and masks. Label resizing uses nearest-neighbor. Model-specific RGB normalization follows the pinned model configuration. Training-only crops do not change immutable full-tile evaluation targets. Split before cropping; preserve official split identities for comparability and maintain a separate grouped transfer/audit protocol.

- [ ] Test missing/corrupt pairs, duplicate/photo/scene overlap, mismatched dimensions, 255 handling, consistent transforms and complete coverage accounting.
- [ ] Implement adapters starting with xBD only. Compare a fixed sample of generated evaluation rasters against canonical annotation rasterization/reference targets, including unclassified policy. Keep modified training targets separate.
- [ ] Run `python3 -m pytest tests/v4/test_data_audit.py tests/v4/test_datasets.py -q`; require PASS. Output counts, class supports and overlap decisions for review.

## L3 — Implement official scoring before training

**Files:** create `evaluation.py`, `tests/v4/test_evaluation.py` and `01_reference_evaluation.ipynb`.

**Interface:** `OfficialAccumulator.update(loc_pred: np.ndarray, damage_pred: np.ndarray, loc_target: np.ndarray, damage_target: np.ndarray) -> None`; `summary() -> dict`.

External benchmark rasters use 0 background and 1–4 damage grades. Accept only valid evaluation encodings; never pass internal 255 directly to an official scorer that expects 0–4. Resolve void/unclassified conversion from the canonical target-generation protocol, record it, and test it. Stream global integer TP/FP/FN counts rather than averaging batch F1s.

Match the pinned upstream scorer exactly: localization binary pixel F1; damage gated by predicted localization and scored on target-building pixels; harmonic mean of the four grade F1s; combined 0.3/0.7 weighting and reference epsilon behavior. Use an independently generated PNG fixture tree with the upstream scorer as the parity oracle. Record reference commit/hash and any minimal compatibility adjustment without changing semantics.

- [ ] Write perfect/wrong-class/missed-building/false-building/empty-class fixtures and pooled-versus-batched accumulation checks; verify failure first.
- [ ] Implement and compare counts and metrics to the upstream reference, tolerance `1e-6` for floating output and exact counts.
- [ ] Run `python3 -m pytest tests/v4/test_evaluation.py -q`; require PASS. Separate instance metrics into separately named outputs, never `xview2_approx`.

## L4 — Build one correct trainer and resume path

**Files:** create `training.py`, `models/cnn.py`, `configs/v4/cnn_baseline.yaml`, `tests/v4/test_resume.py`, `tests/v4/test_losses.py`.

**Interfaces:** model `forward(pre: Tensor, post: Tensor) -> dict[str, Tensor]` returns `loc_logits [B,1,H,W]` and `damage_logits [B,4,H,W]`; `train(config_path: Path, resume: Path | None = None) -> Path` returns the completed or cleanly paused run directory.

Start with a shared ResNet34 encoder, multiscale pre/post features, simple concatenation/absolute-difference fusion, binary localization head and four-grade damage head. Keep localization rooted in pre-image geometry. This is a reproducible project CNN baseline, not a claim of bit-identical reproduction of every winner component.

Initial recipe below is a **proposed starting configuration**, to be profiled and changed through named experiments:

- Native-scale random crops of 512×512; no whole-tile resize. Flip/90-degree rotation shared across the pair; initially no elastic deformation or automatic registration.
- AdamW, encoder learning rate `1e-4`, decoder/head rate `3e-4`, weight decay `1e-4`, warmup one epoch then cosine, gradient norm cap `1.0`, seed `42`.
- Effective batch `8` via explicit microbatch and accumulation. Account for partial final accumulation and advance the scheduler only on actual optimizer updates; do not advance it after a skipped AMP overflow step.
- Localization masked BCE + foreground Dice; damage masked CE + per-class Dice, each composite equally weighted initially. Mask all invalid targets before reductions. On an empty valid set return a differentiable zero for that component. Start without aggressive sampling, class weights, EMA or SWA; imbalance changes become named ablations.
- Plan 60 epochs in resumable chunks as a starting run budget; validate each epoch. Select best checkpoint by **full original-label validation official combined score**. Initially fix inference threshold at 0.5; defer threshold search until the checkpoint is selected. If training is still improving at the declared endpoint, record that and make an explicit continuation decision.

Checkpoint fields: schema/config/source/data/model hashes; model/optimizer/scheduler/scaler states; epoch and update counters; sampler/dataloader state or documented restart position; Python/NumPy/Torch CPU/CUDA RNG states; best metric/epoch and stop reason. Default resume occurs at epoch boundaries to simplify exact sampling replay. Persist both last and best checkpoint. Any later EMA has its own state and ablation identity.

- [ ] Test finite masked loss and gradients, correct zero-valid behavior, accumulation-step counts and resumed optimizer/scheduler/random-state behavior on a deterministic CPU miniature workload.
- [ ] Implement the trainer and baseline. Compare uninterrupted versus epoch-boundary resumed weights/loss within `1e-6` on the deterministic CPU fixture. On GPU document numerical nondeterminism separately.
- [ ] Run `python3 -m pytest tests/v4/test_resume.py tests/v4/test_losses.py -q`; require PASS. Do not report synthetic metrics as model accuracy.

## L5 — Implement DINOv3 and native-resolution inference

**Files:** create `models/dinov3.py`, `models/paired.py`, `inference.py`, `configs/v4/dinov3_d0.yaml`, `tests/v4/test_models.py`, `tests/v4/test_tiling.py`.

Use pinned `facebook/dinov3-vitl16-pretrain-sat493m` for D0 after access verification. Keep original RGB patch embedding and shared before/after weights. Obtain spatial patch tokens, exclude non-spatial tokens, validate grid dimensions against the actual preprocessed input and stride 16. Never guess layer/token layouts from another DINO version. Verify current primary documentation and actual model outputs before finalizing the loader.

D0 trains a simple dense temporal head over frozen spatial features. D1 adds an intermediate-layer multiscale neck, with selected block indices recorded from the loaded model's actual depth. D2 compares trainable last blocks or LoRA; confirm gradient flow and exact trainable parameters. D3 adds the detail branch; D4 adds alignment in the canonical target coordinate frame. Do not introduce all these modules at once or silently alter D0 after comparing it.

Initial frozen-head recipe: native 512 crops, AdamW head learning rate `3e-4`, weight decay `1e-4`, effective batch 8, same loss/evaluation protocol as baseline. For D2 start with backbone/adapter learning rate `1e-5` and head rate `1e-4`; record the choice and profile before committing to a full run. These are hypotheses, not claimed optimal hyperparameters.

**Inference interface:** `predict_pair(pre: np.ndarray, post: np.ndarray, model: nn.Module, recipe: InferenceRecipe) -> PairPrediction`. Preserve original height/width; pad deterministically, overlap 512 tiles with stride 384 initially, blend probabilities with nonzero weights and crop padding. Transform/invert paired TTA identically. Resize probabilities before argmax if necessary, never resize integer class maps bilinearly.

- [ ] Test token-grid extraction with non-spatial tokens, frozen-backbone no-gradient behavior, output shapes, odd image dimensions, uncovered seams/edges, constant-probability stitching and TTA round trips.
- [ ] Use tiny stand-in models for unit tests; gate real DINOv3 load/forward/backward as a separate GPU smoke check. No automatic 7B download in ordinary tests.
- [ ] Run `python3 -m pytest tests/v4/test_models.py tests/v4/test_tiling.py -q`; require PASS. Runtime must separately prove the selected real backbone/head fit and receive gradients where intended.

## L6 — Package notebooks and operate Kaggle MCP safely

**Files:** create `cli.py`, `scripts/v4_submit_spec.py`, thin notebooks, `tests/v4/test_submission_spec.py` and `outputs/v4/registry.jsonl` at execution time.

**CLI contract to implement:** `python3 -m rescuevision_ai.v4.cli audit --config PATH`; `train --config PATH [--resume PATH]`; `evaluate --config PATH --checkpoint PATH`; `profile --config PATH`; `predict --config PATH --checkpoint PATH --pre-image PATH --post-image PATH --out-dir PATH`. Submission builder accepts `--config`, `--stage` and `--out-dir`; it only writes reviewable source/specification artifacts and performs no network submission.

Notebook source loads a pinned package artifact, verifies its checksum, resolves attached input hashes and invokes one CLI stage. Never clone the moving default branch. Package/environment provenance must be available before importing the experiment. Keep dependency installation failures fatal. Do not reinstall the entire unrelated geospatial/reporting stack into every training job.

Technical MCP sequence, to execute only when authorized:

1. Discover current `search_datasets`, `get_dataset_metadata`, file-list/status and notebook schemas. Inspect existing project runs read-only before creating anything.
2. Prepare the request for `save_notebook`: explicit source `text`, unique/versioned slug/title, private visibility, Python/notebook settings, CPU or GPU choice, internet choice and input sources. Use schema presence flags where required. Resolve actual valid language/kernel/machine-shape values; do not invent API literals.
3. Submit once. Record returned owner/slug/version/session identity before subsequent calls. A timeout is unknown submission state: inspect notebook info/status before a retry.
4. Monitor that exact notebook version with `get_notebook_session_status`. Use a few-minute polling interval with backoff for unchanged state, not rapid repeated calls. This is a later running orchestration loop, not an automation installed by this document.
5. After completion, list outputs; retrieve manifests/metrics first, then selected checkpoint/probability artifacts via download tools. Treat returned links as locators requiring an actual verified transfer. Record counts, byte sizes and SHA-256.
6. Mark artifacts verified only after local integrity/contract checks. Attach prior outputs to the next job through the supported kernel source mechanism, verifying mounted content hashes at startup. If version-pinning is insufficient, use a verified immutable dataset/version fallback before proceeding.
7. On clean session-budget stop, submit a continuation only from a fully durable checkpoint. Stop dependent stages on missing/corrupt artifacts. On OOM change microbatch/accumulation explicitly, create a new attempt identity, and retain the failed attempt record.

Use `create_notebook_session` only if the chosen flow requires it; it is not a second launch after `save_notebook`. Do not assume live log streaming. Persist short structured progress records plus logs in outputs, and distinguish accessible live output from artifacts available only at completion. Dataset-version finalization, secrets, account switching and Colab control are documented tool gaps, not fictional MCP calls.

- [ ] Test submission-spec generation is private by default, contains no token, records immutable inputs and cannot itself submit; test unknown-state retry handling using a local orchestration model/fake transport.
- [ ] Run `python3 -m pytest tests/v4/test_submission_spec.py -q`; require PASS.
- [ ] Submit CPU audit, inspect outputs, then submit one GPU smoke. Only passing both unlocks full CNN training and then D0.

## L7 — Profile and use the approved 7B teacher

**Files:** create `models/distillation.py`, `configs/v4/dinov3_teacher_7b.yaml`, teacher notebook and `tests/v4/test_distillation.py`.

The approved backbone provides features, not damage probabilities. Start in evaluation/no-gradient mode and profile one actual pre/post training tile at the chosen dtype/resolution. Record peak memory, throughput and projected feature storage. BF16 requires actual device support; offload/quantization changes must be explicit and checked for feature/output effects. Do not attempt full 7B Adam training on an assumed free GPU.

**Cache key:** SHA-256 of input identity, source model revision, preprocessing specification, tile coordinates and selected layer IDs. Store patch grids, valid extents and metadata in independently resumable shards. Train/validation/test identities remain separate; teacher extraction does not authorize transductive fitting on held-out imagery.

**Feature loss interface:** `feature_distillation_loss(student: Tensor, teacher: Tensor, valid: Tensor) -> Tensor`, using a trainable dimension projection and normalized valid patch comparisons. Start feature loss weight `0.1` against supervised loss weight `1.0`; compare with weight zero on the same training/validation protocol. Frozen teacher parameters must receive no gradients. A separate D5b experiment trains a damage head using training labels before any temperature-scaled logit loss.

- [ ] Test cache invalidation, teacher no-gradient behavior, differing embedding dimensions and masked padding; run `python3 -m pytest tests/v4/test_distillation.py -q` and require PASS.
- [ ] Profile before extraction; extract only if an available GPU genuinely fits. If blocked, report exact memory/access evidence, continue independent ViT-L work, and leave the 7B experiment visibly blocked rather than claiming it ran.
- [ ] Train and validate student-only versus distilled finalists. Keep 7B only when its measured contribution is useful.

## L8 — Add post-only and fine-defect specialists

**Files:** add dataset adapters/configs, `models/post_only.py`, `models/defects.py`, relevant notebooks and `tests/v4/test_task_adapters.py`.

Reproduce the corrected DamageTriage-Bench photo-atomic crop task with its five classes and separate metric. Do not substitute xBD minor/major grades for its roof/structural taxonomy. Evaluate supplied-support recognition separately from predicted-footprint end-to-end use.

For dacl10k/CUBIT/other defect data, preserve original supervision types. Use independent sigmoid channels for genuinely overlapping defect segmentation; image/box labels cannot supervise invented pixel masks. Keep crack/area/component measurements conditional on calibrated scale and actual visible surfaces. Split by structure/photo/capture group, checking cross-dataset duplicates. Expert-labeled building data is required for target-domain claims unsupported by public labels.

- [ ] Test adapter label maps, absent annotation versus negative labels, overlapping multilabel targets and grouped-split integrity. Run `python3 -m pytest tests/v4/test_task_adapters.py -q`; require PASS.
- [ ] Train/evaluate specialists through the same artifact/MCP/resume machinery. Deliver per-class results and visibility limits, not a single blended accuracy.
- [ ] Add 3D surface association only after calibrated imagery/pose/scale exist. If absent, deliver a documented blocked 3D increment and the valid 2D evidence contract; do not fabricate geometry.

## L9 — Freeze final evaluation and deliver a working inference package

**Files:** create `configs/v4/final_recipe.yaml`, final notebook, `tests/v4/test_inference_bundle.py`, model card and final experiment report.

Choose checkpoint, class thresholds/calibration, TTA, overlap and ensemble weights exclusively on validation or nested training folds. Record candidate seeds and failure outcomes. Final recipe lists checkpoint hashes and the exact dataset/scorer identities. Separate historically exposed official comparisons from the untouched independent audit.

Final bundle includes package/source identity, environment lock, model weights/hash, model/config revisions, normalization and label maps, inference recipe, calibration parameters, reference inputs/predictions with tolerances, metrics and limitations. `PairPrediction` contains original dimensions, localization probability, per-grade probabilities, final masks, validity/quality fields and model provenance. Per-building output adds geometry, probabilities, observed defects and evidence references; avoid implying location is georeferenced when transform/CRS is missing.

- [ ] Test clean-environment bundle load, corrupt checkpoint rejection, identical preprocessing, native-shape output and reference prediction agreement. Run `python3 -m pytest tests/v4/test_inference_bundle.py -q`; require PASS.
- [ ] Freeze recipe, run final evaluation without tuning, retrieve complete outputs and verify local artifact hashes.
- [ ] Reproduce the reference inference locally within recorded tolerance. This proves bundle usability, not real-world generalization.
- [ ] Deliver results and source changes for review. Do not silently replace the legacy API predictor, push, deploy, publish weights or submit to a competition. Any later API adapter must preserve and test existing contracts as a separately scoped task.

## Failure handling and reporting Luna must follow

Use `PASS`, `FAIL`, `BLOCKED` and `NOT RUN` per gate. Distinguish local tests, Kaggle execution, artifact verification and scientific evaluation. An MCP acceptance response is not run completion; run completion is not proof that all samples were processed; all samples processed is not proof of useful accuracy.

When blocked, report the exact operation/error, affected task, evidence and remaining independent work. Missing credentials or data cannot be repaired with mock data in a production/benchmark path. Do not keep re-running identical failed jobs or change the metric to improve the displayed score. Never conceal a negative result or silently replace an exposed audit set.

After each task, update `ai/kaggle/building-damage/v4/notes/v4_experiments.md` with its configuration, validation evidence and decision. For each submitted run, record owner/slug/version/session, source/data/model hashes, seed, state, stop reason and artifact locations. Report only meaningful progress: a passed gate, material failure, evidence-based change or required user action.

## Copyable opening instruction for Luna 5.6

“Read `ai/kaggle/building-damage/v4/notes/building_damage_v4_research_plan.md` and `ai/kaggle/building-damage/v4/notes/building_damage_v4_luna56_handoff.md` in `/home/ali/RescueVision`. They define the research and technical execution plan. Do not treat estimated accuracy as achieved or guaranteed. If the user has authorized implementation, begin L1–L3 locally, preserve others' changes, then progress through the CPU audit and GPU smoke gates using Kaggle MCP. Do not launch full training before those gates pass. Use DINOv3, preserve original evaluation labels, maintain resumable immutable artifacts and disclose blockers and negative results. If the request is still plan-only, review the documents and report readiness without editing code or launching jobs.”

## Handoff status

This document is a technical instruction artifact for Luna 5.6. The implementation is now in progress on the `codex/building-damage-v4` branch: L1–L5, K0 and L7 have passed local gates, while K1–K3 and real model/GPU execution remain explicitly blocked or not run as recorded in `ai/kaggle/building-damage/v4/notes/v4_experiments.md`. No Luna session has been created or messaged, and no training job or external submission has been started.
