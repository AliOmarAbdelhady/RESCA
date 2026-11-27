from __future__ import annotations

import numpy as np
import torch
from torch import nn

from rescuevision_ai.v4.inference import InferenceRecipe, predict_pair


class _ConstantPairModel(nn.Module):
    def forward(self, pre: torch.Tensor, post: torch.Tensor) -> dict[str, torch.Tensor]:
        batch, _, height, width = pre.shape
        loc = torch.zeros((batch, 1, height, width), device=pre.device)
        damage = torch.zeros((batch, 4, height, width), device=pre.device)
        damage[:, 2] = 4.0
        return {"loc_logits": loc, "damage_logits": damage}


def test_native_tiling_covers_odd_image_and_preserves_constant_probabilities() -> None:
    pre = np.zeros((7, 11, 3), dtype=np.uint8)
    post = np.full((7, 11, 3), 255, dtype=np.uint8)
    prediction = predict_pair(
        pre,
        post,
        _ConstantPairModel(),
        InferenceRecipe(tile_size=4, stride=3),
    )

    assert prediction.localization_probability.shape == (7, 11)
    assert prediction.damage_probability.shape == (4, 7, 11)
    assert prediction.localization_mask.all()
    assert np.all(prediction.damage_mask == 3)
    assert np.allclose(prediction.localization_probability, 0.5)
    assert np.all(prediction.validity_mask)


def test_tta_applies_to_pair_and_inverts_probability_maps() -> None:
    pre = np.arange(7 * 11 * 3, dtype=np.uint8).reshape(7, 11, 3)
    post = np.flip(pre, axis=1).copy()

    prediction = predict_pair(
        pre,
        post,
        _ConstantPairModel(),
        InferenceRecipe(tile_size=4, stride=3, tta=("identity", "hflip")),
    )

    assert prediction.original_size == (7, 11)
    assert np.allclose(prediction.localization_probability, 0.5)
    assert prediction.model_provenance["tile_size"] == 4
