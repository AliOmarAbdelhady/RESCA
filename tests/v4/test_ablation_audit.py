import pytest

from rescuevision.v4.ablation_audit import validate_training_audit


def valid_report():
    return {'status': 'PASS', 'manifest_sha256': '4c4a2a19c96198eda84088efcb8dcfbf6eb4d6f6c41b2336853e5cc0c038e619',
            'training_labels_processed': 2660, 'validation_labels_opened': 0,
            'class_order': ['no-damage', 'minor-damage', 'major-damage', 'destroyed'],
            'labeled_pixels_by_class': [92406627, 15508042, 19792146, 9309230]}


def test_verified_training_report_is_accepted():
    assert validate_training_audit(valid_report()) == [92406627, 15508042, 19792146, 9309230]


@pytest.mark.parametrize('field,value', [
    ('status', 'ERROR'), ('manifest_sha256', '0' * 64), ('training_labels_processed', 2659),
    ('validation_labels_opened', 1), ('labeled_pixels_by_class', [1, 2, 3, 4]),
    ('class_order', ['minor-damage', 'no-damage', 'major-damage', 'destroyed']),
])
def test_changed_or_leaking_report_is_rejected(field, value):
    report = valid_report()
    report[field] = value
    with pytest.raises(ValueError):
        validate_training_audit(report)
