# Building damage v3: SE-ResNeXt50 joint model

Official xView2 rescoring of the v2 joint model and a joint SE-ResNeXt50 run with EMA, SWA and a class sampler.

| Notebook | Title |
|---|---|
| `rv3_rescore.ipynb` | RV3 official xView2 rescore of joint_damage_full (CPU, zero GPU quota) |
| `rv3_smoke.ipynb` | RV3 CPU smoke: rescore + SERX50 train (EMA/SWA/sampler) + official eval |
| `rv3_train_joint_serox50.ipynb` | RV3 joint damage SE-ResNeXt50 (EMA+SWA+sampler, 608px, adaptive cosine) |

Results are recorded in each notebook's Kaggle run; none are copied here until they are re-verified.
