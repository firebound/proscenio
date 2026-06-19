"""Incorporate a hand-authored Blender mesh as a Proscenio element.

A mesh modelled directly in Blender carries no Proscenio element data, so the
pipeline does not recognize it. This operator adopts it: a single quad (4 verts
/ 1 face) defaults to a Sprite, any denser mesh to a Mesh, and the user can
override the choice in the redo panel. It sets ``element_type`` plus the same
sensible defaults the Element panel controls, then stamps the Custom Property
mirror so the element is recognized end to end. Mirrors the Create Slot shape
(a button plus its adjust/redo dialog).
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import EnumProperty, IntProperty

from ..core._shared.report import report_error, report_info  # type: ignore[import-not-found]
from ..core.mirror import mirror_all_fields  # type: ignore[import-not-found]
from ..properties.object_props import ELEMENT_TYPE_ITEMS  # type: ignore[import-not-found]


def _is_single_quad(obj: bpy.types.Object) -> bool:
    """True when the mesh is a single quad (4 verts / 1 face) - the sprite shape."""
    mesh = getattr(obj, "data", None)
    vertices = getattr(mesh, "vertices", None)
    polygons = getattr(mesh, "polygons", None)
    if vertices is None or polygons is None:
        return False
    return len(vertices) == 4 and len(polygons) == 1


class PROSCENIO_OT_incorporate_element(bpy.types.Operator):
    """Adopt a hand-authored Blender mesh as a Proscenio Mesh or Sprite element."""

    bl_idname = "proscenio.incorporate_element"
    bl_label = "Proscenio: Incorporate as Element"
    bl_description = (
        "Adopt this hand-authored mesh as a Proscenio element. A single quad "
        "defaults to Sprite, any denser mesh to Mesh - override in the redo panel"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    element_type: EnumProperty(  # type: ignore[valid-type]
        name="Element type",
        description="Adopt as a deformable Mesh (Polygon2D) or a rigid Sprite (Sprite2D)",
        items=ELEMENT_TYPE_ITEMS,
        default="mesh",
    )
    hframes: IntProperty(  # type: ignore[valid-type]
        name="Horizontal frames",
        description="Spritesheet column count (sprite only)",
        default=1,
        min=1,
        soft_max=64,
    )
    vframes: IntProperty(  # type: ignore[valid-type]
        name="Vertical frames",
        description="Spritesheet row count (sprite only)",
        default=1,
        min=1,
        soft_max=64,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        # Only offer for a mesh not already carrying element data - an imported or
        # already-incorporated element stamps the proscenio_type Custom Property.
        return obj is not None and obj.type == "MESH" and obj.get("proscenio_type") is None

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        """Seed the element type from the geometry heuristic, then incorporate."""
        obj = context.active_object
        self.element_type = "sprite" if obj is not None and _is_single_quad(obj) else "mesh"
        return self.execute(context)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "element_type")
        if self.element_type == "sprite":
            layout.prop(self, "hframes")
            layout.prop(self, "vframes")

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_error(self, "select a mesh object to incorporate")
            return {"CANCELLED"}
        props = getattr(obj, "proscenio", None)
        if props is None:
            report_error(self, "Proscenio property group not registered")
            return {"CANCELLED"}
        props.element_type = self.element_type
        if self.element_type == "sprite":
            props.hframes = self.hframes
            props.vframes = self.vframes
            props.frame = 0
            props.centered = True
        # Stamp the Custom Property mirror explicitly: assigning a field that
        # already holds its value fires no update callback, so the mirror (and
        # the proscenio_type marker the panel + poll key on) must be written
        # here regardless of whether element_type actually changed.
        mirror_all_fields(props, obj)
        report_info(self, f"incorporated '{obj.name}' as a {self.element_type} element")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_incorporate_element,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
