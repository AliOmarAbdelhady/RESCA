"""Auditable V4 command-line entry points."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch
import yaml

from .contracts import load_experiment
from .data_audit import audit_dataset
from .training import train


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rescuevision.v4.cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit")
    audit.add_argument("--config", type=Path, required=True)

    train_parser = subparsers.add_parser("train")
    train_parser.add_argument("--config", type=Path, required=True)
    train_parser.add_argument("--resume", type=Path)

    for name in ("evaluate", "profile"):
        command = subparsers.add_parser(name)
        command.add_argument("--config", type=Path, required=True)
        if name == "evaluate":
            command.add_argument("--checkpoint", type=Path, required=True)

    predict = subparsers.add_parser("predict")
    predict.add_argument("--config", type=Path, required=True)
    predict.add_argument("--checkpoint", type=Path, required=True)
    predict.add_argument("--pre-image", type=Path, required=True)
    predict.add_argument("--post-image", type=Path, required=True)
    predict.add_argument("--out-dir", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "audit":
        return _audit(args.config)
    if args.command == "train":
        print(train(args.config, resume=args.resume))
        return 0
    if args.command == "profile":
        print(json.dumps({"torch": torch.__version__, "cuda": torch.cuda.is_available()}))
        return 0
    raise RuntimeError(
        f"V4 {args.command} stage is defined but not implemented; do not substitute a legacy predictor"
    )


def _audit(config_path: Path) -> int:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("audit config must be a YAML mapping")
    base = config_path.parent.resolve()
    root = _resolve(base, raw.get("raw_root"))
    output = _resolve(base, raw.get("audit_output"))
    result = audit_dataset(root, adapter=str(raw.get("adapter", "xbd")), out_dir=output)
    print(json.dumps({"manifest": str(result.manifest_path), "counts": result.counts, "overlap_risks": result.overlap_risks}))
    return 0


def _resolve(base: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("audit config path fields must be non-empty strings")
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
