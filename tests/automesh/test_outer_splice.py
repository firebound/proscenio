"""Pure tests for outer_splice.

The extend splice must grow the silhouette by the artist's bump without
amputating the rest of the contour, regardless of contour winding or where
the polyline seam (index 0) falls. These tests pin the resulting silhouette
by exact area and by the survival of the original corners, so a splice that
lands the bump in the wrong arc (the old nearest-vertex behaviour) fails
instead of passing on a weak "a vert exists above the top" check.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.outer_splice import (  # noqa: E402
    apply_outer_extends,
    splice_extend_stroke,
    splice_extend_strokes,
)

_SQUARE_CCW = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
_SQUARE_CW = [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0)]
# Top bump: inside -> over the top edge -> inside. The resulting silhouette is
# the unit square (area 100) plus a triangular cap, area 103 either winding.
_TOP_BUMP = [(5.0, 5.0), (5.0, 11.0), (6.0, 12.0), (7.0, 11.0), (7.0, 5.0)]
_TOP_BUMP_AREA = 103.0


def _area(pts: list[tuple[float, float]]) -> float:
    """Unsigned shoelace area; winding-independent."""
    n = len(pts)
    acc = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        acc += x0 * y1 - x1 * y0
    return abs(acc) / 2.0


def _orient(
    p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]
) -> float:
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def _proper_cross(a, b, c, d) -> bool:
    """True when open segments AB and CD intersect (incl. collinear overlap)."""
    d1, d2 = _orient(c, d, a), _orient(c, d, b)
    d3, d4 = _orient(a, b, c), _orient(a, b, d)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True

    # Collinear overlap: any endpoint of one strictly inside the other segment.
    def on(p, q, r) -> bool:
        if abs(_orient(p, q, r)) > 1e-9:
            return False
        return min(p[0], q[0]) - 1e-9 <= r[0] <= max(p[0], q[0]) + 1e-9 and (
            min(p[1], q[1]) - 1e-9 <= r[1] <= max(p[1], q[1]) + 1e-9
        )

    return any((on(a, b, c), on(a, b, d), on(c, d, a), on(c, d, b)))


def _is_simple(pts: list[tuple[float, float]]) -> bool:
    """No two non-adjacent edges of the closed polygon may intersect."""
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 1, n):
            if j == i or (j + 1) % n == i or (i + 1) % n == j:
                continue  # adjacent edges share a vertex by design
            c, d = pts[j], pts[(j + 1) % n]
            if _proper_cross(a, b, c, d):
                return False
    return True


def _has(pts: list[tuple[float, float]], target: tuple[float, float]) -> bool:
    return any(abs(x - target[0]) < 1e-6 and abs(y - target[1]) < 1e-6 for x, y in pts)


def test_stroke_fully_inside_returns_none():
    stroke = [(2.0, 2.0), (3.0, 3.0), (4.0, 4.0)]
    assert splice_extend_stroke(_SQUARE_CCW, stroke) is None


def test_stroke_fully_outside_returns_none():
    stroke = [(20.0, 20.0), (30.0, 30.0)]
    assert splice_extend_stroke(_SQUARE_CCW, stroke) is None


def test_stroke_too_short_returns_none():
    assert splice_extend_stroke(_SQUARE_CCW, [(5.0, 5.0)]) is None


def test_outer_too_short_returns_none():
    outer = [(0.0, 0.0), (10.0, 0.0)]
    stroke = [(5.0, 5.0), (5.0, 15.0), (5.0, 5.0)]
    assert splice_extend_stroke(outer, stroke) is None


def test_top_bump_grows_silhouette_into_the_correct_arc():
    """The bump caps the top edge: area grows to exactly 103, every original
    corner survives, the result is a simple polygon, and the new geometry sits
    above the top edge (not spliced into some other side)."""
    spliced = splice_extend_stroke(_SQUARE_CCW, _TOP_BUMP)
    assert spliced is not None
    assert _area(spliced) == _TOP_BUMP_AREA
    assert _is_simple(spliced)
    for corner in _SQUARE_CCW:
        assert _has(spliced, corner)
    above = [(x, y) for x, y in spliced if y > 10.0 + 1e-9]
    assert above and all(5.0 <= x <= 7.0 for x, y in above)


def test_against_winding_stroke_does_not_amputate_the_silhouette():
    """Same bump on a clockwise contour. The old index-comparison splice hit
    the exit<entry branch and threw away most of the silhouette (tiny area);
    the crossing-anchored splice grows to the same 103 regardless of winding."""
    spliced = splice_extend_stroke(_SQUARE_CW, _TOP_BUMP)
    assert spliced is not None
    assert _area(spliced) == _TOP_BUMP_AREA
    assert _is_simple(spliced)
    for corner in _SQUARE_CW:
        assert _has(spliced, corner)


def test_seam_straddling_bump_does_not_amputate_the_silhouette():
    """Bump whose two boundary crossings sit on different edges across the
    polyline seam (index 0). The downward cap adds area 10 (square 100 -> 110)
    and keeps all four corners; the old wrap branch mangled this case."""
    # Bottom edge split at (5, 0): seam (0,0)->(5,0) is edge 4, (5,0)->(10,0)
    # is edge 0, so a bump centred under x=5 crosses edge 4 then edge 0.
    outer = [(5.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    stroke = [(3.0, 5.0), (3.0, -2.0), (5.0, -3.0), (7.0, -2.0), (7.0, 5.0)]
    spliced = splice_extend_stroke(outer, stroke)
    assert spliced is not None
    assert _area(spliced) == 110.0
    assert _is_simple(spliced)
    for corner in [(10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]:
        assert _has(spliced, corner)
    assert min(y for _x, y in spliced) == -3.0


def test_snapped_endpoints_on_the_boundary_are_not_dropped():
    """The pen snaps extend endpoints exactly onto the contour. With the old
    `on-edge = outside` mask both ends classified as outside and the whole
    stroke was dropped; boundary-as-inside keeps the bump."""
    # Both endpoints lie ON the top edge (y == 10), middle pushes above it.
    stroke = [(3.0, 10.0), (5.0, 13.0), (7.0, 10.0)]
    spliced = splice_extend_stroke(_SQUARE_CCW, stroke)
    assert spliced is not None
    assert _area(spliced) > 100.0
    assert _is_simple(spliced)
    assert max(y for _x, y in spliced) > 10.0


def test_extend_leaves_silhouette_and_never_returns():
    """Half gesture: out and not back. Anchored at the real crossing, it still
    produces a spike above the top edge."""
    stroke = [(5.0, 9.0), (5.0, 11.0), (5.0, 14.0)]
    spliced = splice_extend_stroke(_SQUARE_CCW, stroke)
    assert spliced is not None
    assert max(y for _x, y in spliced) > 10.0


def test_stroke_starting_outside_then_entering():
    """Half gesture: starts outside, enters. Outside prefix spliced at the
    crossing."""
    stroke = [(5.0, 12.0), (5.0, 11.0), (5.0, 5.0)]
    spliced = splice_extend_stroke(_SQUARE_CCW, stroke)
    assert spliced is not None
    assert max(y for _x, y in spliced) > 10.0


def test_splice_multiple_strokes_sequentially_compose():
    """Two extend strokes compose; the first bump survives in the final outer."""
    stroke1 = [(5.0, 5.0), (5.0, 11.0), (6.0, 5.0)]  # top
    stroke2 = [(5.0, 5.0), (11.0, 5.0), (5.0, 6.0)]  # right
    composed = splice_extend_strokes(_SQUARE_CCW, [stroke1, stroke2])
    assert max(y for _x, y in composed) > 10.0  # top bump present


def test_splice_extend_strokes_skips_fully_inside():
    only_inside = [(2.0, 2.0), (4.0, 4.0)]
    result = splice_extend_strokes(_SQUARE_CCW, [only_inside])
    assert result == _SQUARE_CCW  # unchanged


def test_splice_extend_strokes_empty_list_returns_original():
    assert splice_extend_strokes(_SQUARE_CCW, []) == _SQUARE_CCW


def test_apply_outer_extends_returns_none_when_every_stroke_is_a_noop():
    """The apply path used an `is` identity check that never tripped (the
    splice always returns a fresh list). apply_outer_extends reports the no-op
    by value so the caller can warn and skip the override."""
    only_inside = [(2.0, 2.0), (4.0, 4.0)]
    assert apply_outer_extends(_SQUARE_CCW, [only_inside]) is None


def test_apply_outer_extends_returns_none_on_empty_list():
    assert apply_outer_extends(_SQUARE_CCW, []) is None


def test_apply_outer_extends_returns_the_changed_outer_on_a_real_extend():
    result = apply_outer_extends(_SQUARE_CCW, [_TOP_BUMP])
    assert result is not None
    assert result != _SQUARE_CCW
    assert _area(result) == _TOP_BUMP_AREA
