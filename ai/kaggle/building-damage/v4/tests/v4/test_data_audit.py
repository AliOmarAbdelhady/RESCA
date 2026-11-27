from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import yaml
from PIL import Image

from rescuevision_ai.v4.data_audit import DatasetAuditError, audit_dataset
from rescuevision_ai.v4.datasets import load_manifest
from rescuevision_ai.v4.cli import _resolve


def _write_xbd_sample(
    root: Path,
    split: str = "train",
    sample_id: str = "quake_0001",
    *,
    size: tuple[int, int] = (8, 6),
    subtype: str = "no-damage",
) -> None:
    images = root / split / "images"
    labels = root / split / "labels"
    images.mkdir(parents=True, exist_ok=True)
    labels.mkdir(parents=True, exist_ok=True)
    width, height = size
    pre = np.zeros((height, width, 3), dtype=np.uint8)
    post = np.full((height, width, 3), 127, dtype=np.uint8)
    Image.fromarray(pre).save(images / f"{sample_id}_pre_disaster.png")
    Image.fromarray(post).save(images / f"{sample_id}_post_disaster.png")
    label = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"feature_type": "building", "subtype": subtype},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[1, 1], [4, 1], [4, 3], [1, 3], [1, 1]]],
                },
            }
        ],
    }
    (labels / f"{sample_id}_post_disaster.json").write_text(
        json.dumps(label), encoding="utf-8"
    )


def test_audit_writes_complete_manifest_and_counts(tmp_path: Path) -> None:
    root = tmp_path / "xbd"
    _write_xbd_sample(root)

    result = audit_dataset(root, adapter="xbd", out_dir=tmp_path / "audit")
    records = load_manifest(result.manifest_path)

    assert len(records) == 1
    assert records[0].sample_id == "quake_0001"
    assert records[0].split == "train"
    assert records[0].width == 8
    assert records[0].height == 6
    assert result.counts["records"] == 1
    assert result.counts["by_split"] == {"train": 1}
    assert result.overlap_risks == []
    assert (tmp_path / "audit" / "audit_report.json").is_file()


def test_audit_rejects_missing_pair_instead_of_skipping(tmp_path: Path) -> None:
    root = tmp_path / "xbd"
    _write_xbd_sample(root)
    (root / "train" / "images" / "quake_0001_post_disaster.png").unlink()

    with pytest.raises(DatasetAuditError, match="missing post image"):
        audit_dataset(root, adapter="xbd", out_dir=tmp_path / "audit")


def test_audit_reports_cross_split_duplicate_and_event_overlap(tmp_path: Path) -> None:
    root = tmp_path / "xbd"
    _write_xbd_sample(root)
    for source in (root / "train").rglob("*"):
        if source.is_file():
            destination = root / "hold" / source.relative_to(root / "train")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    result = audit_dataset(root, adapter="xbd", out_dir=tmp_path / "audit")
    kinds = {risk["kind"] for risk in result.overlap_risks}

    assert "duplicate_sample_id" in kinds
    assert "event_across_splits" in kinds


def test_audit_rejects_mismatched_image_dimensions(tmp_path: Path) -> None:
    root = tmp_path / "xbd"
    _write_xbd_sample(root, size=(8, 6))
    mismatch = np.zeros((7, 8, 3), dtype=np.uint8)
    Image.fromarray(mismatch).save(
        root / "train" / "images" / "quake_0001_post_disaster.png"
    )

    with pytest.raises(DatasetAuditError, match="dimensions"):
        audit_dataset(root, adapter="xbd", out_dir=tmp_path / "audit")


def test_repository_xbd_config_resolves_raw_data_from_project_root() -> None:
    config_path = Path(__file__).parents[2] / "configs/v4/data_xbd.yaml"
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    base = config_path.parent.resolve()
    project_root = config_path.parents[2]
    assert _resolve(base, payload["raw_root"]) == (project_root / "data/raw/xbd").resolve()
    assert _resolve(base, payload["audit_output"]) == (
        project_root / "outputs/v4/audit/xbd"
    ).resolve()
