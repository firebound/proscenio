"""Headless tests for sprite bone-parent (Parent To Bone / Clear Bone Parent).

Runs INSIDE Blender via ``run_operator_tests.py``. A sprite is a rigid
Sprite2D; the only non-slot way to make it follow a single bone is a real
``parent_type == "BONE"`` parent. The operators author that as a keep-transform
bone parent so the sprite does not jump to the bone tail, and clear it back to
an object-less transform preserving world. The exporter already reads the bone
parent via ``resolve_sprite_bone``.
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


def test_parent_to_bone_keeps_world_and_wires_bone(automesh_fixture):
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
    assert sprite.parent is arm
    assert sprite.parent_type == "BONE"
    assert sprite.parent_bone == "spine"
    _assert_world_equal(sprite, world_before)  # no jump to the bone tail
    assert resolve_sprite_bone(sprite) == "spine"  # exporter reads it


def test_clear_bone_parent_keeps_world(automesh_fixture):
    _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    sprite = _add_sprite("torso", (0.3, 0.0, 0.7))

    _activate_only(sprite)
    bpy.ops.proscenio.parent_sprite_to_bone(bone_name="spine")
    bpy.context.view_layer.update()
    world_before = sprite.matrix_world.copy()

    result = bpy.ops.proscenio.clear_sprite_bone_parent()

    assert "FINISHED" in result
    assert sprite.parent is None
    assert sprite.parent_type == "OBJECT"
    assert sprite.parent_bone == ""
    _assert_world_equal(sprite, world_before)


def test_parent_poll_false_for_mesh_element(automesh_fixture):
    _add_armature_with_bone("rig", "spine", (1.0, 0.0, 2.0), (1.0, 1.0, 2.0))
    mesh = _add_sprite("body", (0.0, 0.0, 0.0))
    mesh.proscenio.element_type = "mesh"  # not a sprite

    _activate_only(mesh)
    assert bpy.ops.proscenio.parent_sprite_to_bone.poll() is False
