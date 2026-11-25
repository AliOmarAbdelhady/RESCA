from __future__ import annotations

from types import SimpleNamespace

import torch
from torch import nn

from rescuevision.v4.models.dinov3 import (
    FrozenDINOv3Features,
    TokenGridError,
    extract_spatial_tokens,
)


class _DummyDINO(nn.Module):
    def __init__(self, *, prefix_tokens: int = 2, dimension: int = 8) -> None:
        super().__init__()
        self.scale = nn.Parameter(torch.ones(()))
        self.config = SimpleNamespace(num_register_tokens=prefix_tokens - 1)
        self.prefix_tokens = prefix_tokens
        self.dimension = dimension

    def forward(self, pixel_values: torch.Tensor) -> SimpleNamespace:
        batch = pixel_values.shape[0]
        grid_h = pixel_values.shape[-2] // 16
        grid_w = pixel_values.shape[-1] // 16
        tokens = torch.ones(
            batch,
            self.prefix_tokens + grid_h * grid_w,
            self.dimension,
            device=pixel_values.device,
        ) * self.scale
        return SimpleNamespace(last_hidden_state=tokens)


def test_extract_spatial_tokens_excludes_declared_non_spatial_prefix() -> None:
    tokens = torch.arange(2 * 8 * 4, dtype=torch.float32).reshape(2, 8, 4)

    spatial = extract_spatial_tokens(tokens, grid_size=(2, 3), num_prefix_tokens=2)

    assert spatial.shape == (2, 4, 2, 3)
    assert torch.equal(spatial[0, :, 0, 0], tokens[0, 2])
    assert torch.equal(spatial[0, :, 1, 2], tokens[0, 7])


def test_extract_spatial_tokens_rejects_ambiguous_token_layout() -> None:
    tokens = torch.zeros(1, 8, 4)

    try:
        extract_spatial_tokens(tokens, grid_size=(2, 3))
    except TokenGridError as exc:
        assert "prefix" in str(exc)
    else:
        raise AssertionError("ambiguous token layout was accepted")


def test_frozen_backbone_has_no_gradients_and_validates_actual_grid() -> None:
    backbone = _DummyDINO()
    wrapper = FrozenDINOv3Features(backbone, patch_size=16)
    pixels = torch.zeros(2, 3, 32, 48)

    features = wrapper(pixels)

    assert features.shape == (2, 8, 2, 3)
    assert not features.requires_grad
    assert all(not parameter.requires_grad for parameter in backbone.parameters())

