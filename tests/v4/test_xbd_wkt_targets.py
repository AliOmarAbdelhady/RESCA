from __future__ import annotations

import json
import hashlib

import pytest
import numpy as np
from PIL import Image, ImageDraw
import rescuevision.v4.datasets as datasets

from rescuevision.v4.contracts import ContractError
from rescuevision.v4.datasets import _rasterize_xbd_label


def _write_label(path, features):
    path.write_text(json.dumps({"features": features}), encoding="utf-8")


def test_pixel_wkt_polygon_and_hole_are_rasterized(tmp_path):
    path = tmp_path / "label.json"
    _write_label(path, {"xy": [{"properties": {"subtype": "major-damage"},
        "wkt": "POLYGON ((1 1, 8 1, 8 8, 1 8, 1 1), (3 3, 6 3, 6 6, 3 6, 3 3))"}],
        "lng_lat": []})
    loc, damage, _, valid = _rasterize_xbd_label(path, width=10, height=10)
    assert loc[2, 2] == 1 and damage[2, 2] == 2 and valid[2, 2]
    assert loc[4, 4] == 0 and not valid[4, 4]


def test_lng_lat_only_is_rejected_instead_of_used_as_pixels(tmp_path):
    path = tmp_path / "label.json"
    _write_label(path, {"lng_lat": [{"wkt": "POLYGON ((0 0, 1 0, 1 1, 0 0))"}]})
    with pytest.raises(ContractError, match="pixel"):
        _rasterize_xbd_label(path, width=10, height=10)


def test_bad_pixel_wkt_is_rejected(tmp_path):
    path = tmp_path / "label.json"
    _write_label(path, {"xy": [{"properties": {"subtype": "no-damage"}, "wkt": "invalid"}]})
    with pytest.raises(ContractError, match="geometry"):
        _rasterize_xbd_label(path, width=10, height=10)


def test_self_intersection_cannot_silently_change_target(tmp_path):
    path = tmp_path / "label.json"
    _write_label(path, {"xy": [{"properties": {"subtype": "no-damage", "uid": "2aaab43d-9165-49eb-8dee-a16d86f40e57"},
        "wkt": "POLYGON ((806.6023403473426 581.3467453360512, 811.070729347672 581.3467453360512, 810.6645121651652 604.5011247134614, 785.4790468774745 603.6886903484475, 785.4790468789738 623.1871150897915, 813.1999303498654 622.9633712757255, 813.5080324414639 647.560146012224, 765.9806221408822 647.9663631942311, 765.5744049581256 580.9405281530445, 807.0085575281005 581.3467453360512, 806.6023403473426 581.3467453360512))"}]})
    loc, damage, _, valid = _rasterize_xbd_label(path, width=1024, height=1024)
    assert loc[600, 780] == 1 and damage[600, 780] == 0 and valid[600, 780]


def test_unrecognized_invalid_polygon_is_rejected(tmp_path):
    path = tmp_path / "label.json"
    _write_label(path, {"xy": [{"properties": {"subtype": "no-damage"},
        "wkt": "POLYGON ((8 1, 9 1, 9 8, 1 8, 1 1, 8.5 1, 8 1))"}]})
    with pytest.raises(ContractError, match="geometry"):
        _rasterize_xbd_label(path, width=12, height=12)


def test_audited_invalid_pre_polygon_preserves_original_raster(tmp_path, monkeypatch):
    raw = "POLYGON ((8 1, 9 1, 9 8, 1 8, 1 1, 8.5 1, 8 1))"
    uid = "audited-fixture"
    monkeypatch.setattr(datasets, "_AUDITED_PRE_INVALID_WKT", {uid: hashlib.sha256(raw.encode()).hexdigest()}, raising=False)
    path = tmp_path / "label.json"
    _write_label(path, {"xy": [{"properties": {"uid": uid}, "wkt": raw}]})
    loc, _, _, _ = _rasterize_xbd_label(path, width=12, height=12)
    expected = Image.new("L", (12, 12), 0)
    ImageDraw.Draw(expected).polygon([(8, 1), (9, 1), (9, 8), (1, 8), (1, 1), (8.5, 1), (8, 1)], fill=1)
    assert np.array_equal(loc, np.asarray(expected))
