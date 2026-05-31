"""Per-sprite tolerance bounds + invariant enforcement.

Owns the ``SpriteInvariants`` dataclass + the ``SPRITE_BOUNDS`` table
+ the ``check_invariants`` function the validator's run loop calls
to translate measurement metrics into PASS / WARN / FAIL verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass


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
    boundary (see the weight-paint-automesh spec D2 amendment)."""

    ci_safe: bool = True
    """True when the per-pixel validator finishes inside the CI budget.

    The check is O(source_pixels * triangles); sprites larger than
    ~256x256 source push the runtime past practical CI use and ship
    with ``ci_safe=False``. The ``--ci-only`` CLI flag drops them."""


# Per-sprite tolerance bounds. Sprite-specific because each silhouette
# has different alpha coverage / contour complexity. Bounds were
# calibrated by running the current pipeline manually + adding 30%
# headroom on each side.
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
    # ring: the weight-paint-automesh spec D2 amendment - hole-support smoke target. Hard
    # invariant: leaks=0 (mesh NEVER cuts alpha). Achieved by detecting
    # holes on a 1-cell-DILATED foreground so the mesh-hole boundary
    # sits INSIDE the alpha hole. Flip side: mesh covers a band of
    # transparent hole pixels along the outer hole edge. At downscale
    # =0.25 the band can reach ~50% of small holes (the donut hole is
    # 12 cells wide on the downscaled grid; shrinking by 1 cell on
    # each side leaves a 10-cell cutout). Bumping downscale toward
    # 1.0 or upscaling the hole contour after detection are aspirational successor work
    # work. For now, accept the bleed band as the price of "never
    # cut alpha".
    "ring": SpriteInvariants(
        verts=(150, 400),
        faces=(200, 700),
        min_coverage=0.95,
        max_hole_bleed=1500,
    ),
    # hand: silhouette has tight concave gaps between fingers that the
    # conservative downsample at 0.25 cannot perfectly enclose (each
    # gap is ~4 source pixels = 1 downsampled cell). 96% threshold
    # acknowledges the known limitation; future work (downscale=1.0,
    # adaptive resolution, or morphological closing) can raise to
    # 0.98+.
    "hand": SpriteInvariants(
        verts=(180, 450),
        faces=(300, 800),
        min_coverage=0.96,
        max_hole_bleed=0,
    ),
    # swirl: 512x512 AA sprite with TWO holes (8-shape). NOT ci_safe -
    # per-pixel validator at this source size pushes ~30s+ on CI
    # workers. Use --ci-only to skip; full invocation runs it
    # locally. Vert / face budget doubles vs the 200x200 sprites
    # since the downsampled grid is 128x128. Bleed bound ~2x ring
    # at this source size; measured 5224 against the AA 8-shape
    # fixture, 6500 leaves AA-edge headroom.
    "swirl": SpriteInvariants(
        verts=(400, 1200),
        faces=(700, 2400),
        min_coverage=0.97,
        max_hole_bleed=6500,
        ci_safe=False,
    ),
}


def _check_topology_critical(metrics: dict[str, object]) -> tuple[list[str], list[str]]:
    """Topology-only invariants - run for every sprite (no bounds needed).

    Returns ``(failures, warnings)`` from the four cheapest checks
    (faces > 0, triangles > 0, no degenerate, UVs in [0,1]).
    """
    failures: list[str] = []
    warnings: list[str] = []
    faces = metrics["faces"]
    if not isinstance(faces, int) or faces <= 0:
        failures.append("mesh has 0 faces (CRITICAL - no triangulation)")
    triangles = metrics["triangles"]
    if not isinstance(triangles, int) or triangles <= 0:
        failures.append(
            "mesh has 0 TRIANGLE faces (CRITICAL - non-triangle polygons "
            "only; coverage check cannot run)"
        )
    if metrics["degenerate_triangles"]:
        warnings.append(f"{metrics['degenerate_triangles']} degenerate triangles")
    if metrics["uv_out_of_range_loops"]:
        warnings.append(f"{metrics['uv_out_of_range_loops']} UV loops outside [0,1]")
    return failures, warnings


def _check_count_bounds(
    metrics: dict[str, object], bounds: SpriteInvariants
) -> list[str]:
    """Vert + face count must fall inside the per-sprite [min, max] bands."""
    failures: list[str] = []
    verts = metrics["verts"]
    if isinstance(verts, int):
        lo, hi = bounds.verts
        if not lo <= verts <= hi:
            failures.append(f"vert count {verts} outside expected [{lo}, {hi}]")
    faces = metrics["faces"]
    if isinstance(faces, int):
        lo, hi = bounds.faces
        if not lo <= faces <= hi:
            failures.append(f"face count {faces} outside expected [{lo}, {hi}]")
    return failures


def _check_coverage_and_bleed(
    metrics: dict[str, object], bounds: SpriteInvariants
) -> list[str]:
    """Per-pixel coverage + hole bleed bounds (the alpha invariants)."""
    failures: list[str] = []
    coverage = metrics["coverage_pct"]
    if not isinstance(coverage, float):
        failures.append(
            "coverage measurement unavailable (image missing or no "
            "triangles) - cannot enforce min_coverage invariant"
        )
    elif coverage < bounds.min_coverage:
        failures.append(
            f"coverage {coverage:.4f} below minimum {bounds.min_coverage:.4f} "
            f"({metrics['leak_count']} alpha pixels NOT covered by mesh)"
        )
    bleed = metrics["hole_bleed_count"]
    if isinstance(bleed, int) and bleed > bounds.max_hole_bleed:
        failures.append(
            f"hole bleed {bleed} above maximum {bounds.max_hole_bleed} "
            f"(mesh covers transparent pixels - hole-aware CDT failed)"
        )
    return failures


def check_invariants(
    metrics: dict[str, object],
    bounds: SpriteInvariants | None,
) -> dict[str, object]:
    """Assert critical invariants per sprite + collect warning messages.

    Returns ``{"failures": [...], "warnings": [...]}`` so the caller
    can decide PASS / FAIL based on failures + bubble warnings into
    the report without aborting.

    When ``bounds`` is None (sprite not in SPRITE_BOUNDS), only the
    topology invariants run - no per-sprite tolerance enforcement.
    """
    failures, warnings = _check_topology_critical(metrics)
    if bounds is None:
        return {"failures": failures, "warnings": warnings}
    failures.extend(_check_count_bounds(metrics, bounds))
    failures.extend(_check_coverage_and_bleed(metrics, bounds))
    return {"failures": failures, "warnings": warnings}
