"""Unit tests for UV-bounds → source-pixel-bbox math (SPEC 005.1.c.2.1).

Pure Python helpers powering the sliced atlas packer. Tests cover empty
input, full-cover UVs, partial slice, expand padding, clamp to image
bounds, and the inverse remap used by ``apply_packed_atlas``.

Run from the repo root:

    pytest tests/test_uv_bounds.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.uv_bounds import remap_uv_into_slot, uv_bbox_to_pixels  # noqa: E402


def test_empty_uvs_returns_full_image_fallback() -> None:
    assert uv_bbox_to_pixels([], 256, 128) == (0, 0, 256, 128)


def test_full_cover_uvs_yield_full_image_minus_clamp() -> None:
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    bbox = uv_bbox_to_pixels(uvs, 100, 100, expand=0)
    # Floor of 0.0 = 0, ceil of 1.0 = 100 — the full image.
    assert bbox == (0, 0, 100, 100)


def test_partial_uv_yields_sub_region() -> None:
    """UVs covering [0.25, 0.5] x [0.5, 0.75] of a 200x100 image → 50x25 slice."""
    uvs = [(0.25, 0.5), (0.5, 0.5), (0.5, 0.75), (0.25, 0.75)]
    bbox = uv_bbox_to_pixels(uvs, 200, 100, expand=0)
    x, y, w, h = bbox
    assert x == 50
    assert y == 50
    assert w == 50
    assert h == 25


def test_expand_pads_bbox_clamped_to_image() -> None:
    uvs = [(0.5, 0.5), (0.6, 0.5), (0.6, 0.6), (0.5, 0.6)]
    x, y, w, h = uv_bbox_to_pixels(uvs, 100, 100, expand=2)
    assert x == 50 - 2
    assert y == 50 - 2
    # 0.6 * 100 = 60 → +0.999 + 2 expand = 62 ceil
    assert w == 62 - (50 - 2)
    assert h == 62 - (50 - 2)


def test_expand_clamps_to_image_edges() -> None:
    uvs = [(0.0, 0.0), (1.0, 1.0)]
    bbox = uv_bbox_to_pixels(uvs, 64, 64, expand=10)
    assert bbox == (0, 0, 64, 64)


def test_remap_full_slice_equals_slot_normalized() -> None:
    """When slice == full source, mapping is just (slot.x + u*slot.w) / atlas."""
    new_u, new_v = remap_uv_into_slot(
        u=0.5,
        v=0.25,
        slice_px=(0, 0, 100, 100),
        src_w=100,
        src_h=100,
        slot_px=(200, 300, 100, 100),
        atlas_w=1024,
        atlas_h=512,
    )
    assert new_u == pytest.approx((200 + 50) / 1024)
    assert new_v == pytest.approx((300 + 25) / 512)


def test_remap_partial_slice_offsets_correctly() -> None:
    """UV in source pixel space = slice origin → maps to slot origin in atlas."""
    new_u, new_v = remap_uv_into_slot(
        u=0.25,
        v=0.5,
        slice_px=(50, 50, 50, 25),
        src_w=200,
        src_h=100,
        slot_px=(0, 0, 50, 25),
        atlas_w=512,
        atlas_h=256,
    )
    # UV 0.25 of 200px = 50 px (at slice origin)
    # UV 0.5 of 100px = 50 px (at slice origin)
    # → slot origin in atlas = (0, 0)
    assert new_u == pytest.approx(0.0)
    assert new_v == pytest.approx(0.0)


def test_remap_partial_slice_far_corner() -> None:
    """UV at the slice's far corner maps to the slot's far corner."""
    new_u, new_v = remap_uv_into_slot(
        u=0.5,
        v=0.75,
        slice_px=(50, 50, 50, 25),
        src_w=200,
        src_h=100,
        slot_px=(100, 200, 50, 25),
        atlas_w=512,
        atlas_h=256,
    )
    # UV 0.5 of 200 = 100 px (slice far edge)
    # UV 0.75 of 100 = 75 px (slice far edge)
    # delta from slice origin = (50, 25); slot origin (100, 200)
    # → atlas pixel (150, 225)
    assert new_u == pytest.approx(150 / 512)
    assert new_v == pytest.approx(225 / 256)
