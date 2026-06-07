"""Pure-pytest unit tests for the bone-animation writer.

No Blender: the bpy / mathutils stand-ins in ``conftest`` let the
writer module import, and these tests drive only the pure projection
helpers (fcurve-sample -> typed Animation / Track / Key models) with
hand-built fakes. The bpy-bound entry point (``build_animations``) is
covered by monkeypatching the action iterator.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
from mathutils import Vector  # conftest stub

from blender.exporters.godot.writer import animations as anim
from blender.exporters.godot.writer.skeleton import BoneRestLocal

_REST = {"arm": BoneRestLocal(position=(10.0, 20.0), rotation=0.0, scale=(1.0, 1.0))}


def _fcurve(data_path: str, array_index: int, samples: list[tuple[float, float]]) -> SimpleNamespace:
    """Fake FCurve whose keyframe_points carry (frame, value) in ``.co``."""
    kps = [SimpleNamespace(co=Vector((frame, value))) for frame, value in samples]
    return SimpleNamespace(data_path=data_path, array_index=array_index, keyframe_points=kps)


# --- _parse_bone_data_path ------------------------------------------------


@pytest.mark.parametrize(
    "data_path, expected",
    [
        ('pose.bones["arm"].location', ("arm", "location")),
        ('pose.bones["arm"].rotation_euler', ("arm", "rotation_euler")),
        ('pose.bones["arm"].rotation_quaternion', ("arm", "rotation_quaternion")),
        ('pose.bones["arm"].scale', ("arm", "scale")),
        ("location", (None, None)),  # missing pose.bones prefix
        ('pose.bones["arm"].foo', (None, None)),  # unknown property
        ('pose.bones["arm"', (None, None)),  # malformed: no closing bracket
    ],
)
def test_parse_bone_data_path(
    data_path: str, expected: tuple[str | None, str | None]
) -> None:
    assert anim._parse_bone_data_path(data_path) == expected


def test_parse_bone_data_path_strips_quotes() -> None:
    bone, prop = anim._parse_bone_data_path("pose.bones['leg.L'].location")
    assert bone == "leg.L"
    assert prop == "location"


# --- _quat_to_screen_angle ------------------------------------------------


def test_quat_identity_is_zero() -> None:
    assert anim._quat_to_screen_angle({0: 1.0}) == 0.0


def test_quat_screen_angle_uses_w_and_y_axes() -> None:
    # q = (w, x, y, z) at indices 0..3; only w (0) and y (2) feed the angle.
    theta = math.pi / 3
    quat = {0: math.cos(theta / 2), 2: math.sin(theta / 2)}
    assert anim._quat_to_screen_angle(quat) == pytest.approx(theta)


# --- _absolute_* ----------------------------------------------------------


def test_absolute_position_adds_delta_to_rest() -> None:
    assert anim._absolute_position((10.0, 20.0), [1.5, -2.5]) == [11.5, 17.5]


def test_absolute_position_none_delta_is_rest() -> None:
    assert anim._absolute_position((10.0, 20.0), None) == [10.0, 20.0]


def test_absolute_rotation_wraps_into_pi_range() -> None:
    # rest + delta reaches 2*pi; wrap_pi pulls it back to 0.
    assert anim._absolute_rotation(math.pi, math.pi) == pytest.approx(0.0)


def test_absolute_scale_multiplies_rest() -> None:
    assert anim._absolute_scale((2.0, 3.0), [2.0, 0.5]) == [4.0, 1.5]


def test_absolute_scale_none_delta_is_rest() -> None:
    assert anim._absolute_scale((2.0, 3.0), None) == [2.0, 3.0]


# --- _resolve_pose_entry --------------------------------------------------


def test_resolve_location_ignores_depth_axis() -> None:
    # axis 1 (Blender Y / depth) must not promote a position channel.
    delta = anim._resolve_pose_entry({"location": {1: 5.0}}, ppu=100.0)
    assert delta.position is None


def test_resolve_location_projects_x_and_minus_z() -> None:
    delta = anim._resolve_pose_entry({"location": {0: 0.1, 2: 0.2}}, ppu=100.0)
    assert delta.position == [10.0, -20.0]


def test_resolve_euler_below_threshold_is_dropped() -> None:
    delta = anim._resolve_pose_entry({"rotation_euler": {1: 1e-9}}, ppu=1.0)
    assert delta.rotation is None


def test_resolve_euler_uses_y_axis() -> None:
    delta = anim._resolve_pose_entry({"rotation_euler": {1: 0.5}}, ppu=1.0)
    assert delta.rotation == pytest.approx(0.5)


def test_resolve_scale_ignores_depth_axis_and_unit_values() -> None:
    # axes 0 and 2 at unit, depth axis (1) ignored -> no scale channel.
    delta = anim._resolve_pose_entry({"scale": {0: 1.0, 1: 5.0, 2: 1.0}}, ppu=1.0)
    assert delta.scale is None


def test_resolve_scale_emits_xz() -> None:
    delta = anim._resolve_pose_entry({"scale": {0: 2.0, 2: 0.5}}, ppu=1.0)
    assert delta.scale == [2.0, 0.5]


def test_resolve_quaternion_rotation() -> None:
    theta = math.pi / 2
    quat = {0: math.cos(theta / 2), 2: math.sin(theta / 2)}
    delta = anim._resolve_pose_entry({"rotation_quaternion": quat}, ppu=1.0)
    assert delta.rotation == pytest.approx(theta)


# --- build_bone_track -----------------------------------------------------


def test_build_bone_track_position_only() -> None:
    by_time = {0.0: {"location": {0: 0.1}}}
    track = anim.build_bone_track("arm", by_time, ppu=100.0, rest_local=_REST)
    assert track.type == "bone_transform"
    assert track.target == "arm"
    assert len(track.keys) == 1
    key = track.keys[0]
    assert key.position == [20.0, 20.0]  # rest.x (10) + 0.1 * 100; rest.y unchanged
    assert key.rotation is None
    assert key.scale is None


def test_build_bone_track_drops_rest_only_channels_but_keeps_timing() -> None:
    # No channel exceeds threshold -> timing-only keys, no transforms.
    by_time: dict[float, dict[str, dict[int, float]]] = {0.0: {}, 0.5: {}}
    track = anim.build_bone_track("arm", by_time, ppu=100.0, rest_local=_REST)
    assert [k.time for k in track.keys] == [0.0, 0.5]
    assert all(
        k.position is None and k.rotation is None and k.scale is None for k in track.keys
    )


def test_build_bone_track_sorts_keys_by_time() -> None:
    by_time = {0.5: {"rotation_euler": {1: 0.2}}, 0.0: {"rotation_euler": {1: 0.1}}}
    track = anim.build_bone_track("arm", by_time, ppu=1.0, rest_local=_REST)
    assert [k.time for k in track.keys] == [0.0, 0.5]


def test_build_bone_track_fills_rest_when_a_time_lacks_the_channel() -> None:
    # time 0 carries position, time 1 does not -> time 1 emits the rest pose.
    by_time = {0.0: {"location": {0: 0.1}}, 1.0: {}}
    track = anim.build_bone_track("arm", by_time, ppu=100.0, rest_local=_REST)
    assert track.keys[0].position == [20.0, 20.0]
    assert track.keys[1].position == [10.0, 20.0]


def test_build_bone_track_uses_rest_fallback_for_unknown_bone() -> None:
    by_time = {0.0: {"location": {0: 0.1}}}
    track = anim.build_bone_track("ghost", by_time, ppu=100.0, rest_local={})
    # _REST_FALLBACK position is (0, 0) -> 0 + 0.1 * 100 on x.
    assert track.keys[0].position == [10.0, 0.0]


def test_build_bone_track_scale_channel() -> None:
    by_time = {0.0: {"scale": {0: 2.0, 2: 0.5}}}
    track = anim.build_bone_track("arm", by_time, ppu=1.0, rest_local=_REST)
    # rest scale (1, 1) multiplied by the delta (2, 0.5).
    assert track.keys[0].scale == [2.0, 0.5]


# --- action_fcurves / collect_bone_keys -----------------------------------


def test_action_fcurves_legacy_path() -> None:
    fc = _fcurve('pose.bones["arm"].location', 0, [(1, 0.0)])
    action = SimpleNamespace(fcurves=[fc])
    assert list(anim.action_fcurves(action)) == [fc]


def test_action_fcurves_layered_path() -> None:
    fc = _fcurve('pose.bones["arm"].location', 0, [(1, 0.0)])
    cb = SimpleNamespace(fcurves=[fc])
    strip = SimpleNamespace(channelbags=[cb])
    layer = SimpleNamespace(strips=[strip])
    action = SimpleNamespace(fcurves=[], layers=[layer])
    assert list(anim.action_fcurves(action)) == [fc]


def test_collect_bone_keys_groups_by_bone_time_prop_axis() -> None:
    fcx = _fcurve('pose.bones["arm"].location', 0, [(1, 0.1)])
    fcz = _fcurve('pose.bones["arm"].location', 2, [(1, 0.2)])
    action = SimpleNamespace(fcurves=[fcx, fcz])
    keys = anim.collect_bone_keys(action, fps=10)
    # frame 1 -> time (1 - 1) / 10 = 0.0
    assert keys == {"arm": {0.0: {"location": {0: 0.1, 2: 0.2}}}}


def test_collect_bone_keys_skips_unparseable_fcurves() -> None:
    fc = _fcurve("nonsense", 0, [(1, 0.0)])
    action = SimpleNamespace(fcurves=[fc])
    assert anim.collect_bone_keys(action, fps=10) == {}


# --- build_animation / build_animations -----------------------------------


def test_build_animation_returns_none_when_no_bone_keys() -> None:
    action = SimpleNamespace(name="idle", fcurves=[], frame_range=(1.0, 10.0))
    assert anim.build_animation(action, fps=10, ppu=100.0, rest_local=_REST) is None


def test_build_animation_builds_named_looping_animation() -> None:
    fc = _fcurve('pose.bones["arm"].rotation_euler', 1, [(1, 0.0), (11, 0.5)])
    action = SimpleNamespace(name="wave", fcurves=[fc], frame_range=(1.0, 11.0))
    out = anim.build_animation(action, fps=10, ppu=100.0, rest_local=_REST)
    assert out is not None
    assert out.name == "wave"
    assert out.loop is True
    assert out.length == pytest.approx(1.0)  # (11 - 1) / 10
    assert [t.target for t in out.tracks] == ["arm"]


def test_build_animation_clamps_zero_length_to_minimum() -> None:
    fc = _fcurve('pose.bones["arm"].rotation_euler', 1, [(1, 0.3)])
    action = SimpleNamespace(name="pose", fcurves=[fc], frame_range=(1.0, 1.0))
    out = anim.build_animation(action, fps=10, ppu=1.0, rest_local=_REST)
    assert out is not None
    assert out.length == 0.001


def test_build_animations_iterates_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    fc = _fcurve('pose.bones["arm"].rotation_euler', 1, [(1, 0.0), (11, 0.4)])
    action = SimpleNamespace(name="a", fcurves=[fc], frame_range=(1.0, 11.0))
    empty = SimpleNamespace(name="empty", fcurves=[], frame_range=(1.0, 2.0))
    monkeypatch.setattr(anim, "iter_actions", lambda: [action, empty])
    out = anim.build_animations(fps=10, ppu=100.0, rest_local=_REST)
    assert [a.name for a in out] == ["a"]  # the action with no bone keys is dropped
