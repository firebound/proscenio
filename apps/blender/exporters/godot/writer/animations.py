"""Bone-transform animation emission (the skinning-weights wire format + 005)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NotRequired, TypedDict

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector
from proscenio_models import Animation, Key, Track

from ....core._shared.action_fcurves import action_fcurves
from ....core.bpy_helpers._shared._bpy_compat import iter_actions, iter_keyframe_points
from .skeleton import BoneRestLocal, rotate_vec2, wrap_pi

__all__ = ["action_fcurves", "build_animations"]


class _KeyKwargs(TypedDict):
    """Constructor kwargs for a ``bone_transform`` ``Key``.

    Channel fields are ``NotRequired`` so a track only emits the channels it
    animates; an explicit ``None`` would serialise as ``"position": null`` under
    exclude_unset and drift the goldens.
    """

    time: float
    position: NotRequired[list[float]]
    rotation: NotRequired[float]
    scale: NotRequired[list[float]]


_REST_FALLBACK = BoneRestLocal(
    position=(0.0, 0.0),
    rotation=0.0,
    scale=(1.0, 1.0),
    # World-aligned identity so a bone missing from the skeleton dict (e.g. a
    # bare `root` handle keyed at rest) still projects through the same path
    # rather than silently dropping its channels.
    rest_basis=Matrix(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))),
)


@dataclass(frozen=True)
class PoseDelta:
    """Per-keyframe (position, rotation, scale) delta extracted from fcurves.

    Each field is ``None`` when the fcurve produced no significant delta
    on that channel; the writer then drops the channel from the emitted
    track so the rest pose survives unchanged.
    """

    position: list[float] | None
    rotation: float | None
    scale: list[float] | None


def collect_bone_keys(
    action: bpy.types.Action,
    fps: int,
    deform_bones: set[str] | None = None,
) -> dict[str, dict[float, dict[str, dict[int, float]]]]:
    """Group fcurve samples by bone -> time -> property -> axis.

    When ``deform_bones`` is given, fcurves on a bone outside that set are
    dropped - the belt-and-braces export-leak guard so a control-bone track
    (``.IK`` / ``.pole``) never reaches the document even if it would otherwise
    resolve through ``_REST_FALLBACK``. ``None`` disables the filter (the bare
    ``root``-handle path and the pure-helper tests).
    """
    bone_keys: dict[str, dict[float, dict[str, dict[int, float]]]] = {}
    for fc in action_fcurves(action):
        bone_name, prop = _parse_bone_data_path(fc.data_path)
        if bone_name is None or prop is None:
            continue
        if deform_bones is not None and bone_name not in deform_bones:
            continue
        for kp in iter_keyframe_points(fc):
            # Clamp at 0: a bone keyed at Blender frame 0 would yield a negative
            # time, which trips the Key(time >= 0) constraint and aborts the
            # export. Matches the sprite_frame / slot writers.
            time = max(0.0, (float(kp.co.x) - 1.0) / float(fps))
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
    rest_local: dict[str, BoneRestLocal],
    parent_rot_by_time: dict[float, float] | None = None,
) -> Track:
    """Build one ``bone_transform`` track. Channels with no non-rest deltas are
    dropped so the Bone2D rest pose is preserved on import. A bone keyed at
    rest still gets a track (timing markers only) - useful for ``root`` handles.

    ``parent_rot_by_time`` maps a key time to the parent's POSED world rotation
    at that frame (empty / None when the parent is static); it overrides the rest
    parent rotation for the position projection so an animated-parent child does
    not read sideways in Godot.
    """
    rest = rest_local.get(bone_name, _REST_FALLBACK)
    # rest_basis is required for the location/rotation projection. Every bone the
    # skeleton builds carries one and the fallback is identity, so a None here is
    # a contract break (a stale BoneRestLocal); surface it instead of silently
    # emitting a motionless track.
    if rest.rest_basis is None and any(
        "location" in entry or "rotation_euler" in entry or "rotation_quaternion" in entry
        for entry in by_time.values()
    ):
        raise ValueError(f"missing rest_basis for animated bone {bone_name!r}")
    parent_rot = parent_rot_by_time or {}
    resolved = {
        t: _resolve_pose_entry(entry, ppu, rest, parent_rot.get(t)) for t, entry in by_time.items()
    }
    has_position = any(r.position is not None for r in resolved.values())
    has_rotation = any(r.rotation is not None for r in resolved.values())
    has_scale = any(r.scale is not None for r in resolved.values())

    keys: list[Key] = []
    for t in sorted(resolved.keys()):
        r = resolved[t]
        # Pass only the channels this track carries; omitting a channel leaves
        # the Key field unset so exclude_unset drops it. An explicit None would
        # emit "position": null.
        key_kwargs: _KeyKwargs = {"time": round(t, 6)}
        if has_position:
            key_kwargs["position"] = _absolute_position(rest.position, r.position)
        if has_rotation:
            key_kwargs["rotation"] = _absolute_rotation(rest.rotation, r.rotation)
        if has_scale:
            key_kwargs["scale"] = _absolute_scale(rest.scale, r.scale)
        keys.append(Key(**key_kwargs))

    return Track(type="bone_transform", target=bone_name, keys=keys)


def action_length(action: bpy.types.Action, fps: int) -> float:
    """Godot animation length (seconds) for ``action`` at ``fps``, rounded to 6dp.

    The one home for the ``frame_range`` -> length math shared by the bone,
    slot, and sprite-frame animation builders; clamped to a 0.001s floor so a
    single-frame action still emits a valid non-zero length.
    """
    frame_start = float(action.frame_range[0])
    frame_end = float(action.frame_range[1])
    return round(max(0.001, (frame_end - frame_start) / float(fps)), 6)


def build_animation(
    action: bpy.types.Action,
    fps: int,
    ppu: float,
    rest_local: dict[str, BoneRestLocal],
    deform_bones: set[str] | None = None,
) -> Animation | None:
    bone_keys = collect_bone_keys(action, fps, deform_bones)
    if not bone_keys:
        return None

    tracks = [
        build_bone_track(
            name,
            by_time,
            ppu,
            rest_local,
            _posed_parent_rotations(name, by_time, bone_keys, rest_local),
        )
        for name, by_time in bone_keys.items()
    ]
    return Animation(
        name=action.name,
        length=action_length(action, fps),
        loop=True,
        tracks=tracks,
    )


def build_animations(
    fps: int,
    ppu: float,
    rest_local: dict[str, BoneRestLocal],
    deform_bones: set[str] | None = None,
) -> list[Animation]:
    animations: list[Animation] = []
    for action in iter_actions():
        anim = build_animation(action, fps, ppu, rest_local, deform_bones)
        if anim is not None:
            animations.append(anim)
    return animations


def _local_rotation_matrix(entry: dict[str, dict[int, float]]) -> Matrix | None:
    """Bone-local rotation matrix (3x3) from euler, quaternion, or axis-angle samples."""
    if "rotation_euler" in entry:
        e = entry["rotation_euler"]
        return Euler((e.get(0, 0.0), e.get(1, 0.0), e.get(2, 0.0)), "XYZ").to_matrix()
    if "rotation_quaternion" in entry:
        q = entry["rotation_quaternion"]
        return Quaternion((q.get(0, 1.0), q.get(1, 0.0), q.get(2, 0.0), q.get(3, 0.0))).to_matrix()
    if "rotation_axis_angle" in entry:
        # Blender stores axis-angle as [angle, x, y, z]. A zero axis is the
        # rest default; fall back to +Z so the Quaternion build stays valid.
        a = entry["rotation_axis_angle"]
        angle = a.get(0, 0.0)
        axis = Vector((a.get(1, 0.0), a.get(2, 0.0), a.get(3, 1.0)))
        if axis.length_squared < 1e-12:  # degenerate/zero axis -> rest default
            axis = Vector((0.0, 0.0, 1.0))
        return Quaternion(axis.normalized(), angle).to_matrix()
    return None


def _screen_rotation_delta(entry: dict[str, dict[int, float]], rest: BoneRestLocal) -> float | None:
    """Godot screen-rotation delta (radians) for a keyframe's bone-local rotation.

    Rotates the bone-local Y axis (head->tail) by the rest orientation and the
    keyed local rotation to get the bone's screen direction, then takes the
    angle change from rest. Works for any in-plane bone (lateral or up), unlike
    reading a single euler axis - that only matched bones whose local Y was the
    camera axis. Returns None when the screen direction does not move.
    """
    local_rot = _local_rotation_matrix(entry)
    if local_rot is None or rest.rest_basis is None:
        return None
    basis = rest.rest_basis
    y = Vector((0.0, 1.0, 0.0))
    posed_dir = basis @ (local_rot @ y)
    rest_dir = basis @ y
    posed_angle = math.atan2(-posed_dir.z, posed_dir.x)
    rest_angle = math.atan2(-rest_dir.z, rest_dir.x)
    delta = wrap_pi(posed_angle - rest_angle)
    return round(delta, 6) if abs(delta) > 1e-6 else None


_ROTATION_PROPS = ("rotation_euler", "rotation_quaternion", "rotation_axis_angle")


def _entry_has_rotation(entry: dict[str, dict[int, float]]) -> bool:
    return any(prop in entry for prop in _ROTATION_PROPS)


def _interp_delta_at(t: float, samples: list[tuple[float, float]]) -> float:
    """Linearly interpolate a parent rotation delta at time ``t``.

    ``samples`` is the parent's ``(time, screen_rotation_delta)`` list, sorted.
    Clamps outside the keyed range (matching Godot holding the end keys) and
    interpolates linearly between them (bone rotation tracks are linear).
    """
    if t <= samples[0][0]:
        return samples[0][1]
    if t >= samples[-1][0]:
        return samples[-1][1]
    for i in range(1, len(samples)):
        t0, d0 = samples[i - 1]
        t1, d1 = samples[i]
        if t0 <= t <= t1:
            span = t1 - t0
            return d1 if span <= 0 else d0 + (d1 - d0) * (t - t0) / span
    return samples[-1][1]


def _ancestor_rotation_samples(
    parent_name: str,
    bone_keys: dict[str, dict[float, dict[str, dict[int, float]]]],
    rest_local: dict[str, BoneRestLocal],
) -> list[list[tuple[float, float]]]:
    """Sorted ``(time, screen-rotation delta)`` samples for the parent AND every
    animated ancestor above it.

    A bone's WORLD rotation is its parent's world rotation plus its OWN local
    rotation, so the direct parent's posed world rotation delta is the sum of the
    local rotation deltas of the parent and all its ancestors. Walks up the chain
    via ``parent_name`` collecting each ancestor that has rotation keys - so a
    rotating grandparent still turns a child's position even when the direct
    parent has no rotation key of its own.
    """
    chain: list[list[tuple[float, float]]] = []
    ancestor: str | None = parent_name
    seen: set[str] = set()
    while ancestor is not None and ancestor not in seen:
        seen.add(ancestor)
        anc_by_time = bone_keys.get(ancestor)
        anc_rest = rest_local.get(ancestor)
        if anc_rest is None:
            break
        if anc_by_time:
            samples = sorted(
                (t, _screen_rotation_delta(entry, anc_rest) or 0.0)
                for t, entry in anc_by_time.items()
                if _entry_has_rotation(entry)
            )
            if samples:
                chain.append(samples)
        ancestor = anc_rest.parent_name
    return chain


def _posed_parent_rotations(
    bone_name: str,
    by_time: dict[float, dict[str, dict[int, float]]],
    bone_keys: dict[str, dict[float, dict[str, dict[int, float]]]],
    rest_local: dict[str, BoneRestLocal],
) -> dict[float, float]:
    """The direct parent's POSED world rotation at each of the child's key times.

    Recovered analytically: the parent's posed world rotation is
    ``rest.parent_world_rot`` plus the sum of the screen-rotation deltas of the
    parent AND all its animated ancestors at that time (a bone's world rotation
    = its parent's world rotation + its own local rotation, so the deltas chain
    up - see :func:`_ancestor_rotation_samples`), interpolated to the child's key
    times. Empty when the parent is a root or nothing up the chain is
    rotation-animated, so a static-parent child keeps its rest projection (and
    every existing golden with it). Consistent with the writer's fcurve-only
    model: an ancestor posed by a driver/constraint has no rotation track to
    export, so nothing to sample.
    """
    rest = rest_local.get(bone_name)
    if rest is None or rest.parent_name is None:
        return {}
    chain = _ancestor_rotation_samples(rest.parent_name, bone_keys, rest_local)
    if not chain:
        return {}
    return {
        t: rest.parent_world_rot + sum(_interp_delta_at(t, samples) for samples in chain)
        for t in by_time
    }


def _resolve_pose_entry(
    entry: dict[str, dict[int, float]],
    ppu: float,
    rest: BoneRestLocal,
    parent_world_rot: float | None = None,
) -> PoseDelta:
    """Reduce a per-time bucket of fcurve samples to (position, rotation, scale).

    ``parent_world_rot`` overrides ``rest.parent_world_rot`` for the position
    projection: the builder passes the parent's POSED world rotation at this
    frame when the parent is rotation-animated, so the screen delta lands in the
    parent's animated frame rather than its rest frame. ``None`` keeps the rest
    rotation (a static parent, and every existing caller / test).
    """
    position: list[float] | None = None
    rotation: float | None = None
    scale: list[float] | None = None
    effective_parent_rot = rest.parent_world_rot if parent_world_rot is None else parent_world_rot

    if "location" in entry and rest.rest_basis is not None:
        loc = entry["location"]
        # The keyed location is in bone-local space; rotate it by the bone's rest
        # orientation to get the world delta, then project to the Godot screen
        # (drop Y depth, flip Z). Works for any in-plane bone, unlike reading
        # local X/Z directly (that only matched world-aligned bones).
        local = Vector((loc.get(0, 0.0), loc.get(1, 0.0), loc.get(2, 0.0)))
        world = rest.rest_basis @ local
        if max(abs(world.x), abs(world.z)) > 1e-6:
            # Project to the Godot screen, then rotate into the parent-local
            # frame the rest position lives in (Bone2D.position is parent-local).
            # Skipping this leaves a screen-space delta on a parent-local track:
            # correct only when the parent is unrotated, sideways otherwise.
            screen_x = world.x * ppu
            screen_y = -world.z * ppu
            local_x, local_y = rotate_vec2(screen_x, screen_y, -effective_parent_rot)
            position = [round(local_x, 6), round(local_y, 6)]

    rotation = _screen_rotation_delta(entry, rest)

    if "scale" in entry:
        sc = entry["scale"]
        sx = float(sc.get(0, 1.0))
        sz = float(sc.get(2, 1.0))
        # Same XZ reasoning: scaling along bone-Y has no visible effect, so it
        # must not promote a scale channel.
        if max(abs(sx - 1.0), abs(sz - 1.0)) > 1e-6:
            scale = [round(sx, 6), round(sz, 6)]

    return PoseDelta(position=position, rotation=rotation, scale=scale)


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
    if rest == "rotation_axis_angle":
        return bone, "rotation_axis_angle"
    if rest == "scale":
        return bone, "scale"
    return None, None
