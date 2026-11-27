"""Streaming parity implementation of the official xView2 pixel scorer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


class EvaluationInputError(ValueError):
    """Raised when prediction/target rasters violate the scorer contract."""


def _f1(tp: int, fn: int, fp: int) -> float:
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    if precision == 0.0 or recall == 0.0:
        return 0.0
    return (2.0 * precision * recall) / (precision + recall)


@dataclass
class _Counts:
    tp: int = 0
    fn: int = 0
    fp: int = 0

    def add(self, *, tp: int, fn: int, fp: int) -> None:
        self.tp += int(tp)
        self.fn += int(fn)
        self.fp += int(fp)

    def as_dict(self) -> dict[str, int]:
        return {"tp": self.tp, "fn": self.fn, "fp": self.fp}


@dataclass
class OfficialAccumulator:
    """Accumulate global counts for the xView2 official combined F1.

    Inputs use the upstream external raster encoding: localization is binary,
    while damage uses ``0`` for background and ``1..4`` for the four grades.
    The internal ``255`` ignore value is deliberately rejected here; callers
    must resolve it during target generation and retain that decision in the
    run metadata.
    """

    _localization: _Counts = field(default_factory=_Counts, init=False)
    _damage: dict[int, _Counts] = field(
        default_factory=lambda: {class_id: _Counts() for class_id in range(1, 5)},
        init=False,
    )
    _updates: int = field(default=0, init=False)

    def update(
        self,
        loc_pred: np.ndarray,
        damage_pred: np.ndarray,
        loc_target: np.ndarray,
        damage_target: np.ndarray,
    ) -> None:
        loc_pred = _validate_raster(loc_pred, "loc_pred", allowed={0, 1})
        damage_pred = _validate_raster(damage_pred, "damage_pred", allowed={0, 1, 2, 3, 4})
        loc_target = _validate_raster(loc_target, "loc_target", allowed={0, 1})
        damage_target = _validate_raster(
            damage_target, "damage_target", allowed={0, 1, 2, 3, 4}
        )
        shapes = {loc_pred.shape, damage_pred.shape, loc_target.shape, damage_target.shape}
        if len(shapes) != 1:
            raise EvaluationInputError("all rasters must have the same shape")

        pred_buildings = loc_pred > 0
        target_buildings = loc_target > 0
        self._localization.add(
            tp=np.logical_and(pred_buildings, target_buildings).sum(),
            fn=np.logical_and(~pred_buildings, target_buildings).sum(),
            fp=np.logical_and(pred_buildings, ~target_buildings).sum(),
        )

        # This follows the pinned upstream scorer: damage is evaluated only
        # on target-building pixels, while the predicted damage is first gated
        # by the predicted localization mask.
        gated_damage = damage_pred * pred_buildings.astype(np.uint8)
        target_damage_pixels = damage_target > 0
        predicted_damage = gated_damage[target_damage_pixels]
        observed_damage = damage_target[target_damage_pixels]
        for class_id, counts in self._damage.items():
            counts.add(
                tp=np.logical_and(predicted_damage == class_id, observed_damage == class_id).sum(),
                fn=np.logical_and(predicted_damage != class_id, observed_damage == class_id).sum(),
                fp=np.logical_and(predicted_damage == class_id, observed_damage != class_id).sum(),
            )
        self._updates += 1

    def summary(self) -> dict[str, Any]:
        localization_f1 = _f1(
            self._localization.tp, self._localization.fn, self._localization.fp
        )
        damage_f1_by_class = {
            str(class_id): _f1(counts.tp, counts.fn, counts.fp)
            for class_id, counts in self._damage.items()
        }
        harmonic_damage_f1 = 4.0 / sum(
            (score + 1e-6) ** -1 for score in damage_f1_by_class.values()
        )
        combined = 0.3 * localization_f1 + 0.7 * harmonic_damage_f1
        return {
            "metric_name": "xview2_official",
            "updates": self._updates,
            "localization_f1": localization_f1,
            "damage_f1": harmonic_damage_f1,
            "damage_f1_by_class": damage_f1_by_class,
            "combined_f1": combined,
            "counts": {
                "localization": self._localization.as_dict(),
                "damage": {
                    str(class_id): counts.as_dict()
                    for class_id, counts in self._damage.items()
                },
            },
        }


def _validate_raster(value: np.ndarray, name: str, *, allowed: set[int]) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2:
        raise EvaluationInputError(f"{name} must be a 2-D raster")
    if not np.issubdtype(array.dtype, np.integer) and array.dtype != np.bool_:
        raise EvaluationInputError(f"{name} must contain integer values in 0-4")
    observed = set(np.unique(array).tolist())
    if not observed <= allowed:
        raise EvaluationInputError(
            f"{name} contains values outside the allowed 0-4 encoding: {sorted(observed - allowed)}"
        )
    return array.astype(np.uint8, copy=False)

