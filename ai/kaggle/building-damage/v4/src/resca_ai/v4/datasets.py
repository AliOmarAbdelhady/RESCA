"""Manifest-backed paired xBD sample loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

import numpy as np
import torch
from PIL import Image, ImageDraw
from torch.utils.data import Dataset
from shapely import wkt
from shapely.geometry import shape
from shapely.validation import make_valid

from .contracts import ContractError, SampleRecord
from .xbd_audited_pre_geometries import AUDITED_PRE_INVALID_WKT as _AUDITED_PRE_INVALID_WKT


_DAMAGE_IDS = {
    "no-damage": 0,
    "minor-damage": 1,
    "major-damage": 2,
    "destroyed": 3,
}


def load_manifest(path: Path) -> list[SampleRecord]:
    """Load a JSONL manifest and reject malformed entries."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    records: list[SampleRecord] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
            records.append(SampleRecord.from_mapping(payload))
        except (json.JSONDecodeError, ContractError) as exc:
            raise ContractError(f"invalid manifest row {line_number}: {exc}") from exc
    if not records:
        raise ContractError(f"manifest has no records: {path}")
    return records


class PairedDataset(Dataset[dict[str, object]]):
    """Load paired RGB images and rasterize xBD building/damage targets."""

    def __init__(
        self,
        manifest: Path,
        split: str,
        transform: Callable[[dict[str, object]], dict[str, object]] | None = None,
    ) -> None:
        records = [record for record in load_manifest(manifest) if record.split == split]
        if not records:
            raise ContractError(f"manifest has no records for split {split!r}")
        self.records = records
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, object]:
        record = self.records[index]
        pre = _load_rgb(record.pre_path)
        post = _load_rgb(record.post_path)
        if pre.shape != post.shape or pre.shape[:2] != (record.height, record.width):
            raise ContractError(f"runtime image dimensions disagree for {record.sample_id!r}")
        loc_target, damage_target, loc_valid, damage_valid = _rasterize_xbd_label(
            record.label_path, width=record.width, height=record.height
        )
        sample: dict[str, object] = {
            "pre": _to_image_tensor(pre),
            "post": _to_image_tensor(post),
            "loc_target": torch.from_numpy(loc_target),
            "loc_valid": torch.from_numpy(loc_valid),
            "damage_target": torch.from_numpy(damage_target),
            "damage_valid": torch.from_numpy(damage_valid),
            "sample_id": record.sample_id,
            "original_size": (record.height, record.width),
        }
        if self.transform is not None:
            sample = self.transform(sample)
        return sample


def _load_rgb(path: Path) -> np.ndarray:
    try:
        with Image.open(path) as image:
            return np.asarray(image.convert("RGB"), dtype=np.uint8)
    except OSError as exc:
        raise ContractError(f"cannot read image: {path}") from exc


def _to_image_tensor(image: np.ndarray) -> torch.Tensor:
    return torch.from_numpy(image.copy()).permute(2, 0, 1).float().div(255.0)


def _rasterize_xbd_label(path: Path, *, width: int, height: int) -> tuple[np.ndarray, ...]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read label: {path}") from exc
    loc = np.zeros((height, width), dtype=np.uint8)
    damage = np.full((height, width), 255, dtype=np.uint8)
    loc_valid = np.ones((height, width), dtype=bool)
    damage_valid = np.zeros((height, width), dtype=bool)
    for feature in _xbd_pixel_features(payload):
        properties = feature.get("properties") or {}
        if properties.get("feature_type", "building") not in {"building", "building_polygon", "building-footprint"}:
            continue
        subtype = properties.get("subtype")
        if isinstance(subtype, str):
            subtype = subtype.strip().lower().replace("_", "-").replace(" ", "-")
        class_id = _DAMAGE_IDS.get(subtype)
        geometry = _feature_geometry(feature)
        polygons = [geometry] if geometry.geom_type == "Polygon" else list(geometry.geoms)
        for polygon in polygons:
            mask = Image.new("L", (width, height), 0)
            draw = ImageDraw.Draw(mask)
            draw.polygon(list(polygon.exterior.coords), fill=1)
            for interior in polygon.interiors:
                draw.polygon(list(interior.coords), fill=0)
            polygon_mask = np.asarray(mask, dtype=bool)
            loc[polygon_mask] = 1
            if class_id is not None:
                damage[polygon_mask] = class_id
                damage_valid[polygon_mask] = True
    return loc, damage, loc_valid, damage_valid


def _xbd_pixel_features(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        raise ContractError("label must be an object containing pixel features")
    features = payload.get("features")
    if isinstance(features, dict):
        features = features.get("xy")
    if not isinstance(features, list) or any(not isinstance(f, dict) for f in features):
        raise ContractError("label must contain a list of pixel features (features.xy)")
    return features


def _feature_geometry(feature: dict):
    try:
        geometry = wkt.loads(feature["wkt"]) if "wkt" in feature else shape(feature["geometry"])
        # One xBD post-event polygon has a self-intersection. Its exact WKT
        # and UID were audited remotely; make_valid preserves its raster and
        # only separates a zero-area line. Other invalid polygons still fail.
        raw = feature.get("wkt")
        uid = (feature.get("properties") or {}).get("uid")
        # For audited pre-event polygons preserve the original outline exactly;
        # make_valid changes some ground-truth rasters. The UID and source WKT
        # must both match the complete-dataset diagnostic.
        if (not geometry.is_valid and geometry.geom_type == "Polygon"
                and not geometry.is_empty and isinstance(raw, str)
                and _AUDITED_PRE_INVALID_WKT.get(uid) == hashlib.sha256(raw.encode("utf-8")).hexdigest()):
            return geometry
        if (not geometry.is_valid and isinstance(raw, str)
                and uid == "2aaab43d-9165-49eb-8dee-a16d86f40e57"
                and hashlib.sha256(raw.encode("utf-8")).hexdigest() == "37d44ceb038269bdc5d8699faada029ebc67ab4512934308c5a2660f9bd3b71b"):
            repaired = make_valid(geometry)
            parts = list(getattr(repaired, "geoms", []))
            polygons = [part for part in parts if part.geom_type == "Polygon"]
            if len(polygons) != 1 or any(part.geom_type not in {"Polygon", "LineString"} for part in parts):
                raise ValueError("known geometry repair changed unexpectedly")
            geometry = polygons[0]
        if geometry.geom_type not in {"Polygon", "MultiPolygon"} or geometry.is_empty or not geometry.is_valid:
            raise ValueError("expected a valid non-empty Polygon or MultiPolygon")
        return geometry
    except Exception as exc:
        raise ContractError(f"invalid building pixel geometry: {exc}") from exc
