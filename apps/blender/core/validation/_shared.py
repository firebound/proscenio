"""Validation helpers shared between active_element, active_slot, export."""

from __future__ import annotations

import contextlib

from .._shared.pg_cp_fallback import read_field

# Distinct from any real PG / CP value, so read_int can tell "nothing found"
# apart from a legitimate 0 it must still coerce.
_MISSING: object = object()


def read_element_type(obj: object) -> str:
    """PG-first / CP fallback read of the element type. Default ``"mesh"``."""
    return str(read_field(obj, pg_field="element_type", cp_key="proscenio_type", default="mesh"))


def read_int(obj: object, prop_name: str, custom_key: str, default: int) -> int:
    """PG-first / CP fallback read of an integer field.

    Routes the PG-first / CP-fallback resolution through
    ``pg_cp_fallback.read_field`` and adds only the integer coercion: the
    Custom Property fallback tolerates float-form strings (``"3.0"``) and
    falls back to ``default`` for non-numeric values instead of
    propagating a ``ValueError`` - a CP can hold arbitrary user data.
    """
    raw = read_field(obj, pg_field=prop_name, cp_key=custom_key, default=_MISSING)
    if isinstance(raw, int | float) and not isinstance(raw, bool):
        return int(raw)
    if isinstance(raw, str):
        with contextlib.suppress(TypeError, ValueError):
            return int(float(raw))
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
