"""Pure tests for the shared report-verbosity gate (log levels).

``core/_shared/report`` is bpy-free; the report helpers take any object with
a ``report(level, msg)`` method, so a ``SimpleNamespace`` recorder drives the
gate. Each level (errors / info / debug) admits a different slice of the four
helpers; ``report_debug`` is the debug tier and stays silent until the level
is raised to ``debug``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared import report  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_gate():
    """Keep the module-global gate from leaking across tests."""
    report.set_min_level("info")
    yield
    report.set_min_level("info")


def _recorder() -> tuple[SimpleNamespace, list[tuple[set[str], str]]]:
    calls: list[tuple[set[str], str]] = []
    target = SimpleNamespace(report=lambda level, msg: calls.append((level, msg)))
    return target, calls


def _emit_all(target: SimpleNamespace) -> None:
    report.report_error(target, "boom")
    report.report_warn(target, "careful")
    report.report_info(target, "fyi")
    report.report_debug(target, "trace")


def _levels(calls: list[tuple[set[str], str]]) -> list[str]:
    return [next(iter(level)) for level, _ in calls]


def test_errors_level_only_errors():
    report.set_min_level("errors")
    target, calls = _recorder()
    _emit_all(target)
    assert _levels(calls) == ["ERROR"]


def test_info_level_suppresses_debug():
    report.set_min_level("info")
    target, calls = _recorder()
    _emit_all(target)
    # error + warning + info surface; the debug trace is held back.
    assert _levels(calls) == ["ERROR", "WARNING", "INFO"]


def test_debug_level_surfaces_everything():
    report.set_min_level("debug")
    target, calls = _recorder()
    _emit_all(target)
    # the debug trace joins, emitted as an INFO report so Blender shows it.
    assert _levels(calls) == ["ERROR", "WARNING", "INFO", "INFO"]
    assert calls[-1][1] == "[Proscenio debug] trace"


def test_unknown_level_falls_back_to_info():
    report.set_min_level("bogus")
    target, calls = _recorder()
    _emit_all(target)
    assert _levels(calls) == ["ERROR", "WARNING", "INFO"]


def test_debug_prefix_applied():
    report.set_min_level("debug")
    target, calls = _recorder()
    report.report_debug(target, "hello")
    assert calls == [({"INFO"}, "[Proscenio debug] hello")]
