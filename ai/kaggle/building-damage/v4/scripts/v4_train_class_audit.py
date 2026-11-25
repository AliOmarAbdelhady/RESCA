"""Kaggle-only training-label pixel audit; never reads validation labels."""
from __future__ import annotations
print('RV4_AUDIT_STAGE starting imports', flush=True)
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from resca_ai.v4.datasets import _rasterize_xbd_label

MANIFEST_HASH = '4c4a2a19c96198eda84088efcb8dcfbf6eb4d6f6c41b2336853e5cc0c038e619'
DATA_ROOT = Path('/kaggle/input/datasets/tunguz/xview2-challenge-dataset-train-and-test/train/train')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    start = time.monotonic()
    print('RV4_AUDIT_STAGE discovering verified training manifest', flush=True)
    paths = [p for p in Path('/kaggle/input').rglob('rv4_xbd_grouped_manifest.jsonl') if sha256(p) == MANIFEST_HASH]
    if len(paths) != 1:
        raise RuntimeError('Verified training manifest missing or ambiguous')
    rows = [json.loads(line) for line in paths[0].read_text().splitlines() if line.strip()]
    train = [row for row in rows if row['split'] == 'train']
    if len(train) != 2660:
        raise RuntimeError('Unexpected training count')
    print('RV4_AUDIT_STAGE manifest verified; 2660 training labels planned', flush=True)
    totals = np.zeros(4, dtype=np.int64)
    tile_presence = np.zeros(4, dtype=np.int64)
    total_unknown_building_pixels = 0
    nonempty_damage_tiles = 0
    for index, row in enumerate(train, 1):
        if index == 1:
            print('RV4_AUDIT_STAGE processing first training label', flush=True)
        rel = Path(row['label_relative_path'])
        if rel.is_absolute() or '..' in rel.parts:
            raise RuntimeError('Unsafe manifest label path')
        path = DATA_ROOT / rel
        if not path.is_file() or sha256(path) != row['label_sha256']:
            raise RuntimeError(f"Training label hash mismatch: {row['sample_id']}")
        loc, damage, _, valid = _rasterize_xbd_label(path, width=1024, height=1024)
        count = np.bincount(damage[valid].astype(np.int64), minlength=4)
        if len(count) != 4:
            raise RuntimeError(f"Unexpected class encoding: {row['sample_id']}")
        totals += count
        tile_presence += count > 0
        total_unknown_building_pixels += int(np.logical_and(loc > 0, ~valid).sum())
        nonempty_damage_tiles += int(valid.any())
        if index == 1 or index % 25 == 0:
            print(f'RV4_TRAIN_CLASS_AUDIT {index}/2660 elapsed_seconds={time.monotonic() - start:.1f}', flush=True)
    report = {
        'status': 'PASS', 'scope': 'training split only; post-event polygon pixel targets',
        'manifest_sha256': MANIFEST_HASH, 'training_labels_processed': len(train),
        'validation_labels_opened': 0, 'nonempty_damage_tiles': nonempty_damage_tiles,
        'class_order': ['no-damage', 'minor-damage', 'major-damage', 'destroyed'],
        'labeled_pixels_by_class': totals.tolist(), 'tiles_with_class': tile_presence.tolist(),
        'unknown_damage_building_pixels': total_unknown_building_pixels,
        'elapsed_seconds': time.monotonic() - start,
    }
    Path('/kaggle/working/rv4_train_class_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
