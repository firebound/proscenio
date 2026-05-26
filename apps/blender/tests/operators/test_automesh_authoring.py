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


def test_apply_mesh_user_steiners_increase_total_verts(automesh_fixture):
    """User-placed Steiners forwarded through extra_steiners must show up
    as additional verts in the final mesh (PR #59 + #60 + this PR close
    the loop end-to-end).
    """
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
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
    # Baseline: no extra steiners
    baseline = apply_mesh(obj, image, StageOutput(), params, None)
    baseline_verts = baseline["total_verts"]
    # Now add 4 user steiners well inside the hand silhouette (origin area)
    output = StageOutput(user_steiners=[(0.1, 0.1), (-0.1, 0.1), (0.1, -0.1), (-0.1, -0.1)])
    extended = apply_mesh(obj, image, output, params, None)
    # User steiners reached the mesh - vert count grows by ~4 (some may
    # fall outside silhouette or near boundary; the constraint is "more
    # than baseline", not "exactly baseline + 4")
    assert extended["total_verts"] > baseline_verts
