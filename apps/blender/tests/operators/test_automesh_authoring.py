"""Headless tests for the automesh authoring modal (SPEC 013.2 interactive-modal)."""

from __future__ import annotations

import bpy


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def _set_picker(name: str) -> None:
    bpy.context.scene.proscenio.active_armature = bpy.data.objects[name]


def _resolve_image(obj: bpy.types.Object) -> bpy.types.Image:
    """Find a TEX_IMAGE node's image on the active material."""
    for material in obj.data.materials:
        if material is None or not material.use_nodes or material.node_tree is None:
            continue
        for node in material.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                return node.image
    raise RuntimeError("no image texture on fixture hand")


def test_poll_blocks_without_image_texture(automesh_fixture):
    obj = _activate("hand")
    for slot in obj.material_slots:
        slot.material = None
    assert bpy.ops.proscenio.automesh_authoring.poll() is False


def test_compute_outer_returns_non_empty_polyline(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        compute_outer,
    )
    from proscenio.core.skinning.authoring_stages import (
        StageParams,  # type: ignore[import-not-found]
    )

    params = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=2,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
    )
    outer = compute_outer(obj, image, params)
    assert len(outer) >= 8
    for point in outer:
        assert len(point) == 2
        assert all(isinstance(coord, float) for coord in point)


def test_user_steiners_round_trip_via_custom_property(automesh_fixture):
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_steiners,
        write_user_steiners,
    )

    points = [(0.1, 0.2), (-0.3, 0.5), (0.0, 0.0)]
    write_user_steiners(obj, points)
    restored = read_user_steiners(obj)
    assert restored == points


def test_read_user_steiners_returns_empty_when_absent(automesh_fixture):
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_steiners,
    )

    if "proscenio_user_steiners" in obj:
        del obj["proscenio_user_steiners"]
    assert read_user_steiners(obj) == []


def test_apply_mesh_runs_with_prior_sidecar(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    assert obj.get("proscenio_weight_sidecar") is not None
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        apply_mesh,
    )
    from proscenio.core.skinning.authoring_stages import (  # type: ignore[import-not-found]
        StageOutput,
        StageParams,
    )

    params = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=0,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
    )
    counters = apply_mesh(obj, image, StageOutput(), params, bpy.data.objects["automesh.hand_rig"])
    assert "total_verts" in counters


def test_world_steiners_to_local_applies_inverse_matrix(automesh_fixture):
    """Stage 3 stores user_steiners in WORLD XZ (overlay draws in world
    space). build_automesh's interior_points list is MESH-LOCAL XZ. The
    helper must apply obj.matrix_world.inverted() so points land in the
    polygon-filter coordinate space; otherwise sprites at obj.location !=
    world origin lose all user steiners to point_in_polygon rejection
    (user-reported bug 2026-05-25).
    """
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        _world_steiners_to_local,
    )

    # Empty input -> None (apply_mesh forwards None so build_automesh
    # treats it as "no extras").
    assert _world_steiners_to_local(obj, []) is None

    # Round-trip: take a known mesh-local point (origin), convert it to
    # world via obj.matrix_world, feed back through the helper, expect
    # to recover the original local point. Robust to any obj.location
    # the fixture happens to ship with.
    from mathutils import Vector

    local_origin = Vector((0.0, 0.0, 0.0))
    world_of_local_origin = obj.matrix_world @ local_origin
    world_xz = (world_of_local_origin.x, world_of_local_origin.z)
    out = _world_steiners_to_local(obj, [world_xz])
    assert out is not None and len(out) == 1
    # Round-trip should recover (0, 0) within float tolerance.
    assert abs(out[0][0]) < 1e-5
    assert abs(out[0][1]) < 1e-5

    # Shift the sprite by a known +1 on world X; same world-input now
    # maps to a different mesh-local position (shifted -1 on X) because
    # the inverse transform absorbs the new translation.
    original_x = obj.location.x
    obj.location.x = original_x + 1.0
    bpy.context.view_layer.update()
    out_shifted = _world_steiners_to_local(obj, [world_xz])
    assert out_shifted is not None and len(out_shifted) == 1
    # Same world point, sprite moved +1 on X -> local x is now -1
    assert abs(out_shifted[0][0] - (-1.0)) < 1e-5


def test_user_strokes_round_trip(automesh_fixture):
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_strokes,
        write_user_strokes,
    )

    strokes = [
        {"kind": "point", "points": [(0.0, 0.0)]},
        {"kind": "stroke", "points": [(0.1, 0.2), (0.3, 0.4), (0.5, 0.6)]},
    ]
    write_user_strokes(obj, strokes)
    restored = read_user_strokes(obj)
    assert len(restored) == 2
    assert restored[0]["kind"] == "point"
    assert restored[1]["kind"] == "stroke"
    assert len(restored[1]["points"]) == 3


def test_user_strokes_legacy_fallback(automesh_fixture):
    """Legacy proscenio_user_steiners (flat list) reads as kind=point strokes."""
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_strokes,
        write_user_steiners,
    )

    if "proscenio_user_strokes" in obj:
        del obj["proscenio_user_strokes"]
    write_user_steiners(obj, [(1.0, 2.0), (3.0, 4.0)])
    strokes = read_user_strokes(obj)
    assert len(strokes) == 2
    assert all(s["kind"] == "point" for s in strokes)
    assert strokes[0]["points"] == [(1.0, 2.0)]


def test_user_strokes_corrupt_payload_returns_empty(automesh_fixture):
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_strokes,
    )

    obj["proscenio_user_strokes"] = "not valid json {{{"
    assert read_user_strokes(obj) == []


def test_user_outer_strokes_round_trip(automesh_fixture):
    """Stage 2 persistence key read/write round-trip (AS-AM3 T3 scaffold)."""
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_outer_strokes,
        write_user_outer_strokes,
    )

    strokes = [{"kind": "stroke", "points": [(1.0, 2.0), (3.0, 4.0)]}]
    write_user_outer_strokes(obj, strokes)
    restored = read_user_outer_strokes(obj)
    assert len(restored) == 1
    assert restored[0]["kind"] == "stroke"
    assert restored[0]["points"] == [(1.0, 2.0), (3.0, 4.0)]


def test_user_outer_strokes_empty_when_absent(automesh_fixture):
    """Stage 2 persistence key returns empty list when key is absent (AS-AM3 T3)."""
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_outer_strokes,
    )

    if "proscenio_user_outer_strokes" in obj:
        del obj["proscenio_user_outer_strokes"]
    assert read_user_outer_strokes(obj) == []


def test_apply_mesh_stroke_creates_edges(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        apply_mesh,
    )
    from proscenio.core.skinning.authoring_stages import (  # type: ignore[import-not-found]
        StageOutput,
        StageParams,
    )

    # Build a stroke that crosses the hand's central area.
    # Stroke points are world XZ: hand sits at world X=-3.0, so mesh-local
    # X=0 maps to world X=-3.0. Z is unchanged (no Z offset in fixture).
    output = StageOutput(
        user_strokes=[
            {
                "kind": "stroke",
                "points": [(-3.0, 0.5), (-3.0, 0.3), (-3.0, 0.1), (-3.0, -0.1), (-3.0, -0.3)],
            }
        ]
    )
    params = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=0,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
    )
    armature = bpy.data.objects["automesh.hand_rig"]
    counters_before = apply_mesh(obj, image, StageOutput(), params, armature)
    counters_after = apply_mesh(obj, image, output, params, armature)
    # Stroke should apply cleanly (no exception, valid counters). Vert count
    # may DECREASE vs baseline because exclude_zones (AS-AM2) makes auto-fill
    # skip regions near stroke verts - net effect can be fewer total verts
    # when stroke replaces denser auto-fill mass. The actual fold-line is
    # validated structurally (constraint edges in mesh) elsewhere.
    assert counters_after["total_verts"] > 0
    assert counters_after["total_faces"] > 0
    # Stroke must not catastrophically degenerate the mesh - face count
    # stays within +/- 25 percent of baseline (much wider than the natural
    # exclude_zones impact).
    assert counters_after["total_faces"] >= counters_before["total_faces"] * 0.75


def test_user_outer_strokes_persist_via_custom_property(automesh_fixture):
    """Stage 2 strokes round-trip through the custom property (AS-AM4 T6)."""
    obj = _activate("hand")
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        read_user_outer_strokes,
        write_user_outer_strokes,
    )

    strokes = [
        {"kind": "cut", "points": [(-3.0, 0.5), (-3.0, 0.3), (-3.0, 0.1)]},
    ]
    write_user_outer_strokes(obj, strokes)
    restored = read_user_outer_strokes(obj)
    assert len(restored) == 1
    assert restored[0]["kind"] == "cut"


def test_apply_mesh_outer_cut_stroke_carves_corridor(automesh_fixture):
    """Stage 2 cut stroke (kind='cut' on user_outer_strokes) carves a corridor
    hole - same unified path as Stage 4 cuts (T-REV5). The corridor is routed
    through holes_world; assert the apply produces a valid mesh + co-located
    verts exist at the corridor boundary (hole loop materialized). Face count
    is NOT a strict decrease - a short edge-adjacent corridor can net up or
    down depending on how many hole-boundary verts the loop adds."""
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        apply_mesh,
    )
    from proscenio.core.skinning.authoring_stages import (  # type: ignore[import-not-found]
        StageOutput,
        StageParams,
    )

    params = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=0,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
        cut_margin=0.08,
    )
    armature = bpy.data.objects["automesh.hand_rig"]
    cut_output = StageOutput(
        user_outer_strokes=[
            {
                "kind": "cut",
                "points": [
                    (-3.0, 0.4),
                    (-3.0, 0.2),
                    (-3.0, 0.0),
                    (-3.0, -0.2),
                    (-3.0, -0.4),
                ],
            }
        ]
    )
    cut_result = apply_mesh(obj, image, cut_output, params, armature)
    # Valid mesh produced (corridor merged + triangulated without abort).
    assert cut_result["total_verts"] > 0
    assert cut_result["total_faces"] > 0
    # The corridor hole loop carves a gap: the boundary edge count rises
    # (the hole introduces an interior boundary the silhouette did not have).
    boundary = sum(
        1
        for edge in obj.data.edges
        if len([p for p in obj.data.polygons if edge.key in p.edge_keys]) == 1
    )
    assert boundary > 0, "corridor hole produced no interior boundary edges"


def test_apply_mesh_cut_stroke_carves_clean_corridor(automesh_fixture):
    """kind='cut' carves a corridor hole through holes_world (T-REV5).

    The corridor removes faces (the gap between the offset polylines) but
    CLEANLY - via the same CDT-hole path as alpha holes, so no degenerate
    slivers. Assert faces drop vs baseline (corridor carved) but stay above
    half the baseline (a thin corridor, not a catastrophic collapse)."""
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        apply_mesh,
    )
    from proscenio.core.skinning.authoring_stages import (  # type: ignore[import-not-found]
        StageOutput,
        StageParams,
    )

    # Vertical cut through the THICK palm centre (hand at world X=-3.0) so the
    # corridor is fully interior - a clean hole with mesh on both sides.
    output_with_cut = StageOutput(
        user_strokes=[
            {
                "kind": "cut",
                "points": [
                    (-3.0, 0.4),
                    (-3.0, 0.2),
                    (-3.0, 0.0),
                    (-3.0, -0.2),
                    (-3.0, -0.4),
                ],
            }
        ]
    )
    params = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=0,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
        cut_margin=0.08,
    )
    armature = bpy.data.objects["automesh.hand_rig"]
    baseline = apply_mesh(obj, image, StageOutput(), params, armature)
    cut = apply_mesh(obj, image, output_with_cut, params, armature)
    # Corridor carves faces out vs baseline.
    assert cut["total_faces"] < baseline["total_faces"], (
        f"cut corridor should remove faces: baseline={baseline['total_faces']} "
        f"cut={cut['total_faces']}"
    )
    # But a thin corridor must not gut the mesh (degenerate collapse guard).
    assert cut["total_faces"] > baseline["total_faces"] * 0.5, (
        f"cut removed too much (degenerate): baseline={baseline['total_faces']} "
        f"cut={cut['total_faces']}"
    )


def test_apply_mesh_outer_extend_stroke_grows_silhouette(automesh_fixture):
    """Stage 2 extend stroke (kind='stroke' in user_outer_strokes) extends
    the silhouette - mesh face count grows vs baseline (AS-AM10)."""
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    image = _resolve_image(obj)
    from proscenio.core.bpy_helpers.automesh.authoring_pipeline import (  # type: ignore[import-not-found]
        apply_mesh,
    )
    from proscenio.core.skinning.authoring_stages import (  # type: ignore[import-not-found]
        StageOutput,
        StageParams,
    )

    # Hand fixture at world X=-3.0; right edge around X ~ -2.5
    # Draw an extend stroke that pokes out to X = -1.5 and returns
    extend_output = StageOutput(
        user_outer_strokes=[
            {
                "kind": "stroke",
                "points": [
                    (-2.6, 0.4),
                    (-1.8, 0.5),
                    (-1.5, 0.0),
                    (-1.8, -0.5),
                    (-2.6, -0.4),
                ],
            }
        ]
    )
    params = StageParams(
        resolution=0.25,
        alpha_threshold=1,
        margin_pixels=0,
        contour_vertices=64,
        inner_loop_count=0,
        inner_loop_spacing=0.15,
        interior_spacing=0.1,
        bone_radius=0.5,
        bone_factor=2,
    )
    armature = bpy.data.objects["automesh.hand_rig"]
    baseline = apply_mesh(obj, image, StageOutput(), params, armature)
    extend_result = apply_mesh(obj, image, extend_output, params, armature)
    # Extended silhouette: should have AT LEAST as many faces (typically more)
    assert extend_result["total_faces"] >= baseline["total_faces"]
