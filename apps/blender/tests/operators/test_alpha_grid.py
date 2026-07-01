"""Headless tests for the alpha-grid reader + its per-session cache.

Runs INSIDE Blender via ``run_operator_tests.py``. Covers the MAX-downsample
inner-block helper and the ``(image, size, downscale)`` cache that lets the
authoring modal's threshold/margin drags reuse the grid instead of re-walking
the whole image on every rebuild.
"""

from __future__ import annotations

import bpy


def test_max_alpha_in_block_returns_block_maximum(automesh_fixture) -> None:
    from proscenio.core.bpy_helpers.automesh.bridge import (  # type: ignore[import-not-found]
        _max_alpha_in_block,
    )

    # 2x2 source (source_w=2), RGBA floats row-major. Alpha lives at index 3 of
    # each pixel: pixel (x, y) -> ((y * w + x) * 4 + 3).
    pixels = [0.0] * 16
    pixels[3] = 0.5  # pixel (0, 0) alpha -> int(0.5 * 255) = 127
    pixels[11] = 1.0  # pixel (1, 1) alpha -> 255

    full = _max_alpha_in_block(pixels, 2, 0, 2, 0, 2)
    assert full == 255
    corner = _max_alpha_in_block(pixels, 2, 0, 1, 0, 1)
    assert corner == 127


def test_read_alpha_grid_caches_until_cleared(automesh_fixture) -> None:
    from proscenio.core.bpy_helpers.automesh.bridge import (  # type: ignore[import-not-found]
        clear_alpha_grid_cache,
        read_alpha_grid,
    )

    clear_alpha_grid_cache()
    img = bpy.data.images.new("cache_probe", width=4, height=4, alpha=True)

    first = read_alpha_grid(img, 0.5)
    second = read_alpha_grid(img, 0.5)
    assert first is second, "same (image, downscale) must reuse the cached grid"

    other = read_alpha_grid(img, 1.0)
    assert other is not first, "a different downscale must recompute"

    clear_alpha_grid_cache()
    third = read_alpha_grid(img, 0.5)
    assert third is not first, "clearing the cache must force a recompute"
    assert third == first, "the recomputed grid must be identical in content"
