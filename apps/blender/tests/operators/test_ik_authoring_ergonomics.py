"""Headless tests for the IK authoring ergonomics (spec 056 calls 1, 2, 3).

Runs INSIDE Blender via ``run_operator_tests.py``. Covers the create / remove
label resolution, the IK chains subpanel poll, the keyframable influence
affordance, and the opt-in in-plane DOF lock. The chain-scan that drives the
panel cues is unit-tested in ``tests/test_ik_chains.py``; the Rigify-style
control affordances in ``test_ik_control_affordances.py``; the export-leak
filter in ``test_export_leak_control_bones.py``.
"""

from __future__ import annotations

import bpy


def _enter_pose_with_active_bone(rig_name: str, bone_name: str) -> bpy.types.Object:
    rig = bpy.data.objects[rig_name]
    bpy.context.view_layer.objects.active = rig
    for other in bpy.context.selected_objects:
        other.select_set(False)
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    rig.data.bones.active = rig.data.bones[bone_name]
    return rig


def test_key_ik_influence_inserts_a_keyframe(automesh_fixture: None) -> None:
    from proscenio.core._shared.action_fcurves import action_fcurves

    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        bpy.ops.proscenio.toggle_ik_chain()
        bpy.context.scene.frame_set(3)
        assert "FINISHED" in bpy.ops.proscenio.key_ik_influence()

        action = rig.animation_data.action
        assert action is not None, "keying influence created no action"
        # 5.1 uses the layered action API; action_fcurves walks both paths.
        paths = {fc.data_path for fc in action_fcurves(action)}
        keyed_influence = any("Proscenio IK" in p and p.endswith("influence") for p in paths)
        assert keyed_influence, "no influence fcurve was inserted"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_key_ik_influence_poll_false_without_chain(automesh_fixture: None) -> None:
    from proscenio.operators.armature.authoring_ik import PROSCENIO_OT_key_ik_influence

    _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        # No chain on the active bone yet -> the affordance is gated off.
        assert PROSCENIO_OT_key_ik_influence.poll(bpy.context) is False
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_chains_subpanel_poll_follows_chain_presence(automesh_fixture: None) -> None:
    from proscenio.panels.skeleton import PROSCENIO_PT_ik_chains

    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        bpy.context.scene.proscenio.active_armature = rig
        # No chain yet -> the inventory subpanel stays hidden.
        assert PROSCENIO_PT_ik_chains.poll(bpy.context) is False
        bpy.ops.proscenio.toggle_ik_chain()
        assert PROSCENIO_PT_ik_chains.poll(bpy.context) is True
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_ik_toggle_label_resolves_from_state(automesh_fixture: None) -> None:
    from proscenio.panels.skeleton import _active_ik_constraint

    _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        # The button label is "Add IK Chain" while absent, "Remove IK Chain"
        # while present; both read this single state source.
        assert _active_ik_constraint(bpy.context) is None
        bpy.ops.proscenio.toggle_ik_chain()
        assert _active_ik_constraint(bpy.context) is not None
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def test_inplane_lock_toggles_dof_flags(automesh_fixture: None) -> None:
    rig = _enter_pose_with_active_bone("automesh.hand_rig", "fingertip")
    try:
        bpy.ops.proscenio.toggle_ik_chain()
        tip = rig.pose.bones["fingertip"]
        assert not (tip.lock_ik_x and tip.lock_ik_z), "chain started already locked"

        assert "FINISHED" in bpy.ops.proscenio.toggle_ik_inplane_lock()
        assert tip.lock_ik_x and tip.lock_ik_z, "in-plane lock did not set the DOF flags"
        assert tip.lock_ik_y is False, "the in-plane (Y) swing axis must stay free"

        assert "FINISHED" in bpy.ops.proscenio.toggle_ik_inplane_lock()
        assert not (tip.lock_ik_x or tip.lock_ik_z), "second toggle did not unlock"
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
