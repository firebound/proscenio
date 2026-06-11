"""Per-bone SOFT/HARD mode override.

Stored on the mesh object as a JSON dict Custom Property:
    obj['proscenio_bone_modes'] = '{"bone_a": "SOFT", "bone_b": "HARD"}'

Missing entry means the bone uses the operator-level default mode
(per-mesh bind_init_mode). Used by bind_apply at weight-write time
to dispatch SOFT (proximity falloff) vs HARD (single-nearest) per bone.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Literal, cast

from .._shared.cp_keys import PROSCENIO_BONE_MODES as _KEY
from .._shared.json_cp import read_json_dict_cp

if TYPE_CHECKING:
    import bpy

BoneMode = Literal["SOFT", "HARD"]


def read_bone_modes(obj: bpy.types.Object) -> dict[str, BoneMode]:
    """Return the stored per-bone mode dict, filtering invalid values.

    Returns an empty dict when the property is absent or unparseable.
    """
    data = read_json_dict_cp(obj, _KEY)
    return cast(
        "dict[str, BoneMode]",
        {k: v for k, v in data.items() if v in ("SOFT", "HARD")},
    )


def write_bone_modes(obj: bpy.types.Object, modes: dict[str, BoneMode]) -> None:
    """Persist ``modes`` onto ``obj`` as a JSON Custom Property."""
    obj[_KEY] = json.dumps(modes)


def clear_bone_mode(obj: bpy.types.Object, bone_name: str) -> None:
    """Drop ``bone_name``'s override so it falls back to the bind default.

    A no-op when no override is set. Lets the panel offer a per-row clear
    without a separate operator path - the previous enum only set SOFT / HARD,
    leaving an override impossible to undo from the UI.
    """
    modes = dict(read_bone_modes(obj))
    modes.pop(bone_name, None)
    write_bone_modes(obj, modes)


def bone_mode_for(obj: bpy.types.Object, bone_name: str, default: BoneMode) -> BoneMode:
    """Return the per-bone mode for ``bone_name``, or ``default`` if not set."""
    return read_bone_modes(obj).get(bone_name, default)


def overrides_apply_under_bind_mode(bind_mode: str) -> bool:
    """True when per-bone SOFT/HARD overrides reach the weight write.

    Mirrors ``apply_bind``'s BONE_HEAT early-return (it returns before the
    override pass), so per-bone overrides only take effect under the planar
    modes. The Bind panel gates the override box on this so the controls are
    not drawn inert under the default Bone Heat.
    """
    return bind_mode != "BONE_HEAT"
