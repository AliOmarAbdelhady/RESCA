from __future__ import annotations

import torch

from rescuevision.v4.training import (
    masked_binary_bce_dice_loss,
    masked_damage_ce_dice_loss,
    optimizer_step_due,
)


def test_masked_losses_are_finite_and_backpropagate() -> None:
    loc_logits = torch.zeros((2, 1, 3, 3), requires_grad=True)
    loc_target = torch.randint(0, 2, (2, 3, 3), dtype=torch.float32)
    loc_valid = torch.ones((2, 3, 3), dtype=torch.bool)
    damage_logits = torch.zeros((2, 4, 3, 3), requires_grad=True)
    damage_target = torch.randint(0, 4, (2, 3, 3), dtype=torch.long)
    damage_valid = torch.ones((2, 3, 3), dtype=torch.bool)

    loss = masked_binary_bce_dice_loss(loc_logits, loc_target, loc_valid)
    loss = loss + masked_damage_ce_dice_loss(damage_logits, damage_target, damage_valid)
    loss.backward()

    assert torch.isfinite(loss)
    assert loc_logits.grad is not None and torch.isfinite(loc_logits.grad).all()
    assert damage_logits.grad is not None and torch.isfinite(damage_logits.grad).all()


def test_empty_valid_masks_return_differentiable_zero() -> None:
    loc_logits = torch.randn((1, 1, 2, 2), requires_grad=True)
    damage_logits = torch.randn((1, 4, 2, 2), requires_grad=True)
    empty = torch.zeros((1, 2, 2), dtype=torch.bool)

    loss = masked_binary_bce_dice_loss(loc_logits, torch.zeros_like(empty, dtype=torch.float32), empty)
    loss = loss + masked_damage_ce_dice_loss(
        damage_logits, torch.zeros_like(empty, dtype=torch.long), empty
    )
    loss.backward()

    assert loss.item() == 0.0
    assert loc_logits.grad is not None and torch.equal(loc_logits.grad, torch.zeros_like(loc_logits))
    assert damage_logits.grad is not None and torch.equal(
        damage_logits.grad, torch.zeros_like(damage_logits)
    )


def test_partial_final_accumulation_still_steps_optimizer() -> None:
    due = [optimizer_step_due(index, total_batches=5, accumulation_steps=2) for index in range(5)]

    assert due == [False, True, False, True, True]
