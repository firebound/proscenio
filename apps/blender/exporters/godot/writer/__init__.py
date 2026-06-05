"""Proscenio ``.proscenio`` writer.

Walks the active Blender scene and emits a JSON document conforming to
``packages/models/schemas/proscenio.schema.json``.

Coordinate conventions
----------------------
Blender 2D rigs are typically laid out in the XZ world plane (Z up,
Y into the screen). Godot 2D is XY with Y down. The exporter maps:

    Godot.x = Blender.x * pixels_per_unit
    Godot.y = -Blender.z * pixels_per_unit

Rotations: the angle from the Godot +X axis to the bone direction is
computed in Godot space directly (CW positive when Y is down). Bone
local rotation is the world angle minus the parent's world angle.

UVs are written normalized [0, 1] of the atlas image - engine-agnostic.
The Godot importer multiplies by atlas size at attach time.

Vertex Y in mesh local space is dropped: sprite planes are assumed to
be authored as flat quads in Blender XY local then rotated 90 deg on X
by the user so they live in the XZ world plane.

Module organization:

- ``scene_discovery.py`` find armature, sprite meshes, atlas image
- ``skeleton.py``        coord conversion + bone world transforms + rest-local dataclass
- ``sprites.py``         polygon body + sprite_frame metadata + weights
- ``slots.py``           the slot system slot Empty walker
- ``slot_animations.py`` the slot system slot_attachment track emission
- ``animations.py``      bone_transform track emission

Public API: ``export(filepath, *, pixels_per_unit)`` - the only
function consumers should call.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, NotRequired, TypedDict

import bpy
from proscenio_models import (
    Animation,
    ProscenioDocument,
    Skeleton,
    Slot,
)
from proscenio_models import (
    Sprite as SpriteModel,
)

from .animations import build_animations
from .scene_discovery import doc_name, find_armature, find_atlas_image, find_sprite_meshes
from .skeleton import build_skeleton, compute_bone_world_godot
from .slot_animations import build_slot_animations, merge_slot_animations_into
from .slots import build_slots_for_scene
from .sprites import build_sprite


class _DocumentKwargs(TypedDict):
    """Constructor kwargs for ``ProscenioDocument``.

    The optional fields (``slots`` / ``atlas`` / ``animations``) are
    ``NotRequired`` so the writer can omit them entirely when empty.
    Passing them explicitly as ``None`` would mark them "set" and make
    ``model_dump_json(exclude_unset=True)`` emit ``"field": null`` -
    drifting the wire shape away from the goldens, which omit the key.
    """

    format_version: Literal[1]
    name: str
    pixels_per_unit: float
    skeleton: Skeleton
    sprites: list[SpriteModel]
    slots: NotRequired[list[Slot]]
    atlas: NotRequired[str]
    animations: NotRequired[list[Animation]]


SCHEMA_VERSION: Literal[1] = 1
DEFAULT_PIXELS_PER_UNIT = 100.0

__all__ = ["DEFAULT_PIXELS_PER_UNIT", "SCHEMA_VERSION", "export"]


def export(filepath: str | Path, *, pixels_per_unit: float = DEFAULT_PIXELS_PER_UNIT) -> None:
    """Write the active scene to a ``.proscenio`` file."""
    path_str = str(filepath)
    path = Path(bpy.path.abspath(path_str)) if path_str.startswith("//") else Path(path_str)
    scene = bpy.context.scene
    if scene is None:
        raise RuntimeError("Proscenio export needs an active scene")

    armature_obj = find_armature(scene)
    if armature_obj is None:
        raise RuntimeError("Proscenio export needs an Armature in the scene")

    bone_world_godot = compute_bone_world_godot(armature_obj, pixels_per_unit)
    skeleton, bone_rest_local = build_skeleton(armature_obj, bone_world_godot)

    sprite_objs = find_sprite_meshes(scene)

    # Blender skips depsgraph evaluation for hide_viewport=True objects, so
    # `obj.matrix_world` returns an identity / stale value for hidden slot
    # attachments. Un-hide every sprite, force a depsgraph update so each
    # `matrix_world` reflects the parent chain, build the entries, then
    # restore the original hide state. See tests/BUGS_FOUND.md.
    hidden_state: dict[bpy.types.Object, bool] = {}
    for obj in sprite_objs:
        if obj.hide_viewport:
            hidden_state[obj] = True
            obj.hide_viewport = False

    try:
        if hidden_state:
            view_layer = bpy.context.view_layer
            if view_layer is not None:
                view_layer.update()
        sprites_out = [build_sprite(obj, bone_world_godot, pixels_per_unit) for obj in sprite_objs]
    finally:
        for obj in hidden_state:
            obj.hide_viewport = True

    slots = build_slots_for_scene(scene)
    atlas = find_atlas_image(path)

    animations = build_animations(scene.render.fps, pixels_per_unit, bone_rest_local)
    slot_anims = build_slot_animations(scene)
    if slot_anims:
        animations = merge_slot_animations_into(animations, slot_anims)

    # Assemble kwargs so empty optionals are omitted entirely (not passed
    # as None). With exclude_unset=True, an explicit None still serialises
    # as `"field": null`; omitting the key leaves the field unset so the
    # dump drops it - matching the goldens.
    kwargs: _DocumentKwargs = {
        "format_version": SCHEMA_VERSION,
        "name": doc_name(),
        "pixels_per_unit": pixels_per_unit,
        "skeleton": skeleton,
        "sprites": sprites_out,
    }
    if slots:
        kwargs["slots"] = slots
    if atlas is not None:
        kwargs["atlas"] = atlas
    if animations:
        kwargs["animations"] = animations

    document = ProscenioDocument(**kwargs)
    payload = document.model_dump_json(indent=2, exclude_unset=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
