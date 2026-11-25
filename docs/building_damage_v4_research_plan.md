# RescueVision building damage V4: research and proposed experiment plan

Research checked: 21 October 2026. At authoring time this was **planning only; no training, notebook rewrite, dependency installation, or model/data download had been performed.** The implementation has since started on the `codex/building-damage-v4` branch; gate status and evidence are tracked in [the V4 experiment registry](v4_experiments.md). Research PDFs were read separately from the project datasets. This document remains the research plan and does not report a new measured score.

Technical execution companion: [Luna 5.6 implementation handoff](building_damage_v4_luna56_handoff.md), with module contracts, L1–L9 tasks, initial experiment settings, targeted checks, Kaggle MCP sequencing and delivery criteria. Read both before a future authorized implementation.

## Decision

Use DINOv3 in the next building system, but make its value measurable. The proposed main experiment is a **paired DINOv3 satellite encoder with multiscale temporal fusion and a separate high-resolution detail branch**, supervised for building localization and four-class damage assessment. Compare the satellite ViT-L with the approved ViT-7B as a frozen teacher before considering expensive 7B adaptation.

Build three separately evaluated capabilities: paired overhead damage grading; post-only roof/structural damage typing; and close-range visible-defect segmentation. Add 3D evidence after these are reproducible. One model and one dataset cannot establish coverage of every damage type, viewpoint, and building material.

**Agreed resource constraint:** the user has Kaggle and Colab access, with two accounts mentioned, and prioritizes maximum accuracy over time or quota efficiency. No paid/multi-GPU allocation was supplied. Plan for persistent, resumable work across available sessions; do not assume pooled GPU memory, simultaneous capacity, or circumvent service usage limits. V4.0 first targets the paired overhead branch and reproducible evaluation package. Typology, detailed defects and 3D are subsequent increments toward the full requested coverage, rather than eight concurrent training projects.

Use official xView2 combined F1 above 0.82 as a provisional project milestone, then compare against named reproducible methods under the same protocol. There is no defensible guarantee of a world record before experiments, and this review does not certify a universal current world-best model. The exact person/result meant by “82%” remains unidentified.

## 1. What was reviewed and what is currently supported

Read the repository README; model cards; dataset guide; experiment table; graduation research plan; `claude_view.md`; the Kaggle notebook inventory; detailed source in the RV2 full-joint, native-preprocessing, RV3 training/rescore/smoke notebooks; and the local RV2 summaries. Notebook review was static: no cells executed. The separate chat “Plan RescueVision project completion” concerns documentation allocation and the larger response platform; it is not evidence of completed building-model training.

The latest local commit is `f89a61f` (21 October 2026), removing training/core source. The checkout has scripts and notebooks referring to `src/rescuevision`, but that directory is absent. Do not assume the current README's runnable package claims describe this checkout. Recovering or replacing the intended package is a future implementation decision, not something done in this research.

### Local result evidence

| Artifact | Recorded result | What it establishes |
|---|---|---|
| `outputs/v2/joint_damage_siamese_full_summary.json` | 373 test tiles; pixel localization IoU 0.7108; pixel damage macro-F1 0.6986; `xview2_approx.overall_f1` 0.6463 | A saved historical subset result using multiple metric definitions; not a verified official benchmark score |
| Same artifact | Pixel damage F1: intact 0.9508, minor 0.5086, major 0.4585, destroyed 0.8765 | Intermediate damage classes are much weaker than intact/destroyed in this saved evaluation |
| `outputs/v2/building_unetpp_effb4_summary.json` | Test IoU 0.529 and Dice 0.6874, but reported F1 0.4059 | Metrics have different semantics or an inconsistency needing investigation; do not combine them as interchangeable pixel measures |
| `docs/experiments.md` | E1–E11 all “Pending” | The experiment registry does not capture the saved RV2 history |
| Local RV3 notebooks | No saved execution outputs in the files inspected | Source shows intended behavior; no local artifact establishes RV3 completion or its final score |

These are artifact readings, not a fresh checkpoint evaluation. Live Kaggle run status was not checked. A notebook's presence is not proof of a successful training run.

### Material notebook problems to address in a future version

Cell numbers below are one-based, including Markdown cells.

1. **The RV2 approximate score is a different metric.** In `rv2_train_joint_full.ipynb`, cell 7, `xview2_score` uses connected-component matching over several IoU thresholds and an arithmetic mean of class F1s. Official xView2 scoring uses global pixel counts and a harmonic damage mean. Keep object metrics, but name them separately. [Official scorer](https://github.com/DIUx-xView/xView2_scoring/blob/master/xview2_metrics.py).
2. **RV3 rescore selects settings on test data.** `rv3_rescore.ipynb`, cell 11, sets `SCORING_SPLIT = "test"`, sweeps thresholds/rules/dilation and chooses `best_key`. That is exploratory test analysis, not an untouched final test.
3. **Modified ground truth participates in recipe selection.** Both the rescore notebook cell 11 and training notebook cell 10 compare `dmg` and `dmgd`, then maximize across both. In the training notebook this happens on validation and the final test uses original labels, which is better than test selection, but the validation objective can still select a recipe based on altered targets. Validation and final benchmark selection must use original evaluation labels exclusively.
4. **Checkpoint selection optimizes the wrong proxy.** RV2 cell 5 and RV3 training cell 8 use roughly `0.5 * loc_iou + 0.5 * damage_macro_f1`; this is not the benchmark objective. Localization gating also differs between the training validation loop and final scoring.
5. **Global resizing removes detail.** RV2/RV3 joint transforms resize an entire tile to 608×608. Native preprocessing alone does not preserve detail if training subsequently downsamples everything. Compare native-scale random crops and overlapping native-scale inference.
6. **Ignore handling may contaminate localization.** RV3 training cell 6 builds `loc_t = (comb_t > 0)`. Thus 255, if present in the source damage masks, also becomes a positive building. Establish whether these pixels are genuine ungraded buildings, void regions, or excluded annotations; carry localization validity and damage validity separately. This is a source-level risk, not a confirmed prevalence measurement.
7. **Dependencies and source are unstable.** The setup cells clone an unpinned repository revision; some installs use `check=False`; code is duplicated and monkey-patched inside notebooks. A future run can silently use a different environment or fail because the imported package was removed.
8. **Metadata does not prove image alignment.** Native preprocessing computes a phase shift for metadata while saving the original images. That is a diagnostic, not applied registration. A future alignment method must use image evidence, preserve the coordinate frame of labels, handle invalid borders, and be ablated.
9. **Subset and runtime choices need explicit provenance.** RV2 caps test collection; RV3 caps validation probability collection at 250. Dynamic epoch budgets, EMA, SWA, sampling, and losses need fixed recorded policies before runs. Their simultaneous use obscures which change helps.

Do not discard useful work indiscriminately: the RV3 scorer is much closer to the official pixel definition, validation-selected final testing is present in the training notebook, and paired spatial augmentation is already an appropriate idea. Reuse these concepts after verification.

## 2. Correct the old plan

The graduation plan is useful as a system overview, but lacks a rigorous building-research program. The companion `claude_view.md` needs specific corrections:

- “The correct xView2 figure is ~0.74” must not be presented as a universal ceiling. Published results vary by split, model, metric, and evaluation implementation.
- Its statement that DamageTriage-Bench is not public is now outdated; a public dataset, code, and revised checkpoint exist.
- F1 for the undamaged class and F1 for collapse are not the F1 of a separately evaluated binary standing-versus-collapsed model. The cited class scores cannot justify that binary performance claim.
- “Pixel damage segmentation” on xBD usually assigns the building's grade across its footprint; it does not locate each physical crack or damaged roof panel.
- Synthetic ground truth can validate the simulation scenario and geometry; it does not establish real-disaster image accuracy.
- Add provenance, strict splits, annotation validity, native-resolution evaluation, component labels, compute feasibility, calibration, and independent geographic testing before expanding the model list.

## 3. Establish what beating 82% means

For official xView2-style pixel evaluation:

`S = 0.3 × localization_F1 + 0.7 × harmonic_mean(F1_intact, F1_minor, F1_major, F1_destroyed)`.

Damage predictions are gated by predicted buildings and evaluated on target building pixels. Reproduce the official raster formats, aggregation, masking, and epsilon behavior. Test parity with the reference scorer before any expensive run. Never substitute accuracy, weighted-F1, crop-classifier F1, or object matching for this score. [Scorer source](https://github.com/DIUx-xView/xView2_scoring/blob/master/xview2_metrics.py).

### Relevant results and their limits

| Reference | Verified reported result | Relevance / comparison constraint |
|---|---|---|
| ChangeMamba / MambaBDA-Base | xBD overall F1 81.41%; localization 87.38%; damage 78.84% | Strong task-specific paired comparator; paper protocol must be reproduced locally |
| MambaBDA-Base class results | Minor F1 62.74%, compared with intact 95.94% | Hard classes remain the bottleneck even for strong models |
| Damage-TriageFormer revised public crop checkpoint | Five-class post-only test macro-F1 0.616 on corrected photo-atomic split | Footprint-conditioned typology, not xView2 detection or an official four-grade score |
| `zak-510/xView2` | Self-reported test weighted-F1 82.7%; minor/major F1 44%/43% | Possible interpretation of the user's reference; not confirmed to be the intended person and not world-record evidence |

Sources: [ChangeMamba Table IX](https://arxiv.org/html/2404.03425v3), [current Damage-TriageFormer model card](https://huggingface.co/Ymx1025/DamageTriageFormer-model), [82.7% repository](https://github.com/zak-510/xView2). These are reported results, not independently rerun here.

### The concrete 82.7% example: how it works and why the number is misleading as a universal target

I inspected the `zak-510` source as well as its README. Its damage dataset reads post-event imagery, extracts annotated building regions and resizes them to 64×64. A four-block CNN predicts one of four grades. The evaluation explicitly uses ground-truth building crops, bypassing missed building detections, and computes class-frequency-weighted F1. Thus 82.7% does not mean the end-to-end system finds and grades 82.7% of all damaged buildings. The large intact-class score can dominate the weighted result while intermediate damage remains weak. This is a real nearby result found by research, but there is no evidence that it is the unidentified person the user originally recalled. [Dataset source](https://github.com/zak-510/xView2/blob/main/data_processing/damage_data.py), [model source](https://github.com/zak-510/xView2/blob/main/models/damage_model.py), [evaluation source](https://github.com/zak-510/xView2/blob/main/evaluate_damage_classifier.py).

Another possible lead is Zhao et al.'s ECADS-CNN. The primary publisher describes two stages, efficient channel attention, depthwise separable convolutions, and gains over its baseline, but the exact 82.14 figure appearing in secondary search results was not verified in the accessible primary text. Do not certify it as the intended 82% result. [Primary publication](https://www.tandfonline.com/doi/abs/10.1080/17538947.2024.2302577).

A CRD-Net/DINOv3 conference-paper lead also appeared, but its primary conference page/PDF was inaccessible in this review. It is not used as verified numerical evidence or the architectural foundation of this plan.

### What the first-place xView2 solution actually did

Vladimir Durnov's published solution trained building localization first, transferred those weights to paired Siamese damage networks, emphasized damaged classes, used native-scale crops, full-resolution inference, test-time transforms, and averaged multiple encoders/folds. Its README specifies approximately seven days on two GPUs and acknowledges limits to complete training reproducibility. Its success was a training/data/inference recipe, not simply one superior encoder. Reproduce a bounded single-model version first. [Winner's original explanation](https://github.com/DIUx-xView/xView2_first_place).

Two independent findings should shape our objective. A strong-baseline study demonstrates substantial failure on unseen locations. A recent foundation-embedding study reports mean balanced accuracy falling from 0.807 to 0.638 on xView2 when holding out whole disasters; that is a different task/metric, but directly warns against interpreting familiar-event scores as generalization. [Strong-baseline study](https://arxiv.org/abs/2401.17271), [October 2026 shortcut-learning study](https://arxiv.org/abs/2610.13766).

Maintain two result tracks: exact official-split comparison, and geographically separated unseen-event generalization. Never claim beating a published official-split number using a custom split.

## 4. Define the damage coverage before selecting data

| Capability | Proposed output | Evidence required |
|---|---|---|
| Building discovery | Separate footprint/instance, unique ID, detection confidence | Pre-event overhead imagery and/or independently sourced footprints; predicted-footprint evaluation |
| Paired building severity | Four xBD grades plus probability distribution and uncertainty | Before/after imagery, valid registration, building-grade labels |
| Post-only typology | Undamaged, partial/total roof damage, partial structural damage, total collapse | Footprints and post-event imagery with matching typology labels |
| Detailed visible defects | Masks for supported cracks, spalling, exposed reinforcement, corrosion, missing roof material and facade damage | Close oblique/ground images; task-specific expert labels |
| Damage extent | Visible damaged surface fraction, with visibility coverage | Actual defect masks on the visible component, not a uniform xBD grade raster |
| 3D evidence | Height/shape change, surface location of defects, multi-view agreement | Registered multiview imagery, scale/pose and reconstruction quality |
| Unknown condition | Unobservable / unsupported / ambiguous | Explicit missing-data and abstention rules |

“No visible damage” must not become “structurally safe.” Invisible interiors, foundations, concealed joints, and surfaces outside the capture cannot be assessed by inventing visual details. This is an input-evidence boundary: the path to more coverage is better capture and labels.

For example, a 2 mm crack at 0.6 m/pixel spans about 0.0033 pixel, a simple resolution calculation. No architecture can recover a reliable measurement of that crack from those pixels. A requirement of three pixels across it would imply roughly 0.67 mm/pixel, before blur and viewing-angle effects. Specify the smallest required defect and derive the capture resolution; do not promise crack-width measurement from ordinary satellite imagery or generated super-resolution detail.

## 5. Dataset selection and acquisition priority

These are recommendations based on published descriptions and current source pages. No archives were downloaded or validated here. Exact counts/checksums, license terms, label encodings, and overlap must be audited at acquisition.

| Priority / source | Best role | Why add it | Main limitation / action |
|---|---|---|---|
| P0 — [xBD](https://arxiv.org/abs/1911.09296) | Paired localization and severity benchmark | Direct alignment with the existing system and fair xView2 comparisons | No fine-grained defect masks; audit complete release and preserve official split |
| P0 — [DamageTriage-Bench](https://huggingface.co/datasets/Ymx1025/DamageTriage-Bench) | Post-only roof/structure typology | Public release has 7,472 tiles and five damage types | Use `photo_splits.json`; old split had leakage. Units are visible polygon fragments, not necessarily unique physical buildings. Audit overlapping photos and shared Michael imagery |
| P1 — [RescueNet](https://github.com/BinaLab/RescueNet-A-High-Resolution-Post-Disaster-UAV-Dataset-for-Semantic-Segmentation) | UAV building damage and scene context | 4,494 images; building grades, clear/blocked roads, water, vehicles, trees, pools | Hurricane Michael concentration; 11 listed categories including background. Read actual masks/class map. Source license is CC BY-NC-ND |
| P1 — [CUBIT building defect data](https://github.com/CUHK-USR-Group/Defect-Dataset) | Facade defect detection/segmentation | Building-oriented defect material; CUBIT-Seg targets cracks/spalling | Verify current download, annotations and permissions; not earthquake structural certification |
| P1 — [dacl10k](https://github.com/phiyodr/dacl10k-toolkit) | Defect segmentation pretraining | 19 classes, including 13 damage classes; overlapping labels support concurrent defects | Bridge domain; multi-label sigmoid heads, not mutually exclusive softmax; adapt and validate on buildings |
| P2 — [OmniCrack30k](https://github.com/ben-z-original/omnicrack30k) | Crack segmentation specialist | Diverse crack sources and a reproducible reference model | Crack-only scope; deduplicate constituent datasets and split by structure/source |
| P2 — [CODEBRIM](https://arxiv.org/abs/1904.08486) | Multi-defect recognition pretraining | Concrete cracks, spalling, exposed rebar, efflorescence and corrosion | Classification/box supervision does not create pixel defect truth; bridge-to-building shift |
| P2 — [BRIGHT](https://github.com/ChenHongruixuan/BRIGHT) | Separate optical/SAR damage experiment | Different events and an all-weather research route | Different modalities and three severity classes; never treat SAR as ordinary RGB or force damaged into minor/major |
| P2 — [3DAeroRelief](https://github.com/BinaLab/3DAeroRelief) | Post-disaster 3D semantic evaluation | Eight areas, damaged/intact building point labels | Limited geography and damage taxonomy; split by area and overlapping capture |
| P3 — [SpaceNet 8](https://spacenet.ai/sn8-challenge/) | Flooded buildings/roads auxiliary task | Adds flood-related infrastructure labels | Flood extent is not structural damage severity |
| P3 — [FloodNet](https://github.com/BinaLab/FloodNet-Supervised_v1.0) | Existing UAV flood/context path | Retains useful flood-specific capabilities | Different labels and capture domain; keep distinct evaluation |
| P3 — [LADI v2](https://arxiv.org/abs/2406.02780) | Event/context filtering and hard examples | Approximately 10,000 labeled disaster images | Image-level multilabel supervision, not building defect masks |
| Optional — [AFTERMAP](https://github.com/sultankennesaw-Civil/AFTERMAP-Dataset) | Additional UAV building grades/tarp state | Relevant FEMA-aligned annotations | Full data is request-only, not a guaranteed downloadable dependency |
| Optional — [Google Open Buildings Temporal](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings-temporal_v1) | Historical building presence/height context | Prior geometry/context where coverage exists | Effective 4 m resolution and annual historical cadence; no disaster-damage labels |
| Optional — [NOAA emergency imagery](https://www.noaa.gov/information-technology/open-data-dissemination/news/noaa-open-data-office-hours-noaa-emergency-response-imagery-in-cloud) | Carefully selected new-event annotation pool | Real response imagery and new capture conditions | Raw imagery needs labels and overlap checks; not automatically ground truth |

**Best initial combination:** xBD for paired benchmarking; DamageTriage-Bench for damage type; RescueNet for UAV transfer; CUBIT/dacl10k for close-up defects. Add native local building inspection imagery with expert labels to cover the actual target architecture/materials. Use the other datasets only when they add missing supervision or a held-out domain.

Kaggle's connected API confirmed separate Tunguz train/test and Tier-3 xView2 mirrors. The README's train/test link alone does not establish complete xBD coverage. It also found a RescueNet mirror whose listed license differs from the authors' repository; use original provenance and terms, not a mirror's metadata as authority. [xView2 train/test mirror](https://www.kaggle.com/datasets/tunguz/xview2-challenge-dataset-train-and-test), [Tier-3 mirror](https://www.kaggle.com/datasets/tunguz/xview2-challenge-dataset-tier-3-data), [RescueNet mirror](https://www.kaggle.com/datasets/yaroslavchyrko/rescuenet).

### Combining datasets without corrupting labels

Keep a canonical ontology with dataset-specific adapters. xBD's no/minor/major/destroyed grades and DamageTriage-Bench's component/extent types are not interchangeable. BRIGHT's damaged category does not specify minor versus major. Missing annotations mean “not supervised,” not “absent.” Train shared features with separate heads and explicit loss masks. Preserve original labels for benchmark evaluation; any reviewed corrections form a separate named evaluation set.

Group before cropping or augmentation. Keep all crops, repeated views and neighboring overlapping imagery of the same structure/scene in one split. Check cross-dataset overlap, especially Hurricane Michael. Keep official benchmark tracks unchanged, while deduplicating/filtering auxiliary training material that intersects held-out scenes. Declare external data and possible undisclosed foundation-pretraining overlap. Semi-supervised and transductive use of test imagery must be separately labeled and must not silently enter a supervised comparison.

## 6. Model shortlist and proposed architecture

### DINOv3 is the core candidate, not a ready-made damage detector

The approved `facebook/dinov3-vit7b16-pretrain-sat493m` is a satellite-pretrained feature backbone. Dense patch features still need a task head and labeled training. Meta also releases a distilled satellite ViT-L. The model card's GEO-Bench segmentation means are 75.0 for 7B and 74.5 for ViT-L; these are not xBD damage results and do not prove that 7B wins this task. [Meta model card](https://huggingface.co/facebook/dinov3-vit7b16-pretrain-sat493m), [satellite ViT-L](https://huggingface.co/facebook/dinov3-vitl16-pretrain-sat493m).

The user's email establishes accepted access to the named 7B repository; authenticated downloading and access to other gated variants have not been tested. Preserve model-specific normalization and revision identifiers in future runs.

### Proposed paired overhead path — hypothesis to test

1. Quality-check pre/post metadata, cloud/blur, resolution and registration. Use the original benchmark label grid as the reference frame. Align only the other image/features into that frame, mask invalid borders, and keep labels fixed. Do not register away genuine collapse/change.
2. Encode pre and post separately with shared satellite DINOv3 weights. Begin frozen, then compare LoRA/last-block adaptation. Do not replace the RGB patch embed with an unexplained six-channel input.
3. Extract intermediate spatial tokens into an FPN/DPT-style multiscale neck. Exclude register/class tokens from the spatial grid correctly.
4. Compare simple concatenation plus absolute difference against learned temporal attention/alignment. Keep a small CNN high-resolution branch as an independently tested detail source.
5. Predict localization from stable pre-event geometry and damage from both images. Keep a post-only fallback separately supervised/evaluated.
6. Add a footprint-pooled instance head for building-level class consistency; evaluate both supplied-footprint recognition and predicted-footprint end-to-end performance.
7. Export native-resolution raster probabilities and separate instances, with confidence and validity masks. Only afterward apply validation-selected postprocessing.

### Proposed post-only and close-up paths

For post-only typology, reproduce the corrected Damage-TriageFormer crop baseline, then compare satellite and natural-image DINOv3 initialization. For detailed defects, use a DINOv3 multiscale decoder with overlapping crops and multilabel outputs where defects overlap. Compare a specialized crack segmenter against the general defect head; do not assume that a building-grade classifier supplies crack masks.

Associate close-up observations with a building/component/view and later a 3D surface. Store observed area and occlusion. Fuse evidence only when observations are geometrically compatible. High-resolution natural-image initialization may fit inspection images better than satellite pretraining; this is an experiment, not a settled fact.

### Bounded alternatives

| Candidate | Why include | Decision rule |
|---|---|---|
| Winner-style Siamese U-Net, ResNet34 or SE-ResNeXt50 | Reproducible strong CNN reference and transfer-localization recipe | Establish correctness before expensive foundation runs |
| ChangeMamba/MambaBDA | Purpose-built paired damage network and strong published baseline | Compare on identical data, inference and scoring |
| DINOv3 satellite ViT-L + multiscale head | Primary trainable foundation candidate | Promote on validation improvement across events/classes |
| Approved DINOv3 7B, frozen | Teacher features / high-compute accuracy branch | Retain only if measured benefit justifies compute |
| DINOv3 natural-image ViT-L | Inspection/UAV transfer comparator | Select separately by branch/domain |
| ConvNeXt/Swin + UPerNet or Mask2Former | Architectural diversity and segmentation control | One bounded comparator; ensemble only complementary errors |
| SAM-family prompting | Annotation assistance and boundary proposal/refinement | Benchmark proposal recall and human corrections; no damage truth inferred from generic masks |
| Prithvi/TerraMind/DOFA | Future modality-specific study | Defer until real matching multispectral/SAR input exists |

A standardized 2026 preprint compares more than 30 methods over 13 datasets and finds foundation models do not consistently dominate. In its Table 11, xBD mIoU is 64.24 for ChangeMamba, 62.48 for natural-image DINOv3-L, and 61.61 for satellite DINOv3-L. These are mIoUs under that study's protocol, not xView2 overall F1. This supports comparing task heads and temporal modeling rather than selecting by model size. [Author's benchmark and code](https://github.com/ChenHongruixuan/AnyDisasterMapping), [author-hosted paper, Table 11](https://chrx97.com/Files/EO4DisasterMapping.pdf).

## 7. Compute strategy

Rough arithmetic for a seven-billion-parameter model: two-byte weights alone require about 14 GB before activations, decoder, workspace and framework overhead. A conventional mixed-precision full Adam training state can approach 112 GB at roughly 16 bytes/parameter, before activations; implementation/sharding changes this. These are planning estimates, not a measured memory profile. Two 16 GB GPUs do not automatically behave as one 32 GB GPU; ordinary data parallelism replicates weights.

| Available resources | Proposed role for 7B | Main training route |
|---|---|---|
| Kaggle-sized GPUs | Optional offline/remote frozen teacher only if a measured workload fits; otherwise defer extraction | ViT-L frozen features, then small adapters/heads; train CNN baseline |
| One 40–80 GB GPU | Profile frozen tiled feature extraction first; consider low-rank adaptation only after memory/timing evidence | ViT-L adaptation plus bounded 7B teacher experiment |
| Multiple large GPUs | Sharded 7B adaptation becomes a candidate | Profile first; retain single-model baseline and full resource accounting |

For the user's Kaggle/Colab-only setup, the proposed execution order is:

1. Create immutable processed-data shards and a single split manifest in persistent storage once; verify checksums when attaching them to later sessions.
2. Measure an assigned GPU's actual memory and compute support. Start with a small complete forward/backward workload at the intended resolution, not just loading weights.
3. Train each candidate across resumable sessions with frequent durable checkpoints. Session boundaries must not restart optimizer schedules or silently reset sampling/random state.
4. If the 7B frozen workload fits, extract training features in restartable shards keyed by model revision, image hash and preprocessing. If it does not fit, lower inference microbatch/crop size only within the declared experiment, consider validated offload, or wait for an actually available larger Colab GPU. Full 7B training is not assumed.
5. Run finalists and distinct seeds as separate jobs; combine probabilities after completion. Account boundaries do not combine hardware, data splits or memory.
6. Spend additional available sessions on rare-class data, target-domain labels, repeated seeds and complementary models. More elapsed time can buy more experiments; it cannot recover invisible defects or create missing GPU memory.

Cache only the features actually needed. Example estimate: 10,000 images × 32×32 tokens × 1,024 channels × two bytes is about 21 GB for one layer; pre/post, more layers and overlap multiply that. A dense teacher cache can become the storage bottleneck. Do not assume BF16 is appropriate for every Kaggle GPU. Record actual dtype, peak VRAM, samples/sec, I/O time, GPU-hours and cost before approving full runs.

## 8. Experimental program with stop/go gates

### Gate A — Restore a valid experiment contract

Future tasks: choose a runnable immutable source revision; reconcile missing package imports; inventory all raw files, splits, masks and checkpoints; record hashes and event/building IDs. Verify the official scorer and local wrapper agree on perfect predictions, all-background, wrong-class, missed-building, false-building, and ignored-label fixtures. Check original/dilated masks are never confused.

Exit: a versioned data/evaluation manifest and a reproducible historical-score audit, or an explicit statement that artifacts are insufficient. Reserve the independent final audit data at this point. Do not spend full training effort before this gate.

### Gate B — Reproduce the bounded baseline

Train one winner-style paired CNN with native-scale crops and fixed compute budget. Compare whole-tile resize against native-scale crop/overlap inference under the same split. Monitor full validation official score, class F1s and event results. Complete one controlled run before adding EMA/SWA/ensembles.

Exit: stable full-validation baseline, saved probabilities, original-label scores and a resolved error taxonomy. Compare initialization, sampling and resolution one variable at a time.

### Gate C — Test DINOv3's actual contribution

Run the following sequence; each row adds one change to a declared parent experiment.

| ID | Experiment | Question |
|---|---|---|
| D0 | Frozen satellite ViT-L + simple dense temporal head | Are pretrained spatial features already useful? |
| D1 | D0 + multiscale feature neck | Does the decoder recover useful spatial structure? |
| D2 | D1 + low-rank or limited-block adaptation | Is task adaptation worth its compute? |
| D3 | D2 + high-resolution CNN detail branch | Does it improve small buildings and intermediate grades? |
| D4 | D3 + learned temporal alignment | Does it reduce registration failures without harming true changes? |
| D5 | Best validated student + approved frozen 7B teacher | Does 7B add measurable transferable information? |
| D6 | Strongest branch + instance consistency supervision | Does it improve building-level reliability without masking mixed defects? |

Start D5 with projected patch-feature distillation from the approved frozen backbone using training imagery only. The generic backbone has no damage-class logits. A separate D5b experiment may train a damage head on its frozen features, or adapt a teacher, before using temperature-scaled class-probability distillation. Budget and evaluate these separately. Teacher predictions are fallible; examine whether they reinforce minor/major errors. No teacher fitting or tuning on held-out test data.

Stop adding complexity when gains disappear across repeated seeds or improve the overall score while degrading important damage recall beyond the predefined tolerance.

### Gate D — Improve data and difficult classes

Inspect an error sample stratified by event, class, building size and visibility. Determine whether each error reflects resolution, bad pairing, registration, ambiguous truth, missed buildings or classification. Request new labels where evidence is resolvable. Compare bounded class-aware sampling and weighted CE/focal plus Dice; then ordinal/contrastive objectives individually. Avoid blindly combining aggressive oversampling with extreme inverse-frequency weights.

Keep healthy roofs, shadows, renovation, construction sites, bare ground, solar panels and vegetation as hard negatives. A genuine unseen target-region set matters more than adding another copy of xBD from a different mirror.

Exit: measurable gains on untouched validation groups, not only a better training curve.

### Gate E — Add detailed damage coverage

Reproduce corrected post-only typology and close-up defect baselines. Add human-labeled roof/facade components and building-specific defects where public data does not cover the requirement. Define annotation instructions with a structural/domain expert, double-label a subset blindly, adjudicate disagreements, and retain uncertain/occluded labels. Use human-reviewed model proposals for annotation speed, not unreviewed pseudo-labels as test truth.

Exit: per-defect metrics on held-out buildings, clear observability limits and no unsupported labels in product output. 3D experiments follow only with calibrated capture and verified cross-view correspondence.

### Gate F — Accuracy finalist and independent evaluation

Use three seeds for finalist comparisons. Select thresholds, checkpoint, crop overlap, TTA and ensemble weights using validation or nested held-out training folds only. The historically inspected xBD test data must be labeled as exposed: a new training run does not make it untouched again. Retain official-test results for transparent benchmark comparability with this disclosure. Before V4 tuning, reserve an additional scene/event-disjoint labeled audit set, checked against all auxiliary data. Freeze everything, evaluate that independent final holdout once, and retain all predictions. If no fresh labeled set is available, independent final generalization remains unverified. If research continues after examining its errors, reserve another untouched audit set.

Report a single-model result and a separate ensemble result. Bootstrap confidence intervals by event/scene or building groups, not millions of correlated pixels. With few events, state that uncertainty estimates are limited. Beating one baseline is a project improvement; a world-record claim requires a verified leaderboard or comprehensive same-protocol independent comparison.

## 9. Metrics and promotion criteria

| Track | Primary metrics | Required breakdown |
|---|---|---|
| Official paired benchmark | Official combined score, localization F1, harmonic damage F1 | Four class F1s; full tile coverage; exact protocol |
| Building instances | Matched-instance AP/F1 and class confusion; missed/double-counted buildings | Building size/density and predicted versus supplied footprints |
| Post-only typology | Macro-F1, all class precision/recall/F1 | Roof versus structural; fragment versus unique-building units |
| Detailed defects | Class IoU/Dice/AP as appropriate; crack boundary/continuity metrics | Defect scale, material, component, occlusion |
| Measurements | Length/area error only where scale and geometry are known | Calibration uncertainty and visible surface coverage |
| Transfer | Event/geography-held-out metrics, worst-event/class performance | Hazard, sensor, resolution and architecture/material |
| Confidence | Calibration error/Brier score and risk versus retained coverage | Abstention rate and severe errors among accepted predictions |
| Resources | GPU-hours, peak memory, throughput and latency | Resolution, TTA, model count and hardware |

Provisional ambition: official combined score above 0.82 is a milestone, not a promise or a world-record certificate. An illustrative target of localization F1 0.90 and harmonic damage F1 0.80 gives 0.83 combined; raising localization alone cannot compensate for a near-zero minor class. Set separate minimum recall requirements and review coverage using the intended response workflow; there is no honest universal target percentage for every defect dataset.

Promote only when the exact primary metric improves with repeatability, class/event regressions are disclosed and within a predefined tolerance, and compute remains feasible. A lower-confidence prediction can be sent for review rather than forced into an intact class. Confidence thresholds are calibrated on validation data; test labels never choose them.

## 10. Notebook redesign specification for later implementation

The next version should have thin notebooks over a versioned package/configuration, not thousands of duplicated training lines. Proposed notebooks:

1. `00_data_and_split_audit`: provenance, completeness, label maps, overlap and duplicate checks.
2. `01_reference_evaluation`: scorer parity and historical checkpoint audit; no model selection on test.
3. `02_paired_cnn_baseline`: one declared baseline recipe.
4. `03_dinov3_paired`: D0–D4 configuration-driven ablations.
5. `04_dinov3_7b_teacher`: measured memory/storage profile, extraction and distillation.
6. `05_post_only_typology`: corrected photo-atomic baseline and transfer study.
7. `06_closeup_defects`: multilabel defect and crack specialists.
8. `07_final_evaluation`: immutable validation-selected recipe, full test report and failure slices.

Each run must record source commit, environment lock, dataset revisions/hashes, split manifest, model revision, input normalization, ignore policy, all seeds, sampler and loss, optimizer/scheduler, augmentation, crop/inference settings, budget/stopping reason, checkpoint selection, resume state and output checksums. Resume must restore optimizer, scheduler, scaler and random states. Training augmentation must transform paired geometry together; photometric changes should be physically plausible and separately ablated. Synthetic smoke samples must never enter benchmark reports.

Memory-bounded caches, deterministic artifact names, resumable execution and persistent output storage are required. Fail on incomplete inputs and unexpected label values rather than silently skipping tiles. Show a planned-versus-processed count for every evaluation. No notebook may choose a best score across different ground-truth definitions.

## 11. Proposed per-building evidence record

The later map/API output should associate a building ID and geometry with input dates/viewpoints, source/model revisions, quality/coverage flags, severity probabilities, damage-type probabilities, visible component/defect masks, measurement uncertainty, review state and evidence image references. Keep reported/observed hazards distinct from inferred ones. Component defects can coexist; whole-building grades remain a separate summary.

This gives the larger RescueVision 2D/3D platform auditable evidence without requiring unrelated rescue-routing, person-tracking or app development in this building-model research phase.

## 12. Remaining decisions and research limits

- The user does not know the identity of the 82% reference. Research found nearby but non-equivalent results; do not ask the user to resolve it or pretend a unique identity was established. Adopt the official metric and named reproducible comparators as the concrete research targets.
- Kaggle/Colab are the available platforms; inspect the actually assigned GPU class and storage before any future run. The user prioritizes accuracy over elapsed time; hardware capacity still determines the viable 7B experiment.
- Confirm the initial target data: paired satellite images, post-only UAV survey, close inspection, or a staged combination. This plan proposes that staged combination.
- The smallest desired defect, target materials/geography and expert annotation access determine whether “detailed damage” can be supervised.
- Source pages and dataset cards were checked, not full data archives. Dataset integrity, permissions and label usability remain acquisition gates.
- Published benchmark numbers were read, not independently reproduced. The large 2026 comparative paper is a preprint, and inaccessible primary-paper leads were excluded from verified conclusions.

Recommended first implementation work, when separately authorized: establish Gate A, then reproduce one CNN baseline and one DINOv3 satellite ViT-L baseline before revising the rest of the notebooks or buying 7B training compute.

## 13. End-to-end implementation and operation through Kaggle MCP

Added 21 October 2026 after inspecting the connected Kaggle MCP tool schemas. **Status: operational plan written; no notebook saved/submitted, GPU session created, dataset uploaded, or training started.** Tool availability proves an interface exists, not that private writes, GPU allocation or downloads will succeed. Prior read-only dataset searches succeeded; notebook execution permissions and assigned hardware remain untested.

Use Kaggle MCP as the orchestration interface, with versioned local Python code and thin submitted notebooks as the execution payload. This section covers the building-model lifecycle from source/data preparation to a locally verifiable inference package; it does not authorize implementation, publication, API deployment, or unrelated platform development.

### 13.1 Tool coverage and real gaps

| Operation | Available MCP tools | Constraint / fallback |
|---|---|---|
| Discover source datasets | `search_datasets`, `get_dataset_metadata`, `list_dataset_files`, `get_dataset_files_summary` | Record owner, slug, version, source terms and expected file counts; search results alone are insufficient |
| Check dataset readiness | `get_dataset_status` | Processing completion is not integrity verification; check mounted content inside the job |
| Discover existing project notebooks | `search_notebooks`, `get_notebook_info`, `list_notebook_files` | Confirm owner/private visibility and immutable source identity before reusing anything |
| Submit code and execute | `save_notebook` | This tool can immediately run code. Use only at the later authorized execution stage |
| Start a session | `create_notebook_session` | Not needed for normal save-and-run orchestration; do not create an extra session for the same job |
| Monitor execution | `get_notebook_session_status` | Use exact owner/slug/version label returned or resolved for the submitted job |
| Enumerate/download results | `list_notebook_session_output`, `download_notebook_output`, `download_notebook_output_zip` | Record session/version identity and verify downloaded checksums; output existence is not an accuracy result |
| Cancel an owned run | `cancel_notebook_session` | Target the recorded session ID; do not cancel unrelated or unidentified jobs |
| Upload dataset bytes | `upload_dataset_file` | Available schema does not establish complete local-file transfer and dataset/version finalization support |
| Create/version a prepared dataset | No corresponding tool exposed in this session | Prefer existing notebook outputs via `kernelDataSources`; if a durable dataset is needed, use a verified official CLI/UI path during authorized execution |
| Configure HF secrets, switch accounts, read live GPU quota | No corresponding tool exposed in this session | Account/secret setup outside MCP; never embed tokens in notebook text or outputs |
| Control Colab | No capability in the Kaggle MCP namespace | Colab is a separate execution fallback with the same artifact contract; no promise of MCP control |

Tool names in this section are short names in the `mcp__kaggle__` namespace. Re-read schemas if availability changes. In particular, do not treat `create_model` as a substitute for uploading/versioning model weights.

### 13.2 Proposed file ownership and interfaces

These are future files to create; none are implemented by this plan:

- `configs/v4/`: dataset adapters, model/experiment configurations and frozen evaluation recipes. Keep secrets out of configurations.
- `src/rescuevision/v4/data_audit.py`: build and validate immutable data/split manifests; each record includes dataset revision, image identity, event/scene/building group, split, paths and label-validity metadata.
- `src/rescuevision/v4/evaluation.py`: official scorer adapter, independent object/defect metrics and complete-coverage reports.
- `src/rescuevision/v4/training.py`: shared train/resume entry point consuming one experiment configuration, one manifest and an optional resume checkpoint; produces a run directory with the contract below.
- `src/rescuevision/v4/models/`: separate paired DINOv3, paired CNN, post-only and defect modules implementing the research gates. Do not restore the removed package wholesale without checking its dependencies and intended scope.
- `src/rescuevision/v4/artifacts.py`: validate run metadata, checkpoint/probability hashes and dependency compatibility before downstream use.
- `scripts/v4_submit_spec.py`: prepare notebook text and the MCP request specification without submitting it. Submission remains an explicit orchestration action.
- `notebooks/kaggle/v4/00_data_and_split_audit.ipynb` through `07_final_evaluation.ipynb`: thin wrappers for the eight stages defined in section 10.
- `tests/v4/`: targeted checks for scorer parity, split overlap, label validity, inference stitching and checkpoint resume. These verify consequential behavior; no notebook-only duplicate test suite.

Every job produces `/kaggle/working/rv4/<run_id>/` with `run_manifest.json`, `metrics.json`, `progress.json`, `artifact_manifest.json`, logs and the stage-specific data/checkpoints/predictions. The run manifest includes source/environment/model/data hashes, parent experiment, seed, resolved configuration, assigned hardware and stopping reason. `artifact_manifest.json` lists byte sizes and SHA-256 hashes. Runtime failure is distinct from an unsuccessful scientific experiment.

### 13.3 Sequential tasks and acceptance gates

**Task K0 — Prepare the reproducible source and evaluation package locally.**

- [ ] Inventory the current missing package/imports and select the smallest deliberate repair scope. Package the chosen code and locked dependencies at an immutable revision.
- [ ] Implement the Gate A scorer and split checks before training code changes; verify expected failures for mismatched scorer semantics, altered evaluation labels, overlapping groups and missing tiles.
- [ ] Define the private notebook source payload, run directory contract and submission specification. Check that no secrets or test-selected recipes enter it.
- [ ] Acceptance: local meaningful checks pass; the exact source/environment artifact is reviewable. Do not submit a GPU job yet.

**Task K1 — Resolve datasets and model access.**

- [ ] Use the dataset discovery tools to resolve complete xBD inputs, supplementary data and intended versions. Inspect metadata/file lists and compare against the canonical source.
- [ ] Keep raw source datasets read-only. Resolve gated HF access through a secret mechanism available to the actual Kaggle runtime; verify access without printing credentials. The approval email is not runtime-authentication proof.
- [ ] If private prepared datasets are necessary, establish the verified CLI/UI upload/finalization path; otherwise plan downstream attachment of preprocessing notebook outputs.
- [ ] Acceptance: all required inputs have identities, expected contents, permitted usage and a documented attachment route. Missing access blocks only the dependent job.

**Task K2 — Submit the CPU data audit/preparation stage.**

- [ ] Call `save_notebook` once with private visibility, explicit source `text`, Python/notebook settings, dataset sources and CPU settings. Use the schema's presence flags where required; use supported values rather than inventing machine-shape names.
- [ ] Record the returned notebook/session/version identity. If the response is ambiguous or times out, inspect `get_notebook_info` and status before retrying to avoid duplicate runs.
- [ ] In the notebook, audit inputs, preserve original labels, construct hashes/manifests, check overlap and produce restartable processed shards. Use native resolution and separate localization/damage validity.
- [ ] Retrieve and inspect the audit report through output-list/download tools. Reject unexplained skips and count mismatches.
- [ ] Acceptance: preprocessing artifacts and independent audit split are validated; no train/test contamination; no GPU training before this passes.

**Task K3 — Submit a GPU capability and correctness smoke job.**

- [ ] Attach the verified preprocessing/source artifacts using supported data-source fields, including `kernelDataSources` for prior notebook outputs when supported by the actual runtime. Verify mounted artifact hashes rather than relying on a mutable slug.
- [ ] Submit a private GPU smoke notebook through `save_notebook` with `enableGpu`, explicit internet setting and a supported assigned machine configuration. Log actual GPU, dtype support, free disk and memory.
- [ ] Exercise real data loading, augmentation, forward/backward, checkpoint save/reload, native-resolution inference and scorer invocation on a small declared subset. Keep synthetic smoke data separately labeled if used.
- [ ] Compare uninterrupted and resumed short training at a declared numerical tolerance; verify optimizer/scheduler/scaler/random-state restoration. Check label/ignore edge cases and tile stitching.
- [ ] Acceptance: the complete miniature path works and the planned workload fits. A successful import or allocated GPU alone does not pass.

**Task K4 — Run the paired CNN baseline to completion.**

- [ ] Submit `02_paired_cnn_baseline` with fixed parent artifacts, seed, configuration and validation-only selection. Save last/best checkpoints and training progress at safe boundaries in the output directory.
- [ ] Bound each job to a measured session workload; do not request an invented unlimited timeout. End cleanly with a resumable checkpoint before expected session exhaustion where feasible.
- [ ] Monitor status at a sensible interval; retrieve available progress artifacts when exposed. MCP does not promise a live stdout stream or durable output from a forcibly killed session.
- [ ] If interrupted, resume from the newest fully persisted, checksum-verified compatible checkpoint in a new version/job. Do not assume temporary disk or an unfinished output is recoverable.
- [ ] Acceptance: complete validation coverage, correct official metric and reproducible checkpoint/probability artifacts. Historical exposed-test comparisons remain explicitly labeled.

**Task K5 — Run the DINOv3 experimental sequence.**

- [ ] Submit D0–D4 sequentially, advancing only after each parent artifact is inspected. Keep all experiment choices and failures in the registry, not just the best result.
- [ ] Profile approved 7B feature extraction separately. If it fits, shard and persist training-only features, then run D5 distillation. If it does not fit, record the hardware failure and continue the valid ViT-L branch; a larger assigned Colab GPU is a conditional fallback, not assumed capacity.
- [ ] Train a task head before any D5b class-probability distillation. Compare student-only and distilled performance under the same protocol.
- [ ] Run three seeds for finalists. Additional sessions fund stronger evidence and model diversity; they do not change split or test-selection rules.
- [ ] Acceptance: validated gain with class/event tradeoffs and resource measurements. No model is promoted solely because it is larger.

**Task K6 — Add the remaining building capabilities in gated increments.**

- [ ] Run corrected post-only typology preparation/training/evaluation, then close-up defect and crack experiments with their own labels/heads/metrics.
- [ ] Acquire expert-reviewed target-building annotations where public labels are insufficient. Missing annotations are not negative examples.
- [ ] Add 3D association only after camera geometry, scale, registration and surface coverage are available and verified.
- [ ] Acceptance: per-capability held-out metrics, data provenance and explicit observability limits. Success on xBD does not substitute for these checks.

**Task K7 — Freeze and evaluate the final candidate.**

- [ ] Produce an immutable evaluation configuration containing checkpoint hashes, validation-selected thresholds/calibration, TTA, overlap and ensemble weights.
- [ ] Submit the final evaluation notebook with no training or recipe search. Evaluate the official comparison track and separate fresh audit track with appropriate prior-exposure disclosure.
- [ ] Check planned/processed counts, original target identities, class/event results, uncertainty and single-model versus ensemble outcomes.
- [ ] Acceptance: complete metrics/probabilities and reproducible evidence. Scores above 0.82 remain measured project results, not automatically a world-record claim.

**Task K8 — Collect, package and verify local inference.**

- [ ] Enumerate the completed session's outputs and download selected checkpoints, configurations, reports and manifests through MCP. Use ZIP retrieval only when the selected artifact volume makes it practical.
- [ ] Verify hashes and load the finalized inference package in a clean supported environment. Reproduce predictions/metrics on fixed reference inputs within the declared tolerance.
- [ ] Deliver weights, preprocessing/label contracts, inference instructions, model card, benchmark report and failure examples. Preserve per-building evidence for the future 2D/3D platform.
- [ ] Acceptance: locally verifiable inference package and traceable results. Deployment, public publishing and competition submission are separate actions and are not part of the current authorization.

### 13.4 Job lifecycle, recovery and monitoring contract

Maintain a local registry with one record per experiment attempt: `run_id`, parent IDs, source/data/config/model hashes, owner, slug, version label, session ID, submitted/observed times, state and retrieved artifact hashes. Use logical states `prepared → submitted → running → completed → artifacts_verified → scientifically_reviewed`; add `failed`, `cancelled` and `blocked_input` with reasons. These are our registry states, not assumed literal Kaggle API response values.

Before submitting a dependent stage, require both completion and artifact verification. A status timeout means unknown state, not failure or permission to duplicate the job. Inspect before resubmitting. After out-of-memory failure, change the microbatch/accumulation policy explicitly, update the experiment identity and preserve the parent failure. A new session must verify inputs and checkpoint compatibility again. Never auto-relaunch indefinitely or train on a different split to make a run pass.

Long-lived monitoring is not established merely by this document or by an active chat. If later requested, configure a supported follow-up mechanism to query status and notify on meaningful completion/failure/action needs, keeping unchanged states quiet. No such monitor was created here.

### 13.5 Implementation readiness verdict

The source/data/model/evaluation sequence and its MCP operations are now planned end to end. **It is not an MCP-only guarantee:** dataset/version publication, secret setup, account switching, Colab control, current GPU allocation and live logs have explicit gaps or runtime checks. Execution begins only after the user's separate implementation instruction, starting with K0–K3 rather than an expensive full training submission.
