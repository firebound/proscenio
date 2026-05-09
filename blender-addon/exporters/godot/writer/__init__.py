"""Proscenio ``.proscenio`` writer (SPEC 009 wave 9.4).

Walks the active Blender scene and emits a JSON document conforming to
``schemas/proscenio.schema.json``.

Coordinate conventions
----------------------
Blender 2D rigs are typically laid out in the XZ world plane (Z up,
Y into the screen). Godot 2D is XY with Y down. The exporter maps:

    Godot.x = Blender.x * pixels_per_unit
    Godot.y = -Blender.z * pixels_per_unit

Rotations: the angle from the Godot +X axis to the bone direction is
computed in Godot space directly (CW positive when Y is down). Bone
local rotation is the world angle minus the parent's world angle.

UVs are written normalized [0, 1] of the atlas image -- engine-agnostic.
The Godot importer multiplies by atlas size at attach time.

Vertex Y in mesh local space is dropped: sprite planes are assumed to
be authored as flat quads in Blender XY local then rotated 90 deg on X
by the user so they live in the XZ world plane.

Module organization (SPEC 009 wave 9.4):

- ``_schema.py``         TypedDicts mirroring the JSON shapes
- ``scene_discovery.py`` find armature, sprite meshes, atlas image
- ``skeleton.py``        coord conversion + bone world transforms
- ``sprites.py``         polygon body + sprite_frame metadata + weights
- ``slots.py``           SPEC 004 D8 slot Empty walker
- ``slot_animations.py`` SPEC 004 D5 slot_attachment track emission
- ``animations.py``      bone_transform track emission

Public API: ``export(filepath, *, pixels_per_unit)`` -- the only
function consumers should call.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import bpy

from ._schema import DEFAULT_PIXELS_PER_UNIT, SCHEMA_VERSION
from .animations import build_animations
from .scene_discovery import doc_name, find_armature, find_atlas_image, find_sprite_meshes
from .skeleton import build_skeleton, compute_bone_world_godot
from .slot_animations import build_slot_animations, merge_slot_animations_into
from .slots import build_slots_for_scene
from .sprites import build_sprite

__all__ = ["DEFAULT_PIXELS_PER_UNIT", "SCHEMA_VERSION", "export"]


def export(filepath: str | Path, *, pixels_per_unit: float = DEFAULT_PIXELS_PER_UNIT) -> None:
    """Write the active scene to a ``.proscenio`` file."""
    path_str = str(filepath)
    path = Path(bpy.path.abspath(path_str)) if path_str.startswith("//") else Path(path_str)
    scene = bpy.context.scene

    armature_obj = find_armature(scene)
    if armature_obj is None:
        raise RuntimeError("Proscenio export needs an Armature in the scene")

    bone_world_godot = compute_bone_world_godot(armature_obj, pixels_per_unit)
    skeleton, bone_rest_local = build_skeleton(armature_obj, bone_world_godot)

    sprite_objs = find_sprite_meshes(scene)

    doc: dict[str, Any] = {
        "format_version": SCHEMA_VERSION,
        "name": doc_name(),
        "pixels_per_unit": pixels_per_unit,
        "skeleton": skeleton,
        "sprites": [build_sprite(obj, bone_world_godot, pixels_per_unit) for obj in sprite_objs],
    }

    slots = build_slots_for_scene(scene)
    if slots:
        doc["slots"] = slots

    atlas = find_atlas_image(path)
    if atlas:
        doc["atlas"] = atlas

    animations = build_animations(scene.render.fps, pixels_per_unit, bone_rest_local)
    slot_anims = build_slot_animations(scene)
    if slot_anims:
        animations = merge_slot_animations_into(animations or [], slot_anims)
    if animations:
        doc["animations"] = animations

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
