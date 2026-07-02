"""Sprite (Sprite2D) element emission: frame metadata, flips, pivot offset."""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

import bpy
from mathutils import Vector
from proscenio_models import SpriteElement

from .....core._shared import region as region_core
from .....core._shared.pg_cp_fallback import read_field
from ..skeleton import world_to_godot_xy
from ._common import _derive_modulate, _derive_z_index, resolve_sprite_bone


class _SpriteFrameKwargs(TypedDict):
    """Constructor kwargs for ``SpriteElement``; ``texture_region`` is omitted
    in auto mode and set only for manual regions."""

    type: Literal["sprite"]
    name: str
    bone: str
    hframes: int
    vframes: int
    frame: int
    centered: bool
    texture_region: NotRequired[list[float]]
    modulate: NotRequired[list[float]]
    z_index: NotRequired[int]
    flip_h: NotRequired[bool]
    flip_v: NotRequired[bool]
    offset: NotRequired[list[float]]


def _derive_flips(obj: bpy.types.Object) -> tuple[bool | None, bool | None]:
    """Flip flags from negative local scale signs (sprite only).

    A rigid sprite has no exported vertices to bake a mirror into, so the
    sign of the local scale becomes a Sprite2D flag. The quad is authored in
    local XY then stood up 90deg on X, so local X is horizontal and local Y
    vertical. A non-negative axis emits nothing.
    """
    flip_h = True if obj.scale.x < 0 else None
    flip_v = True if obj.scale.y < 0 else None
    return flip_h, flip_v


def _compute_sprite_offset(obj: bpy.types.Object, ppu: float) -> list[float] | None:
    """Sprite2D pixel offset from the object origin to its quad centre.

    A rigid sprite renders centred on its node origin (the bone attach
    point); when the authored pivot sits away from the quad centre the
    texture must shift by that gap or it lands in the wrong place. Projects
    the local mesh-bounds centre and the origin through the same Godot screen
    mapping the mesh path uses, then returns their difference. None when
    origin and centre coincide (no authored pivot) or the object carries no
    geometry. Reads ``mesh.vertices`` rather than ``bound_box`` so the bounds
    are current without a depsgraph refresh.
    """
    mesh = getattr(obj, "data", None)
    vertices = getattr(mesh, "vertices", None)
    if not vertices:
        return None
    xs = [v.co.x for v in vertices]
    ys = [v.co.y for v in vertices]
    zs = [v.co.z for v in vertices]
    # A flipped sprite (negative local scale) exports flip_h/flip_v flags that
    # already mirror the texture in Godot. If the pivot gap were measured through
    # the mirrored matrix it would be counted twice - once here, once by the flag
    # - so cancel the reflection first: multiply the local centre by the scale
    # sign, since ``|S| @ v == S @ (sign(S) .* v)``. A non-flipped sprite has all
    # signs +1, so the measured offset (and every golden) is unchanged.
    scale = obj.scale
    # Per-axis sign; a non-negative axis (including 0) maps to +1.
    sign_x, sign_y, sign_z = (1.0 if c >= 0 else -1.0 for c in (scale.x, scale.y, scale.z))
    local_center = Vector(
        (
            (min(xs) + max(xs)) / 2.0 * sign_x,
            (min(ys) + max(ys)) / 2.0 * sign_y,
            (min(zs) + max(zs)) / 2.0 * sign_z,
        )
    )
    matrix_world = obj.matrix_world
    center_godot = world_to_godot_xy(matrix_world @ local_center, ppu)
    origin_godot = world_to_godot_xy(matrix_world.translation, ppu)
    offset = [
        round(center_godot.x - origin_godot.x, 6),
        round(center_godot.y - origin_godot.y, 6),
    ]
    return None if offset == [0.0, 0.0] else offset


def build_sprite(obj: bpy.types.Object, ppu: float) -> SpriteElement:
    """Emit a ``sprite`` element entry (Sprite2D)."""
    hframes = int(read_field(obj, cp_key="proscenio_hframes", default=1))
    vframes = int(read_field(obj, cp_key="proscenio_vframes", default=1))
    if hframes < 1 or vframes < 1:
        raise RuntimeError(
            f"Proscenio: sprite object {obj.name!r} needs hframes >= 1 "
            f"and vframes >= 1 (got hframes={hframes}, vframes={vframes})."
        )

    sf_kwargs: _SpriteFrameKwargs = {
        "type": "sprite",
        "name": obj.name,
        "bone": resolve_sprite_bone(obj),
        "hframes": hframes,
        "vframes": vframes,
        "frame": int(read_field(obj, cp_key="proscenio_frame", default=0)),
        "centered": bool(read_field(obj, cp_key="proscenio_centered", default=True)),
    }
    manual_region = region_core.manual_region_or_none(obj)
    if manual_region is not None:
        sf_kwargs["texture_region"] = manual_region
    modulate = _derive_modulate(obj)
    if modulate is not None:
        sf_kwargs["modulate"] = modulate
    z_index = _derive_z_index(obj)
    if z_index is not None:
        sf_kwargs["z_index"] = z_index
    flip_h, flip_v = _derive_flips(obj)
    if flip_h is not None:
        sf_kwargs["flip_h"] = flip_h
    if flip_v is not None:
        sf_kwargs["flip_v"] = flip_v
    offset = _compute_sprite_offset(obj, ppu)
    if offset is not None:
        sf_kwargs["offset"] = offset
    return SpriteElement(**sf_kwargs)
