from __future__ import annotations

from pathlib import Path

import torch

from rescuevision_ai.v4.artifacts import validate_resume
from rescuevision_ai.v4.models.cnn import PairedCNN
from rescuevision_ai.v4.training import (
    capture_rng_state,
    load_checkpoint,
    restore_rng_state,
    save_checkpoint,
)


def _step(model: PairedCNN, optimizer: torch.optim.Optimizer, batch: tuple[torch.Tensor, ...]) -> float:
    pre, post, loc_target, damage_target = batch
    output = model(pre, post)
    loss = output["loc_logits"].square().mean() + output["damage_logits"].square().mean()
    loss.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    return float(loss.detach())


def test_epoch_boundary_resume_restores_weights_and_rng(tmp_path: Path) -> None:
    torch.manual_seed(17)
    batches = [
        (
            torch.randn(1, 3, 8, 8),
            torch.randn(1, 3, 8, 8),
            torch.zeros(1, 8, 8),
            torch.zeros(1, 8, 8, dtype=torch.long),
        ),
        (
            torch.randn(1, 3, 8, 8),
            torch.randn(1, 3, 8, 8),
            torch.ones(1, 8, 8),
            torch.ones(1, 8, 8, dtype=torch.long),
        ),
    ]
    model_a = PairedCNN(backbone="tiny", base_channels=4)
    optimizer_a = torch.optim.SGD(model_a.parameters(), lr=0.01)
    metadata = {
        "schema_version": "v4.0",
        "model_id": "paired_cnn_baseline",
        "model_revision": "cnn-r1",
        "normalization_id": "imagenet_rgb_v1",
        "train_manifest_sha256": "train",
        "validation_manifest_sha256": "val",
        "audit_manifest_sha256": "audit",
    }
    _step(model_a, optimizer_a, batches[0])
    checkpoint = tmp_path / "checkpoint.pt"
    save_checkpoint(
        checkpoint,
        model=model_a,
        optimizer=optimizer_a,
        scheduler=None,
        scaler=None,
        metadata=metadata,
        state={"epoch": 1, "optimizer_updates": 1},
    )
    _step(model_a, optimizer_a, batches[1])
    final_a = {name: value.detach().clone() for name, value in model_a.state_dict().items()}

    model_b = PairedCNN(backbone="tiny", base_channels=4)
    optimizer_b = torch.optim.SGD(model_b.parameters(), lr=0.01)
    loaded_metadata, state = load_checkpoint(
        checkpoint, model=model_b, optimizer=optimizer_b, scheduler=None, scaler=None
    )
    validate_resume(loaded_metadata, metadata)
    assert state == {"epoch": 1, "optimizer_updates": 1}
    _step(model_b, optimizer_b, batches[1])

    for name, value in model_b.state_dict().items():
        assert torch.allclose(value, final_a[name], atol=1e-6, rtol=0.0), name


def test_rng_state_round_trip() -> None:
    torch.manual_seed(123)
    state = capture_rng_state()
    first = torch.rand(4)
    restore_rng_state(state)
    second = torch.rand(4)

    assert torch.equal(first, second)
