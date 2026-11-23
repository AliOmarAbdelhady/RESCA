# Tier 1 Papers: Summaries

Summaries of the seven most important papers for RescueVision (ranks 1–7 in [research_papers.md](research_papers.md)). Each one explains what the paper is about, its key idea, its main result, how RescueVision uses it and what it does not solve. Citations use IEEE numeric style; the full references are at the end.

> These summaries were written from knowledge of the papers and the model settings in `configs/`. Check each number against the original paper before submitting the report.

## At a glance

| Rank | Paper | Used in RescueVision for | Config file(s) |
|---|---|---|---|
| 1 | U-Net [1] | Building segmentation, damage segmentation, change detection | `building_seg_unet.yaml`, `damage_seg_unet_6ch.yaml`, `change_siamese_unet.yaml` |
| 2 | ResNet [2] | ResNet34 encoder for the building U-Net, Siamese U-Net and ChangeFormer | `building_seg_unet.yaml`, `change_siamese_unet.yaml`, `changeformer_xbd.yaml` |
| 3 | EfficientNet [3] | EfficientNet-B3 encoder for the 6-channel damage U-Net and the crop classifier | `damage_seg_unet_6ch.yaml`, `efficientnet_damage_classifier.yaml` |
| 4 | DINOv3 [4] | Frozen DINOv3 backbone for the per-building damage classifier (config still loads DINOv2) | `dinov2_damage_classifier.yaml` |
| 5 | SegFormer [5] | SegFormer-B2/B3 for FloodNet, building and damage segmentation | `floodnet_segformer.yaml`, `segformer_building.yaml`, `segformer_damage.yaml` |
| 6 | Attention Is All You Need [6] | The Transformer behind SegFormer, DINOv3 and ChangeFormer | (indirect) |
| 7 | FCN [7] | The idea of pixel-level prediction that all segmentation models follow | (indirect) |

---

## 1. U-Net: Convolutional Networks for Biomedical Image Segmentation

**Reference:** Ronneberger, Fischer and Brox, MICCAI 2015 [1].

**What it's about.** U-Net is a network that labels every pixel of an image. It was designed for medical images, where only a few labelled examples are available.

**Key idea.** The network has a U shape. An encoder shrinks the image step by step to learn *what* is in it. A decoder enlarges it back to full size to recover *where* things are. **Skip connections** copy detailed features from each encoder level straight across to the matching decoder level, so fine boundaries are not lost. Heavy data augmentation (including elastic deformations) lets the network learn from very few training images.

**Main result.** U-Net won the ISBI 2015 cell-tracking challenge by a large margin. It needed only a few dozen training images and segmented a 512×512 image in under a second on a GPU [1].

**How RescueVision uses it.** U-Net is the main architecture of the project:

- building segmentation from the pre-disaster image (3 channels, ResNet34 encoder);
- damage segmentation from the pre and post images stacked together (6 channels, EfficientNet-B3 encoder, 5 classes);
- a Siamese version for change detection, which runs both images through shared encoders.

Building outlines need sharp boundaries, so the skip connections matter directly for RescueVision's building masks.

**What it does not solve.** U-Net was not designed for satellite images or for comparing two dates. RescueVision adapts it by stacking the before/after images (6 channels) or using a Siamese design. Its accuracy on a new disaster still depends on how similar that disaster is to the training data (xBD [8]).

---

## 2. Deep Residual Learning for Image Recognition (ResNet)

**Reference:** He, Zhang, Ren and Sun, CVPR 2016 [2].

**What it's about.** Before ResNet, adding more layers to a network often made it *worse*, even on training data (the "degradation problem"). ResNet made very deep networks trainable.

**Key idea.** Each block learns a **residual**: only the change it needs to add to its input. A shortcut connection adds the input back to the block's output (*output = F(x) + x*). If a layer is not useful, it can learn to pass its input through unchanged, so extra depth no longer hurts.

**Main result.** The paper trained networks of up to 152 layers on ImageNet. An ensemble reached 3.57% top-5 error and won the ILSVRC 2015 classification challenge [2].

**How RescueVision uses it.** ResNet34, pretrained on ImageNet, is the encoder of:

- the building segmentation U-Net;
- the Siamese U-Net for change detection;
- the ChangeFormer change-detection configuration.

Starting from ImageNet weights means the encoder already recognises edges, textures and shapes. This shortens training on xBD.

**What it does not solve.** ResNet was trained on everyday ground-level photos, not overhead imagery. Its pretrained features are a starting point and must be fine-tuned on satellite data.

---

## 3. EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks

**Reference:** Tan and Le, ICML 2019 [3].

**What it's about.** Networks are usually made bigger by adding depth, width or input resolution, one at a time and by trial and error. EfficientNet asks how to scale all three together.

**Key idea.** **Compound scaling** grows depth, width and resolution together using fixed ratios. The authors first found a small, efficient base network (EfficientNet-B0) with automated architecture search, then scaled it up into a family from B0 to B7.

**Main result.** EfficientNet-B7 reached 84.3% top-1 accuracy on ImageNet while being 8.4 times smaller and 6.1 times faster than the best previous network [3]. Smaller versions gave strong accuracy for far less computation.

**How RescueVision uses it.** EfficientNet-B3, pretrained on ImageNet, is used as:

- the encoder of the 6-channel damage segmentation U-Net;
- the backbone of the per-building damage classifier (4 classes), as an alternative to DINOv3.

B3 is a practical middle size: accurate enough for damage levels, small enough to train on a Kaggle GPU.

**What it does not solve.** EfficientNet's pretrained weights expect 3-channel RGB input. For the 6-channel before/after input, the first layer has to be adapted, so part of the pretrained knowledge is not used directly.

---

## 4. DINOv3

**Reference:** Siméoni et al., Meta AI, arXiv 2025 [4].

**What it's about.** DINOv3 is a "foundation" image model from Meta: a Vision Transformer trained without any human labels so that its features work for many tasks out of the box. It is the successor to DINOv2, scaled up in model size and training data.

**Key idea.** The model learns by **self-supervision**: it teaches itself to give consistent features for different views of the same image. Training very large models for a long time normally makes their pixel-level (dense) features degrade. DINOv3 adds **Gram anchoring**, a training step that keeps those dense features stable [4]. The large model is then distilled into smaller ones that can be used **frozen**, with only a small classifier trained on top.

**Main result.** The authors report that frozen DINOv3 features outperform earlier self-supervised and weakly supervised models across many benchmarks, with the largest gains on dense tasks such as segmentation [4]. Meta also released versions pretrained on **SAT-493M**, a set of 493 million satellite images from Maxar at 0.6 m resolution [4].

**How RescueVision uses it.** The per-building damage classifier uses a frozen self-supervised backbone with a small MLP head that predicts 4 damage levels from building crops. This makes training fast and reduces overfitting when labelled damage examples are limited. The satellite-pretrained DINOv3 versions are a closer match to xBD imagery than models trained only on everyday photos.

> **Note:** `configs/dinov2_damage_classifier.yaml` still loads `facebook/dinov2-base`. Update the config to a DINOv3 checkpoint before reporting DINOv3 results.

**What it does not solve.** Satellite pretraining is not damage-specific, so frozen features may still miss subtle damage signs. The largest DINOv3 models are also heavy to run. Comparing a DINOv3 version against the fine-tuned EfficientNet classifier on the same xBD crops would show whether the switch helps.

---

## 5. SegFormer: Simple and Efficient Design for Semantic Segmentation with Transformers

**Reference:** Xie et al., NeurIPS 2021 [5].

**What it's about.** SegFormer is a segmentation model that uses a Transformer encoder instead of a CNN while staying light and fast.

**Key idea.** Two choices make it simple:

- a **hierarchical Transformer encoder** (Mix Transformer) that produces features at several scales and needs no positional encoding, so it handles image sizes different from training;
- a **lightweight all-MLP decoder** that combines those multi-scale features without complex modules.

**Main result.** SegFormer gave better accuracy than previous methods with far fewer parameters. The largest version (B5) reached 84.0% mIoU on the Cityscapes validation set, and it was more robust to image corruptions than CNN-based models [5].

**How RescueVision uses it.** SegFormer is used for:

- FloodNet segmentation (10 classes), with `segformer-b2` pretrained on ADE20K;
- alternative building segmentation (B2, 2 classes) and damage segmentation (B3, 5 classes, 6-channel input) on xBD.

This allows a direct comparison between CNN-based U-Nets and a Transformer-based segmenter on the same data.

**What it does not solve.** The pretrained weights come from street-level and indoor scenes (Cityscapes, ADE20K). Drone flood imagery looks very different, and FloodNet covers a single hurricane, so results may not transfer to other disaster types [9].

---

## 6. Attention Is All You Need

**Reference:** Vaswani et al., NeurIPS 2017 [6].

**What it's about.** This paper introduced the **Transformer**, a network that processes data using attention alone, without recurrence or convolution. It was first applied to machine translation.

**Key idea.** **Self-attention** lets every element in the input look at every other element and decide how much to weigh it. **Multi-head attention** runs several of these in parallel to capture different relationships. **Positional encoding** adds order information. Because there is no step-by-step recurrence, training parallelises well on GPUs.

**Main result.** The Transformer set new state-of-the-art translation scores (28.4 BLEU on English–German) at a fraction of the training cost of earlier models [6].

**How RescueVision uses it.** Indirectly, but fundamentally. Three model families in the project are Transformers:

- **SegFormer** (segmentation);
- **DINOv3** (building damage classifier, a Vision Transformer);
- **ChangeFormer** (change detection).

This paper is the reason those models exist and should be cited when explaining them.

**What it does not solve.** Self-attention cost grows with the square of the number of input elements, which is expensive for large images. Image models such as SegFormer add designs (hierarchical, reduced attention) specifically to manage this.

---

## 7. Fully Convolutional Networks for Semantic Segmentation (FCN)

**Reference:** Long, Shelhamer and Darrell, CVPR 2015 [7].

**What it's about.** FCN showed how to turn an image classification network into one that predicts a label for **every pixel**, trained end to end.

**Key idea.**

- Replace the final fully connected layers with convolutions, so the network accepts any image size and outputs a map instead of a single label.
- **Upsample** the coarse output back to full resolution with learned layers.
- Use **skip connections** that combine deep, coarse features (what) with shallow, fine ones (where).

**Main result.** FCN improved PASCAL VOC 2012 segmentation to 62.2% mean IoU, a 20% relative improvement over earlier methods, while running much faster [7].

**How RescueVision uses it.** Indirectly. Every segmentation model in the project (U-Net, Siamese U-Net, SegFormer) follows the FCN idea of a dense, pixel-level output trained end to end. U-Net extends FCN's skip connections into a full symmetric decoder.

**What it does not solve.** FCN's outputs are coarse around object edges. Later designs, including U-Net, were created to recover sharper boundaries, which matter for building outlines.

---

## How the seven papers connect

- **FCN [7]** introduced pixel-level prediction → **U-Net [1]** refined it with a symmetric decoder and skip connections.
- **ResNet [2]** and **EfficientNet [3]** provide the pretrained CNN encoders inside RescueVision's U-Nets.
- **Attention Is All You Need [6]** introduced the Transformer → **SegFormer [5]** and **DINOv3 [4]** apply it to images.
- RescueVision uses both lines (CNN U-Nets and Transformers), so the report can compare them on the same xBD [8] and FloodNet [9] data.

## References

[1] O. Ronneberger, P. Fischer, and T. Brox, "U-Net: Convolutional networks for biomedical image segmentation," in *Medical Image Computing and Computer-Assisted Intervention (MICCAI)*, LNCS vol. 9351, Springer, 2015, pp. 234–241, doi: 10.1007/978-3-319-24574-4_28. [Online]. Available: https://arxiv.org/abs/1505.04597

[2] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in *Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 770–778, doi: 10.1109/CVPR.2016.90. [Online]. Available: https://arxiv.org/abs/1512.03385

[3] M. Tan and Q. V. Le, "EfficientNet: Rethinking model scaling for convolutional neural networks," in *Proc. 36th Int. Conf. Machine Learning (ICML)*, PMLR vol. 97, 2019, pp. 6105–6114. [Online]. Available: https://arxiv.org/abs/1905.11946

[4] O. Siméoni et al., "DINOv3," arXiv:2508.10104, 2025. [Online]. Available: https://arxiv.org/abs/2508.10104

[5] E. Xie, W. Wang, Z. Yu, A. Anandkumar, J. M. Alvarez, and P. Luo, "SegFormer: Simple and efficient design for semantic segmentation with transformers," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 34, 2021, pp. 12077–12090. [Online]. Available: https://arxiv.org/abs/2105.15203

[6] A. Vaswani et al., "Attention is all you need," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, 2017, pp. 5998–6008. [Online]. Available: https://arxiv.org/abs/1706.03762

[7] J. Long, E. Shelhamer, and T. Darrell, "Fully convolutional networks for semantic segmentation," in *Proc. IEEE Conf. Computer Vision and Pattern Recognition (CVPR)*, 2015, pp. 3431–3440, doi: 10.1109/CVPR.2015.7298965. [Online]. Available: https://arxiv.org/abs/1411.4038

[8] R. Gupta et al., "xBD: A dataset for assessing building damage from satellite imagery," arXiv:1911.09296, 2019. [Online]. Available: https://arxiv.org/abs/1911.09296

[9] M. Rahnemoonfar, T. Chowdhury, A. Sarkar, D. Varshney, M. Yari, and R. R. Murphy, "FloodNet: A high resolution aerial imagery dataset for post flood scene understanding," *IEEE Access*, vol. 9, pp. 89644–89654, 2021, doi: 10.1109/ACCESS.2021.3090981. [Online]. Available: https://arxiv.org/abs/2012.02951
