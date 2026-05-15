"""Resolve the active armature target for Proscenio skeleton operations.

bpy-bound (lazy ``bpy`` import to keep direct ``core/`` modules import
clean for ``pytest`` consumers that only need the pure-Python helpers
elsewhere in the package).

Resolution order (SPEC 012.2 hybrid Opcao A.5 + B):

1. ``scene.proscenio.active_armature`` pointer set explicitly by the
   user via the Skeleton subpanel - always wins.
2. ``context.view_layer.objects.active`` when it is an Armature
   object - matches the long-standing Blender expectation that "the
   active object is what you operate on".
3. The scene contains exactly one Armature - auto-pick it so the
   common single-rig workflow needs zero clicks.
4. ``None`` - caller decides whether to fall back to the legacy
   Proscenio.QuickRig auto-create or report a warning.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    import bpy


def resolve_skeleton_target(
    context: bpy.types.Context,
) -> bpy.types.Object | None:
    """Return the armature object Proscenio skeleton ops should target.

    See module docstring for the resolution order.
    """
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    proscenio = getattr(scene, "proscenio", None)
    if proscenio is not None:
        explicit = getattr(proscenio, "active_armature", None)
        if explicit is not None and explicit.type == "ARMATURE":
            return explicit
    view_layer = getattr(context, "view_layer", None)
    if view_layer is not None:
        active = view_layer.objects.active
        if active is not None and active.type == "ARMATURE":
            return active
    armatures = [obj for obj in scene.objects if obj.type == "ARMATURE"]
    if len(armatures) == 1:
        return armatures[0]
    return None
