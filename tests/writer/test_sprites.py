"""Pure-pytest unit tests for the sprite / weights writer.

The bpy / mathutils substitutes in conftest let the module import. These
tests drive the bpy-free projection helpers (vertex-group weights, sprite
frame metadata, per-sprite texture resolution) with hand-built fakes. The
mesh-geometry path of ``build_element`` needs a real matrix and stays with
the in-Blender suite.
"""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from blender.exporters.godot.writer import scene_discovery, sprites

# spec 037: the writer reads each per-Object field from its ``proscenio_*``
# Custom Property (idprop) via ``obj.get``. ``_Obj`` is a bpy-Object stand-in
# whose ``.get`` derives the idprop value from a ``proscenio=`` namespace, so
# the test data stays readable while exercising the real idprop read path.
_FIELD_TO_CP = {"element_type": "proscenio_type"}


def _cp_key(field: str) -> str:
    return _FIELD_TO_CP.get(field, f"proscenio_{field}")


class _Obj(SimpleNamespace):
    """A fake bpy Object: attribute access plus idprop-style ``.get``."""

    def get(self, key, default=None):  # noqa: ANN001, ANN201
        pg = getattr(self, "proscenio", None)
        if pg is None:
            return default
        for field, value in vars(pg).items():
            if _cp_key(field) == key:
                return value
        return default


def _vgroup(index: int, name: str) -> SimpleNamespace:
    return SimpleNamespace(index=index, name=name)


def _vec(x: float = 0.0, y: float = 0.0, z: float = 0.0) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, z=z)


class _Mat4:
    """4x4 world-matrix stand-in: row indexing, ``@ Vector`` and ``translation``.

    The conftest mathutils stub is 3x3 (the skeleton math), while the sprite
    rest-transform path reads a 4x4 by ``[row][col]`` and the offset path
    multiplies a point through it - this covers both surfaces.
    """

    def __init__(self, rows: list[list[float]]) -> None:
        self.rows = rows

    def __getitem__(self, index: int) -> list[float]:
        return self.rows[index]

    def __matmul__(self, v: SimpleNamespace) -> SimpleNamespace:
        p = (v.x, v.y, v.z, 1.0)
        out = [sum(self.rows[i][j] * p[j] for j in range(4)) for i in range(3)]
        return SimpleNamespace(x=out[0], y=out[1], z=out[2])

    @property
    def translation(self) -> SimpleNamespace:
        return SimpleNamespace(x=self.rows[0][3], y=self.rows[1][3], z=self.rows[2][3])


def _identity4(tx: float = 0.0, ty: float = 0.0, tz: float = 0.0) -> _Mat4:
    return _Mat4(
        [
            [1.0, 0.0, 0.0, tx],
            [0.0, 1.0, 0.0, ty],
            [0.0, 0.0, 1.0, tz],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )


def test_derive_modulate_none_for_opaque_white() -> None:
    obj = SimpleNamespace(color=(1.0, 1.0, 1.0, 1.0))
    assert sprites._derive_modulate(obj) is None


def test_derive_modulate_returns_the_tint() -> None:
    obj = SimpleNamespace(color=(1.0, 0.5, 0.25, 1.0))
    assert sprites._derive_modulate(obj) == [1.0, 0.5, 0.25, 1.0]


def test_derive_z_index_none_at_the_front_layer() -> None:
    # Draw order 0 is the front layer; the default needs no z_index.
    obj = _Obj(proscenio=SimpleNamespace(y_draw_order=0))
    assert sprites._derive_z_index(obj) is None


def test_derive_z_index_negates_the_draw_order() -> None:
    # A back layer (order 2) maps to z_index -2; Godot draws a lower z_index behind.
    obj = _Obj(proscenio=SimpleNamespace(y_draw_order=2))
    assert sprites._derive_z_index(obj) == -2


def test_derive_z_index_pulls_forward_on_negative_order() -> None:
    # A negative order pulls the plane in front of the front layer (z_index 3).
    obj = _Obj(proscenio=SimpleNamespace(y_draw_order=-3))
    assert sprites._derive_z_index(obj) == 3


def test_derive_z_index_reads_the_custom_property_fallback() -> None:
    # Headless writer path: no PropertyGroup, so the order resolves via the
    # proscenio_y_draw_order Custom Property (order -4 -> z_index 4).
    obj = SimpleNamespace(
        proscenio=None,
        get=lambda key, default=None: {"proscenio_y_draw_order": -4}.get(key, default),
    )
    assert sprites._derive_z_index(obj) == 4


def test_derive_z_index_ignores_the_object_y() -> None:
    # The stored order is the source of truth; the object's Y (only the viewport
    # spacing) is never read, so a stray Y drag cannot shift the exported order.
    obj = _Obj(location=_vec(y=0.123), proscenio=SimpleNamespace(y_draw_order=1))
    assert sprites._derive_z_index(obj) == -1


def test_derive_flips_none_for_positive_scale() -> None:
    obj = SimpleNamespace(scale=_vec(x=1.0, y=1.0, z=1.0))
    assert sprites._derive_flips(obj) == (None, None)


def test_derive_flips_reads_negative_scale_signs() -> None:
    # Quad authored in local XY then stood up 90deg on X: local X is horizontal,
    # local Y is vertical. A mirrored sprite has no per-vertex geometry to carry
    # the flip, so the sign becomes a flag.
    assert sprites._derive_flips(SimpleNamespace(scale=_vec(x=-1.0, y=1.0))) == (
        True,
        None,
    )
    assert sprites._derive_flips(SimpleNamespace(scale=_vec(x=1.0, y=-1.0))) == (
        None,
        True,
    )


def test_build_polygon_topology_dedups_shared_vertices() -> None:
    # A quad split into two triangles sharing the 10->12 edge.
    faces = [[(10, 0), (11, 1), (12, 2)], [(10, 3), (12, 4), (13, 5)]]
    order, polygons = sprites._build_polygon_topology(faces)
    # First-seen order: 10, 11, 12 from face one; 13 new from face two.
    assert [vi for vi, _ in order] == [10, 11, 12, 13]
    # Shared verts 10 and 12 reuse their emitted index in the second face.
    assert polygons == [[0, 1, 2], [0, 2, 3]]


def test_build_polygon_topology_single_face_keeps_loop_order() -> None:
    faces = [[(5, 0), (6, 1), (7, 2), (8, 3)]]
    order, polygons = sprites._build_polygon_topology(faces)
    assert order == [(5, 0), (6, 1), (7, 2), (8, 3)]
    assert polygons == [[0, 1, 2, 3]]


def test_build_polygon_topology_empty_mesh() -> None:
    order, polygons = sprites._build_polygon_topology([])
    assert order == []
    assert polygons == []


def test_resolve_sprite_bone_prefers_bone_parent() -> None:
    obj = SimpleNamespace(parent_type="BONE", parent_bone="forearm.L", vertex_groups=[])
    assert sprites.resolve_sprite_bone(obj) == "forearm.L"


def test_resolve_sprite_bone_falls_back_to_first_vertex_group() -> None:
    obj = SimpleNamespace(
        parent_type="OBJECT", parent_bone="", vertex_groups=[_vgroup(0, "spine")]
    )
    assert sprites.resolve_sprite_bone(obj) == "spine"


def test_resolve_sprite_bone_empty_when_no_bone_or_groups() -> None:
    obj = SimpleNamespace(parent_type="OBJECT", parent_bone="", vertex_groups=[])
    assert sprites.resolve_sprite_bone(obj) == ""


def test_build_sprite_reads_grid_and_bone() -> None:
    obj = _Obj(
        name="face",
        parent_type="BONE",
        parent_bone="head",
        vertex_groups=[],
        proscenio=SimpleNamespace(hframes=2, vframes=3, frame=4, centered=False),
        color=(1.0, 1.0, 1.0, 1.0),
        location=_vec(),
        scale=_vec(1.0, 1.0, 1.0),
        matrix_world=_identity4(),
    )
    sprite = sprites.build_sprite(obj, ppu=100.0)
    assert sprite.type == "sprite"
    assert sprite.name == "face"
    assert sprite.bone == "head"
    assert (sprite.hframes, sprite.vframes, sprite.frame) == (2, 3, 4)
    assert sprite.centered is False
    assert sprite.texture_region is None  # auto mode omits the region
    # The rest position is always carried; identity rotation/scale are omitted.
    assert sprite.position == [0.0, 0.0]
    assert (sprite.rotation, sprite.scale) == (None, None)
    # A default-appearance object emits no appearance fields.
    assert (sprite.modulate, sprite.z_index, sprite.flip_h, sprite.flip_v) == (
        None,
        None,
        None,
        None,
    )


def test_build_sprite_emits_derived_appearance() -> None:
    obj = _Obj(
        name="hat",
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        proscenio=SimpleNamespace(
            hframes=1, vframes=1, frame=0, centered=True, y_draw_order=1
        ),
        color=(1.0, 0.5, 0.25, 1.0),
        location=_vec(y=0.001),  # one step back; the order, not the Y, drives z_index
        scale=_vec(-1.0, 1.0, 1.0),  # mirrored horizontally
        matrix_world=_Mat4(
            [
                [-1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.001],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )
    sprite = sprites.build_sprite(obj, ppu=100.0)
    assert sprite.modulate == [1.0, 0.5, 0.25, 1.0]
    assert sprite.z_index == -1
    assert sprite.flip_h is True
    assert sprite.flip_v is None  # omitted, not False


def _rot_y4(angle: float, tx: float = 0.0, ty: float = 0.0, tz: float = 0.0) -> _Mat4:
    """World matrix rotated by ``angle`` about world Y (the screen rotation)."""
    c, s = math.cos(angle), math.sin(angle)
    return _Mat4(
        [
            [c, 0.0, s, tx],
            [0.0, 1.0, 0.0, ty],
            [-s, 0.0, c, tz],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )


def test_rest_transform_maps_translation_to_godot_screen() -> None:
    # Blender world (x, z) -> Godot (x*ppu, -z*ppu), same mapping as bones.
    obj = _Obj(
        name="fx",
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        proscenio=SimpleNamespace(hframes=1, vframes=1, frame=0, centered=True),
        color=(1.0, 1.0, 1.0, 1.0),
        scale=_vec(1.0, 1.0, 1.0),
        matrix_world=_identity4(tx=5.1, tz=-4.1),
    )
    sprite = sprites.build_sprite(obj, ppu=100.0)
    assert sprite.position == [510.0, 410.0]


def test_rest_transform_reads_in_plane_rotation() -> None:
    # A Blender rotation about world +Y turns the picture plane; the Godot
    # angle equals it (CW positive with Y down).
    obj = _Obj(
        name="fx",
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        proscenio=SimpleNamespace(hframes=1, vframes=1, frame=0, centered=True),
        color=(1.0, 1.0, 1.0, 1.0),
        scale=_vec(1.0, 1.0, 1.0),
        matrix_world=_rot_y4(math.radians(30.0)),
    )
    sprite = sprites.build_sprite(obj, ppu=100.0)
    assert sprite.rotation == pytest.approx(math.radians(30.0), abs=1e-6)
    assert sprite.scale is None  # unit scale still omitted under rotation


def test_rest_transform_scale_covers_both_quad_conventions() -> None:
    # PSD-imported planes are flat in local XZ (vertical = local Z, depth =
    # local Y); a hand-made plane is local XY stood up 90deg on X (vertical =
    # local Y, depth = local Z). The screen projection zeroes the depth axis,
    # so the vertical scale must come out the same either way.
    xz_authored = _Mat4(
        [
            [2.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 3.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    # Stood-up: local Y maps to world +Z (scaled 3), local Z to world -Y.
    xy_stood_up = _Mat4(
        [
            [2.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, -1.0, 0.0],
            [0.0, 3.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    for matrix in (xz_authored, xy_stood_up):
        obj = _Obj(
            name="fx",
            parent_type="OBJECT",
            parent_bone="",
            vertex_groups=[],
            proscenio=SimpleNamespace(hframes=1, vframes=1, frame=0, centered=True),
            color=(1.0, 1.0, 1.0, 1.0),
            scale=_vec(1.0, 1.0, 1.0),
            matrix_world=matrix,
        )
        sprite = sprites.build_sprite(obj, ppu=100.0)
        assert sprite.scale == [2.0, 3.0]
        assert sprite.rotation is None


def test_sprite_off_picture_plane_flat_quads_pass() -> None:
    from blender.core.godot_export_math import sprite_off_picture_plane

    # Both flat conventions face the camera (normal along the depth axis, which
    # projects to zero on screen), so neither reads as tilted.
    xz_authored = _Mat4(
        [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    )
    xy_stood_up = _Mat4(
        [[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0]]
    )
    assert sprite_off_picture_plane(xz_authored) is False
    assert sprite_off_picture_plane(xy_stood_up) is False


def test_sprite_off_picture_plane_ignores_in_plane_rotation() -> None:
    from blender.core.godot_export_math import sprite_off_picture_plane

    # An in-plane rotation spins about the depth axis - the normal stays aligned
    # with the camera, so a keep-transform in-plane bone (fire, badge) is fine.
    assert sprite_off_picture_plane(_rot_y4(math.radians(90.0))) is False


def test_sprite_off_picture_plane_flags_a_tilted_quad() -> None:
    from blender.core.godot_export_math import sprite_off_picture_plane

    # Tilt the quad 45deg about world X: both local Y and Z now project onto
    # the screen, so the face turns partly edge-on - the snap-parent failure.
    c, s = math.cos(math.radians(45.0)), math.sin(math.radians(45.0))
    tilted = _Mat4(
        [[1.0, 0.0, 0.0, 0.0], [0.0, c, -s, 0.0], [0.0, s, c, 0.0], [0.0, 0.0, 0.0, 1.0]]
    )
    assert sprite_off_picture_plane(tilted) is True


def test_rest_transform_mirror_is_not_a_rotation() -> None:
    # A horizontal mirror (negative local X scale) exports flip_h; the angle
    # read cancels the sign so the sprite does not masquerade as rotated 180.
    obj = _Obj(
        name="fx",
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        proscenio=SimpleNamespace(hframes=1, vframes=1, frame=0, centered=True),
        color=(1.0, 1.0, 1.0, 1.0),
        scale=_vec(-2.0, 1.0, 1.0),
        matrix_world=_Mat4(
            [
                [-2.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )
    sprite = sprites.build_sprite(obj, ppu=100.0)
    assert sprite.rotation is None
    assert sprite.scale == [2.0, 1.0]  # magnitude only; the mirror is the flag
    assert sprite.flip_h is True


def test_sprite_offset_pulls_back_into_the_node_frame() -> None:
    # XZ-authored quad whose centre sits at local (0.5, 0, 0.25), object
    # rotated 90deg in the picture plane. Sprite2D.offset applies before the
    # node transform, so the measured gap must come out in the node's local
    # frame - the plain local centre in screen axes - not rotated by the
    # world matrix.
    mesh = SimpleNamespace(
        vertices=[
            SimpleNamespace(co=_vec(0.0, 0.0, 0.0)),
            SimpleNamespace(co=_vec(1.0, 0.0, 0.5)),
        ]
    )
    obj = SimpleNamespace(
        scale=_vec(1.0, 1.0, 1.0),
        data=mesh,
        matrix_world=_rot_y4(math.radians(90.0)),
    )
    offset = sprites._compute_sprite_offset(obj, ppu=100.0)
    assert offset == pytest.approx([50.0, -25.0], abs=1e-4)


def test_sprite_offset_divides_out_the_node_scale() -> None:
    # A scaled sprite carries its scale on the node now; the offset is
    # pre-transform pixels, so the world gap divides the scale back out.
    mesh = SimpleNamespace(
        vertices=[
            SimpleNamespace(co=_vec(0.0, 0.0, 0.0)),
            SimpleNamespace(co=_vec(1.0, 0.0, 0.5)),
        ]
    )
    obj = SimpleNamespace(
        scale=_vec(1.0, 1.0, 1.0),
        data=mesh,
        matrix_world=_Mat4(
            [
                [2.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 4.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        ),
    )
    offset = sprites._compute_sprite_offset(obj, ppu=100.0)
    # Local centre (0.5, 0, 0.25): screen px (50, -25) regardless of the 2x/4x
    # node scale the world matrix carries.
    assert offset == pytest.approx([50.0, -25.0], abs=1e-4)


def test_resolve_sprite_bone_prefers_the_follow_constraint() -> None:
    # Spec 080 D5 precedence: Proscenio Child Of > raw bone parent > first
    # vertex group.
    obj = SimpleNamespace(
        parent_type="BONE",
        parent_bone="stale_parent",
        vertex_groups=[_vgroup(0, "stale_group")],
        constraints=[
            SimpleNamespace(name="Proscenio Sprite Follow", type="CHILD_OF", subtarget="arm")
        ],
    )
    assert sprites.resolve_sprite_bone(obj) == "arm"


def test_resolve_sprite_bone_falls_back_parent_then_vgroup() -> None:
    parented = SimpleNamespace(
        parent_type="BONE", parent_bone="spine", vertex_groups=[_vgroup(0, "g")], constraints=[]
    )
    assert sprites.resolve_sprite_bone(parented) == "spine"
    grouped = SimpleNamespace(
        parent_type="OBJECT", parent_bone="", vertex_groups=[_vgroup(0, "head")], constraints=[]
    )
    assert sprites.resolve_sprite_bone(grouped) == "head"


def test_resolve_sprite_bone_ignores_a_repurposed_constraint_name() -> None:
    # A non-CHILD_OF constraint wearing the Proscenio name is not a binding.
    obj = SimpleNamespace(
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        constraints=[
            SimpleNamespace(name="Proscenio Sprite Follow", type="COPY_LOCATION", subtarget="x")
        ],
    )
    assert sprites.resolve_sprite_bone(obj) == ""


def test_build_sprite_rejects_zero_grid() -> None:
    obj = _Obj(
        name="bad",
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        proscenio=SimpleNamespace(hframes=0, vframes=1, frame=0, centered=True),
    )
    with pytest.raises(RuntimeError, match="hframes"):
        sprites.build_sprite(obj, ppu=100.0)


def test_build_sprite_routes_sprite_kind() -> None:
    obj = _Obj(
        name="spark",
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        proscenio=SimpleNamespace(
            element_type="sprite", hframes=1, vframes=1, frame=0, centered=True
        ),
        color=(1.0, 1.0, 1.0, 1.0),
        location=_vec(),
        scale=_vec(1.0, 1.0, 1.0),
        matrix_world=_identity4(),
    )
    out = sprites.build_element(obj, {}, ppu=100.0)
    assert out.type == "sprite"
    assert out.name == "spark"


def test_build_sprite_rejects_unknown_kind() -> None:
    obj = _Obj(
        name="weird",
        parent_type="OBJECT",
        parent_bone="",
        vertex_groups=[],
        proscenio=SimpleNamespace(element_type="bogus"),
    )
    with pytest.raises(RuntimeError, match="unknown element_type"):
        sprites.build_element(obj, {}, ppu=100.0)


def test_resolve_known_groups_keeps_matching_and_drops_unknown(capsys) -> None:
    obj = SimpleNamespace(
        name="s", vertex_groups=[_vgroup(0, "arm"), _vgroup(1, "ghost")]
    )
    known = sprites._resolve_known_groups(obj, available_bones={"arm"})
    assert known == {0: "arm"}
    # The dropped group must also surface the warning the comment claimed but
    # never asserted: capture the side-effect so a silent regression is caught.
    warned = capsys.readouterr().out
    assert "ghost" in warned and "matching bone" in warned


def test_vertex_bone_weights_sums_known_groups_only() -> None:
    vertex = SimpleNamespace(
        groups=[
            SimpleNamespace(group=0, weight=0.25),
            SimpleNamespace(group=0, weight=0.25),
            SimpleNamespace(group=9, weight=1.0),  # unknown group ignored
        ]
    )
    out = sprites._vertex_bone_weights(vertex, known_groups={0: "arm"})
    assert out == {"arm": 0.5}


def test_build_sprite_weights_empty_without_groups_or_vertices() -> None:
    obj = SimpleNamespace(name="s", vertex_groups=[])
    out = sprites.build_sprite_weights(
        obj, SimpleNamespace(), [], fallback_bone="", available_bones=set()
    )
    assert out == []


def test_build_sprite_weights_distributes_per_vertex() -> None:
    obj = SimpleNamespace(
        name="s", vertex_groups=[_vgroup(0, "arm"), _vgroup(1, "hand")]
    )
    mesh = SimpleNamespace(
        vertices=[
            SimpleNamespace(
                groups=[
                    SimpleNamespace(group=0, weight=3.0),
                    SimpleNamespace(group=1, weight=1.0),
                ]
            ),
        ]
    )
    weights = sprites.build_sprite_weights(
        obj, mesh, [0], fallback_bone="arm", available_bones={"arm", "hand"}
    )
    assert {w.bone: w.values for w in weights} == {"arm": [0.75], "hand": [0.25]}


def test_build_sprite_weights_raises_when_no_group_resolves() -> None:
    obj = SimpleNamespace(name="s", vertex_groups=[_vgroup(0, "ghost")])
    mesh = SimpleNamespace(vertices=[SimpleNamespace(groups=[])])
    with pytest.raises(RuntimeError, match="resolve to bones"):
        sprites.build_sprite_weights(
            obj, mesh, [0], fallback_bone="", available_bones={"arm"}
        )


def test_build_sprite_weights_uses_fallback_for_zero_weight_vertex() -> None:
    obj = SimpleNamespace(name="s", vertex_groups=[_vgroup(0, "arm")])
    mesh = SimpleNamespace(
        vertices=[SimpleNamespace(groups=[])]
    )  # vertex carries no weight
    weights = sprites.build_sprite_weights(
        obj, mesh, [0], fallback_bone="arm", available_bones={"arm"}
    )
    assert {w.bone: w.values for w in weights} == {"arm": [1.0]}


def test_build_sprite_weights_falls_back_when_attach_bone_is_not_a_real_bone() -> None:
    # The fallback (attach) bone need not name a real armature bone; a zero-weight
    # vertex must still get a deterministic real-bone fallback from known_groups,
    # not an all-zero (undeformed) weight column.
    obj = SimpleNamespace(
        name="s", vertex_groups=[_vgroup(0, "ghost"), _vgroup(1, "arm")]
    )
    mesh = SimpleNamespace(
        vertices=[SimpleNamespace(groups=[])]
    )  # vertex carries no weight
    weights = sprites.build_sprite_weights(
        obj, mesh, [0], fallback_bone="ghost", available_bones={"arm"}
    )
    assert weights, "zero-weight vertex got an all-zero weight column (no fallback)"
    assert {w.bone: w.values for w in weights} == {"arm": [1.0]}


@pytest.mark.parametrize(
    "image, expected",
    [
        (SimpleNamespace(filepath="tex/body.png", name="ignored"), "body.png"),
        (SimpleNamespace(filepath="", name="hand"), "hand.png"),
        (SimpleNamespace(filepath="", name="face.png"), "face.png"),
        (SimpleNamespace(filepath="", name=""), None),
    ],
)
def test_image_filename(image: SimpleNamespace, expected: str | None) -> None:
    assert scene_discovery.image_filename(image) == expected


def test_per_sprite_texture_reads_first_image_node() -> None:
    image = SimpleNamespace(filepath="paint/leg.png", name="leg")
    node = SimpleNamespace(type="TEX_IMAGE", image=image)
    tree = SimpleNamespace(nodes=[node])
    mat = SimpleNamespace(use_nodes=True, node_tree=tree)
    obj = SimpleNamespace(data=SimpleNamespace(materials=[mat]))
    assert sprites._per_sprite_texture(obj) == "leg.png"


def test_per_sprite_texture_none_without_image_nodes() -> None:
    obj = SimpleNamespace(data=SimpleNamespace(materials=[]))
    assert sprites._per_sprite_texture(obj) is None
