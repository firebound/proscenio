"""Blender operators."""

import contextlib
from pathlib import Path
from typing import ClassVar

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from ..core import validation  # type: ignore[import-not-found]


class PROSCENIO_OT_smoke_test(bpy.types.Operator):
    """Smoke test operator — confirms the addon registers and dispatches."""

    bl_idname = "proscenio.smoke_test"
    bl_label = "Proscenio: Smoke Test"
    bl_description = "Print a sanity check to the system console"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        message = "Proscenio smoke test OK"
        self.report({"INFO"}, message)
        print(f"[Proscenio] {message}")
        return {"FINISHED"}


def _populate_validation_results(scene: bpy.types.Scene, issues: list[validation.Issue]) -> None:
    """Mirror an Issue list into the scene's CollectionProperty for the panel."""
    props = getattr(scene, "proscenio", None)
    if props is None:
        return
    props.validation_results.clear()
    for issue in issues:
        item = props.validation_results.add()
        item.severity = issue.severity
        item.message = issue.message
        item.obj_name = issue.obj_name or ""
    props.validation_ran = True


class PROSCENIO_OT_validate_export(bpy.types.Operator):
    """Run the full export-time validation pass and surface issues in the panel."""

    bl_idname = "proscenio.validate_export"
    bl_label = "Proscenio: Validate"
    bl_description = (
        "Walks the scene, checks every sprite against the armature, "
        "verifies atlas files. Errors block export."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        issues = validation.validate_export(context.scene)
        _populate_validation_results(context.scene, issues)
        errors = sum(1 for i in issues if i.severity == "error")
        warnings = sum(1 for i in issues if i.severity == "warning")
        if errors:
            self.report({"ERROR"}, f"Proscenio: {errors} error(s), {warnings} warning(s)")
        elif warnings:
            self.report({"WARNING"}, f"Proscenio: {warnings} warning(s)")
        else:
            self.report({"INFO"}, "Proscenio: validation OK")
        return {"FINISHED"}


def _run_writer(filepath: str, pixels_per_unit: float) -> str | None:
    """Invoke the writer; return an error message or ``None`` on success."""
    from ..exporters.godot import writer  # type: ignore[import-not-found]

    try:
        writer.export(filepath, pixels_per_unit=pixels_per_unit)
    except Exception as exc:
        return str(exc)
    return None


def _gate_on_validation(operator: bpy.types.Operator, scene: bpy.types.Scene) -> bool:
    """Return False (and report) when validation finds blocking errors."""
    issues = validation.validate_export(scene)
    _populate_validation_results(scene, issues)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        operator.report(
            {"ERROR"},
            f"Proscenio: export blocked by {len(errors)} validation error(s) "
            f"— see Validation panel.",
        )
        return False
    return True


class PROSCENIO_OT_export_godot(bpy.types.Operator, ExportHelper):
    """Export the active scene as a `.proscenio` JSON document."""

    bl_idname = "proscenio.export_godot"
    bl_label = "Proscenio: Export (.proscenio)"
    bl_description = "Write the active scene to a Proscenio JSON file"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    filename_ext = ".proscenio"
    filter_glob: StringProperty(default="*.proscenio", options={"HIDDEN"})  # type: ignore[valid-type]

    pixels_per_unit: FloatProperty(  # type: ignore[valid-type]
        name="Pixels per unit",
        description="Conversion ratio between Blender units and Godot pixels",
        default=100.0,
        min=0.0001,
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not _gate_on_validation(self, context.scene):
            return {"CANCELLED"}

        error = _run_writer(self.filepath, self.pixels_per_unit)
        if error is not None:
            self.report({"ERROR"}, f"Proscenio export failed: {error}")
            return {"CANCELLED"}

        path = Path(self.filepath)
        self.report({"INFO"}, f"Proscenio: wrote {path.name}")
        print(f"[Proscenio] exported → {path}")
        scene_props = getattr(context.scene, "proscenio", None)
        if scene_props is not None:
            scene_props.last_export_path = self.filepath
        return {"FINISHED"}


class PROSCENIO_OT_reexport_godot(bpy.types.Operator):
    """One-click re-export to the sticky path stored on the scene."""

    bl_idname = "proscenio.reexport_godot"
    bl_label = "Proscenio: Re-export"
    bl_description = "Re-run the writer using the last export path — no file dialog"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        scene_props = getattr(context.scene, "proscenio", None)
        return scene_props is not None and bool(scene_props.last_export_path)

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene_props = context.scene.proscenio
        filepath = bpy.path.abspath(scene_props.last_export_path)

        if not _gate_on_validation(self, context.scene):
            return {"CANCELLED"}

        error = _run_writer(filepath, scene_props.pixels_per_unit)
        if error is not None:
            self.report({"ERROR"}, f"Proscenio re-export failed: {error}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Proscenio: re-exported → {Path(filepath).name}")
        print(f"[Proscenio] re-exported → {filepath}")
        return {"FINISHED"}


class PROSCENIO_OT_select_issue_object(bpy.types.Operator):
    """Select the object referenced by a validation issue and make it active."""

    bl_idname = "proscenio.select_issue_object"
    bl_label = "Proscenio: Select Issue Object"
    bl_description = "Selects and activates the object that the issue refers to"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object name",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.obj_name:
            self.report({"WARNING"}, "Proscenio: issue has no object name")
            return {"CANCELLED"}
        obj = bpy.data.objects.get(self.obj_name)
        if obj is None:
            self.report({"WARNING"}, f"Proscenio: object '{self.obj_name}' not found")
            return {"CANCELLED"}
        for other in context.scene.objects:
            other.select_set(False)
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


_PREVIEW_CAM_NAME = "Proscenio.PreviewCam"
_IK_CONSTRAINT_NAME = "Proscenio IK"


class PROSCENIO_OT_create_ortho_camera(bpy.types.Operator):
    """Create or focus an orthographic preview camera matching pixels_per_unit."""

    bl_idname = "proscenio.create_ortho_camera"
    bl_label = "Proscenio: Preview Camera"
    bl_description = (
        "Adds (or focuses) an orthographic camera sized to the scene's "
        "pixels_per_unit and render resolution. Use Numpad 0 to enter the view."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        scene_props = getattr(scene, "proscenio", None)
        ppu = float(scene_props.pixels_per_unit) if scene_props is not None else 100.0
        ortho_scale = max(scene.render.resolution_x, scene.render.resolution_y) / ppu

        cam_obj = bpy.data.objects.get(_PREVIEW_CAM_NAME)
        if cam_obj is None:
            cam_data = bpy.data.cameras.new(name=_PREVIEW_CAM_NAME)
            cam_obj = bpy.data.objects.new(name=_PREVIEW_CAM_NAME, object_data=cam_data)
            scene.collection.objects.link(cam_obj)
            cam_obj.location = (0.0, -10.0, 0.0)
            cam_obj.rotation_euler = (1.5707963, 0.0, 0.0)
            created = True
        else:
            created = False

        cam = cam_obj.data
        cam.type = "ORTHO"
        cam.ortho_scale = ortho_scale

        scene.camera = cam_obj
        for other in context.scene.objects:
            other.select_set(False)
        cam_obj.select_set(True)
        context.view_layer.objects.active = cam_obj

        verb = "created" if created else "updated"
        self.report(
            {"INFO"},
            f"Proscenio: {verb} '{_PREVIEW_CAM_NAME}' (ortho_scale={ortho_scale:.4f})",
        )
        return {"FINISHED"}


class PROSCENIO_OT_toggle_ik_chain(bpy.types.Operator):
    """Toggle a Proscenio-owned IK constraint on the active pose bone."""

    bl_idname = "proscenio.toggle_ik_chain"
    bl_label = "Proscenio: Toggle IK"
    bl_description = (
        "Adds an IK constraint named 'Proscenio IK' to the active pose bone "
        "(chain length 2). Click again to remove it. Hand-added constraints "
        "are left untouched."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    chain_length: IntProperty(  # type: ignore[valid-type]
        name="Chain length",
        default=2,
        min=0,
        soft_max=8,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        if context.mode != "POSE":
            return False
        bone = getattr(context, "active_pose_bone", None)
        return bone is not None

    def execute(self, context: bpy.types.Context) -> set[str]:
        bone = context.active_pose_bone
        existing = bone.constraints.get(_IK_CONSTRAINT_NAME)
        if existing is not None:
            bone.constraints.remove(existing)
            self.report({"INFO"}, f"Proscenio: removed IK from '{bone.name}'")
            return {"FINISHED"}

        ik = bone.constraints.new(type="IK")
        ik.name = _IK_CONSTRAINT_NAME
        ik.chain_count = self.chain_length
        self.report(
            {"INFO"},
            f"Proscenio: added IK to '{bone.name}' (chain={self.chain_length}); "
            f"set the target manually.",
        )
        return {"FINISHED"}


class PROSCENIO_OT_reproject_sprite_uv(bpy.types.Operator):
    """Re-unwrap the active mesh's UVs against its first image-textured material."""

    bl_idname = "proscenio.reproject_sprite_uv"
    bl_label = "Proscenio: Reproject UV"
    bl_description = (
        "Re-projects the active mesh's UVs (Smart UV Project) so the texture "
        "lines up after vertex edits. Active object only."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    angle_limit: FloatProperty(  # type: ignore[valid-type]
        name="Angle limit",
        description="Smart UV Project angle limit (radians)",
        default=1.15192,
        min=0.0,
        max=3.14159,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        prior_mode = context.mode
        prior_active = context.view_layer.objects.active
        prior_selection = [o for o in context.scene.objects if o.select_get()]

        try:
            for other in context.scene.objects:
                other.select_set(False)
            obj.select_set(True)
            context.view_layer.objects.active = obj
            if prior_mode != "EDIT_MESH":
                bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(angle_limit=self.angle_limit)
        finally:
            if prior_mode != "EDIT_MESH":
                with contextlib.suppress(RuntimeError):
                    bpy.ops.object.mode_set(mode="OBJECT")
            for other in context.scene.objects:
                other.select_set(False)
            for o in prior_selection:
                o.select_set(True)
            if prior_active is not None:
                context.view_layer.objects.active = prior_active

        self.report({"INFO"}, f"Proscenio: reprojected UVs on '{obj.name}'")
        return {"FINISHED"}


class PROSCENIO_OT_snap_region_to_uv(bpy.types.Operator):
    """Copy current UV bounds into the manual region_x/y/w/h fields."""

    bl_idname = "proscenio.snap_region_to_uv"
    bl_label = "Proscenio: Snap region to UV bounds"
    bl_description = (
        "Reads the active mesh's UV bounds and writes them into the manual "
        "region fields. Use this to seed manual mode with the current auto value."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        props = getattr(obj, "proscenio", None)
        if props is None:
            self.report({"WARNING"}, "Proscenio: PropertyGroup not registered on this object")
            return {"CANCELLED"}

        mesh = obj.data
        uv_layer = mesh.uv_layers.active
        if uv_layer is None or not mesh.polygons:
            self.report({"WARNING"}, f"Proscenio: '{obj.name}' has no UV layer or no polygons")
            return {"CANCELLED"}

        xs: list[float] = []
        ys: list[float] = []
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                u = uv_layer.data[li].uv
                xs.append(float(u.x))
                ys.append(1.0 - float(u.y))

        if not xs:
            self.report({"WARNING"}, f"Proscenio: '{obj.name}' has no UV data")
            return {"CANCELLED"}

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)
        props.region_x = x_min
        props.region_y = y_min
        props.region_w = x_max - x_min
        props.region_h = y_max - y_min
        self.report(
            {"INFO"},
            f"Proscenio: snapped region to UV bounds "
            f"({props.region_x:.4f}, {props.region_y:.4f}, "
            f"{props.region_w:.4f}, {props.region_h:.4f})",
        )
        return {"FINISHED"}


class PROSCENIO_OT_bake_current_pose(bpy.types.Operator):
    """Insert keyframes for every Bone2D's transform at the current frame."""

    bl_idname = "proscenio.bake_current_pose"
    bl_label = "Proscenio: Bake Current Pose"
    bl_description = (
        "Inserts a location/rotation/scale keyframe on every pose bone of the "
        "first armature in the scene at the playhead. Requires Pose Mode."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        active = context.active_object
        if active is None or active.type != "ARMATURE":
            return False
        return bool(context.mode == "POSE")

    def execute(self, context: bpy.types.Context) -> set[str]:
        armature = context.active_object
        frame = context.scene.frame_current
        bones = armature.pose.bones
        if not bones:
            self.report({"WARNING"}, "Proscenio: armature has no pose bones")
            return {"CANCELLED"}
        for bone in bones:
            for path in ("location", "rotation_quaternion", "rotation_euler", "scale"):
                if hasattr(bone, path):
                    bone.keyframe_insert(data_path=path, frame=frame)
        self.report({"INFO"}, f"Proscenio: baked pose at frame {frame} for {len(bones)} bone(s)")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
    PROSCENIO_OT_smoke_test,
    PROSCENIO_OT_validate_export,
    PROSCENIO_OT_export_godot,
    PROSCENIO_OT_reexport_godot,
    PROSCENIO_OT_select_issue_object,
    PROSCENIO_OT_create_ortho_camera,
    PROSCENIO_OT_toggle_ik_chain,
    PROSCENIO_OT_reproject_sprite_uv,
    PROSCENIO_OT_snap_region_to_uv,
    PROSCENIO_OT_bake_current_pose,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
