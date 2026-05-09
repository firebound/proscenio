"""Validation finding PropertyGroup (SPEC 009 wave 9.10).

A single entry in ``ProscenioSceneProps.validation_results``. Surfaced
in the Validation panel + the Diagnostics panel.
"""

from __future__ import annotations

from bpy.props import StringProperty
from bpy.types import PropertyGroup


class ProscenioValidationIssue(PropertyGroup):
    """A single validation finding stored on the scene for the panel to render."""

    severity: StringProperty(  # type: ignore[valid-type]
        name="Severity",
        default="warning",
        description="One of 'error' or 'warning'",
    )
    message: StringProperty(  # type: ignore[valid-type]
        name="Message",
        default="",
    )
    obj_name: StringProperty(  # type: ignore[valid-type]
        name="Object",
        default="",
        description="Name of the offending object (empty if scene-wide)",
    )
