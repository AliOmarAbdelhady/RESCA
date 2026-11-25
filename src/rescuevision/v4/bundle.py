"""Self-contained inference-bundle contracts for the V4 final recipe."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from .artifacts import sha256_file, validate_artifact, write_json_atomic
from .inference import InferenceRecipe, PairPrediction


class BundleError(ValueError):
    """Raised when an inference bundle is incomplete or internally inconsistent."""


@dataclass(frozen=True)
class BundleSpec:
    """Immutable model, preprocessing, labels and inference-recipe identity."""

    model_id: str
    model_revision: str
    source_revision: str
    data_revision: str
    normalization_id: str
    resolution_policy: str
    label_map: Mapping[str, int]
    recipe: InferenceRecipe
    metrics: Mapping[str, float] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in (
            "model_id",
            "model_revision",
            "source_revision",
            "data_revision",
            "normalization_id",
            "resolution_policy",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise BundleError(f"{field_name} must be a non-empty string")
        labels = dict(self.label_map)
        if not labels or any(not isinstance(name, str) or not name.strip() for name in labels):
            raise BundleError("label_map must contain non-empty names")
        values = list(labels.values())
        if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in values):
            raise BundleError("label_map values must be positive integer output ids")
        if len(set(values)) != len(values):
            raise BundleError("label_map output ids must be unique")
        if any(not isinstance(name, str) or not name.strip() for name in self.limitations):
            raise BundleError("limitations must contain non-empty strings")

    def to_metadata(self) -> dict[str, Any]:
        recipe = self.recipe
        return {
            "model_id": self.model_id,
            "model_revision": self.model_revision,
            "source_revision": self.source_revision,
            "data_revision": self.data_revision,
            "normalization_id": self.normalization_id,
            "resolution_policy": self.resolution_policy,
            "label_map": dict(self.label_map),
            "recipe": {
                "tile_size": recipe.tile_size,
                "stride": recipe.stride,
                "localization_threshold": recipe.localization_threshold,
                "tta": list(recipe.tta),
                "device": recipe.device,
            },
            "metrics": dict(self.metrics),
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class InferenceBundle:
    """Loaded bundle with its verified local checkpoint."""

    root: Path
    spec: BundleSpec
    metadata: Mapping[str, Any]
    checkpoint_path: Path
    checkpoint_sha256: str


def bundle_preprocessing_identity(
    normalization_id: str,
    resolution_policy: str,
    recipe: InferenceRecipe,
) -> str:
    """Hash every preprocessing and tiling choice that affects predictions."""

    payload = {
        "normalization_id": normalization_id,
        "resolution_policy": resolution_policy,
        "recipe": {
            "tile_size": recipe.tile_size,
            "stride": recipe.stride,
            "localization_threshold": recipe.localization_threshold,
            "tta": list(recipe.tta),
            "device": recipe.device,
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_inference_bundle(
    destination: Path,
    *,
    checkpoint_path: Path,
    spec: BundleSpec,
) -> Path:
    """Create a reviewable bundle with a copied, hashed checkpoint."""

    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    weights_dir = destination / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    bundled_checkpoint = weights_dir / "checkpoint.pt"
    shutil.copy2(checkpoint_path, bundled_checkpoint)
    checkpoint_sha256 = sha256_file(bundled_checkpoint)
    metadata = {
        "schema_version": "v4.inference_bundle.1",
        **spec.to_metadata(),
        "preprocessing_identity": bundle_preprocessing_identity(
            spec.normalization_id, spec.resolution_policy, spec.recipe
        ),
        "checkpoint": {
            "path": "weights/checkpoint.pt",
            "sha256": checkpoint_sha256,
        },
    }
    write_json_atomic(destination / "bundle.json", metadata)
    return destination


def load_inference_bundle(root: Path) -> InferenceBundle:
    """Load and verify a bundle before any model weights are consumed."""

    root = Path(root)
    metadata_path = root / "bundle.json"
    if not metadata_path.is_file():
        raise BundleError(f"bundle metadata is missing: {metadata_path}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BundleError(f"cannot read bundle metadata: {metadata_path}") from exc
    if not isinstance(metadata, dict) or metadata.get("schema_version") != "v4.inference_bundle.1":
        raise BundleError("unsupported or missing inference bundle schema_version")
    checkpoint = metadata.get("checkpoint")
    if not isinstance(checkpoint, dict):
        raise BundleError("bundle checkpoint metadata must be an object")
    relative_path = checkpoint.get("path")
    expected_sha256 = checkpoint.get("sha256")
    if not isinstance(relative_path, str) or not relative_path:
        raise BundleError("bundle checkpoint path must be a non-empty string")
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise BundleError("bundle checkpoint path must stay inside the bundle")
    if not isinstance(expected_sha256, str):
        raise BundleError("bundle checkpoint sha256 is missing")
    checkpoint_path = root / relative
    validate_artifact(checkpoint_path, expected_sha256)
    spec = _spec_from_metadata(metadata)
    expected_preprocessing = bundle_preprocessing_identity(
        spec.normalization_id, spec.resolution_policy, spec.recipe
    )
    if metadata.get("preprocessing_identity") != expected_preprocessing:
        raise BundleError("bundle preprocessing identity does not match its recipe")
    return InferenceBundle(
        root=root,
        spec=spec,
        metadata=metadata,
        checkpoint_path=checkpoint_path,
        checkpoint_sha256=expected_sha256,
    )


def prediction_digest(prediction: PairPrediction) -> str:
    """Hash prediction arrays for deterministic reference-output checks."""

    digest = hashlib.sha256()
    digest.update(json.dumps({"original_size": prediction.original_size}).encode("utf-8"))
    arrays = (
        prediction.localization_probability,
        prediction.damage_probability,
        prediction.localization_mask,
        prediction.damage_mask,
        prediction.validity_mask,
    )
    for array in arrays:
        value = np.ascontiguousarray(array)
        digest.update(json.dumps({"shape": value.shape, "dtype": str(value.dtype)}).encode("utf-8"))
        digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def _spec_from_metadata(metadata: Mapping[str, Any]) -> BundleSpec:
    required = {
        "model_id",
        "model_revision",
        "source_revision",
        "data_revision",
        "normalization_id",
        "resolution_policy",
        "label_map",
        "recipe",
        "metrics",
        "limitations",
    }
    missing = required - set(metadata)
    if missing:
        raise BundleError(f"bundle metadata is missing: {', '.join(sorted(missing))}")
    recipe_data = metadata["recipe"]
    if not isinstance(recipe_data, Mapping):
        raise BundleError("bundle recipe must be an object")
    allowed_recipe = {"tile_size", "stride", "localization_threshold", "tta", "device"}
    if set(recipe_data) != allowed_recipe:
        raise BundleError("bundle recipe fields are incomplete or unknown")
    try:
        recipe = InferenceRecipe(
            tile_size=recipe_data["tile_size"],
            stride=recipe_data["stride"],
            localization_threshold=recipe_data["localization_threshold"],
            tta=tuple(recipe_data["tta"]),
            device=recipe_data["device"],
        )
    except (TypeError, ValueError) as exc:
        raise BundleError(f"invalid bundle recipe: {exc}") from exc
    label_map = metadata["label_map"]
    metrics = metadata["metrics"]
    limitations = metadata["limitations"]
    if not isinstance(label_map, Mapping) or not isinstance(metrics, Mapping) or not isinstance(limitations, list):
        raise BundleError("bundle labels, metrics and limitations have invalid types")
    return BundleSpec(
        model_id=metadata["model_id"],
        model_revision=metadata["model_revision"],
        source_revision=metadata["source_revision"],
        data_revision=metadata["data_revision"],
        normalization_id=metadata["normalization_id"],
        resolution_policy=metadata["resolution_policy"],
        label_map=dict(label_map),
        recipe=recipe,
        metrics=dict(metrics),
        limitations=tuple(limitations),
    )
