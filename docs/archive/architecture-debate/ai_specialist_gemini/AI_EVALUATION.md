# RescueVision — AI Evaluation, Gates, Domain Shift & Honest Limits (`AI_EVALUATION.md`)

**Author:** AI Systems Specialist E (Gemini 4 Hydrogen)
**Date:** 2026-11-25
**Rule of Scientific Honesty:** No benchmark number is invented here. Current `docs/experiments.md` experiments are `Pending`, and `01_reference_data.sql` contains unverified active rows. Every numerical threshold below labeled **Target Gate** is a proposed engineering acceptance threshold to validate empirically during Phase 1–2—never a claimed measurement.

---

## 1. Datasets Inventory, Roles & Known Gaps

| Task | Dataset | Role in RescueVision | Documented Scale / Scope | Known Domain Gaps & Mitigation |
|---|---|---|---|---|
| **F1 Building Damage (Pre/Post)** | **[xBD / xView2](https://arxiv.org/abs/1911.09296)** | Primary pre/post training, validation & frozen test benchmark | 850,736 building polygons across 45,362 km² and 19 disasters (15 countries) | Satellite nadir (`~0.3–0.8 m/px`), severe class imbalance ("destroyed" & "minor" rare). Mitigate via `splits_event_aware.csv`, focal+Dice+Lovasz loss, and temperature+conformal calibration. |
| **F1 Multimodal / VHR Damage** | **[BRIGHT](https://arxiv.org/abs/2501.06019)** ([GitHub](https://github.com/ChenHongruixuan/BRIGHT)) | Cross-sensor generalization & multimodal benchmark | Global VHR optical + SAR disaster building damage pairs | Optical+SAR fusion is Phase 3 research; optical subset tests cross-event generalization beyond xBD. |
| **F1/F2 Post-Only UAV Scene** | **[RescueNet](https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation)** ([arXiv:2202.12361](https://arxiv.org/abs/2202.12361)) | Post-only building damage + clear/blocked roads + debris | 4,494 high-res UAV images (DJI Mavic Pro, Hurricane Michael) | Single hurricane event & US coastal architecture. Combine with `FloodNet` and local Cairo test imagery. |
| **F1/F2 Oblique Aerial PDA** | **[LADI v2](https://arxiv.org/abs/2406.02780)** ([HF Dataset](https://huggingface.co/datasets/MITLL/LADI-v2-dataset)) | Low-altitude oblique multi-label FEMA PDA evaluation | Multi-event Civil Air Patrol oblique disaster imagery | Image-level multi-label rather than pixel masks; ideal for `AI_POST_ONLY` linear-probe triage & oblique stress testing. |
| **F2 Flood & Road Blockage** | **[FloodNet](https://arxiv.org/abs/2012.02951)** | Flooded vs dry road/building UAV semantic segmentation | High-res post-Hurricane Harvey UAV imagery (10 classes) | Single hurricane in Texas; urban Cairo flash floods differ in asphalt/sand color and roof style. |
| **F2 Pavement Distress (Optional)** | **[RDD2022](https://github.com/sekilab/RoadDamageDetector)** | Optional pretraining for road-surface damage | 47,000+ multi-country road images | Tracks cracks/potholes rather than disaster rubble/blockage; secondary to `RescueNet` passability labels. |
| **F3 Aerial SAR Persons (Terrain)** | **SARD** ([Kaggle/ICPRAM 2024](https://www.scitepress.org/Link.aspx?doi=10.5220/0012388200003654) / [Research Plan](../graduation_project_research_plan.md)) & **HERIDAL** ([Accenture/AIR](https://github.com/Accenture/AIR)) | Primary aerial victim detection training/eval | ~1,981 images (SARD) + ~1,700 images (HERIDAL), tiny targets | Mostly wilderness/mountain/grass terrain, NOT collapsed Middle-Eastern urban rubble. |
| **F3 Flooded Persons (Water)** | **[SeaDronesSee](https://github.com/Ben93kie/SeaDronesSee)** ([arXiv:2105.01922](https://arxiv.org/abs/2105.01922)) | Swimmers/floaters/boats in water + MOT tracking | ~5,630 UAV images + MOT tracks | Open-sea maritime lighting differs from muddy urban floodwater; essential for flood-rescue recall. |
| **F3 Partial Occlusion (Thermal)** | **POP** ([PMC11840078](https://pmc.ncbi.nlm.nih.gov/articles/PMC11840078/)) & **[HIT-UAV](https://github.com/suojiashun/HIT-UAV)** | Thermal UAV occluded human detection (Stretch) | 8,768 labeled thermal images (POP; stable AP up to 70% occlusion) | Requires thermal camera (`spectral_band = 'THERMAL'`); only active when thermal payload is present. |
| **F3 Hard-Negative Pretrain** | **[VisDrone](https://github.com/VisDrone/VisDrone-Dataset)** ([arXiv:1804.07437](https://arxiv.org/abs/1804.07437)) | Backbone pretraining & urban clutter hard negatives | Large-scale urban UAV detection & tracking | Biased toward upright street pedestrians; never use alone for prone/collapsed SAR evaluation. |
| **F5 Fire & Smoke (Optional)** | **[D-Fire](https://github.com/AlimTleuliyev/wildfire-detection)** & **FLAME 2** | Fire/smoke bounding boxes triggering `FIRE_GAS_EXPLOSION` | 21,000 YOLO-format fire/smoke images (`D-Fire`) | Wildfire/prescribed burn imagery; urban smoke plumes may need local false-positive calibration against dust clouds. |
| **Local Target Validation** | **Team-Collected Local AOI (Cairo / Campus)** | Mandatory thesis domain-shift & geolocation test set | Controlled UAV/simulated survey with mannequins, road obstacles & GNSS-measured targets | Must be collected/annotated cleanly (zero training contamination) to prove geolocation $\rho$ calibration and Egypt-domain shift. |

---

## 2. Canonical Evaluation Metrics per Feature

1. **F1 · Building Damage Assessment (`building-damage`):**
   * **Primary Metric (Official Challenge Scorer Only):** [`DIUx-xView/xView2_scoring`](https://github.com/DIUx-xView/xView2_scoring) (`0.3 × localization_f1 + 0.7 × harmonic_mean(F1_no_damage, F1_minor, F1_major, F1_destroyed)`). **Ban approximate proxies** (`xview2_approx`) for final reporting.
   * **Per-Class Reporting:** Report all 4 damage F1s + confusion matrix (specifically watching `minor` vs `major`, the hardest boundary).
   * **Calibration & Uncertainty:**
     * **ECE (Expected Calibration Error)** before and after Temperature Scaling ($T$).
     * **Conformal Empirical Coverage** ($1 - \alpha = 0.90$) and **Mean Set Size** ($|S(x)| \in [1, 4]$) via [`MAPIE`](https://github.com/scikit-learn-contrib/MAPIE).
2. **F2 · Flood & Road Condition (`flood-road-seg`):**
   * **Segmentation Quality:** mIoU and per-class IoU/F1 (`FLOOD_WATER`, `ROAD_CLEAR`, `ROAD_BLOCKED`).
   * **Safety-Critical Routing Metric:** **False-Safe Rate** — fraction of truly `ROAD_BLOCKED` or `FLOODED` pixels/segments predicted as `ROAD_CLEAR` (must be minimized via threshold tuning on `val` split).
3. **F3 · Aerial Person Detection (`person-detection`):**
   * **Detection:** `mAP@0.5`, `mAP@0.5:0.95` evaluated under **`SAHI`** (`640×640` slices, 20% overlap) on full-resolution UAV images (never downscaled 640px).
   * **Operational SAR Curve:** **Recall at a fixed False-Positives-Per-Image (FPPI) budget** (e.g., `Recall @ <= 1.0 FP/image` on `val`) so analysts are not flooded with rubble false alarms.
   * **Geolocation Accuracy & Uncertainty Coverage:** Mean, median, and 90th-percentile ground error (metres) against surveyed targets, plus **empirical radius coverage**: percentage of true targets falling within predicted `location_error_m` ($\rho$).
4. **F4 · Multi-Object Tracking (`person-tracking`):**
   * `MOTA`, `IDF1`, and **ID Switches (IDSW)** on `SeaDronesSee-MOT` and multi-frame drone clips; stationary-track precision (does a static rock falsely become a persistent `STATIONARY` track?).

---

## 3. Automated CI Evaluation Gates (`ci-ai-gate.yml`)

No model version in `kaggle/<feature>/vN/` can be promoted to `models/registry/` or `ai_models.is_active = true` unless the automated PR check passes:

| Gate | Automated Check | Target Acceptance Policy *(to be validated in Phase 1)* |
|---|---|---|
| **G1 · Split Integrity** | Verify `dataset_ref.json` `splits_event_aware.csv` SHA-256 matches canonical registry; zero event/disaster ID overlap across `train`/`val`/`test`. | 0% leakage (hard block) |
| **G2 · Official Metric Regression** | `metrics.json` on untouched frozen `test` split $\ge$ currently active model's primary metric (xView2 Score / `SAHI` Recall@1FPPI / False-Safe-bounded `ROAD_BLOCKED` F1). | $\ge$ current production baseline |
| **G3 · Calibration & Conformal Gate** | Verify post-scaling `ece_after <= 0.05` (**Target Gate**) and conformal validation coverage within $[0.87, 0.93]$ for nominal $0.90$. | Pass calibration check |
| **G4 · ONNX Numerical Parity** | Run `export.py` parity test on deterministic seed + golden chips across PyTorch vs ONNX Runtime. | `max_abs_diff < 1e-4` and class-flip rate `< 0.1%` |
| **G5 · Golden GeoTIFF Smoke & Latency** | Run ONNX container on 2 fixed GeoTIFF chips (satellite + UAV) and verify valid GeoJSON/raster bounds + CPU latency budget. | Valid schema + non-empty outputs within timeout |
| **G6 · Model Card & Provenance** | Verify `model_card.md` non-empty, license recorded (`Apache-2.0` / `MIT` / explicit copyleft waiver), and zero weight binaries (`*.pt`/`*.onnx`) committed to Git. | Hard block on weights in Git |

---

## 4. Domain-Shift & Runtime Drift Checks

Because xBD (global satellite) and FloodNet/SARD (US/European UAV) differ sharply from **Cairo / MENA urban morphology and custom drone sensors**:

1. **Offline Generalization Protocol (Mandatory in Thesis):**
   * **Leave-One-Disaster-Type-Out / Whole-Event Holdout:** Report xBD test scores stratified by disaster type (earthquake vs flood vs fire) and unseen geography.
   * **GSD & Resolution Sensitivity Curve:** Evaluate `joint_damage` and `person_sar` across synthetic downsampling (`0.05`, `0.15`, `0.30`, `0.60`, `1.00 m/px`) to empirically determine the exact `gsd_cm` cutoffs enforced in `ai_models` metadata (`FR-PD-06`).
   * **Local Field-Proxy Test Set:** Run the frozen models on a small local UAV/orthomosaic survey (mannequins + obstacles + GCPs) and report the real **sim/benchmark-to-local drop** honestly.
2. **Online Runtime Drift Detection (`ai-embed` + `geo-worker`):**
   * Compute the centroid and covariance (or k-NN cosine distance bank) of `768-d` `DINOv3`/`DINOv2` embeddings over the xBD/RescueNet validation manifold during export.
   * At runtime, every incoming `capture_session` tile receives an **OOD distance score** and predictive **Shannon entropy**. If $> 30\%$ of tiles in a session exceed the 95th-percentile training-manifold distance (e.g., heavy smoke, night thermal-miss, or unfamiliar roof architecture), `geo-worker` attaches an explicit `OOD_SHIFT_WARNING` banner to `processing_jobs` and automatically routes `building_assessments` to human review.

---

## 5. Honest Limits (To State Explicitly in Reports & UI)

1. **No Under-Rubble Detection:** Optical/thermal UAV AI detects *visible or partially exposed* persons only. Buried victims require physical acoustic/UWB radar/canine teams.
2. **Post-Only Triage Has Lower Fidelity:** Without a pre-event image, `AI_POST_ONLY` cannot reliably distinguish newly collapsed concrete from pre-existing ruins or construction sites; UI badges and wider cost ranges must reflect this.
3. **Geolocation Error Grows With Oblique Angle & Missing DSM:** Without a `NodeODM` DSM and calibrated camera intrinsics/gimbal angles, single-frame pixel-to-GPS can drift by many metres on sloped roofs or multi-story buildings.
4. **SARD/HERIDAL vs Urban Rubble Gap:** Public SAR datasets have few thousand images mostly in open terrain; urban post-earthquake rubble recall will initially be noisy, which is why **multi-view persistence + `D-07` human confirmation** are non-negotiable.
5. **Restorations Costs Are Indicative Ranges, Not Structural Engineering:** HAZUS repair ratios × regional rates provide rapid prioritization budgets, not insurance or contractor quotes (`docs/limitations_and_ethics.md`).
