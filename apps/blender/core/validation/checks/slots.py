"""Slot check: walk slot Empties + cross-check name uniqueness."""

from __future__ import annotations

from collections.abc import Sequence

from ...slot.slot_emit import is_slot_empty
from .._shared import name_of
from ..active_slot import validate_active_slot
from ..issue import Issue


def validate_slots(scene_objects: Sequence[object]) -> list[Issue]:
    """Walk slot Empties + cross-check name uniqueness."""
    seen: set[str] = set()
    issues: list[Issue] = []
    for obj in scene_objects:
        if not is_slot_empty(obj):
            continue
        name = name_of(obj)
        if name in seen:
            issues.append(Issue("error", f"duplicate slot name '{name}'", name))
        seen.add(name)
        issues.extend(validate_active_slot(obj))
    return issues
