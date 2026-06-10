"""Validation finding PropertyGroup.

A single entry in ``ProscenioSceneProps.validation_results``. Surfaced
in the Validation panel + the Diagnostics panel.
"""

from __future__ import annotations

from bpy.props import StringProperty
from bpy.types import PropertyGroup


class ProscenioValidationIssue(PropertyGroup):
    """A single validation finding stored on the scene for the panel to render.

    RNA-storage mirror of the bpy-free ``core.validation.Issue`` dataclass
    (same three fields). They stay separate classes because this one must
    subclass ``PropertyGroup`` for CollectionProperty storage while Issue
    stays bpy-free for the pure core + tests;
    ``operators.export_flow._populate_validation_results`` copies one into
    the other, so a new field has to land in all three.
    """

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
