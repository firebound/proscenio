"""Doll actions — idle, wave, blink, walk (SPEC 007 step 3).

Each action keyframes a small set of bones across a fixed frame range.
The animation values are intentionally small (a few degrees / cm) so the
test stays inside the writer's expected precision rounding.
"""

from __future__ import annotations

import math

import bpy

IDLE_FRAMES = 30
WAVE_FRAMES = 30
BLINK_FRAMES = 12
WALK_FRAMES = 30


def build_idle(armature_obj: bpy.types.Object) -> bpy.types.Action:
    """Subtle spine bob + breath. Loops cleanly."""
    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name="idle")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = IDLE_FRAMES

    bpy.ops.object.mode_set(mode="POSE")
    spine = armature_obj.pose.bones.get("spine.001")
    spine_002 = armature_obj.pose.bones.get("spine.002")
    if spine is not None:
        for frame, dy in ((1, 0.0), (8, 0.012), (16, 0.0), (24, -0.012), (30, 0.0)):
            bpy.context.scene.frame_set(frame)
            spine.location = (0.0, 0.0, dy)
            spine.keyframe_insert(data_path="location", frame=frame)
    if spine_002 is not None:
        for frame, dy in ((1, 0.0), (15, 0.008), (30, 0.0)):
            bpy.context.scene.frame_set(frame)
            spine_002.location = (0.0, 0.0, dy)
            spine_002.keyframe_insert(data_path="location", frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")
    return action


def build_wave(armature_obj: bpy.types.Object) -> bpy.types.Action:
    """Right-arm wave — shoulder.R + upper_arm.R + forearm.R rotation."""
    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name="wave")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = WAVE_FRAMES

    bpy.ops.object.mode_set(mode="POSE")
    upper = armature_obj.pose.bones.get("upper_arm.R")
    fore = armature_obj.pose.bones.get("forearm.R")
    if upper is not None:
        upper.rotation_mode = "XYZ"
        for frame, deg in ((1, 0.0), (10, -90.0), (20, -90.0), (30, 0.0)):
            bpy.context.scene.frame_set(frame)
            upper.rotation_euler = (0.0, math.radians(deg), 0.0)
            upper.keyframe_insert(data_path="rotation_euler", frame=frame)
    if fore is not None:
        fore.rotation_mode = "XYZ"
        for frame, deg in ((1, 0.0), (10, -30.0), (15, -45.0), (20, -30.0), (30, 0.0)):
            bpy.context.scene.frame_set(frame)
            fore.rotation_euler = (0.0, math.radians(deg), 0.0)
            fore.keyframe_insert(data_path="rotation_euler", frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")
    return action


def build_blink(eye_l_obj: bpy.types.Object, eye_r_obj: bpy.types.Object) -> bpy.types.Action:
    """Both eyes animate ``proscenio.frame`` 0→1→2→3→2→1→0 over 12 frames.

    Action targets the eye objects (one action per object actually — Blender
    actions are per-Object animation_data). Returns the eye_l action; the
    eye_r action is created independently here.
    """
    sequence = (
        (1, 0),
        (3, 1),
        (5, 2),
        (7, 3),
        (9, 2),
        (11, 1),
        (12, 0),
    )
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = BLINK_FRAMES

    primary_action = None
    for obj in (eye_l_obj, eye_r_obj):
        obj.animation_data_create()
        action_name = f"blink.{obj.name}"
        action = bpy.data.actions.new(name=action_name)
        obj.animation_data.action = action
        if primary_action is None:
            primary_action = action
        for frame, value in sequence:
            bpy.context.scene.frame_set(frame)
            if hasattr(obj, "proscenio"):
                obj.proscenio.frame = value
                obj.proscenio.keyframe_insert(data_path="frame", frame=frame)
            else:
                obj["proscenio_frame"] = value
                obj.keyframe_insert(data_path='["proscenio_frame"]', frame=frame)
    assert primary_action is not None
    return primary_action


def build_walk(armature_obj: bpy.types.Object) -> bpy.types.Action:
    """30-frame walk loop — thigh + shin + spine sway."""
    armature_obj.animation_data_create()
    action = bpy.data.actions.new(name="walk")
    armature_obj.animation_data.action = action
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = WALK_FRAMES

    bpy.ops.object.mode_set(mode="POSE")
    pose = armature_obj.pose

    def _key(bone_name: str, frame: int, deg: float) -> None:
        bone = pose.bones.get(bone_name)
        if bone is None:
            return
        bone.rotation_mode = "XYZ"
        bpy.context.scene.frame_set(frame)
        bone.rotation_euler = (0.0, math.radians(deg), 0.0)
        bone.keyframe_insert(data_path="rotation_euler", frame=frame)

    # Left leg forward → back
    for frame, deg in ((1, 20.0), (8, 0.0), (15, -20.0), (22, 0.0), (30, 20.0)):
        _key("thigh.L", frame, deg)
        _key("thigh.R", frame, -deg)
    for frame, deg in ((1, 0.0), (8, -15.0), (15, 0.0), (22, -15.0), (30, 0.0)):
        _key("shin.L", frame, deg)
        _key("shin.R", frame, deg)
    # Spine subtle counter-sway
    spine = pose.bones.get("spine")
    if spine is not None:
        spine.rotation_mode = "XYZ"
        for frame, deg in ((1, 0.0), (8, 2.0), (15, 0.0), (22, -2.0), (30, 0.0)):
            bpy.context.scene.frame_set(frame)
            spine.rotation_euler = (0.0, 0.0, math.radians(deg))
            spine.keyframe_insert(data_path="rotation_euler", frame=frame)

    bpy.ops.object.mode_set(mode="OBJECT")
    return action


def build_all(
    armature_obj: bpy.types.Object,
    sprite_objs: dict[str, bpy.types.Object],
) -> None:
    """Build every doll action in a fresh state."""
    build_idle(armature_obj)
    build_wave(armature_obj)
    eye_l = sprite_objs.get("eye.L")
    eye_r = sprite_objs.get("eye.R")
    if eye_l is not None and eye_r is not None:
        build_blink(eye_l, eye_r)
    build_walk(armature_obj)
