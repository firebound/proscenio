"""Operator report helpers with shared ``Proscenio:`` prefix.

Every operator in the addon reports user-facing messages through
``self.report({"INFO"|"WARNING"|"ERROR"}, "Proscenio: ...")``. The
``Proscenio:`` prefix was duplicated across 39 call sites; small
report helpers centralise it and let call sites focus on the actual
message.

Pure Python - the helpers accept anything implementing the minimal
``ReportTarget`` Protocol (``op.report({...}, msg)``). Real
``bpy.types.Operator`` instances and the ``SimpleNamespace`` mocks
used by the pytest suite both satisfy it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

_PREFIX = "Proscenio: "
_DEBUG_PREFIX = "[Proscenio debug] "

# Report-verbosity gate. The addon preferences push the user's choice here
# via ``set_min_level``; pure-module callers + the pytest mocks keep the
# default (info). ``errors`` shows only error reports; ``info`` (default)
# adds info + warnings; ``debug`` adds the per-item pipeline traces
# (importer planes, automesh counters, validation issues) on top.
_LEVELS = {"errors": 0, "info": 1, "debug": 2}
_INFO_LEVEL = _LEVELS["info"]
_DEBUG_LEVEL = _LEVELS["debug"]
_min_level = _LEVELS["info"]


def set_min_level(name: str) -> None:
    """Set the report-verbosity gate from a preference enum value."""
    global _min_level
    _min_level = _LEVELS.get(name, _LEVELS["info"])


@runtime_checkable
class ReportTarget(Protocol):
    """Minimal surface of ``bpy.types.Operator`` the report helpers touch."""

    def report(self, level: set[str], message: str) -> None: ...


def report_info(op: ReportTarget, msg: str) -> None:
    """Emit an INFO report with the ``Proscenio:`` prefix (gated by log level)."""
    if _min_level >= _INFO_LEVEL:
        op.report({"INFO"}, _PREFIX + msg)


def report_warn(op: ReportTarget, msg: str) -> None:
    """Emit a WARNING report with the ``Proscenio:`` prefix (gated by log level)."""
    if _min_level >= _INFO_LEVEL:
        op.report({"WARNING"}, _PREFIX + msg)


def report_error(op: ReportTarget, msg: str) -> None:
    """Emit an ERROR report with the ``Proscenio:`` prefix."""
    op.report({"ERROR"}, _PREFIX + msg)


def report_debug(op: ReportTarget, msg: str) -> None:
    """Emit a dev debug trace tagged ``[Proscenio debug]``, only at the debug level.

    Debug traces are the per-item pipeline detail (importer planes, automesh
    counters, validation issues) that would drown the Info log; they surface
    only when the user raises the log level to ``debug``. Emitted as an INFO
    report because Blender filters its native DEBUG severity out of every
    visible channel; the distinct ``[Proscenio debug]`` tag (vs the plain
    ``Proscenio:`` prefix) keeps them readable apart in the Info editor.
    """
    if _min_level >= _DEBUG_LEVEL:
        op.report({"INFO"}, _DEBUG_PREFIX + msg)
