import pytest
import torch
import torch.nn.functional as F

from rescuevision_ai.v4.losses import masked_damage_cross_entropy


def test_uniform_weights_match_baseline_loss_and_gradient():
    logits = torch.tensor([[[[1., -1.]], [[0., 1.]], [[-1., 0.]], [[0.5, 0.5]]]], requires_grad=True)
    labels = torch.tensor([[[0, 2]]])
    valid = torch.tensor([[[True, True]]])
    weighted = masked_damage_cross_entropy(logits, labels, valid, [1., 1., 1., 1.])
    gradient = torch.autograd.grad(weighted, logits, retain_graph=True)[0]
    baseline = F.cross_entropy(logits, labels, reduction='none')[valid].mean()
    baseline_gradient = torch.autograd.grad(baseline, logits)[0]
    torch.testing.assert_close(weighted, baseline)
    torch.testing.assert_close(gradient, baseline_gradient)


def test_weighted_mean_and_ignored_pixels():
    logits = torch.tensor([[[[3., 0., 1.]], [[0., 0., 0.]], [[0., 0., 0.]], [[0., 0., 0.]]]], requires_grad=True)
    labels = torch.tensor([[[0, 1, 255]]])
    valid = torch.tensor([[[True, True, False]]])
    loss = masked_damage_cross_entropy(logits, labels, valid, [1., 3., 1., 1.])
    values = F.cross_entropy(logits[:, :, :, :2], labels[:, :, :2], reduction='none')
    expected = (values[0, 0, 0] + 3 * values[0, 0, 1]) / 4
    torch.testing.assert_close(loss, expected)
    gradient = torch.autograd.grad(loss, logits)[0]
    assert torch.count_nonzero(gradient[:, :, :, 2]) == 0


def test_empty_mask_returns_finite_zero_with_zero_gradient():
    logits = torch.randn(1, 4, 1, 2, requires_grad=True)
    loss = masked_damage_cross_entropy(logits, torch.full((1, 1, 2), 255), torch.zeros((1, 1, 2), dtype=torch.bool), [1., 2., 3., 4.])
    assert torch.isfinite(loss) and loss.item() == 0
    loss.backward()
    assert torch.count_nonzero(logits.grad) == 0


def test_each_damage_class_contributes_gradient():
    logits = torch.zeros(1, 4, 1, 4, requires_grad=True)
    labels = torch.tensor([[[0, 1, 2, 3]]])
    valid = torch.ones_like(labels, dtype=torch.bool)
    masked_damage_cross_entropy(logits, labels, valid, [0.67, 1.65, 1.46, 2.13]).backward()
    assert torch.all(logits.grad.abs().sum(dim=1) > 0)


def test_invalid_supervised_label_is_rejected():
    with pytest.raises(ValueError):
        masked_damage_cross_entropy(torch.zeros(1, 4, 1, 1), torch.full((1, 1, 1), 255), torch.ones(1, 1, 1, dtype=torch.bool), [1.] * 4)


@pytest.mark.parametrize('weights', [[1., 1., 1.], [1., 0., 1., 1.], [1., -1., 1., 1.], [1., float('nan'), 1., 1.]])
def test_invalid_weights_are_rejected(weights):
    with pytest.raises(ValueError):
        masked_damage_cross_entropy(torch.zeros(1, 4, 1, 1), torch.zeros(1, 1, 1, dtype=torch.long), torch.ones(1, 1, 1, dtype=torch.bool), weights)
