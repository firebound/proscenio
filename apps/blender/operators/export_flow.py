"""Export-flow operators: Validate, Export, Re-export."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import bpy
from bpy.props import FloatProperty, StringProperty
from bpy_extras.io_utils import ExportHelper

from ..core import validation  # type: ignore[import-not-found]
from ..core._shared.props_access import scene_props  # type: ignore[import-not-found]
from ..core._shared.report import (  # type: ignore[import-not-found]
    report_debug,
    report_error,
    report_info,
    report_warn,
)


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


def _report_issue_traces(operator: bpy.types.Operator, issues: list[validation.Issue]) -> None:
    """Debug-level per-issue trace; surfaces only at the debug log level.

    The Validation panel already lists every issue, but a console echo helps
    headless / CLI export runs where there is no panel to read.
    """
    for issue in issues:
        suffix = f" [{issue.obj_name}]" if issue.obj_name else ""
        report_debug(operator, f"{issue.severity}: {issue.message}{suffix}")


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
    _report_issue_traces(operator, issues)
    errors = [i for i in issues if i.severity == "error"]
    if errors:
        report_error(
            operator,
            f"export blocked by {len(errors)} validation error(s) - see Validation panel.",
        )
        return False
    return True


def _gate_and_write(
    operator: bpy.types.Operator,
    scene: bpy.types.Scene,
    filepath: str,
    pixels_per_unit: float,
    *,
    fail_verb: str,
) -> bool:
    """Shared export spine: gate on validation, then run the writer.

    Returns False (after reporting) when validation blocks or the writer
    fails, True on success. ``fail_verb`` tunes the error message
    ("export" / "re-export"); the caller owns the success report and any
    sticky-path bookkeeping, since those differ between the two operators.
    """
    if not _gate_on_validation(operator, scene):
        return False
    error = _run_writer(filepath, pixels_per_unit)
    if error is not None:
        report_error(operator, f"{fail_verb} failed: {error}")
        return False
    return True


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
        _report_issue_traces(self, issues)
        errors = sum(1 for i in issues if i.severity == "error")
        warnings = sum(1 for i in issues if i.severity == "warning")
        if errors:
            report_error(self, f"{errors} error(s), {warnings} warning(s)")
        elif warnings:
            report_warn(self, f"{warnings} warning(s)")
        else:
            report_info(self, "validation OK")
        return {"FINISHED"}


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
        if not _gate_and_write(
            self, context.scene, self.filepath, self.pixels_per_unit, fail_verb="export"
        ):
            return {"CANCELLED"}

        path = Path(self.filepath)
        report_info(self, f"wrote {path.name}")
        print(f"[Proscenio] exported -> {path}")
        props = scene_props(context)
        if props is not None:
            props.last_export_path = self.filepath
        return {"FINISHED"}


class PROSCENIO_OT_reexport_godot(bpy.types.Operator):
    """One-click re-export to the sticky path stored on the scene."""

    bl_idname = "proscenio.reexport_godot"
    bl_label = "Proscenio: Re-export"
    bl_description = "Re-run the writer using the last export path - no file dialog"
    bl_options: ClassVar[set[str]] = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        props = scene_props(context)
        return props is not None and bool(props.last_export_path)

    def execute(self, context: bpy.types.Context) -> set[str]:
        props = context.scene.proscenio
        filepath = bpy.path.abspath(props.last_export_path)

        if not _gate_and_write(
            self, context.scene, filepath, props.pixels_per_unit, fail_verb="re-export"
        ):
            return {"CANCELLED"}

        report_info(self, f"re-exported -> {Path(filepath).name}")
        print(f"[Proscenio] re-exported -> {filepath}")
        return {"FINISHED"}


_classes: tuple[type, ...] = (
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
