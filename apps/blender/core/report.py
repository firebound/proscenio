"""Operator report helpers with shared ``Proscenio:`` prefix (the code-modularity work).

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


@runtime_checkable
class ReportTarget(Protocol):
    """Minimal surface of ``bpy.types.Operator`` the report helpers touch."""

    def report(self, level: set[str], message: str) -> None: ...


def report_info(op: ReportTarget, msg: str) -> None:
    """Emit an INFO report with the ``Proscenio:`` prefix."""
    op.report({"INFO"}, _PREFIX + msg)


def report_warn(op: ReportTarget, msg: str) -> None:
    """Emit a WARNING report with the ``Proscenio:`` prefix."""
    op.report({"WARNING"}, _PREFIX + msg)


def report_error(op: ReportTarget, msg: str) -> None:
    """Emit an ERROR report with the ``Proscenio:`` prefix."""
    op.report({"ERROR"}, _PREFIX + msg)
