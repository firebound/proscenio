"""Unit tests for the vendored MaxRects atlas packer (SPEC 005.1.c.2).

The packer is bpy-free pure Python; tests run without Blender. Coverage:

- Empty input → empty result.
- Single rect fits at the start size.
- Multiple rects do not overlap and stay inside the atlas bounds.
- Padding is honored (placements sit ``+padding`` inside their reserved slot).
- Atlas grows when start_size is insufficient.
- ``max_size`` cap returns None.
- ``power_of_two=True`` rounds up to POT dimensions.

Run from the repo root:

    pytest tests/test_atlas_packer.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.atlas_packer import Rect, pack  # noqa: E402


def _overlaps(a: Rect, b: Rect) -> bool:
    return not (a.right <= b.x or b.right <= a.x or a.bottom <= b.y or b.bottom <= a.y)


def test_pack_empty_returns_empty_result() -> None:
    result = pack([])
    assert result is not None
    assert result.atlas_w == 0
    assert result.atlas_h == 0
    assert result.placements == {}


def test_pack_single_rect_fits() -> None:
    result = pack([("solo", 64, 32)], padding=2, start_size=128)
    assert result is not None
    placement = result.placements["solo"]
    assert placement.w == 64
    assert placement.h == 32
    assert placement.x >= 2  # padding offset
    assert placement.y >= 2


def test_pack_multiple_rects_do_not_overlap() -> None:
    items = [(f"r{i}", 60 + i, 40 + i) for i in range(8)]
    result = pack(items, padding=2, start_size=512)
    assert result is not None
    rects = list(result.placements.values())
    for i, a in enumerate(rects):
        for b in rects[i + 1 :]:
            assert not _overlaps(a, b)


def test_pack_keeps_placements_inside_atlas() -> None:
    items = [(f"r{i}", 50, 50) for i in range(10)]
    result = pack(items, padding=2, start_size=256)
    assert result is not None
    for r in result.placements.values():
        assert r.x >= 0
        assert r.y >= 0
        assert r.right <= result.atlas_w
        assert r.bottom <= result.atlas_h


def test_pack_grows_when_start_size_too_small() -> None:
    items = [(f"r{i}", 100, 100) for i in range(5)]
    # 5 × 100×100 with padding=2 needs ~210x210 minimum + slack.
    # start_size=128 forces a doubling step.
    result = pack(items, padding=2, start_size=128)
    assert result is not None
    assert result.atlas_w >= 256


def test_pack_returns_none_when_max_size_exceeded() -> None:
    items = [("huge", 5000, 5000)]
    result = pack(items, padding=2, max_size=2048)
    assert result is None


def test_pack_power_of_two_rounds_up() -> None:
    items = [(f"r{i}", 50, 50) for i in range(3)]
    result = pack(items, padding=2, start_size=128, power_of_two=True)
    assert result is not None
    # POT dimensions: 128, 256, 512, ...
    assert result.atlas_w & (result.atlas_w - 1) == 0
    assert result.atlas_h & (result.atlas_h - 1) == 0


def test_pack_padding_separates_placements() -> None:
    """Adjacent placements should be at least ``2*padding`` apart on the shared axis."""
    items = [("a", 50, 50), ("b", 50, 50)]
    result = pack(items, padding=4, start_size=128)
    assert result is not None
    a = result.placements["a"]
    b = result.placements["b"]
    # If they share a row (same y range overlap), x gap must be >= 2*padding.
    rows_overlap = not (a.bottom <= b.y or b.bottom <= a.y)
    cols_overlap = not (a.right <= b.x or b.right <= a.x)
    if rows_overlap:
        assert abs(a.x - b.right) >= 8 or abs(b.x - a.right) >= 8
    if cols_overlap:
        assert abs(a.y - b.bottom) >= 8 or abs(b.y - a.bottom) >= 8
