# Building damage v2: full xBD and joint model

Event-preserving full-xBD preprocessing, Unet++ EfficientNet-B4 building segmentation, longer change-detection runs and a joint building + damage Siamese model.

| Notebook | Title |
|---|---|
| `rv2_event_map_extract.ipynb` | RescueVision v2 - event split map extract from old tar |
| `rv2_joint_eval_rerun.ipynb` | RescueVision v2 - joint model eval rerun (hardened) |
| `rv2_preprocess_full.ipynb` | RescueVision v2 - FULL xBD preprocessing (JPEG pack, event-preserving splits) |
| `rv2_preprocess_native.ipynb` | RescueVision v2 - xBD native preprocessing -> single tar |
| `rv2_smoke.ipynb` | RescueVision v2 - CPU smoke (all 3 new models, synthetic native data) |
| `rv2_train_building_v2.ipynb` | RescueVision v2 - building segmentation (Unet++ EffB4, 608px) |
| `rv2_train_change_full.ipynb` | RescueVision v2 - change detection on FULL xBD (60 epochs) |
| `rv2_train_change_v2.ipynb` | RescueVision v2 - change detection (256px crops, long train) |
| `rv2_train_joint_damage.ipynb` | RescueVision v2 - joint building+damage siamese (5-channel, 608px) |
| `rv2_train_joint_full.ipynb` | RescueVision v2 - joint siamese on FULL xBD (18 epochs, 9h budget) |

Results are recorded in each notebook's Kaggle run; none are copied here until they are re-verified.
