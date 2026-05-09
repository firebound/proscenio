"""Issue dataclass + Severity literal (SPEC 005)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Issue:
    """A single validation finding.

    ``obj_name`` is optional and lets a future "select offending object"
    UX click straight to the source.
    """

    severity: Severity
    message: str
    obj_name: str | None = None
