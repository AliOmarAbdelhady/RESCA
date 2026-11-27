"""Prepare, but do not run or submit, a paired epoch-3 Kaggle ablation."""
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
parser.add_argument('output_dir', type=Path)
parser.add_argument('--mode', choices=('bounded', 'full'), required=True)
args = parser.parse_args()
buffer = io.BytesIO()
with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted((root / 'src/rescuevision_ai').rglob('*.py')):
        archive.write(path, path.relative_to(root))
    archive.write(root / 'scripts/v4_d0_epoch3_ablation_stage.py', 'stage.py')
archive = buffer.getvalue()
digest = hashlib.sha256(archive).hexdigest()
encoded = base64.b64encode(archive).decode('ascii')

for arm in ('unweighted', 'weighted'):
    source = f'''import base64, hashlib, io, os, runpy, sys, zipfile\nfrom pathlib import Path\nprint("RV4_STAGE notebook starting", flush=True)\narchive = base64.b64decode({encoded!r})\nif hashlib.sha256(archive).hexdigest() != {digest!r}: raise RuntimeError("source archive hash mismatch")\nroot = Path("/kaggle/working/rv4_ablation_source")\nroot.mkdir(exist_ok=True)\nwith zipfile.ZipFile(io.BytesIO(archive)) as z: z.extractall(root)\nsys.path.insert(0, str(root / "src"))\nos.environ["RV4_SOURCE_SHA256"] = {digest!r}\nos.environ["RV4_D0_MODE"] = {args.mode!r}\nos.environ["RV4_ABLATION_ARM"] = {arm!r}\nrunpy.run_path(str(root / "stage.py"), run_name="__main__")\n'''
    compile(source, 'rv4_epoch3_ablation', 'exec')
    notebook = {'cells': [{'cell_type': 'code', 'id': 'rv4-epoch3-ablation',
                           'execution_count': None, 'metadata': {}, 'outputs': [],
                           'source': source.splitlines(keepends=True)}],
                'metadata': {'kernelspec': {'display_name': 'Python 3',
                                            'language': 'python', 'name': 'python3'}},
                'nbformat': 4, 'nbformat_minor': 5}
    metadata = {
        'id': f'aliomarsaleh/rv4-epoch3-{args.mode}-{arm}',
        'title': f'RV4 Epoch3 {args.mode.title()} {arm.title()}', 'code_file': 'stage.ipynb',
        'language': 'python', 'kernel_type': 'notebook', 'is_private': True,
        'enable_gpu': True, 'enable_tpu': False, 'enable_internet': False,
        'dataset_sources': ['pr4deepr/dinov3-github-repository',
                            'tunguz/xview2-challenge-dataset-train-and-test'],
        'kernel_sources': ['aliomarsaleh/rv4-xbd-grouped-manifest-audit',
                           'aliomarsaleh/rv4-d0-epoch2-full',
                           'aliomarsaleh/rv4-train-class-pixel-audit'],
        'competition_sources': [],
        'model_sources': ['yadavdamodar/dinov3-vitl16-pretrain-sat493m/PyTorch/default/1'],
        'machine_shape': 'NvidiaTeslaT4',
    }
    output = args.output_dir / arm
    output.mkdir(parents=True, exist_ok=True)
    (output / 'stage.ipynb').write_text(json.dumps(notebook), encoding='utf-8')
    (output / 'kernel-metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')

print(json.dumps({'status': 'PREPARED', 'source_archive_sha256': digest,
                  'mode': args.mode, 'arms': ['unweighted', 'weighted'],
                  'executed_cells': False}))
