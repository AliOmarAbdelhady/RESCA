"""Shared validation helpers for the post-only and defect task adapters."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


class TaskAdapterError(ValueError):
    """Raised when a specialist-task annotation or split violates its contract."""


def assert_grouped_split_integrity(
    records: Iterable[Mapping[str, Any]],
    *,
    group_fields: Sequence[str],
) -> None:
    """Reject structure/photo groups that occur in more than one split.

    A visible fragment can have several rows in one split, but a structure or
    capture group must never be used as both training and evaluation evidence.
    Missing group identifiers are rejected instead of silently weakening the
    split guarantee.
    """

    if not group_fields:
        raise TaskAdapterError("at least one grouped split field is required")
    seen: dict[str, dict[str, str]] = {field: {} for field in group_fields}
    for index, record in enumerate(records):
        split = record.get("split")
        if not isinstance(split, str) or not split.strip():
            raise TaskAdapterError(f"record {index} has no non-empty split")
        for field in group_fields:
            group = record.get(field)
            if not isinstance(group, str) or not group.strip():
                raise TaskAdapterError(f"record {index} has no non-empty {field}")
            prior_split = seen[field].get(group)
            if prior_split is not None and prior_split != split:
                raise TaskAdapterError(
                    f"{field} {group!r} occurs in both {prior_split!r} and {split!r} splits"
                )
            seen[field][group] = split
