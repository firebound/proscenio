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

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import bpy


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


def scene_skinning(context: bpy.types.Context) -> object | None:
    """Return ``context.scene.proscenio.skinning`` or None when unavailable.

    Routes through :func:`scene_props` so the ``context.scene`` / ``proscenio``
    None-guards live in one place; callers read the typed skinning fields they
    expect via subsequent ``getattr``.
    """
    props = scene_props(context)
    return getattr(props, "skinning", None) if props is not None else None


def active_armature(context: bpy.types.Context) -> bpy.types.Object | None:
    """Return the Skeleton-panel picker armature, or None.

    Reads ``scene.proscenio.active_armature`` and returns it only when it is an
    ``ARMATURE`` object: an unset picker, an unregistered PropertyGroup, or a
    non-armature pointer all yield None. The single source of truth for "which
    armature do skeleton / skinning operations target".
    """
    props = scene_props(context)
    picker = getattr(props, "active_armature", None) if props is not None else None
    if picker is None or getattr(picker, "type", None) != "ARMATURE":
        return None
    return cast("bpy.types.Object", picker)


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
