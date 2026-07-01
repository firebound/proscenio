"""Pure-pytest tests for the PSD layer placement math (bpy-free)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.psd.placement import LayerPlacement, layer_placement, origin_for_kind  # noqa: E402


def test_mesh_origin_is_ignored():
    # A Polygon2D has no pivot, so an [origin] on a mesh layer cancels at export:
    # the importer drops it and keeps the bbox-centre placement.
    assert origin_for_kind((10, 20), "mesh", "torso") is None


def test_mesh_without_origin_stays_none():
    assert origin_for_kind(None, "mesh", "torso") is None


def test_sprite_origin_is_kept():
    assert origin_for_kind((10, 20), "sprite", "spark") == (10, 20)


def test_no_origin_no_anchor_centres_on_the_doc_centre():
    # 100x100 doc, ppu 100, bbox (40,40)+(20,20) centres on the doc centre.
    placement = layer_placement(
        position_px=(40, 40),
        size_px=(20, 20),
        doc_size_px=(100, 100),
        pixels_per_unit=100.0,
        z_order=0,
        spacing=0.5,
        origin_px=None,
        anchor_px=None,
    )
    assert placement == LayerPlacement(
        location=(0.0, 0.0, 0.0),
        size=(0.2, 0.2),
        geometry_offset=(0.0, 0.0),
    )


def test_z_order_fans_the_y_gap_by_spacing():
    placement = layer_placement(
        position_px=(40, 40),
        size_px=(20, 20),
        doc_size_px=(100, 100),
        pixels_per_unit=100.0,
        z_order=3,
        spacing=0.5,
        origin_px=None,
        anchor_px=None,
    )
    assert placement.location[1] == 1.5  # 3 * 0.5


def test_origin_bakes_a_geometry_offset_and_moves_the_pivot():
    # Origin 20 PSD px below the texture centre (PSD y is down): the object pivot
    # moves to the origin and the quad geometry offset compensates so the visible
    # texture stays put.
    placement = layer_placement(
        position_px=(40, 40),
        size_px=(20, 20),
        doc_size_px=(100, 100),
        pixels_per_unit=100.0,
        z_order=0,
        spacing=0.001,
        origin_px=(50, 70),
        anchor_px=None,
    )
    # Pivot at origin (50,70): world X 0, world Z = (50 - 70)/100 = -0.20.
    assert placement.location == (0.0, 0.0, -0.2)
    # Geometry offset lifts the quad back to the bbox centre (world Z 0): +0.20.
    assert placement.geometry_offset == (0.0, 0.2)


def test_anchor_re_zeroes_placement_against_the_anchor_point():
    placement = layer_placement(
        position_px=(90, 90),
        size_px=(20, 20),
        doc_size_px=(200, 200),
        pixels_per_unit=100.0,
        z_order=0,
        spacing=0.0,
        origin_px=None,
        anchor_px=(100, 100),
    )
    # bbox centre (100,100) equals the anchor -> world origin.
    assert placement.location == (0.0, 0.0, 0.0)
