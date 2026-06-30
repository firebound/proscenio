"""Pure-pytest unit tests for the bone-animation writer.

No Blender: the bpy / mathutils stand-ins in ``conftest`` let the writer
module import and run the real projection math (the stub ``Matrix`` /
``Euler`` / ``Quaternion`` mirror Blender's conventions). These tests drive
the pure helpers (fcurve-sample -> typed Animation / Track / Key models)
with hand-built fakes; the bpy-bound entry point is covered by
monkeypatching the action iterator.

The new in-plane projection routes every keyed transform through the
bone's ``rest_basis`` (its 3x3 rest orientation), so the fixtures below
pick two rest frames: an identity (world-aligned) bone and a ``+X``
lateral bone (its head->tail Y axis maps to world +X, ``rest_basis`` =
``Rz(-90deg)``). The expected angles are hand-derived from those frames.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest
from mathutils import Matrix, Vector  # conftest stub

from blender.exporters.godot.writer import animations as anim
from blender.exporters.godot.writer.skeleton import BoneRestLocal

_IDENTITY = Matrix(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
# A +X lateral bone: Rz(-90deg) sends the local Y (head->tail) axis to world +X.
_PLUS_X = Matrix(((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)))

_IDENT_REST = BoneRestLocal(
    position=(0.0, 0.0), rotation=0.0, scale=(1.0, 1.0), rest_basis=_IDENTITY
)
_PLUS_X_REST = BoneRestLocal(
    position=(0.0, 0.0), rotation=0.0, scale=(1.0, 1.0), rest_basis=_PLUS_X
)

# Bone keyed into a typical rest pose, identity orientation, for build_bone_track.
_REST = {
    "arm": BoneRestLocal(
        position=(10.0, 20.0), rotation=0.0, scale=(1.0, 1.0), rest_basis=_IDENTITY
    )
}
# Same rest position but a +X frame, so a keyed local-X rotation reads as a real
# screen swing rather than a degenerate depth-axis spin.
_REST_X = {
    "arm": BoneRestLocal(
        position=(10.0, 20.0), rotation=0.0, scale=(1.0, 1.0), rest_basis=_PLUS_X
    )
}


def _fcurve(
    data_path: str, array_index: int, samples: list[tuple[float, float]]
) -> SimpleNamespace:
    """Fake FCurve whose keyframe_points carry (frame, value) in ``.co``."""
    kps = [SimpleNamespace(co=Vector((frame, value))) for frame, value in samples]
    return SimpleNamespace(
        data_path=data_path, array_index=array_index, keyframe_points=kps
    )


@pytest.mark.parametrize(
    "data_path, expected",
    [
        ('pose.bones["arm"].location', ("arm", "location")),
        ('pose.bones["arm"].rotation_euler', ("arm", "rotation_euler")),
        ('pose.bones["arm"].rotation_quaternion', ("arm", "rotation_quaternion")),
        ('pose.bones["arm"].rotation_axis_angle', ("arm", "rotation_axis_angle")),
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


def test_resolve_location_ignores_depth_axis() -> None:
    # A world-aligned bone: a Blender-Y (depth) delta must not promote position.
    delta = anim._resolve_pose_entry({"location": {1: 5.0}}, 100.0, _IDENT_REST)
    assert delta.position is None


def test_resolve_location_projects_x_and_minus_z() -> None:
    # World-aligned: local X -> screen X, local Z -> screen -Z.
    delta = anim._resolve_pose_entry({"location": {0: 0.1, 2: 0.2}}, 100.0, _IDENT_REST)
    assert delta.position == [10.0, -20.0]


def test_resolve_location_rotates_through_rest_basis() -> None:
    # On a +X bone the local Y (along the bone) maps to world +X, so a local-Y
    # delta lands on screen X, not depth - proving the rest_basis projection.
    delta = anim._resolve_pose_entry({"location": {1: 0.1}}, 100.0, _PLUS_X_REST)
    assert delta.position == [10.0, 0.0]


def test_resolve_location_rotates_delta_into_parent_local_frame() -> None:
    # Godot applies a Bone2D position track in PARENT-local space, and the rest
    # position is emitted parent-local too. So a screen-space delta must be
    # rotated by the parent's world rotation before it is added to the rest.
    # Parent rotated -90deg (a +Z `root`): a local-Z (screen-vertical) delta of
    # 0.15 -> screen (0, -15) -> rotated by +90deg -> (15, 0) on the parent-local
    # X axis. Without the rotation it would stay (0, -15) and read sideways in
    # Godot once the parent's rotation is applied.
    rotated_parent_rest = BoneRestLocal(
        position=(30.0, 0.0),
        rotation=0.0,
        scale=(1.0, 1.0),
        rest_basis=_IDENTITY,
        parent_world_rot=-math.pi / 2,
    )
    delta = anim._resolve_pose_entry(
        {"location": {2: 0.15}}, 100.0, rotated_parent_rest
    )
    assert delta.position == [15.0, 0.0]


def test_resolve_location_unrotated_parent_is_unchanged() -> None:
    # parent_world_rot defaults to 0 (root / world-aligned parent): the screen
    # projection is emitted as-is, so the prior behaviour is preserved.
    delta = anim._resolve_pose_entry({"location": {0: 0.1, 2: 0.2}}, 100.0, _IDENT_REST)
    assert delta.position == [10.0, -20.0]


def test_resolve_euler_below_threshold_is_dropped() -> None:
    delta = anim._resolve_pose_entry({"rotation_euler": {0: 1e-9}}, 1.0, _PLUS_X_REST)
    assert delta.rotation is None


def test_resolve_euler_swings_in_screen_plane() -> None:
    # +X bone, local-X rotation by 0.5 rad -> screen delta -0.5 (hand-derived).
    delta = anim._resolve_pose_entry({"rotation_euler": {0: 0.5}}, 1.0, _PLUS_X_REST)
    assert delta.rotation == pytest.approx(-0.5)


def test_resolve_quaternion_swings_in_screen_plane() -> None:
    # +X bone, quaternion rotation about local X by pi/2 -> screen delta -pi/2.
    half = math.pi / 4
    quat = {0: math.cos(half), 1: math.sin(half)}
    delta = anim._resolve_pose_entry({"rotation_quaternion": quat}, 1.0, _PLUS_X_REST)
    assert delta.rotation == pytest.approx(-math.pi / 2)


def test_resolve_rotation_about_bone_axis_is_dropped() -> None:
    # Rotating about local Y spins the bone around its own head->tail axis: no
    # screen direction change, so no rotation channel.
    delta = anim._resolve_pose_entry({"rotation_euler": {1: 0.7}}, 1.0, _PLUS_X_REST)
    assert delta.rotation is None


def test_resolve_scale_ignores_depth_axis_and_unit_values() -> None:
    # axes 0 and 2 at unit, depth axis (1) ignored -> no scale channel.
    delta = anim._resolve_pose_entry(
        {"scale": {0: 1.0, 1: 5.0, 2: 1.0}}, 1.0, _IDENT_REST
    )
    assert delta.scale is None


def test_resolve_scale_emits_xz() -> None:
    delta = anim._resolve_pose_entry({"scale": {0: 2.0, 2: 0.5}}, 1.0, _IDENT_REST)
    assert delta.scale == [2.0, 0.5]


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
        k.position is None and k.rotation is None and k.scale is None
        for k in track.keys
    )


def test_build_bone_track_sorts_keys_by_time() -> None:
    by_time = {0.5: {"rotation_euler": {0: 0.2}}, 0.0: {"rotation_euler": {0: 0.1}}}
    track = anim.build_bone_track("arm", by_time, ppu=1.0, rest_local=_REST_X)
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
    # _REST_FALLBACK position is (0, 0) with an identity rest_basis -> 0 + 0.1*100 on x.
    assert track.keys[0].position == [10.0, 0.0]


def test_build_bone_track_raises_without_rest_basis_for_animated_bone() -> None:
    # A stale BoneRestLocal (no rest_basis) carrying real transform keys is a
    # contract break: fail fast rather than emit a motionless track.
    stale = {"arm": BoneRestLocal(position=(0.0, 0.0), rotation=0.0, scale=(1.0, 1.0))}
    with pytest.raises(ValueError, match="rest_basis"):
        anim.build_bone_track(
            "arm", {0.0: {"location": {0: 0.1}}}, ppu=100.0, rest_local=stale
        )


def test_build_bone_track_scale_channel() -> None:
    by_time = {0.0: {"scale": {0: 2.0, 2: 0.5}}}
    track = anim.build_bone_track("arm", by_time, ppu=1.0, rest_local=_REST)
    # rest scale (1, 1) multiplied by the delta (2, 0.5).
    assert track.keys[0].scale == [2.0, 0.5]


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


def test_collect_bone_keys_drops_non_deform_bone_tracks() -> None:
    # Belt-and-braces export-leak guard (spec 056, decision 4A): when the deform
    # set is supplied, a control-bone fcurve (here the .IK target) is dropped so
    # it never becomes an animation track, even though it parses fine.
    deform_fc = _fcurve('pose.bones["hand"].location', 0, [(1, 0.1)])
    control_fc = _fcurve('pose.bones["hand.IK"].location', 0, [(1, 0.2)])
    action = SimpleNamespace(fcurves=[deform_fc, control_fc])
    keys = anim.collect_bone_keys(action, fps=10, deform_bones={"hand"})
    assert set(keys) == {"hand"}, "non-deform control bone leaked into bone keys"


def test_collect_bone_keys_without_deform_set_keeps_every_bone() -> None:
    # No deform set supplied -> no filtering (preserves the bare-root-handle path
    # and every existing call site).
    fc = _fcurve('pose.bones["anything.IK"].location', 0, [(1, 0.2)])
    action = SimpleNamespace(fcurves=[fc])
    assert set(anim.collect_bone_keys(action, fps=10)) == {"anything.IK"}


def test_frame_zero_bone_key_clamps_to_nonnegative_time() -> None:
    # A bone keyed at Blender frame 0 yields (0 - 1) / fps, a NEGATIVE time, which
    # trips the Key(time >= 0) constraint and aborts the whole export. The
    # sprite_frame / slot writers already clamp at 0; the bone writer must match.
    fc = _fcurve('pose.bones["arm"].rotation_euler', 0, [(0, 0.5)])
    action = SimpleNamespace(fcurves=[fc])
    by_time = anim.collect_bone_keys(action, fps=10)["arm"]
    track = anim.build_bone_track("arm", by_time, ppu=1.0, rest_local=_REST_X)
    assert [k.time for k in track.keys] == [0.0]


def test_build_animation_returns_none_when_no_bone_keys() -> None:
    action = SimpleNamespace(name="idle", fcurves=[], frame_range=(1.0, 10.0))
    assert anim.build_animation(action, fps=10, ppu=100.0, rest_local=_REST) is None


def test_build_animation_builds_named_looping_animation() -> None:
    fc = _fcurve('pose.bones["arm"].rotation_euler', 0, [(1, 0.0), (11, 0.5)])
    action = SimpleNamespace(name="wave", fcurves=[fc], frame_range=(1.0, 11.0))
    out = anim.build_animation(action, fps=10, ppu=100.0, rest_local=_REST_X)
    assert out is not None
    assert out.name == "wave"
    assert out.loop is True
    assert out.length == pytest.approx(1.0)  # (11 - 1) / 10
    assert [t.target for t in out.tracks] == ["arm"]


def test_build_animation_clamps_zero_length_to_minimum() -> None:
    fc = _fcurve('pose.bones["arm"].rotation_euler', 0, [(1, 0.3)])
    action = SimpleNamespace(name="pose", fcurves=[fc], frame_range=(1.0, 1.0))
    out = anim.build_animation(action, fps=10, ppu=1.0, rest_local=_REST_X)
    assert out is not None
    assert out.length == 0.001


def test_build_animation_drops_non_deform_tracks() -> None:
    # End-to-end through build_animation: only the deform bone's track survives.
    deform_fc = _fcurve('pose.bones["arm"].rotation_euler', 0, [(1, 0.0), (11, 0.4)])
    control_fc = _fcurve('pose.bones["arm.IK"].location', 0, [(1, 0.0), (11, 0.5)])
    action = SimpleNamespace(
        name="wave", fcurves=[deform_fc, control_fc], frame_range=(1.0, 11.0)
    )
    out = anim.build_animation(
        action, fps=10, ppu=100.0, rest_local=_REST_X, deform_bones={"arm"}
    )
    assert out is not None
    assert [t.target for t in out.tracks] == ["arm"]


def test_build_animations_iterates_actions(monkeypatch: pytest.MonkeyPatch) -> None:
    fc = _fcurve('pose.bones["arm"].rotation_euler', 0, [(1, 0.0), (11, 0.4)])
    action = SimpleNamespace(name="a", fcurves=[fc], frame_range=(1.0, 11.0))
    empty = SimpleNamespace(name="empty", fcurves=[], frame_range=(1.0, 2.0))
    monkeypatch.setattr(anim, "iter_actions", lambda: [action, empty])
    out = anim.build_animations(fps=10, ppu=100.0, rest_local=_REST_X)
    assert [a.name for a in out] == ["a"]  # the action with no bone keys is dropped
