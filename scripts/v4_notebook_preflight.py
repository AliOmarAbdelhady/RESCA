#!/usr/bin/env python3
"""Static, source-only preflight for V4 Kaggle notebook wrappers.

This command parses notebook JSON and Python syntax. It never executes a cell,
imports the experiment package, accesses a dataset, or contacts Kaggle.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


class NotebookPreflightError(ValueError):
    """Raised when a notebook cannot satisfy the remote-run contract."""


_EXPECTED: dict[str, dict[str, set[str]]] = {
    "00_data_and_split_audit.ipynb": {
        "required": {"INPUT_ROOT", "rv4_cpu_audit", "label_schema_ok"},
        "forbidden": set(),
    },
    "00_gpu_smoke.ipynb": {
        "required": {"torch.cuda.is_available", "rv4_gpu_smoke", "refusing a CPU fallback"},
        "forbidden": set(),
    },
    "01_dinov3_vitl_profile.ipynb": {
        "required": {"dinov3_vitl16_pretrain_sat493m", "rv4_dinov3_vitl_profile", "torch.hub.load"},
        "forbidden": set(),
    },
    "01_dinov3_teacher_profile.ipynb": {
        "required": {"rescuevision.v4.cli", "'profile'", "RV4_CONFIG", "check=True"},
        "forbidden": set(),
    },
    "02_specialist_manifest_audit.ipynb": {
        "required": {
            "load_post_only_manifest",
            "load_defect_manifest",
            "RV4_POST_ONLY_MANIFEST",
            "RV4_DEFECT_MANIFEST",
        },
        "forbidden": set(),
    },
    "03_final_bundle_verify.ipynb": {
        "required": {"load_inference_bundle", "RV4_BUNDLE_DIR"},
        "forbidden": set(),
    },
}
_FORBIDDEN_CODE = frozenset((
    "save_notebook",
    "create_notebook_session",
    "kagglehub",
    "git clone",
    "pip install",
    "hf_token",
    "kaggle_key",
))


def preflight_notebook_directory(directory: Path) -> dict[str, Any]:
    """Return a JSON-serializable static report or raise on any failure."""

    directory = Path(directory)
    if not directory.is_dir():
        raise NotebookPreflightError(f"notebook directory is missing: {directory}")
    actual = {path.name for path in directory.glob("*.ipynb")}
    expected = set(_EXPECTED)
    errors: list[str] = []
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        if missing:
            errors.append(f"missing notebooks: {', '.join(missing)}")
        if unexpected:
            errors.append(f"unexpected notebooks: {', '.join(unexpected)}")
    notebooks: list[dict[str, Any]] = []
    for name in sorted(expected & actual):
        notebooks.append(_inspect_notebook(directory / name, errors))
    report = {
        "schema_version": "v4.notebook-preflight.1",
        "directory": str(directory.resolve()),
        "executed_cells": False,
        "notebooks": notebooks,
        "errors": errors,
        "status": "FAIL" if errors else "PASS",
    }
    if errors:
        raise NotebookPreflightError(json.dumps(report, indent=2, sort_keys=True))
    return report


def _inspect_notebook(path: Path, errors: list[str]) -> dict[str, Any]:
    name = path.name
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{name}: invalid JSON: {exc}")
        return {"name": name, "status": "FAIL"}
    if payload.get("nbformat") != 4 or payload.get("nbformat_minor", 0) < 2:
        errors.append(f"{name}: requires nbformat 4.2 or newer")
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        errors.append(f"{name}: cells must be a non-empty list")
        return {"name": name, "status": "FAIL"}
    code_source: list[str] = []
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            errors.append(f"{name}: cell {index} is not an object")
            continue
        if cell.get("execution_count") is not None:
            errors.append(f"{name}: cell {index} has an execution count")
        if cell.get("outputs"):
            errors.append(f"{name}: cell {index} contains saved outputs")
        if cell.get("cell_type") == "code":
            source = "".join(cell.get("source", []))
            code_source.append(source)
            try:
                ast.parse(source, filename=f"{name}:cell-{index}")
            except SyntaxError as exc:
                errors.append(f"{name}:cell-{index}: syntax error: {exc}")
    source = "\n".join(code_source)
    required = _EXPECTED[name]["required"]
    for token in sorted(required):
        if token not in source:
            errors.append(f"{name}: missing required source token {token!r}")
    for token in _FORBIDDEN_CODE | _EXPECTED[name]["forbidden"]:
        if token.lower() in source.lower():
            errors.append(f"{name}: forbidden source token {token!r}")
    return {
        "name": name,
        "code_cells": sum(cell.get("cell_type") == "code" for cell in cells if isinstance(cell, dict)),
        "status": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    report = preflight_notebook_directory(args.notebook_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
