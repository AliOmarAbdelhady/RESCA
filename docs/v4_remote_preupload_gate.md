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

Current state: the private xBD CPU audit (kernel version 4), private GPU smoke
(kernel version 1), and real DINOv3 ViT-L profile (kernel version 5) have
completed successfully. The ViT-L report was retrieved and hash-verified on a
Tesla T4 using a real 512×512 xBD pair; it produced `x_norm_patchtokens` with
shape `[1, 1024, 1024]`. The failed profile attempts were corrected by adding
the repository root to `sys.path` before importing `hubconf.py` and by using
the repository's actual `dinov3_vitl16` entry point with the local SAT-493M
checkpoint path.

The 7B teacher profile is now a separate memory/source gate. The approved
SAT-493M model has no published Kaggle model variation, so the first profile
completed cleanly with an explicit `BLOCKED_MODEL_ARTIFACT_MISSING` report
instead of attempting a blind load. A published 26.86 GB LVD1689M 7B
Transformers variation was then attached only as a size proxy; its identity
was not substituted for SAT-493M. The proxy run completed cleanly with all six
shards mounted: the Tesla T4 had 15.5 GiB total memory, while the conservative
runtime projection was 23.2 GB, so `load_attempted` was false and the report
status was `PROFILED_INSUFFICIENT_MEMORY`. The next executable gate requires
an A100-class or larger GPU, or a separately validated compression/offload
experiment. Tier-3 and specialist datasets remain separate acquisition and
annotation gates; they are not silently treated as present because xBD passed.

The complete source inventory and multi-task mixing policy are recorded in
`configs/v4/dataset_registry.yaml` and `docs/v4_all_dataset_training_policy.md`.
