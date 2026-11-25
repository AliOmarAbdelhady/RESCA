"""Synchronized spatial transforms for paired images and raster targets."""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class HorizontalFlip:
    """Flip both images and every spatial target on the same axis."""

    always: bool = False

    def __call__(self, sample: dict[str, object]) -> dict[str, object]:
        if not self.always:
            return sample
        transformed = dict(sample)
        for key in ("pre", "post"):
            transformed[key] = torch.flip(_tensor(sample[key], key), dims=[2])
        for key in ("loc_target", "loc_valid", "damage_target", "damage_valid"):
            transformed[key] = torch.flip(_tensor(sample[key], key), dims=[1])
        return transformed


def _tensor(value: object, key: str) -> torch.Tensor:
    if not isinstance(value, torch.Tensor):
        raise TypeError(f"transform field {key!r} must be a torch.Tensor")
    return value
