"""Proscenio panels package.

Every tool is a sibling top-level panel in the ``Proscenio`` tab,
ordered by ``bl_order``. ``PROSCENIO_PT_main`` is the footer (version
banner + repo link), pinned last with a high ``bl_order``. Panels poll
on the active selection (or scene state) so irrelevant panels stay out
of the way.

Submodules per concern:

- _helpers.py        - cross-cutting (header drawer, mode predicates)
- element.py         - PROSCENIO_PT_element + per-kind subpanels
- slots.py           - PROSCENIO_PT_slots + Active Slot subpanel
- helpers.py         - PROSCENIO_PT_helpers (Preview Camera)
- skeleton.py        - PROSCENIO_PT_skeleton + UL_bones
- mesh_generation.py - PROSCENIO_PT_mesh_generation + automesh subpanels
- weight_paint.py     - PROSCENIO_PT_weight_paint + bind / weight subpanels
- outliner.py        - PROSCENIO_PT_outliner + UL_sprite_outliner
- animation.py       - PROSCENIO_PT_animation + UL_actions
- atlas.py           - PROSCENIO_PT_atlas + packer box
- validation.py      - PROSCENIO_PT_validation
- pipeline.py        - PROSCENIO_PT_pipeline + Import/Export subpanels
- help.py            - PROSCENIO_PT_help
- diagnostics.py     - PROSCENIO_PT_diagnostics
"""

from __future__ import annotations

import bpy

from . import (
    animation,
    atlas,
    diagnostics,
    element,
    help,
    helpers,
    mesh_generation,
    outliner,
    pipeline,
    skeleton,
    slots,
    validation,
    weight_paint,
)


class PROSCENIO_PT_main(bpy.types.Panel):
    """Sidebar footer - version banner + repo link, pinned below every tool panel."""

    bl_label = "About"
    bl_idname = "PROSCENIO_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Proscenio"
    bl_order = 100

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row(align=True)
        row.label(text="Pipeline v0.1.0")
        right = row.row(align=True)
        right.alignment = "RIGHT"
        gh = right.operator("wm.url_open", text="", icon="URL", emboss=False)
        gh.url = "https://github.com/Space-Wizard-Studios/firebound-proscenio"
        op = right.operator("proscenio.help", text="", icon="QUESTION", emboss=False)
        op.topic = "pipeline_overview"


_main_classes: tuple[type, ...] = (PROSCENIO_PT_main,)


def register() -> None:
    outliner.register()
    element.register()
    slots.register()
    skeleton.register()
    mesh_generation.register()
    weight_paint.register()
    animation.register()
    atlas.register()
    validation.register()
    pipeline.register()
    helpers.register()
    help.register()
    diagnostics.register()
    for cls in _main_classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_main_classes):
        bpy.utils.unregister_class(cls)
    diagnostics.unregister()
    help.unregister()
    helpers.unregister()
    pipeline.unregister()
    validation.unregister()
    atlas.unregister()
    animation.unregister()
    weight_paint.unregister()
    mesh_generation.unregister()
    skeleton.unregister()
    slots.unregister()
    element.unregister()
    outliner.unregister()
