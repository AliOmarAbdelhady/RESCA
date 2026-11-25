from __future__ import annotations

import numpy as np
import pytest

from resca_ai.v4.evaluation import EvaluationInputError, OfficialAccumulator


def test_perfect_prediction_reaches_one_and_records_global_counts() -> None:
    target = np.array([[0, 1, 2], [3, 4, 0]], dtype=np.uint8)
    accumulator = OfficialAccumulator()
    accumulator.update(target > 0, target, target > 0, target)

    summary = accumulator.summary()

    assert summary["localization_f1"] == pytest.approx(1.0)
    assert summary["damage_f1"] == pytest.approx(1.0)
    assert summary["combined_f1"] == pytest.approx(1.0)
    assert summary["counts"]["localization"] == {"tp": 4, "fn": 0, "fp": 0}
    assert summary["counts"]["damage"]["1"] == {"tp": 1, "fn": 0, "fp": 0}


def test_damage_is_gated_by_predicted_localization_and_target_buildings() -> None:
    loc_target = np.array([[1, 1], [0, 0]], dtype=np.uint8)
    damage_target = np.array([[1, 2], [0, 0]], dtype=np.uint8)
    loc_pred = np.array([[1, 0], [1, 0]], dtype=np.uint8)
    damage_pred = np.array([[1, 2], [4, 1]], dtype=np.uint8)

    accumulator = OfficialAccumulator()
    accumulator.update(loc_pred, damage_pred, loc_target, damage_target)
    summary = accumulator.summary()

    # The missed second building remains a damage false negative, while the
    # predicted building outside the target cannot create damage credit.
    assert summary["counts"]["localization"] == {"tp": 1, "fn": 1, "fp": 1}
    assert summary["counts"]["damage"]["1"] == {"tp": 1, "fn": 0, "fp": 0}
    assert summary["counts"]["damage"]["2"] == {"tp": 0, "fn": 1, "fp": 0}


def test_wrong_class_and_empty_class_follow_upstream_epsilon_rule() -> None:
    loc = np.ones((1, 2), dtype=np.uint8)
    target = np.array([[1, 2]], dtype=np.uint8)
    prediction = np.array([[2, 1]], dtype=np.uint8)

    accumulator = OfficialAccumulator()
    accumulator.update(loc, prediction, loc, target)
    summary = accumulator.summary()

    assert summary["damage_f1_by_class"] == {
        "1": pytest.approx(0.0),
        "2": pytest.approx(0.0),
        "3": pytest.approx(0.0),
        "4": pytest.approx(0.0),
    }
    assert summary["damage_f1"] == pytest.approx(1e-6)


def test_accumulation_is_global_not_mean_of_batch_f1s() -> None:
    target_a = np.array([[1]], dtype=np.uint8)
    target_b = np.array([[1, 0]], dtype=np.uint8)
    accumulator = OfficialAccumulator()
    accumulator.update(np.array([[1]], dtype=np.uint8), target_a, np.array([[1]], dtype=np.uint8), target_a)
    accumulator.update(np.array([[1, 1]], dtype=np.uint8), target_b, np.array([[1, 0]], dtype=np.uint8), target_b)

    summary = accumulator.summary()

    assert summary["counts"]["localization"] == {"tp": 2, "fn": 0, "fp": 1}
    assert summary["localization_f1"] == pytest.approx(0.8)


@pytest.mark.parametrize(
    "bad_array",
    [
        np.array([[255]], dtype=np.uint8),
        np.array([[5]], dtype=np.uint8),
    ],
)
def test_external_rasters_reject_internal_or_out_of_range_values(bad_array: np.ndarray) -> None:
    accumulator = OfficialAccumulator()
    with pytest.raises(EvaluationInputError, match="0-4"):
        accumulator.update(bad_array, bad_array, np.zeros_like(bad_array), np.zeros_like(bad_array))


def test_update_rejects_shape_mismatch() -> None:
    accumulator = OfficialAccumulator()
    with pytest.raises(EvaluationInputError, match="same shape"):
        accumulator.update(
            np.zeros((2, 2), dtype=np.uint8),
            np.zeros((2, 2), dtype=np.uint8),
            np.zeros((1, 2), dtype=np.uint8),
            np.zeros((1, 2), dtype=np.uint8),
        )
