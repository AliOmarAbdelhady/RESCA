# AI

Training and testing happen on GPUs: Kaggle, Colab, or a teammate's own laptop or desktop with CUDA. Training and running notebooks and tests locally is allowed, and tests may need PyTorch and a GPU. The CPU-only limit applies to production serving only, which starts in about five months (from around April 2027); until then do not restrict experiments to CPU.

In production the server is CPU-only: models run as ONNX (or OpenVINO) inside small FastAPI services. A model never decides alone; a person confirms consequential results.

## Layout

```
ai/
  kaggle/<feature>/v1/, v2/, …     one folder per experiment version (the notebooks)
  src/resca_ai/                   shared, tested code: datasets, transforms, models, metrics, export
  serving/
    template/                     the one FastAPI + ONNX Runtime service template
    damage/  vision/  embed/      one folder per model family, built from the template
  model-cards/<model>-<version>.md
```

Features: `building-damage` (F1), `flood-road-segmentation` (F2), `person-detection` (F3), `person-tracking` (F4), `compound-hazards` (F5), `reports-retrieval` (F6). Today: `building-damage` has v1 to v4 and `flood-road-segmentation` has v1 and v2. Each version folder has a README listing its notebooks. v1 to v3 hold several notebooks each and predate the layout below. v4 also holds its own research code (`src/`, `tests/`, `configs/`, `scripts/`, `notes/`) because it is still an experiment. Code moves into `ai/src/resca_ai` only once it has proved itself, and from then on it must pass every gate.

### What a new version folder holds

```
ai/kaggle/building-damage/v3/
  README.md          goal, what changed from v2, result, decision (promote or not)
  notebook.ipynb     thin: installs resca_ai at a pinned commit, runs it, no logic of its own
  config.yaml        every setting: data revision, split hash, seeds, model, training
  manifest.json      dataset revision and licence, code commit, environment, hashes
  results.json       metrics on validation and, after selection is frozen, on test
```

Notebooks are committed without outputs. Weights and datasets never enter Git; weights go to object storage under a checksum, referenced from `manifest.json`.

## Rules

| ID | Rule | Gate |
|---|---|---|
| A1 | Every experiment is reproducible: dataset revision and licence, manifest hash, code commit, seeds, environment and preprocessing recorded; shared transforms live in `ai/src` and the service uses the same ones. | Manifest validation; small CPU rerun within tolerance |
| A2 | Split by disaster event and geography before tiling or augmentation; keep before/after pairs and near-duplicates together; fit only on training data; **never choose settings on the test split**; open the test split once, after selection is frozen. | Disjoint-split and duplicate checks; split hash committed |
| A3 | Before scoring a candidate, write down the baseline, per-class recall floors for safety classes (for example destroyed buildings, people), false-alarm ceiling, minimum samples and CPU budget. A model is promoted only if it meets them, with a signed model card. | Promotion check rejects missing thresholds |
| A4 | The exported ONNX model gives the same decisions as the source model after preprocessing, quantization and postprocessing, on golden inputs including edge cases. Use int8 only where it is measured faster without changing decisions. | Parity test; latency and memory on the target CPU |
| A5 | All model services use the same template: verified model digest at startup, threads set to physical cores, one heavy job at a time across the server, bounded payloads, private network only. | Readiness checks digest; concurrency tests |
| A6 | Results record model version, input quality, confidence, abstentions, latency and failures. Consequential outputs (a detected person, a damage grade that drives cost, a hazard) are shown as *AI proposed* and need a person to confirm. A missing or uncertain model produces "unknown", never a guess. | State-machine tests; review |

## Model service contract

Request: job ID, input object key and its hash, coordinate system, units, requested model and digest, deadline. Response: results with provenance (model, version, digest), confidence per item, or a typed failure. The service rejects unknown models, external URLs and unit mismatches before doing work (C3). It holds no database credentials.

## CPU notes (for production, later)

Benchmarks on a 4-core laptop CPU (Intel i5-1135G7, ONNX Runtime 1.32, OpenVINO 2026.4, 25 November 2026): static int8 helped convolution models 2 to 8 times; dynamic int8 made SegFormer 4 times slower. Set threads to physical cores, never hyperthreads. Contabo's AMD CPUs lack AVX-512, so re-measure there.
