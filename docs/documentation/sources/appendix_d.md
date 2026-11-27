<!-- Appendix D, Literature Review Shortlist and Search Log. Owner: Person 2 (Bela). Built by tools/build_report.py. -->
Table D-1 keeps the priority order of the team’s ranked list of 28 candidate papers. Tier 1 papers inform the comparison in Table 2-1, and the detectors of Table 2-2 are cited where they are discussed. Rows without a reference number are candidate reading for the planned evaluation and are not cited in this report. Rank reflects relevance to the project, not quality.

Table: Table D-1: Ranked research shortlist
| Rank / tier | Paper | Relevance to RescueVision |
| 1 / 1 | U-Net: Convolutional Networks for Biomedical Image Segmentation (2015) [@unet] | Building and paired-image damage segmentation |
| 2 / 1 | Deep Residual Learning for Image Recognition (ResNet, 2015) [@resnet] | Residual encoder for segmentation and change detection |
| 3 / 1 | EfficientNet: Rethinking Model Scaling for CNNs (2019) [@efficientnet] | Efficient encoder and building-crop classifier |
| 4 / 1 | DINOv3 (2025) [@dinov3] | Candidate self-supervised image backbone with satellite-pretrained versions |
| 5 / 1 | SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers (2021) [@segformer] | Transformer-based semantic segmentation |
| 6 / 1 | Attention Is All You Need (2017) [@transformer] | Attention-based architecture behind the Transformer models |
| 7 / 1 | Fully Convolutional Networks for Semantic Segmentation (FCN, 2015) [@fcn] | Dense pixel-level prediction |
| 8 / 2 | Focal Loss for Dense Object Detection (RetinaNet, 2017) [@focalloss] | Loss for imbalanced classes; candidate because “destroyed” buildings are rare in xBD |
| 9 / 2 | V-Net (Dice loss, 2016) | Candidate: Dice loss for segmentation with imbalanced classes |
| 10 / 2 | An Image is Worth 16x16 Words (Vision Transformer, 2020) | Candidate: the backbone type of the DINO models |
| 11 / 2 | How Transferable Are Features in Deep Neural Networks? (2014) | Candidate: transfer learning from ImageNet weights, which the planned training relies on |
| 12 / 2 | YOLOv4: Optimal Speed and Accuracy of Object Detection (2020) [@yolov4] | The detector chosen in the SARD study for people in search-and-rescue images |
| 13 / 2 | Dropout as a Bayesian Approximation (Gal and Ghahramani, 2015) | Candidate: estimates model uncertainty for “needs verification” flags |
| 14 / 2 | Billion-scale Similarity Search with GPUs (FAISS, 2017) | Candidate: similarity search for comparable past incidents |
| 15 / 2 | Grad-CAM: Visual Explanations from Deep Networks (2016) | Candidate: shows which image areas drove a damage prediction |
| 16 / 2 | Adam: A Method for Stochastic Optimization (2014) | Candidate optimiser for the planned training |
| 17 / 3 | Encoder-Decoder with Atrous Separable Convolution (DeepLabv3+, 2018) | Candidate segmentation baseline to compare with U-Net |
| 18 / 3 | DETRs Beat YOLOs on Real-time Object Detection (RT-DETR, 2024) [@rtdetr] | Alternative real-time person detector |
| 19 / 3 | Faster R-CNN (2015) [@fasterrcnn] | Two-stage detector compared in the SARD study |
| 20 / 3 | You Only Look Once (YOLO, 2015) | Candidate: origin of single-pass real-time detection |
| 21 / 3 | Feature Pyramid Networks for Object Detection (2016) | Candidate: multi-scale features for small people in drone images |
| 22 / 3 | Emerging Properties in Self-Supervised Vision Transformers (DINO, 2021) | Candidate: the method the DINOv2 and DINOv3 models build on |
| 23 / 3 | Masked-attention Mask Transformer (Mask2Former, 2021) | Candidate for post-event-only segmentation |
| 24 / 3 | Segment Anything (SAM, 2023) | Candidate for outlining buildings with little training |
| 25 / 4 | Swin Transformer (2021) | Candidate alternative encoder for segmentation |
| 26 / 4 | End-to-End Object Detection with Transformers (DETR, 2020) | Background for RT-DETR |
| 27 / 4 | Batch Normalization (2015) | Background: training-stability technique inside ResNet and EfficientNet |
| 28 / 4 | ImageNet Classification with Deep Convolutional Neural Networks (AlexNet, 2012) | Background: the start of modern deep learning for images |

Table D-2 records the searches behind Chapter 2. Each source was then checked against its publisher, DOI or official page before it was accepted.

Table: Table D-2: Literature search log
| Date | Search terms | Source searched | Selected | Reason for selection |
| 23 Nov. 2026 | situation awareness dynamic systems; common operational picture sensemaking | Web search, then SAGE, Wiley and university repository | [@endsley], [@wolbers] | Theory of how responders understand displayed information |
| 23 Nov. 2026 | satellite image analysis crisis management; Copernicus EMS rapid mapping products | Web search, then IEEE, DLR and Copernicus EMS | [@voigt], [@copernicus] | Peer-reviewed and official descriptions of operational damage mapping |
| 23 Nov. 2026 | damage mapping accuracy 2006 Indonesia; collaborative damage mapping cognitive systems engineering | Web search, then dblp and NHESS | [@kerle2010], [@kerlehoffman] | Evidence that damage maps can be wrong and must fit users’ tasks |
| 23 Nov. 2026 | SensePlace2 geovisual analytics situational awareness | Web search, then IEEE VAST | [@senseplace] | An evaluated interactive crisis map |
| 23 Nov. 2026 | xBD building damage dataset; earthquake damage remote sensing survey | Web search, then CVF, arXiv and University of Pavia | [@xbd], [@dellacqua] | Main dataset and background survey for damage mapping |
| 23 Nov. 2026 | Siamese change detection; xView2 multi-temporal fusion; CNN damage detection operational conditions | Web search, then arXiv, HAL and MDPI | [@daudt], [@weber], [@nex] | Methods the design uses and the main caution on transfer |
| 23 Nov. 2026 | FloodNet; RescueNet UAV dataset | Web search, then IEEE Access, Scientific Data and arXiv | [@floodnet], [@rescuenet] | Drone datasets used or planned by the project |
| 23 Nov. 2026 | 3D point cloud damage detection oblique; UAV damage object-based analysis; SfM georectified mosaics; OpenDroneMap accuracy | Web search, then ISPRS, NHESS, MDPI and OpenDroneMap | [@vetrivel], [@galarreta], [@turner], [@odm] | Evidence for 3D analysis and map accuracy limits |
| 23 Nov. 2026 | social media mass emergency survey; Ushahidi crowdsourcing crisis information | Web search, then ACM, arXiv and IIED | [@imran], [@okolloh] | The self-reporting channel for people needing help |
| 23 Nov. 2026 | UAV disaster management; SARD person detection; UAV human detection search and rescue; VisDrone; UAV target geolocation | Web search, then IEEE, MDPI and arXiv | [@erdelj], [@sard], [@lygouras], [@visdrone], [@liu] | Detection, tracking and location of people from the air |
| 23 Nov. 2026 | radar under rubble breathing detection | Web search, then MIT Lincoln Laboratory | [@murmur] | Why buried people need specialist sensors |
| 23 Nov. 2026 | blocked roads earthquake satellite; flood road network risk; emergency logistics path selection; A\*; D\* Lite | Web search, then ISPRS, Journal of Hydrology, Elsevier, IEEE and CMU | [@rastiveis], [@yin], [@yuanwang], [@astar], [@dstarlite] | Hazards to movement and routing methods |
| 23 Nov. 2026 | crisis management cognition coordination; multi-agency information sharing obstacles | Web search, then Wiley and Springer | [@comfort], [@bharosa] | Why coordination between agencies fails |
| 23 Nov. 2026 | Sahana; HOT Tasking Manager; INSARAG Guidelines 2020; International Charter; Ushahidi features | Web search, then IEEE and official websites | [@sahana], [@hot], [@insarag], [@charter], [@ushahidi] | Official descriptions of comparable systems |
| 27 Nov. 2026 | natural hazard interactions review; multi-hazard risk challenges; floodwater downed power lines | Web search, then Reviews of Geophysics, Springer and CDC | [@gillmalamud], [@kappes], [@cdcflood] | Evidence for the compound hazard feature F5 |
| 27 Nov. 2026 | Hazus earthquake technical manual repair cost | Web search, then FEMA | [@hazus] | Reference method for the restoration cost feature F1 |
| 27 Nov. 2026 | Faster R-CNN; focal loss; YOLOv4; RT-DETR | Web search, then NeurIPS, CVF and arXiv | [@fasterrcnn], [@focalloss], [@yolov4], [@rtdetr] | Detector families compared in Table 2-2 |

Two candidates were not used: an arXiv paper on road segmentation with OpenStreetMap routing whose identifier could not be confirmed, and ground-penetrating radar studies, because [@murmur] already supports the point on buried people.
