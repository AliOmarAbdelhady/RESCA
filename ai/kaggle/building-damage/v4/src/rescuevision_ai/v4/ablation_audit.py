"""Strict identity checks for the training-only pixel audit used in V4."""

from __future__ import annotations

from typing import Any

EXPECTED_MANIFEST = '4c4a2a19c96198eda84088efcb8dcfbf6eb4d6f6c41b2336853e5cc0c038e619'
EXPECTED_COUNTS = [92406627, 15508042, 19792146, 9309230]
EXPECTED_ORDER = ['no-damage', 'minor-damage', 'major-damage', 'destroyed']


def validate_training_audit(report: dict[str, Any]) -> list[int]:
    expected = {
        'status': 'PASS', 'manifest_sha256': EXPECTED_MANIFEST,
        'training_labels_processed': 2660, 'validation_labels_opened': 0,
        'class_order': EXPECTED_ORDER, 'labeled_pixels_by_class': EXPECTED_COUNTS,
    }
    if not isinstance(report, dict) or any(report.get(key) != value for key, value in expected.items()):
        raise ValueError('training audit identity or coverage does not match K34')
    return list(EXPECTED_COUNTS)
