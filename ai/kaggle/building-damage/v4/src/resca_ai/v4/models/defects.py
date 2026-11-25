"""Multi-label visible-defect adapter and dense sigmoid head."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import torch
from torch import Tensor, nn

from ..task_adapters import TaskAdapterError


def _validate_class_names(class_names: Sequence[str]) -> tuple[str, ...]:
    names = tuple(class_names)
    if not names or any(not isinstance(name, str) or not name.strip() for name in names):
        raise TaskAdapterError("class_names must contain non-empty names")
    if len(set(names)) != len(names):
        raise TaskAdapterError("class_names must be unique")
    return names


def _classification_state(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, Mapping):
        state = value.get("state", value.get("label"))
        if state is None or state in {"absent", "unlabeled", "unknown"}:
            return None
        if state in {"positive", "present", True}:
            return True
        if state in {"negative", "not-present", False}:
            return False
    if isinstance(value, str):
        normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
        if normalized in {"positive", "present", "yes"}:
            return True
        if normalized in {"negative", "not-present", "no"}:
            return False
        if normalized in {"absent", "unlabeled", "unknown"}:
            return None
    raise TaskAdapterError(f"unsupported defect classification annotation: {value!r}")


def build_multilabel_classification_target(
    annotations: Mapping[str, Any],
    *,
    class_names: Sequence[str],
) -> tuple[Tensor, Tensor]:
    """Return class targets and validity, preserving unlabeled classes.

    A missing/absent annotation is invalid supervision. An explicit negative is
    a valid zero. Classes are independent, so several positive defects may
    coexist for one image or building.
    """

    names = _validate_class_names(class_names)
    target = torch.zeros(len(names), dtype=torch.float32)
    valid = torch.zeros(len(names), dtype=torch.bool)
    for index, name in enumerate(names):
        if name not in annotations:
            continue
        state = _classification_state(annotations[name])
        if state is None:
            continue
        target[index] = float(state)
        valid[index] = True
    return target, valid


def _mask_value(value: Any, *, spatial_shape: tuple[int, int], name: str) -> Tensor:
    if isinstance(value, Mapping):
        if "mask" not in value:
            raise TaskAdapterError(
                f"{name} has image/box/classification supervision but no pixel mask; "
                "do not invent a pixel mask"
            )
        value = value["mask"]
    if isinstance(value, (bool, str)) or value is None:
        raise TaskAdapterError(f"{name} requires an explicit pixel mask")
    if isinstance(value, np.ndarray):
        value = torch.from_numpy(value)
    elif not isinstance(value, Tensor):
        value = torch.as_tensor(value)
    if tuple(value.shape) != spatial_shape:
        raise TaskAdapterError(
            f"{name} mask shape {tuple(value.shape)} does not match {spatial_shape}"
        )
    value = value.to(dtype=torch.float32)
    if torch.any((value < 0) | (value > 1)):
        raise TaskAdapterError(f"{name} mask values must be in [0, 1]")
    return value


def build_multilabel_mask_target(
    annotations: Mapping[str, Any],
    *,
    class_names: Sequence[str],
    spatial_shape: tuple[int, int],
) -> tuple[Tensor, Tensor]:
    """Build independent dense defect channels and per-class validity masks."""

    names = _validate_class_names(class_names)
    if len(spatial_shape) != 2 or any(size <= 0 for size in spatial_shape):
        raise TaskAdapterError("spatial_shape must be two positive dimensions")
    target = torch.zeros((len(names), *spatial_shape), dtype=torch.float32)
    valid = torch.zeros(len(names), dtype=torch.bool)
    for index, name in enumerate(names):
        if name not in annotations or annotations[name] is None:
            continue
        target[index] = _mask_value(annotations[name], spatial_shape=spatial_shape, name=name)
        valid[index] = True
    return target, valid


def multilabel_macro_f1(
    probabilities: Tensor,
    targets: Tensor,
    *,
    valid: Tensor | None = None,
    threshold: float = 0.5,
) -> float:
    """Compute macro F1 over independently supervised defect channels.

    ``valid`` may mark whole classes or individual sample/pixel entries. Classes
    without any valid annotation are excluded from the mean rather than treated
    as negative examples.
    """

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    if probabilities.shape != targets.shape or probabilities.ndim not in {2, 4}:
        raise ValueError("probabilities and targets must share [N,C] or [B,C,H,W] shape")
    if probabilities.ndim == 4:
        probabilities = probabilities.permute(0, 2, 3, 1).reshape(-1, probabilities.shape[1])
        targets = targets.permute(0, 2, 3, 1).reshape(-1, targets.shape[1])
    else:
        probabilities = probabilities.reshape(-1, probabilities.shape[-1])
        targets = targets.reshape(-1, targets.shape[-1])
    if torch.any((targets < 0) | (targets > 1)):
        raise ValueError("targets must be binary values")
    if valid is None:
        valid_matrix = torch.ones_like(targets, dtype=torch.bool)
    elif valid.ndim == 1 and valid.shape[0] == targets.shape[1]:
        valid_matrix = valid.to(dtype=torch.bool).reshape(1, -1).expand_as(targets)
    elif valid.shape == targets.shape:
        valid_matrix = valid.to(dtype=torch.bool)
    else:
        raise ValueError("valid must have one value per class or per target entry")
    predicted = probabilities >= threshold
    scores: list[float] = []
    for class_id in range(targets.shape[1]):
        keep = valid_matrix[:, class_id]
        if not keep.any():
            continue
        predicted_class = predicted[keep, class_id]
        target_class = targets[keep, class_id].to(dtype=torch.bool)
        true_positive = (predicted_class & target_class).sum().item()
        false_positive = (predicted_class & ~target_class).sum().item()
        false_negative = (~predicted_class & target_class).sum().item()
        denominator = 2 * true_positive + false_positive + false_negative
        scores.append(0.0 if denominator == 0 else 2.0 * true_positive / denominator)
    if not scores:
        raise TaskAdapterError("no valid defect labels are available for macro F1")
    return sum(scores) / len(scores)


class DefectHead(nn.Module):
    """Dense independent logits; callers apply sigmoid per defect channel."""

    def __init__(self, in_channels: int, num_classes: int) -> None:
        super().__init__()
        if in_channels <= 0 or num_classes <= 0:
            raise ValueError("in_channels and num_classes must be positive")
        self.classifier = nn.Conv2d(in_channels, num_classes, kernel_size=1)
        self.num_classes = num_classes

    def forward(self, features: Tensor) -> Tensor:
        if features.ndim != 4:
            raise ValueError("defect features must be BCHW")
        return self.classifier(features)
