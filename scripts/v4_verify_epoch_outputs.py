"""Kaggle-only verification of the completed corrected D0 epoch outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from rescuevision.v4.evaluation import OfficialAccumulator

INPUT = Path('/kaggle/input')
EXPECTED_REPORT = 'ddf61ec9857025a51586213c5f6f3de0e8b0d547b95512867c23751167836f2b'
EXPECTED_MANIFEST = '4c4a2a19c96198eda84088efcb8dcfbf6eb4d6f6c41b2336853e5cc0c038e619'
EXPECTED_CHECKPOINT = 'c04c272b0852066c5752be354e88abc77d809bc2d01796709fbbdb2fbd8e36f0'


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def unique_hashed(name: str, expected: str) -> Path:
    matches = [p for p in INPUT.rglob(name) if p.is_file() and sha256(p) == expected]
    if len(matches) != 1:
        raise RuntimeError(f'Expected one verified {name}; found {len(matches)}')
    return matches[0]


def main() -> None:
    manifest = unique_hashed('rv4_xbd_grouped_manifest.jsonl', EXPECTED_MANIFEST)
    report_path = unique_hashed('rv4_d0_epoch_report.json', EXPECTED_REPORT)
    checkpoint = unique_hashed('rv4_d0_epoch_001.pt', EXPECTED_CHECKPOINT)
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if report.get('status') != 'PASS' or report.get('mode') != 'full' or report.get('checkpoint_sha256') != EXPECTED_CHECKPOINT:
        raise RuntimeError('epoch report identity or status mismatch')
    rows = [json.loads(line) for line in manifest.read_text(encoding='utf-8').splitlines() if line.strip()]
    expected_ids = {row['sample_id'] for row in rows if row['split'] == 'validation'}
    artifacts = report['prediction_artifacts']
    observed_ids = [item['sample_id'] for item in artifacts]
    if len(expected_ids) != 139 or len(observed_ids) != 139 or len(set(observed_ids)) != 139 or set(observed_ids) != expected_ids:
        raise RuntimeError('prediction identities do not match the complete validation manifest')
    prediction_root = report_path.parent / 'rv4_d0_predictions'
    if not prediction_root.is_dir():
        raise RuntimeError('prediction directory is not attached beside the report')
    actual_files = {p.name for p in prediction_root.glob('*.npz')}
    if actual_files != {sample_id + '.npz' for sample_id in expected_ids}:
        raise RuntimeError('prediction filenames differ from the expected validation identities')
    scorer = OfficialAccumulator()
    for index, artifact in enumerate(artifacts, 1):
        path = prediction_root / (artifact['sample_id'] + '.npz')
        if sha256(path) != artifact['sha256']:
            raise RuntimeError(f'prediction hash mismatch: {path.name}')
        with np.load(path, allow_pickle=False) as prediction:
            arrays = [prediction[key] for key in ('localization_mask', 'damage_mask', 'localization_target', 'damage_target')]
            if any(array.shape != (1024, 1024) for array in arrays):
                raise RuntimeError(f'prediction raster shape mismatch: {path.name}')
            scorer.update(*arrays)
        if index % 20 == 0:
            print(f'RV4_VERIFY {index}/139', flush=True)
    reconstructed = scorer.summary()
    original = report['validation_score']
    if reconstructed['counts'] != original['counts'] or reconstructed['updates'] != 139:
        raise RuntimeError('reconstructed metric counts do not match epoch report')
    for key in ('combined_f1', 'localization_f1', 'damage_f1'):
        if abs(reconstructed[key] - original[key]) > 1e-12:
            raise RuntimeError(f'reconstructed score differs: {key}')
    result = {
        'status': 'PASS', 'scope': 'artifact integrity and stored-raster score reconstruction; independent target-rasterizer parity not tested',
        'prediction_files_verified': len(artifacts), 'checkpoint_sha256': sha256(checkpoint),
        'manifest_sha256': EXPECTED_MANIFEST, 'epoch_report_sha256': EXPECTED_REPORT,
        'reconstructed_score': reconstructed,
    }
    Path('/kaggle/working/rv4_epoch_output_verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
