"""Issue dataclass + Severity literal (the authoring panel)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Issue:
    """A single validation finding.

    ``obj_name`` is optional and lets a future "select offending object"
    UX click straight to the source.

    The RNA-storage mirror of this record is
    ``properties.validation_issue.ProscenioValidationIssue`` - a separate
    PropertyGroup because the scene CollectionProperty + UIList need a bpy
    type, while this dataclass stays bpy-free for the pure validation core
    and its tests. ``operators.export_flow._populate_validation_results``
    copies the fields across, so a new field lands in all three places.
    """

    severity: Severity
    message: str
    obj_name: str | None = None
