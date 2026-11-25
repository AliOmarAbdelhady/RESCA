from __future__ import annotations

import hashlib
import random
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

import scripts.v4_d0_epoch_stage as stage


def _checkpoint(path: Path):
    random.seed(17)
    np.random.seed(17)
    torch.manual_seed(17)
    model = nn.Linear(2, 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003)
    optimizer.zero_grad()
    model(torch.tensor([[1.0, 2.0]])).sum().backward()
    optimizer.step()
    payload = {
        'schema_version': 'rv4.d0-epoch.1', 'epoch': 1, 'mode': 'bounded',
        'manifest_sha256': stage.MANIFEST_HASH, 'source_archive_sha256': 'a' * 64,
        'backbone_weights_sha256': 'b' * 64, 'seed': 42,
        'head': model.state_dict(), 'optimizer': optimizer.state_dict(),
        'rng_python': random.getstate(), 'rng_numpy': np.random.get_state(),
        'rng_torch': torch.get_rng_state(), 'rng_cuda': [], 'scheduler': None, 'scaler': None,
    }
    torch.save(payload, path)
    expected_next = (random.random(), float(np.random.random()), float(torch.rand(())))
    return hashlib.sha256(path.read_bytes()).hexdigest(), model, optimizer, expected_next


def test_resume_restores_head_optimizer_epoch_and_rng(tmp_path):
    path = tmp_path / 'checkpoint.pt'
    digest, original, old_optimizer, expected_next = _checkpoint(path)
    assert hasattr(stage, 'restore_epoch_checkpoint')
    model = nn.Linear(2, 1)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.9)
    epoch = stage.restore_epoch_checkpoint(path, model, optimizer, expected_sha256=digest,
        expected_mode='bounded', expected_source_sha256='a' * 64, expected_weights_sha256='b' * 64)
    assert epoch == 1
    assert all(torch.equal(a, b) for a, b in zip(original.parameters(), model.parameters()))
    assert optimizer.param_groups[0]['lr'] == old_optimizer.param_groups[0]['lr']
    assert (random.random(), float(np.random.random()), float(torch.rand(()))) == expected_next


def test_resume_rejects_corrupt_or_incompatible_parent(tmp_path):
    path = tmp_path / 'checkpoint.pt'
    digest, _, _, _ = _checkpoint(path)
    assert hasattr(stage, 'restore_epoch_checkpoint')
    model = nn.Linear(2, 1)
    optimizer = torch.optim.AdamW(model.parameters())
    for changes in ({'expected_sha256': '0' * 64}, {'expected_mode': 'full'},
                    {'expected_source_sha256': 'c' * 64}, {'expected_weights_sha256': 'd' * 64}):
        kwargs = dict(expected_sha256=digest, expected_mode='bounded', expected_source_sha256='a' * 64,
                      expected_weights_sha256='b' * 64)
        kwargs.update(changes)
        with pytest.raises(RuntimeError):
            stage.restore_epoch_checkpoint(path, model, optimizer, **kwargs)
