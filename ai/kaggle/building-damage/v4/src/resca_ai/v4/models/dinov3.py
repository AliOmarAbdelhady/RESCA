"""DINOv3 feature extraction with explicit token-grid validation."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import torch
from torch import Tensor, nn


class TokenGridError(ValueError):
    """Raised when a DINO output cannot be mapped to the declared patch grid."""


def extract_spatial_tokens(
    tokens: Tensor,
    *,
    grid_size: tuple[int, int],
    num_prefix_tokens: int | None = None,
) -> Tensor:
    """Convert a token sequence to ``[B,C,grid_h,grid_w]``.

    The caller must declare the number of non-spatial prefix tokens whenever
    the sequence contains more tokens than the patch grid.  This prevents a
    loader from silently treating class/register tokens as image features.
    """

    if tokens.ndim != 3:
        raise TokenGridError(f"expected [B,N,C] tokens, got shape {tuple(tokens.shape)}")
    grid_h, grid_w = grid_size
    expected_spatial = grid_h * grid_w
    batch, token_count, channels = tokens.shape
    if num_prefix_tokens is None:
        if token_count != expected_spatial:
            raise TokenGridError(
                "token sequence has non-spatial tokens; declare num_prefix_tokens "
                f"for {token_count} tokens and grid {grid_size}"
            )
        num_prefix_tokens = 0
    if num_prefix_tokens < 0 or token_count != num_prefix_tokens + expected_spatial:
        raise TokenGridError(
            f"token count {token_count} does not equal prefix {num_prefix_tokens} "
            f"plus grid {grid_size}"
        )
    spatial = tokens[:, num_prefix_tokens:, :]
    return spatial.reshape(batch, grid_h, grid_w, channels).permute(0, 3, 1, 2).contiguous()


class FrozenDINOv3Features(nn.Module):
    """Run a DINOv3 backbone in frozen no-gradient feature mode."""

    def __init__(self, backbone: nn.Module, *, patch_size: int = 16) -> None:
        super().__init__()
        if patch_size <= 0:
            raise ValueError("patch_size must be positive")
        self.backbone = backbone
        self.patch_size = patch_size
        for parameter in self.backbone.parameters():
            parameter.requires_grad_(False)
        self.backbone.eval()

    def forward(self, pixel_values: Tensor) -> Tensor:
        if pixel_values.ndim != 4:
            raise TokenGridError("pixel_values must have shape [B,3,H,W]")
        height, width = pixel_values.shape[-2:]
        if height % self.patch_size or width % self.patch_size:
            raise TokenGridError(
                f"input {(height, width)} is not divisible by patch size {self.patch_size}"
            )
        with torch.no_grad():
            output = self.backbone(pixel_values)
            tokens, prefix = _tokens_and_prefix(output, self.backbone)
            return extract_spatial_tokens(
                tokens,
                grid_size=(height // self.patch_size, width // self.patch_size),
                num_prefix_tokens=prefix,
            )


def _tokens_and_prefix(output: Any, backbone: nn.Module) -> tuple[Tensor, int | None]:
    patch_tokens = getattr(output, "x_norm_patchtokens", None)
    if patch_tokens is None and isinstance(output, dict):
        patch_tokens = output.get("x_norm_patchtokens")
    if isinstance(patch_tokens, Tensor):
        return patch_tokens, 0

    tokens = getattr(output, "last_hidden_state", None)
    if tokens is None and isinstance(output, dict):
        tokens = output.get("last_hidden_state")
    if not isinstance(tokens, Tensor):
        raise TokenGridError("DINOv3 output has no supported spatial token field")

    config = getattr(backbone, "config", None)
    register_tokens = getattr(config, "num_register_tokens", None)
    if isinstance(register_tokens, int) and register_tokens >= 0:
        return tokens, 1 + register_tokens
    return tokens, None


def load_dinov3_satellite(
    model_id: str = "facebook/dinov3-vitl16-pretrain-sat493m",
    *,
    revision: str | None = None,
    device: str | torch.device | None = None,
) -> FrozenDINOv3Features:
    """Load an explicitly requested Hugging Face DINOv3 revision.

    This function performs the network/model load only when called by an
    execution stage. Ordinary unit tests use stand-ins and never invoke it.
    """

    try:
        from transformers import AutoModel
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("transformers is required to load DINOv3") from exc
    kwargs: dict[str, Any] = {"trust_remote_code": True}
    if revision is not None:
        kwargs["revision"] = revision
    backbone = AutoModel.from_pretrained(model_id, **kwargs)
    wrapper = FrozenDINOv3Features(backbone)
    if device is not None:
        wrapper = wrapper.to(device)
    return wrapper

