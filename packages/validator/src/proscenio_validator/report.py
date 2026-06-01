"""Console + JSON output formatting for the validator report."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ._types import LeakRecord, Metrics, Quadrants, SpritePayload, ValidationReport


def _print_leak_quadrants(quadrants: Quadrants) -> None:
    """Print TL/TR/BL/BR breakdown when any quadrant has leaks."""
    if not quadrants.any():
        return
    print(
        f"  leaks_by_quadrant TL={quadrants.TL} TR={quadrants.TR} "
        f"BL={quadrants.BL} BR={quadrants.BR}"
    )


def _print_leak_sample(sample: list[LeakRecord]) -> None:
    """Print the first up-to-5 leak records (pixel coord + world coord)."""
    if not sample:
        return
    print(f"  first {min(5, len(sample))} leak pixels:")
    for rec in sample[:5]:
        print(
            f"    pixel=({rec.pixel_x}, PIL_y={rec.pixel_y_visual_pil}) "
            f"alpha={rec.alpha} world=({rec.world_x}, {rec.world_z})"
        )


def _print_sprite_report(name: str, payload: SpritePayload) -> None:
    """Print the per-sprite block (metrics + leaks + invariant verdicts)."""
    m: Metrics = payload.metrics
    inv = payload.invariants
    status = "PASS" if not inv.failures else "FAIL"
    print(f"\n[{status}] {name}:")
    print(
        f"  verts={m.verts} faces={m.faces} triangles={m.triangles} "
        f"degenerate={m.degenerate_triangles}"
    )
    if m.coverage_pct is not None:
        print(
            f"  coverage={m.coverage_pct:.6f} leaks={m.leak_count} "
            f"hole_bleed={m.hole_bleed_count} mean_area={m.mean_area:.6f}"
        )
        _print_leak_quadrants(m.leak_quadrants)
        _print_leak_sample(m.leak_records_sample)
    for warn in inv.warnings:
        print(f"  WARN: {warn}")
    for fail in inv.failures:
        print(f"  FAIL: {fail}")


def print_report(report: ValidationReport) -> int:
    """Print the full report + return the number of failure-level issues."""
    print()
    print("=" * 60)
    print("AUTOMESH VALIDATION REPORT")
    print("=" * 60)
    for name, payload in report.sprites.items():
        _print_sprite_report(name, payload)
    print("\n" + "=" * 60)
    total_failures = len(report.failures)
    if total_failures:
        print(f"VALIDATION FAILED: {total_failures} issue(s)")
        for fail in report.failures:
            print(f"  - {fail}")
    else:
        print("VALIDATION PASSED")
    print("=" * 60)
    return total_failures


def write_json_report(report: ValidationReport, path: Path | None) -> None:
    """Optionally serialize the report to ``path`` (skip when path is None)."""
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, default=str)
    print(f"\nReport written to {path}")
