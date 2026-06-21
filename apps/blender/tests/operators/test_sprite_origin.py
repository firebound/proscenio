"""Headless tests for the PS [origin] -> Sprite2D pivot contract.

Runs INSIDE Blender via ``run_operator_tests.py``. Two halves of the
sprite-origin cleanup:

- Origin is sprite-only: the importer ignores an [origin] on a mesh layer
  (a Polygon2D has no pivot, so it cancels at export) and keeps it on a sprite.
- The round trip: a PS [origin] flows through the importer placement and the
  writer into the Sprite2D offset that puts the node pivot on that origin -
  the wiring that was only code-read before.
"""

from __future__ import annotations

import bpy


def test_mesh_origin_is_ignored(automesh_fixture):
    from proscenio.importers.photoshop.planes import _origin_for_kind

    assert _origin_for_kind((10, 20), "mesh", "torso") is None


def test_sprite_origin_is_kept(automesh_fixture):
    from proscenio.importers.photoshop.planes import _origin_for_kind

    assert _origin_for_kind((10, 20), "sprite", "spark") == (10, 20)


def test_mesh_without_origin_stays_none(automesh_fixture):
    from proscenio.importers.photoshop.planes import _origin_for_kind

    assert _origin_for_kind(None, "mesh", "torso") is None


def _build_sprite_quad(
    name: str,
    size: tuple[float, float],
    geometry_offset: tuple[float, float],
    location: tuple[float, float, float],
) -> bpy.types.Object:
    """Build the quad the importer would stamp at the given placement, as a sprite."""
    width, height = size
    ox, oz = geometry_offset
    half_w, half_h = width / 2.0, height / 2.0
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        [
            (ox - half_w, 0.0, oz - half_h),
            (ox + half_w, 0.0, oz - half_h),
            (ox + half_w, 0.0, oz + half_h),
            (ox - half_w, 0.0, oz + half_h),
        ],
        [],
        [(0, 1, 2, 3)],
    )
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.proscenio.element_type = "sprite"
    bpy.context.view_layer.update()  # refresh matrix_world from the new location
    return obj


def test_origin_round_trips_to_the_sprite_offset(automesh_fixture):
    from proscenio.exporters.godot.writer import sprites
    from proscenio.importers.photoshop.planes import _layer_placement

    # 100x100 doc, ppu 100, no anchor: bbox (40,40)+(20,20) centres on the doc
    # centre (world 0,0); the [origin] sits 20 PSD px below it (PSD y is down).
    placement = _layer_placement(
        position_px=(40, 40),
        size_px=(20, 20),
        doc_size_px=(100, 100),
        pixels_per_unit=100.0,
        z_order=0,
        spacing=0.001,  # z_order 0 -> Y 0 regardless; origin/offset is the subject
        origin_px=(50, 70),
        anchor_px=None,
    )
    obj = _build_sprite_quad(
        "origin_spr", placement.size, placement.geometry_offset, placement.location
    )
    sprite = sprites.build_sprite(obj, ppu=100.0)
    # Origin 20 px below the texture centre (Godot +Y is down) -> the offset
    # lifts the texture 20 px so the node pivot lands on the authored origin.
    assert sprite.offset == [0.0, -20.0]
