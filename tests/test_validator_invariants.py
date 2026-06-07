"""Pure-pytest tests for the automesh validator invariant rules.

invariants.py is bpy-free (imports only the typed payload bags), so the
PASS/WARN/FAIL rule logic is unit-testable with hand-built Metrics.
"""

from __future__ import annotations

from typing import Any

from proscenio_validator._types import Metrics, Quadrants
from proscenio_validator.invariants import SPRITE_BOUNDS, SpriteInvariants, check_invariants

_BOUNDS = SpriteInvariants(verts=(200, 400), faces=(350, 700), min_coverage=0.98, max_hole_bleed=0)


def _metrics(**overrides: Any) -> Metrics:
    base: dict[str, Any] = {
        "verts": 300,
        "faces": 500,
        "triangles": 500,
        "degenerate_triangles": 0,
        "mean_area": 1.0,
        "uv_out_of_range_loops": 0,
        "coverage_pct": 0.99,
        "leak_count": 0,
        "leak_quadrants": Quadrants(),
        "leak_records_sample": [],
        "hole_bleed_count": 0,
    }
    base.update(overrides)
    return Metrics(**base)


def _failures(**overrides: Any) -> list[str]:
    return check_invariants(_metrics(**overrides), _BOUNDS).failures


def _warnings(**overrides: Any) -> list[str]:
    return check_invariants(_metrics(**overrides), _BOUNDS).warnings


def test_clean_metrics_pass() -> None:
    assert check_invariants(_metrics(), _BOUNDS).failures == []


def test_zero_faces_is_critical() -> None:
    assert any("0 faces" in f for f in _failures(faces=0))


def test_zero_triangles_is_critical() -> None:
    assert any("0 TRIANGLE" in f for f in _failures(triangles=0))


def test_degenerate_triangles_warn() -> None:
    assert any("degenerate" in w for w in _warnings(degenerate_triangles=3))


def test_uv_out_of_range_warn() -> None:
    assert any("UV loops" in w for w in _warnings(uv_out_of_range_loops=2))


def test_vert_count_outside_bounds_fails() -> None:
    assert any("vert count" in f for f in _failures(verts=10))


def test_face_count_outside_bounds_fails() -> None:
    assert any("face count" in f for f in _failures(faces=5000))


def test_missing_coverage_measurement_fails() -> None:
    assert any("coverage measurement unavailable" in f for f in _failures(coverage_pct=None))


def test_coverage_below_minimum_fails() -> None:
    assert any("below minimum" in f for f in _failures(coverage_pct=0.5))


def test_hole_bleed_above_maximum_fails() -> None:
    assert any("hole bleed" in f for f in _failures(hole_bleed_count=100))


def test_no_bounds_runs_topology_only() -> None:
    # Without bounds the count band is not enforced - only topology checks run.
    assert check_invariants(_metrics(verts=99999), None).failures == []


def test_sprite_bounds_table_is_populated() -> None:
    assert "blob" in SPRITE_BOUNDS
    assert SPRITE_BOUNDS["blob"].min_coverage == 0.98
