"""Hashing, atomic writes and compatibility checks for V4 artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path
from typing import Any, Mapping

from .contracts import ContractError


class ArtifactIntegrityError(ValueError):
    """Raised when an artifact is missing or does not match its recorded hash."""


_RESUME_COMPATIBILITY_FIELDS = (
    "schema_version",
    "model_id",
    "model_revision",
    "normalization_id",
    "resolution_policy",
    "train_manifest_sha256",
    "validation_manifest_sha256",
    "audit_manifest_sha256",
    "source_revision",
    "data_revision",
)


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Return a SHA-256 digest without loading the whole file into memory."""

    path = Path(path)
    if not path.is_file():
        raise ArtifactIntegrityError(f"artifact is missing or not a file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_artifact(path: Path, expected_sha256: str) -> None:
    """Raise when ``path`` is absent or differs from its recorded digest."""

    if len(expected_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_sha256.lower()):
        raise ArtifactIntegrityError("expected_sha256 must be a 64-character hexadecimal digest")
    actual = sha256_file(path)
    if actual != expected_sha256.lower():
        raise ArtifactIntegrityError(
            f"sha256 mismatch for {Path(path)}: expected {expected_sha256.lower()}, got {actual}"
        )


def validate_resume(checkpoint_meta: Mapping[str, Any], run_meta: Mapping[str, Any]) -> None:
    """Ensure a checkpoint belongs to the immutable inputs of a run."""

    for field in _RESUME_COMPATIBILITY_FIELDS:
        checkpoint_has = field in checkpoint_meta
        run_has = field in run_meta
        if checkpoint_has != run_has:
            raise ContractError(f"resume metadata missing compatible field: {field}")
        if checkpoint_has and checkpoint_meta[field] != run_meta[field]:
            raise ContractError(
                f"resume metadata incompatible for {field}: "
                f"checkpoint={checkpoint_meta[field]!r}, run={run_meta[field]!r}"
            )


def write_json_atomic(path: Path, payload: Any) -> None:
    """Write JSON through a sibling temporary file and atomic rename.

    ``allow_nan=False`` prevents a metrics file from silently containing a
    value that is not valid interoperable JSON.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        encoded = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    except ValueError as exc:
        raise ValueError("non-finite values are not allowed in JSON artifacts") from exc

    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def build_artifact_manifest(run_dir: Path) -> list[dict[str, Any]]:
    """List complete regular files below ``run_dir`` with size and digest."""

    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise ArtifactIntegrityError(f"run directory is missing: {run_dir}")
    entries: list[dict[str, Any]] = []
    for path in sorted(run_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(run_dir)
        name = relative.name
        if name == "artifact_manifest.json" or name.endswith((".partial", ".tmp")):
            continue
        if any(part.startswith(".") for part in relative.parts):
            continue
        entries.append(
            {
                "path": relative.as_posix(),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return entries

