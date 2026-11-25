"""Build without submitting the Kaggle training-only class audit."""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output_dir", type=Path)
args = parser.parse_args()
archive_buffer = io.BytesIO()
with zipfile.ZipFile(archive_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root / "src/rescuevision").rglob("*.py")):
        archive.write(path, path.relative_to(root))
    archive.write(root / "scripts/v4_train_class_audit.py", "stage.py")
archive_bytes = archive_buffer.getvalue()
digest = hashlib.sha256(archive_bytes).hexdigest()
encoded = base64.b64encode(archive_bytes).decode("ascii")
source = f'''print("RV4_AUDIT_STAGE notebook started", flush=True)\nimport base64, hashlib, io, runpy, sys, zipfile\nfrom pathlib import Path\narchive = base64.b64decode({encoded!r})\nif hashlib.sha256(archive).hexdigest() != {digest!r}: raise RuntimeError("source archive hash mismatch")\nprint("RV4_AUDIT_STAGE source archive verified", flush=True)\nroot = Path("/kaggle/working/rv4_full_tile_source")\nroot.mkdir(exist_ok=True)\nwith zipfile.ZipFile(io.BytesIO(archive)) as z: z.extractall(root)\nsys.path.insert(0, str(root / "src"))\nrunpy.run_path(str(root / "stage.py"), run_name="__main__")\n'''
compile(source, "full_tile_smoke_notebook", "exec")
notebook = {
    "cells": [{"cell_type": "code", "id": "full-tile-smoke", "execution_count": None,
               "metadata": {}, "outputs": [], "source": source.splitlines(keepends=True)}],
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
    "nbformat": 4, "nbformat_minor": 5,
}
metadata = {
    "id": "aliomarsaleh/rv4-train-class-pixel-audit",
    "title": "RV4 Train Class Pixel Audit", "code_file": "smoke.ipynb",
    "language": "python", "kernel_type": "notebook", "is_private": True,
    "enable_gpu": False, "enable_tpu": False, "enable_internet": False,
    "dataset_sources": ["tunguz/xview2-challenge-dataset-train-and-test"],
    "kernel_sources": ["aliomarsaleh/rv4-xbd-grouped-manifest-audit"],
    "competition_sources": [],
    "model_sources": [],
}
args.output_dir.mkdir(parents=True, exist_ok=True)
(args.output_dir / "smoke.ipynb").write_text(json.dumps(notebook), encoding="utf-8")
(args.output_dir / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
print(json.dumps({"status": "PREPARED", "source_archive_sha256": digest, "executed_cells": False}))
