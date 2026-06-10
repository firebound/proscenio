"""Authoring modal session state.

Captures viewport state at invoke so _finish can restore it via
try/finally even on exception. Object lookups by name so undo-driven
object recreation does not stale the restore path.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

import bpy

from .._shared.select import restore_selection


@dataclass(frozen=True)
class AuthoringSession:
    """Container for prior state captured at modal invoke."""

    prior_active: bpy.types.Object | None
    prior_selected_names: list[str] = field(default_factory=list)
    prior_mode: str = "OBJECT"
    obj_name: str | None = None


def capture(context: bpy.types.Context, obj: bpy.types.Object) -> AuthoringSession:
    """Snapshot everything needed to restore on exit."""
    return AuthoringSession(
        prior_active=context.view_layer.objects.active,
        prior_selected_names=[o.name for o in context.selected_objects],
        prior_mode=obj.mode,
        obj_name=obj.name,
    )


def restore(context: bpy.types.Context, session: AuthoringSession) -> None:
    """Reapply prior state in safe order. Errors logged, never raised."""
    obj = bpy.data.objects.get(session.obj_name) if session.obj_name else None
    if obj is not None and obj.mode != session.prior_mode:
        with contextlib.suppress(RuntimeError):
            context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode=session.prior_mode)
    restore_selection(context, session.prior_selected_names, session.prior_active)
