"""Pure helper used by ``properties.__init__`` to copy legacy Custom
Properties into the new PropertyGroup.

Lives in its own module so the unit tests can import the function
without dragging in ``bpy``. The Blender side calls into this from
``properties/__init__.py`` (which does import ``bpy`` for
PropertyGroup registration).
"""

from __future__ import annotations

import contextlib
from typing import Any

OBJECT_PROPS: tuple[tuple[str, str], ...] = (
    ("proscenio_type", "sprite_type"),
    ("proscenio_hframes", "hframes"),
    ("proscenio_vframes", "vframes"),
    ("proscenio_frame", "frame"),
    ("proscenio_centered", "centered"),
    ("proscenio_region_mode", "region_mode"),
    ("proscenio_region_x", "region_x"),
    ("proscenio_region_y", "region_y"),
    ("proscenio_region_w", "region_w"),
    ("proscenio_region_h", "region_h"),
)


def hydrate_object(
    obj: Any,
    mapping: tuple[tuple[str, str], ...] = OBJECT_PROPS,
) -> None:
    """Copy legacy Custom Properties on ``obj`` into ``obj.proscenio``.

    Type-mismatched values (e.g. a string in an int slot) are skipped
    silently — the writer's RuntimeError catches genuine invalid data
    at export time.
    """
    props = getattr(obj, "proscenio", None)
    if props is None:
        return
    for custom_key, prop_name in mapping:
        if custom_key in obj:
            with contextlib.suppress(TypeError, ValueError):
                setattr(props, prop_name, obj[custom_key])
