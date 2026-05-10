"""Driver shortcut operator (SPEC 005.1.d.1)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import EnumProperty, StringProperty

from ..core.props_access import object_props  # type: ignore[import-not-found]
from ..core.report import report_error, report_info  # type: ignore[import-not-found]

_DRIVER_VAR_NAME = "var"
_DRIVER_TARGET_PROPERTIES: tuple[tuple[str, str, str], ...] = (
    ("frame", "Frame index", "Sprite-frame index -- driven 0..hframes*vframes"),
    ("region_x", "Region X", "Texture region origin X (0..1)"),
    ("region_y", "Region Y", "Texture region origin Y (0..1)"),
    ("region_w", "Region W", "Texture region width (0..1)"),
    ("region_h", "Region H", "Texture region height (0..1)"),
)
_DRIVER_SOURCE_AXES: tuple[tuple[str, str, str], ...] = (
    ("ROT_Z", "Bone Rot Z", "Pose bone local rotation around Z (typical 2D plane)"),
    ("ROT_X", "Bone Rot X", "Pose bone local rotation around X"),
    ("ROT_Y", "Bone Rot Y", "Pose bone local rotation around Y"),
    ("LOC_X", "Bone Loc X", "Pose bone local translation X"),
    ("LOC_Y", "Bone Loc Y", "Pose bone local translation Y"),
    ("LOC_Z", "Bone Loc Z", "Pose bone local translation Z"),
)


def _ensure_single_driver(
    sprite: bpy.types.Object,
    data_path: str,
) -> bpy.types.FCurve:
    """Idempotent: drop any existing driver on ``data_path`` first, then add fresh.

    After ``driver_add`` Blender seeds the fcurve with default keyframes
    around the property's current value, with constant extrapolation.
    Those keyframes act as an output remap that clamps every driver
    expression result to the [first_key, last_key] range -- silently
    breaking the feature for property values outside that band. Strip
    them so the driver expression result passes through 1:1.
    """
    if sprite.animation_data is not None:
        existing = sprite.animation_data.drivers.find(data_path)
        if existing is not None:
            sprite.driver_remove(data_path)
    fcurve = sprite.driver_add(data_path)
    while fcurve.keyframe_points:
        fcurve.keyframe_points.remove(fcurve.keyframe_points[0])
    return fcurve


class PROSCENIO_OT_create_driver(bpy.types.Operator):
    """Drive a sprite's `proscenio.<prop>` from a chosen pose bone (5.1.d.1)."""

    bl_idname = "proscenio.create_driver"
    bl_label = "Proscenio: Drive Sprite from Bone"
    bl_description = (
        "Adds a driver to the active sprite's proscenio property using "
        "the armature/bone selected in the panel. Re-running on the same "
        "sprite + target property replaces the driver."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    target_property: EnumProperty(  # type: ignore[valid-type]
        name="Target",
        description="Sprite proscenio property the driver writes to",
        items=_DRIVER_TARGET_PROPERTIES,
        default="region_x",
    )
    source_axis: EnumProperty(  # type: ignore[valid-type]
        name="Source",
        description="Pose bone transform channel feeding the driver",
        items=_DRIVER_SOURCE_AXES,
        default="ROT_Z",
    )
    expression: StringProperty(  # type: ignore[valid-type]
        name="Expression",
        description=(
            "Driver expression. 'var' is the bone channel; edit in the "
            "Drivers Editor for scaling / offsets / branching."
        ),
        default="var",
    )
    armature_name: StringProperty(  # type: ignore[valid-type]
        name="Armature",
        description="Name of the armature object hosting the source bone",
        default="",
    )
    bone_name: StringProperty(  # type: ignore[valid-type]
        name="Bone",
        description="Pose bone whose transform feeds the driver",
        default="",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        sprite = context.active_object
        if sprite is None or sprite.type != "MESH":
            return False
        return hasattr(sprite, "proscenio")

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        """Pre-fill operator props from the active sprite's PropertyGroup."""
        sprite = context.active_object
        if sprite is not None:
            props = object_props(sprite)
            if props is not None:
                self.target_property = str(props.driver_target)
                self.source_axis = str(props.driver_source_axis)
                self.expression = str(props.driver_expression) or "var"
                arm = props.driver_source_armature
                self.armature_name = arm.name if arm is not None else ""
                self.bone_name = str(props.driver_source_bone)
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        sprite = context.active_object
        props = object_props(sprite)
        if sprite is None or sprite.type != "MESH" or props is None:
            report_error(self, "select a sprite mesh as the active object")
            return {"CANCELLED"}

        armature = bpy.data.objects.get(self.armature_name) if self.armature_name else None
        if armature is None or armature.type != "ARMATURE":
            report_error(self, "pick a source armature in the panel")
            return {"CANCELLED"}
        bones = getattr(armature.data, "bones", None)
        if bones is None or self.bone_name not in bones:
            report_error(self, f"bone '{self.bone_name}' not in armature '{armature.name}'")
            return {"CANCELLED"}

        data_path = f"proscenio.{self.target_property}"
        try:
            fcurve = _ensure_single_driver(sprite, data_path)
        except (TypeError, RuntimeError) as exc:
            report_error(self, f"could not add driver on {data_path}: {exc}")
            return {"CANCELLED"}

        driver = fcurve.driver
        driver.type = "SCRIPTED"
        driver.expression = self.expression or "var"
        var = driver.variables[0] if driver.variables else driver.variables.new()
        var.name = _DRIVER_VAR_NAME
        var.type = "TRANSFORMS"
        target = var.targets[0]
        target.id = armature
        target.bone_target = self.bone_name
        target.transform_type = self.source_axis
        # WORLD_SPACE matches 2D-cutout convention: rotation around the
        # world Z (or Y for front-ortho rigs) is what the animator means
        # when they R Z 45 in pose mode, regardless of the bone's local
        # axis orientation. LOCAL_SPACE returns 0 when the bone axis
        # happens to align with the rotation axis (e.g. vertical bones
        # rotated around world Z).
        target.transform_space = "WORLD_SPACE"
        # XYZ Euler keeps the variable in radians instead of returning
        # quaternion components (sin(angle/2)) that confuse expressions.
        target.rotation_mode = "XYZ"

        # Mirror redo-panel overrides back to the PropertyGroup.
        props.driver_target = self.target_property
        props.driver_source_axis = self.source_axis
        props.driver_expression = self.expression or "var"
        props.driver_source_armature = armature
        props.driver_source_bone = self.bone_name

        report_info(
            self,
            f"driver on '{sprite.name}.{data_path}' "
            f"<- {armature.name}:{self.bone_name}.{self.source_axis}",
        )
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_create_driver,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
