"""PropertyGroup → Custom Property mirror logic (post-005.1.c.1 fix).

Lives outside ``properties/__init__.py`` so the unit tests can exercise
the mirror without dragging in ``bpy``. Pure Python — only requires
``obj`` to support ``__setitem__`` (Blender Object does, ``SimpleNamespace``
mocks in tests do too).

Why this exists: Blender PropertyGroup update callbacks only fire on
explicit user edits. Defaults never trigger. So a per-field mirror
left the Custom Property snapshot incomplete. Reload Scripts then
rehydrated PropertyGroup from a partial CP set, losing untouched
fields. The fix is to mirror **every** field on **any** update.

Map covers the full Object-side schema:

- sprite_type, hframes, vframes, frame, centered (SPEC 005)
- region_mode, region_x/y/w/h (SPEC 005.1.c.1)
"""

from __future__ import annotations

from typing import Any

OBJECT_MIRROR_MAP: tuple[tuple[str, str, type], ...] = (
    ("proscenio_type", "sprite_type", str),
    ("proscenio_hframes", "hframes", int),
    ("proscenio_vframes", "vframes", int),
    ("proscenio_frame", "frame", int),
    ("proscenio_centered", "centered", bool),
    ("proscenio_region_mode", "region_mode", str),
    ("proscenio_region_x", "region_x", float),
    ("proscenio_region_y", "region_y", float),
    ("proscenio_region_w", "region_w", float),
    ("proscenio_region_h", "region_h", float),
    ("proscenio_material_isolated", "material_isolated", bool),
)


def mirror_all_fields(props: Any, obj: Any) -> None:
    """Write every Proscenio PropertyGroup field to its Custom Property mirror.

    Type-cast through ``caster`` to coerce Blender's typed property values
    into plain Python primitives the Custom Property dict accepts. Caster
    failures are skipped silently — a malformed value should never break
    the mirror flush for the rest of the fields.
    """
    for cp_key, attr, caster in OBJECT_MIRROR_MAP:
        if not hasattr(props, attr):
            continue
        try:
            obj[cp_key] = caster(getattr(props, attr))
        except (TypeError, ValueError):
            continue
