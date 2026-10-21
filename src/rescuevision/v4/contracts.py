"""Strict configuration and compatibility contracts for building V4."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

import yaml


class ContractError(ValueError):
    """Raised when a V4 input violates a declared contract."""


_REQUIRED_FIELDS = {
    "schema_version",
    "experiment_id",
    "task",
    "model_id",
    "model_revision",
    "train_manifest",
    "validation_manifest",
    "audit_manifest",
    "normalization_id",
    "resolution_policy",
    "loss",
    "optimizer",
    "scheduler",
    "effective_batch_size",
    "seed",
    "selection_metric",
    "output_dir",
}
_OPTIONAL_FIELDS = {"parent_experiment_id", "source_revision", "data_revision"}
_ALLOWED_FIELDS = _REQUIRED_FIELDS | _OPTIONAL_FIELDS
_TASKS = {"paired_overhead", "post_only", "defects"}


@dataclass(frozen=True)
class ExperimentConfig:
    """Resolved, immutable experiment configuration.

    Manifest and output paths are resolved against the directory containing
    the YAML file.  Hashes and revisions remain strings so they can be copied
    into run manifests without changing their meaning.
    """

    schema_version: str
    experiment_id: str
    task: str
    model_id: str
    model_revision: str
    train_manifest: Path
    validation_manifest: Path
    audit_manifest: Path
    normalization_id: str
    resolution_policy: str
    loss: str
    optimizer: str
    scheduler: str
    effective_batch_size: int
    seed: int
    selection_metric: str
    output_dir: Path
    parent_experiment_id: str | None = None
    source_revision: str | None = None
    data_revision: str | None = None

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any], *, base_dir: Path) -> "ExperimentConfig":
        unknown = set(mapping) - _ALLOWED_FIELDS
        if unknown:
            raise ContractError(f"unknown field(s): {', '.join(sorted(unknown))}")
        missing = _REQUIRED_FIELDS - set(mapping)
        if missing:
            raise ContractError(f"missing required field(s): {', '.join(sorted(missing))}")

        values = dict(mapping)
        for field in _REQUIRED_FIELDS:
            value = values[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                raise ContractError(f"{field} must be non-empty")

        task = values["task"]
        if task not in _TASKS:
            raise ContractError(f"unsupported task: {task!r}")

        model_id = str(values["model_id"])
        if not _model_supports_task(model_id, task):
            raise ContractError(
                f"model {model_id!r} is incompatible with task {task!r}"
            )

        batch_size = values["effective_batch_size"]
        seed = values["seed"]
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
            raise ContractError("effective_batch_size must be a positive integer")
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ContractError("seed must be a non-negative integer")

        def resolve_path(value: Any) -> Path:
            if not isinstance(value, (str, Path)):
                raise ContractError("path fields must be strings")
            path = Path(value)
            return path if path.is_absolute() else (base_dir / path).resolve()

        return cls(
            schema_version=str(values["schema_version"]),
            experiment_id=str(values["experiment_id"]),
            task=task,
            model_id=model_id,
            model_revision=str(values["model_revision"]),
            train_manifest=resolve_path(values["train_manifest"]),
            validation_manifest=resolve_path(values["validation_manifest"]),
            audit_manifest=resolve_path(values["audit_manifest"]),
            normalization_id=str(values["normalization_id"]),
            resolution_policy=str(values["resolution_policy"]),
            loss=str(values["loss"]),
            optimizer=str(values["optimizer"]),
            scheduler=str(values["scheduler"]),
            effective_batch_size=batch_size,
            seed=seed,
            selection_metric=str(values["selection_metric"]),
            output_dir=resolve_path(values["output_dir"]),
            parent_experiment_id=_optional_string(values.get("parent_experiment_id")),
            source_revision=_optional_string(values.get("source_revision")),
            data_revision=_optional_string(values.get("data_revision")),
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("train_manifest", "validation_manifest", "audit_manifest", "output_dir"):
            result[key] = str(result[key])
        return result


@dataclass(frozen=True)
class SampleRecord:
    """One immutable paired sample entry in a V4 manifest."""

    sample_id: str
    source_dataset: str
    source_version: str
    pre_path: Path
    post_path: Path
    pre_sha256: str
    post_sha256: str
    event_id: str
    scene_id: str
    building_group_id: str
    split: str
    label_path: Path
    label_sha256: str
    width: int
    height: int
    unknown_damage_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("pre_path", "post_path", "label_path"):
            result[key] = str(result[key])
        return result

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "SampleRecord":
        required = {
            "sample_id",
            "source_dataset",
            "source_version",
            "pre_path",
            "post_path",
            "pre_sha256",
            "post_sha256",
            "event_id",
            "scene_id",
            "building_group_id",
            "split",
            "label_path",
            "label_sha256",
            "width",
            "height",
        }
        unknown = set(mapping) - required - {"unknown_damage_count"}
        if unknown:
            raise ContractError(f"unknown sample field(s): {', '.join(sorted(unknown))}")
        missing = required - set(mapping)
        if missing:
            raise ContractError(f"missing sample field(s): {', '.join(sorted(missing))}")
        if any(not isinstance(mapping[key], str) or not mapping[key].strip() for key in required - {"width", "height"}):
            raise ContractError("sample string fields must be non-empty strings")
        for key in ("width", "height"):
            if isinstance(mapping[key], bool) or not isinstance(mapping[key], int) or mapping[key] <= 0:
                raise ContractError(f"sample {key} must be a positive integer")
        unknown_damage_count = mapping.get("unknown_damage_count", 0)
        if isinstance(unknown_damage_count, bool) or not isinstance(unknown_damage_count, int) or unknown_damage_count < 0:
            raise ContractError("unknown_damage_count must be a non-negative integer")
        return cls(
            sample_id=mapping["sample_id"],
            source_dataset=mapping["source_dataset"],
            source_version=mapping["source_version"],
            pre_path=Path(mapping["pre_path"]),
            post_path=Path(mapping["post_path"]),
            pre_sha256=mapping["pre_sha256"],
            post_sha256=mapping["post_sha256"],
            event_id=mapping["event_id"],
            scene_id=mapping["scene_id"],
            building_group_id=mapping["building_group_id"],
            split=mapping["split"],
            label_path=Path(mapping["label_path"]),
            label_sha256=mapping["label_sha256"],
            width=mapping["width"],
            height=mapping["height"],
            unknown_damage_count=unknown_damage_count,
        )


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ContractError("optional string fields must be null or non-empty strings")
    return value


def _model_supports_task(model_id: str, task: str) -> bool:
    if task == "paired_overhead":
        return model_id.startswith(("paired_", "dinov3_satellite", "change_"))
    if task == "post_only":
        return model_id.startswith(("post_only_", "damage_triage", "typology_"))
    return model_id.startswith(("defect_", "crack_", "multilabel_"))


def load_experiment(path: Path) -> ExperimentConfig:
    """Load and strictly validate one YAML experiment configuration."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ContractError(f"invalid YAML: {exc}") from exc
    if not isinstance(raw, Mapping):
        raise ContractError("experiment configuration must be a mapping")
    return ExperimentConfig.from_mapping(raw, base_dir=path.parent.resolve())

