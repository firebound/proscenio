"""Authoring modal session state (the interactive-modal work, T16).

Captures viewport state at invoke so _finish can restore it via
try/finally even on exception. Object lookups by name so undo-driven
object recreation does not stale the restore path.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

import bpy


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
    _restore_selection(context, session)


def _restore_selection(context: bpy.types.Context, session: AuthoringSession) -> None:
    for obj in list(context.selected_objects):
        with contextlib.suppress(RuntimeError, ReferenceError):
            obj.select_set(False)
    for name in session.prior_selected_names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            with contextlib.suppress(RuntimeError):
                obj.select_set(True)
    if session.prior_active is not None:
        with contextlib.suppress(RuntimeError, ReferenceError):
            context.view_layer.objects.active = session.prior_active
