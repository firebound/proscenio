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
