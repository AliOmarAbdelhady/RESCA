"""Loss functions for explicitly supervised damage pixels."""

from __future__ import annotations

from collections.abc import Sequence

import torch
import torch.nn.functional as F
from torch import Tensor


def masked_damage_cross_entropy(
    logits: Tensor, labels: Tensor, valid: Tensor, weights: Sequence[float] | Tensor
) -> Tensor:
    """Return a class-weighted mean over valid pixels; ignored labels are harmless."""
    if logits.ndim != 4 or logits.shape[1] != 4:
        raise ValueError("damage logits must have shape [batch, 4, height, width]")
    if labels.shape != logits.shape[:1] + logits.shape[2:] or valid.shape != labels.shape:
        raise ValueError("labels and valid mask must match the logits spatial shape")
    if labels.dtype != torch.long or valid.dtype != torch.bool:
        raise ValueError("labels must be long and valid mask must be boolean")
    weight = torch.as_tensor(weights, device=logits.device, dtype=logits.dtype)
    if weight.shape != (4,) or not bool(torch.isfinite(weight).all()) or not bool((weight > 0).all()):
        raise ValueError("weights must contain four finite positive values")
    if not bool(valid.any()):
        return logits.sum() * 0.0
    selected_labels = labels[valid]
    if bool(((selected_labels < 0) | (selected_labels > 3)).any()):
        raise ValueError("valid damage labels must be in 0..3")
    safe_labels = labels.masked_fill(~valid, 0)
    per_pixel = F.cross_entropy(logits, safe_labels, reduction="none")
    selected_weights = weight[selected_labels]
    return (per_pixel[valid] * selected_weights).sum() / selected_weights.sum()
