"""Viewport-authoring helper operators (the Helpers panel).

Hosts the ``Re-space planes`` operator: it rewrites every Proscenio plane's
Y to ``y_draw_order * spacing`` so a changed Y Location spacing preference
takes effect, and so a plane dragged off its layer snaps back. The Preview
Camera operator lives under ``armature/`` for historical reasons.
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..addon_prefs import y_location_spacing  # type: ignore[import-not-found]
from ..core._shared.cp_keys import PROSCENIO_Y_DRAW_ORDER  # type: ignore[import-not-found]
from ..core._shared.pg_cp_fallback import read_field  # type: ignore[import-not-found]
from ..core._shared.report import report_info  # type: ignore[import-not-found]
from ..core.slot.slot_emit import is_slot_empty  # type: ignore[import-not-found]


class PROSCENIO_OT_respace_planes(bpy.types.Operator):
    """Re-apply the Y Location spacing to every Proscenio plane.

    Each element's Y is set to ``y_draw_order * spacing``. Use it after
    changing the Y Location spacing preference, or to snap a plane that was
    dragged off its layer back onto it. Slot-attached meshes are skipped -
    the slot owns their placement.
    """

    bl_idname = "proscenio.respace_planes"
    bl_label = "Proscenio: Re-space Planes"
    bl_description = (
        "Set every Proscenio element's Y to its draw-order layer times the "
        "Y Location spacing preference. Applies a changed spacing and snaps "
        "planes dragged off their layer back into place"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        spacing = y_location_spacing(context)
        moved = 0
        for obj in context.scene.objects:
            if obj.type != "MESH" or obj.get("proscenio_type") is None:
                continue
            if is_slot_empty(obj.parent):
                continue
            order = int(read_field(obj, cp_key=PROSCENIO_Y_DRAW_ORDER, default=0))
            obj.location.y = order * spacing
            moved += 1
        report_info(self, f"re-spaced {moved} plane(s) at {spacing:g} per layer")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_respace_planes,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
