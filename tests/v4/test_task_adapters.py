from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch

from rescuevision.v4.models.defects import (
    DefectHead,
    build_multilabel_classification_target,
    build_multilabel_mask_target,
)
from rescuevision.v4.models.post_only import (
    POST_ONLY_CLASSES,
    PostOnlyLabelError,
    encode_post_only_label,
    post_only_macro_f1,
)
from rescuevision.v4.contracts import load_experiment
from rescuevision.v4.task_adapters import TaskAdapterError, assert_grouped_split_integrity


def test_post_only_ontology_has_five_non_interchangeable_classes() -> None:
    assert POST_ONLY_CLASSES == (
        "undamaged",
        "partial_roof",
        "total_roof",
        "partial_structural",
        "total_collapse",
    )
    assert encode_post_only_label("total roof damage") == 2
    assert encode_post_only_label("total collapse") == 4


def test_post_only_rejects_xbd_grade_as_a_typology_label() -> None:
    with pytest.raises(PostOnlyLabelError, match="unsupported"):
        encode_post_only_label("minor-damage")


def test_post_only_macro_f1_is_separate_from_xview2_score() -> None:
    predictions = torch.tensor([0, 1, 2, 3, 4])
    targets = torch.tensor([0, 1, 2, 3, 4])

    assert post_only_macro_f1(predictions, targets) == pytest.approx(1.0)


def test_grouped_split_integrity_rejects_shared_structure_or_photo_group() -> None:
    records = [
        {"split": "train", "structure_id": "s1", "photo_group_id": "p1"},
        {"split": "validation", "structure_id": "s1", "photo_group_id": "p2"},
    ]

    with pytest.raises(TaskAdapterError, match="structure_id"):
        assert_grouped_split_integrity(records, group_fields=("structure_id", "photo_group_id"))


def test_grouped_split_integrity_accepts_disjoint_groups() -> None:
    records = [
        {"split": "train", "structure_id": "s1", "photo_group_id": "p1"},
        {"split": "validation", "structure_id": "s2", "photo_group_id": "p2"},
        {"split": "test", "structure_id": "s3", "photo_group_id": "p3"},
    ]

    assert_grouped_split_integrity(records, group_fields=("structure_id", "photo_group_id"))


def test_classification_target_distinguishes_absent_from_explicit_negative() -> None:
    target, valid = build_multilabel_classification_target(
        {"crack": True, "spalling": False},
        class_names=("crack", "spalling", "corrosion"),
    )

    assert torch.equal(target, torch.tensor([1.0, 0.0, 0.0]))
    assert torch.equal(valid, torch.tensor([True, True, False]))


def test_mask_target_allows_overlapping_defects_without_inventing_pixels() -> None:
    crack = np.array([[1, 1], [0, 0]], dtype=np.uint8)
    spalling = np.array([[1, 0], [1, 0]], dtype=np.uint8)
    target, valid = build_multilabel_mask_target(
        {"crack": crack, "spalling": spalling},
        class_names=("crack", "spalling", "corrosion"),
        spatial_shape=(2, 2),
    )

    assert target.shape == (3, 2, 2)
    assert target[0, 0, 0] == 1 and target[1, 0, 0] == 1
    assert torch.equal(valid, torch.tensor([True, True, False]))

    with pytest.raises(TaskAdapterError, match="pixel mask"):
        build_multilabel_mask_target(
            {"crack": {"box": [0, 0, 1, 1]}},
            class_names=("crack",),
            spatial_shape=(2, 2),
        )


def test_defect_head_returns_independent_sigmoid_channels() -> None:
    head = DefectHead(in_channels=4, num_classes=3)
    logits = head(torch.zeros(2, 4, 8, 8))

    assert logits.shape == (2, 3, 8, 8)
    assert head.num_classes == 3


def test_specialist_configs_use_their_own_task_and_metric_contracts() -> None:
    root = Path(__file__).parents[2]
    post_only = load_experiment(root / "configs/v4/post_only_typology.yaml")
    defects = load_experiment(root / "configs/v4/defect_multilabel.yaml")

    assert post_only.task == "post_only"
    assert post_only.selection_metric == "post_only_macro_f1"
    assert defects.task == "defects"
    assert defects.selection_metric == "defect_macro_f1"
