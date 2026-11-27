"""Post-event-only typology adapter and classification head."""

from __future__ import annotations

from collections.abc import Sequence

import torch
from torch import Tensor, nn

from ..task_adapters import TaskAdapterError


POST_ONLY_CLASSES = (
    "undamaged",
    "partial_roof",
    "total_roof",
    "partial_structural",
    "total_collapse",
)


class PostOnlyLabelError(TaskAdapterError):
    """Raised when a post-only typology label is missing or from another ontology."""


_LABEL_ALIASES = {
    "undamaged": 0,
    "no-visible-damage": 0,
    "no-damage-visible": 0,
    "intact": 0,
    "partial-roof": 1,
    "partial-roof-damage": 1,
    "total-roof": 2,
    "total-roof-damage": 2,
    "partial-structural": 3,
    "partial-structural-damage": 3,
    "total-collapse": 4,
    "collapsed": 4,
}


def encode_post_only_label(label: str | int) -> int:
    """Encode the five-class post-only ontology without reusing xBD grades."""

    if isinstance(label, bool):
        raise PostOnlyLabelError("boolean is not a post-only class")
    if isinstance(label, int):
        if 0 <= label < len(POST_ONLY_CLASSES):
            return label
        raise PostOnlyLabelError(f"unsupported post-only class id: {label}")
    if not isinstance(label, str) or not label.strip():
        raise PostOnlyLabelError("post-only label must be a non-empty string or class id")
    normalized = label.strip().lower().replace("_", "-").replace(" ", "-")
    class_id = _LABEL_ALIASES.get(normalized)
    if class_id is None:
        raise PostOnlyLabelError(
            f"unsupported post-only label {label!r}; xBD grades are not this ontology"
        )
    return class_id


def post_only_macro_f1(
    predictions: Tensor,
    targets: Tensor,
    *,
    valid: Tensor | None = None,
    num_classes: int = len(POST_ONLY_CLASSES),
) -> float:
    """Compute macro F1 for post-only classes, independently of xView2 scoring."""

    if num_classes <= 0:
        raise ValueError("num_classes must be positive")
    if predictions.ndim >= 2 and predictions.shape[-1] == num_classes:
        predictions = predictions.argmax(dim=-1)
    if predictions.shape != targets.shape:
        raise ValueError("predictions and targets must have the same shape")
    predictions = predictions.reshape(-1).to(dtype=torch.long)
    targets = targets.reshape(-1).to(dtype=torch.long)
    if valid is not None:
        if valid.numel() != predictions.numel():
            raise ValueError("valid mask must contain one value per prediction")
        keep = valid.reshape(-1).to(dtype=torch.bool)
        predictions, targets = predictions[keep], targets[keep]
    scores: list[float] = []
    for class_id in range(num_classes):
        predicted = predictions == class_id
        actual = targets == class_id
        true_positive = (predicted & actual).sum().item()
        false_positive = (predicted & ~actual).sum().item()
        false_negative = (~predicted & actual).sum().item()
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(0.0 if denominator == 0 else 2.0 * true_positive / denominator)
    return sum(scores) / num_classes


class PostOnlyHead(nn.Module):
    """Global-pooling classifier for footprint-conditioned post-only features."""

    def __init__(self, in_channels: int, *, num_classes: int = len(POST_ONLY_CLASSES)) -> None:
        super().__init__()
        if in_channels <= 0 or num_classes <= 0:
            raise ValueError("in_channels and num_classes must be positive")
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(in_channels, num_classes)
        self.num_classes = num_classes

    def forward(self, features: Tensor) -> Tensor:
        if features.ndim != 4:
            raise ValueError("post-only features must be BCHW")
        return self.classifier(self.pool(features).flatten(1))
