"""Proscenio `.proscenio` writer.

Walks the active Blender scene and emits a JSON document conforming to
`schemas/proscenio.schema.json`.

Coordinate conventions
----------------------
Blender 2D rigs are typically laid out in the XZ world plane (Z up,
Y into the screen). Godot 2D is XY with Y down. The exporter maps:

    Godot.x = Blender.x * pixels_per_unit
    Godot.y = -Blender.z * pixels_per_unit

Rotations: the angle from the Godot +X axis to the bone direction is
computed in Godot space directly (CW positive when Y is down). Bone
local rotation is the world angle minus the parent's world angle.

UVs are written normalized [0, 1] of the atlas image — engine-agnostic.
The Godot importer multiplies by atlas size at attach time.

Vertex Y in mesh local space is dropped: sprite planes are assumed to
be authored as flat quads in Blender XY local then rotated 90° on X by
the user so they live in the XZ world plane.
"""

from __future__ import annotations

import json
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, TypedDict

import bpy
from mathutils import Vector

SCHEMA_VERSION = 1
DEFAULT_PIXELS_PER_UNIT = 100.0

# Closed value sets mirrored from `schemas/proscenio.schema.json`. Update
# both at the same time when the schema bumps.
TrackType = Literal["bone_transform", "sprite_frame", "slot_attachment", "visibility"]
InterpType = Literal["linear", "constant"]
SpriteType = Literal["polygon", "sprite_frame"]


class BoneDict(TypedDict):
    name: str
    parent: str | None
    position: list[float]
    rotation: float
    scale: list[float]
    length: float


class RestLocal(TypedDict):
    position: tuple[float, float]
    rotation: float
    scale: tuple[float, float]


class SpriteFrameDict(TypedDict):
    type: Literal["sprite_frame"]
    name: str
    bone: str
    hframes: int
    vframes: int
    frame: int
    centered: bool


def export(filepath: str | Path, *, pixels_per_unit: float = DEFAULT_PIXELS_PER_UNIT) -> None:
    """Write the active scene to a `.proscenio` file."""
    path_str = str(filepath)
    path = Path(bpy.path.abspath(path_str)) if path_str.startswith("//") else Path(path_str)
    scene = bpy.context.scene

    armature_obj = _find_armature(scene)
    if armature_obj is None:
        raise RuntimeError("Proscenio export needs an Armature in the scene")

    bone_world_godot = _compute_bone_world_godot(armature_obj, pixels_per_unit)
    skeleton, bone_rest_local = _build_skeleton(armature_obj, bone_world_godot)

    sprite_objs = _find_sprite_meshes(scene)

    doc: dict[str, Any] = {
        "format_version": SCHEMA_VERSION,
        "name": _doc_name(),
        "pixels_per_unit": pixels_per_unit,
        "skeleton": skeleton,
        "sprites": [_build_sprite(obj, bone_world_godot, pixels_per_unit) for obj in sprite_objs],
    }

    atlas = _find_atlas_image(path)
    if atlas:
        doc["atlas"] = atlas

    animations = _build_animations(scene.render.fps, pixels_per_unit, bone_rest_local)
    if animations:
        doc["animations"] = animations

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Object discovery
# --------------------------------------------------------------------------- #


def _find_armature(scene: bpy.types.Scene) -> bpy.types.Object | None:
    for obj in scene.objects:
        if obj.type == "ARMATURE":
            return obj
    return None


def _find_sprite_meshes(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    sprites: list[bpy.types.Object] = []
    for obj in scene.objects:
        if obj.type == "MESH":
            sprites.append(obj)
    sprites.sort(key=lambda o: o.name)
    return sprites


def _find_atlas_image(out_path: Path) -> str | None:
    """Return atlas filename, preferring linked images, falling back to a sibling atlas.png."""
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                fp = node.image.filepath
                if fp:
                    return Path(bpy.path.abspath(fp)).name
                return f"{node.image.name}.png"
    sibling = out_path.parent / "atlas.png"
    if sibling.exists():
        return sibling.name
    return None


def _doc_name() -> str:
    blend = bpy.data.filepath
    return Path(blend).stem if blend else "proscenio_doc"


# --------------------------------------------------------------------------- #
# Coordinate conversion
# --------------------------------------------------------------------------- #


def _world_to_godot_xy(p: Vector, ppu: float) -> Vector:
    """Blender world (XZ plane, Y into screen) → Godot world XY."""
    return Vector((p.x * ppu, -p.z * ppu))


def _godot_world_angle_from_dir(dir_blender: Vector) -> float:
    """Angle in Godot 2D from +X axis to the projection of `dir_blender` on XZ."""
    return math.atan2(-dir_blender.z, dir_blender.x)


# --------------------------------------------------------------------------- #
# Bone world transforms in Godot space
# --------------------------------------------------------------------------- #


def _compute_bone_world_godot(
    armature_obj: bpy.types.Object, ppu: float
) -> dict[str, dict[str, float]]:
    """Return per-bone Godot world position (Vector2-ish) and rotation in radians."""
    armature: bpy.types.Armature = armature_obj.data
    arm_world = armature_obj.matrix_world

    out: dict[str, dict[str, float]] = {}
    for bone in armature.bones:
        head_world_blender = arm_world @ bone.head_local
        tail_world_blender = arm_world @ bone.tail_local
        head_godot = _world_to_godot_xy(head_world_blender, ppu)
        dir_blender = tail_world_blender - head_world_blender
        angle = _godot_world_angle_from_dir(dir_blender)
        out[bone.name] = {
            "x": head_godot.x,
            "y": head_godot.y,
            "rot": angle,
            "length": bone.length * ppu,
        }
    return out


# --------------------------------------------------------------------------- #
# Skeleton
# --------------------------------------------------------------------------- #


def _build_skeleton(
    armature_obj: bpy.types.Object,
    world_godot: dict[str, dict[str, float]],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Return the skeleton JSON and a per-bone rest dict in Bone2D-local space.

    The rest dict is keyed by bone name and provides `position`, `rotation`,
    `scale` so the animation builder can emit absolute Godot animation values
    (rest + delta) instead of raw deltas.
    """
    armature: bpy.types.Armature = armature_obj.data
    bones_out: list[dict[str, Any]] = []
    rest_local: dict[str, dict[str, Any]] = {}

    for bone in armature.bones:
        w = world_godot[bone.name]
        if bone.parent is None:
            local_pos = (w["x"], w["y"])
            local_rot = w["rot"]
        else:
            p = world_godot[bone.parent.name]
            # Express child position in parent's local frame.
            dx = w["x"] - p["x"]
            dy = w["y"] - p["y"]
            cos_p = math.cos(-p["rot"])
            sin_p = math.sin(-p["rot"])
            local_pos = (dx * cos_p - dy * sin_p, dx * sin_p + dy * cos_p)
            local_rot = w["rot"] - p["rot"]
            local_rot = _wrap_pi(local_rot)

        bones_out.append(
            {
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
                "position": [round(local_pos[0], 6), round(local_pos[1], 6)],
                "rotation": round(local_rot, 6),
                "scale": [1.0, 1.0],
                "length": round(w["length"], 6),
            }
        )
        rest_local[bone.name] = {
            "position": (local_pos[0], local_pos[1]),
            "rotation": local_rot,
            "scale": (1.0, 1.0),
        }

    return {"bones": bones_out}, rest_local


def _wrap_pi(a: float) -> float:
    while a > math.pi:
        a -= 2.0 * math.pi
    while a < -math.pi:
        a += 2.0 * math.pi
    return a


# --------------------------------------------------------------------------- #
# Sprites
# --------------------------------------------------------------------------- #


def _build_sprite(
    obj: bpy.types.Object,
    world_godot: dict[str, dict[str, float]],
    ppu: float,
) -> dict[str, Any]:
    """Build a sprite entry. The sprite kind is read from the
    ``proscenio_type`` Object Custom Property (default ``"polygon"``).

    For ``sprite_frame``, the writer emits the spritesheet metadata (hframes,
    vframes, frame, centered) read from sibling custom properties; vertices
    and UVs are not produced because Godot's Sprite2D derives them from the
    grid at runtime.
    """
    sprite_type: str = str(obj.get("proscenio_type", "polygon"))
    if sprite_type == "sprite_frame":
        return dict(_build_sprite_frame(obj))
    if sprite_type != "polygon":
        raise RuntimeError(
            f"Proscenio: object {obj.name!r} has unknown proscenio_type "
            f"{sprite_type!r}; expected 'polygon' or 'sprite_frame'."
        )

    mesh: bpy.types.Mesh = obj.data
    mesh_world = obj.matrix_world

    bone_name = _resolve_sprite_bone(obj)
    bone_world = world_godot.get(bone_name)
    uv_layer = mesh.uv_layers.active

    polygon: list[list[float]] = []
    uvs: list[list[float]] = []

    if mesh.polygons:
        first_poly = mesh.polygons[0]
        for vi, li in zip(first_poly.vertices, first_poly.loop_indices, strict=False):
            v = mesh.vertices[vi]
            world_blender = mesh_world @ v.co
            world_godot_pos = _world_to_godot_xy(world_blender, ppu)
            if bone_world is None:
                local = world_godot_pos
            else:
                dx = world_godot_pos.x - bone_world["x"]
                dy = world_godot_pos.y - bone_world["y"]
                cos_b = math.cos(-bone_world["rot"])
                sin_b = math.sin(-bone_world["rot"])
                local = Vector((dx * cos_b - dy * sin_b, dx * sin_b + dy * cos_b))
            polygon.append([round(local.x, 6), round(local.y, 6)])

            if uv_layer is not None:
                u = uv_layer.data[li].uv
                # Blender UV origin is bottom-left; Godot pixel space is top-left.
                uvs.append([round(float(u.x), 6), round(1.0 - float(u.y), 6)])
            else:
                uvs.append([0.0, 0.0])

    region = _compute_texture_region(uvs)

    return {
        "name": obj.name,
        "bone": bone_name,
        "texture_region": region,
        "polygon": polygon,
        "uv": uvs,
    }


def _build_sprite_frame(obj: bpy.types.Object) -> SpriteFrameDict:
    """Emit a `sprite_frame` sprite entry from Object Custom Properties.

    Required custom properties on the Object:

        proscenio_type      = "sprite_frame"
        proscenio_hframes   : int  (>= 1)
        proscenio_vframes   : int  (>= 1)

    Optional:

        proscenio_frame     : int  (default 0)
        proscenio_centered  : bool (default True)
    """
    if "proscenio_hframes" not in obj or "proscenio_vframes" not in obj:
        raise RuntimeError(
            f"Proscenio: sprite_frame object {obj.name!r} needs "
            f"`proscenio_hframes` and `proscenio_vframes` Custom Properties."
        )

    return {
        "type": "sprite_frame",
        "name": obj.name,
        "bone": _resolve_sprite_bone(obj),
        "hframes": int(obj["proscenio_hframes"]),
        "vframes": int(obj["proscenio_vframes"]),
        "frame": int(obj.get("proscenio_frame", 0)),
        "centered": bool(obj.get("proscenio_centered", True)),
    }


def _resolve_sprite_bone(obj: bpy.types.Object) -> str:
    if obj.parent_type == "BONE" and obj.parent_bone:
        return str(obj.parent_bone)
    if obj.vertex_groups:
        return str(obj.vertex_groups[0].name)
    return ""


def _compute_texture_region(uvs: list[list[float]]) -> list[float]:
    if not uvs:
        return [0.0, 0.0, 0.0, 0.0]
    xs = [u[0] for u in uvs]
    ys = [u[1] for u in uvs]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    return [
        round(x_min, 6),
        round(y_min, 6),
        round(x_max - x_min, 6),
        round(y_max - y_min, 6),
    ]


# --------------------------------------------------------------------------- #
# Animations
# --------------------------------------------------------------------------- #


def _build_animations(
    fps: int, ppu: float, rest_local: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    animations: list[dict[str, Any]] = []
    for action in bpy.data.actions:
        anim = _build_animation(action, fps, ppu, rest_local)
        if anim is not None:
            animations.append(anim)
    return animations


def _action_fcurves(action: bpy.types.Action) -> Iterator[Any]:
    """Yield FCurves from a Blender 4.4+ layered action or a legacy action."""
    if hasattr(action, "fcurves") and action.fcurves:
        # Legacy action — Blender ≤ 4.3.
        yield from action.fcurves
        return
    if not hasattr(action, "layers"):
        return
    for layer in action.layers:
        for strip in layer.strips:
            channelbags = getattr(strip, "channelbags", None) or []
            for cb in channelbags:
                yield from cb.fcurves


_REST_FALLBACK: dict[str, Any] = {
    "position": (0.0, 0.0),
    "rotation": 0.0,
    "scale": (1.0, 1.0),
}


def _collect_bone_keys(
    action: bpy.types.Action, fps: int
) -> dict[str, dict[float, dict[str, dict[int, float]]]]:
    """Group fcurve samples by bone → time → property → axis."""
    bone_keys: dict[str, dict[float, dict[str, dict[int, float]]]] = {}
    for fc in _action_fcurves(action):
        bone_name, prop = _parse_bone_data_path(fc.data_path)
        if bone_name is None or prop is None:
            continue
        for kp in fc.keyframe_points:
            time = (kp.co[0] - 1.0) / float(fps)
            entry = bone_keys.setdefault(bone_name, {}).setdefault(time, {})
            entry.setdefault(prop, {})[fc.array_index] = float(kp.co[1])
    return bone_keys


def _absolute_position(rest_xy: tuple[float, float], delta: list[float] | None) -> list[float]:
    dx, dy = delta or [0.0, 0.0]
    return [round(rest_xy[0] + dx, 6), round(rest_xy[1] + dy, 6)]


def _absolute_rotation(rest_rot: float, delta: float | None) -> float:
    return round(_wrap_pi(rest_rot + (delta or 0.0)), 6)


def _absolute_scale(rest_xy: tuple[float, float], delta: list[float] | None) -> list[float]:
    sx, sy = delta or [1.0, 1.0]
    return [round(rest_xy[0] * sx, 6), round(rest_xy[1] * sy, 6)]


def _build_bone_track(
    bone_name: str,
    by_time: dict[float, dict[str, dict[int, float]]],
    ppu: float,
    rest_local: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build one `bone_transform` track. Channels with no non-rest deltas are
    dropped so the Bone2D rest pose is preserved on import. A bone keyed at
    rest still gets a track (timing markers only) — useful for `root` handles.
    """
    resolved = {t: _resolve_pose_entry(entry, ppu) for t, entry in by_time.items()}
    has = {
        p: any(r[p] is not None for r in resolved.values())
        for p in ("position", "rotation", "scale")
    }
    rest = rest_local.get(bone_name, _REST_FALLBACK)

    keys: list[dict[str, Any]] = []
    for t in sorted(resolved.keys()):
        r = resolved[t]
        key: dict[str, Any] = {"time": round(t, 6)}
        if has["position"]:
            key["position"] = _absolute_position(rest["position"], r["position"])
        if has["rotation"]:
            key["rotation"] = _absolute_rotation(rest["rotation"], r["rotation"])
        if has["scale"]:
            key["scale"] = _absolute_scale(rest["scale"], r["scale"])
        keys.append(key)

    return {"type": "bone_transform", "target": bone_name, "keys": keys}


def _build_animation(
    action: bpy.types.Action,
    fps: int,
    ppu: float,
    rest_local: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    bone_keys = _collect_bone_keys(action, fps)
    if not bone_keys:
        return None

    tracks = [
        _build_bone_track(name, by_time, ppu, rest_local) for name, by_time in bone_keys.items()
    ]
    frame_start, frame_end = action.frame_range
    length = max(0.001, (frame_end - frame_start) / float(fps))

    return {
        "name": action.name,
        "length": round(length, 6),
        "loop": True,
        "tracks": tracks,
    }


def _resolve_pose_entry(entry: dict[str, dict[int, float]], ppu: float) -> dict[str, Any]:
    """Reduce a per-time bucket of fcurve samples to (position, rotation, scale).

    Returns None for any channel whose value matches the rest pose so callers
    can decide whether to drop the channel from the entire track. Position is
    in Godot Bone2D-local pixels, rotation in Godot CW radians, scale unitless.
    """
    position: list[float] | None = None
    rotation: float | None = None
    scale: list[float] | None = None

    if "location" in entry:
        loc = entry["location"]
        bx = float(loc.get(0, 0.0))
        by = float(loc.get(1, 0.0))
        bz = float(loc.get(2, 0.0))
        if max(abs(bx), abs(by), abs(bz)) > 1e-6:
            # Bone-local delta → Godot Bone2D-local. For our XZ rig the bone
            # +Y axis points along the bone (Godot Bone2D +X) while bone +X is
            # lateral (Godot Bone2D +Y, after a sign flip).
            position = [round(by * ppu, 6), round(-bx * ppu, 6)]

    if "rotation_euler" in entry:
        rz = float(entry["rotation_euler"].get(2, 0.0))
        if abs(rz) > 1e-6:
            rotation = round(-rz, 6)
    if "rotation_quaternion" in entry:
        angle = _quat_to_screen_angle(entry["rotation_quaternion"])
        if abs(angle) > 1e-6:
            rotation = round(angle, 6)

    if "scale" in entry:
        sc = entry["scale"]
        sx = float(sc.get(0, 1.0))
        sy = float(sc.get(1, 1.0))
        sz = float(sc.get(2, 1.0))
        if max(abs(sx - 1.0), abs(sy - 1.0), abs(sz - 1.0)) > 1e-6:
            scale = [round(sy, 6), round(sx, 6)]

    return {"position": position, "rotation": rotation, "scale": scale}


def _quat_to_screen_angle(quat_axes: dict[int, float]) -> float:
    """Bone-local quaternion → Godot 2D screen rotation in radians.

    For our XZ-plane 2D rig, world +Y points away from the camera (front
    view) and bone Z aligns with -world Y. A user rotating a bone "around
    world Y" by +θ in Blender's pose mode produces a bone-local quaternion
    `(cos(θ/2), 0, 0, -sin(θ/2))`. The visual direction matches Godot's
    Y-down CW positive convention, so:

        godot_angle = -2 * atan2(q.z, q.w) = +θ

    This breaks down for rigs not aligned with the XZ plane — a future SPEC
    will generalize via the bone's rest matrix.
    """
    w = float(quat_axes.get(0, 1.0))
    z = float(quat_axes.get(3, 0.0))
    return -2.0 * math.atan2(z, w)


def _parse_bone_data_path(data_path: str) -> tuple[str | None, str | None]:
    if not data_path.startswith("pose.bones["):
        return None, None
    try:
        end = data_path.index("]")
        bone = data_path[12:end].strip("\"'")
        rest = data_path[end + 2 :]
    except ValueError:
        return None, None
    if rest == "location":
        return bone, "location"
    if rest == "rotation_euler":
        return bone, "rotation_euler"
    if rest == "rotation_quaternion":
        return bone, "rotation_quaternion"
    if rest == "scale":
        return bone, "scale"
    return None, None
