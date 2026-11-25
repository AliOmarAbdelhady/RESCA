"""JSONL adapters for the post-only and visible-defect specialist tasks."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models.post_only import encode_post_only_label
from .task_adapters import TaskAdapterError, assert_grouped_split_integrity


@dataclass(frozen=True)
class PostOnlyRecord:
    sample_id: str
    image_path: Path
    split: str
    structure_id: str
    photo_group_id: str
    annotation_unit: str
    label_id: int
    footprint_source: str


@dataclass(frozen=True)
class DefectRecord:
    sample_id: str
    image_path: Path
    split: str
    structure_id: str
    photo_group_id: str
    annotations: Mapping[str, Any]


def load_post_only_manifest(path: Path) -> list[PostOnlyRecord]:
    """Load corrected post-only records without merging them into xBD grades."""

    rows = _read_jsonl(path)
    _assert_unique_ids(rows)
    assert_grouped_split_integrity(rows, group_fields=("structure_id", "photo_group_id"))
    records: list[PostOnlyRecord] = []
    for index, row in enumerate(rows):
        _require_fields(
            row,
            index,
            {
                "sample_id",
                "image_path",
                "split",
                "structure_id",
                "photo_group_id",
                "annotation_unit",
                "label",
            },
            allowed={"footprint_source"},
        )
        annotation_unit = _non_empty(row["annotation_unit"], "annotation_unit", index)
        if annotation_unit not in {"visible_fragment", "unique_building"}:
            raise TaskAdapterError(f"row {index} has unsupported annotation_unit {annotation_unit!r}")
        footprint_source = _non_empty(row.get("footprint_source", "provided"), "footprint_source", index)
        if footprint_source not in {"provided", "predicted", "none"}:
            raise TaskAdapterError(f"row {index} has unsupported footprint_source {footprint_source!r}")
        records.append(
            PostOnlyRecord(
                sample_id=_non_empty(row["sample_id"], "sample_id", index),
                image_path=_path(row["image_path"], "image_path", index),
                split=_non_empty(row["split"], "split", index),
                structure_id=_non_empty(row["structure_id"], "structure_id", index),
                photo_group_id=_non_empty(row["photo_group_id"], "photo_group_id", index),
                annotation_unit=annotation_unit,
                label_id=encode_post_only_label(row["label"]),
                footprint_source=footprint_source,
            )
        )
    return records


def load_defect_manifest(path: Path) -> list[DefectRecord]:
    """Load defect records while preserving missing annotation keys."""

    rows = _read_jsonl(path)
    _assert_unique_ids(rows)
    assert_grouped_split_integrity(rows, group_fields=("structure_id", "photo_group_id"))
    records: list[DefectRecord] = []
    for index, row in enumerate(rows):
        _require_fields(
            row,
            index,
            {"sample_id", "image_path", "split", "structure_id", "photo_group_id", "annotations"},
        )
        annotations = row["annotations"]
        if not isinstance(annotations, Mapping):
            raise TaskAdapterError(f"row {index} annotations must be an object")
        records.append(
            DefectRecord(
                sample_id=_non_empty(row["sample_id"], "sample_id", index),
                image_path=_path(row["image_path"], "image_path", index),
                split=_non_empty(row["split"], "split", index),
                structure_id=_non_empty(row["structure_id"], "structure_id", index),
                photo_group_id=_non_empty(row["photo_group_id"], "photo_group_id", index),
                annotations=dict(annotations),
            )
        )
    return records


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.is_file():
        raise TaskAdapterError(f"specialist manifest is missing: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise TaskAdapterError(f"invalid specialist JSONL row {line_number}") from exc
        if not isinstance(row, dict):
            raise TaskAdapterError(f"specialist JSONL row {line_number} must be an object")
        rows.append(row)
    if not rows:
        raise TaskAdapterError(f"specialist manifest has no records: {path}")
    return rows


def _assert_unique_ids(rows: list[Mapping[str, Any]]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(rows):
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise TaskAdapterError(f"row {index} has no non-empty sample_id")
        if sample_id in seen:
            raise TaskAdapterError(f"duplicate sample_id {sample_id!r}")
        seen.add(sample_id)


def _require_fields(
    row: Mapping[str, Any],
    index: int,
    required: set[str],
    *,
    allowed: set[str] | None = None,
) -> None:
    allowed_fields = required | (allowed or set())
    missing = required - set(row)
    unknown = set(row) - allowed_fields
    if missing:
        raise TaskAdapterError(f"row {index} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise TaskAdapterError(f"row {index} has unknown fields: {', '.join(sorted(unknown))}")


def _non_empty(value: Any, field: str, index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TaskAdapterError(f"row {index} {field} must be a non-empty string")
    return value


def _path(value: Any, field: str, index: int) -> Path:
    return Path(_non_empty(value, field, index))
