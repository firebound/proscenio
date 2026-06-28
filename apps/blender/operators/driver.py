"""Driver shortcut operator (the Drive-from-Bone shortcut)."""

from __future__ import annotations

from typing import ClassVar

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty

from ..core._shared.props_access import object_props  # type: ignore[import-not-found]
from ..core._shared.report import (  # type: ignore[import-not-found]
    report_error,
    report_info,
    report_warn,
)
from ..core.armature.driver_expression import (  # type: ignore[import-not-found]
    DRIVER_SOURCE_AXIS_ITEMS,
    build_driver_expression,
)
from ..core.armature.driver_targets import (  # type: ignore[import-not-found]
    DRIVER_TARGET_PROPERTIES,
    driver_data_path,
    is_proscenio_driver_path,
)

_DRIVER_VAR_NAME = "var"


def _ensure_single_driver(
    sprite: bpy.types.Object,
    data_path: str,
    source_armature: bpy.types.Object,
    source_bone: str,
) -> bpy.types.FCurve:
    """Idempotent: drop any existing driver on ``data_path`` first, then add fresh.

    Also drops sibling ``proscenio.*`` drivers off the same ``(armature,
    bone)`` source, so changing the ``Target`` property on redo does not
    leave the old driver on the previous ``data_path``. Consequence: a
    sprite cannot host two proscenio drivers off the same bone.

    ``driver_add`` seeds the fcurve with constant-extrapolation keyframes
    around the property's current value; those clamp every expression
    result to the [first_key, last_key] band, so strip them to let the
    expression pass through 1:1.
    """
    _purge_stale_drivers(sprite, data_path, source_armature, source_bone)
    fcurve = sprite.driver_add(data_path)
    while fcurve.keyframe_points:
        fcurve.keyframe_points.remove(fcurve.keyframe_points[0])
    return fcurve


def _purge_stale_drivers(
    sprite: bpy.types.Object,
    data_path: str,
    source_armature: bpy.types.Object,
    source_bone: str,
) -> None:
    """Remove driver on ``data_path`` plus any sibling proscenio driver
    sourced from the same ``(armature, bone)`` pair."""
    if sprite.animation_data is None:
        return
    existing = sprite.animation_data.drivers.find(data_path)
    if existing is not None:
        sprite.driver_remove(data_path)
    stale_paths = [
        fc.data_path
        for fc in sprite.animation_data.drivers
        if fc.data_path != data_path
        and is_proscenio_driver_path(fc.data_path)
        and _driver_matches_source(fc.driver, source_armature, source_bone)
    ]
    for path in stale_paths:
        sprite.driver_remove(path)


def _driver_matches_source(
    driver: bpy.types.Driver,
    source_armature: bpy.types.Object,
    source_bone: str,
) -> bool:
    """True when ``driver`` reads from ``(source_armature, source_bone)``."""
    for var in driver.variables:
        for target in var.targets:
            if target.id is source_armature and target.bone_target == source_bone:
                return True
    return False


class PROSCENIO_OT_create_driver(bpy.types.Operator):
    """Drive a sprite's `proscenio.<prop>` from a chosen pose bone."""

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
        items=DRIVER_TARGET_PROPERTIES,
        default="region_x",
    )
    source_axis: EnumProperty(  # type: ignore[valid-type]
        name="Source",
        description="Pose bone transform channel feeding the driver",
        items=DRIVER_SOURCE_AXIS_ITEMS,
        default="ROT_Y",
    )
    expression: StringProperty(  # type: ignore[valid-type]
        name="Expression",
        description=(
            "Advanced driver expression. 'var' is the bone channel; edit in the "
            "Drivers Editor for scaling / offsets / branching."
        ),
        default="var",
    )
    advanced: BoolProperty(  # type: ignore[valid-type]
        name="Advanced expression",
        description="Use the raw expression instead of the two-range linear map",
        default=False,
    )
    in_min: FloatProperty(  # type: ignore[valid-type]
        name="Input min",
        description="Bone-channel value mapped to the output minimum",
        default=-1.5708,
    )
    in_max: FloatProperty(  # type: ignore[valid-type]
        name="Input max",
        description="Bone-channel value mapped to the output maximum",
        default=1.5708,
    )
    out_min: FloatProperty(  # type: ignore[valid-type]
        name="Output min",
        description="Target value at the input minimum",
        default=0.0,
    )
    out_max: FloatProperty(  # type: ignore[valid-type]
        name="Output max",
        description="Target value at the input maximum",
        default=1.0,
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
                self.advanced = bool(props.driver_advanced)
                self.in_min = float(props.driver_in_min)
                self.in_max = float(props.driver_in_max)
                self.out_min = float(props.driver_out_min)
                self.out_max = float(props.driver_out_max)
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

        # Drive the Custom Property (idprop) directly, not the PropertyGroup
        # proxy: the field's one storage home is the idprop the writer reads,
        # and Blender cannot keyframe / reliably drive a get/set proxy field.
        # ``driver_add`` resolves the path against an existing idprop, so seed
        # it from the proxy's current value (its default when unset) first.
        cp_key = f"proscenio_{self.target_property}"
        if cp_key not in sprite:
            sprite[cp_key] = getattr(props, self.target_property)
        data_path = driver_data_path(self.target_property)
        try:
            fcurve = _ensure_single_driver(sprite, data_path, armature, self.bone_name)
        except (TypeError, RuntimeError) as exc:
            report_error(self, f"could not add driver on {data_path}: {exc}")
            return {"CANCELLED"}

        if self.advanced:
            expression = self.expression or "var"
        else:
            expression = build_driver_expression(
                self.in_min, self.in_max, self.out_min, self.out_max
            )

        driver = fcurve.driver
        driver.type = "SCRIPTED"
        driver.expression = expression
        var = driver.variables[0] if driver.variables else driver.variables.new()
        var.name = _DRIVER_VAR_NAME
        var.type = "TRANSFORMS"
        target = var.targets[0]
        target.id = armature
        target.bone_target = self.bone_name
        target.transform_type = self.source_axis
        if self.source_axis.startswith("ROT_"):
            # WORLD_SPACE reads back the pose-mode rotation 1:1; LOCAL_SPACE
            # returns 0 when the bone's local axis coincides with it.
            target.transform_space = "WORLD_SPACE"
            # XYZ Euler keeps the variable in radians, not quaternion
            # components (sin(angle/2)) that confuse expressions.
            target.rotation_mode = "XYZ"
        else:
            # Translations: LOCAL_SPACE gives the pose offset from rest.
            # WORLD_SPACE would fold in the armature object's own transform
            # and break rigs repositioned at instance time.
            target.transform_space = "LOCAL_SPACE"

        # Mirror redo-panel overrides back to the PropertyGroup. The computed
        # expression is stored too, so the Advanced field shows the built map
        # as a starting point to hand-tweak.
        props.driver_target = self.target_property
        props.driver_source_axis = self.source_axis
        props.driver_expression = expression
        props.driver_advanced = self.advanced
        props.driver_in_min = self.in_min
        props.driver_in_max = self.in_max
        props.driver_out_min = self.out_min
        props.driver_out_max = self.out_max
        props.driver_source_armature = armature
        props.driver_source_bone = self.bone_name

        # The source bone is NOT auto-excluded from export here. A Drive-from-Bone
        # source can be a real deform bone (e.g. an eye sprite driven by the head
        # bone that also deforms the mesh); auto-excluding it would silently drop a
        # deform bone from the Godot skeleton. A non-deform helper is already
        # dropped by ``bone_is_exported`` (the use_deform gate), so the rigger
        # excludes a deform helper explicitly via the Skeleton list export toggle.

        report_info(
            self,
            f"driver on '{sprite.name}.{data_path}' "
            f"<- {armature.name}:{self.bone_name}.{self.source_axis}",
        )
        return {"FINISHED"}


class PROSCENIO_OT_remove_driver(bpy.types.Operator):
    """Remove one ``proscenio.*`` bone driver from the active sprite."""

    bl_idname = "proscenio.remove_driver"
    bl_label = "Proscenio: Remove Driver"
    bl_description = "Removes this bone driver from the active sprite's proscenio property"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    data_path: StringProperty(  # type: ignore[valid-type]
        name="Data path",
        description="The proscenio.<prop> data path whose driver is removed",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        sprite = context.active_object
        if sprite is None or sprite.type != "MESH":
            report_error(self, "select a sprite mesh as the active object")
            return {"CANCELLED"}
        if not self.data_path:
            report_warn(self, "no driver data path given")
            return {"CANCELLED"}
        if not is_proscenio_driver_path(self.data_path):
            # This operator manages only the Drive-from-Bone proscenio idprop
            # drivers; refuse any other path so a direct call cannot strip
            # unrelated drivers.
            report_warn(self, f"unsupported driver path '{self.data_path}'")
            return {"CANCELLED"}
        anim = sprite.animation_data
        if anim is None or anim.drivers.find(self.data_path) is None:
            report_warn(self, f"no driver on '{self.data_path}'")
            return {"CANCELLED"}
        sprite.driver_remove(self.data_path)
        report_info(self, f"removed driver on '{sprite.name}.{self.data_path}'")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_create_driver,
    PROSCENIO_OT_remove_driver,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
