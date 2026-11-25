# RescueVision — Edge AI & Offline Field Inference (`EDGE_AI.md`)

**Author:** AI Systems Specialist E (Gemini 4 Hydrogen)
**Date:** 2026-11-25
**Scope:** Clear boundary between what runs on the **mobile phone / drone ground station** vs **Contabo / burst GPU server**, runtime selection for Expo React Native, and degraded offline behaviour.

---

## 1. Realistic Edge Scope (Challenging Over-Engineered Proposals)

* **`redteam_gemini.md` proposes** a live `MediaMTX` RTSP + `SMPTE 336M` KLV telemetry pipeline + `NATS Edge Leaf` running 5–10 fps `YOLOv8s` TensorRT on a field Jetson/laptop in the core path.
* **`redteam_glm.md` notes** that zero raw KLV drone streams or field Jetson hardware exist in the team's assets, and recommends cutting on-device detection from MVP.
* **Our Balanced AI Specialist Verdict:**
  * **MVP (Core):** Do **NOT** block Phase 1 on live RTSP/KLV streaming or Jetson hardware. Server-side `geo-worker` + `LitServe/ONNX` handles uploaded frames and orthomosaics reliably.
  * **Phase 2 Practical Edge (Phone-First Offline Photo Triage):** Build a lightweight, rock-solid **offline photo triage mode** inside the **Expo Field App** (`frontend/apps/mobile`) so a responder with zero cellular signal can snap a photo (or inspect a drone micro-SD frame on their phone), detect visible persons/hazards locally in `< 1 second`, and queue a compact `< 50 KB` JSON + cropped thumbnail to the SQLite offline outbox.
  * **Phase 3 Stretch (Field Laptop Ground Station):** If the team acquires a real drone or Gazebo stream late in the year, the exact same `ai-vision-sar` ONNX container runs locally on a field laptop beside the drone controller (`docker compose -f docker-compose.edge.yml`) and syncs detections via REST/outbox when uplink returns.

---

## 2. Edge Runtime Selection for Expo (React Native) & Field Hardware

| Runtime | Format | Expo / Mobile Support | Hardware Backends | Verdict for RescueVision |
|---|---|---|---|---|
| **[`onnxruntime-react-native`](https://onnxruntime.ai/)** | `.onnx` (INT8/FP16) | **Expo Dev Build / Prebuild** (NOT Expo Go) | CoreML (iOS ANE), NNAPI/XNNPACK (Android) | **CHOSEN (Primary Mobile Runtime).** Uses the **exact same `.onnx` artifact family** exported by `kaggle/<feature>/vN/export.py`—zero separate `.tflite` or `.pte` conversion pipeline to maintain. |
| **[`react-native-executorch`](https://docs.swmansion.com/react-native-executorch/)** (Software Mansion / Meta) | `.pte` | Expo Dev Build + Worklets | CoreML/MLX (iOS), XNNPACK/Vulkan (Android) | **Strong Alternative / Phase 2 Spike** if `onnxruntime-react-native` shows higher memory or slower NPU delegation on target Android phones. |
| **LiteRT (formerly TFLite)** | `.tflite` (INT8) | Community RN bridges | NNAPI / GPU Delegate (Android), CoreML (iOS) | **Avoid unless needed:** Requires PyTorch $\rightarrow$ ONNX $\rightarrow$ TF $\rightarrow$ TFLite conversion, which frequently breaks transformer/DETR ops. |
| **CoreML / TensorRT** | `.mlpackage` / `.plan` | Native iOS only / NVIDIA Jetson only | Apple ANE / NVIDIA Tensor Cores | **Platform-specific only:** CoreML is accessed transparently *through* ONNX Runtime Execution Providers on iOS; TensorRT is used only if a physical Jetson Orin is added as a stretch field node. |

> **Mandatory Expo Constraint:** Because C++/native inference delegates (ONNX Runtime / ExecuTorch) and offline SQLite (`op-sqlite`) + `MapLibre` require native bindings, **Expo Go cannot be used**. The mobile app must use **Expo Prebuild / EAS Development Builds** from Sprint 1.

---

## 3. What Runs Where (Server vs. Phone vs. Field GCS)

| Capability | Contabo Server / Burst GPU | Expo Mobile App (Responder Phone) | Field Laptop GCS *(Optional Stretch)* |
|---|---|---|---|
| **F1 Building Damage (`SiameseUNetSE` 608px, `NodeODM`)** | **Yes (Server Only)** — too heavy in RAM/VRAM and requires multi-GB pre/post COGs. | **No** — views cached pre-synced `PMTiles` & `building_assessments` offline. | **No** (unless running offline `NodeODM` rapid-map preset). |
| **F2 Road/Flood Segmentation (`SegFormer-B2`)** | **Yes (Server Only)** — feeds PostGIS `hazards` and `pgRouting`. | **No** — views synced danger zones & runs local Haversine/polygon geofence alarm. | **Optional** (`SegFormer-B2` INT8 ONNX on CPU/laptop GPU). |
| **F3 Visible Person Detection** | **Yes (Full-Res `SAHI` + `D-FINE-S/M`)** — highest recall on 4K/8K imagery. | **Yes (Offline Triage Mode)** — single-frame `YOLOX-Tiny` / `D-FINE-Nano` INT8 (`~5–15 MB` ONNX) on camera photo or selected drone JPEG (`416px`–`640px`). | **Yes (`D-FINE-S` ONNX)** on incoming drone SD-card batches or local RTSP snapshots. |
| **F4 Person Tracking (`BoT-SORT`)** | **Yes (Server Worker)** — multi-frame + cross-view geo-clustering. | **No** — submits single georeferenced `RESPONDER_REPORT` / provisional `EDGE_DETECTION` point. | **Yes (CPU `BoT-SORT`)** on local drone video clips. |
| **F5 Compound Hazard Rules (`ELECTRIFIED_WATER`)** | **Yes (Authoritative PostGIS Transaction)** — updates routes & sends alerts. | **Local Geofence Warning Only** — caches known `compound_alerts.danger_zone` polygons in `op-sqlite` and vibrates/alerts if responder GPS enters zone while offline (labeled with sync age!). | **Local Rule Cache** mirroring active `danger_zone` polygons. |

---

## 4. Offline Behaviour, Model Packaging & Sync Protocol

1. **Dynamic Model Delivery (Keep App Binary Small):**
   * Do **not** bundle 50 MB of `.onnx` weights inside the Expo JS bundle.
   * On first authenticated Wi-Fi launch (or "Prepare Offline Mission Pack"), the app downloads the active compact edge bundle (`person-detector-edge` INT8 `.onnx`, `< 15 MB`, SHA-256 verified against `/v1/edge/models`) into `expo-file-system` persistent storage.
2. **On-Device Inference Execution:**
   * When offline in the field, a responder captures an inspection photo (or selects an imported drone JPEG) inside the **Field Triage** screen.
   * Inference runs off the JS UI thread (Worklet / native async JSI module) in `< 1 s` on mid-range Android/iOS devices.
   * **UI Guardrail (`IR-UI-05`, `D-07`):** Edge detections display a clear **"Provisional On-Device Triage — Lower Recall Than Server SAHI"** banner. The responder confirms or discards the box before saving.
3. **Bandwidth-Efficient Offline Queue (`op-sqlite` Outbox):**
   * Instead of queuing a 12 MB raw JPEG over flaky 2G/3G, the app stores:
     * A UUIDv7 `client_op_id`, `edge_model_id` & `edge_model_version` (preserving `ai_models` provenance!), GPS `(lat, lon, accuracy_m)`, timestamp, bounding box, confidence, and a **cropped `< 50 KB` WebP/JPEG thumbnail** in the local `op-sqlite` outbox (full-res original stays queued at low priority for Wi-Fi upload).
   * On reconnect, `POST /v1/sync/push` uploads the lightweight triage alert immediately so Command sees the victim crop within seconds, while the high-res image backfills asynchronously when bandwidth permits.
4. **Honest Offline Risk Warning (`IR-UI-06`):**
   * An offline device **cannot know** about a new `ELECTRIFIED_WATER` alert raised while disconnected. The mobile map header permanently renders the last successful sync timestamp (e.g., `"OFFLINE — Hazard zones synced 38 min ago"`).
