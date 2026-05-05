"""Blender operators."""

from pathlib import Path
from typing import ClassVar

import bpy
from bpy.props import FloatProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from ..core import validation  # type: ignore[import-not-found]


class PROSCENIO_OT_smoke_test(bpy.types.Operator):
    """Smoke test operator — confirms the addon registers and dispatches."""

    bl_idname = "proscenio.smoke_test"
    bl_label = "Hello Proscenio"
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
    bl_label = "Validate"
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
    bl_label = "Export Proscenio (.proscenio)"
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
    bl_label = "Re-export"
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


_classes: tuple[type, ...] = (
    PROSCENIO_OT_smoke_test,
    PROSCENIO_OT_validate_export,
    PROSCENIO_OT_export_godot,
    PROSCENIO_OT_reexport_godot,
)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
