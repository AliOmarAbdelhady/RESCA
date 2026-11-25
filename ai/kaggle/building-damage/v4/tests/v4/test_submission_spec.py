from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.v4_submit_spec import build_submission_spec, retry_decision


def _write_config(tmp_path: Path) -> Path:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text('{"sample_id":"one"}\n', encoding="utf-8")
    config = tmp_path / "experiment.yaml"
    config.write_text(
        "\n".join(
            [
                "schema_version: v4.0",
                "experiment_id: spec-test",
                "task: paired_overhead",
                "model_id: paired_cnn_baseline",
                "model_revision: cnn-r1",
                "train_manifest: manifest.jsonl",
                "validation_manifest: manifest.jsonl",
                "audit_manifest: manifest.jsonl",
                "normalization_id: imagenet_rgb_v1",
                "resolution_policy: native_512_crop",
                "loss: masked_bce_dice_ce_dice",
                "optimizer: adamw",
                "scheduler: warmup_cosine",
                "effective_batch_size: 8",
                "seed: 42",
                "selection_metric: xview2_official_combined",
                "output_dir: outputs/run",
            ]
        ),
        encoding="utf-8",
    )
    return config


def test_submission_spec_is_private_and_hashes_immutable_inputs(tmp_path: Path) -> None:
    config = _write_config(tmp_path)
    output = build_submission_spec(config, stage="cpu_audit", out_dir=tmp_path / "spec")
    payload = json.loads(output.read_text(encoding="utf-8"))

    expected_hash = hashlib.sha256((tmp_path / "manifest.jsonl").read_bytes()).hexdigest()
    assert payload["visibility"] == "private"
    assert payload["submitted"] is False
    assert payload["stage"] == "cpu_audit"
    assert payload["immutable_inputs"]["train_manifest"]["sha256"] == expected_hash
    encoded = output.read_text(encoding="utf-8").lower()
    assert "hf_token" not in encoded
    assert "kaggle_key" not in encoded
    assert "secret" not in encoded


def test_unknown_kaggle_state_requires_inspection_before_retry() -> None:
    assert retry_decision("unknown") == "inspect_before_retry"
    assert retry_decision("running") == "do_not_retry"
    assert retry_decision("completed") == "do_not_retry"
    assert retry_decision("failed") == "retry_with_new_attempt_identity"
