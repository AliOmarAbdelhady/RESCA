# V4 all-dataset training policy

The project will train on all datasets that are successfully acquired,
licensed, audited and represented in [the dataset registry](../configs/v4/dataset_registry.yaml).
“All datasets” does not mean concatenating incompatible labels into one
softmax target. It means a shared representation with task-specific adapters,
heads, validity masks and evaluation metrics.

The remote training sequence is:

1. Acquire each source in an authenticated Kaggle/Colab runtime and record the
   exact owner, version, files, license and SHA-256 values.
2. Audit every source before training: image readability, annotation counts,
   source label map, duplicate structure/capture groups, cross-dataset overlap,
   and official split boundaries.
3. Preserve official xBD train/validation/test identities. Use xBD and tier-3
   only through the paired overhead adapter; never use the official xBD test
   images for supervised fitting or threshold selection.
4. Use DamageTriage-Bench and RescueNet through post-only heads, CUBIT,
   dacl10k, OmniCrack30k and CODEBRIM through defect heads, BRIGHT through a
   separate RGB/SAR branch, 3DAeroRelief through a separate 3D/point branch,
   SpaceNet 8 and FloodNet through context branches, and LADI through image
   context. Source labels remain source labels.
5. Mix all compatible training partitions with an explicit task sampler. Each
   batch carries a task identifier; only the corresponding head and valid loss
   terms receive gradients. Missing annotations are masked, never converted to
   negatives.
6. Evaluate every dataset on its own untouched test split and report per-class,
   per-event and per-source metrics. The official xView2 combined F1 remains the
   primary paired benchmark; defect, post-only, context and 3D metrics are
   separate.
7. After final benchmark evaluation is frozen, optionally run a production
   retraining pass using train plus validation data from each source. That pass
   produces deployable weights but must not replace the untouched benchmark
   score.

Dataset access, permission, missing labels, incompatible modalities or absent
expert annotation are blocking conditions for that source. The pipeline must
record the source as blocked rather than silently dropping it or fabricating
targets. No stage in this policy runs on the laptop CPU/GPU.
