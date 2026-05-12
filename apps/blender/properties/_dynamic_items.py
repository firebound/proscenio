"""EnumProperty dynamic-items + PointerProperty poll callbacks (SPEC 009 wave 9.7).

Isolates the small bpy-side gotchas that surround the
``ProscenioObjectProps`` driver picker:

- ``_is_armature``: PointerProperty.poll filter that gates the
  Armature picker to ARMATURE objects only.
- ``_driver_bone_items``: dynamic items callback for the
  ``driver_source_bone`` Enum.
- The module-level cache that pins the items list for the lifetime
  of the addon, dodging the EnumProperty GC bug where Blender frees
  the returned list mid-draw and corrupts the UI strings.
- ``_on_any_update``: shared update callback that mirrors every PG
  field to its Custom Property on every edit (post-005.1.c.1 fix).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

from ..core.mirror import mirror_all_fields  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from .object_props import ProscenioObjectProps


def is_armature(_self: object, obj: bpy.types.Object) -> bool:
    """PointerProperty poll: only allow ARMATURE objects in the picker."""
    return bool(obj.type == "ARMATURE")


# Module-level cache: Blender's EnumProperty with a callable ``items=``
# GCs the returned list as soon as the callback exits, which corrupts
# the tuple strings shown in the UI ("Detected EnumProperty items
# mismatch" + garbled labels). Keeping the per-armature list reachable
# here pins the references for the lifetime of the addon.
_DRIVER_BONE_ITEMS_CACHE: dict[int, list[tuple[str, str, str]]] = {}
_NO_ARMATURE_ITEMS: tuple[tuple[str, str, str], ...] = (("", "(pick an armature first)", ""),)
_NO_BONES_ITEMS: tuple[tuple[str, str, str], ...] = (("", "(armature has no bones)", ""),)


def driver_bone_items(
    self: ProscenioObjectProps,
    _context: bpy.types.Context | None,
) -> list[tuple[str, str, str]] | tuple[tuple[str, str, str], ...]:
    """Dynamic items for the ``driver_source_bone`` dropdown.

    Walks the picked ``driver_source_armature`` and lists every bone by
    name. Falls back to a sentinel placeholder when no armature is
    picked or the armature has no bones - keeps the dropdown clickable
    instead of vanishing the whole row.
    """
    armature = self.driver_source_armature
    if armature is None:
        return _NO_ARMATURE_ITEMS
    bones = getattr(getattr(armature, "data", None), "bones", None)
    if bones is None or len(bones) == 0:
        return _NO_BONES_ITEMS
    items = [(bone.name, bone.name, "") for bone in bones]
    _DRIVER_BONE_ITEMS_CACHE[id(armature)] = items
    return items


def on_any_update(self: ProscenioObjectProps, context: bpy.types.Context) -> None:
    """Mirror every field on any panel edit.

    Bug fix (post-005.1.c.1): individual per-field callbacks left the
    CP set partial - defaults never fired their callback, so Reload
    Scripts restored only the field the user touched. Mirroring all 10
    fields on every update keeps the CP snapshot complete after the
    first interaction.
    """
    obj = context.active_object
    if obj is not None:
        mirror_all_fields(self, obj)
