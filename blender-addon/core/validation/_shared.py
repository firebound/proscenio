"""Validation helpers shared between active_sprite, active_slot, export."""

from __future__ import annotations

from typing import Any


def read_sprite_type(obj: Any) -> str:
    """PG-first / CP fallback read of the sprite type. Default ``"polygon"``."""
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, "sprite_type"):
        return str(props.sprite_type)
    return str(obj.get("proscenio_type", "polygon")) if hasattr(obj, "get") else "polygon"


def read_int(obj: Any, prop_name: str, custom_key: str, default: int) -> int:
    """PG-first / CP fallback read of an integer field."""
    props = getattr(obj, "proscenio", None)
    if props is not None and hasattr(props, prop_name):
        return int(getattr(props, prop_name))
    if hasattr(obj, "get") and custom_key in obj:
        return int(obj[custom_key])
    return default


def armature_bone_names(armature_obj: Any) -> set[str]:
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
