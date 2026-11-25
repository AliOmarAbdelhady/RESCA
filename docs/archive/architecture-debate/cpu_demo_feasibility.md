# RescueVision — Single-User CPU-Only Contabo Demo Feasibility Analysis

**Role:** Performance & MLOps Engineer
**Date:** 2026-11-25
**Scope:** End-to-end feasibility of running the complete RescueVision application as a **single-user demonstration** on a **GPU-less Contabo CPU server** with **$0 GPU rental budget** (all model training done externally on free Kaggle/Colab GPUs).

---

## 1. Verdict

**Verdict: `YES, WITH CONDITIONS`**

The entire RescueVision application **can** run reliably as a responsive single-user demo on a single CPU-only Contabo server (~€28/month net on **Cloud VPS Plus 8**, or ~$65.20/month on **Cloud VDS M** for dedicated physical cores), **provided five engineering conditions are enforced**: (1) **heavy batch photogrammetry (`NodeODM`), area-wide damage/flood raster sweeps, and any 3D Gaussian Splatting (`3DGS`) optimization are precomputed before the live demo** (on a workstation, Kaggle/Colab free T4, or overnight on the Contabo box itself), while the live demo executes **single-tile / single-frame ONNX Runtime or OpenVINO inference**, PostGIS/pgRouting/pgvector queries, tile serving, WebSocket updates, and mobile sync; (2) **all PyTorch runtime serving, `NVIDIA Triton`, and TensorRT `.plan` dependencies are dropped** from production containers in favor of a single sequential **ONNX Runtime / OpenVINO CPU inference worker** using `FP32` or calibrated **Static QDQ INT8** (`YOLOX-S` / `RT-DETRv2-S`, `SiameseUNetSE`, `SegFormer-B2`, `DINOv2-base`) with threads pinned to physical cores; (3) **server-side 3DGS training (`OpenSplat`) is removed completely** and replaced by precomputed `NodeODM` OGC 3D Tiles + MapLibre building extrusion, or `.spz`/`.rad` splats pre-trained on Kaggle/Colab and rendered strictly on the **viewer's laptop/phone GPU via WebGL2 (`Spark`)**; (4) **the optional LLM/VLM Commander Copilot routes to a free-tier hosted API (Groq or Gemini API free tier)** over the existing read-only `rv_readonly` PII-stripped boundary rather than running a multi-GB `llama.cpp` model on the same server RAM/CPU; and (5) **unmaintained `MinIO` is replaced** by lightweight **SeaweedFS**, **RustFS**, or **Garage**.

---

## 2. Local Hardware Benchmark Baseline & Methodology

To ground scaling estimates instead of guessing PyTorch CPU speeds, architecture-matched ONNX compute graphs were benchmarked locally inside an isolated throwaway virtualenv (`/tmp/.../rv_bench_venv`, `onnxruntime==1.32.0`, `openvino==2026.4.1`, `onnx==1.23.2`, `numpy==2.5.5`).

- **Local Benchmark Host CPU (`lscpu`):** `11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz` — **4 physical cores / 8 logical threads** (boost up to 4.20 GHz), **8 MiB L3 cache**, SIMD flags: `avx2`, `avx512f`, `avx512_vnni`. Host RAM: `31,228 MiB` total (~`12,508 MiB` available during test).
- **Critical Comparison Caveat (Laptop vs. Contabo EPYC):**
  1. The local `i5-1135G7` has **`avx512_vnni`** (hardware INT8 vector dot-product), whereas Contabo `Cloud VDS` (**AMD EPYC 7282**, Zen 2) and standard KVM nodes (`AMD EPYC Processor (with IBPB)`) expose **AVX2 only** (no `AVX-512` / `VNNI`). Furthermore, Contabo EPYC 7282 KVM nodes have a documented `__get_cpuid_count` AVX-512 false-positive `SIGILL` bug in unpatched runtimes ([pytorch#94943](https://github.com/pytorch/pytorch/issues/94943), [contabo-cpuid-issue](https://blog.frehi.be/2023/08/25/amd-epyc-7282-and-avx-512-under-kvm/)). Expect Contabo EPYC single-core INT8 throughput per clock to be **~1.3×–1.8× slower *(estimate)*** than Intel `avx512_vnni`, partially offset on 8 dedicated/performance cores by higher aggregate core count and larger L3 cache.
  2. Local ONNX models used **random weights with exact layer shapes/dimensions** (measuring pure compute, operator dispatch, and memory-bandwidth latency, not accuracy).
  3. **Hyperthreading Discovery:** Pinning ONNX Runtime `intra_op_num_threads` to **4 physical cores** beat 8 logical threads dramatically on heavy models (`vit_b14_224`: `222.0 ms` @ 4t vs `412.6 ms` @ 8t — **1.86× faster**; `yolox_s_640_proxy`: `161.2 ms` @ 4t vs `274.4 ms` @ 8t — **1.70× faster**). **Rule:** Always set `OMP_NUM_THREADS` / `intra_op_num_threads` to physical core count (`<= 8`), never hyperthread count, and run **one heavy inference job at a time**.

### Local Measured ONNX Runtime & OpenVINO Results (`i5-1135G7`, `batch=1`)

| Benchmark Graph (Compute Proxy) | Input Shape | Model Size (FP32 → INT8) | ORT FP32 (`t=4`) | ORT FP32 (`t=8`) | OpenVINO FP32 (`t=4`) | Quantized (`t=4`) | Key Takeaway |
|---|---|---:|---:|---:|---:|---:|---|
| `vit_b14_224` (DINOv2-base: 12L, d=768, 12H, 257 tok) | `1×3×224×224` | `326.6 MB` → `82.4 MB` (Dyn) | `222.0 ms` | `412.6 ms` | `234.7 ms` | **`83.9 ms`** (ORT Dyn INT8) | **2.65× speedup** with Dynamic INT8 on MatMul-heavy ViT. |
| `yolox_s_640_proxy` (CSP + FPN + decoupled head) | `1×3×640×640` | `43.1 MB` → `10.8 MB` (Static QDQ) | `161.2 ms` | `274.4 ms` | `149.3 ms` | `73.5 ms` (ORT Static) / **`65.6 ms`** (OV Static) | **2.46× speedup** with Static INT8; avoid Dynamic INT8 on convs. |
| `resnet34_unet_512_proxy` (ResNet34 encoder + UNet dec) | `1×3×512×512` | `89.5 MB` → `22.4 MB` (Static QDQ) | `546.3 ms` | `462.4 ms` | `267.9 ms` | `130.5 ms` (ORT Static) / **`63.5 ms`** (OV Static) | **8.6× speedup** (ORT FP32 → OpenVINO Static INT8). |
| `segformer_b2_512_proxy` (MiT-B2 + MLP head) | `1×3×512×512` | `93.5 MB` → `23.5 MB` (Dyn) | **`225.3 ms`** | — | `396.0 ms` | `921.6 ms` (ORT Dyn INT8) | **Dynamic INT8 regressed 4.1×** on depthwise Mix-FFN convs; use FP32 or calibrated Static QDQ only. |
| `siamese_seresnext50_608_proxy` (Dual `groups=32` enc + diff) | `2×3×608×608` | `173.4 MB` (FP32) | `850.2 ms` | — | **`631.4 ms`** | — | Add full UNet SE skip decoder memory traffic → **`~1.5–4.0 s`/tile *(estimate)***. |
| SAHI 4K Slicing + Greedy NMS (`3840×2160`, `640×640`, `0.2` ovl) | `32` slices | NumPy array ops | **`25.43 ms`** | — | — | — | Slicing/NMS overhead is negligible; total 4K SAHI time ≈ `32 × detector_ms`. |
| ByteTrack Association (`Kalman + IoU`, 25 tracks) | `25` boxes | Pure NumPy | **`0.062 ms/frame`** | — | — | — | Zero bottleneck (`~0.4–1.0 ms/frame` in full Python loop). |
| `pgvector`-equivalent Cosine Search (`10,000 × 768-d`) | `10k × 768` | `30 MB` float32 | **`4.19 ms/query`** | — | — | — | Instant on CPU (`< 10 ms` with PG18 HNSW). |

---

## 3. Component-by-Component CPU Feasibility Matrix

*(Every derived or scaled latency marked **(estimate)** is extrapolated from the cited published benchmark and/or our local `i5-1135G7` proxy timings adjusted for Contabo EPYC AVX2.)*

### 3.1 Core Infrastructure, Data, Tiles & Client Apps

| Component | Runs on CPU? | Expected Time for Single-User Demo Workload | RAM Footprint | Evidence Link | Mitigation if Slow / Bottleneck |
|---|---|---|---|---|---|
| **PostgreSQL 18 + PostGIS 3.6 + pgRouting 4 + pgvector + PgBouncer** | **Yes (Native)** | OLTP queries / `pgr_aStar` city-grid route (`4×4` Cairo demo grid or urban AOI): **`5–40 ms` *(estimate)***; `ST_AsMVT` uncached tile: **`15–80 ms` *(estimate)***; `pgvector` HNSW top-5 search: **`< 10 ms`**. | **`400–900 MB`** (with `shared_buffers=1GB`–`1.5GB`, `work_mem=32MB`, `PgBouncer ~20 MB`). | [pgRouting](https://github.com/pgRouting/pgrouting), [pgvector](https://github.com/pgvector/pgvector), local `10k×768d` timing (`4.19 ms`) | Precompute `road_segments` topology & spatial `GIST`/`HNSW` indexes; cache `ST_AsMVT` responses in Caddy/in-memory LRU (`30–60 s` TTL) or drop Redis for 1-user demo. |
| **Backend API (`core-api`, FastAPI + WebSockets + `Procrastinate`)** | **Yes (Native)** | REST CRUD & auth: **`5–30 ms` *(estimate)***; WebSocket broadcast (`uvicorn` `1–2` workers): **`< 15 ms` *(estimate)***; job enqueue (`SKIP LOCKED`): **`< 10 ms`**. | **`180–350 MB`** (no PyTorch/GDAL imported in API process). | [Procrastinate](https://github.com/procrastinate-org/procrastinate), [FastAPI](https://fastapi.tiangolo.com/) | Enforce strict separation: `core-api` has **zero ML/raster libraries**; return `202 Accepted` for AI/geospatial work and push progress via WebSocket (`LISTEN/NOTIFY` or `Procrastinate` polling). |
| **Web Console (React/Vite + MapLibre GL JS + 3D Tiles)** | **Yes (Static Build + Client GPU)** | Static SPA served by `Caddy`: **`< 50 ms`**. All 2D map pan/zoom, vector extrusion, and optional 3D rendering execute on the **viewer's laptop GPU via WebGL2**. | **`~25–50 MB`** server-side (`Caddy` static serving). | [MapLibre GL JS](https://maplibre.org/), [3DTilesRendererJS](https://github.com/NASA-AMMOS/3DTilesRendererJS) | Cap viewport polygons via PostGIS `ST_SimplifyPreserveTopology` + MVT clipping; keep CesiumJS (`~1.2 MB` JS) out unless strict global globe is required. |
| **Expo Mobile App** | **Runs on Phone (Served by Backend)** | Phone runs native React Native/Expo client; Contabo serves only JSON API, WebSockets, and PowerSync/offline sync deltas (**`10–50 ms` *(estimate)***). | **`0 MB` extra** (or **`~150–300 MB`** if running self-hosted `PowerSync`). | [Expo](https://expo.dev/), [PowerSync](https://www.powersync.com/) | For a 1-user demo, Expo connects directly to `core-api` REST/WS + SQLite outbox; keep `PowerSync` optional (`--profile offline-sync`) to save RAM/ops. |
| **Object Storage (`MinIO` → `SeaweedFS` / `RustFS` / `Garage`)** | **Yes (Native)** | Presigned S3 upload / byte-range COG reads: **`5–25 ms`/req *(estimate)***. **Note:** `github.com/minio/minio` is archived/unmaintained (AGPL-3.0). | **`~345 MB`** (`RustFS` idle) or **`~80–300 MB`** (`Garage` / single-binary `SeaweedFS` tuned) vs `~804 MB` 3-container `SeaweedFS`. | [MinIO Archived Repo](https://github.com/minio/minio), [RustFS vs MinIO vs SeaweedFS Mar 2026 Bench](https://www.rustfs.com/blog/rustfs-minio-seaweedfs-garage-memory-benchmark-2026/) | Replace `MinIO` with **RustFS** or **SeaweedFS** (Apache-2.0) for S3-compatible COG byte-range reads and model artifact storage. |
| **Map Tiles (`Martin` + `TiTiler`)** | **Yes (Native)** | `Martin` MVT vector tiles: **`3–25 ms`/tile *(estimate)***. `TiTiler` dynamic COG raster tile (`256×256` PNG/WebP): **`40–180 ms`/tile *(estimate)*** (first cold read; `< 10 ms` cached). | **`Martin`: `25–35 MB`**; **`TiTiler`: `350–612 MB`** (1–2 workers). | [Martin](https://github.com/maplibre/martin), [Martin Bench](https://skyserve.ai/blog/vector-tiles-benchmark-martin-tegola-pg-tileserv/), [TiTiler](https://github.com/developmentseed/titiler) | **Mandatory:** Set `GDAL_CACHEMAX=200` (MB) and `MALLOC_ARENA_MAX=2` on `TiTiler` (default GDAL caches 5% host RAM/worker!). Put Caddy disk/mem tile cache in front; prebuild COG overviews (`gdaladdo`). |

### 3.2 Photogrammetry & 3D Reconstruction

| Component | Runs on CPU? | Expected Time for Single-User Demo Workload | RAM Footprint | Evidence Link | Mitigation if Slow / Bottleneck |
|---|---|---|---|---|---|
| **OpenDroneMap / NodeODM (Orthomosaic + DSM + 3D Mesh)** | **Yes (CPU-native)** | **50–80 images (20MP):** **`12–25 min` *(estimate)***. **100–200 images:** **`35–45 min`**. **~393 images:** **`~2 hr`**. Too slow for a live 5-min demo button click, fine overnight. | **40 imgs:** `4 GB`; **100–200 imgs:** `16 GB`; **250 imgs:** `16–32 GB`; **500+ imgs:** `32+ GB`. | [ODM Installation & RAM Docs](https://docs.opendronemap.org/installation/), [ODM Benchmark Paper (MDPI)](https://www.mdpi.com/2072-4292/14/16/4077) | **Precompute offline** before demo (local/Colab/overnight Contabo). If running a tiny live demo stitch (`<= 25` downscaled `2000px` photos), set `--fast-orthophoto --orthophoto-resolution 5` (cuts runtime >75–80% by skipping dense MVS, though 3D mesh/DSM is omitted). |
| **3D Gaussian Splatting (`OpenSplat` Training)** | **Technically yes, practically NO** | CPU optimization is **~100× slower than GPU** (~1 iter/s → **`4–8+ hours`** for 15k–30k iterations on one building block). | **`6–16+ GB`** system RAM. | [OpenSplat GitHub](https://github.com/WebODM/OpenSplat), [RadianceFields OpenSplat CPU note](https://radiancefields.com/opensplat-1-0-is-here) | **Remove `opensplat` container from Contabo completely.** Replace with either (a) precomputed `NodeODM` 3D mesh → OGC 3D Tiles via `3DTilesRendererJS`, or (b) splats **trained offline on Kaggle/Colab T4** exported to compressed `.spz`/`.rad` and rendered on the **client browser GPU via `@sparkjsdev/spark` (WebGL2 + WASM LoD)**. |

### 3.3 Vision AI, Tracking & Embeddings (ONNX Runtime / OpenVINO CPU)

| Component | Runs on CPU? | Expected Time for Single-User Demo Workload | RAM Footprint | Evidence Link | Mitigation if Slow / Bottleneck |
|---|---|---|---|---|---|
| **Joint Building Damage (`SiameseUNetSE` `se_resnext50_32x4d`, `608×608`)** | **Yes** | **`~1.5–4.0 s/tile` *(estimate)*** (`631 ms` OV / `850 ms` ORT measured on simplified proxy). A `0.8×0.8 km` Kahramanmaras AOI at `0.5 m/px` (`1600×1600 px` ≈ **16 tiles** w/ 25% overlap) takes **`~25–65 s` *(estimate)***. `10 km²` high-res UAV would take tens of minutes. | **`~450–750 MB`** (1 ORT/OV session, `173 MB` FP32 weights). | Local `siamese_seresnext50_608_proxy` (`631–850 ms`), [configs/inference.yaml](../../../configs/inference.yaml) | **Precompute AOI-wide damage maps** before demo (`FR-DA` review loads from PostGIS in `< 50 ms`). Allow **live on-demand inference on 1–4 user-selected tiles (`608×608`)** (~2–12 s async wait with WebSocket progress bar). Export calibrated **Static QDQ INT8** (`OpenVINO`) for ~2× extra speedup *(estimate)*. |
| **Building Segmentation (`U-Net ResNet34`, `512×512`)** | **Yes** | **`63.5 ms/tile`** (local OV Static INT8) to **`268–546 ms/tile`** (FP32) → **`~100–120 ms/tile` *(estimate)*** on Contabo EPYC AVX2 Static INT8 (`~2 s` for 16 tiles). | **`~250–400 MB`** (`89.5 MB` FP32 → `22.4 MB` INT8). | Local `resnet34_unet_512_proxy` (`63.5 ms` OV INT8), [configs/building_seg_unet.yaml](../../../configs/building_seg_unet.yaml) | Prefer **joint `SiameseUNetSE`** (fewer passes) or **OSM/Microsoft Building Footprints** + Static INT8 `OpenVINO` when footprints are absent. |
| **Flood & Road Passability (`SegFormer-B2`, `512×512`)** | **Yes** | **`~225–400 ms/tile`** measured locally FP32 (`~1–4 s/tile` on generic edge CPU; **`~350–650 ms/tile` *(estimate)*** on Contabo EPYC FP32). 16 tiles (`0.8×0.8 km`) ≈ **`6–11 s` *(estimate)***. | **`~350–550 MB`** (`93.5 MB` FP32). | Local `segformer_b2_512_proxy` (`225.3 ms` ORT FP32), [AbrahamPJ/segformer-b2-clothes-onnx](https://huggingface.co/AbrahamPJ/segformer-b2-clothes-onnx) | **Do NOT use Dynamic INT8** (4.1× slower locally: `921.6 ms`). Run **FP32 ORT** or calibrated **Static INT8**, and swap `SegFormer-B2` → `SegFormer-B0`/`B1` if sub-200 ms live tiling is needed. |
| **Post-Only Building Triage & Scene Embeddings (`DINOv2-base` / `DINOv3 SAT-493M`, `224×224`)** | **Yes** | **DINOv2-base (`224×224`):** **`83.9 ms/crop`** (local ORT Dyn INT8; `222 ms` FP32) → **`~120–160 ms/crop` *(estimate)*** on Contabo EPYC. `100` crops ≈ **`12–16 s` *(estimate)***. (`DINOv3 ViT-L/SAT-493M` ~3.5× slower → **`~450–600 ms/crop` *(estimate)***). | **`~350–550 MB`** (`DINOv2-base` Dyn INT8 `82.4 MB`); **`~900 MB`** (`DINOv3-L` INT8). | Local `vit_b14_224` (`83.9 ms` Dyn INT8), [Armaggheddon/tips-onnx](https://huggingface.co/Armaggheddon/tips-onnx), [dinov2-large-int8](https://huggingface.co/robotflowlabs/dinov2-large-int8) | **Use `DINOv2-base` (or `DINOv3-B` distilled) with ORT Dynamic INT8** for live single-crop queries (`< 200 ms`); **precompute `image_embeddings` (`pgvector`) offline** for historical archive. |
| **Person Detection (`YOLOX-S` / `RT-DETRv2-S` / `D-FINE-S`, `640×640` + `SAHI`)** | **Yes (with SAHI cap)** | **Single `640×640` frame:** `48.4 ms` (`YOLOX-S` Static INT8 on 2 Xeons) / `65.6 ms` (local OV INT8) / `76.5 ms` (`RT-DETRv2-S` OV INT8) → **`~70–130 ms/frame` *(estimate)*** on Contabo EPYC (`~8–14 FPS` single frame). **4K (`3840×2160`) with 32 SAHI slices:** **`~2.5–4.5 s/frame` *(estimate)*** (Static INT8) vs **`~10–18 s`** (FP32 DETR). | **`~200–450 MB`** (`YOLOX-S` INT8 `~11 MB`, `RT-DETRv2-S` INT8 `~20 MB`). | [tailetan/edge-realtime-inference](https://github.com/tailetan/edge-realtime-inference) (`48.4 ms` YOLOX-S INT8), [CoreEpoch/rtdetrv2-s-int8-onnx](https://huggingface.co/CoreEpoch/rtdetrv2-s-int8-onnx) (`76.5 ms`), [D-FINE](https://github.com/Peterande/D-FINE), local SAHI (`25.4 ms` overhead) | **No 30 fps live SAHI video.** Run live SAHI only on **single uploaded UAV photos** (2–5 s async), or slice at `1280×1280` input / `perform_standard_pred=False` (`12–16` slices instead of `32`). Precompute full drone photo sweeps. Use Apache-2.0 **YOLOX-S** or **RT-DETRv2-S** (not AGPL `YOLOv8s`). |
| **Person Tracking (`ByteTrack` / `BoT-SORT`)** | **Yes (Native CPU)** | **`0.062 ms/frame`** (local NumPy Kalman+IoU) to **`~0.4–1.0 ms/frame`** (`ByteTrack` full pipeline). `BoT-SORT` with ReID adds **`~18 ms/frame`** on CPU; `BoT-SORT` with `gmc_method=none` or `0.25×` optical flow adds **`~2–5 ms/frame` *(estimate)***. | **`< 50 MB`** inside `geo-worker`. | [ForaSoft ByteTrack vs BoT-SORT](https://www.forasoft.com/blog/article/how-to-track-people-in-realtime-on-cpu), [FoundationVision/ByteTrack](https://github.com/FoundationVision/ByteTrack), [NirAharon/BoT-SORT](https://github.com/NirAharon/BoT-SORT) | Disable ReID (`with_reid=False`) on CPU; for discrete drone photo sequences, use the geo-overlap temporal track linker (`ST_DWithin` uncertainty circles) already proposed in `AI_SYSTEM.md`. |

### 3.4 Optional LLM / VLM Commander Copilot

| Component | Runs on CPU? | Expected Time for Single-User Demo Workload | RAM Footprint | Evidence Link | Mitigation if Slow / Bottleneck |
|---|---|---|---|---|---|
| **Local `llama.cpp` Copilot (Qwen2.5-3B / Llama-3.1-8B `Q4_K_M`)** | **Yes, but slow & heavy** | Published AMD EPYC Rome/Milan CPU benchmarks: **8B `Q4_K_M` = `~11.2 tok/s`** on an 8-vCPU EPYC VM (`~22.2 tok/s` only across full 32-core dual EPYC 7282 sockets). A 250-token structured JSON tool-call response takes **`~20–30 s` *(estimate)***, stalling AI vision workers on the same 8 cores. | **`1.8–2.5 GB`** (3B) / **`4.5–5.5 GB`** (8B `Q4_K_M` + KV cache) **resident**. | [llama.cpp EPYC 7282 Discussion #5034](https://github.com/ggml-org/llama.cpp/discussions/5034), [llama.cpp EPYC 7443P 8vCPU](https://github.com/ggml-org/llama.cpp/discussions/9669) | **Do NOT host `llama.cpp` on Contabo for the demo.** Use a **$0 Free Hosted API** (**Groq Free Tier**: `30 RPM / 1,000 RPD` or **Gemini API Free Tier**: `5–15 RPM / 250k TPM`) via `PydanticAI` over `rv_readonly` (zero PII sent externally), giving **`< 1.5 s`** tool responses and saving `4–5 GB` RAM. |

---

## 4. Recommended Contabo Plan & Memory/Cost Sizing

### 4.1 Current Contabo Offerings Comparison (Verified 2026 Plans)

| Plan Tier | Exact Plan | CPU | RAM | Storage (NVMe/SSD) | Network | Monthly Cost (Est. EU / USD) | Verdict for RescueVision Demo |
|---|---|---|---:|---:|---:|---:|---|
| **Core VPS** | `Cloud VPS 8` (formerly VPS L/20) | 8 shared vCPUs (mixed gen) | 24 GB | 150 GB NVMe / 300 GB SSD | 600 Mbit/s | **€11.20–€14.00/mo** ($13.44–$16.80) | **Risky.** High shared-host CPU steal causes unpredictable 3–10× latency spikes during live ONNX inference. |
| **Performance VPS** | **`Cloud VPS Plus 8`** *(Primary Pick)* | **8 shared AMD EPYC vCPUs** | **24 GB** | **450 GB PCIe Gen4 NVMe** | **1 Gbit/s** | **€28.00/mo net** (€33.32 incl. VAT) / **$33.60/mo** (24mo promo, $42.00 std EU; $43.65 US) | **Best Value Demo Pick.** Strong single-thread EPYC, fast Gen4 NVMe for COGs/3D Tiles, ample 24 GB RAM for full stack + 1 active ONNX worker. |
| **Performance VPS (Large)** | `Cloud VPS Plus 12` | 12 shared AMD EPYC vCPUs | 48 GB | 600 GB PCIe Gen4 NVMe | 1 Gbit/s | **€47.20/mo net** / **$56.80/mo** (promo) | Worth it only if running multi-model warm memory caching + NodeODM overnight without swapping. |
| **Max Performance (Dedicated Cores)** | `Cloud VDS S` | 6 **dedicated** EPYC 7282 cores | 24 GB | 180 GB NVMe | 250 Mbit/s | **$52.00/mo** (promo) / €37.13–€46.65 incl. VAT | Tighter disk (180 GB) and slightly fewer cores for TiTiler + ONNX concurrency. |
| **Max Performance (Dedicated Cores)** | **`Cloud VDS M`** *(Zero-Jitter Pick)* | **8 dedicated AMD EPYC 7282 physical cores (2.8 GHz)** | **32 GB** | **240 GB NVMe** | **500 Mbit/s** | **$65.20/mo** (24mo promo, $81.50 std) / **€46.65–€59.02/mo** incl. VAT | **Best for Live Graded Defense.** Zero noisy-neighbor CPU steal; 32 GB RAM safely covers occasional live small-batch NodeODM (100–200 imgs = 16 GB). |
| **Bare Metal** | `AMD Ryzen 12 Cores` (Ryzen 9 7900) | 12 physical Zen 4 cores (AVX-512, 5.4 GHz) | 64 GB DDR5 | 1 TB NVMe | 1 Gbit/s | **€109.65–€129.00/mo** ($131.75–$155) | Overkill for a 1-user student demo (and frequently out of stock on Contabo). |

*Sources: [Contabo Cloud VPS](https://contabo.com/en/vps/), [Contabo Performance VPS](https://contabo.com/en/vps-performance/), [Cloud VPS Plus 8](https://contabo.com/en/vps-performance/cloud-vps-plus-8/), [Contabo Cloud VDS](https://contabo.com/en/vps-dedicated/), [Contabo Dedicated](https://contabo.com/en/dedicated-servers/).*

### 4.2 Sizing & RAM Budget on **`Cloud VPS Plus 8` (8 vCPU, 24 GB RAM, 450 GB NVMe)**

| Memory Consumer | Steady-State RAM (`docker stats` estimate) | Notes |
|---|---:|---|
| Linux OS + Docker daemon + `Caddy 2` | `~600 MB` | Host kernel + TLS proxy + tile cache |
| `PostgreSQL 18` (PostGIS + pgRouting + pgvector) + `PgBouncer` | `~1,800 MB` | `shared_buffers=1GB`, single-user connections |
| `RustFS` or `SeaweedFS` (replacing archived `MinIO`) | `~350–800 MB` | S3 storage for COGs, 3D Tiles, ONNX weights, PDFs |
| `core-api` (FastAPI + WS) + `geo-worker` (`Procrastinate`) | `~550 MB` | No `torch` / no `cuda`; uses `rasterio` + `shapely` |
| `Martin` (`~35 MB`) + `TiTiler` (`~450 MB`, `GDAL_CACHEMAX=200`) | `~485 MB` | `1` TiTiler worker (`WEB_CONCURRENCY=1`) |
| **Sequential CPU AI Runner** (1 active model loaded or 3 ultra-lean ORT/OV sessions with `workers=1`) | **`~1,200–2,200 MB`** | **Total Peak with 1 active model: `~5.0–6.5 GB` / `24 GB`** |
| **Free Headroom (Page Cache + GDAL + Burst)** | **`~17.5 GB`** | Keeps PostGIS + COG blocks hot in Linux page cache! |

- **Storage Allocation (`450 GB NVMe`):** OS/Docker images `~20 GB`, PostgreSQL WAL + OSM Egypt/Turkiye roads `~15 GB`, Precomputed Demo COGs + 3D Tiles + Raw UAV imagery `~30–80 GB`, ONNX INT8/FP32 weights `~2 GB`, leaving **>300 GB free**.
- **Recommendation Summary:** Start on **`Cloud VPS Plus 8`** (**€28.00/mo net** / **$33.60/mo**). Upgrade to **`Cloud VDS M`** (**$65.20/mo**) only if during rehearsals shared-VPS CPU steal spikes live `SAHI` / `SiameseUNetSE` latencies above target, or if examiners insist on clicking a live `NodeODM` run (capped at ~100–150 photos).

---

## 5. Single-User Demo Workflow (Precomputed vs. Live)

For a **10–15 minute graduation / stakeholder demonstration** without a GPU, the platform splits cleanly into **Precomputed Area Artifacts** (loaded instantaneously from PostGIS / TiTiler / SeaweedFS) and **Live Interactive CPU Inference** (triggered on a single tile, photo, or building crop in front of the audience).

### 5.1 Precomputed Before the Demo (Free Kaggle/Colab T4 or Overnight on Contabo)

1. **Model Training & ONNX Export (Kaggle/Colab Free T4):**
   - Train `SiameseUNetSE` (`608×608`), `SegFormer-B2` (`512×512`), `YOLOX-S` or `RT-DETRv2-S` (`640×640`), and `DINOv2-base` probe (`224×224`).
   - Fit temperature scaling $T$ and `MAPIE` conformal quantile $\hat{q}$ on validation splits (pure CPU math).
   - Export to `.onnx`, calibrate **Static QDQ INT8** for CNN/DETR models (`YOLOX-S`, `RT-DETRv2-S`, `ResNet34-UNet`, `SiameseUNetSE`), **Dynamic INT8** for `DINOv2-base`, keep `SegFormer-B2` in `FP32` (or benchmarked Static INT8), and upload `.onnx` + SHA-256 digests to Contabo S3 (`model-artifacts/`).
2. **AOI Photogrammetry (`NodeODM`):**
   - Stitch the primary demo drone sortie (100–300 frames) into `ORTHOMOSAIC` COG (`gdaladdo` overviews), `DSM` COG, and OGC `3D Tiles` (`MESH_3D_TILES`). Upload to S3 (`cog-products/`, `3d-artifacts/`).
3. **Optional 3DGS Priority Collapse Scene:**
   - Train `gsplat`/`OpenSplat` on Kaggle T4 (10–20 min), export compressed `.spz`/`.rad` (~15–40 MB), store in S3 (`3d-artifacts/`).
4. **AOI-Wide Baseline Damage & Embedding Index:**
   - Pre-populate `buildings`, `building_assessments`, `cost_estimates`, `road_segments`, and 10k historical `image_embeddings` (`pgvector` HNSW) for the main scenario (`02_demo_scenario.sql` Cairo grid + Kahramanmaras AOI) so the commander dashboard opens rich and immediate.

### 5.2 Live During the Demo (Everything Runs End-to-End on Contabo CPU)

| Demo Step | What Executes on Contabo CPU | Expected Live Wait | User Experience |
|---|---|---|---|
| **1. Open 2D/3D Command Console** | `Caddy` + `Martin` MVT + `TiTiler` COG + `3DTilesRendererJS` / `Spark` WebGL2 on viewer's laptop GPU | **`< 1 s`** initial viewport | Instant 2D orthomosaic, building damage polygons, and smooth 60 fps client-GPU 3D view. |
| **2. Upload & Analyze a New Disaster Tile (`608×608` pre/post pair)** | Presigned S3 upload → `Procrastinate` job → `SiameseUNetSE` ONNX + `SegFormer-B2` ONNX + `MAPIE` conformal set → PostGIS write + WS push | **`~2.5–6 s` *(estimate)*** | Progress bar (`0% → 100%`) via WebSocket; building status + `[cost_low, cost_high]` update live. |
| **3. Upload a Single UAV Photo for Person Search (`F3` + `F4`)** | GSD check → `SAHI` (capped `12–16` slices @ `1280` or `32` @ `640`) + `YOLOX-S`/`RT-DETRv2-S` Static INT8 → DSM raycast → `ByteTrack`/geo-cluster | **`~2.5–4.5 s` *(estimate)*** | Live pin drops on map with uncertainty radius $\rho$ and cropped thumbnail in Analyst queue. |
| **4. Analyst Verify & Hazard Re-Routing (`F2` + `UC-04`)** | Confirm flood/blockage → PostGIS `hazards` + edge weight update → `pgRouting` `pgr_aStar` → WebSocket push to Web & Expo Mobile | **`< 150 ms`** | Route recalculates immediately around blocked roads on both web console and Expo phone. |
| **5. Visual Similarity Search (`F6`)** | `DINOv2-base` INT8 ONNX (`224×224`) → `pgvector` HNSW cosine top-5 | **`~150–250 ms` *(estimate)*** | Sub-second retrieval of visually similar historical damage cases. |
| **6. Commander Copilot Briefing** | `PydanticAI` calls **Groq / Gemini Free API** + executes 1–2 read-only `rv_readonly` PostGIS SQL tools | **`~1–3 s` *(estimate)*** | Structured Arabic/English situation briefing with clickable `building_id` citations. |

---

## 6. Required Changes to Existing Architecture Proposals to Be CPU-First

| Repo File / Proposal | Current GPU/Heavy Assumption | Required Change for CPU-Only Contabo Demo |
|---|---|---|
| [`configs/*.yaml`](../../../configs/inference.yaml) (`inference.yaml`, `dinov2_damage_classifier.yaml`, `floodnet_segformer.yaml`, `retrieval.yaml`, `building_seg_unet.yaml`) | All hardcode `device: "cuda"` and `.pt` PyTorch checkpoints. | Add `device: "cpu"`, `runtime: "openvino"` or `"onnxruntime"`, `quantization: "static_int8"` / `"dynamic_int8"`, `intra_op_threads: 4` (or physical cores), and `.onnx` artifact paths. |
| [`docs/architecture/platform-architecture-plan.md`](../platform-architecture-plan.md) | Recommends **NestJS** core API + **MinIO** + **Celery** + PyTorch containers + server-side OpenDroneMap/3DGS. | Consolidate backend into **Python/FastAPI + `Procrastinate`** (`SKIP LOCKED`), replace **MinIO → RustFS/SeaweedFS**, drop Celery/Redis for 1-user demo, precompute ODM/3DGS. |
| [`docs/architecture/debate/gemini_proposal.md`](gemini_proposal.md) & [`HOSTING_CONTABO.md`](gemini_proposal/HOSTING_CONTABO.md) | Proposes **4 separate LitServe PyTorch GPU containers** + WireGuard burst to **paid RunPod/Lambda GPU** + MinIO + Redis + CesiumJS. | Drop paid burst-GPU nodes and 4 PyTorch processes. Run **1 lightweight ONNX Runtime / OpenVINO CPU inference service** (or sequential `geo-worker` loader with `workers=1`, `intra_op_num_threads <= physical_cores`), replace MinIO → RustFS/SeaweedFS, use MapLibre + `3DTilesRendererJS`/`Spark`. |
| [`docs/architecture/debate/redteam_gemini.md`](redteam_gemini.md), [`DOCKER.md`](redteam_gemini/DOCKER.md) & [`HOSTING_CONTABO.md`](redteam_gemini/HOSTING_CONTABO.md) | Proposes **`nvcr.io/nvidia/tritonserver`** with GPU-locked **TensorRT `.plan`** engines, server **`opensplat`** container (`gpu-3dgs`), **`mediamtx`** 30 fps RTSP+KLV live video, **`nats`** + **`redis`** + **`powersync`** + **`minio`**. | **Drop `tritonserver` & TensorRT `.plan`** completely (`.onnx` is CPU/GPU portable without TensorRT lock-in). **Remove `opensplat` container** (render Kaggle-trained `.spz`/`.rad` client-side in `Spark`). Make **`mediamtx`**, **`nats`**, **`redis`**, and **`powersync`** optional disabled profiles for the 1-user Contabo demo. Replace `minio` → `rustfs`/`seaweedfs`. |
| [`docs/architecture/debate/glm_proposal.md`](glm_proposal.md) | Evaluates multi-service Docker/Compose topologies with MinIO and live GPU inference assumptions. | Align core compose profile to `caddy` + `postgres` (`pg18`) + `pgbouncer` + `rustfs`/`seaweedfs` + `core-api` + `geo-worker` (with embedded or 1 local ORT/OV CPU server) + `martin` + `titiler`. |
| [`docs/architecture/debate/ai_specialist_gemini/AI_SYSTEM.md`](ai_specialist_gemini/AI_SYSTEM.md) & [`AI_SERVING_AND_INTEGRATION.md`](ai_specialist_gemini/AI_SERVING_AND_INTEGRATION.md) | Recommends `LitServe + ONNX Runtime` with **`CUDAExecutionProvider` on Modal/RunPod** as primary fast lane and `DINOv3 SAT-493M` ViT-L. | Keep `LitServe`/`FastAPI` + `ONNX Runtime / OpenVINO`, `MAPIE` conformal calibration, Apache-2.0 `D-FINE-S`/`RT-DETRv2-S`/`YOLOX-S`, and `BoT-SORT` (`gmc_method=none`) / `ByteTrack` on CPU. Switch default provider to **`OpenVINOExecutionProvider` / `CPUExecutionProvider`**, default embedder to **`DINOv2-base` Dynamic INT8** (lighter than `DINOv3-L`), enforce **1 active worker (`workers=1`)** to avoid thread contention, and set `AI_COPILOT` to **Groq/Gemini Free Tier** (`0` local LLM RAM). |

---

## 7. Sources

- **Contabo Plans & Hardware Behavior:**
  - Contabo Cloud VPS Pricing & Specs: https://contabo.com/en/vps/
  - Contabo Performance VPS (`Cloud VPS Plus 8` / `12`): https://contabo.com/en/vps-performance/ and https://contabo.com/en/vps-performance/cloud-vps-plus-8/
  - Contabo Cloud VDS (`Cloud VDS S` / `M`, dedicated EPYC 7282 cores): https://contabo.com/en/vps-dedicated/
  - Contabo Dedicated Bare Metal Servers: https://contabo.com/en/dedicated-servers/
  - AMD EPYC 7282 KVM `AVX-512` false-positive CPUID issue: https://github.com/pytorch/pytorch/issues/94943 and https://blog.frehi.be/2023/08/25/amd-epyc-7282-and-avx-512-under-kvm/
- **Object Storage & Tile Servers:**
  - MinIO Archived / Unmaintained Repository Notice: https://github.com/minio/minio
  - RustFS vs MinIO vs SeaweedFS vs Garage Memory Benchmark (March 2026): https://www.rustfs.com/blog/rustfs-minio-seaweedfs-garage-memory-benchmark-2026/
  - Martin Vector Tile Server: https://github.com/maplibre/martin and Vector Tiles Benchmark (Aug 2026): https://skyserve.ai/blog/vector-tiles-benchmark-martin-tegola-pg-tileserv/
  - TiTiler Dynamic COG Tile Server & GDAL Memory Configuration: https://github.com/developmentseed/titiler and https://developmentseed.org/titiler/
- **AI Inference, Vision, Tracking & SAHI Benchmarks:**
  - YOLOX Apache-2.0 & Static INT8 CPU Benchmarks (`48.4 ms` on 2 Xeon vCPUs): https://github.com/Megvii-BaseDetection/YOLOX and https://github.com/tailetan/edge-realtime-inference
  - RT-DETRv2 & OpenVINO INT8 CPU Benchmarks (`76.5 ms` `rtdetrv2-s-int8`): https://github.com/lyuwenyu/RT-DETR and https://huggingface.co/CoreEpoch/rtdetrv2-s-int8-onnx
  - D-FINE (Apache-2.0): https://github.com/Peterande/D-FINE
  - SAHI (Slicing Aided Hyper Inference): https://github.com/obss/sahi
  - ByteTrack vs BoT-SORT CPU Benchmarks: https://github.com/FoundationVision/ByteTrack, https://github.com/NirAharon/BoT-SORT, and https://www.forasoft.com/blog/article/how-to-track-people-in-realtime-on-cpu
  - SegFormer-B2 ONNX & DINOv2 INT8 ONNX References: https://huggingface.co/AbrahamPJ/segformer-b2-clothes-onnx, https://huggingface.co/Armaggheddon/tips-onnx, https://huggingface.co/robotflowlabs/dinov2-large-int8
- **Photogrammetry, 3DGS & Client WebGL Rendering:**
  - OpenDroneMap / NodeODM System & RAM Requirements: https://docs.opendronemap.org/installation/ and https://github.com/OpenDroneMap/NodeODM
  - OpenDroneMap Multi-Site Benchmark Study (MDPI Remote Sensing): https://www.mdpi.com/2072-4292/14/16/4077
  - OpenSplat CPU vs GPU Performance (`~100×` slower on CPU): https://github.com/WebODM/OpenSplat and https://radiancefields.com/opensplat-1-0-is-here
  - Client-Side WebGL2 3DGS (`@sparkjsdev/spark`) & OGC 3D Tiles (`3DTilesRendererJS`): https://github.com/sparkjsdev/spark and https://github.com/NASA-AMMOS/3DTilesRendererJS
- **LLM CPU Inference vs. Free Hosted APIs:**
  - `llama.cpp` AMD EPYC 7282 / 7443P CPU Benchmarks: https://github.com/ggml-org/llama.cpp/discussions/5034 and https://github.com/ggml-org/llama.cpp/discussions/9669
  - Groq API Free Tier Rate Limits: https://console.groq.com/docs/rate-limits
  - Google Gemini API Free Tier Rate Limits: https://ai.google.dev/gemini-api/docs/rate-limits
