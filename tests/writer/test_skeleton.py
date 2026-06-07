"""Pure-pytest unit tests for the skeleton writer math.

Imports resolve through the bpy / mathutils stand-ins in ``conftest``.
These tests drive the pure transform helpers and ``build_skeleton``,
which is pure float math once the bone hierarchy is supplied.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import bpy  # conftest stub
import pytest
from mathutils import Vector  # conftest stub

from blender.exporters.godot.writer.skeleton import (
    BoneWorld,
    build_skeleton,
    godot_world_angle_from_dir,
    world_to_godot_xy,
    wrap_pi,
)


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
    assert godot_world_angle_from_dir(Vector((0.0, 0.0, 1.0))) == pytest.approx(-math.pi / 2)


def _armature_obj(bones: list[SimpleNamespace]) -> SimpleNamespace:
    armature = bpy.types.Armature()
    armature.bones = bones
    return SimpleNamespace(data=armature)


def test_build_skeleton_root_bone_uses_world_transform() -> None:
    root = SimpleNamespace(name="root", parent=None)
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
    root = SimpleNamespace(name="root", parent=None)
    child = SimpleNamespace(name="child", parent=root)
    world = {
        "root": BoneWorld(x=0.0, y=0.0, rot=0.0, length=1.0),
        "child": BoneWorld(x=2.0, y=0.0, rot=0.0, length=1.0),
    }
    skeleton, _rest = build_skeleton(_armature_obj([root, child]), world)
    child_bone = next(b for b in skeleton.bones if b.name == "child")
    assert child_bone.parent == "root"
    # parent at origin with no rotation -> child local equals the world delta.
    assert child_bone.position == [2.0, 0.0]
    assert child_bone.rotation == pytest.approx(0.0)
