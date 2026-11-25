# Building damage v1: baselines

First baselines on xBD: building segmentation (U-Net ResNet34), 6-channel damage segmentation (U-Net EfficientNet-B3), a DINOv2 damage classifier and Siamese change detection, plus preprocessing and smoke notebooks. The `0N_` notebooks are the local versions; the `rv_` notebooks are the Kaggle runs (E1 to E4). `rv_pipeline_smoke` smoke-tests all five v1 models, the FloodNet one included.

| Notebook | Title |
|---|---|
| `01_xbd_data_exploration.ipynb` | 01 - xBD Dataset Exploration |
| `02_xbd_preprocessing_visual_checks.ipynb` | 02 - xBD Preprocessing Visual Checks |
| `03_train_building_segmentation_baseline.ipynb` | 03 - Train Building Segmentation Baseline (U-Net ResNet34) |
| `04_train_damage_segmentation_baseline.ipynb` | 04 - Train Damage Segmentation Baseline (6-Channel U-Net EfficientNet-B3) |
| `05_train_damage_classifier_dinov2.ipynb` | 05 - Train Damage Classifier with DINOv2 |
| `06_change_detection_baseline.ipynb` | 06 - Change Detection Baseline (Siamese U-Net ResNet34) |
| `rv_pipeline_smoke.ipynb` | RESCA - CPU pipeline smoke (synthetic, all 5 models) |
| `rv_tar_probe.ipynb` | RESCA - tar mount probe (real data, CPU) |
| `rv_train_building_seg.ipynb` | RESCA - E1 building segmentation (U-Net RN34) |
| `rv_train_change_detection.ipynb` | RESCA - E3 change detection (Siamese U-Net) |
| `rv_train_damage_classifier_dinov2.ipynb` | RESCA - E4 damage classifier (DINOv2) |
| `rv_train_damage_seg.ipynb` | RESCA - E2 damage segmentation (6-ch EffNet-B3 U-Net) |
| `rv_xbd_preprocess.ipynb` | RESCA - xBD preprocessing -> single tar |

Results are recorded in each notebook's Kaggle run; none are copied here until they are re-verified.
