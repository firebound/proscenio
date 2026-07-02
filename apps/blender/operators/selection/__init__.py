"""Selection operators: validation issue, outliner row, favorites, bone rows.

Covers the issue / outliner / action row clicks and favorite toggles, plus the
Skeleton-list bone-row affordances: the connectivity info tooltip, the Relative
Parenting toggle, the per-bone favorite, and the Rig UI collection-select.

Split into ``objects`` / ``bones`` / ``actions`` with a shared ``_shared``; this
package facade re-exports the operator classes and registers them so the
``bl_idname`` strings and the aggregator's ``register()`` call are unchanged.
"""

from __future__ import annotations

import bpy

from .actions import PROSCENIO_OT_set_active_action
from .bones import (
    PROSCENIO_OT_select_bone_by_name,
    PROSCENIO_OT_select_bone_collection,
    PROSCENIO_OT_toggle_bone_export,
    PROSCENIO_OT_toggle_bone_favorite,
    PROSCENIO_OT_toggle_bone_relative_parent,
)
from .objects import (
    PROSCENIO_OT_select_issue_object,
    PROSCENIO_OT_select_outliner_object,
    PROSCENIO_OT_toggle_outliner_favorite,
)

_classes: tuple[type, ...] = (
    PROSCENIO_OT_select_issue_object,
    PROSCENIO_OT_select_outliner_object,
    PROSCENIO_OT_select_bone_by_name,
    PROSCENIO_OT_set_active_action,
    PROSCENIO_OT_toggle_outliner_favorite,
    PROSCENIO_OT_toggle_bone_relative_parent,
    PROSCENIO_OT_toggle_bone_favorite,
    PROSCENIO_OT_toggle_bone_export,
    PROSCENIO_OT_select_bone_collection,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
