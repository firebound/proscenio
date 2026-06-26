"""Bone appearance operators: assign a custom shape, color a collection.

Both act on the Skeleton-picked armature. ``assign_bone_shape`` sets a generated
2D widget as the ``custom_shape`` of the active bone, the selected bones, or a
whole collection; ``color_bone_collection`` batches ``bone.color`` over every
bone in a collection, since Blender has no native per-collection color. The two
share the collection-iteration helper with the Rig UI select operator.
"""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
)

from ...core._shared.report import report_warn  # type: ignore[import-not-found]
from ...core.armature.skeleton_target import (  # type: ignore[import-not-found]
    resolve_skeleton_target,
)
from ...core.bpy_helpers._shared.bone_collections import (  # type: ignore[import-not-found]
    iter_collection_bones,
)
from ...core.bpy_helpers.bone_widgets import (  # type: ignore[import-not-found]
    SHAPE_IDS,
    ensure_bone_widget,
)

_SHAPE_ITEMS = tuple((sid, sid.capitalize(), f"2D {sid} outline") for sid in SHAPE_IDS)

_SCOPE_ITEMS = (
    ("ACTIVE", "Active", "Assign to the active bone only"),
    ("SELECTED", "Selected", "Assign to every selected bone"),
    ("COLLECTION", "Collection", "Assign to every bone in a bone collection"),
)

#: Bone-color palette ids: DEFAULT (inherit), the 15 theme slots, and CUSTOM.
_PALETTE_ITEMS = (
    ("DEFAULT", "Default", "No themed color - inherit"),
    *[(f"THEME{i:02d}", f"Theme {i:02d}", f"Theme color {i:02d}") for i in range(1, 16)],
    ("CUSTOM", "Custom", "Use the custom color triplet below"),
)


def _pose_bones_for_scope(
    armature: bpy.types.Object, scope: str, collection_name: str
) -> list[bpy.types.PoseBone]:
    """Resolve the target pose bones for an assignment scope.

    ACTIVE = the armature's active bone, SELECTED = every selected bone,
    COLLECTION = the named collection's bones. Names are mapped through
    ``armature.pose.bones`` so a missing pose bone is simply skipped.
    """
    pose = getattr(armature, "pose", None)
    if pose is None:
        return []
    if scope == "COLLECTION":
        names = [b.name for b in iter_collection_bones(armature, collection_name)]
    elif scope == "SELECTED":
        names = [pb.name for pb in pose.bones if pb.bone.select]
    else:  # ACTIVE
        active = getattr(armature.data, "bones", None)
        active_bone = getattr(active, "active", None)
        names = [active_bone.name] if active_bone is not None else []
    return [pose.bones[n] for n in names if n in pose.bones]


class PROSCENIO_OT_assign_bone_shape(bpy.types.Operator):
    """Assign a generated 2D custom shape to the scoped bones."""

    bl_idname = "proscenio.assign_bone_shape"
    bl_label = "Proscenio: Assign Bone Shape"
    bl_description = (
        "Set a generated 2D outline as the custom shape of the active bone, the "
        "selected bones, or a whole bone collection"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    shape: EnumProperty(  # type: ignore[valid-type]
        name="Shape",
        items=_SHAPE_ITEMS,
        default="circle",
    )
    scope: EnumProperty(  # type: ignore[valid-type]
        name="Scope",
        items=_SCOPE_ITEMS,
        default="ACTIVE",
    )
    collection_name: StringProperty(  # type: ignore[valid-type]
        name="Bone collection",
        default="",
    )
    shape_scale: FloatProperty(  # type: ignore[valid-type]
        name="Scale",
        default=1.0,
        min=0.01,
        soft_max=5.0,
    )
    offset: FloatProperty(  # type: ignore[valid-type]
        name="Offset",
        description="Slide the shape along the bone",
        default=0.0,
        soft_min=-2.0,
        soft_max=2.0,
    )
    clear: BoolProperty(  # type: ignore[valid-type]
        name="Clear",
        description="Remove the custom shape from the scoped bones instead of assigning one",
        default=False,
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = resolve_skeleton_target(context)
        if armature is None:
            report_warn(self, "no armature picked - pick one in the Skeleton panel", always=True)
            return {"CANCELLED"}
        targets = _pose_bones_for_scope(armature, self.scope, self.collection_name)
        if not targets:
            report_warn(self, "no target bones for this scope")
            return {"CANCELLED"}
        # Clear: empty the custom_shape (the native "remove" is blanking the
        # Custom Object field in Bone Properties; this is the panel shortcut).
        if self.clear:
            for pose_bone in targets:
                pose_bone.custom_shape = None
            return {"FINISHED"}
        widget = ensure_bone_widget(self.shape)
        for pose_bone in targets:
            pose_bone.custom_shape = widget
            pose_bone.custom_shape_scale_xyz = (self.shape_scale,) * 3
            pose_bone.custom_shape_translation = (0.0, self.offset, 0.0)
        return {"FINISHED"}


class PROSCENIO_OT_color_bone_collection(bpy.types.Operator):
    """Apply a bone color to every bone in a collection in one click.

    Blender has no per-collection color, so this batches ``bone.color`` over the
    collection's data bones, leaving the pose-bone override at DEFAULT so the
    color stays consistent across pose. A theme palette by default, with a
    custom triplet when the palette is CUSTOM.
    """

    bl_idname = "proscenio.color_bone_collection"
    bl_label = "Proscenio: Color Bone Collection"
    bl_description = "Apply a bone color to every bone in this collection at once"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        default="",
    )
    collection_name: StringProperty(  # type: ignore[valid-type]
        name="Bone collection",
        default="",
    )
    palette: EnumProperty(  # type: ignore[valid-type]
        name="Palette",
        items=_PALETTE_ITEMS,
        default="THEME01",
    )
    custom_normal: FloatVectorProperty(  # type: ignore[valid-type]
        name="Regular",
        subtype="COLOR",
        size=3,
        min=0.0,
        max=1.0,
        default=(0.8, 0.2, 0.2),
    )
    custom_select: FloatVectorProperty(  # type: ignore[valid-type]
        name="Selected",
        subtype="COLOR",
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 0.4, 0.4),
    )
    custom_active: FloatVectorProperty(  # type: ignore[valid-type]
        name="Active",
        subtype="COLOR",
        size=3,
        min=0.0,
        max=1.0,
        default=(1.0, 0.6, 0.6),
    )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.prop(self, "palette")
        if self.palette == "CUSTOM":
            layout.prop(self, "custom_normal")
            layout.prop(self, "custom_select")
            layout.prop(self, "custom_active")

    def execute(self, _context: bpy.types.Context) -> set[str]:
        armature = bpy.data.objects.get(self.armature_name)
        if armature is None or armature.type != "ARMATURE":
            report_warn(self, f"armature '{self.armature_name}' not found")
            return {"CANCELLED"}
        bones = iter_collection_bones(armature, self.collection_name)
        if not bones:
            report_warn(self, f"collection '{self.collection_name}' has no bones")
            return {"CANCELLED"}
        for bone in bones:
            bone.color.palette = self.palette
            if self.palette == "CUSTOM":
                bone.color.custom.normal = self.custom_normal
                bone.color.custom.select = self.custom_select
                bone.color.custom.active = self.custom_active
        # Bone colors only render when the armature's "Bone Colors" viewport
        # display is on; a rig with it off would show no change, reading as "the
        # color did nothing". Enable it so the applied color is visible.
        armature.data.show_bone_colors = True
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_assign_bone_shape,
    PROSCENIO_OT_color_bone_collection,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
