"""Pure-pytest tests for the validator report formatting (console + JSON).

report.py is bpy-free; these drive the print + JSON-serialise paths with
a hand-built ValidationReport (passing, failing, with leak detail).
"""

from __future__ import annotations

import json
from pathlib import Path

from proscenio_validator._types import (
    Invariants,
    LeakRecord,
    Metrics,
    Quadrants,
    SpritePayload,
    ValidationReport,
)
from proscenio_validator.report import print_report, write_json_report


def _payload(*, failures: list[str], with_leaks: bool) -> SpritePayload:
    metrics = Metrics(
        verts=300,
        faces=500,
        triangles=500,
        degenerate_triangles=0,
        mean_area=1.0,
        uv_out_of_range_loops=0,
        coverage_pct=0.97,
        leak_count=2 if with_leaks else 0,
        leak_quadrants=Quadrants(TL=2) if with_leaks else Quadrants(),
        leak_records_sample=(
            [
                LeakRecord(
                    pixel_x=1,
                    pixel_y_storage=2,
                    pixel_y_visual_pil=3,
                    alpha=255,
                    world_x=0.1,
                    world_z=0.2,
                    quadrant="TL",
                )
            ]
            if with_leaks
            else []
        ),
        hole_bleed_count=0,
    )
    return SpritePayload(metrics=metrics, invariants=Invariants(failures=failures, warnings=["minor"]))


def test_print_report_passing_returns_zero() -> None:
    report = ValidationReport(sprites={"blob": _payload(failures=[], with_leaks=False)}, failures=[])
    assert print_report(report) == 0


def test_print_report_failing_returns_failure_count() -> None:
    report = ValidationReport(
        sprites={"blob": _payload(failures=["bad mesh"], with_leaks=True)},
        failures=["bad mesh"],
    )
    assert print_report(report) == 1


def test_write_json_report_writes_valid_json(tmp_path: Path) -> None:
    report = ValidationReport(sprites={"blob": _payload(failures=[], with_leaks=True)}, failures=[])
    out = tmp_path / "nested" / "report.json"
    write_json_report(report, out)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "sprites" in data and "blob" in data["sprites"]


def test_write_json_report_none_is_skipped() -> None:
    write_json_report(ValidationReport(), None)  # no path -> no write, no error
