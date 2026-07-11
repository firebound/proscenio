"""Headless tests for the Animation-panel set-active-action operator (spec 045).

The action assignment must target the Skeleton picker
(`scene.proscenio.active_armature`), not the first armature it finds in
the scene.
"""

from __future__ import annotations

import bpy


def _set_picker(name: str | None) -> None:
    bpy.context.scene.proscenio.active_armature = (
        bpy.data.objects[name] if name is not None else None
    )


def _new_armature(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, bpy.data.armatures.new(name + "_data"))
    bpy.context.scene.collection.objects.link(obj)
    return obj


def test_assigns_action_to_picked_armature(automesh_fixture):
    arm = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    bpy.data.actions.new("anim_picked")

    result = bpy.ops.proscenio.set_active_action(action_name="anim_picked")

    assert "FINISHED" in result
    assert arm.animation_data is not None
    assert arm.animation_data.action is bpy.data.actions["anim_picked"]


def test_cancels_when_no_armature_picked(automesh_fixture):
    arm = bpy.data.objects["automesh.hand_rig"]
    # ensure no stale assignment, then clear the picker
    if arm.animation_data is not None:
        arm.animation_data.action = None
    _set_picker(None)
    bpy.data.actions.new("anim_no_picker")

    result = bpy.ops.proscenio.set_active_action(action_name="anim_no_picker")

    assert "CANCELLED" in result
    assert arm.animation_data is None or arm.animation_data.action is None


def test_refuses_a_visibility_only_action(automesh_fixture):
    """A slot swap (visibility-only) action must not graft onto the armature.

    Direct visibility keyframes create an action whose only fcurves are
    hide_render / hide_viewport; assigning it to the rig would play empty and
    hide the real rig action of that name. The operator refuses it (spec 079 D2).
    """
    arm = bpy.data.objects["automesh.hand_rig"]
    if arm.animation_data is not None:
        arm.animation_data.action = None
    _set_picker("automesh.hand_rig")

    # Author a visibility-only action on a scratch mesh so its fcurves are real.
    mesh = bpy.data.objects.new("swap_probe", bpy.data.meshes.new("swap_probe_m"))
    bpy.context.scene.collection.objects.link(mesh)
    mesh.animation_data_create()
    mesh.animation_data.action = bpy.data.actions.new("vis_only")
    mesh.hide_render = True
    mesh.hide_viewport = True
    mesh.keyframe_insert(data_path="hide_render", frame=1)
    mesh.keyframe_insert(data_path="hide_viewport", frame=1)

    result = bpy.ops.proscenio.set_active_action(action_name="vis_only")

    assert "CANCELLED" in result
    assert arm.animation_data is None or arm.animation_data.action is None, (
        "a visibility-only swap action must not be grafted onto the armature"
    )


def test_ignores_unpicked_second_armature(automesh_fixture):
    arm = bpy.data.objects["automesh.hand_rig"]
    other = _new_armature("other_rig")
    _set_picker("automesh.hand_rig")
    bpy.data.actions.new("anim_two")

    bpy.ops.proscenio.set_active_action(action_name="anim_two")

    assert arm.animation_data.action is bpy.data.actions["anim_two"]
    assert other.animation_data is None, "a non-picked scene armature must not receive the action"
