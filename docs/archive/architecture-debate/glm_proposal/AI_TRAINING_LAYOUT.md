# AI training workspace layout

*Draft blueprint for `ai/training/`. It refines the owner's idea of `kaggle/<feature-name>/v1, v2, v3`: what goes into each version folder, how a version is promoted, where weights live, and how Kaggle and Colab notebooks stay in step with the repository.*

## 1. Principles

1. **One feature, one folder. One version, one sub-folder.** A version folder is a complete, reproducible description of one model version: code, configuration, data, results and card.
2. **Scripts are the source of truth. Notebooks are thin wrappers.** AI coding agents and code review work well on `.py` files and badly on notebook JSON. A notebook exists only so that a hosted GPU can run the scripts.
3. **A version with results is frozen.** A new idea is a new version. Nothing is rerun "in place" and overwritten.
4. **Weights and data never enter Git.** Git holds the code, the configuration, the numbers and the checksums.
5. **Every number in a report can be traced** to a version folder, a dataset version and a commit.

## 2. Why `ai/training/` instead of a top-level `kaggle/`

The owner's structure is kept exactly: `<feature>/v1, v2, v3`. Two changes are proposed, both about the name and the place:

- **Place it under `ai/`, together with serving.** The whole AI side then lives in one top-level folder, and the step from training to serving is a move within `ai/`. The software side (`backend/`, `frontend/`, `database/`, `contracts/`) stays separate.
- **Call the folder `training`, not `kaggle`.** The same notebooks may run on Colab or on a workstation. A folder named after one provider misleads an agent looking for "where do I put a Colab notebook".

If the team prefers the literal name, a top-level `kaggle/` works with everything below unchanged. The content matters more than the name.

## 3. Layout

```
ai/training/
├── README.md                     How the workspace works. Short. Points to this document.
├── LEDGER.md                     One table of every version of every feature and its status.
├── _template/                    Copied to start a new version. Never edited as a version.
├── _helpers/                     Scripts that start a version, push it, and import its results.
├── damage-assessment/            One folder per feature.
│   ├── README.md                 The feature: problem, datasets, metric, what the versions tried.
│   ├── explore/                  Exploration notebooks that belong to the feature, not to a version.
│   ├── v1/
│   ├── v2/
│   └── v3/
├── hazard-segmentation/
│   ├── README.md
│   └── v1/
├── person-detection/
│   ├── README.md
│   └── v1/
└── image-embedding/
    ├── README.md
    └── v1/
```

A **feature** is what the product needs: "damage-assessment" covers building footprints, damage grade and change detection because those models are trained and evaluated together on the same data. A **version** is one trained candidate for that feature. Several models (building segmentation, damage classification) can live in one version if they are always trained and shipped together.

## 4. What goes into a version folder

| File | Purpose | Written by | May be edited after results exist |
| --- | --- | --- | --- |
| `README.md` | The hypothesis of this version, what changed from the previous one, the result in a few lines, the status | The author of the version | Status line only |
| `config.yaml` | The complete training configuration: model, data, hyperparameters, seed, export settings. No hidden defaults | The author | No |
| `dataset.yaml` | Which datasets and which **versions**, with checksums, and the split definitions | The author | No |
| `train.py` | Trains the model. Imports the shared library; contains no library code | The author | Bug fixes only, recorded in `README.md` |
| `evaluate.py` | Produces `metrics.json` on the fixed evaluation split | The author | Bug fixes only |
| `export.py` | Exports the runtime artifact for ONNX Runtime or OpenVINO, quantises it to int8 where that helps, and checks accuracy and latency against the original | The author | Bug fixes only |
| `notebooks/train.ipynb`, `notebooks/evaluate.ipynb` | Thin wrappers that run on a hosted GPU | Generated from the scripts | Never by hand |
| `kernel-metadata.json` | Identity and data sources of the Kaggle kernel | Generated | Never by hand |
| `metrics.json` | The evaluation results, machine-readable, with the commit, dataset versions and seed | `evaluate.py` | Never |
| `latency.json` | Inference latency on CPU, measured on a named reference machine | `export.py` | Never |
| `MODEL_CARD.md` | What the model does, on what data, with which limits | The author, from the template | Clarifications only |
| `weights.yaml` | Where the weights are and their SHA-256. The file itself is elsewhere | `export.py` | Never |
| `eval/` | Small result files: per-class table, confusion matrix, a few named failure cases | `evaluate.py` | Never |

Everything in the table except the weights is committed. The model card template is written in Milestone 4 with the headings that `DOCUMENTATION_SET.md` §5 checks.

## 5. Notebooks stay thin

The committed notebook for a version does four things: install the pinned dependencies, clone the repository at a pinned commit, set the paths from `config.yaml`, and call `train.py`. Everything else is in the scripts.

Notebooks are produced from the scripts with Jupytext [B33], which converts a Python file in the "percent" format to a notebook. A check in CI regenerates them and fails if the committed notebook differs. An agent therefore never edits a notebook; it edits the script.

Notebook outputs are stripped before commit, so no printed paths, tokens or large images enter the repository.

## 6. The ledger

`ai/training/LEDGER.md` is the first file to read to learn the state of the AI side. One row per version:

| Feature | Version | Status | Primary metric | Against active | Commit | Weights | Serving image | Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| damage-assessment | v3 | active | (from `metrics.json`) | — | … | sha256… | …-v3-… | … |
| damage-assessment | v4 | candidate | … | +0.4 | … | … | not built | … |
| hazard-segmentation | v1 | evaluated | … | not comparable | … | … | … | … |

Status values: `planned`, `running`, `evaluated`, `candidate`, `active`, `retired`, `rejected`. Only one version of a feature is `active`. The ledger is generated from the version folders and the registry by `make ledger`, so it cannot disagree with them.

## 7. Where weights, datasets and artifacts live

| Artifact | Where | Pinned by | Why |
| --- | --- | --- | --- |
| Code, configuration, metrics, model card | Git | The commit | Reviewed and diffable |
| Trained weights | A GitHub release attached to the tag `model-<feature>-v<N>` | SHA-256 in `weights.yaml` | Each file in a release must be under 2 GiB [B34]; the asset is immutable and public to anyone who can read the repository |
| A copy on the training side | Kaggle Models or a versioned Kaggle dataset [B30] | The version number | Fast to reach from a notebook |
| Exported runtime file (`.onnx`, quantised) | Baked into the serving image at build time | The image digest | The server never downloads a model at start-up |
| Datasets | Kaggle Datasets, versioned [B30], or object storage with a manifest | `dataset.yaml`: version and checksum | Reproducible; nothing large in Git |
| The evidence bundle for the demo | Object storage on the server, or a release asset for distribution | `scenarios/<name>/manifest.yaml` | See `AI_PIPELINE.md` §10 |
| Evaluation output in bulk (images, masks) | Object storage, temporary | Not kept | Only the small files in `eval/` are kept |

## 8. How a notebook on Kaggle stays in step with the repository

The repository is the truth. The hosted notebook is a place where the truth is executed.

```bash
make training-new FEATURE=damage-assessment         # creates v(N+1) from _template on a new branch
make kaggle-push   FEATURE=damage-assessment VERSION=4   # generates notebooks + metadata, pushes, starts the run
make kaggle-pull   FEATURE=damage-assessment VERSION=4   # downloads metrics and logs, opens a results branch
```

What each step does:

1. **`training-new`** copies `_template/`, numbers the version, writes the branch name into `README.md`.
2. **`kaggle-push`** regenerates the notebooks from the scripts, writes `kernel-metadata.json` (the kernel id, the code file, the language and the data sources, as the Kaggle CLI documents them [B30]) and runs `kaggle kernels push`. The CLI documentation describes this as pushing the code and metadata and then running the kernel [B30].
3. **The notebook** clones the repository at the commit recorded in its metadata, runs `train.py`, `evaluate.py` and `export.py`, writes `metrics.json`, `latency.json` and the weights to the kernel output, and uploads the weights to the model store named in `config.yaml`.
4. **`kaggle-pull`** downloads the outputs, places `metrics.json`, `latency.json`, `weights.yaml` and `eval/` into the version folder, refreshes the ledger, and prints the command that opens the pull request.

On Colab the same notebooks open straight from GitHub [B32]. Results come back with `make results-import FEATURE=… VERSION=… PATH=<folder>`.

## 9. Datasets and splits

- `dataset.yaml` names a dataset by owner, slug and **version number**, or by an object-storage prefix and a manifest checksum. "Latest" is never accepted.
- Preprocessed data is itself a versioned dataset. Preprocessing runs once; training runs read it.
- The split definition is part of `dataset.yaml`. For damage assessment the split must keep all images of one disaster event on one side, so that the evaluation measures performance on an event the model has never seen. The current configuration files already name an event-aware split file, so the practice exists; the version folder makes it explicit.
- The calibration set used for int8 quantisation is named separately and is taken from the training split, never from the evaluation split.

## 10. From a version folder to production

The full path is in `AI_PIPELINE.md`. In summary: a version becomes a `candidate` when its evaluation passes the gates, becomes `active` when the registry file is changed in a reviewed pull request, and is replaced, never overwritten. Rolling back is reverting the registry file.

## 11. What happens to the notebooks that exist today

The current `notebooks/` folder holds real research history: 7 numbered notebooks and 34 Kaggle notebooks whose names already carry a version prefix (`rv_`, `rv2_`, `rv3_`). That history should not be lost. This is a recommendation by file name; whoever ran the experiments confirms it.

| Today | Target | Reason |
| --- | --- | --- |
| `notebooks/kaggle/rv_train_*`, `rv_xbd_preprocess`, `rv_pipeline_smoke`, `rv_tar_probe` | `ai/training/damage-assessment/v1/` | First-generation runs |
| `notebooks/kaggle/rv2_*` | `ai/training/damage-assessment/v2/` | Second-generation runs, including the event map and the joint evaluation |
| `notebooks/kaggle/rv3_*` | `ai/training/damage-assessment/v3/` | Third-generation runs |
| `notebooks/kaggle/rv_floodnet_*` | `ai/training/hazard-segmentation/v1/` | Flood and road segmentation |
| `notebooks/03_…` to `06_…` (training baselines) | `ai/training/damage-assessment/explore/` | Baseline experiments that predate versioning |
| `notebooks/07_floodnet_segmentation.ipynb` | `ai/training/hazard-segmentation/explore/` | Same |
| `notebooks/01_…`, `02_…` (data exploration and preprocessing checks) | `ai/datasets/xbd/` | They describe a dataset, not a model |
| `scripts/train_*.py`, `scripts/prepare_*.py` | The matching version folders, and shared parts into `ai/libs/modelkit/` | They are the scripts behind the notebooks |
| `configs/*.yaml` | The matching version folders as `config.yaml` | They are the first configurations |
| `docs/model_cards.md` | Split into the `MODEL_CARD.md` of the matching versions | It is already a set of model cards |

The old notebooks keep their names as `explore/` material or are copied into the version folders as `legacy/`. Their cells are not rewritten.

## 12. GPU budget

Training does not happen on the server. It happens on free hosted GPUs. The Kaggle account used for this project has a weekly GPU quota of 108,000 seconds, which is 30 hours, reported by the Kaggle API on 2026-11-25 with a reset on 2026-11-28. Treat that as the budget per account.

How to stay inside it:

1. **Smoke first.** Every version runs on a tiny subset for a few minutes before a full run.
2. **Preprocess once.** Preprocessing is a versioned dataset, not a step in every training run.
3. **Cap the run.** `config.yaml` sets a maximum time and a maximum number of epochs. The best checkpoint is saved continuously.
4. **Measure CPU latency off-host.** `export.py` measures latency on a named reference machine and records it in `latency.json`, together with the processor and its instruction-set flags. The server's own numbers come from `make bench` after deployment, and only those count: the Contabo host has AVX2 but no AVX-512 or VNNI, so an int8 gain measured on a laptop does not transfer (`../cpu_demo_feasibility.md` §2).

## 13. Rules for AI coding agents in this folder

- Never commit a weights file, a dataset, a cache or a notebook output.
- Never edit `metrics.json`, `latency.json`, `weights.yaml` or anything in `eval/` by hand.
- Never change `config.yaml`, `dataset.yaml` or the scripts of a version that already has `metrics.json`. Create a new version.
- Never edit a notebook. Edit the script and regenerate.
- Always start a version from `_template/`.
- Always fill in every section of the model card, including the limits. An honest limit is worth more than a hidden one.
- Never put an access token in a notebook or a configuration file. Kaggle credentials come from the environment, and `kaggle.json` is ignored by Git.

## 14. Open points

- The mapping of the existing notebooks (§11) needs confirmation from the experiments' author.
- The per-file size limit for `eval/` and the number of failure examples to keep are set in Milestone 0.
- Whether weights are also mirrored to a model store other than release assets is a convenience decision, not an architectural one.
