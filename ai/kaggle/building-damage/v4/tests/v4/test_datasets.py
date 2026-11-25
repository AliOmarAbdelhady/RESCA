from __future__ import annotations

from pathlib import Path

import torch

from resca_ai.v4.data_audit import audit_dataset
from resca_ai.v4.datasets import PairedDataset
from resca_ai.v4.transforms import HorizontalFlip
from tests.v4.test_data_audit import _write_xbd_sample


def test_paired_dataset_returns_separate_validity_masks_and_native_shape(tmp_path: Path) -> None:
    root = tmp_path / "xbd"
    _write_xbd_sample(root, size=(8, 6), subtype="unclassified")
    result = audit_dataset(root, adapter="xbd", out_dir=tmp_path / "audit")

    sample = PairedDataset(result.manifest_path, split="train")[0]

    assert sample["pre"].shape == (3, 6, 8)
    assert sample["post"].shape == (3, 6, 8)
    assert sample["loc_target"].shape == (6, 8)
    assert sample["damage_target"].shape == (6, 8)
    assert sample["pre"].dtype == torch.float32
    assert sample["loc_valid"].dtype == torch.bool
    assert sample["damage_valid"].dtype == torch.bool
    assert sample["loc_target"].max().item() == 1
    assert sample["damage_target"].max().item() == 255
    assert not sample["damage_valid"][2, 2].item()
    assert sample["loc_valid"].all().item()


def test_horizontal_flip_transforms_pair_and_all_masks_together(tmp_path: Path) -> None:
    root = tmp_path / "xbd"
    _write_xbd_sample(root, size=(8, 6))
    result = audit_dataset(root, adapter="xbd", out_dir=tmp_path / "audit")
    plain = PairedDataset(result.manifest_path, split="train")[0]
    flipped = PairedDataset(
        result.manifest_path,
        split="train",
        transform=HorizontalFlip(always=True),
    )[0]

    assert torch.equal(flipped["pre"], torch.flip(plain["pre"], dims=[2]))
    assert torch.equal(flipped["post"], torch.flip(plain["post"], dims=[2]))
    assert torch.equal(
        flipped["loc_target"], torch.flip(plain["loc_target"], dims=[1])
    )
    assert torch.equal(
        flipped["damage_valid"], torch.flip(plain["damage_valid"], dims=[1])
    )
