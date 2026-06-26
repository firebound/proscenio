"""Headless tests for the spec 069 bone-display + Rig UI operators.

Runs INSIDE Blender via ``run_operator_tests.py``. Exercises the real operators
against a built rig with bone collections, asserting the business effect:

- the per-bone favorite and Relative Parenting toggles flip the real bone state
  (and prove ``Bone.use_relative_parent`` is writable on the data bone, the lock
  the design rests on);
- ``select_bone_collection`` selects exactly the collection's bones;
- ``assign_bone_shape`` sets a generated widget as the pose bone's custom shape;
- ``color_bone_collection`` applies a palette to every bone in the collection.
"""

from __future__ import annotations

import bpy


def _make_rig(name: str) -> bpy.types.Object:
    """A 3-bone rig: root -> spine (connected child) -> tip (disconnected child)."""
    arm_data = bpy.data.armatures.new(name + "_data")
    arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    root = arm_data.edit_bones.new("root")
    root.head = (0.0, 0.0, 0.0)
    root.tail = (0.0, 0.0, 1.0)
    spine = arm_data.edit_bones.new("spine")
    spine.head = (0.0, 0.0, 1.0)
    spine.tail = (0.0, 0.0, 2.0)
    spine.parent = root
    spine.use_connect = True
    tip = arm_data.edit_bones.new("tip")
    tip.head = (0.5, 0.0, 2.0)
    tip.tail = (0.5, 0.0, 3.0)
    tip.parent = spine
    tip.use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def _collection_with(arm: bpy.types.Object, name: str, bone_names: tuple[str, ...]):
    """Create a bone collection and assign the named bones to it."""
    collection = arm.data.collections.new(name)
    for bone_name in bone_names:
        collection.assign(arm.data.bones[bone_name])
    return collection


def _enter_pose(arm: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")


def _bone_selected(arm: bpy.types.Object, name: str) -> bool:
    pose_bone = arm.pose.bones[name]
    return bool(pose_bone.select if hasattr(pose_bone, "select") else pose_bone.bone.select)


# --- per-bone favorite ---------------------------------------------------


def test_toggle_bone_favorite_flips_the_flag(automesh_fixture):
    arm = _make_rig("fav_rig")
    assert arm.data.bones["spine"].proscenio.is_favorite is False

    bpy.ops.proscenio.toggle_bone_favorite(armature_name="fav_rig", bone_name="spine")
    assert arm.data.bones["spine"].proscenio.is_favorite is True

    bpy.ops.proscenio.toggle_bone_favorite(armature_name="fav_rig", bone_name="spine")
    assert arm.data.bones["spine"].proscenio.is_favorite is False


def test_toggle_bone_favorite_cancels_for_missing_bone(automesh_fixture):
    _make_rig("fav_rig2")
    result = bpy.ops.proscenio.toggle_bone_favorite(armature_name="fav_rig2", bone_name="nope")
    assert "CANCELLED" in result


# --- relative parenting toggle (data-bone write access) --------------------


def test_toggle_relative_parent_flips_use_relative_parent(automesh_fixture):
    # Proves Bone.use_relative_parent is writable on the data bone in Object
    # mode - the design's whole premise for making this a one-click toggle.
    arm = _make_rig("rel_rig")
    assert arm.data.bones["tip"].use_relative_parent is False

    bpy.ops.proscenio.toggle_bone_relative_parent(armature_name="rel_rig", bone_name="tip")
    assert arm.data.bones["tip"].use_relative_parent is True

    bpy.ops.proscenio.toggle_bone_relative_parent(armature_name="rel_rig", bone_name="tip")
    assert arm.data.bones["tip"].use_relative_parent is False


# --- Rig UI: select a whole collection ------------------------------------


def test_select_bone_collection_selects_its_bones(automesh_fixture):
    arm = _make_rig("sel_rig")
    _collection_with(arm, "Arm", ("spine", "tip"))
    _enter_pose(arm)
    # Seed a selection outside the collection so the replace semantics are real.
    bpy.ops.proscenio.select_bone_by_name(armature_name="sel_rig", bone_name="root")

    bpy.ops.proscenio.select_bone_collection(armature_name="sel_rig", collection_name="Arm")

    assert _bone_selected(arm, "spine") is True
    assert _bone_selected(arm, "tip") is True
    assert _bone_selected(arm, "root") is False


def test_select_bone_collection_cancels_for_empty_collection(automesh_fixture):
    arm = _make_rig("sel_rig2")
    arm.data.collections.new("Empty")
    _enter_pose(arm)
    result = bpy.ops.proscenio.select_bone_collection(
        armature_name="sel_rig2", collection_name="Empty"
    )
    assert "CANCELLED" in result


# --- custom shape assignment ----------------------------------------------


def test_assign_bone_shape_sets_custom_shape(automesh_fixture):
    arm = _make_rig("shape_rig")
    bpy.context.scene.proscenio.active_armature = arm
    arm.data.bones.active = arm.data.bones["spine"]

    bpy.ops.proscenio.assign_bone_shape(shape="square", scope="ACTIVE")

    widget = arm.pose.bones["spine"].custom_shape
    assert widget is not None
    assert widget.name == "WGT-proscenio-square"


def test_assign_bone_shape_collection_scope_hits_every_bone(automesh_fixture):
    arm = _make_rig("shape_rig2")
    _collection_with(arm, "Arm", ("spine", "tip"))
    bpy.context.scene.proscenio.active_armature = arm

    bpy.ops.proscenio.assign_bone_shape(shape="circle", scope="COLLECTION", collection_name="Arm")

    assert arm.pose.bones["spine"].custom_shape is not None
    assert arm.pose.bones["tip"].custom_shape is not None
    assert arm.pose.bones["root"].custom_shape is None


def test_widget_plane_faces_the_front_camera(automesh_fixture):
    # Regression for the edge-on bug: the rig's bones point +Z (they lie in the
    # X-Z picture plane a 2D Proscenio rig draws into). The widget mesh must end
    # up facing the front-ortho camera (which looks along world Y), i.e. its
    # world-space normal is along Y, not Z. The old X-Z widget geometry put the
    # normal along world Z, so every outline collapsed to a line.
    from mathutils import Vector

    arm = _make_rig("plane_rig")
    bpy.context.scene.proscenio.active_armature = arm
    arm.data.bones.active = arm.data.bones["spine"]
    _enter_pose(arm)
    bpy.ops.proscenio.assign_bone_shape(shape="circle", scope="ACTIVE")

    pose_bone = arm.pose.bones["spine"]
    verts = [Vector(v.co) for v in pose_bone.custom_shape.data.vertices[:3]]
    local_normal = (verts[1] - verts[0]).cross(verts[2] - verts[0]).normalized()
    world_normal = (pose_bone.matrix.to_3x3() @ local_normal).normalized()
    assert abs(world_normal.y) > 0.9, f"widget edge-on to front camera: {tuple(world_normal)}"
    assert abs(world_normal.z) < 0.1


def test_clear_bone_shape_removes_custom_shape(automesh_fixture):
    arm = _make_rig("clear_rig")
    bpy.context.scene.proscenio.active_armature = arm
    arm.data.bones.active = arm.data.bones["spine"]
    bpy.ops.proscenio.assign_bone_shape(shape="square", scope="ACTIVE")
    assert arm.pose.bones["spine"].custom_shape is not None

    bpy.ops.proscenio.assign_bone_shape(clear=True, scope="ACTIVE")
    assert arm.pose.bones["spine"].custom_shape is None


# --- per-collection color ------------------------------------------------


def test_color_bone_collection_applies_palette_to_all(automesh_fixture):
    arm = _make_rig("color_rig")
    _collection_with(arm, "Arm", ("spine", "tip"))

    bpy.ops.proscenio.color_bone_collection(
        armature_name="color_rig", collection_name="Arm", palette="THEME03"
    )

    assert arm.data.bones["spine"].color.palette == "THEME03"
    assert arm.data.bones["tip"].color.palette == "THEME03"
    # A bone outside the collection is untouched.
    assert arm.data.bones["root"].color.palette == "DEFAULT"
    # The op enables the armature's bone-color display so the result is visible.
    assert arm.data.show_bone_colors is True
