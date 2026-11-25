# RescueVision — Deep AI Systems Architecture Report (`ai_specialist_gemini.md`)

**Author:** AI Systems Specialist E (Gemini 4 Hydrogen)
**Date:** 2026-11-25
**Output Blueprint Folder:** [`docs/architecture/debate/ai_specialist_gemini/`](./ai_specialist_gemini/)
**Status:** Independent deep-dive AI architecture & critical challenge to existing platform proposals (pre-implementation phase).

---

## Executive Summary

1. **The Core Diagnosis:** RescueVision's 56-table PostgreSQL 18 + PostGIS + pgRouting + pgvector schema (`database/schema/`) is rigorous, and its latest Kaggle training work (`notebooks/kaggle/rv3_train_joint_serox50.ipynb` implementing `SiameseUNetSE`) shows genuine engineering maturity. However, the project's AI layer suffers from **severe blueprint fragmentation**: `database/seed/01_reference_data.sql` activates 9 unbuilt models with `NULL` metrics, `configs/` and `docs/model_cards.md` assume a redundant 4-stage F1 cascade, zero code or experiments exist for **F3 (person detection)**, **F4 (tracking)**, or **F5 (fire/smoke)**, and existing architecture proposals either under-specify ML serving (raw FastAPI) or over-engineer it for a 6-student team on a GPU-less Contabo VPS (NVIDIA Triton `.plan` + MediaMTX KLV + 3D Gaussian Splatting).
2. **Consolidated 4-Family + 1 Photogrammetry Architecture:** Replace the 9-model sprawl with **3 stateless inference containers + 1 optional photogrammetry worker**:
   * **`ai-damage`:** `SiameseUNetSE` (`se_resnext50_32x4d`, benchmarked vs [`ChangeOS`](https://github.com/Z-Zheng/ChangeOS) / [`MambaBDA`](https://github.com/innopam/MambaCD)) for joint building localization & 4-class damage (`AI_BEFORE_AFTER`), plus a post-only linear/MLP triage head (`AI_POST_ONLY`).
   * **`ai-vision-sar`:** Permissively licensed **`D-FINE-S`** ([`Peterande/D-FINE`](https://github.com/Peterande/D-FINE), Apache-2.0) or **`RF-DETR-S`** ([`roboflow/rf-detr`](https://github.com/roboflow/rf-detr), Apache-2.0) wrapped in **[`SAHI`](https://github.com/obss/sahi)** tiling for visible/partially-visible persons (`F3`), paired with **`SegFormer-B2`** trained on [`FloodNet`](https://arxiv.org/abs/2012.02951) + [`RescueNet`](https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation) for floodwater and road blockage (`F2`/`F5`). *(Person tracking via [`BoT-SORT`](https://github.com/NirAharon/BoT-SORT) runs on CPU inside the geospatial worker, not in a GPU container.)*
   * **`ai-embed`:** One frozen **`DINOv3 SAT-493M`** ([`facebookresearch/dinov3`](https://github.com/facebookresearch/dinov3), [`arXiv:2508.10104`](https://arxiv.org/abs/2508.10104)) / [`Clay v1.5`](https://github.com/Clay-foundation/model) (or `dinov2-base` baseline) 768-d encoder powering **three features at once**: post-only building triage, `pgvector` HNSW historical case search (`FR-RP-10`), and runtime out-of-distribution (OOD) drift detection.
   * **`nodeodm` (Optional Profile):** [`OpenDroneMap/NodeODM`](https://github.com/OpenDroneMap/NodeODM) for raw overlapping UAV photo stitching into Cloud-Optimized GeoTIFFs (`ORTHOMOSAIC`, `DSM`) and OGC 3D Tiles (`NASA-AMMOS/3DTilesRendererJS`).
3. **Four Genuinely Novel, Defensible Contributions:**
   * **Conformal Cost-Linked Triage (`MAPIE` + Temperature Scaling):** Calibrated logits feed split conformal prediction sets (`S(x)` at 90% coverage), ranking ambiguous multi-grade buildings to the front of the `D-07` human review queue and bounding `cost_estimates [cost_low, cost_high]`.
   * **Physics-Aware Aerial SAR Localization:** Enforces the `gsd_cm <= 5.0` physics gate (`FR-PD-06`), projects `SAHI` detections onto the `NodeODM` DSM (or Copernicus DEM) with GPS + gimbal angular error propagation into `person_detections.location_error_m`, and filters static rubble false positives via `BoT-SORT` Camera Motion Compensation + cross-view geo-clustering.
   * **AI-to-Rule-Engine Closed Safety Loop:** `SegFormer-B2` `FLOOD_WATER` polygons write `hazards` (`AI_DETECTED`) directly inside the transactional PostgreSQL hazard engine (`evaluate_hazard_rules()`), automatically firing `ELECTRIFIED_WATER` alerts and `pgRouting` re-routes while keeping human confirmation mandatory (`NFR-SF-02`).
   * **Contabo-Realistic CPU-First + Serverless Burst GPU Serving:** Every AI container runs **[`LitServe`](https://github.com/Lightning-AI/LitServe) + [`ONNX Runtime`](https://github.com/microsoft/onnxruntime)**—portable across Contabo CPU (`CPUExecutionProvider` / `OpenVINO`) for always-on fallback and bursted **[`Modal`](https://modal.com/docs/guide/tailscale) / [`RunPod`](https://www.runpod.io/)** GPUs (`CUDAExecutionProvider`) over **[`Tailscale`](https://tailscale.com/)** for heavy orthomosaic/SAHI jobs.
4. **Honest Boundaries:** RGB drone AI cannot see victims buried under intact rubble; post-only damage triage has higher false-positive risk than pre/post change detection; and all current models remain untrained/unvalidated until Phase 1–2 experiments pass `ci-ai-gate.yml` on frozen event-held-out splits and a local Cairo test AOI.

---

## 1. Blueprint Folder Contents

All detailed specifications, schemas, contracts, and checklists live in [`docs/architecture/debate/ai_specialist_gemini/`](./ai_specialist_gemini/):

| Document | Contents |
|---|---|
| [`AI_SYSTEM.md`](./ai_specialist_gemini/AI_SYSTEM.md) | Feature-by-feature target AI architecture (F1–F6), alternatives considered, inputs/outputs, conformal uncertainty, `D-07` human review, novel contributions, and phased AI roadmap. |
| [`AI_TRAINING_LAYOUT.md`](./ai_specialist_gemini/AI_TRAINING_LAYOUT.md) | Refined `kaggle/<feature-name>/v1, v2, v3...` + `rv_ai` package structure, exact per-version dossier files, weight storage policy (never in Git), Kaggle-to-GitHub sync, and 5-step promotion/rollback lifecycle. |
| [`AI_SERVING_AND_INTEGRATION.md`](./ai_specialist_gemini/AI_SERVING_AND_INTEGRATION.md) | `LitServe + ONNX Runtime` 3-container design, `Procrastinate` async queue vs sync REST contracts, `ai_models` SQL evidence constraint, and Contabo CPU-first + Tailscale Burst-GPU topology. |
| [`AI_EVALUATION.md`](./ai_specialist_gemini/AI_EVALUATION.md) | Verified dataset inventory & gaps, canonical metrics (`xView2_scoring`, `ECE`, `MAPIE`, `SAHI`, false-safe road rate), CI promotion gates, domain-shift/OOD checks, and honest limitations. |
| [`EDGE_AI.md`](./ai_specialist_gemini/EDGE_AI.md) | Server vs Expo phone vs field laptop split, `onnxruntime-react-native` vs ExecuTorch/LiteRT, Expo Dev Build constraints, `<50 KB` offline triage outbox, and staleness warnings. |
| [`AI_COPILOT.md`](./ai_specialist_gemini/AI_COPILOT.md) | Grounded Read-Only `PydanticAI` Commander Copilot over `rv_readonly`, zero raw SQL, `<untrusted_field_text>` injection defense, programmatic ID/number verifier, and DPA/vLLM options. |

---

## 2. Challenging the Other Proposals & Current Repo Artifacts

| Topic | What Others Propose (`platform-plan` / `gemini_proposal` / `redteam_gemini` / `redteam_glm`) | AI Specialist Critique & Challenge | Our Resolution |
|---|---|---|---|
| **Model Registry & Seed (`01_reference_data.sql`)** | `01_reference_data.sql` activates 9 models with `NULL` metrics/URIs; `configs/` defines separate `U-Net`, `Siamese U-Net`, `EfficientNet`, `DINOv2` stages. | **Fatal Provenance Gap:** Activating unbuilt models breaks `FR-IM-07`, while cascading 4 models for F1 wastes VRAM and compounds localization errors into damage errors. | Consolidate F1 into `SiameseUNetSE` (paired) + `DINOv3` linear probe (post-only), and add a DB `CHECK` blocking `is_active = true` without `weights_sha256`, `metrics`, and `status = 'VALIDATED'`. |
| **Serving Stack (`FastAPI` vs `LitServe` vs `Triton`)** | `platform-plan` uses bare FastAPI; `gemini_proposal` uses 4 LitServe GPU containers; `redteam_gemini` mandates NVIDIA Triton + TensorRT `.plan`; `redteam_glm` rejects LitServe for bare FastAPI + ONNX/OpenVINO. | **Triton `.plan` locks you to one GPU SM architecture** and adds C++ `config.pbtxt` complexity for a GPU-less Contabo VPS. Conversely, **bare FastAPI** throws away micro-batching across hundreds of building crops and `SAHI` slices. | **LitServe + ONNX Runtime** in 3 containers (`ai-damage`, `ai-vision-sar`, `ai-embed`): ~50 lines of FastAPI-compatible Python with automatic micro-batching, portable across Contabo CPU and bursted Modal/RunPod GPUs. |
| **Person Detector License & Pipeline (`F3`)** | `01_reference_data.sql` & `redteam_gemini` specify `YOLOv8s` (`ultralytics`); `redteam_glm` warns on AGPL-3.0 and suggests Apache-2.0 DETR/YOLOX. | **Both license & physics flaws:** `ultralytics` is `AGPL-3.0`, and standard single-frame `640px` inference drops tiny aerial victims while flat-earth GPS projection fails on oblique angles. | Mandate Apache-2.0 **`D-FINE-S`** / **`RF-DETR-S`** (COCO/custom weights) + **`SAHI`** slicing + `gsd_cm <= 5.0` gate + **DSM raycasting** + **`BoT-SORT`** CMC tracking on CPU. |
| **3D Reconstruction & Live Video (`F2`/`F3`)** | `redteam_gemini` puts **3D Gaussian Splatting (`opensplat`/`Spark`)** and **MediaMTX RTSP + SMPTE 336M KLV + NATS** in the core pipeline. | **Scope Creep Trap:** Zero overlapping raw KLV disaster video exists in the repo; 3DGS lacks metric DSMs for raycasting and consumes weeks of debugging. | Use **`NodeODM`** (optional `photogrammetry` profile) for metric `ORTHOMOSAIC` + `DSM` + `3D Tiles` (`3DTilesRendererJS`) on unified **MapLibre GL JS**. Keep 3DGS strictly as a single-building Phase 3 stretch demo. |
| **Foundation Embeddings (`pgvector`) & Copilot (`F6`)** | `redteam_glm` cuts `image_embeddings` (`pgvector`) and rejects database-tool copilots; `redteam_gemini` includes `Clay v1.5` + `PydanticAI` in core. | **Cutting `pgvector` wastes an already-built index** (`11_field_reports_audit.sql`) when one `DINOv3`/`DINOv2` forward pass gives us post-only triage + similarity search + OOD drift detection together. Conversely, putting a Copilot in Phase 1 MVP delays core vision. | Ship **`ai-embed`** (`DINOv3 SAT-493M` / `DINOv2`) in **Phase 2** for tri-task reuse (`AI_POST_ONLY` + `pgvector` + OOD), and ship the **Read-Only `PydanticAI` Copilot** in **Phase 3** with programmatic ID/number verification. |
| **Edge AI (`EDGE_AI.md`)** | `redteam_gemini` demands Jetson/GCS live RTSP edge inference; `redteam_glm` defers edge to a late spike. | **Phone-first beats Jetson-first:** Responders already carry Expo smartphones; they do not carry Jetson Orins in Phase 1. | Ship **Expo Dev Build offline photo triage** (`onnxruntime-react-native`, INT8 `<15 MB` `.onnx`, `<50 KB` WebP crop outbox) in **Phase 2**; defer field laptop GCS to Phase 3. |

---

## 3. Target AI Portfolio Mapped to `ai_models` (`database/schema/04_imagery_ai.sql`)

| `ai_models.name` | `task` Enum | Architecture | Datasets | Serving Container / Runtime | Novel Safeguard |
|---|---|---|---|---|---|
| `joint-damage` | `DAMAGE_CLASSIFICATION` *(handles loc+dmg)* | `SiameseUNetSE` (`se_resnext50_32x4d`, `608px`) vs `ChangeOS` | `xBD`, `BRIGHT` (optical), `RescueNet` | `ai-damage` (`LitServe` + ONNX Runtime) | Temperature Scaling (`ECE <= 0.05` target) + `MAPIE` 90% conformal sets driving `[cost_low, cost_high]` |
| `post-damage-probe` | `DAMAGE_CLASSIFICATION` *(method=`AI_POST_ONLY`)* | `DINOv3 SAT-493M` / `DINOv2-base` frozen + MLP | `RescueNet`, `LADI v2`, `xBD` post | `ai-embed` + `ai-damage` head | Explicit `AI_POST_ONLY` confidence penalty + wider conformal sets |
| `person-sar-hq` | `PERSON_DETECTION` | `D-FINE-S` or `RF-DETR-S` (Apache-2.0) + `SAHI` | `SARD`, `HERIDAL`, `SeaDronesSee` (+ `POP` thermal opt.) | `ai-vision-sar` (`LitServe` + ONNX Runtime) | `gsd_cm <= 5.0` gate + DSM raycast + angular error $\rho$ |
| `person-sar-edge` | `PERSON_DETECTION` *(edge)* | `YOLOX-Tiny` / `D-FINE-Nano` INT8 ONNX | Same (`416–640px`) | Expo mobile (`onnxruntime-react-native`) | Provisional badge + `<50 KB` crop outbox |
| `person-tracker` | `PERSON_TRACKING` | `BoT-SORT` (CMC) + Geo-circle clustering | `SeaDronesSee-MOT` + multi-view sequences | `geo-worker` (CPU Python library) | Multi-azimuth static false-positive suppression; `D-07` human verification |
| `flood-road-seg` | `HAZARD_SEGMENTATION` / `ROAD_CONDITION` | `SegFormer-B2` | `FloodNet` + `RescueNet` | `ai-vision-sar` (`LitServe` + ONNX Runtime) | False-safe road metric minimization; triggers `ELECTRIFIED_WATER` transactionally |
| `fire-smoke` *(Stretch)* | `FIRE_SMOKE_DETECTION` | `D-FINE-S` / `YOLOX-S` | `D-Fire` + `FLAME 2` | `ai-vision-sar` | Feeds `hazards` (`FIRE`) $\rightarrow$ `FIRE_GAS_EXPLOSION` rule |
| `eo-embedder` | `IMAGE_EMBEDDING` | `DINOv3 SAT-493M` / `DINOv2-base` (`768-d`) | `xBD` + historical incidents | `ai-embed` (`LitServe` + ONNX Runtime) | Powers `pgvector` HNSW search + OOD cosine drift alert |

---

## 4. Phased AI Delivery Roadmap & Team Split (6 Students, 1 Academic Year)

To survive a two-semester timeline where 3–4 teammates carry core engineering load (`redteam_glm.md` T1), isolate AI milestones cleanly from backend/frontend delivery so `core-api` and maps ship even while models iterate:

* **Phase 0 (Weeks 1–3) — AI Package & Hygiene:** Extract `rv_ai` into `ai/` from `rv3_train_joint_serox50.ipynb`, restructure into `kaggle/<feature>/vN/`, enforce the `ai_models` SQL evidence constraint (all 9 seed rows start `is_active = false`), and wire `ci-ai-gate.yml`.
* **Phase 1 — MVP Core AI (Weeks 4–12):**
  * Train/calibrate `kaggle/building-damage/v2` (`SiameseUNetSE` + TempScale + `MAPIE`) and verify official `xView2_scoring`.
  * Train `kaggle/flood-road-seg/v2` (`SegFormer-B2` on `FloodNet` + `RescueNet`) and wire `FLOOD_WATER` polygons into `evaluate_hazard_rules()`.
  * Train `kaggle/person-detection/v1` (`D-FINE-S` / `YOLOX-S` + `SAHI` on `SARD` + `HERIDAL` + `SeaDronesSee`).
  * Deploy the 3 `LitServe + ONNX Runtime` containers in CPU mode behind `Procrastinate` (`processing_jobs`) on Contabo.
* **Phase 2 — Mapping, Tracking, EO Core & Offline Edge (Weeks 13–20):**
  * Integrate `NodeODM` (`STITCH` $\rightarrow$ COG + DSM + 3D Tiles) + DSM collinearity raycasting + `BoT-SORT` CMC tracking.
  * Upgrade `ai-embed` to `DINOv3 SAT-493M` (or `Clay v1.5`), enabling `AI_POST_ONLY`, `pgvector` retrieval, and OOD drift banners.
  * Ship Expo Dev Build offline photo person-triage (`onnxruntime-react-native` + `op-sqlite` outbox).
* **Phase 3 — Burst GPU, Copilot & Stretch (Weeks 21–28):**
  * Enable **Tailscale + Modal/RunPod** burst GPU profile for fast thesis demos and large surveys.
  * Ship the **Read-Only Grounded `PydanticAI` Commander Copilot** (`AI_COPILOT.md`).
  * Collect & evaluate on the **local Cairo/campus UAV validation AOI** (mannequins, road obstacles, GCPs) for honest thesis defense numbers.
  * *Stretch only if ahead:* `D-Fire` smoke/fire model, `POP` thermal branch, and single-building 3D Gaussian Splat (`gsplat` + `Spark`).

---

## 5. Verified Research & Open-Source References

1. **Building Damage & Change Detection:**
   * Gupta et al., *xBD: A Dataset for Assessing Building Damage from Satellite Imagery* — [`arXiv:1911.09296`](https://arxiv.org/abs/1911.09296)
   * Official xView2 Evaluation Scorer — [`DIUx-xView/xView2_scoring`](https://github.com/DIUx-xView/xView2_scoring) · 1st Place Solution — [`DIUx-xView/xView2_first_place`](https://github.com/DIUx-xView/xView2_first_place)
   * Zheng et al., *ChangeOS: Building Damage Assessment via Deep Object-Based Semantic Change Detection* — [`Z-Zheng/ChangeOS`](https://github.com/Z-Zheng/ChangeOS)
   * Chen et al., *ChangeMamba / MambaBDA* — [`innopam/MambaCD`](https://github.com/innopam/MambaCD)
   * Microsoft Building Damage Assessment Toolkit — [`microsoft/building-damage-assessment`](https://github.com/microsoft/building-damage-assessment)
   * BRIGHT Multimodal VHR Damage Dataset — [`arXiv:2501.06019`](https://arxiv.org/abs/2501.06019) · [`ChenHongruixuan/BRIGHT`](https://github.com/ChenHongruixuan/BRIGHT)
   * Microsoft Global ML Building Footprints — [`microsoft/GlobalMLBuildingFootprints`](https://github.com/microsoft/GlobalMLBuildingFootprints)
2. **Foundation Models & Geospatial Segmentation:**
   * Siméoni et al., *DINOv3* (including `SAT-493M`) — [`arXiv:2508.10104`](https://arxiv.org/abs/2508.10104) · [`facebookresearch/dinov3`](https://github.com/facebookresearch/dinov3)
   * Clay Foundation Model — [`Clay-foundation/model`](https://github.com/Clay-foundation/model)
   * Prithvi-EO-2.0 — [`arXiv:2412.02732`](https://arxiv.org/abs/2412.02732) · [`NASA-IMPACT/Prithvi-EO-2.0`](https://github.com/NASA-IMPACT/Prithvi-EO-2.0)
   * SegFormer — [`arXiv:2105.15203`](https://arxiv.org/abs/2105.15203)
   * SAM 2 & Segment Geospatial (`samgeo`) — [`arXiv:2408.00714`](https://arxiv.org/abs/2408.00714) · [`facebookresearch/segment-anything-2`](https://github.com/facebookresearch/segment-anything-2) · [`opengeos/segment-geospatial`](https://github.com/opengeos/segment-geospatial)
   * TorchGeo & Segmentation Models PyTorch — [`microsoft/torchgeo`](https://github.com/microsoft/torchgeo) · [`qubvel-org/segmentation_models.pytorch`](https://github.com/qubvel-org/segmentation_models.pytorch)
3. **Aerial Flood, Road & SAR Victim Detection / Tracking:**
   * FloodNet — [`arXiv:2012.02951`](https://arxiv.org/abs/2012.02951)
   * RescueNet — [`arXiv:2202.12361`](https://arxiv.org/abs/2202.12361) · [`BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation`](https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation)
   * LADI v2 — [`arXiv:2406.02780`](https://arxiv.org/abs/2406.02780) · [`MITLL/LADI-v2-dataset`](https://huggingface.co/datasets/MITLL/LADI-v2-dataset)
   * RDD2022 — [`sekilab/RoadDamageDetector`](https://github.com/sekilab/RoadDamageDetector)
   * VisDrone — [`arXiv:1804.07437`](https://arxiv.org/abs/1804.07437) · [`VisDrone/VisDrone-Dataset`](https://github.com/VisDrone/VisDrone-Dataset)
   * SeaDronesSee — [`arXiv:2105.01922`](https://arxiv.org/abs/2105.01922) · [`Ben93kie/SeaDronesSee`](https://github.com/Ben93kie/SeaDronesSee)
   * HERIDAL / AIR — [`Accenture/AIR`](https://github.com/Accenture/AIR) · POP Thermal Occluded Person — [`PMC11840078`](https://pmc.ncbi.nlm.nih.gov/articles/PMC11840078/) · HIT-UAV — [`suojiashun/HIT-UAV`](https://github.com/suojiashun/HIT-UAV)
   * D-Fire — [`AlimTleuliyev/wildfire-detection`](https://github.com/AlimTleuliyev/wildfire-detection)
   * Permissive Detectors & Tiling: [`Peterande/D-FINE`](https://github.com/Peterande/D-FINE) · [`roboflow/rf-detr`](https://github.com/roboflow/rf-detr) · [`lyuwenyu/RT-DETR`](https://github.com/lyuwenyu/RT-DETR) · [`Megvii-BaseDetection/YOLOX`](https://github.com/Megvii-BaseDetection/YOLOX) · [`obss/sahi`](https://github.com/obss/sahi)
   * Multi-Object Tracking: [`NirAharon/BoT-SORT`](https://github.com/NirAharon/BoT-SORT) · [`FoundationVision/ByteTrack`](https://github.com/FoundationVision/ByteTrack)
4. **Photogrammetry, 3D, Serving, Edge, MLOps & Copilot:**
   * Photogrammetry & 3D: [`OpenDroneMap/NodeODM`](https://github.com/OpenDroneMap/NodeODM) · [`NASA-AMMOS/3DTilesRendererJS`](https://github.com/NASA-AMMOS/3DTilesRendererJS) · [`nerfstudio-project/gsplat`](https://github.com/nerfstudio-project/gsplat) · [`sparkjsdev/spark`](https://github.com/sparkjsdev/spark)
   * Serving & Queue: [`Lightning-AI/LitServe`](https://github.com/Lightning-AI/LitServe) · [`microsoft/onnxruntime`](https://github.com/microsoft/onnxruntime) · [`openvinotoolkit/openvino`](https://github.com/openvinotoolkit/openvino) · [`procrastinate-org/procrastinate`](https://github.com/procrastinate-org/procrastinate) · [`bentoml/BentoML`](https://github.com/bentoml/BentoML) · [`triton-inference-server/server`](https://github.com/triton-inference-server/server)
   * Burst GPU & Mesh VPN: [`Modal + Tailscale`](https://modal.com/docs/guide/tailscale) · [`RunPod`](https://www.runpod.io/) · [`Tailscale`](https://tailscale.com/)
   * Edge AI: [`ONNX Runtime Mobile / React Native`](https://onnxruntime.ai/) · [`ExecuTorch / React Native`](https://docs.swmansion.com/react-native-executorch/)
   * MLOps, Calibration & Copilot: [`mlflow/mlflow`](https://github.com/mlflow/mlflow) · [`iterative/dvc`](https://github.com/iterative/dvc) · [`treeverse/lakeFS`](https://github.com/treeverse/lakeFS) · [`huggingface/huggingface_hub`](https://github.com/huggingface/huggingface_hub) · [`scikit-learn-contrib/MAPIE`](https://github.com/scikit-learn-contrib/MAPIE) · [`pydantic/pydantic-ai`](https://github.com/pydantic/pydantic-ai) · [`vllm-project/vllm`](https://github.com/vllm-project/vllm) · [`mbzuai-oryx/GeoChat`](https://github.com/mbzuai-oryx/GeoChat)
