"""Per-bone SOFT/HARD mode override (the weight-paint productivity follow-up (per-bone mode toggle)/D16).

Stored on the mesh object as a JSON dict Custom Property:
    obj['proscenio_bone_modes'] = '{"bone_a": "SOFT", "bone_b": "HARD"}'

Missing entry means the bone uses the operator-level default mode
(per-mesh bind_init_mode). Used by bind_apply at weight-write time
to dispatch SOFT (proximity falloff) vs HARD (single-nearest) per bone.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import bpy

BoneMode = Literal["SOFT", "HARD"]
_KEY = "proscenio_bone_modes"


def read_bone_modes(obj: bpy.types.Object) -> dict[str, BoneMode]:
    """Return the stored per-bone mode dict, filtering invalid values.

    Returns an empty dict when the property is absent or unparseable.
    """
    raw = obj.get(_KEY)
    if raw is None:
        return {}
    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (ValueError, TypeError):
        return {}
    return {k: v for k, v in data.items() if v in ("SOFT", "HARD")}


def write_bone_modes(obj: bpy.types.Object, modes: dict[str, BoneMode]) -> None:
    """Persist ``modes`` onto ``obj`` as a JSON Custom Property."""
    obj[_KEY] = json.dumps(modes)


def bone_mode_for(obj: bpy.types.Object, bone_name: str, default: BoneMode) -> BoneMode:
    """Return the per-bone mode for ``bone_name``, or ``default`` if not set."""
    return read_bone_modes(obj).get(bone_name, default)
