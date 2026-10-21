# V4 remote pre-upload gate

The laptop is source-only. No V4 notebook, test, CLI command, model download
or training job may run on its CPU/GPU.

Before a notebook is uploaded to Kaggle, the source must pass the static
preflight contract:

```text
python3 scripts/v4_notebook_preflight.py \
  --notebook-dir notebooks/kaggle/v4
```

That command is a source validator, not an end-to-end runtime proof. It checks
JSON structure, Python syntax, clean execution state, required package entry
points, required environment variables and forbidden network/credential
patterns. It never executes a cell.

The first remote run must be a private CPU audit with the attached immutable
package, configuration and dataset version. It must produce a verified audit
report and manifest before a GPU notebook is prepared. The next remote gates
are:

1. private CPU audit and manifest/hash verification;
2. private GPU smoke using a tiny stand-in model and one real input tile;
3. DINOv3 ViT-L profile and feature extraction on the authorized split;
4. gated DINOv3 7B teacher profile only if the actual device fits;
5. training, evaluation and bundle retrieval only after the earlier gates pass.

An uploaded notebook is not considered successful because Kaggle accepts it.
The gate is complete only when the exact version finishes and its outputs are
downloaded and verified locally by hash and contract. Unknown session state is
inspected before retrying; a failed run receives a new attempt identity.

Current state: the private xBD CPU audit (kernel version 4) and the private GPU
smoke (kernel version 1) have completed successfully and their JSON outputs were
retrieved and hash-verified. The next gate is a real DINOv3 ViT-L profile on the
authorized Kaggle GPU. It requires a Kaggle Secret containing the Hugging Face
access token for the gated satellite checkpoint. Tier-3 and specialist datasets
are still separate acquisition and annotation gates; they are not silently
treated as present because xBD passed.

The complete source inventory and multi-task mixing policy are recorded in
`configs/v4/dataset_registry.yaml` and `docs/v4_all_dataset_training_policy.md`.
