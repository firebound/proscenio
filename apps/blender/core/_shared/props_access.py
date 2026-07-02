"""Typed accessors for Proscenio PropertyGroups.

Replaces the ~12 inline ``getattr(scene, "proscenio", None)`` /
``getattr(obj, "proscenio", None)`` repetitions across operators and
panels. Each call site previously re-implemented the None-guard plus
a comment explaining why; this helper keeps the guard in one place
and lets the call site read as a flat ``props = scene_props(context)``
followed by ``if props is None: return``.

Pure Python with bpy types only at the type-hint boundary, lazy via
``TYPE_CHECKING`` - the runtime path uses ``getattr`` and never
imports bpy. Tests can call into the helpers with
``SimpleNamespace(proscenio=...)`` shaped objects.

The return type ``object | None`` reflects that the PropertyGroup's
exact class depends on which Blender / addon build registered it;
callers read the typed fields they expect via subsequent ``getattr``
or by reaching for the helpers in ``core/pg_cp_fallback.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .report import ReportTarget, report_warn

if TYPE_CHECKING:
    import bpy


def object_is_visible(obj: bpy.types.Object | None) -> bool:
    """True when ``obj`` exists and is visible in the active view layer.

    A hidden object cannot become the active object, so an operator that runs
    ``bpy.ops.object.mode_set`` on it crashes with 'Context missing active
    object'. Mode-entering operators gate on this. Tolerant of objects / mocks
    without ``visible_get`` (treated as visible) and of a dead reference.
    """
    if obj is None:
        return False
    visible_get = getattr(obj, "visible_get", None)
    if not callable(visible_get):
        return True
    try:
        return bool(visible_get())
    except (RuntimeError, ReferenceError):
        return False


def require_object_visible(
    op: ReportTarget, obj: bpy.types.Object | None, *, action: str = "edit this object"
) -> bool:
    """Guard for operators that make ``obj`` active + enter a mode.

    Returns ``True`` when ``obj`` is usable; otherwise reports a controlled
    warning (telling the user to unhide it) and returns ``False`` - turning a
    hard ``mode_set`` crash on a hidden object into a graceful no-op.
    """
    if obj is None:
        report_warn(op, f"no object to {action}", always=True)
        return False
    if not object_is_visible(obj):
        try:
            name = getattr(obj, "name", "the object")
        except (RuntimeError, ReferenceError):
            # visible_get() can fail on a dead RNA object; reading name may too.
            name = "the object"
        report_warn(
            op,
            f"'{name}' is hidden - unhide it (Outliner eye / Alt+H) to {action}",
            always=True,
        )
        return False
    return True


def scene_props(context: bpy.types.Context) -> object | None:
    """Return ``context.scene.proscenio`` or ``None`` when not registered.

    The PropertyGroup is registered in ``properties/__init__.py`` via
    ``Scene.proscenio = PointerProperty(...)``. Until that registration
    completes (or in headless contexts where the addon was not loaded)
    the attribute is missing and the access raises ``AttributeError``.
    """
    scene = getattr(context, "scene", None)
    if scene is None:
        return None
    return getattr(scene, "proscenio", None)


def object_props(obj: bpy.types.Object | None) -> object | None:
    """Return ``obj.proscenio`` or ``None`` when not registered.

    ``obj`` is allowed to be ``None`` so callers can chain through
    ``object_props(context.active_object)`` without an explicit guard.
    """
    if obj is None:
        return None
    return getattr(obj, "proscenio", None)


def element_type_of(obj: bpy.types.Object | None) -> str:
    """Return ``obj``'s proscenio ``element_type`` ('mesh' or 'sprite').

    Defaults to ``"mesh"`` when the object, the PropertyGroup, or the field is
    absent (the schema default). Live-bpy PG read shared by the Mesh Generation
    gate and the automesh operators so they refuse to mesh a sprite element
    consistently; the headless validator reads the type via
    ``validation.read_element_type`` (PG + Custom Property fallback) instead.
    """
    props = object_props(obj)
    return str(getattr(props, "element_type", "mesh")) if props is not None else "mesh"


def scene_skinning(context: bpy.types.Context) -> object | None:
    """Return ``context.scene.proscenio.skinning`` or None when unavailable.

    Routes through :func:`scene_props` so the ``context.scene`` / ``proscenio``
    None-guards live in one place; callers read the typed skinning fields they
    expect via subsequent ``getattr``.
    """
    props = scene_props(context)
    return getattr(props, "skinning", None) if props is not None else None


def resolve_pixels_per_unit(context: bpy.types.Context) -> float:
    """Scene pixels-per-unit, defaulting to 100.0 when unset or unregistered.

    Routes through :func:`scene_props` so the ``context.scene`` /
    ``proscenio`` None-guards live in one place. The ``or 100.0`` also
    maps a stored 0 to the default (a zero scale is never valid).
    """
    props = scene_props(context)
    if props is None:
        return 100.0
    return float(getattr(props, "pixels_per_unit", 0.0)) or 100.0
