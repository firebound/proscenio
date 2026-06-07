"""Pure-pytest coverage for the validator's typed payload bags.

``proscenio_validator._types`` is the one bpy-free corner of the
validator (the rest drives bmesh + operators inside Blender). These
tests instantiate every payload dataclass and exercise the only behavior
they carry, ``Quadrants.any``.
"""

from __future__ import annotations

from proscenio_validator._types import (
    Invariants,
    LeakRecord,
    Metrics,
    Quadrants,
    SpritePayload,
    ValidationReport,
)


def _metrics(quadrants: Quadrants) -> Metrics:
    return Metrics(
        verts=4,
        faces=2,
        triangles=2,
        degenerate_triangles=0,
        mean_area=1.5,
        uv_out_of_range_loops=0,
        coverage_pct=99.0,
        leak_count=quadrants.TL,
        leak_quadrants=quadrants,
        leak_records_sample=[
            LeakRecord(
                pixel_x=1,
                pixel_y_storage=2,
                pixel_y_visual_pil=3,
                alpha=255,
                world_x=0.1,
                world_z=0.2,
                quadrant="TL",
            )
        ],
        hole_bleed_count=0,
    )


def test_quadrants_any_false_when_all_zero() -> None:
    assert Quadrants().any() is False


def test_quadrants_any_true_when_any_nonzero() -> None:
    assert Quadrants(TR=3).any() is True


def test_metrics_and_payload_carry_fields() -> None:
    payload = SpritePayload(
        metrics=_metrics(Quadrants(TL=1)),
        invariants=Invariants(failures=["bad"]),
    )
    assert payload.metrics.verts == 4
    assert payload.metrics.leak_records_sample[0].quadrant == "TL"
    assert payload.invariants.failures == ["bad"]
    assert payload.invariants.warnings == []


def test_validation_report_defaults_are_empty() -> None:
    report = ValidationReport()
    assert report.sprites == {}
    assert report.failures == []
