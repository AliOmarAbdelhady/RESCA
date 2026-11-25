"""Losses, deterministic checkpoints and the V4 baseline train entry point."""

from __future__ import annotations

import os
import random
import uuid
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch
from torch import Tensor
from torch.nn import functional as F
from torch.utils.data import DataLoader

from .artifacts import validate_resume
from .contracts import ExperimentConfig
from .datasets import PairedDataset
from .models.cnn import PairedCNN


def masked_binary_bce_dice_loss(logits: Tensor, target: Tensor, valid: Tensor) -> Tensor:
    """Masked BCE plus foreground Dice with a differentiable empty-set zero."""

    if logits.ndim != 4 or logits.shape[1] != 1:
        raise ValueError("localization logits must have shape [B,1,H,W]")
    target = target.to(dtype=logits.dtype)
    valid = valid.to(dtype=torch.bool)
    if target.ndim == 3:
        target = target.unsqueeze(1)
    if valid.ndim == 3:
        valid = valid.unsqueeze(1)
    if target.shape != logits.shape or valid.shape != logits.shape:
        raise ValueError("localization target and valid mask must match logits")
    if not valid.any():
        return logits.sum() * 0.0
    pointwise = F.binary_cross_entropy_with_logits(logits, target, reduction="none")
    bce = pointwise[valid].mean()
    probabilities = logits.sigmoid()[valid]
    target_values = target[valid]
    intersection = (probabilities * target_values).sum()
    dice = (2.0 * intersection + 1e-6) / (
        probabilities.sum() + target_values.sum() + 1e-6
    )
    return 0.5 * bce + 0.5 * (1.0 - dice)


def masked_damage_ce_dice_loss(logits: Tensor, target: Tensor, valid: Tensor) -> Tensor:
    """Masked four-grade CE plus mean per-class Dice."""

    if logits.ndim != 4 or logits.shape[1] != 4:
        raise ValueError("damage logits must have shape [B,4,H,W]")
    target = target.to(dtype=torch.long)
    valid = valid.to(dtype=torch.bool)
    if target.ndim != 3 or valid.ndim != 3 or target.shape != logits.shape[0:1] + logits.shape[2:]:
        raise ValueError("damage target and valid mask must have shape [B,H,W]")
    if not valid.any():
        return logits.sum() * 0.0
    safe_target = target.masked_fill(~valid, 0)
    pointwise = F.cross_entropy(logits, safe_target, reduction="none")
    ce = pointwise[valid].mean()
    probabilities = logits.softmax(dim=1)
    one_hot = F.one_hot(safe_target.clamp(0, 3), num_classes=4).permute(0, 3, 1, 2)
    valid_4d = valid.unsqueeze(1)
    dice_values: list[Tensor] = []
    for class_id in range(4):
        predicted = probabilities[:, class_id][valid]
        observed = one_hot[:, class_id].to(dtype=logits.dtype)[valid]
        intersection = (predicted * observed).sum()
        dice_values.append(
            (2.0 * intersection + 1e-6)
            / (predicted.sum() + observed.sum() + 1e-6)
        )
    del valid_4d
    return 0.5 * ce + 0.5 * (1.0 - torch.stack(dice_values).mean())


def composite_loss(outputs: Mapping[str, Tensor], batch: Mapping[str, Tensor]) -> Tensor:
    return 0.5 * masked_binary_bce_dice_loss(
        outputs["loc_logits"], batch["loc_target"], batch["loc_valid"]
    ) + 0.5 * masked_damage_ce_dice_loss(
        outputs["damage_logits"], batch["damage_target"], batch["damage_valid"]
    )


def optimizer_step_due(batch_index: int, *, total_batches: int, accumulation_steps: int) -> bool:
    if total_batches <= 0 or accumulation_steps <= 0:
        raise ValueError("total_batches and accumulation_steps must be positive")
    return (batch_index + 1) % accumulation_steps == 0 or batch_index == total_batches - 1


def capture_rng_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
    }
    if torch.cuda.is_available():
        state["cuda"] = torch.cuda.get_rng_state_all()
    return state


def restore_rng_state(state: Mapping[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if torch.cuda.is_available() and "cuda" in state:
        torch.cuda.set_rng_state_all(state["cuda"])


def save_checkpoint(
    path: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    scaler: Any,
    metadata: Mapping[str, Any],
    state: Mapping[str, Any],
) -> None:
    """Atomically save all state needed for an epoch-boundary resume."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "metadata": dict(metadata),
        "state": dict(state),
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scheduler": scheduler.state_dict() if scheduler is not None else None,
        "scaler": scaler.state_dict() if scaler is not None else None,
        "rng": capture_rng_state(),
    }
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_checkpoint(
    path: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    scaler: Any,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load an atomic checkpoint and restore model/optimizer/RNG state."""

    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location="cpu")
    model.load_state_dict(payload["model"])
    optimizer.load_state_dict(payload["optimizer"])
    if scheduler is not None and payload.get("scheduler") is not None:
        scheduler.load_state_dict(payload["scheduler"])
    if scaler is not None and payload.get("scaler") is not None:
        scaler.load_state_dict(payload["scaler"])
    if payload.get("rng") is not None:
        restore_rng_state(payload["rng"])
    return dict(payload["metadata"]), dict(payload["state"])


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def train(config_path: Path, resume: Path | None = None) -> Path:
    """Run the declared baseline for one epoch-boundary-resumable chunk.

    This local entry point deliberately keeps the first implementation small;
    native crops, validation and official promotion are added only after the
    CPU audit and GPU smoke gates pass.
    """

    from .contracts import load_experiment

    config: ExperimentConfig = load_experiment(config_path)
    set_seed(config.seed)
    if config.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("configuration requested cuda but no CUDA device is available")
    device = torch.device(
        "cuda" if config.device == "cuda" or (config.device == "auto" and torch.cuda.is_available()) else "cpu"
    )
    model = PairedCNN(backbone="resnet34").to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    loader = DataLoader(
        PairedDataset(config.train_manifest, split="train"),
        batch_size=min(config.microbatch_size, config.effective_batch_size),
        shuffle=True,
        num_workers=config.num_workers,
    )
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": config.schema_version,
        "model_id": config.model_id,
        "model_revision": config.model_revision,
        "normalization_id": config.normalization_id,
        "resolution_policy": config.resolution_policy,
        "source_revision": config.source_revision,
        "data_revision": config.data_revision,
    }
    if resume is not None:
        checkpoint_metadata, checkpoint_state = load_checkpoint(
            resume, model=model, optimizer=optimizer, scheduler=None, scaler=None
        )
        validate_resume(checkpoint_metadata, metadata)
        start_epoch = int(checkpoint_state.get("epoch", 0))
    else:
        start_epoch = 0
    accumulation_steps = max(1, math.ceil(config.effective_batch_size / config.microbatch_size))
    for epoch in range(start_epoch, config.max_epochs):
        model.train()
        total_batches = len(loader)
        optimizer.zero_grad(set_to_none=True)
        for batch_index, batch in enumerate(loader):
            outputs = model(batch["pre"].to(device), batch["post"].to(device))
            loss = composite_loss(
                outputs,
                {key: value.to(device) for key, value in batch.items() if isinstance(value, Tensor)},
            )
            (loss / accumulation_steps).backward()
            if optimizer_step_due(
                batch_index,
                total_batches=total_batches,
                accumulation_steps=accumulation_steps,
            ):
                torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip_norm)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
        save_checkpoint(
            output_dir / "last.pt",
            model=model,
            optimizer=optimizer,
            scheduler=None,
            scaler=None,
            metadata=metadata,
            state={"epoch": epoch + 1, "optimizer_updates": total_batches},
        )
    return output_dir

