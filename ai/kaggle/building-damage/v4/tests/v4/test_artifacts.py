from __future__ import annotations

import hashlib
import math
from pathlib import Path

import pytest

from resca_ai.v4.artifacts import (
    ArtifactIntegrityError,
    build_artifact_manifest,
    sha256_file,
    validate_artifact,
    validate_resume,
    write_json_atomic,
)
from resca_ai.v4.contracts import ContractError, load_experiment


def test_sha256_and_validate_artifact_detect_corruption(tmp_path: Path) -> None:
    artifact = tmp_path / "weights.bin"
    artifact.write_bytes(b"checkpoint-v1")
    expected = hashlib.sha256(b"checkpoint-v1").hexdigest()

    assert sha256_file(artifact) == expected
    validate_artifact(artifact, expected)

    artifact.write_bytes(b"corrupted")
    with pytest.raises(ArtifactIntegrityError, match="sha256 mismatch"):
        validate_artifact(artifact, expected)


def test_validate_resume_rejects_incompatible_immutable_fields() -> None:
    checkpoint = {
        "schema_version": "v4.0",
        "model_id": "paired_cnn_baseline",
        "model_revision": "cnn-r1",
        "normalization_id": "imagenet_rgb_v1",
        "train_manifest_sha256": "train-a",
        "validation_manifest_sha256": "val-a",
        "audit_manifest_sha256": "audit-a",
    }
    run = {**checkpoint, "normalization_id": "dinov3_satellite_v1"}

    with pytest.raises(ContractError, match="normalization_id"):
        validate_resume(checkpoint, run)


def test_atomic_json_rejects_non_finite_values_and_leaves_no_partial(tmp_path: Path) -> None:
    target = tmp_path / "metrics.json"

    with pytest.raises(ValueError, match="non-finite"):
        write_json_atomic(target, {"score": math.nan})

    assert not target.exists()
    assert not list(tmp_path.glob("*.tmp"))


def test_artifact_manifest_ignores_partial_files(tmp_path: Path) -> None:
    (tmp_path / "metrics.json").write_text('{"score": 0.8}\n', encoding="utf-8")
    (tmp_path / "checkpoint.pt").write_bytes(b"weights")
    (tmp_path / "checkpoint.pt.partial").write_bytes(b"incomplete")
    (tmp_path / ".checkpoint.pt.tmp").write_bytes(b"incomplete")

    manifest = build_artifact_manifest(tmp_path)
    paths = {entry["path"] for entry in manifest}

    assert paths == {"checkpoint.pt", "metrics.json"}
    assert all(entry["sha256"] for entry in manifest)


def test_load_experiment_resolves_paths_and_rejects_unknown_fields(tmp_path: Path) -> None:
    config = tmp_path / "experiment.yaml"
    config.write_text(
        "\n".join(
            [
                "schema_version: v4.0",
                "experiment_id: cnn_baseline_r1",
                "parent_experiment_id: null",
                "task: paired_overhead",
                "model_id: paired_cnn_baseline",
                "model_revision: cnn-r1",
                "train_manifest: manifests/train.jsonl",
                "validation_manifest: manifests/val.jsonl",
                "audit_manifest: manifests/audit.jsonl",
                "normalization_id: imagenet_rgb_v1",
                "resolution_policy: native_512_crop",
                "loss: masked_bce_dice_ce_dice",
                "optimizer: adamw",
                "scheduler: warmup_cosine",
                "effective_batch_size: 8",
                "seed: 42",
                "selection_metric: xview2_official_combined",
                "output_dir: outputs/v4/cnn_baseline_r1",
                "max_epochs: 60",
                "microbatch_size: 2",
                "num_workers: 0",
                "device: auto",
                "grad_clip_norm: 1.0",
            ]
        ),
        encoding="utf-8",
    )

    loaded = load_experiment(config)
    assert loaded.train_manifest == (tmp_path / "manifests/train.jsonl").resolve()
    assert loaded.output_dir == (tmp_path / "outputs/v4/cnn_baseline_r1").resolve()
    assert loaded.max_epochs == 60
    assert loaded.microbatch_size == 2

    config.write_text(config.read_text(encoding="utf-8") + "\nunexpected: true\n", encoding="utf-8")
    with pytest.raises(ContractError, match="unknown field"):
        load_experiment(config)


def test_load_experiment_rejects_impossible_task_model_pair(tmp_path: Path) -> None:
    config = tmp_path / "experiment.yaml"
    config.write_text(
        "\n".join(
            [
                "schema_version: v4.0",
                "experiment_id: bad_pair",
                "task: defects",
                "model_id: paired_cnn_baseline",
                "model_revision: cnn-r1",
                "train_manifest: train.jsonl",
                "validation_manifest: val.jsonl",
                "audit_manifest: audit.jsonl",
                "normalization_id: imagenet_rgb_v1",
                "resolution_policy: native_512_crop",
                "loss: multilabel_bce",
                "optimizer: adamw",
                "scheduler: warmup_cosine",
                "effective_batch_size: 8",
                "seed: 42",
                "selection_metric: defect_macro_f1",
                "output_dir: outputs/v4/bad_pair",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ContractError, match="incompatible"):
        load_experiment(config)
