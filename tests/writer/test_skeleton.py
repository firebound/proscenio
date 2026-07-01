"""Pure-pytest unit tests for the skeleton writer math.

Imports resolve through the bpy / mathutils stand-ins in ``conftest``.
These tests drive the pure transform helpers and ``build_skeleton``
(pure float math once the bone hierarchy is supplied).
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import bpy  # conftest stub
import pytest
from mathutils import Matrix, Vector  # conftest stub

from blender.core.godot_export_math import (
    godot_world_angle_from_dir,
    world_to_godot_xy,
    wrap_pi,
)
from blender.exporters.godot.writer.skeleton import (
    BoneWorld,
    build_skeleton,
    compute_bone_world_godot,
)

# Identity rest orientation for fake bones; build_skeleton reads
# ``bone.matrix_local.to_3x3()`` for the rest_basis these tests do not assert.
_I = Matrix(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))


@pytest.mark.parametrize(
    "angle, expected",
    [
        (0.0, 0.0),
        (math.pi, math.pi),
        (math.pi + 0.5, -(math.pi - 0.5)),  # wraps just past +pi
        (-math.pi - 0.5, math.pi - 0.5),  # wraps just past -pi
    ],
)
def test_wrap_pi(angle: float, expected: float) -> None:
    assert wrap_pi(angle) == pytest.approx(expected)


def test_world_to_godot_xy_flips_z_into_y() -> None:
    out = world_to_godot_xy(Vector((2.0, 9.0, 3.0)), ppu=10.0)
    assert (out.x, out.y) == (20.0, -30.0)


def test_godot_world_angle_from_dir() -> None:
    assert godot_world_angle_from_dir(Vector((1.0, 0.0, 0.0))) == pytest.approx(0.0)
    assert godot_world_angle_from_dir(Vector((0.0, 0.0, 1.0))) == pytest.approx(
        -math.pi / 2
    )


def _armature_obj(bones: list[SimpleNamespace]) -> SimpleNamespace:
    armature = bpy.types.Armature()
    armature.bones = bones
    return SimpleNamespace(data=armature)


def _bone(
    name: str, parent: object = None, *, use_deform: bool = True
) -> SimpleNamespace:
    """Fake bone carrying the fields build_skeleton reads, deforming by default."""
    return SimpleNamespace(
        name=name, parent=parent, matrix_local=_I, use_deform=use_deform
    )


def test_compute_bone_length_folds_in_armature_scale() -> None:
    # An un-applied armature object scale must scale the emitted bone length:
    # ``bone.length`` is the armature-local rest length and ignores the object
    # scale, so the length is taken from the head->tail vector in *world* space
    # (which carries the scale). Regression for bone-length-armature-scale.
    from mathutils import Vector

    bone = SimpleNamespace(
        name="arm",
        parent=None,
        use_deform=True,
        head_local=Vector((0.0, 0.0, 0.0)),
        tail_local=Vector((1.0, 0.0, 0.0)),  # unit rest length in armature space
    )
    scale_2x = Matrix(((2.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 0.0, 2.0)))
    armature_obj = SimpleNamespace(
        data=_armature_obj([bone]).data, matrix_world=scale_2x
    )
    world = compute_bone_world_godot(armature_obj, ppu=10.0)
    # world head->tail length = |diag(2) @ (1,0,0)| = 2; * ppu(10) = 20.
    assert world["arm"].length == pytest.approx(20.0)


def test_compute_bone_length_unit_scale_matches_rest_length() -> None:
    # With a unit-scale armature the world length equals the armature-local rest
    # length, so existing (unit-scale) fixtures / goldens are unchanged.
    from mathutils import Vector

    bone = SimpleNamespace(
        name="arm",
        parent=None,
        use_deform=True,
        head_local=Vector((0.0, 0.0, 0.0)),
        tail_local=Vector((3.0, 0.0, 0.0)),
    )
    identity = Matrix(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
    armature_obj = SimpleNamespace(
        data=_armature_obj([bone]).data, matrix_world=identity
    )
    world = compute_bone_world_godot(armature_obj, ppu=10.0)
    assert world["arm"].length == pytest.approx(30.0)  # 3 * ppu, scale-free


def test_build_skeleton_root_bone_uses_world_transform() -> None:
    root = SimpleNamespace(name="root", parent=None, matrix_local=_I, use_deform=True)
    world = {"root": BoneWorld(x=5.0, y=7.0, rot=0.25, length=3.0)}
    skeleton, rest = build_skeleton(_armature_obj([root]), world)
    bone = skeleton.bones[0]
    assert bone.name == "root"
    assert bone.parent is None
    assert bone.position == [5.0, 7.0]
    assert bone.rotation == pytest.approx(0.25)
    assert bone.length == 3.0
    assert rest["root"].position == (5.0, 7.0)


def test_build_skeleton_child_is_relative_to_parent() -> None:
    root = SimpleNamespace(name="root", parent=None, matrix_local=_I, use_deform=True)
    child = SimpleNamespace(name="child", parent=root, matrix_local=_I, use_deform=True)
    world = {
        "root": BoneWorld(x=0.0, y=0.0, rot=0.0, length=1.0),
        "child": BoneWorld(x=2.0, y=0.0, rot=0.0, length=1.0),
    }
    skeleton, rest = build_skeleton(_armature_obj([root, child]), world)
    child_bone = next(b for b in skeleton.bones if b.name == "child")
    assert child_bone.parent == "root"
    # parent at origin with no rotation -> child local equals the world delta.
    assert child_bone.position == [2.0, 0.0]
    assert child_bone.rotation == pytest.approx(0.0)
    # The rest record carries the parent name so the animation builder can read
    # the parent's rotation keys for the posed-parent projection (O4).
    assert rest["child"].parent_name == "root"
    assert rest["root"].parent_name is None


def test_build_skeleton_skips_non_deform_control_bones() -> None:
    # The .IK / .pole control bones are non-deforming scaffolding; they must
    # never enter the deform skeleton the Godot export builds for Polygon2D
    # skinning. Regression for the export-leak filter (spec 056, decision 4A).
    deform = _bone("hand", parent=None, use_deform=True)
    control = _bone("hand.IK", parent=None, use_deform=False)
    world = {
        "hand": BoneWorld(x=1.0, y=2.0, rot=0.0, length=1.0),
        "hand.IK": BoneWorld(x=3.0, y=4.0, rot=0.0, length=0.5),
    }
    skeleton, rest = build_skeleton(_armature_obj([deform, control]), world)
    names = [b.name for b in skeleton.bones]
    assert names == ["hand"], "non-deform control bone leaked into skeleton bones[]"
    assert "hand.IK" not in rest, "non-deform control bone leaked into rest_local"


def test_build_skeleton_reparents_child_past_a_filtered_parent() -> None:
    # A deform child whose parent is a non-deform control: dropping the control
    # must not leave a dangling parent reference (Godot import would reject it).
    # The child re-parents to the nearest deform ancestor.
    grandparent = _bone("root", parent=None, use_deform=True)
    control = _bone("root.ctrl", parent=grandparent, use_deform=False)
    child = _bone("hand", parent=control, use_deform=True)
    world = {
        "root": BoneWorld(x=0.0, y=0.0, rot=0.0, length=1.0),
        "root.ctrl": BoneWorld(x=1.0, y=0.0, rot=0.0, length=1.0),
        "hand": BoneWorld(x=2.0, y=0.0, rot=0.0, length=1.0),
    }
    skeleton, rest = build_skeleton(_armature_obj([grandparent, control, child]), world)
    names = [b.name for b in skeleton.bones]
    assert names == ["root", "hand"]
    hand = next(b for b in skeleton.bones if b.name == "hand")
    assert hand.parent == "root", "child kept a dangling parent to the filtered control"
    # parent_name must track the EMITTED parent (the nearest deform ancestor),
    # not the skipped raw Blender parent - the animation builder reads the
    # exported parent's keys, so a stale "root.ctrl" here would miss them.
    assert rest["hand"].parent_name == "root"


def test_build_skeleton_child_of_root_control_becomes_a_root() -> None:
    # No deform ancestor above the filtered parent -> the child becomes a root.
    control = _bone("ctrl", parent=None, use_deform=False)
    deform = _bone("bone", parent=control, use_deform=True)
    world = {
        "ctrl": BoneWorld(x=0.0, y=0.0, rot=0.0, length=1.0),
        "bone": BoneWorld(x=2.0, y=0.0, rot=0.0, length=1.0),
    }
    skeleton, _rest = build_skeleton(_armature_obj([control, deform]), world)
    assert [b.name for b in skeleton.bones] == ["bone"]
    bone = skeleton.bones[0]
    assert bone.parent is None
    # With no deform parent the bone uses its own world transform.
    assert bone.position == [2.0, 0.0]
