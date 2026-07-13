"""Headless tests for the element bone-follow operators (Bind / Convert / Clear).

Runs INSIDE Blender via ``run_operator_tests.py``. Constraint-first (spec 080
D4): Bind authors object-parent + a Child Of whose inverse cancels the bone
REST via the shared bone-follow core; a raw keep-transform bone parent stays a
power-user fallback that Convert upgrades in place. The exporter reads the
binding through ``resolve_sprite_bone`` (constraint first).
"""

from __future__ import annotations

import bpy
import pytest


def _add_armature_with_bone(
    name: str,
    bone: str,
    head: tuple[float, float, float],
    tail: tuple[float, float, float],
) -> bpy.types.Object:
    arm_data = bpy.data.armatures.new(name)
    arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones.new(bone)
    eb.head = head
    eb.tail = tail
    bpy.ops.object.mode_set(mode="OBJECT")
    # Pick this rig as the Skeleton target, the way the user would, so the
    # bone-attach resolver targets it over the fixture's own armature.
    bpy.context.scene.proscenio.active_armature = arm
    return arm


def _add_sprite(name: str, location: tuple[float, float, float]) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(
        [(-0.5, 0.0, -0.5), (0.5, 0.0, -0.5), (0.5, 0.0, 0.5), (-0.5, 0.0, 0.5)],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.proscenio.element_type = "sprite"
    return obj


def _activate_only(obj: bpy.types.Object) -> None:
    for other in list(bpy.context.selected_objects):
        other.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _assert_world_equal(obj: bpy.types.Object, expected) -> None:
    for i in range(4):
        for j in range(4):
            assert obj.matrix_world[i][j] == pytest.approx(expected[i][j], abs=1e-5)


def _follow_constraint(obj: bpy.types.Object) -> bpy.types.Constraint | None:
    return obj.constraints.get("Proscenio Sprite Follow")


def test_bind_authors_constraint_keeps_world_and_exports(automesh_fixture):
    from proscenio.exporters.godot.writer.sprites import (  # type: ignore[import-not-found]
        resolve_sprite_bone,
    )

    arm = _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))
    bpy.context.view_layer.update()
    world_before = sprite.matrix_world.copy()

    _activate_only(sprite)
    result = bpy.ops.proscenio.parent_sprite_to_bone(bone_name="spine")

    assert "FINISHED" in result
    # Constraint-first: NO raw bone parent is authored.
    assert sprite.parent_type != "BONE"
    con = _follow_constraint(sprite)
    assert con is not None and con.type == "CHILD_OF"
    assert con.target is arm and con.subtarget == "spine"
    # The inverse cancels the bone REST, so the sprite stays put at rest.
    bpy.context.view_layer.update()
    _assert_world_equal(sprite, world_before)
    assert resolve_sprite_bone(sprite) == "spine"  # exporter reads the constraint


def test_bind_inverse_is_computed_from_rest_not_pose(automesh_fixture):
    arm = _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))
    # Pose the bone BEFORE binding: the inverse must still cancel the REST
    # (what Godot reproduces), never the posed matrix (D7).
    arm.pose.bones["spine"].rotation_mode = "XYZ"
    arm.pose.bones["spine"].rotation_euler = (0.0, 0.6, 0.0)
    bpy.context.view_layer.update()

    _activate_only(sprite)
    bpy.ops.proscenio.parent_sprite_to_bone(bone_name="spine")

    con = _follow_constraint(sprite)
    expected = (arm.matrix_world @ arm.data.bones["spine"].matrix_local).inverted()
    for i in range(4):
        for j in range(4):
            assert con.inverse_matrix[i][j] == pytest.approx(expected[i][j], abs=1e-6)


def test_clear_removes_constraint_and_keeps_world(automesh_fixture):
    _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))

    _activate_only(sprite)
    bpy.ops.proscenio.parent_sprite_to_bone(bone_name="spine")
    bpy.context.view_layer.update()
    world_before = sprite.matrix_world.copy()

    result = bpy.ops.proscenio.clear_sprite_bone_parent()

    assert "FINISHED" in result
    assert _follow_constraint(sprite) is None
    assert sprite.parent_type != "BONE"
    bpy.context.view_layer.update()
    _assert_world_equal(sprite, world_before)


def test_convert_upgrades_raw_parent_to_constraint(automesh_fixture):
    from proscenio.exporters.godot.writer.sprites import (  # type: ignore[import-not-found]
        resolve_sprite_bone,
    )

    arm = _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))
    bpy.context.view_layer.update()
    # Hand-author the power-user fallback: a keep-transform raw bone parent.
    world = sprite.matrix_world.copy()
    sprite.parent = arm
    sprite.parent_type = "BONE"
    sprite.parent_bone = "spine"
    sprite.matrix_parent_inverse.identity()
    sprite.matrix_world = world
    bpy.context.view_layer.update()
    world_before = sprite.matrix_world.copy()

    _activate_only(sprite)
    result = bpy.ops.proscenio.convert_element_follow()

    assert "FINISHED" in result
    assert sprite.parent_type != "BONE"  # raw parent dropped
    con = _follow_constraint(sprite)
    assert con is not None and con.subtarget == "spine"  # same bone, new shape
    bpy.context.view_layer.update()
    _assert_world_equal(sprite, world_before)  # never moved on screen
    assert resolve_sprite_bone(sprite) == "spine"


def test_convert_on_a_posed_rig_preserves_the_authored_rest(automesh_fixture):
    # The corrupted-convert repro: converting a bone-parented element while
    # the rig sits on a posed frame must NOT bake that frame's pose into the
    # element's new rest - the keep-world snapshot runs against the REST pose.
    arm = _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))
    bpy.context.view_layer.update()
    world_at_rest = sprite.matrix_world.copy()
    world = sprite.matrix_world.copy()
    sprite.parent = arm
    sprite.parent_type = "BONE"
    sprite.parent_bone = "spine"
    sprite.matrix_parent_inverse.identity()
    sprite.matrix_world = world
    bpy.context.view_layer.update()

    # Pose the bone, then convert on the posed frame.
    arm.pose.bones["spine"].rotation_mode = "XYZ"
    arm.pose.bones["spine"].rotation_euler = (0.0, 0.7, 0.0)
    bpy.context.view_layer.update()
    _activate_only(sprite)
    result = bpy.ops.proscenio.convert_element_follow()
    assert "FINISHED" in result

    # Back at rest, the element sits exactly at its authored rest placement.
    arm.pose.bones["spine"].rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    _assert_world_equal(sprite, world_at_rest)


def test_clear_on_a_posed_rig_preserves_the_authored_rest(automesh_fixture):
    arm = _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))
    bpy.context.view_layer.update()
    world_at_rest = sprite.matrix_world.copy()

    _activate_only(sprite)
    bpy.ops.proscenio.parent_sprite_to_bone(bone_name="spine")
    arm.pose.bones["spine"].rotation_mode = "XYZ"
    arm.pose.bones["spine"].rotation_euler = (0.0, 0.7, 0.0)
    bpy.context.view_layer.update()

    result = bpy.ops.proscenio.clear_sprite_bone_parent()
    assert "FINISHED" in result
    arm.pose.bones["spine"].rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    _assert_world_equal(sprite, world_at_rest)


def test_bind_poll_accepts_rigid_mesh_and_rejects_skinned(automesh_fixture):
    _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    rigid = _add_sprite("plank", (0.0, 0.0, 0.0))
    rigid.proscenio.element_type = "mesh"  # rigid mesh: no vertex groups

    _activate_only(rigid)
    assert bpy.ops.proscenio.parent_sprite_to_bone.poll() is True

    skinned = _add_sprite("body", (0.0, 0.0, 0.0))
    skinned.proscenio.element_type = "mesh"
    skinned.vertex_groups.new(name="spine")  # skinned: binds via weights instead

    _activate_only(skinned)
    assert bpy.ops.proscenio.parent_sprite_to_bone.poll() is False


def test_bind_poll_false_when_already_following(automesh_fixture):
    _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))

    _activate_only(sprite)
    bpy.ops.proscenio.parent_sprite_to_bone(bone_name="spine")

    assert bpy.ops.proscenio.parent_sprite_to_bone.poll() is False
    assert bpy.ops.proscenio.clear_sprite_bone_parent.poll() is True
