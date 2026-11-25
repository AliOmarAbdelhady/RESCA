"""Frozen-teacher feature distillation primitives for the DINOv3 7B branch."""

from __future__ import annotations

import hashlib
import json
from typing import Iterable

import torch
from torch import Tensor, nn
from torch.nn import functional as F


class FeatureProjection(nn.Module):
    """Trainable dimension adapter kept outside the frozen teacher."""

    def __init__(self, student_dim: int, teacher_dim: int) -> None:
        super().__init__()
        if student_dim <= 0 or teacher_dim <= 0:
            raise ValueError("embedding dimensions must be positive")
        self.projection = nn.Linear(student_dim, teacher_dim)

    def forward(self, features: Tensor) -> Tensor:
        return self.projection(features)


class FrozenFeatureTeacher(nn.Module):
    """Wrap a teacher so parameters and forward activations remain detached."""

    def __init__(self, teacher: nn.Module) -> None:
        super().__init__()
        self.teacher = teacher
        for parameter in self.teacher.parameters():
            parameter.requires_grad_(False)
        self.teacher.eval()

    def forward(self, *args: object, **kwargs: object) -> Tensor:
        with torch.no_grad():
            output = self.teacher(*args, **kwargs)
        if not isinstance(output, Tensor):
            raise TypeError("frozen teacher must return a Tensor feature representation")
        return output.detach()


def feature_distillation_loss(student: Tensor, teacher: Tensor, valid: Tensor) -> Tensor:
    """Compare normalized valid patch features, excluding padding/void patches."""

    if student.ndim < 2:
        raise ValueError("feature tensors must have a leading sample dimension")
    channel_first = (
        student.ndim == 4
        and valid.ndim == 3
        and tuple(student.shape[0:1] + student.shape[2:]) == tuple(valid.shape)
    )
    if channel_first:
        if teacher.ndim != 4 or teacher.shape[0] != student.shape[0] or teacher.shape[2:] != student.shape[2:]:
            raise ValueError("channel-first student and teacher grids must share batch and spatial shape")
        student = student.permute(0, 2, 3, 1)
        teacher = teacher.permute(0, 2, 3, 1)
    if student.shape != teacher.shape:
        raise ValueError("student and teacher feature tensors must have the same shape")
    expected_valid_shape = student.shape[:-1]
    if tuple(valid.shape) != tuple(expected_valid_shape):
        raise ValueError(
            f"valid mask must have shape {expected_valid_shape}, got {tuple(valid.shape)}"
        )
    valid = valid.to(dtype=torch.bool)
    if not valid.any():
        return student.sum() * 0.0
    student_normalized = F.normalize(student, dim=-1)
    teacher_normalized = F.normalize(teacher.detach(), dim=-1)
    per_patch = (student_normalized - teacher_normalized).square().mean(dim=-1)
    return per_patch[valid].mean()


def teacher_cache_key(
    *,
    input_identity: str,
    model_revision: str,
    preprocessing_spec: str,
    tile_coordinates: tuple[int, int, int, int],
    layer_ids: Iterable[int],
) -> str:
    """Return a stable cache identity for one immutable teacher extraction."""

    payload = {
        "input_identity": input_identity,
        "model_revision": model_revision,
        "preprocessing_spec": preprocessing_spec,
        "tile_coordinates": list(tile_coordinates),
        "layer_ids": list(layer_ids),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

