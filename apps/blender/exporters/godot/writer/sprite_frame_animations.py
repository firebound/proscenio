"""Sprite-frame animation emission: bake bone-driven frame-index drivers.

A sprite's frame index can be driven from a pose bone (the Drive-from-Bone
shortcut writes a SCRIPTED driver on the ``["proscenio_frame"]`` Custom
Property). Blender evaluates the driver as the bone animates, but the raw
fcurve carries no keyframes, so the writer baked nothing - the in-Blender
preview switched frames while the export dropped them. This module bakes the
driven value by stepping the scene over the armature's assigned action,
reading the posed bone channel the driver reads, evaluating the driver
expression, and emitting a ``sprite_frame`` track with constant-interpolation
keys at each change.

The driver targets the ``proscenio_frame`` idprop directly (the field's one
storage home, present whether or not the addon PropertyGroup is registered),
so the same track exports headless and in the editor; reproducing the driver
from the posed bone keeps the bake independent of live driver evaluation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import bpy
from proscenio_models import Animation, Key, Track

from ....core._shared.action_fcurves import action_fcurves
from ....core._shared.pg_cp_fallback import read_field
from ....core.bpy_helpers._shared._bpy_compat import (
    iter_driver_targets,
    iter_driver_variables,
    iter_drivers,
    iter_keyframe_points,
    iter_objects,
    pose_bone_by_name,
)

_FRAME_DRIVER_PATH = '["proscenio_frame"]'
_ROT_COMPONENT = {"ROT_X": 0, "ROT_Y": 1, "ROT_Z": 2}
_LOC_COMPONENT = {"LOC_X": 0, "LOC_Y": 1, "LOC_Z": 2}
# Math functions/constants a driver expression may reference (Blender exposes
# the math module in its driver namespace). Builtins are stripped at eval time
# so only these and the driver variables resolve - math has no system access.
_SAFE_MATH: dict[str, object] = {
    name: value for name, value in vars(math).items() if not name.startswith("_")
}


@dataclass(frozen=True)
class _FrameDriver:
    """A sprite whose frame idprop is driven from a pose bone."""

    sprite: bpy.types.Object
    armature: bpy.types.Object
    driver: bpy.types.Driver


def _driver_armature(driver: bpy.types.Driver) -> bpy.types.Object | None:
    """Return the armature object the driver reads a bone transform from."""
    for variable in iter_driver_variables(driver):
        for target in iter_driver_targets(variable):
            source = target.id
            if isinstance(source, bpy.types.Object) and source.type == "ARMATURE":
                return source
    return None


def _collect_frame_drivers(scene: bpy.types.Scene) -> list[_FrameDriver]:
    """Find sprites whose frame idprop is driven from a bone."""
    out: list[_FrameDriver] = []
    for obj in iter_objects(scene):
        anim_data = obj.animation_data
        if anim_data is None:
            continue
        for fcurve in iter_drivers(anim_data):
            if fcurve.data_path != _FRAME_DRIVER_PATH:
                continue
            driver = fcurve.driver
            if driver is None:
                continue
            armature = _driver_armature(driver)
            if armature is not None:
                out.append(_FrameDriver(sprite=obj, armature=armature, driver=driver))
            break
    return out


def _transform_channel(target: bpy.types.DriverTarget) -> float:
    """Read the posed-bone transform channel the driver variable points at.

    Reproduces a TRANSFORMS driver variable: a rotation channel decodes the
    bone matrix to Euler in the target's space, a location channel reads the
    translation. Only ROT_Y in WORLD_SPACE is exercised by a fixture; the
    other axes follow the same documented convention.
    """
    armature = target.id
    if not isinstance(armature, bpy.types.Object) or armature.type != "ARMATURE":
        return 0.0
    pose = armature.pose
    if pose is None:
        return 0.0
    pose_bone = pose_bone_by_name(pose, target.bone_target)
    if pose_bone is None:
        return 0.0
    world_space = target.transform_space == "WORLD_SPACE"
    matrix = armature.matrix_world @ pose_bone.matrix if world_space else pose_bone.matrix_basis
    channel = target.transform_type
    if channel in _ROT_COMPONENT:
        # The Drive-from-Bone shortcut writes XYZ Euler rotation channels.
        return float(matrix.to_euler("XYZ")[_ROT_COMPONENT[channel]])
    if channel in _LOC_COMPONENT:
        return float(matrix.to_translation()[_LOC_COMPONENT[channel]])
    return 0.0


def _driver_values(driver: bpy.types.Driver) -> dict[str, float] | None:
    """Build the {variable name -> value} namespace at the current posed frame.

    Returns None when any variable is not a bone TRANSFORMS read - the bake
    only reproduces the Drive-from-Bone shape, so an unfamiliar variable type
    skips the sprite rather than guessing.
    """
    values: dict[str, float] = {}
    for variable in iter_driver_variables(driver):
        if variable.type != "TRANSFORMS":
            return None
        target = next(iter(iter_driver_targets(variable)), None)
        if target is None:
            return None
        values[variable.name] = _transform_channel(target)
    return values


def _eval_frame(expression: str, values: dict[str, float]) -> int | None:
    """Evaluate the driver expression to an integer frame index, or None.

    The expression is the user's own Blender driver (Blender already evaluates
    it every frame); builtins are stripped so only the driver variables and the
    math subset resolve. Truncates toward zero to match Blender's float->int
    assignment onto the integer ``frame`` property.
    """
    try:
        result = eval(expression, {"__builtins__": {}}, {**_SAFE_MATH, **values})
    except Exception:
        return None
    return int(result)


def _grid_max_frame(sprite: bpy.types.Object) -> int:
    """Highest valid frame index for the sprite's grid (``hframes * vframes - 1``)."""
    hframes = int(read_field(sprite, cp_key="proscenio_hframes", default=1))
    vframes = int(read_field(sprite, cp_key="proscenio_vframes", default=1))
    return max(0, hframes * vframes - 1)


def _wrap_frame(raw: int, max_frame: int) -> int:
    """Wrap an out-of-range frame index into the grid, matching Blender's preview.

    The driven (or keyed) value can overshoot the grid, and Godot's
    ``Sprite2D.frame`` rejects an out-of-range index. Blender's spritesheet
    preview shader picks the cell with a ``MODULO`` on the frame, so an index
    past the last cell wraps back to the start (``4 -> 0``, ``5 -> 1`` for a
    4-cell grid) rather than sticking on the last cell. Wrap here too so the
    export matches what the author saw in Blender; clamping instead collapsed
    the overshoot into one repeated cell and dropped the motion. Python's
    modulo keeps the result in ``[0, max_frame]`` for negative indices as well
    (``-1 -> max_frame``), the same cell Blender's texture-repeat lands on.
    """
    return raw % (max_frame + 1)


def _bake_track(
    scene: bpy.types.Scene, fd: _FrameDriver, action: bpy.types.Action, fps: int
) -> Track | None:
    """Step the scene over the action and bake the driven frame into a track.

    The driven value can overshoot the sprite grid (the expression is
    arbitrary), and Godot's ``Sprite2D.frame`` rejects an out-of-range index,
    so wrap into ``[0, hframes * vframes - 1]`` - matching Blender's preview
    (see :func:`_wrap_frame`). A key lands only where the frame changes -
    frames are discrete, so the keys carry constant interpolation (hard cuts).
    Times use the ``(frame - 1) / fps`` base shared with the bone tracks so the
    two play in lockstep.
    """
    lo = int(action.frame_range[0])
    hi = int(action.frame_range[1])
    max_frame = _grid_max_frame(fd.sprite)
    keys: list[Key] = []
    last: int | None = None
    for frame in range(lo, hi + 1):
        scene.frame_set(frame)
        values = _driver_values(fd.driver)
        if values is None:
            return None
        raw = _eval_frame(fd.driver.expression, values)
        if raw is None:
            return None
        value = _wrap_frame(raw, max_frame)
        if value != last:
            # (frame - 1) / fps matches the bone tracks; clamp at 0 so an action
            # starting at frame 0 does not emit a negative time (Key.time is ge=0).
            time = round(max(0.0, (frame - 1) / float(fps)), 6)
            keys.append(Key(time=time, interp="constant", frame=value))
            last = value
    if not keys:
        return None
    return Track(type="sprite_frame", target=fd.sprite.name, keys=keys)


def _action_length(action: bpy.types.Action, fps: int) -> float:
    frame_start = float(action.frame_range[0])
    frame_end = float(action.frame_range[1])
    return round(max(0.001, (frame_end - frame_start) / float(fps)), 6)


def _direct_frame_track(
    sprite: bpy.types.Object, action: bpy.types.Action, fps: int
) -> Track | None:
    """Emit a ``sprite_frame`` track from keyframes set directly on the sprite's
    ``["proscenio_frame"]`` Custom Property (the blink_eyes shape: a frame
    cycle, no driver).

    Reads the fcurve keyframe values straight off the action, so it does not
    need the addon PropertyGroup registered. Wraps into the sprite grid (see
    :func:`_wrap_frame`), constant interpolation, ``(frame - 1) / fps`` time
    base - same as the driven bake.
    """
    fcurve: bpy.types.FCurve | None = None
    for fc in action_fcurves(action):
        if fc.data_path == _FRAME_DRIVER_PATH:
            fcurve = fc
            break
    if fcurve is None:
        return None
    max_frame = _grid_max_frame(sprite)
    keys: list[Key] = []
    last: int | None = None
    for kp in iter_keyframe_points(fcurve):
        value = _wrap_frame(round(float(kp.co[1])), max_frame)
        time = round(max(0.0, (float(kp.co[0]) - 1.0) / float(fps)), 6)
        if value != last:
            keys.append(Key(time=time, interp="constant", frame=value))
            last = value
    if not keys:
        return None
    return Track(type="sprite_frame", target=sprite.name, keys=keys)


def _is_sprite(obj: bpy.types.Object) -> bool:
    return str(read_field(obj, cp_key="proscenio_type", default="mesh")) == "sprite"


def build_sprite_frame_animations(scene: bpy.types.Scene, fps: int) -> list[Animation]:
    """Bake sprite-frame animations: bone-driven frames AND frames keyed directly
    on the frame idprop.

    One animation per action, named to match ``build_animations`` so the by-name
    merge folds the track in beside any bone_transform tracks. Restores the
    current frame so the driven bake leaves no scene-state trace.
    """
    by_action: dict[str, list[Track]] = {}
    lengths: dict[str, float] = {}

    # Direct keyframes on the sprite's own action (no scene stepping needed).
    for obj in iter_objects(scene):
        if obj.type != "MESH" or not _is_sprite(obj):
            continue
        anim_data = obj.animation_data
        action = anim_data.action if anim_data is not None else None
        if action is None:
            continue
        track = _direct_frame_track(obj, action, fps)
        if track is not None:
            by_action.setdefault(action.name, []).append(track)
            lengths[action.name] = _action_length(action, fps)

    # Bone-driven frames (steps the scene to evaluate each driver).
    drivers = _collect_frame_drivers(scene)
    if drivers:
        saved_frame = scene.frame_current
        try:
            for fd in drivers:
                anim_data = fd.armature.animation_data
                action = anim_data.action if anim_data is not None else None
                if action is None:
                    continue
                track = _bake_track(scene, fd, action, fps)
                if track is None:
                    continue
                by_action.setdefault(action.name, []).append(track)
                lengths[action.name] = _action_length(action, fps)
        finally:
            scene.frame_set(saved_frame)

    return [
        Animation(name=name, length=lengths[name], loop=True, tracks=tracks)
        for name, tracks in by_action.items()
    ]
