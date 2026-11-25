"""Paired CNN baseline with shared before/after feature extraction."""

from __future__ import annotations

import torch
from torch import Tensor, nn
from torch.nn import functional as F
from torchvision.models import resnet34


class _TinyEncoder(nn.Module):
    def __init__(self, base_channels: int) -> None:
        super().__init__()
        self.out_channels = base_channels * 4
        self.net = nn.Sequential(
            nn.Conv2d(3, base_channels, 3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_channels, base_channels * 2, 3, stride=2, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(base_channels * 2, self.out_channels, 3, stride=2, padding=1),
            nn.ReLU(inplace=True),
        )

    def forward(self, image: Tensor) -> Tensor:
        return self.net(image)


class _ResNet34Encoder(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        backbone = resnet34(weights=None)
        self.out_channels = 512
        self.features = nn.Sequential(
            backbone.conv1,
            backbone.bn1,
            backbone.relu,
            backbone.maxpool,
            backbone.layer1,
            backbone.layer2,
            backbone.layer3,
            backbone.layer4,
        )

    def forward(self, image: Tensor) -> Tensor:
        return self.features(image)


class PairedCNN(nn.Module):
    """Shared encoder, temporal concatenation/difference and dense heads.

    ``backbone="resnet34"`` is the declared baseline.  ``backbone="tiny"``
    is intentionally available for deterministic CPU tests and smoke runs; it
    is never a benchmark recipe.
    """

    def __init__(
        self,
        *,
        backbone: str = "resnet34",
        base_channels: int = 16,
        head_channels: int = 128,
    ) -> None:
        super().__init__()
        if backbone == "resnet34":
            self.encoder = _ResNet34Encoder()
        elif backbone == "tiny":
            self.encoder = _TinyEncoder(base_channels)
        else:
            raise ValueError(f"unsupported CNN backbone: {backbone!r}")
        channels = self.encoder.out_channels
        self.fusion = nn.Sequential(
            nn.Conv2d(channels * 3, head_channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(head_channels, head_channels, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
        )
        self.localization_head = nn.Conv2d(head_channels, 1, kernel_size=1)
        self.damage_head = nn.Conv2d(head_channels, 4, kernel_size=1)
        self.backbone_name = backbone

    def forward(self, pre: Tensor, post: Tensor) -> dict[str, Tensor]:
        if pre.ndim != 4 or post.ndim != 4:
            raise ValueError("pre and post must be BCHW tensors")
        if pre.shape != post.shape:
            raise ValueError("pre and post must have identical shapes")
        pre_features = self.encoder(pre)
        post_features = self.encoder(post)
        fused = torch.cat(
            [pre_features, post_features, torch.abs(post_features - pre_features)], dim=1
        )
        fused = self.fusion(fused)
        loc_logits = self.localization_head(fused)
        damage_logits = self.damage_head(fused)
        output_size = pre.shape[-2:]
        return {
            "loc_logits": F.interpolate(
                loc_logits, size=output_size, mode="bilinear", align_corners=False
            ),
            "damage_logits": F.interpolate(
                damage_logits, size=output_size, mode="bilinear", align_corners=False
            ),
        }
