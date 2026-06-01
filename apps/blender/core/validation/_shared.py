"""Validation helpers shared between active_sprite, active_slot, export."""

from __future__ import annotations

import contextlib
from typing import Protocol, runtime_checkable


@runtime_checkable
class _CPLookup(Protocol):
    """Anything that exposes dict-style ``__contains__`` + ``.get`` + ``__getitem__``.

    Both ``bpy.types.Object`` (Custom Property access) and the
    pytest ``SimpleNamespace`` mocks satisfy this Protocol.
    """

    def __contains__(self, key: object) -> bool: ...
    def __getitem__(self, key: str) -> object: ...
    def get(self, key: str, default: object | None = None) -> object: ...


def read_sprite_type(obj: object) -> str:
    """PG-first / CP fallback read of the sprite type. Default ``"polygon"``."""
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, "sprite_type"):
        return str(props.sprite_type)
    if isinstance(obj, _CPLookup):
        return str(obj.get("proscenio_type", "polygon"))
    return "polygon"


def read_int(obj: object, prop_name: str, custom_key: str, default: int) -> int:
    """PG-first / CP fallback read of an integer field.

    The Custom Property fallback tolerates float-form strings (``"3.0"``)
    and falls back to ``default`` for non-numeric values instead of
    propagating a ``ValueError`` - a CP can hold arbitrary user data.
    """
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, prop_name):
        return int(getattr(props, prop_name))
    if isinstance(obj, _CPLookup) and custom_key in obj:
        value = obj[custom_key]
        if isinstance(value, int | float) and not isinstance(value, bool):
            return int(value)
        if isinstance(value, str):
            with contextlib.suppress(TypeError, ValueError):
                return int(float(value))
    return default


def armature_bone_names(armature_obj: object) -> set[str]:
    """Return the set of bone names on the armature, or empty when malformed."""
    armature = getattr(armature_obj, "data", None)
    bones = getattr(armature, "bones", None) if armature is not None else None
    if bones is None:
        return set()
    return {str(b.name) for b in bones}


def abspath_or_none(filepath: str) -> str | None:
    """Resolve a Blender ``//`` path lazily; return the literal path otherwise."""
    try:
        import bpy
    except ImportError:
        return filepath if not filepath.startswith("//") else None
    return str(bpy.path.abspath(filepath))
