"""Proscenio panels package (SPEC 009 wave 9.3).

The sidebar is anchored by ``PROSCENIO_PT_main``. Every other panel is
a child via ``bl_parent_id``, which gives us collapsible subsections
users can fold individually. Subpanels poll on the active selection
(or scene state) so empty subpanels do not clutter the sidebar.

Submodules per concern:

- _helpers.py        - cross-cutting (header drawer, mode predicates)
- active_sprite.py   - PROSCENIO_PT_active_sprite + 9 helpers
- active_slot.py     - PROSCENIO_PT_active_slot + attachment helpers
- skeleton.py        - PROSCENIO_PT_skeleton + UL_bones
- outliner.py        - PROSCENIO_PT_outliner + UL_sprite_outliner
- animation.py       - PROSCENIO_PT_animation + UL_actions
- atlas.py           - PROSCENIO_PT_atlas + packer box
- validation.py      - PROSCENIO_PT_validation
- export.py          - PROSCENIO_PT_export
- help.py            - PROSCENIO_PT_help
- diagnostics.py     - PROSCENIO_PT_diagnostics
"""

from __future__ import annotations

import bpy

from . import (
    active_slot,
    active_sprite,
    animation,
    atlas,
    diagnostics,
    export,
    help,
    outliner,
    skeleton,
    validation,
)


class PROSCENIO_PT_main(bpy.types.Panel):
    """Sidebar root - version banner; child panels do the work."""

    bl_label = "Proscenio"
    bl_idname = "PROSCENIO_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row()
        row.label(text="Pipeline v0.1.0")
        right = row.row()
        right.alignment = "RIGHT"
        op = right.operator("proscenio.help", text="", icon="QUESTION", emboss=False)
        op.topic = "pipeline_overview"


_main_classes: tuple[type, ...] = (PROSCENIO_PT_main,)


def register() -> None:
    for cls in _main_classes:
        bpy.utils.register_class(cls)
    active_sprite.register()
    active_slot.register()
    skeleton.register()
    outliner.register()
    animation.register()
    atlas.register()
    validation.register()
    export.register()
    help.register()
    diagnostics.register()


def unregister() -> None:
    diagnostics.unregister()
    help.unregister()
    export.unregister()
    validation.unregister()
    atlas.unregister()
    animation.unregister()
    outliner.unregister()
    skeleton.unregister()
    active_slot.unregister()
    active_sprite.unregister()
    for cls in reversed(_main_classes):
        bpy.utils.unregister_class(cls)
