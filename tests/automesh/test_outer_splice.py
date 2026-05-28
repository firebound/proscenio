"""Pure tests for outer_splice (AS-AM10)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.outer_splice import (  # noqa: E402
    splice_extend_stroke,
    splice_extend_strokes,
)


def test_stroke_fully_inside_returns_none():
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    stroke = [(2.0, 2.0), (3.0, 3.0), (4.0, 4.0)]
    assert splice_extend_stroke(outer, stroke) is None


def test_stroke_fully_outside_returns_none():
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    stroke = [(20.0, 20.0), (30.0, 30.0)]
    assert splice_extend_stroke(outer, stroke) is None


def test_stroke_too_short_returns_none():
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    assert splice_extend_stroke(outer, [(5.0, 5.0)]) is None


def test_outer_too_short_returns_none():
    outer = [(0.0, 0.0), (10.0, 0.0)]
    stroke = [(5.0, 5.0), (5.0, 15.0), (5.0, 5.0)]
    assert splice_extend_stroke(outer, stroke) is None


def test_extend_outward_then_return_extends_silhouette():
    """Stroke leaves square, draws a bump, returns. Bump verts spliced in."""
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    stroke = [
        (5.0, 5.0),    # inside (start)
        (5.0, 11.0),   # outside (top bump)
        (6.0, 12.0),   # outside (peak)
        (7.0, 11.0),   # outside (top bump)
        (7.0, 5.0),    # inside (return)
    ]
    spliced = splice_extend_stroke(outer, stroke)
    assert spliced is not None
    bump_y = [p[1] for p in spliced]
    # At least one vert should have y > 10 (the bump above the square top)
    assert max(bump_y) > 10.0
    # Original outer count was 4; bump adds 3 outside verts
    assert len(spliced) >= 6


def test_extend_leaves_silhouette_and_never_returns():
    """Stroke exits the silhouette and never re-enters - single-point splice."""
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    stroke = [
        (5.0, 9.0),    # inside (near top edge)
        (5.0, 11.0),   # outside
        (5.0, 14.0),   # outside (further out)
    ]
    spliced = splice_extend_stroke(outer, stroke)
    assert spliced is not None
    bump_y = [p[1] for p in spliced]
    assert max(bump_y) > 10.0


def test_stroke_starting_outside_then_entering():
    """Stroke starts outside the silhouette and enters - outside prefix spliced."""
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    stroke = [
        (5.0, 12.0),   # outside (starts above)
        (5.0, 11.0),   # outside
        (5.0, 5.0),    # inside (re-entry)
    ]
    spliced = splice_extend_stroke(outer, stroke)
    assert spliced is not None
    bump_y = [p[1] for p in spliced]
    assert max(bump_y) > 10.0


def test_splice_multiple_strokes_sequentially_compose():
    """Two independent extend strokes: verify each splice produces a bump.

    Strokes are applied independently (not composed) so order effects don't
    interfere. The sequential-composition function is tested indirectly via
    splice_extend_strokes; here we verify both strokes individually produce
    the expected bump so the composed result contains at least one bump.
    """
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    # Top bump: inside -> above top edge -> inside
    stroke1 = [(5.0, 5.0), (5.0, 11.0), (6.0, 5.0)]
    # Right bump: inside -> right of right edge -> inside (applied to original outer)
    stroke2 = [(5.0, 5.0), (11.0, 5.0), (5.0, 6.0)]

    after_stroke1 = splice_extend_stroke(outer, stroke1)
    assert after_stroke1 is not None
    assert max(p[1] for p in after_stroke1) > 10.0  # top bump landed

    after_stroke2 = splice_extend_stroke(outer, stroke2)
    assert after_stroke2 is not None
    assert max(p[0] for p in after_stroke2) > 10.0  # right bump landed

    # splice_extend_strokes composes sequentially: after stroke1 the outer
    # changes and stroke2 may land differently, but at minimum the top bump
    # from stroke1 must survive in the final result.
    composed = splice_extend_strokes(outer, [stroke1, stroke2])
    assert max(p[1] for p in composed) > 10.0  # top bump present


def test_splice_extend_strokes_skips_fully_inside():
    """Fully-inside strokes in a batch are skipped without affecting the outer."""
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    only_inside = [(2.0, 2.0), (4.0, 4.0)]  # no effect
    result = splice_extend_strokes(outer, [only_inside])
    assert result == outer  # unchanged


def test_splice_extend_strokes_empty_list_returns_original():
    outer = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)]
    result = splice_extend_strokes(outer, [])
    assert result == outer
