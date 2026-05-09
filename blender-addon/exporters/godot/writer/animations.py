"""Bone-transform animation emission (SPEC 003 + 005)."""

from __future__ import annotations

import math
from collections.abc import Iterator
from typing import Any

import bpy

from .skeleton import wrap_pi


def action_fcurves(action: bpy.types.Action) -> Iterator[Any]:
    """Yield FCurves from a Blender 4.4+ layered action or a legacy action."""
    if hasattr(action, "fcurves") and action.fcurves:
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


def collect_bone_keys(
    action: bpy.types.Action, fps: int
) -> dict[str, dict[float, dict[str, dict[int, float]]]]:
    """Group fcurve samples by bone -> time -> property -> axis."""
    bone_keys: dict[str, dict[float, dict[str, dict[int, float]]]] = {}
    for fc in action_fcurves(action):
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
    return round(wrap_pi(rest_rot + (delta or 0.0)), 6)


def _absolute_scale(rest_xy: tuple[float, float], delta: list[float] | None) -> list[float]:
    sx, sy = delta or [1.0, 1.0]
    return [round(rest_xy[0] * sx, 6), round(rest_xy[1] * sy, 6)]


def build_bone_track(
    bone_name: str,
    by_time: dict[float, dict[str, dict[int, float]]],
    ppu: float,
    rest_local: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build one ``bone_transform`` track. Channels with no non-rest deltas are
    dropped so the Bone2D rest pose is preserved on import. A bone keyed at
    rest still gets a track (timing markers only) -- useful for ``root`` handles.
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


def build_animation(
    action: bpy.types.Action,
    fps: int,
    ppu: float,
    rest_local: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    bone_keys = collect_bone_keys(action, fps)
    if not bone_keys:
        return None

    tracks = [
        build_bone_track(name, by_time, ppu, rest_local) for name, by_time in bone_keys.items()
    ]
    frame_start, frame_end = action.frame_range
    length = max(0.001, (frame_end - frame_start) / float(fps))

    return {
        "name": action.name,
        "length": round(length, 6),
        "loop": True,
        "tracks": tracks,
    }


def build_animations(
    fps: int, ppu: float, rest_local: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    animations: list[dict[str, Any]] = []
    for action in bpy.data.actions:
        anim = build_animation(action, fps, ppu, rest_local)
        if anim is not None:
            animations.append(anim)
    return animations


def _resolve_pose_entry(entry: dict[str, dict[int, float]], ppu: float) -> dict[str, Any]:
    """Reduce a per-time bucket of fcurve samples to (position, rotation, scale)."""
    position: list[float] | None = None
    rotation: float | None = None
    scale: list[float] | None = None

    if "location" in entry:
        loc = entry["location"]
        bx = float(loc.get(0, 0.0))
        by = float(loc.get(1, 0.0))
        bz = float(loc.get(2, 0.0))
        if max(abs(bx), abs(by), abs(bz)) > 1e-6:
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
    """Bone-local quaternion -> Godot 2D screen rotation in radians.

    For our XZ-plane 2D rig, world +Y points away from the camera (front
    view) and bone Z aligns with -world Y. A user rotating a bone "around
    world Y" by +theta in Blender's pose mode produces a bone-local
    quaternion ``(cos(theta/2), 0, 0, -sin(theta/2))``. The visual
    direction matches Godot's Y-down CW positive convention, so:

        godot_angle = -2 * atan2(q.z, q.w) = +theta

    This breaks down for rigs not aligned with the XZ plane -- a future
    SPEC will generalize via the bone's rest matrix.
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
