"""Kaggle-only bounded DINOv3 supervised and full-tile validation smoke.

This is a correctness gate using a verified grouped manifest, not a training
recipe or a benchmark score. It must run on Kaggle with an assigned GPU.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
import os
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F

from rescuevision.v4.datasets import _rasterize_xbd_label
from rescuevision.v4.evaluation import OfficialAccumulator

MANIFEST_HASH = "4c4a2a19c96198eda84088efcb8dcfbf6eb4d6f6c41b2336853e5cc0c038e619"
DATA_ROOT = Path("/kaggle/input/datasets/tunguz/xview2-challenge-dataset-train-and-test/train/train")
REPO = Path("/kaggle/input/datasets/pr4deepr/dinov3-github-repository/dinov3")
WEIGHTS = Path("/kaggle/input/models/yadavdamodar/dinov3-vitl16-pretrain-sat493m/pytorch/default/1/dinov3_vitl16_pretrain_sat493m-eadcf0ff.pth")
TILE = 512


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checked_path(row: dict, key: str) -> Path:
    rel = Path(row[key + "_relative_path"])
    if rel.is_absolute() or ".." in rel.parts:
        raise RuntimeError(f"unsafe manifest path for {key}")
    path = DATA_ROOT / rel
    if not path.is_file() or sha256(path) != row[key + "_sha256"]:
        raise RuntimeError(f"missing or changed {key} input for {row['sample_id']}")
    return path


def load_sample(row: dict) -> tuple[np.ndarray, ...]:
    paths = {key: checked_path(row, key) for key in ("pre", "post", "pre_label", "label")}
    with Image.open(paths["pre"]) as img:
        pre = np.asarray(img.convert("RGB"), dtype=np.uint8)
    with Image.open(paths["post"]) as img:
        post = np.asarray(img.convert("RGB"), dtype=np.uint8)
    if pre.shape != (1024, 1024, 3) or post.shape != pre.shape:
        raise RuntimeError(f"unexpected image dimensions for {row['sample_id']}")
    loc, _, _, _ = _rasterize_xbd_label(paths["pre_label"], width=1024, height=1024)
    _, damage, _, damage_valid = _rasterize_xbd_label(paths["label"], width=1024, height=1024)
    return pre, post, loc, damage, damage_valid


def image_tensor(image: np.ndarray) -> torch.Tensor:
    value = torch.from_numpy(image.copy()).permute(2, 0, 1).float().div_(255)
    mean = torch.tensor([0.485, 0.456, 0.406])[:, None, None]
    std = torch.tensor([0.229, 0.224, 0.225])[:, None, None]
    return ((value - mean) / std).unsqueeze(0).cuda()


def tokens(backbone: nn.Module, image: np.ndarray) -> torch.Tensor:
    with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16):
        value = backbone.forward_features(image_tensor(image))["x_norm_patchtokens"]
    if tuple(value.shape) != (1, 1024, 1024):
        raise RuntimeError(f"unexpected patch tokens: {tuple(value.shape)}")
    return value.float().reshape(1, 32, 32, 1024).permute(0, 3, 1, 2).contiguous()


def logits_for(backbone: nn.Module, head: nn.Module, pre: np.ndarray, post: np.ndarray) -> torch.Tensor:
    output = head(torch.cat((tokens(backbone, pre), tokens(backbone, post)), dim=1))
    return F.interpolate(output, size=(TILE, TILE), mode="bilinear", align_corners=False)



def restore_epoch_checkpoint(
    path: Path, model: nn.Module, optimizer: torch.optim.Optimizer, *,
    expected_sha256: str, expected_mode: str, expected_source_sha256: str,
    expected_weights_sha256: str,
) -> int:
    """Restore a specifically verified parent and all saved training RNGs."""
    if not path.is_file() or sha256(path) != expected_sha256:
        raise RuntimeError("parent checkpoint is missing or its hash does not match")
    payload = torch.load(path, map_location="cpu", weights_only=False)
    expected = {
        "schema_version": "rv4.d0-epoch.1", "mode": expected_mode,
        "manifest_sha256": MANIFEST_HASH, "source_archive_sha256": expected_source_sha256,
        "backbone_weights_sha256": expected_weights_sha256, "seed": 42,
        "scheduler": None, "scaler": None,
    }
    if any(payload.get(key) != value for key, value in expected.items()):
        raise RuntimeError("parent checkpoint configuration is incompatible")
    epoch = payload.get("epoch")
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
        raise RuntimeError("parent checkpoint epoch is invalid")
    cuda_states = payload.get("rng_cuda")
    if not isinstance(cuda_states, list):
        raise RuntimeError("parent checkpoint CUDA random state is missing")
    if cuda_states and (not torch.cuda.is_available() or len(cuda_states) != torch.cuda.device_count()):
        raise RuntimeError("parent checkpoint CUDA device count is incompatible")
    model.load_state_dict(payload["head"], strict=True)
    optimizer.load_state_dict(payload["optimizer"])
    random.setstate(payload["rng_python"])
    np.random.set_state(payload["rng_numpy"])
    torch.set_rng_state(payload["rng_torch"])
    if cuda_states:
        torch.cuda.set_rng_state_all(cuda_states)
    return epoch


def main() -> None:
    mode = os.environ.get("RV4_D0_MODE", "bounded")
    if mode not in {"bounded", "full"}:
        raise RuntimeError(f"unsupported mode: {mode}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required; refusing CPU fallback")
    seed = 42
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    manifests = list(Path("/kaggle/input").rglob("rv4_xbd_grouped_manifest.jsonl"))
    matches = [path for path in manifests if sha256(path) == MANIFEST_HASH]
    if len(matches) != 1:
        raise RuntimeError(f"verified K20 manifest missing or ambiguous: {len(matches)}")
    rows = [json.loads(line) for line in matches[0].read_text().splitlines() if line.strip()]
    train_all = [row for row in rows if row["split"] == "train"]
    val_all = [row for row in rows if row["split"] == "validation"]
    if len(train_all) != 2660 or len(val_all) != 139:
        raise RuntimeError("audited split count mismatch")
    if len({row["sample_id"] for row in rows}) != len(rows):
        raise RuntimeError("duplicate sample IDs in manifest")
    if {row["event"] for row in train_all} & {row["event"] for row in val_all}:
        raise RuntimeError("event overlap in manifest")
    train = train_all[:4] if mode == "bounded" else train_all
    validation = val_all[:1] if mode == "bounded" else val_all
    if not (REPO / "hubconf.py").is_file() or not WEIGHTS.is_file():
        raise RuntimeError("pinned DINOv3 inputs missing")
    weight_sha = sha256(WEIGHTS)
    source_sha = os.environ.get("RV4_SOURCE_SHA256", "")
    if len(source_sha) != 64:
        raise RuntimeError("source archive hash identity is missing")
    print(f"RV4_STAGE start mode={mode} train={len(train)} validation={len(validation)}", flush=True)
    sys.path.insert(0, str(REPO))
    backbone = torch.hub.load(str(REPO), "dinov3_vitl16", source="local", weights=str(WEIGHTS)).eval().cuda()
    for parameter in backbone.parameters():
        parameter.requires_grad_(False)
    head = nn.Sequential(nn.Conv2d(2048, 256, 1), nn.GroupNorm(32, 256), nn.GELU(), nn.Conv2d(256, 5, 1)).cuda()
    optimizer = torch.optim.AdamW(head.parameters(), lr=3e-4, weight_decay=1e-4)
    parent_hash = {
        "bounded": "9c17c64123103588d0bb8c7a5be1473564932b1cc6ceb906e7a92b043158e822",
        "full": "c04c272b0852066c5752be354e88abc77d809bc2d01796709fbbdb2fbd8e36f0",
    }[mode]
    parent_candidates = list(Path("/kaggle/input").rglob("rv4_d0_epoch_001.pt"))
    parents = [path for path in parent_candidates if sha256(path) == parent_hash]
    if len(parents) != 1:
        raise RuntimeError(f"verified parent checkpoint missing or ambiguous: {len(parents)}")
    parent_epoch = restore_epoch_checkpoint(
        parents[0], head, optimizer, expected_sha256=parent_hash, expected_mode=mode,
        expected_source_sha256="d8148a23bb1c290ce6c014c2f25c2d3ade72232ff37f4e3ca488a828a2fb49b7",
        expected_weights_sha256=weight_sha,
    )
    if parent_epoch != 1:
        raise RuntimeError("this continuation expects an epoch-1 parent")
    epoch = parent_epoch + 1
    print(f"RV4_STAGE resumed epoch={epoch} parent_sha256={parent_hash}", flush=True)
    start = time.monotonic()
    losses = []
    total_damage_pixels = 0
    processed_train = []
    for index, row in enumerate(train):
        pre, post, loc, damage, valid = load_sample(row)
        rng = random.Random(seed + parent_epoch * 100000 + index)
        top, left = rng.randint(0, 512), rng.randint(0, 512)
        sl = np.s_[top:top + TILE, left:left + TILE]
        logits = logits_for(backbone, head, pre[sl], post[sl])
        loc_tensor = torch.from_numpy(loc[sl].copy()).float()[None, None].cuda()
        valid_tensor = torch.from_numpy(valid[sl].copy())[None].cuda()
        damage_tensor = torch.from_numpy(damage[sl].copy()).long()[None].cuda().masked_fill(~valid_tensor, 0)
        loc_loss = F.binary_cross_entropy_with_logits(logits[:, :1], loc_tensor)
        if valid_tensor.any():
            damage_loss = F.cross_entropy(logits[:, 1:], damage_tensor, reduction="none")[valid_tensor].mean()
        else:
            damage_loss = logits[:, 1:].sum() * 0.0
        loss = (loc_loss + damage_loss) * 0.5
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss: {row['sample_id']}")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if not all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters()):
            raise RuntimeError(f"invalid gradients: {row['sample_id']}")
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
        total_damage_pixels += int(valid[sl].sum())
        processed_train.append(row["sample_id"])
        if (index + 1) % 100 == 0:
            print(f"RV4_TRAIN {index + 1}/{len(train)}", flush=True)
    if len(processed_train) != len(train) or total_damage_pixels == 0:
        raise RuntimeError("training coverage or labeled-damage supervision failed")
    head.eval()
    scorer = OfficialAccumulator()
    event_scorers = {}
    prediction_dir = Path("/kaggle/working/rv4_d0_predictions")
    prediction_dir.mkdir(exist_ok=True)
    prediction_artifacts = []
    processed_val = []
    with torch.no_grad():
        for index, row in enumerate(validation):
            pre, post, loc, damage, valid = load_sample(row)
            loc_prob = np.zeros((1024, 1024), dtype=np.float32)
            damage_prob = np.zeros((4, 1024, 1024), dtype=np.float32)
            coverage = np.zeros((1024, 1024), dtype=np.uint8)
            for top in (0, TILE):
                for left in (0, TILE):
                    sl = np.s_[top:top + TILE, left:left + TILE]
                    logits = logits_for(backbone, head, pre[sl], post[sl])
                    loc_prob[sl] = logits[0, 0].sigmoid().cpu().numpy()
                    damage_prob[:, sl[0], sl[1]] = logits[0, 1:].softmax(dim=0).cpu().numpy()
                    coverage[sl] += 1
            if not np.all(coverage == 1):
                raise RuntimeError(f"full-tile coverage failed: {row['sample_id']}")
            loc_pred = (loc_prob >= 0.5).astype(np.uint8)
            damage_pred = (damage_prob.argmax(axis=0) + 1).astype(np.uint8)
            damage_target = np.where(valid, damage + 1, 0).astype(np.uint8)
            scorer.update(loc_pred, damage_pred, loc, damage_target)
            event_scorer = event_scorers.setdefault(row["event"], OfficialAccumulator())
            event_scorer.update(loc_pred, damage_pred, loc, damage_target)
            prediction_path = prediction_dir / f"{row['sample_id']}.npz"
            np.savez_compressed(
                prediction_path, localization=loc_prob.astype(np.float16), damage=damage_prob.astype(np.float16),
                localization_mask=loc_pred, damage_mask=damage_pred,
                localization_target=loc.astype(np.uint8), damage_target=damage_target,
            )
            prediction_artifacts.append({"sample_id": row["sample_id"], "path": str(prediction_path), "sha256": sha256(prediction_path)})
            processed_val.append(row["sample_id"])
            if (index + 1) % 10 == 0:
                print(f"RV4_VALIDATION {index + 1}/{len(validation)}", flush=True)
    if len(processed_val) != len(validation):
        raise RuntimeError("validation coverage mismatch")
    checkpoint = Path(f"/kaggle/working/rv4_d0_epoch_{epoch:03d}.pt")
    torch.save({
        "schema_version": "rv4.d0-epoch.1", "epoch": epoch, "mode": mode,
        "manifest_sha256": MANIFEST_HASH, "source_archive_sha256": source_sha,
        "backbone_weights_sha256": weight_sha, "seed": seed,
        "head": head.state_dict(), "optimizer": optimizer.state_dict(),
        "rng_python": random.getstate(), "rng_numpy": np.random.get_state(),
        "rng_torch": torch.get_rng_state(), "rng_cuda": torch.cuda.get_rng_state_all(),
        "scheduler": None, "scaler": None,
    }, checkpoint)
    saved = torch.load(checkpoint, map_location="cuda", weights_only=False)
    if saved["manifest_sha256"] != MANIFEST_HASH or saved["source_archive_sha256"] != source_sha:
        raise RuntimeError("checkpoint identity mismatch")
    head.load_state_dict(saved["head"])
    optimizer.load_state_dict(saved["optimizer"])
    report = {
        "status": "PASS", "mode": mode, "epoch": epoch,
        "parent_checkpoint_sha256": parent_hash, "parent_epoch": parent_epoch,
        "scope": "grouped xBD training/validation; PIL target-rasterizer parity unverified",
        "manifest_sha256": MANIFEST_HASH, "source_archive_sha256": source_sha,
        "backbone_weights_sha256": weight_sha, "gpu": torch.cuda.get_device_name(),
        "train_planned": len(train), "train_processed": len(processed_train),
        "validation_planned": len(validation), "validation_processed": len(processed_val),
        "train_processed_ids_sha256": hashlib.sha256("\n".join(processed_train).encode()).hexdigest(),
        "validation_processed_ids_sha256": hashlib.sha256("\n".join(processed_val).encode()).hexdigest(),
        "optimizer_steps": len(processed_train), "damage_valid_pixels_in_crops": total_damage_pixels,
        "train_loss_mean": float(np.mean(losses)), "validation_score": scorer.summary(),
        "validation_scores_by_event": {event: acc.summary() for event, acc in event_scorers.items()},
        "validation_threshold": 0.5, "validation_tile_size": TILE, "validation_tta": ["identity"],
        "checkpoint_sha256": sha256(checkpoint), "prediction_artifacts": prediction_artifacts,
        "elapsed_seconds": time.monotonic() - start,
    }
    Path("/kaggle/working/rv4_d0_epoch_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
