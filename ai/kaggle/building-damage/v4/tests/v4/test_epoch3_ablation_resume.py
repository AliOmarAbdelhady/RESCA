import hashlib
import random

import numpy as np
import torch
import torch.nn.functional as F

import scripts.v4_d0_epoch3_ablation_stage as stage
from rescuevision_ai.v4.losses import masked_damage_cross_entropy


def test_epoch2_resume_produces_same_uniform_update_as_baseline(tmp_path):
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    original = torch.nn.Conv2d(2, 4, 1)
    optimizer = torch.optim.AdamW(original.parameters(), lr=0.003)
    original(torch.ones(1, 2, 1, 2)).sum().backward()
    optimizer.step()
    path = tmp_path / 'epoch2.pt'
    torch.save({'schema_version': 'rv4.d0-epoch.1', 'epoch': 2, 'mode': 'full',
                'manifest_sha256': stage.MANIFEST_HASH, 'source_archive_sha256': 'a' * 64,
                'backbone_weights_sha256': 'b' * 64, 'seed': 42, 'head': original.state_dict(),
                'optimizer': optimizer.state_dict(), 'rng_python': random.getstate(),
                'rng_numpy': np.random.get_state(), 'rng_torch': torch.get_rng_state(),
                'rng_cuda': [], 'scheduler': None, 'scaler': None}, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()

    results = []
    for uniform in (False, True):
        model = torch.nn.Conv2d(2, 4, 1)
        optim = torch.optim.AdamW(model.parameters(), lr=0.3)
        epoch = stage.restore_epoch_checkpoint(path, model, optim, expected_sha256=digest,
            expected_mode='full', expected_source_sha256='a' * 64, expected_weights_sha256='b' * 64)
        assert epoch == 2
        inputs = torch.rand(1, 2, 1, 2)
        labels = torch.tensor([[[0, 3]]])
        valid = torch.tensor([[[True, True]]])
        optim.zero_grad()
        logits = model(inputs)
        loss = (masked_damage_cross_entropy(logits, labels, valid, [1.] * 4) if uniform
                else F.cross_entropy(logits, labels, reduction='none')[valid].mean())
        loss.backward()
        optim.step()
        results.append((loss.detach(), [p.detach().clone() for p in model.parameters()]))
    torch.testing.assert_close(results[0][0], results[1][0])
    for baseline, weighted in zip(results[0][1], results[1][1]):
        torch.testing.assert_close(baseline, weighted)
