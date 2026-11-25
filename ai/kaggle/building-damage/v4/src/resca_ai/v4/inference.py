"""Native-resolution, overlap-tiled paired inference."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F


@dataclass(frozen=True)
class InferenceRecipe:
    tile_size: int = 512
    stride: int = 384
    localization_threshold: float = 0.5
    tta: tuple[str, ...] = ("identity",)
    device: str = "auto"

    def __post_init__(self) -> None:
        if self.tile_size <= 0 or self.stride <= 0 or self.stride > self.tile_size:
            raise ValueError("stride must be positive and no greater than tile_size")
        if not 0.0 <= self.localization_threshold <= 1.0:
            raise ValueError("localization_threshold must be in [0,1]")
        if not self.tta or any(name not in {"identity", "hflip"} for name in self.tta):
            raise ValueError("tta must contain identity and/or hflip")
        if self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be one of: auto, cpu, cuda")


@dataclass(frozen=True)
class PairPrediction:
    original_size: tuple[int, int]
    localization_probability: np.ndarray
    damage_probability: np.ndarray
    localization_mask: np.ndarray
    damage_mask: np.ndarray
    validity_mask: np.ndarray
    model_provenance: dict[str, Any]


def predict_pair(
    pre: np.ndarray,
    post: np.ndarray,
    model: nn.Module,
    recipe: InferenceRecipe,
) -> PairPrediction:
    """Predict paired rasters while preserving their original dimensions."""

    pre = _validate_image(pre, "pre")
    post = _validate_image(post, "post")
    if pre.shape != post.shape:
        raise ValueError("pre and post images must have identical shapes")
    height, width = pre.shape[:2]
    device = _resolve_device(recipe.device)
    model = model.to(device)
    was_training = model.training
    model.eval()
    loc_probabilities: list[np.ndarray] = []
    damage_probabilities: list[np.ndarray] = []
    validity_masks: list[np.ndarray] = []
    with torch.no_grad():
        for augmentation in recipe.tta:
            aug_pre, aug_post = _apply_tta(pre, post, augmentation)
            loc, damage, valid = _predict_tiled(
                aug_pre, aug_post, model, recipe, device=device
            )
            loc_probabilities.append(_invert_tta(loc, augmentation))
            damage_probabilities.append(_invert_tta(damage, augmentation))
            validity_masks.append(_invert_tta(valid, augmentation))
    if was_training:
        model.train()
    localization_probability = np.mean(loc_probabilities, axis=0).astype(np.float32)
    damage_probability = np.mean(damage_probabilities, axis=0).astype(np.float32)
    validity_mask = np.logical_and.reduce(validity_masks)
    localization_mask = localization_probability >= recipe.localization_threshold
    damage_mask = np.argmax(damage_probability, axis=0).astype(np.uint8) + 1
    damage_mask = np.where(localization_mask, damage_mask, 0).astype(np.uint8)
    return PairPrediction(
        original_size=(height, width),
        localization_probability=localization_probability,
        damage_probability=damage_probability,
        localization_mask=localization_mask,
        damage_mask=damage_mask,
        validity_mask=validity_mask,
        model_provenance={
            "model_class": model.__class__.__name__,
            "tile_size": recipe.tile_size,
            "stride": recipe.stride,
            "tta": list(recipe.tta),
        },
    )


def _predict_tiled(
    pre: np.ndarray,
    post: np.ndarray,
    model: nn.Module,
    recipe: InferenceRecipe,
    *,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    height, width = pre.shape[:2]
    loc_sum = np.zeros((height, width), dtype=np.float64)
    damage_sum = np.zeros((4, height, width), dtype=np.float64)
    weights = np.zeros((height, width), dtype=np.float64)
    for top in _tile_starts(height, recipe.tile_size, recipe.stride):
        for left in _tile_starts(width, recipe.tile_size, recipe.stride):
            tile_height = min(recipe.tile_size, height - top)
            tile_width = min(recipe.tile_size, width - left)
            pre_tile = _pad_tile(pre[top : top + tile_height, left : left + tile_width], recipe.tile_size)
            post_tile = _pad_tile(post[top : top + tile_height, left : left + tile_width], recipe.tile_size)
            pre_tensor = _image_tensor(pre_tile).unsqueeze(0).to(device)
            post_tensor = _image_tensor(post_tile).unsqueeze(0).to(device)
            output = model(pre_tensor, post_tensor)
            if "loc_logits" not in output or "damage_logits" not in output:
                raise ValueError("model output must contain loc_logits and damage_logits")
            loc_logits = output["loc_logits"]
            damage_logits = output["damage_logits"]
            loc_logits = F.interpolate(
                loc_logits, size=(recipe.tile_size, recipe.tile_size), mode="bilinear", align_corners=False
            )
            damage_logits = F.interpolate(
                damage_logits, size=(recipe.tile_size, recipe.tile_size), mode="bilinear", align_corners=False
            )
            loc = loc_logits.sigmoid()[0, 0].cpu().numpy()[:tile_height, :tile_width]
            damage = damage_logits.softmax(dim=1)[0].cpu().numpy()[:, :tile_height, :tile_width]
            loc_sum[top : top + tile_height, left : left + tile_width] += loc
            damage_sum[:, top : top + tile_height, left : left + tile_width] += damage
            weights[top : top + tile_height, left : left + tile_width] += 1.0
    if np.any(weights == 0):
        raise RuntimeError("tiling left uncovered pixels")
    return (
        (loc_sum / weights).astype(np.float32),
        (damage_sum / weights[None, ...]).astype(np.float32),
        weights > 0,
    )


def _tile_starts(length: int, tile_size: int, stride: int) -> list[int]:
    if length <= tile_size:
        return [0]
    starts = list(range(0, length - tile_size + 1, stride))
    last = length - tile_size
    if starts[-1] != last:
        starts.append(last)
    return starts


def _pad_tile(image: np.ndarray, tile_size: int) -> np.ndarray:
    height, width = image.shape[:2]
    return np.pad(
        image,
        ((0, tile_size - height), (0, tile_size - width), (0, 0)),
        mode="constant",
        constant_values=0,
    )


def _image_tensor(image: np.ndarray) -> torch.Tensor:
    array = image.astype(np.float32)
    if array.max(initial=0.0) > 1.0:
        array /= 255.0
    return torch.from_numpy(array).permute(2, 0, 1)


def _validate_image(image: np.ndarray, name: str) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError(f"{name} must have shape [H,W,3]")
    if array.shape[0] <= 0 or array.shape[1] <= 0:
        raise ValueError(f"{name} must have non-empty spatial dimensions")
    return array


def _resolve_device(requested: str) -> torch.device:
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("cuda inference requested but no CUDA device is available")
    return torch.device("cuda" if requested == "cuda" or (requested == "auto" and torch.cuda.is_available()) else "cpu")


def _apply_tta(pre: np.ndarray, post: np.ndarray, augmentation: str) -> tuple[np.ndarray, np.ndarray]:
    if augmentation == "identity":
        return pre, post
    if augmentation == "hflip":
        return np.flip(pre, axis=1).copy(), np.flip(post, axis=1).copy()
    raise ValueError(f"unsupported TTA: {augmentation}")


def _invert_tta(array: np.ndarray, augmentation: str) -> np.ndarray:
    if augmentation == "identity":
        return array
    if augmentation == "hflip":
        return np.flip(array, axis=-1).copy()
    raise ValueError(f"unsupported TTA: {augmentation}")

