"""Operator report helpers with shared ``Proscenio:`` prefix (SPEC 009 wave 9.1).

Every operator in the addon reports user-facing messages through
``self.report({"INFO"|"WARNING"|"ERROR"}, "Proscenio: ...")``. The
``Proscenio:`` prefix was duplicated across 39 call sites; small
report helpers centralise it and let call sites focus on the actual
message.

Pure Python -- ``op.report`` is the only interaction and it's typed
loosely so tests can pass a ``SimpleNamespace`` with a ``report``
attribute.
"""

from __future__ import annotations

from typing import Any

_PREFIX = "Proscenio: "


def report_info(op: Any, msg: str) -> None:
    """Emit an INFO report with the ``Proscenio:`` prefix."""
    op.report({"INFO"}, _PREFIX + msg)


def report_warn(op: Any, msg: str) -> None:
    """Emit a WARNING report with the ``Proscenio:`` prefix."""
    op.report({"WARNING"}, _PREFIX + msg)


def report_error(op: Any, msg: str) -> None:
    """Emit an ERROR report with the ``Proscenio:`` prefix."""
    op.report({"ERROR"}, _PREFIX + msg)
