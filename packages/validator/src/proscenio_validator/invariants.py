"""Per-sprite tolerance bounds + invariant enforcement.

Owns the ``SpriteInvariants`` dataclass + the ``SPRITE_BOUNDS`` table
+ the ``check_invariants`` function the validator's run loop calls
to translate measurement metrics into PASS / WARN / FAIL verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass

from ._types import Invariants, Metrics


@dataclass(frozen=True)
class SpriteInvariants:
    """Per-sprite tolerance bounds the validator enforces."""

    verts: tuple[int, int]
    """Inclusive [min, max] expected vertex count for the generated mesh."""

    faces: tuple[int, int]
    """Inclusive [min, max] expected face count for the generated mesh."""

    min_coverage: float
    """Required fraction of alpha pixels covered by some triangle (0..1)."""

    max_hole_bleed: int
    """Allowed count of transparent hole pixels covered by mesh.

    Zero for solid sprites; >0 for hole-support fixtures where the
    1-cell safety dilate leaves a small bleed band along each hole
    boundary."""

    ci_safe: bool = True
    """True when the per-pixel validator finishes inside the CI budget.

    The check is O(source_pixels * triangles); sprites larger than
    ~256x256 source push the runtime past practical CI use and ship
    with ``ci_safe=False``. The ``--ci-only`` CLI flag drops them."""


SPRITE_BOUNDS: dict[str, SpriteInvariants] = {
    "blob": SpriteInvariants(
        verts=(200, 400),
        faces=(350, 700),
        min_coverage=0.98,
        max_hole_bleed=0,
    ),
    "lshape": SpriteInvariants(
        verts=(120, 350),
        faces=(200, 600),
        min_coverage=0.96,
        max_hole_bleed=0,
    ),
    # ring: hole-support smoke target.
    "ring": SpriteInvariants(
        verts=(150, 400),
        faces=(200, 700),
        min_coverage=0.95,
        max_hole_bleed=1500,
    ),
    "hand": SpriteInvariants(
        verts=(180, 450),
        faces=(300, 800),
        min_coverage=0.96,
        max_hole_bleed=0,
    ),
    "swirl": SpriteInvariants(
        verts=(400, 1200),
        faces=(700, 2400),
        min_coverage=0.97,
        max_hole_bleed=6500,
        ci_safe=False,
    ),
}


def _check_topology_critical(metrics: Metrics) -> tuple[list[str], list[str]]:
    """Topology-only invariants - run for every sprite (no bounds needed).

    Returns ``(failures, warnings)`` from the four cheapest checks
    (faces > 0, triangles > 0, no degenerate, UVs in [0,1]).
    """
    failures: list[str] = []
    warnings: list[str] = []
    if metrics.faces <= 0:
        failures.append("mesh has 0 faces (CRITICAL - no triangulation)")
    if metrics.triangles <= 0:
        failures.append(
            "mesh has 0 TRIANGLE faces (CRITICAL - non-triangle polygons "
            "only; coverage check cannot run)"
        )
    if metrics.degenerate_triangles:
        warnings.append(f"{metrics.degenerate_triangles} degenerate triangles")
    if metrics.uv_out_of_range_loops:
        warnings.append(f"{metrics.uv_out_of_range_loops} UV loops outside [0,1]")
    return failures, warnings


def _check_count_bounds(metrics: Metrics, bounds: SpriteInvariants) -> list[str]:
    """Vert + face count must fall inside the per-sprite [min, max] bands."""
    failures: list[str] = []
    lo, hi = bounds.verts
    if not lo <= metrics.verts <= hi:
        failures.append(f"vert count {metrics.verts} outside expected [{lo}, {hi}]")
    lo, hi = bounds.faces
    if not lo <= metrics.faces <= hi:
        failures.append(f"face count {metrics.faces} outside expected [{lo}, {hi}]")
    return failures


def _check_coverage_and_bleed(metrics: Metrics, bounds: SpriteInvariants) -> list[str]:
    """Per-pixel coverage + hole bleed bounds (the alpha invariants)."""
    failures: list[str] = []
    if metrics.coverage_pct is None:
        failures.append(
            "coverage measurement unavailable (image missing or no "
            "triangles) - cannot enforce min_coverage invariant"
        )
    elif metrics.coverage_pct < bounds.min_coverage:
        failures.append(
            f"coverage {metrics.coverage_pct:.4f} below minimum "
            f"{bounds.min_coverage:.4f} ({metrics.leak_count} alpha pixels "
            "NOT covered by mesh)"
        )
    if metrics.hole_bleed_count > bounds.max_hole_bleed:
        failures.append(
            f"hole bleed {metrics.hole_bleed_count} above maximum "
            f"{bounds.max_hole_bleed} (mesh covers transparent pixels - "
            "hole-aware CDT failed)"
        )
    return failures


def check_invariants(metrics: Metrics, bounds: SpriteInvariants | None) -> Invariants:
    """Assert critical invariants per sprite + collect warning messages.

    Returns an :class:`Invariants` record so the caller can decide
    PASS / FAIL based on failures + bubble warnings into the report
    without aborting.

    When ``bounds`` is None (sprite not in SPRITE_BOUNDS), only the
    topology invariants run - no per-sprite tolerance enforcement.
    """
    failures, warnings = _check_topology_critical(metrics)
    if bounds is None:
        return Invariants(failures=failures, warnings=warnings)
    failures.extend(_check_count_bounds(metrics, bounds))
    failures.extend(_check_coverage_and_bleed(metrics, bounds))
    return Invariants(failures=failures, warnings=warnings)
