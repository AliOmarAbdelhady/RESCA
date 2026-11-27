# Research Papers for RescueVision

Foundational deep learning papers behind the models and methods used in RescueVision, ranked by importance to the project (1 = most important).

> Links have not been checked yet. Open each one to confirm the title and authors before citing it in the report.

## Tier 1: Core (must cite; the models are built on these)

| Rank | Paper name | Link | Where it's useful (what it's about) |
|---|---|---|---|
| 1 | U-Net: Convolutional Networks for Biomedical Image Segmentation (2015) | [arxiv.org/abs/1505.04597](https://arxiv.org/abs/1505.04597) | The architecture of the building segmentation, damage segmentation and Siamese change models |
| 2 | Deep Residual Learning for Image Recognition (ResNet, 2015) | [arxiv.org/abs/1512.03385](https://arxiv.org/abs/1512.03385) | ResNet34 is the encoder in the building U-Net and Siamese U-Net |
| 3 | EfficientNet: Rethinking Model Scaling for CNNs (2019) | [arxiv.org/abs/1905.11946](https://arxiv.org/abs/1905.11946) | Backbone of the 6-channel damage U-Net and the damage classifier |
| 4 | DINOv3 (Siméoni et al., 2025) | [arxiv.org/abs/2508.10104](https://arxiv.org/abs/2508.10104) | Feature extractor for the per-building damage classifier; has a version pretrained on satellite imagery |
| 5 | SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers (2021) | [arxiv.org/abs/2105.15203](https://arxiv.org/abs/2105.15203) | The FloodNet segmentation model |
| 6 | Attention Is All You Need (Vaswani et al., 2017) | [arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762) | Introduced the Transformer, which SegFormer, ChangeFormer and DINOv3 are built on |
| 7 | Fully Convolutional Networks for Semantic Segmentation (FCN, 2015) | [arxiv.org/abs/1411.4038](https://arxiv.org/abs/1411.4038) | The first deep network to label every pixel; the basis for all the segmentation models |

## Tier 2: Strong support (explain design choices and evaluation)

| Rank | Paper name | Link | Where it's useful (what it's about) |
|---|---|---|---|
| 8 | Focal Loss for Dense Object Detection (RetinaNet, 2017) | [arxiv.org/abs/1708.02002](https://arxiv.org/abs/1708.02002) | Loss for imbalanced classes; useful because "destroyed" is rare in xBD |
| 9 | V-Net (Dice loss, 2016) | [arxiv.org/abs/1606.04797](https://arxiv.org/abs/1606.04797) | Dice loss for segmentation with imbalanced classes |
| 10 | An Image is Worth 16x16 Words (Vision Transformer, 2020) | [arxiv.org/abs/2010.11929](https://arxiv.org/abs/2010.11929) | Applied Transformers to images; the backbone type of DINOv3 |
| 11 | How Transferable Are Features in Deep Neural Networks? (2014) | [arxiv.org/abs/1411.1792](https://arxiv.org/abs/1411.1792) | Explains transfer learning from ImageNet weights, which the training relies on |
| 12 | YOLOv4: Optimal Speed and Accuracy of Object Detection (2020) | [arxiv.org/abs/2004.10934](https://arxiv.org/abs/2004.10934) | The detector the SARD paper chose for people in search-and-rescue images |
| 13 | Dropout as a Bayesian Approximation (Gal & Ghahramani, 2015) | [arxiv.org/abs/1506.02142](https://arxiv.org/abs/1506.02142) | Estimates model uncertainty; supports "confidence / needs verification" flags |
| 14 | Billion-scale Similarity Search with GPUs (FAISS, 2017) | [arxiv.org/abs/1702.08734](https://arxiv.org/abs/1702.08734) | The library behind the "similar past cases" search |
| 15 | Grad-CAM: Visual Explanations from Deep Networks (2016) | [arxiv.org/abs/1610.02391](https://arxiv.org/abs/1610.02391) | Shows which image areas drove a damage prediction; explainability for responders |
| 16 | Adam: A Method for Stochastic Optimization (2014) | [arxiv.org/abs/1412.6980](https://arxiv.org/abs/1412.6980) | The optimiser used to train the models |

## Tier 3: Useful (comparisons, alternatives, future work)

| Rank | Paper name | Link | Where it's useful (what it's about) |
|---|---|---|---|
| 17 | Encoder-Decoder with Atrous Separable Convolution (DeepLabv3+, 2018) | [arxiv.org/abs/1802.02611](https://arxiv.org/abs/1802.02611) | A standard segmentation baseline to compare the U-Net against |
| 18 | DETRs Beat YOLOs on Real-time Object Detection (RT-DETR, 2023) | [arxiv.org/abs/2304.08069](https://arxiv.org/abs/2304.08069) | Alternative person detector named in the research plan |
| 19 | Faster R-CNN (2015) | [arxiv.org/abs/1506.01497](https://arxiv.org/abs/1506.01497) | Classic two-stage person detector; one of the detectors the SARD paper compared |
| 20 | You Only Look Once (YOLO, 2015) | [arxiv.org/abs/1506.02640](https://arxiv.org/abs/1506.02640) | Real-time detection; basis for victim detection on drones |
| 21 | Feature Pyramid Networks for Object Detection (2016) | [arxiv.org/abs/1612.03144](https://arxiv.org/abs/1612.03144) | Multi-scale features for small objects such as people in drone images |
| 22 | Emerging Properties in Self-Supervised Vision Transformers (DINO, 2021) | [arxiv.org/abs/2104.14294](https://arxiv.org/abs/2104.14294) | Self-supervised learning method that DINOv3 builds on |
| 23 | Masked-attention Mask Transformer (Mask2Former, 2021) | [arxiv.org/abs/2112.01527](https://arxiv.org/abs/2112.01527) | Planned option in the research plan for post-only segmentation |
| 24 | Segment Anything (SAM, 2023) | [arxiv.org/abs/2304.02643](https://arxiv.org/abs/2304.02643) | Foundation model that could outline buildings with little training |

## Tier 4: Background only (cite if there is room)

| Rank | Paper name | Link | Where it's useful (what it's about) |
|---|---|---|---|
| 25 | Swin Transformer (2021) | [arxiv.org/abs/2103.14030](https://arxiv.org/abs/2103.14030) | Transformer backbone for large images; an alternative encoder for segmentation |
| 26 | End-to-End Object Detection with Transformers (DETR, 2020) | [arxiv.org/abs/2005.12872](https://arxiv.org/abs/2005.12872) | Transformer-based detection; background for RT-DETR |
| 27 | Batch Normalization (2015) | [arxiv.org/abs/1502.03167](https://arxiv.org/abs/1502.03167) | Training-stability technique used inside ResNet and EfficientNet |
| 28 | ImageNet Classification with Deep Convolutional Neural Networks (AlexNet, 2012) | [papers.nips.cc](https://papers.nips.cc/paper/4824-imagenet-classification-with-deep-convolutional-neural-networks) | Started modern deep learning for images; background for the introduction |
