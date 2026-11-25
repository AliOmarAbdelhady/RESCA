from __future__ import annotations

import torch
from torch import nn

from rescuevision.v4.models.distillation import (
    FrozenFeatureTeacher,
    FeatureProjection,
    feature_distillation_loss,
    teacher_cache_key,
)


def test_teacher_cache_key_changes_with_any_identity_component() -> None:
    base = teacher_cache_key(
        input_identity="image-a",
        model_revision="dinov3-7b-r1",
        preprocessing_spec="native512-p16",
        tile_coordinates=(0, 0, 512, 512),
        layer_ids=(12, 24),
    )
    changed = teacher_cache_key(
        input_identity="image-b",
        model_revision="dinov3-7b-r1",
        preprocessing_spec="native512-p16",
        tile_coordinates=(0, 0, 512, 512),
        layer_ids=(12, 24),
    )

    assert len(base) == 64
    assert base != changed


def test_projection_supports_different_embedding_dimensions() -> None:
    projection = FeatureProjection(student_dim=3, teacher_dim=5)
    student = torch.randn(2, 4, 3)
    teacher = torch.randn(2, 4, 5)
    valid = torch.tensor([[True, True, False, False], [True, False, True, False]])

    loss = feature_distillation_loss(projection(student), teacher, valid)

    assert loss.ndim == 0
    assert torch.isfinite(loss)


def test_masked_distillation_ignores_padding_and_has_differentiable_empty_zero() -> None:
    student = torch.randn(1, 3, 4, requires_grad=True)
    teacher = torch.randn(1, 3, 4)
    invalid = torch.zeros(1, 3, dtype=torch.bool)

    loss = feature_distillation_loss(student, teacher, invalid)
    loss.backward()

    assert loss.item() == 0.0
    assert student.grad is not None and torch.equal(student.grad, torch.zeros_like(student))


def test_masked_distillation_accepts_channel_first_patch_grids() -> None:
    student = torch.randn(2, 4, 3, 5, requires_grad=True)
    teacher = torch.randn(2, 6, 3, 5)
    projection = FeatureProjection(student_dim=4, teacher_dim=6)
    valid = torch.ones(2, 3, 5, dtype=torch.bool)

    loss = feature_distillation_loss(projection(student.permute(0, 2, 3, 1)).permute(0, 3, 1, 2), teacher, valid)
    loss.backward()

    assert torch.isfinite(loss)


def test_frozen_teacher_receives_no_gradients() -> None:
    module = nn.Linear(4, 4)
    teacher = FrozenFeatureTeacher(module)
    features = teacher(torch.ones(2, 4))

    assert not features.requires_grad
    assert all(not parameter.requires_grad for parameter in module.parameters())
