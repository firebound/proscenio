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
