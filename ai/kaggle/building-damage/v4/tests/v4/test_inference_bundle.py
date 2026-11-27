from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import pytest
import torch
from torch import nn

from rescuevision_ai.v4.artifacts import ArtifactIntegrityError
from rescuevision_ai.v4.bundle import (
    BundleSpec,
    bundle_preprocessing_identity,
    load_inference_bundle,
    prediction_digest,
    write_inference_bundle,
)
from rescuevision_ai.v4.inference import InferenceRecipe, predict_pair


class _ConstantPairModel(nn.Module):
    def forward(self, pre: torch.Tensor, post: torch.Tensor) -> dict[str, torch.Tensor]:
        batch, _, height, width = pre.shape
        loc = torch.zeros((batch, 1, height, width), device=pre.device)
        damage = torch.zeros((batch, 4, height, width), device=pre.device)
        damage[:, 1] = 4.0
        return {"loc_logits": loc, "damage_logits": damage}


def _spec() -> BundleSpec:
    return BundleSpec(
        model_id="paired_cnn_baseline",
        model_revision="cnn-r1",
        source_revision="local-v4",
        data_revision="xbd-official-to-be-resolved",
        normalization_id="imagenet_rgb_v1",
        resolution_policy="native_512_crop",
        label_map={"undamaged": 1, "minor": 2, "major": 3, "destroyed": 4},
        recipe=InferenceRecipe(tile_size=4, stride=3, tta=("identity", "hflip")),
    )


def test_bundle_loads_and_verifies_checkpoint_and_recipe(tmp_path: Path) -> None:
    checkpoint = tmp_path / "source.pt"
    torch.save({"state_dict": {"weight": torch.ones(1)}}, checkpoint)
    bundle_dir = tmp_path / "bundle"

    write_inference_bundle(bundle_dir, checkpoint_path=checkpoint, spec=_spec())
    loaded = load_inference_bundle(bundle_dir)

    assert loaded.spec.model_id == "paired_cnn_baseline"
    assert loaded.spec.recipe.tile_size == 4
    assert loaded.checkpoint_path.is_file()
    assert loaded.checkpoint_sha256 == loaded.metadata["checkpoint"]["sha256"]


def test_bundle_rejects_corrupt_checkpoint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "source.pt"
    checkpoint.write_bytes(b"checkpoint")
    bundle_dir = tmp_path / "bundle"
    write_inference_bundle(bundle_dir, checkpoint_path=checkpoint, spec=_spec())
    bundled_checkpoint = bundle_dir / "weights/checkpoint.pt"
    bundled_checkpoint.write_bytes(b"corrupted")

    with pytest.raises(ArtifactIntegrityError, match="sha256 mismatch"):
        load_inference_bundle(bundle_dir)


def test_bundle_rejects_tampered_preprocessing_identity(tmp_path: Path) -> None:
    checkpoint = tmp_path / "source.pt"
    checkpoint.write_bytes(b"checkpoint")
    bundle_dir = tmp_path / "bundle"
    write_inference_bundle(bundle_dir, checkpoint_path=checkpoint, spec=_spec())
    metadata_path = bundle_dir / "bundle.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["preprocessing_identity"] = "0" * 64
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    with pytest.raises(ValueError, match="preprocessing identity"):
        load_inference_bundle(bundle_dir)


def test_preprocessing_identity_changes_when_recipe_or_normalization_changes() -> None:
    recipe = _spec().recipe
    base = bundle_preprocessing_identity("imagenet_rgb_v1", "native_512_crop", recipe)
    changed = bundle_preprocessing_identity(
        "dinov3_sat493m_rgb_v1", "native_512_crop", recipe
    )
    changed_recipe = bundle_preprocessing_identity(
        "imagenet_rgb_v1",
        "native_512_crop",
        InferenceRecipe(tile_size=8, stride=4, tta=recipe.tta),
    )

    assert len(base) == 64
    assert base != changed
    assert base != changed_recipe


def test_bundle_recipe_preserves_native_shape_and_reference_digest(tmp_path: Path) -> None:
    checkpoint = tmp_path / "source.pt"
    checkpoint.write_bytes(b"checkpoint")
    bundle_dir = tmp_path / "bundle"
    write_inference_bundle(bundle_dir, checkpoint_path=checkpoint, spec=_spec())
    loaded = load_inference_bundle(bundle_dir)

    pre = np.zeros((7, 11, 3), dtype=np.uint8)
    post = np.full((7, 11, 3), 255, dtype=np.uint8)
    model = _ConstantPairModel()
    prediction_a = predict_pair(pre, post, model, loaded.spec.recipe)
    prediction_b = predict_pair(pre, post, model, loaded.spec.recipe)

    assert prediction_a.original_size == (7, 11)
    assert prediction_a.localization_probability.shape == (7, 11)
    assert prediction_a.damage_probability.shape == (4, 7, 11)
    assert prediction_digest(prediction_a) == prediction_digest(prediction_b)
