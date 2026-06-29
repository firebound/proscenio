"""Pure tests for the hidden-object guard (props_access).

A hidden object cannot become the active object, so an operator that runs
``bpy.ops.object.mode_set`` on it crashes with 'Context missing active object'.
``object_is_visible`` / ``require_object_visible`` turn that into a controlled
warning. No Blender - the helpers are pure and duck-typed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.props_access import (  # noqa: E402
    object_is_visible,
    require_object_visible,
)


class _Recorder:
    """Minimal ReportTarget double capturing (level, message) reports."""

    def __init__(self) -> None:
        self.reports: list[tuple[set[str], str]] = []

    def report(self, level: set[str], message: str) -> None:
        self.reports.append((level, message))


def test_object_is_visible_none_is_false():
    assert object_is_visible(None) is False


def test_object_is_visible_reads_visible_get():
    assert object_is_visible(SimpleNamespace(visible_get=lambda: True)) is True
    assert object_is_visible(SimpleNamespace(visible_get=lambda: False)) is False


def test_object_is_visible_without_method_treated_visible():
    # A mock / object lacking visible_get is treated visible (no false block).
    assert object_is_visible(SimpleNamespace()) is True


def test_object_is_visible_tolerates_dead_reference():
    def _boom() -> bool:
        raise ReferenceError("StructRNA removed")

    assert object_is_visible(SimpleNamespace(visible_get=_boom)) is False


def test_require_visible_passes_silently_when_visible():
    op = _Recorder()
    obj = SimpleNamespace(visible_get=lambda: True, name="Rig")
    assert require_object_visible(op, obj) is True
    assert op.reports == []


def test_require_visible_warns_on_hidden():
    op = _Recorder()
    obj = SimpleNamespace(visible_get=lambda: False, name="Rig")
    assert require_object_visible(op, obj, action="enter Edit Mode") is False
    assert op.reports, "a hidden object must report a warning, not pass"
    level, message = op.reports[0]
    assert "WARNING" in level
    assert "hidden" in message
    assert "Rig" in message
    assert "enter Edit Mode" in message


def test_require_visible_warns_on_none():
    op = _Recorder()
    assert require_object_visible(op, None) is False
    assert op.reports and "WARNING" in op.reports[0][0]
