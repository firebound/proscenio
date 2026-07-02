from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.automesh.stroke_pick import stroke_index_within  # noqa: E402


def _stroke(*points: tuple[float, float]) -> dict[str, list[tuple[float, float]]]:
    return {"points": list(points)}


def test_returns_first_stroke_with_a_vertex_inside_the_pick_disc():
    strokes = [_stroke((0.0, 0.0), (1.0, 0.0)), _stroke((5.0, 5.0))]
    # A point 0.1 from the second vertex of the first stroke; radius^2 = 0.04.
    assert stroke_index_within(strokes, (1.1, 0.0), 0.04) == 0


def test_none_when_every_vertex_is_outside_the_pick_disc():
    strokes = [_stroke((0.0, 0.0)), _stroke((10.0, 10.0))]
    assert stroke_index_within(strokes, (5.0, 5.0), 0.04) is None


def test_returns_the_earliest_matching_stroke_index():
    # Both strokes have a vertex within range; the first one wins.
    strokes = [_stroke((0.0, 0.0)), _stroke((0.05, 0.0))]
    assert stroke_index_within(strokes, (0.0, 0.0), 1.0) == 0


def test_empty_stroke_list_is_none():
    assert stroke_index_within([], (0.0, 0.0), 1.0) is None
