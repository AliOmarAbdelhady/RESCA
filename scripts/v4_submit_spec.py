#!/usr/bin/env python3
"""Create a reviewable Kaggle MCP request without submitting it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from rescuevision.v4.artifacts import write_json_atomic
from rescuevision.v4.contracts import ExperimentConfig, load_experiment


class SubmissionSpecError(ValueError):
    """Raised when a private submission specification cannot be built."""


_GPU_STAGES = {"gpu_smoke", "train", "evaluate", "profile", "predict"}
_STAGES = {"cpu_audit", "gpu_smoke", "train", "evaluate", "profile", "predict"}


def build_submission_spec(config_path: Path, *, stage: str, out_dir: Path) -> Path:
    """Write a private, immutable-input submission payload and return its path."""

    if stage not in _STAGES:
        raise SubmissionSpecError(f"unsupported stage: {stage!r}")
    config_path = Path(config_path).resolve()
    config = load_experiment(config_path)
    source_text = (
        "# V4 Kaggle wrapper source; package artifact must be attached immutably.\n"
        "from rescuevision.v4.cli import main\n"
        "main()\n"
    )
    immutable_inputs = {
        field: _file_reference(getattr(config, field))
        for field in ("train_manifest", "validation_manifest", "audit_manifest")
    }
    payload: dict[str, Any] = {
        "schema_version": "v4.0-submission-spec",
        "stage": stage,
        "experiment_id": config.experiment_id,
        "visibility": "private",
        "submitted": False,
        "execution_policy": "spec_only_no_network_submission",
        "request": {
            "tool": "mcp__kaggle__save_notebook",
            "kernel_type": "notebook",
            "language": "python",
            "enable_gpu": stage in _GPU_STAGES,
            "enable_internet": False,
            "is_private": True,
            "source_presence_flags": {"text": True, "slug": True, "title": True},
        },
        "source": {
            "text": source_text,
            "sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
        },
        "config": config.to_dict(),
        "config_path": str(config_path),
        "config_sha256": _sha256(config_path),
        "immutable_inputs": immutable_inputs,
        "retry_policy": {
            "unknown": "inspect_before_retry",
            "running": "do_not_retry",
            "completed": "do_not_retry",
            "failed": "retry_with_new_attempt_identity",
        },
    }
    out_dir = Path(out_dir)
    output = out_dir / f"{config.experiment_id}.{stage}.submission.json"
    write_json_atomic(output, payload)
    return output


def retry_decision(state: str) -> str:
    """Return the safe action for a recorded Kaggle lifecycle state."""

    decisions = {
        "unknown": "inspect_before_retry",
        "running": "do_not_retry",
        "completed": "do_not_retry",
        "failed": "retry_with_new_attempt_identity",
        "cancelled": "retry_with_new_attempt_identity",
    }
    try:
        return decisions[state]
    except KeyError as exc:
        raise SubmissionSpecError(f"unrecognized lifecycle state: {state!r}") from exc


def _file_reference(path: Path) -> dict[str, Any]:
    path = Path(path)
    return {
        "path": str(path),
        "exists": path.is_file(),
        "sha256": _sha256(path) if path.is_file() else None,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--stage", choices=sorted(_STAGES), required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    print(build_submission_spec(args.config, stage=args.stage, out_dir=args.out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
