"""Headless: the animation writer resolves an axis-angle rotation channel.

Runs INSIDE Blender via ``run_operator_tests.py`` for real ``mathutils``
(the pure-pytest writer suite stubs mathutils without the axis-angle
``Quaternion(axis, angle)`` constructor). Bake Current Pose now keys an
AXIS_ANGLE bone on ``rotation_axis_angle``; the exporter must read that
channel or the bone exports with no rotation.
"""

from __future__ import annotations

import math


def test_local_rotation_matrix_supports_axis_angle(automesh_fixture: None) -> None:
    from mathutils import Vector
    from proscenio.exporters.godot.writer.animations import _local_rotation_matrix

    # 90 degrees about +Z, stored Blender-style as [angle, x, y, z].
    mat = _local_rotation_matrix({"rotation_axis_angle": {0: math.pi / 2, 1: 0.0, 2: 0.0, 3: 1.0}})
    assert mat is not None, "axis-angle channel was not resolved (exports no rotation)"

    rotated = mat @ Vector((1.0, 0.0, 0.0))  # +X rotated 90deg about +Z -> +Y
    assert abs(rotated.x) < 1e-5
    assert abs(rotated.y - 1.0) < 1e-5
