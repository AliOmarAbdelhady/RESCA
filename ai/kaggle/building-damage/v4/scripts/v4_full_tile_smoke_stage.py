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
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.nn import functional as F

from rescuevision_ai.v4.datasets import _rasterize_xbd_label
from rescuevision_ai.v4.evaluation import OfficialAccumulator

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


def main() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required; refusing CPU fallback")
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    manifests = sorted(Path("/kaggle/input").rglob("rv4_xbd_grouped_manifest.jsonl"))
    matches = [path for path in manifests if sha256(path) == MANIFEST_HASH]
    if len(matches) != 1:
        raise RuntimeError(f"verified K20 manifest missing or ambiguous: {len(matches)} matches")
    rows = [json.loads(line) for line in matches[0].read_text().splitlines() if line.strip()]
    train = [row for row in rows if row["split"] == "train"]
    validation = [row for row in rows if row["split"] == "validation"]
    if len(train) != 2660 or len(validation) != 139:
        raise RuntimeError("manifest split counts differ from the audited split")
    if {row["event"] for row in train} & {row["event"] for row in validation}:
        raise RuntimeError("event overlap in manifest")
    if not (REPO / "hubconf.py").is_file() or not WEIGHTS.is_file():
        raise RuntimeError("pinned DINOv3 repository or weights missing")
    print("RV4_STAGE load_backbone", flush=True)
    sys.path.insert(0, str(REPO))
    backbone = torch.hub.load(str(REPO), "dinov3_vitl16", source="local", weights=str(WEIGHTS)).eval().cuda()
    for parameter in backbone.parameters():
        parameter.requires_grad_(False)
    head = nn.Sequential(nn.Conv2d(2048, 256, 1), nn.GroupNorm(32, 256), nn.GELU(), nn.Conv2d(256, 5, 1)).cuda()
    optimizer = torch.optim.AdamW(head.parameters(), lr=3e-4, weight_decay=1e-4)
    train_samples = []
    start = time.monotonic()
    for row in train:
        pre, post, loc, damage, valid = load_sample(row)
        # This bounded smoke intentionally selects two positive centre crops.
        sl = np.s_[256:768, 256:768]
        if not valid[sl].any():
            continue
        logits = logits_for(backbone, head, pre[sl], post[sl])
        loc_tensor = torch.from_numpy(loc[sl].copy()).float()[None, None].cuda()
        valid_tensor = torch.from_numpy(valid[sl].copy())[None].cuda()
        damage_tensor = torch.from_numpy(damage[sl].copy()).long()[None].cuda().masked_fill(~valid_tensor, 0)
        loc_loss = F.binary_cross_entropy_with_logits(logits[:, :1], loc_tensor)
        damage_loss = F.cross_entropy(logits[:, 1:], damage_tensor, reduction="none")[valid_tensor].mean()
        loss = (loc_loss + damage_loss) * 0.5
        if not torch.isfinite(loss):
            raise RuntimeError("non-finite supervised loss")
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if not all(p.grad is not None and torch.isfinite(p.grad).all() for p in head.parameters()):
            raise RuntimeError("missing or non-finite head gradients")
        optimizer.step()
        train_samples.append({"sample_id": row["sample_id"], "valid_damage_pixels": int(valid[sl].sum()), "loss": float(loss.detach().cpu())})
        if len(train_samples) == 2:
            break
    if len(train_samples) != 2:
        raise RuntimeError("fewer than two positive training crops")
    print("RV4_STAGE full_tile_validation", flush=True)
    head.eval()
    row = validation[0]
    pre, post, loc, damage, valid = load_sample(row)
    loc_pred = np.zeros((1024, 1024), dtype=np.uint8)
    damage_pred = np.zeros((1024, 1024), dtype=np.uint8)
    coverage = np.zeros((1024, 1024), dtype=np.uint8)
    with torch.no_grad():
        for top in (0, TILE):
            for left in (0, TILE):
                sl = np.s_[top:top + TILE, left:left + TILE]
                logits = logits_for(backbone, head, pre[sl], post[sl])
                loc_pred[sl] = (logits[0, 0].sigmoid().cpu().numpy() >= 0.5).astype(np.uint8)
                damage_pred[sl] = (logits[0, 1:].argmax(dim=0).cpu().numpy() + 1).astype(np.uint8)
                coverage[sl] += 1
    if not np.all(coverage == 1):
        raise RuntimeError("full-tile validation coverage mismatch")
    damage_target = np.where(valid, damage + 1, 0).astype(np.uint8)
    scorer = OfficialAccumulator()
    scorer.update(loc_pred, damage_pred, loc.astype(np.uint8), damage_target)
    ckpt = Path("/kaggle/working/rv4_full_tile_smoke.pt")
    torch.save({"head": head.state_dict(), "optimizer": optimizer.state_dict(), "manifest_sha256": MANIFEST_HASH}, ckpt)
    reloaded = torch.load(ckpt, map_location="cuda", weights_only=False)
    if reloaded["manifest_sha256"] != MANIFEST_HASH:
        raise RuntimeError("checkpoint manifest identity mismatch")
    head.load_state_dict(reloaded["head"])
    optimizer.load_state_dict(reloaded["optimizer"])
    report = {
        "status": "PASS", "purpose": "bounded full-tile smoke; not a benchmark or training result",
        "manifest_sha256": MANIFEST_HASH, "gpu": torch.cuda.get_device_name(),
        "train_samples": train_samples, "optimizer_steps": len(train_samples),
        "validation_sample": row["sample_id"], "validation_tiles": 4,
        "validation_covered_pixels": int((coverage > 0).sum()),
        "pre_localization_pixels": int(loc.sum()), "post_damage_valid_pixels": int(valid.sum()),
        "metric_scope": "single grouped-validation image; PIL target rasterization not yet independently verified",
        "scorer_smoke": scorer.summary(), "checkpoint_sha256": sha256(ckpt),
        "elapsed_seconds": time.monotonic() - start,
    }
    Path("/kaggle/working/rv4_full_tile_smoke.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
