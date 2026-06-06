"""PropertyGroup -> Custom Property mirror logic.

Lives outside ``properties/__init__.py`` so the unit tests can exercise
the mirror without dragging in ``bpy``. Pure Python - only requires
``obj`` to support ``__setitem__`` (Blender Object does, ``SimpleNamespace``
mocks in tests do too).

Why this exists: Blender PropertyGroup update callbacks only fire on
explicit user edits. Defaults never trigger. So a per-field mirror
left the Custom Property snapshot incomplete. Reload Scripts then
rehydrated PropertyGroup from a partial CP set, losing untouched
fields. The fix is to mirror **every** field on **any** update.

Map covers the full Object-side schema:

- sprite_type, hframes, vframes, frame, centered (the authoring panel)
- region_mode, region_x/y/w/h (the authoring panel.1.c.1)
- is_slot, slot_default
- is_outliner_favorite (the outliner subpanel)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from ._shared import cp_keys


def _as_str(v: object) -> str:
    return str(v)


def _as_int(v: object) -> int:
    if isinstance(v, int | float | str) and not isinstance(v, bool):
        return int(v)
    if isinstance(v, bool):
        return int(v)
    raise TypeError(f"cannot coerce {type(v).__name__} to int")


def _as_float(v: object) -> float:
    if isinstance(v, int | float | str):
        return float(v)
    raise TypeError(f"cannot coerce {type(v).__name__} to float")


def _as_bool(v: object) -> bool:
    if isinstance(v, int | float | bool | str):
        return bool(v)
    raise TypeError(f"cannot coerce {type(v).__name__} to bool")


Caster = Callable[[object], object]

OBJECT_MIRROR_MAP: tuple[tuple[str, str, Caster], ...] = (
    (cp_keys.PROSCENIO_TYPE, "sprite_type", _as_str),
    (cp_keys.PROSCENIO_HFRAMES, "hframes", _as_int),
    (cp_keys.PROSCENIO_VFRAMES, "vframes", _as_int),
    (cp_keys.PROSCENIO_FRAME, "frame", _as_int),
    (cp_keys.PROSCENIO_CENTERED, "centered", _as_bool),
    (cp_keys.PROSCENIO_REGION_MODE, "region_mode", _as_str),
    (cp_keys.PROSCENIO_REGION_X, "region_x", _as_float),
    (cp_keys.PROSCENIO_REGION_Y, "region_y", _as_float),
    (cp_keys.PROSCENIO_REGION_W, "region_w", _as_float),
    (cp_keys.PROSCENIO_REGION_H, "region_h", _as_float),
    (cp_keys.PROSCENIO_MATERIAL_ISOLATED, "material_isolated", _as_bool),
    (cp_keys.PROSCENIO_IS_SLOT, "is_slot", _as_bool),
    (cp_keys.PROSCENIO_SLOT_DEFAULT, "slot_default", _as_str),
    (cp_keys.PROSCENIO_OUTLINER_FAVORITE, "is_outliner_favorite", _as_bool),
)


@runtime_checkable
class _CPWriter(Protocol):
    """Anything that exposes dict-style assignment ``obj[key] = value``.

    Both ``bpy.types.Object`` (Custom Property storage) and ``SimpleNamespace``
    mocks with a stubbed ``__setitem__`` satisfy this Protocol.
    """

    def __setitem__(self, key: str, value: object) -> None: ...


def mirror_all_fields(props: object, obj: _CPWriter) -> None:
    """Write every Proscenio PropertyGroup field to its Custom Property mirror.

    Type-cast through ``caster`` to coerce Blender's typed property values
    into plain Python primitives the Custom Property dict accepts. Caster
    failures are skipped silently - a malformed value should never break
    the mirror flush for the rest of the fields.
    """
    for cp_key, attr, caster in OBJECT_MIRROR_MAP:
        if not hasattr(props, attr):
            continue
        try:
            obj[cp_key] = caster(getattr(props, attr))
        except (TypeError, ValueError):
            continue
