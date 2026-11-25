"""Raw xBD inventory, pair validation and immutable manifest generation."""

from __future__ import annotations

import json
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image

from .artifacts import sha256_file, write_json_atomic
from .contracts import ContractError, SampleRecord
from .datasets import _xbd_pixel_features, _feature_geometry


class DatasetAuditError(ValueError):
    """Raised when raw data cannot satisfy the V4 paired-input contract."""


@dataclass(frozen=True)
class AuditResult:
    manifest_path: Path
    report_path: Path
    records: list[SampleRecord]
    counts: dict[str, Any]
    overlap_risks: list[dict[str, Any]]


_BUILDING_TYPES = {"building", "building_polygon", "building-footprint"}


def audit_dataset(root: Path, adapter: str, out_dir: Path) -> AuditResult:
    """Audit an xBD-shaped tree and write a JSONL manifest plus report."""

    root = Path(root).resolve()
    out_dir = Path(out_dir).resolve()
    if adapter != "xbd":
        raise DatasetAuditError(f"unsupported adapter: {adapter!r}")
    if not root.is_dir():
        raise DatasetAuditError(f"dataset root is missing: {root}")

    split_dirs = [
        path
        for path in sorted(root.iterdir())
        if path.is_dir() and (path / "images").is_dir()
    ]
    if not split_dirs:
        raise DatasetAuditError(f"no split/images directories found under {root}")

    records: list[SampleRecord] = []
    unknown_damage = 0
    building_count = 0
    for split_dir in split_dirs:
        split = split_dir.name
        image_dir = split_dir / "images"
        label_dir = split_dir / "labels"
        pre_paths = sorted(image_dir.glob("*_pre_disaster.png"))
        post_paths = sorted(image_dir.glob("*_post_disaster.png"))
        pre_by_id = {path.name[: -len("_pre_disaster.png")]: path for path in pre_paths}
        post_by_id = {path.name[: -len("_post_disaster.png")]: path for path in post_paths}
        missing_pre = sorted(set(post_by_id) - set(pre_by_id))
        missing_post = sorted(set(pre_by_id) - set(post_by_id))
        if missing_pre:
            raise DatasetAuditError(f"missing pre image for sample {missing_pre[0]!r}")
        if missing_post:
            raise DatasetAuditError(f"missing post image for sample {missing_post[0]!r}")
        if not label_dir.is_dir():
            raise DatasetAuditError(f"missing labels directory for split {split!r}")

        for sample_id in sorted(pre_by_id):
            pre_path = pre_by_id[sample_id]
            post_path = post_by_id[sample_id]
            label_path = label_dir / f"{sample_id}_post_disaster.json"
            if not label_path.is_file():
                raise DatasetAuditError(f"missing label for sample {sample_id!r}")
            pre_width, pre_height = _image_size(pre_path)
            post_width, post_height = _image_size(post_path)
            if (pre_width, pre_height) != (post_width, post_height):
                raise DatasetAuditError(
                    f"image dimensions disagree for {sample_id!r}: "
                    f"pre={(pre_width, pre_height)}, post={(post_width, post_height)}"
                )
            features = _read_label_features(label_path)
            sample_buildings = 0
            sample_unknown = 0
            for feature in features:
                properties = feature.get("properties") or {}
                if properties.get("feature_type", "building") not in _BUILDING_TYPES:
                    continue
                _validate_geometry(feature)
                sample_buildings += 1
                subtype = _normalise_subtype(properties.get("subtype"))
                if subtype is None:
                    sample_unknown += 1
            building_count += sample_buildings
            unknown_damage += sample_unknown
            event_id = _event_id(sample_id)
            records.append(
                SampleRecord(
                    sample_id=sample_id,
                    source_dataset="xbd",
                    source_version="raw",
                    pre_path=pre_path,
                    post_path=post_path,
                    pre_sha256=sha256_file(pre_path),
                    post_sha256=sha256_file(post_path),
                    event_id=event_id,
                    scene_id=sample_id,
                    building_group_id=sample_id,
                    split=split,
                    label_path=label_path,
                    label_sha256=sha256_file(label_path),
                    width=pre_width,
                    height=pre_height,
                    unknown_damage_count=sample_unknown,
                )
            )

    overlap_risks = _find_overlap_risks(records)
    counts = {
        "records": len(records),
        "building_features": building_count,
        "unknown_damage_features": unknown_damage,
        "by_split": {
            split: sum(record.split == split for record in records)
            for split in sorted({record.split for record in records})
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.jsonl"
    temporary = out_dir / f".{manifest_path.name}.{uuid.uuid4().hex}.tmp"
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
        os.replace(temporary, manifest_path)
    finally:
        if temporary.exists():
            temporary.unlink()
    report_path = out_dir / "audit_report.json"
    write_json_atomic(
        report_path,
        {
            "adapter": adapter,
            "root": str(root),
            "counts": counts,
            "overlap_risks": overlap_risks,
            "manifest_path": str(manifest_path),
        },
    )
    return AuditResult(
        manifest_path=manifest_path,
        report_path=report_path,
        records=records,
        counts=counts,
        overlap_risks=overlap_risks,
    )


def _image_size(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.size
    except (OSError, ValueError) as exc:
        raise DatasetAuditError(f"corrupt image: {path}") from exc


def _read_label_features(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DatasetAuditError(f"corrupt label JSON: {path}") from exc
    try:
        return _xbd_pixel_features(payload)
    except ContractError as exc:
        raise DatasetAuditError(f"invalid pixel features in {path}: {exc}") from exc


def _validate_geometry(feature: dict[str, Any]) -> None:
    try:
        _feature_geometry(feature)
    except ContractError as exc:
        raise DatasetAuditError(str(exc)) from exc


def _normalise_subtype(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    normalised = value.strip().lower().replace("_", "-").replace(" ", "-")
    return {
        "no-damage": 0,
        "minor-damage": 1,
        "major-damage": 2,
        "destroyed": 3,
    }.get(normalised)


def _event_id(sample_id: str) -> str:
    head, separator, tail = sample_id.rpartition("_")
    return head if separator and tail.isdigit() else sample_id


def _find_overlap_risks(records: list[SampleRecord]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    by_id: dict[str, list[SampleRecord]] = defaultdict(list)
    by_hash: dict[str, list[SampleRecord]] = defaultdict(list)
    by_event: dict[str, set[str]] = defaultdict(set)
    for record in records:
        by_id[record.sample_id].append(record)
        by_hash[f"{record.pre_sha256}:{record.post_sha256}"].append(record)
        by_event[record.event_id].add(record.split)
    for sample_id, grouped in by_id.items():
        splits = sorted({record.split for record in grouped})
        if len(splits) > 1:
            risks.append({"kind": "duplicate_sample_id", "sample_id": sample_id, "splits": splits})
    for pair_hash, grouped in by_hash.items():
        splits = sorted({record.split for record in grouped})
        if len(splits) > 1:
            risks.append({"kind": "duplicate_image_hash", "pair_sha256": pair_hash, "splits": splits})
    for event_id, splits in by_event.items():
        if len(splits) > 1:
            risks.append({"kind": "event_across_splits", "event_id": event_id, "splits": sorted(splits)})
    return risks
