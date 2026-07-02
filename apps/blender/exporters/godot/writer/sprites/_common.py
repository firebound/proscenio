"""Shared element helpers used by both the mesh and sprite paths."""

from __future__ import annotations

import bpy

from .....core._shared.cp_keys import PROSCENIO_Y_DRAW_ORDER
from .....core._shared.pg_cp_fallback import read_field
from .....core.bpy_helpers._shared._bpy_compat import (
    object_color,
    vertex_group_at,
)

_OPAQUE_WHITE = [1.0, 1.0, 1.0, 1.0]


def _derive_modulate(obj: bpy.types.Object) -> list[float] | None:
    """RGBA tint from the native object color, or None when opaque white.

    Reads ``Object.color`` so appearance needs no new authoring surface; an
    object with no tint emits nothing and keeps the goldens stable.
    """
    color = [round(c, 6) for c in object_color(obj)]
    return None if color == _OPAQUE_WHITE else color


def _derive_z_index(obj: bpy.types.Object) -> int | None:
    """Godot ``z_index`` from the stored Y Location (Draw Order) layer.

    ``y_draw_order`` is the authoritative whole-number draw order; Godot draws
    a higher ``z_index`` on top, so negate to keep "higher order = further
    back". Reads the PropertyGroup first, the Custom Property fallback second
    (the headless writer path). The object's actual Y is just the order times
    the addon spacing, so the export never reads ``location.y`` and never
    depends on the spacing preference. A net-zero order emits nothing.
    """
    order = int(read_field(obj, cp_key=PROSCENIO_Y_DRAW_ORDER, default=0))
    return -order or None


def resolve_sprite_bone(obj: bpy.types.Object) -> str:
    if obj.parent_type == "BONE" and obj.parent_bone:
        return str(obj.parent_bone)
    if obj.vertex_groups:
        return str(vertex_group_at(obj, 0).name)
    return ""
