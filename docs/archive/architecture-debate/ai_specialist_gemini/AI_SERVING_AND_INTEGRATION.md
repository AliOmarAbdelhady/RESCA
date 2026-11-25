# RescueVision — AI Serving, Backend Contract & Contabo GPU Strategy (`AI_SERVING_AND_INTEGRATION.md`)

**Author:** AI Systems Specialist E (Gemini 4 Hydrogen)
**Date:** 2026-11-25
**Goal:** Define practical, resilient container boundaries, the backend-to-AI contract, registry integrity, and a realistic **CPU-first + Burst-GPU** deployment strategy for a **GPU-less Contabo VPS**.

---

## 1. Critique of Other Serving Proposals

| Proposal | Proposed Serving Stack | What Works | Where We Challenge It |
|---|---|---|---|
| `platform-architecture-plan.md` | 4 bare **FastAPI** containers (`ai-damage`, `ai-person`, `ai-embed`, `imagery-worker`) | Simple, familiar Python | Raw FastAPI lacks dynamic micro-batching; 4 separate PyTorch processes duplicate VRAM/RAM overhead. |
| `gemini_proposal.md` | 4 **LitServe** GPU containers + `Procrastinate` + `Redis` | LitServe micro-batching is great for building crops | 4 GPU containers on 1 GPU fragment CUDA contexts (~400–800 MB RAM/VRAM each). |
| `redteam_gemini.md` | 1 **NVIDIA Triton** container (`tensorrt` `.plan` + `onnxruntime`) + `MediaMTX` RTSP/KLV + `NATS` | Single CUDA context, highest theoretical throughput | TensorRT `.plan` files are **GPU-architecture locked** (cannot move from T4/3090 to Contabo CPU or A10G without recompiling); `config.pbtxt` + KLV + NATS is excessive for 6 students. |
| `redteam_glm.md` | 1 FastAPI template, 3 containers (`ai-damage`, `ai-person`, `ai-scene`), **CPU-first ONNX/OpenVINO** | Honest about Contabo lacking a GPU; zero DB creds in AI containers | Rejecting LitServe throws away effortless dynamic batching across `building_assessments` crops and `SAHI` tiles. |

---

## 2. Recommended Serving Stack: **LitServe + ONNX Runtime (3 Model-Family Containers)**

We combine the best ideas from both camps: **[`Lightning-AI/LitServe`](https://github.com/Lightning-AI/LitServe)** wrapping **[`microsoft/onnxruntime`](https://github.com/microsoft/onnxruntime)** (with optional `OpenVINO` execution provider on Intel Contabo CPUs and `CUDAExecutionProvider` on bursted GPUs).

### Why `LitServe + ONNX Runtime` Beats Both Bare FastAPI and NVIDIA Triton Here
1. **Hardware Portability (CPU ↔ Burst GPU Without Rebuilds):** A validated `.onnx` model runs on Contabo's x86_64 CPU (`CPUExecutionProvider` / `OpenVINOExecutionProvider`) AND on any rented NVIDIA GPU (`CUDAExecutionProvider` on RunPod/Modal/lab RTX) via one environment flag (`RV_ORT_PROVIDER=CUDAExecutionProvider|CPUExecutionProvider`)—unlike TensorRT `.plan` engines.
2. **Built-in Dynamic Micro-Batching:** Built on FastAPI, `LitServe` automatically groups concurrent building crops (`ai-damage`, `ai-embed`) or `SAHI` slices (`ai-vision-sar`) into GPU/CPU batches (`max_batch_size=16..32`, `batch_timeout=0.02s`) in ~50 lines of Python—no `config.pbtxt` boilerplate.
3. **Balanced Container Isolation (3 Containers, Not 9 and Not 1):**
   * **`ai-damage`** — Hosts `joint_damage` (`SiameseUNetSE` / `ChangeOS` ONNX) + `post_damage_probe` head. Serves `F1`.
   * **`ai-vision-sar`** — Hosts `person_sar` (`D-FINE-S` / `RF-DETR-S` ONNX) + `flood_road_seg` (`SegFormer-B2` ONNX) + optional `fire_smoke` (`D-FINE` / `YOLOX`). Serves `F2`, `F3`, `F5`. *(Tracking via `BoT-SORT` runs on CPU inside `geo-worker` as a pure Python/NumPy library, not in a GPU container!)*
   * **`ai-embed`** — Hosts `eo_embedder` (`DINOv3 SAT-493M` / `DINOv2-base` ONNX, 768-d). Serves `F1` post-only feature extraction, `F6` `pgvector` similarity search, and OOD drift scoring.
   * **`nodeodm`** *(Optional Profile `photogrammetry`)* — [`OpenDroneMap/NodeODM`](https://github.com/OpenDroneMap/NodeODM) for raw drone frame stitching (`ORTHOMOSAIC` + `DSM` + `3D Tiles`). Disabled cleanly when pre-stitched GeoTIFFs or satellite tiles are uploaded.

---

## 3. Backend-to-AI Contract & Security Boundary

### Rule #1: Zero Database Credentials in AI Containers
AI containers (`ai-damage`, `ai-vision-sar`, `ai-embed`) are **stateless compute engines**. They **never** hold `DATABASE_URL`, `rv_worker` passwords, or MinIO write keys. Only `geo-worker` (running alongside `core-api` in the core Python stack) reads from PostgreSQL/MinIO, calls the AI containers, calibrates logits, and writes results back under `inference_runs`.

### Sync vs. Async Execution Paths

| Path | Trigger | Mechanism | Latency Budget | Fallback if AI Offline (`NFR-RL-04`) |
|---|---|---|---|---|
| **Async Job Queue (95% of AI load)** | Drone/satellite `capture_session` upload, `STITCH`, `ANALYZE`, `REPORT` | `core-api` writes `processing_jobs` (`QUEUED`) + enqueues **[`Procrastinate`](https://github.com/procrastinate-org/procrastinate)** task in **one PostgreSQL transaction**. `geo-worker` claims via `SKIP LOCKED`, streams tiles/crops to AI containers, updates `progress_pct` every $\le 30\text{ s}$ (`NFR-PF-05`). | Seconds (single frame) to minutes (orthomosaic) | Job stays `QUEUED` or enters exponential backoff; map viewing, manual hazard reports, routing, and case dispatch keep working 100%. |
| **Sync Internal REST (Short `< 2s` work)** | Single-image `pgvector` similarity query, single-crop re-score, or Copilot `search_similar_cases` | `core-api` calls `ai-embed` `POST /v1/embed` with `timeout=2.5s` and circuit breaker (3 failures $\rightarrow$ open 30s). | `< 500 ms` GPU / `< 2 s` CPU | Returns empty similarity list + `"Embedding service temporarily unavailable"` banner without failing the request. |

### Canonical AI Container HTTP Contract (`v1`)

Every AI container exposes identical operational and inference endpoints:

| Endpoint | Purpose | Key Request / Response Fields |
|---|---|---|
| `GET /healthz` | Liveness probe | `{"status": "ok"}` |
| `GET /readyz` | Readiness probe (weights loaded + SHA-256 verified + dummy tensor pass) | `{"ready": true, "models": {"joint_damage": "2.0.0"}, "provider": "CUDAExecutionProvider"}` |
| `GET /v1/model-info` | Provenance verification before `geo-worker` starts an `inference_run` | `name`, `version`, `task`, `weights_sha256`, `input_shape`, `gsd_range_cm`, `calibration_temp`, `conformal_qhat`, `license` |
| `POST /v1/damage:predict` | Batched pre/post tiles (`608×608` PNG/raw tensor) or building crops | Request: `run_id`, `tiles[]` (`tile_id`, `pre_b64`/`url`, `post_b64`/`url`, `gsd_cm`).<br>Response: `model_version`, `raw_logits` (or calibrated probs), `embedding_768` (optional), `ood_distance` |
| `POST /v1/vision:detect-persons` | `SAHI`-sliced or single UAV frames | Request: `run_id`, `images[]` (`image_id`, `gsd_cm`, `slice_coords`).<br>Response: `detections[]` (`bbox_xywh`, `score`, `class_id`, `slice_id`) |
| `POST /v1/vision:segment-hazards` | Flood/road semantic masks | Request: `run_id`, `tiles[]`.<br>Response: `mask_png_b64` / RLE polygons per class (`FLOOD_WATER`, `ROAD_CLEAR`, `ROAD_BLOCKED`), `mean_entropy` |
| `POST /v1/embed` | 768-d `DINOv3`/`DINOv2` feature extraction | Request: `crops[]`.<br>Response: `embeddings: float[N][768]`, `ood_cosine_dist: float[N]` |

> **Provenance Guarantee (`FR-IM-07`):** Before `geo-worker` sends tile 1 of an `ANALYZE` job, it queries `GET /v1/model-info` and asserts `resp.weights_sha256 == db_ai_models.weights_sha256`. A container running stale or mismatched weights refuses the job rather than silently tainting `building_assessments`.

---

## 4. Model Registry, Versioning & Schema Hardening

To fix the current seed bug in [`database/seed/01_reference_data.sql`](../../../../database/seed/01_reference_data.sql) (where 9 unbuilt models are seeded as `is_active = true` with `NULL` metrics), extend `ai_models` (`database/schema/04_imagery_ai.sql`) with an evidence constraint:

```sql
ALTER TABLE ai_models
  ADD COLUMN IF NOT EXISTS weights_sha256   text,
  ADD COLUMN IF NOT EXISTS calibration_temp numeric(6,4) DEFAULT 1.0000 CHECK (calibration_temp > 0),
  ADD COLUMN IF NOT EXISTS conformal_qhat   numeric(6,4),
  ADD COLUMN IF NOT EXISTS eval_set_digest  text,
  ADD COLUMN IF NOT EXISTS code_commit      text,
  ADD COLUMN IF NOT EXISTS status           text NOT NULL DEFAULT 'CANDIDATE'
    CHECK (status IN ('CANDIDATE', 'VALIDATED', 'DEPRECATED', 'ROLLED_BACK'));

ALTER TABLE ai_models ADD CONSTRAINT ai_models_active_requires_evidence CHECK (
  NOT is_active OR (
    weights_uri IS NOT NULL AND
    weights_sha256 IS NOT NULL AND
    metrics IS NOT NULL AND
    status = 'VALIDATED'
  )
);
```

* **Zero-Downtime Versioning:** `v1` and `v2` weight bundles can coexist in MinIO (`s3://model-artifacts/serving/<feature>/<vN>/`). Rolling back `v2 → v1` is a 1-second SQL transaction flipping `is_active`, plus restarting/reloading the stateless AI container pointing at `v1`.

---

## 5. Contabo Hosting & Hybrid Burst-GPU Strategy

**Reality Constraint:** Standard Contabo VPS/VDS instances provide generous CPU/RAM/NVMe at low student cost, **but have no NVIDIA GPUs**. Designing as if a dedicated A100 sits inside Contabo guarantees demo failure.

### Three-Mode Execution Topology

```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ Contabo Core VPS (Docker Compose, Always-On, CPU-only)              │
  │  caddy ──► core-api (FastAPI) ──► PostgreSQL 18 (PostGIS/pgRouting) │
  │                │                  ▲                                 │
  │                ▼                  │ (SKIP LOCKED + Procrastinate)   │
  │            geo-worker ────────────┘                                 │
  │                │                                                    │
  │      ┌─────────┴─────────────────────────────┐                      │
  │      │ Tailscale / WireGuard Private Mesh    │                      │
  └──────┼───────────────────────────────────────┼──────────────────────┘
         │                                       │
         ▼ (Mode A: Default CPU Fallback)        ▼ (Mode B/C: Burst GPU via Tailscale)
  [Local ONNX CPU Containers]             [Modal Serverless / RunPod / Lab RTX GPU]
   - ai-damage / ai-vision / ai-embed      - Same Docker images w/ CUDAExecutionProvider
   - Handles single tiles & demo frames    - Plus NodeODM for heavy drone stitching
```

1. **Mode A — Contabo CPU Always-On (`docker-compose.cpu.yml`):**
   * Runs `ai-damage`, `ai-vision-sar`, and `ai-embed` with **INT8/FP32 ONNX Runtime (`CPUExecutionProvider` / `OpenVINO`)**.
   * Realistic performance (to be benchmarked, not assumed): suitable for single-frame triage, `ai-embed` queries, and small demonstration tiles (1–4 tiles) so the platform never breaks when no GPU is rented.
2. **Mode B — Hybrid Tailscale Burst to Lab GPU or RunPod Pod (`docker-compose.gpu.yml`):**
   * During thesis demos, field exercises, or heavy survey uploads, spin up a **RunPod** GPU pod ([`runpod.io`](https://www.runpod.io/)) or university lab workstation (`RTX 3090/4090`) joining the private **[`Tailscale`](https://tailscale.com/)** mesh VPN (`100.x.y.z`).
   * `geo-worker` routes `AI_DAMAGE_URL`, `AI_VISION_URL`, and `NODEODM_URL` to the Tailscale GPU node over encrypted WireGuard—zero public GPU ports exposed.
3. **Mode C — True Scale-to-Zero Serverless Burst (`Modal`):**
   * For unattended spiky surveys, deploy the identical `rv_ai` ONNX inference workers as **[`Modal`](https://modal.com/docs/guide/tailscale)** GPU functions (`gpu="T4"` or `"A10G"`, billed per second, cold start in seconds, connected back to Contabo MinIO/callback via Tailscale userspace SOCKS5 or presigned S3 URLs).
   * **Cost Control:** Students pay **$0/hour** while the Contabo server runs 24/7 between demos, and spend only pennies per survey during active runs.

### Memory & Batching Guardrails on a Single Shared GPU (e.g., 16 GB T4 / 24 GB 3090)
* When bursting all 3 AI containers onto one 16 GB T4 GPU, set explicit ONNX Runtime `gpu_mem_limit` session options (`4 GB` for `ai-damage`, `4 GB` for `ai-vision-sar`, `2 GB` for `ai-embed`) and enforce `workers_per_device=1` in `LitServe`, leaving headroom for `NodeODM` or avoiding concurrent `STITCH` + `ANALYZE` GPU contention via a `Procrastinate` resource lock (`queue="gpu_exclusive"`).
