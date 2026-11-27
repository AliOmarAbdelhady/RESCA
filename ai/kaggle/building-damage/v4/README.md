# Building damage v4: DINOv3 research

DINOv3-based research line with audited xBD labels and splits. Unlike v1 to v3, this version holds its own code: `src/rescuevision_ai/v4` (package), `tests/v4`, `configs/v4`, `scripts/` (Kaggle staging) and `notes/` (plan, experiment registry, policies). Notebooks marked *DO NOT RUN FOR SUPERVISED TRAINING* say why in their first cell.

Run the tests from this folder:

```
PYTHONPATH=src:. python -m pytest tests/v4 -q
```

They need PyTorch; a GPU is fine (see [docs/AI.md](../../../../docs/AI.md)). Known: `test_notebook_wrappers` fails because its list of notebooks predates `00_xbd_label_schema_diagnostic`, `06_xbd_grouped_manifest_audit` and `01_reference_evaluation`.

This code is not linted by CI yet (`ai/kaggle` is the experiment area). Parts that prove themselves move into `ai/src/rescuevision_ai` and must then pass every gate.

| Notebook | Title |
|---|---|
| `00_data_and_split_audit.ipynb` | V4 CPU data and split audit |
| `00_gpu_smoke.ipynb` | V4 remote GPU smoke |
| `00_xbd_label_schema_diagnostic.ipynb` | xBD label schema and old parser diagnostic |
| `01_dinov3_teacher_profile.ipynb` | V4 DINOv3 7B teacher memory profile |
| `01_dinov3_vitl_profile.ipynb` | V4 DINOv3 ViT-L SAT-493M profile |
| `01_reference_evaluation.ipynb` | V4 reference evaluation |
| `02_dinov3_d0_smoke.ipynb` | V4 DINOv3 ViT-L D0 remote smoke (do not run for supervised training) |
| `02_specialist_manifest_audit.ipynb` | V4 specialist manifest audit |
| `03_dinov3_d0_full_coverage.ipynb` | V4 DINOv3 ViT-L D0 full-coverage remote epoch (do not run for supervised training) |
| `03_final_bundle_verify.ipynb` | V4 final inference bundle verification |
| `04_dinov3_d0_resumable_smoke.ipynb` | V4 DINOv3 ViT-L resumable D0 smoke (do not run for supervised training) |
| `05_dinov3_d0_resumable_full.ipynb` | V4 DINOv3 ViT-L resumable multi-epoch training (do not run for supervised training) |
| `06_xbd_grouped_manifest_audit.ipynb` | xBD grouped manifest audit |

Results are recorded in each notebook's Kaggle run; none are copied here until they are re-verified.
