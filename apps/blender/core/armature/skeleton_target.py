"""Resolve the active armature target for Proscenio skeleton operations.

The picker on the Skeleton subpanel is the **only** source of truth
at operator time. Heuristics (active object, single-armature scene)
exist solely in the ``auto_populate_active_armature`` handler that
fires on file open / addon enable - they pre-fill the picker so it
visibly reflects what skeleton ops will target. Once the user
explicitly clears the picker via the "x" button, that intent is
respected: ``resolve_skeleton_target`` returns ``None`` and the
caller (Quick Armature) falls back to the auto-created
``Proscenio.QuickRig`` rig.

This keeps the picker / behavior contract honest: what the user
sees in the panel == what the operator targets.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._shared.props_access import active_armature

if TYPE_CHECKING:  # pragma: no cover - typing only
    import bpy


def resolve_skeleton_target(
    context: bpy.types.Context,
) -> bpy.types.Object | None:
    """Return the armature object Proscenio skeleton ops should target.

    Reads ``scene.proscenio.active_armature`` only. ``None`` when the
    picker is unset (initial state or user-cleared) - the caller
    decides whether to fall back to the legacy ``Proscenio.QuickRig``
    auto-create or report a warning.

    The duck-typed accessor pattern (``getattr(...)``) lets the pytest
    suite drive this with ``SimpleNamespace`` mocks; runtime callers
    pass real ``bpy.types.Object`` instances.
    """
    return active_armature(context)
