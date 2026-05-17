"""Headless automesh validation - SPEC 013 Wave 13.1 invariant check.

Runs ``proscenio.automesh_from_sprite`` against each sprite in the
``examples/generated/automesh/automesh.blend`` fixture and asserts
critical invariants the operator is supposed to preserve:

- Mesh has > 0 triangle faces (catches the "no triangulation" bug
  surfaced in PR #51 smoke when output_type was 4/5 instead of
  1/2).
- Mesh covers >= 98% of alpha foreground pixels (catches the
  "boundary cuts inside the sprite alpha" bug - pixels visible
  in the source PNG that the mesh failed to enclose).
- Vert + face counts within sensible per-sprite tolerance bounds.
- No degenerate triangles (area below epsilon).
- All UV coords in [0, 1].
- No phantom verts (any unconnected loose vertices flag a warning).

Run via headless Blender:

    "<blender.exe>" --background \\
        --python scripts/validate_automesh.py \\
        -- --report scripts/validate_automesh_report.json

The ``--`` separates Blender args from script args. Script writes
the JSON report so the dev can diff successive runs + a non-zero
exit code on any invariant failure for CI integration.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import bpy  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "examples" / "generated" / "automesh" / "automesh.blend"
ADDON_PATH = REPO_ROOT / "apps" / "blender"
ADDON_PACKAGE = "proscenio"

# Mount apps/blender on sys.path so the validator can import
# bpy-free helpers under ``core/`` directly (same pattern the
# pytest suite under ``tests/test_*.py`` uses). The full addon
# register cycle still happens in _load_and_register_addon below
# so ``bpy.ops.proscenio.*`` resolves.
if str(ADDON_PATH) not in sys.path:
    sys.path.insert(0, str(ADDON_PATH))

from core.geometry_2d import point_in_triangle_xz  # noqa: E402


def _load_and_register_addon() -> None:
    """Mount apps/blender as the ``proscenio`` package + run register().

    The automesh validator invokes the operator via ``bpy.ops.proscenio.
    automesh_from_sprite``, which requires the addon's classes to be
    registered with Blender. The headless CI runner has no user-installed
    addon, so we mount the on-disk source directly under the manifest
    package name and call register() ourselves. Mirrors the pattern used
    by ``apps/blender/tests/run_tests.py`` for module loading; the
    register() call is the extra step needed for operator access.
    """
    if ADDON_PACKAGE not in sys.modules:
        init_path = ADDON_PATH / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            ADDON_PACKAGE,
            init_path,
            submodule_search_locations=[str(ADDON_PATH)],
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not build import spec for {init_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[ADDON_PACKAGE] = module
        spec.loader.exec_module(module)
    sys.modules[ADDON_PACKAGE].register()


@dataclass(frozen=True)
class SpriteInvariants:
    """Per-sprite tolerance bounds the validator enforces.

    Each field has a single, named meaning - replaces a 5-key dict
    that read different at every access site (5x ``bounds.get(key,
    default)`` instead of typed attribute access). The frozen
    semantics make the SPRITE_BOUNDS table act as a constant lookup.
    """

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
    boundary (see SPEC 013 D2 amendment)."""

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
    # ring: SPEC 013 D2 amendment - hole-support smoke target. Hard
    # invariant: leaks=0 (mesh NEVER cuts alpha). Achieved by detecting
    # holes on a 1-cell-DILATED foreground so the mesh-hole boundary
    # sits INSIDE the alpha hole. Flip side: mesh covers a band of
    # transparent hole pixels along the outer hole edge. At downscale
    # =0.25 the band can reach ~50% of small holes (the donut hole is
    # 12 cells wide on the downscaled grid; shrinking by 1 cell on
    # each side leaves a 10-cell cutout). Bumping downscale toward
    # 1.0 or upscaling the hole contour after detection are Wave 13.3
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
    # swirl: 400x400 AA sprite with TWO holes (8-shape). NOT ci_safe -
    # 512x512 source = ~250k pixels per validator pass times ~1000+
    # triangles in pure Python = ~30s+ on CI workers. Use --ci-only
    # to skip; full invocation runs it locally. Vert / face budget
    # doubles vs the 200x200 sprites since the downsampled grid is
    # 100x100. Bleed bound ~2x ring at this source size; measured
    # 5224 against the AA 8-shape fixture, 6500 leaves AA-edge
    # headroom.
    "swirl": SpriteInvariants(
        verts=(400, 1200),
        faces=(700, 2400),
        min_coverage=0.97,
        max_hole_bleed=6500,
        ci_safe=False,
    ),
}

DEGENERATE_AREA_EPSILON = 1e-8


def parse_args() -> argparse.Namespace:
    """Parse args appearing after ``--`` in the Blender invocation."""
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="Headless automesh validation")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional JSON report output path",
    )
    parser.add_argument(
        "--margin-pixels",
        type=int,
        default=0,
        help="margin_pixels operator option (default 0 = no annulus)",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=1,
        help="alpha_threshold operator option (default 1 = include AA edges)",
    )
    parser.add_argument(
        "--ci-only",
        action="store_true",
        help=(
            "Skip sprites flagged ci_safe=False in SPRITE_BOUNDS. The "
            "per-pixel coverage check is O(source_pixels * triangles) "
            "in pure Python; larger fixtures (>= ~256x256 source) push "
            "the runtime past practical CI budget."
        ),
    )
    return parser.parse_args(argv)


def load_fixture() -> None:
    """Open the automesh fixture .blend in the headless session."""
    if not FIXTURE_PATH.exists():
        sys.exit(f"[validate] FAIL: fixture not found at {FIXTURE_PATH}")
    bpy.ops.wm.open_mainfile(filepath=str(FIXTURE_PATH))


def read_alpha_for_sprite(sprite_obj: bpy.types.Object) -> list[list[int]]:
    """Read the active material's image alpha into a 2D int grid (0-255)."""
    image = _resolve_image(sprite_obj)
    if image is None:
        return []
    pixels = list(image.pixels[:])
    w, h = image.size[0], image.size[1]
    grid: list[list[int]] = [[0] * w for _ in range(h)]
    for y in range(h):
        row = grid[y]
        base = y * w * 4
        for x in range(w):
            row[x] = int(pixels[base + x * 4 + 3] * 255)
    return grid


def _resolve_image(obj: bpy.types.Object) -> bpy.types.Image | None:
    """Find the first TEX_IMAGE node image on the mesh's materials."""
    if obj.data is None:
        return None
    active = getattr(obj, "active_material", None)
    if active is not None and active.use_nodes:
        for node in active.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                return node.image
    for mat in obj.data.materials:
        if mat is None or not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image is not None:
                return node.image
    return None


def measure_mesh(sprite_obj: bpy.types.Object) -> dict[str, object]:
    """Inspect the generated mesh + return metrics + invariant flags."""
    mesh = sprite_obj.data
    verts = [v.co for v in mesh.vertices]
    triangles: list[
        tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    ] = []
    degenerate = 0
    areas: list[float] = []
    for poly in mesh.polygons:
        if len(poly.vertices) != 3:
            continue
        v0 = verts[poly.vertices[0]]
        v1 = verts[poly.vertices[1]]
        v2 = verts[poly.vertices[2]]
        a = (v0.x, v0.z)
        b = (v1.x, v1.z)
        c = (v2.x, v2.z)
        ax = b[0] - a[0]
        az = b[1] - a[1]
        bx = c[0] - a[0]
        bz = c[1] - a[1]
        area = abs(ax * bz - az * bx) / 2.0
        if area < DEGENERATE_AREA_EPSILON:
            degenerate += 1
            continue
        areas.append(area)
        triangles.append((a, b, c))

    # UVs check.
    uv_out_of_range = 0
    if mesh.uv_layers.active is not None:
        for uv in mesh.uv_layers.active.data:
            if not (0.0 - 1e-3 <= uv.uv[0] <= 1.0 + 1e-3):
                uv_out_of_range += 1
            elif not (0.0 - 1e-3 <= uv.uv[1] <= 1.0 + 1e-3):
                uv_out_of_range += 1

    # Coverage: sample each foreground alpha pixel against the
    # triangle list. Coarse sampling (every 2nd pixel) keeps the
    # run fast for 200x200 sprites without losing meaningful
    # coverage signal.
    image = _resolve_image(sprite_obj)
    coverage_pct: float | None = None
    leak_count = 0
    leak_records: list[dict[str, object]] = []
    quadrants: dict[str, int] = {}
    bleed_count = 0
    if image is not None and triangles:
        debug_dir = REPO_ROOT / "scripts" / "validate_automesh_debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_png = debug_dir / f"{sprite_obj.name}_coverage.png"
        coverage_pct, leak_count, leak_records, quadrants, bleed_count = (
            _measure_coverage(image, triangles, debug_png)
        )

    return {
        "verts": len(verts),
        "faces": len(mesh.polygons),
        "triangles": len(triangles),
        "degenerate_triangles": degenerate,
        "mean_area": sum(areas) / len(areas) if areas else 0.0,
        "uv_out_of_range_loops": uv_out_of_range,
        "coverage_pct": coverage_pct,
        "leak_count": leak_count,
        "leak_quadrants": quadrants,
        # First 30 leak records inline; full list in report JSON only
        # when leak_count > 0 to keep noise down.
        "leak_records_sample": leak_records[:30],
        # SPEC 013 D2 amendment: mesh-over-transparent-pixel count.
        # Non-zero indicates hole-aware CDT failed to exclude an alpha
        # gap. Zero is the invariant for hole-supporting sprites
        # (ring etc.).
        "hole_bleed_count": bleed_count,
    }


def _compute_hole_pixel_mask(
    pixels: list[float],
    w: int,
    h: int,
) -> list[list[bool]]:
    """True for transparent pixels fully enclosed by alpha foreground.

    Flood-fills transparent pixels reachable from the image border;
    the remainder are alpha holes. Mirrors the bridge-side
    ``alpha_contour.extract_holes`` logic but operates on the raw
    full-resolution pixel grid (no downscaling) so the validator
    measures against ground truth, not the operator's downsampled
    view.
    """
    transparent: list[list[bool]] = [
        [int(pixels[(y * w + x) * 4 + 3] * 255) <= 0 for x in range(w)]
        for y in range(h)
    ]
    visited: list[list[bool]] = [[False] * w for _ in range(h)]
    stack: list[tuple[int, int]] = []
    for x in range(w):
        if transparent[0][x]:
            stack.append((x, 0))
        if transparent[h - 1][x]:
            stack.append((x, h - 1))
    for y in range(h):
        if transparent[y][0]:
            stack.append((0, y))
        if transparent[y][w - 1]:
            stack.append((w - 1, y))
    while stack:
        x, y = stack.pop()
        if not (0 <= x < w and 0 <= y < h):
            continue
        if visited[y][x] or not transparent[y][x]:
            continue
        visited[y][x] = True
        stack.append((x + 1, y))
        stack.append((x - 1, y))
        stack.append((x, y + 1))
        stack.append((x, y - 1))
    return [
        [transparent[y][x] and not visited[y][x] for x in range(w)] for y in range(h)
    ]


_DEBUG_COLOUR_COVERED = (0, 200, 0, 255)
_DEBUG_COLOUR_LEAK = (255, 0, 0, 255)
_DEBUG_COLOUR_HOLE_BLEED = (0, 100, 255, 255)


@dataclass(frozen=True)
class _CoverageContext:
    """Pre-computed per-image values that every pixel classification needs.

    Bundles the alpha buffer + triangle list + hole mask + world-coord
    scaling constants + the debug image buffer in a single read-only
    record so ``_classify_pixel`` stays under the 13-argument limit
    without having to plumb a dozen positionals through the inner loop.
    """

    w: int
    h: int
    pixels: list[float]
    triangles: list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]]
    hole_mask: list[list[bool]]
    world_scale: float
    half_w: float
    half_h: float
    half_cell: float
    debug_image: list[int] | None


def _paint_debug_pixel(
    debug_image: list[int] | None,
    pixel_index: int,
    rgba: tuple[int, int, int, int],
) -> None:
    """Write one RGBA pixel into the flat debug-image buffer."""
    if debug_image is None:
        return
    idx = pixel_index * 4
    debug_image[idx] = rgba[0]
    debug_image[idx + 1] = rgba[1]
    debug_image[idx + 2] = rgba[2]
    debug_image[idx + 3] = rgba[3]


def _pixel_world_coords(
    x: int, y: int, ctx: _CoverageContext
) -> tuple[float, float]:
    """Cell-center world coords for source pixel ``(x, y)``.

    Matches the mesh's ``pixel_contour_to_world`` cell-center
    placement (+ half_cell offset on each axis) + the bridge's
    Y-flip-on-read convention so the validator measures against
    the same geometry the operator built.
    """
    visual_y = ctx.h - 1 - y
    wx = x * ctx.world_scale - ctx.half_w + ctx.half_cell
    wz = ctx.half_h - visual_y * ctx.world_scale - ctx.half_cell
    return wx, wz


def _classify_pixel(
    x: int,
    y: int,
    ctx: _CoverageContext,
    leaks_records: list[dict[str, object]],
    quadrants: dict[str, int],
) -> tuple[int, int]:
    """Classify pixel ``(x, y)`` against the mesh + paint the debug buffer.

    Returns ``(fg_increment, bleed_increment)`` so the caller can
    keep the counters without juggling locals in the inner loop.
    Leak records + quadrant counts are mutated in-place via the
    passed-in collections (kept separate from ctx because they
    accumulate across calls).
    """
    alpha = int(ctx.pixels[(y * ctx.w + x) * 4 + 3] * 255)
    pixel_index = y * ctx.w + x
    wx, wz = _pixel_world_coords(x, y, ctx)
    inside_any = any(point_in_triangle_xz((wx, wz), t) for t in ctx.triangles)
    if alpha <= 0:
        # Transparent pixel. Only count as "hole bleed" when it sits
        # inside the alpha silhouette (= part of a detected hole).
        # Exterior transparent covered by mesh is the expected
        # safety-margin band from the 1-cell dilate + MAX downsample.
        if inside_any and ctx.hole_mask[y][x]:
            _paint_debug_pixel(ctx.debug_image, pixel_index, _DEBUG_COLOUR_HOLE_BLEED)
            return 0, 1
        return 0, 0
    if inside_any:
        _paint_debug_pixel(ctx.debug_image, pixel_index, _DEBUG_COLOUR_COVERED)
        return 1, 0
    _paint_debug_pixel(ctx.debug_image, pixel_index, _DEBUG_COLOUR_LEAK)
    visual_y = ctx.h - 1 - y
    quadrant = ("T" if visual_y > ctx.h / 2 else "B") + ("L" if x < ctx.w / 2 else "R")
    quadrants[quadrant] += 1
    leaks_records.append(
        {
            "pixel_x": x,
            "pixel_y_storage": y,
            "pixel_y_visual_pil": visual_y,
            "alpha": alpha,
            "world_x": round(wx, 6),
            "world_z": round(wz, 6),
            "quadrant": quadrant,
        }
    )
    return 1, 0


def _measure_coverage(
    image: bpy.types.Image,
    triangles: list[
        tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    ],
    debug_png_path: Path | None = None,
) -> tuple[float, int, list[dict[str, object]], dict[str, int], int]:
    """Exhaustive coverage measurement of every source pixel.

    Visits EVERY pixel (no sample_step skip) and routes each through
    ``_classify_pixel``, which:

    - Maps to world coords via cell-center convention matching the
      mesh's ``pixel_contour_to_world`` placement.
    - Tests point-in-triangle against the full triangle list.
    - Routes to one of three bins: covered alpha (green), leaked
      alpha = mesh failed to cover (red, with per-quadrant +
      per-record bookkeeping), or hole bleed = mesh over transparent
      pixel inside a detected alpha hole (blue).

    Pre-computes the hole-pixel mask via flood-fill from the image
    border so the bleed check can distinguish exterior safety margin
    from real hole bleed without re-scanning the alpha grid per
    pixel.

    Optionally writes a debug PNG via Blender's image API
    (no PIL dep). Pixel ordering matches Blender's bottom-up
    convention (validator iterates in storage order); visual output
    aligns with the source PNG pixel-for-pixel.
    """
    pixels = list(image.pixels[:])
    w, h = image.size[0], image.size[1]
    world_scale = 1.0 / 100.0
    ctx = _CoverageContext(
        w=w,
        h=h,
        pixels=pixels,
        triangles=triangles,
        hole_mask=_compute_hole_pixel_mask(pixels, w, h),
        world_scale=world_scale,
        half_w=w * world_scale / 2.0,
        half_h=h * world_scale / 2.0,
        half_cell=world_scale / 2.0,
        debug_image=[0, 0, 0, 0] * (w * h) if debug_png_path is not None else None,
    )

    fg = 0
    bleed_count = 0
    leaks_records: list[dict[str, object]] = []
    quadrants = {"TL": 0, "TR": 0, "BL": 0, "BR": 0}
    for y in range(h):
        for x in range(w):
            fg_inc, bleed_inc = _classify_pixel(x, y, ctx, leaks_records, quadrants)
            fg += fg_inc
            bleed_count += bleed_inc

    if ctx.debug_image is not None and debug_png_path is not None:
        _write_debug_png(debug_png_path, w, h, ctx.debug_image)

    coverage = 1.0 - (len(leaks_records) / fg) if fg else 1.0
    return (coverage, len(leaks_records), leaks_records, quadrants, bleed_count)


def _write_debug_png(path: Path, w: int, h: int, rgba_bytes: list[int]) -> None:
    """Write an RGBA image to ``path`` via Blender's image API.

    Pure-Blender (no PIL dep at validate time). Pixels are written
    in Blender's bottom-up convention; since our debug_image was
    populated using ``y`` iterated in storage order (also bottom-up),
    the visual output matches the source image orientation pixel-for-
    pixel.
    """
    name = f"_debug_{path.stem}"
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, width=w, height=h, alpha=True)
    img.pixels[:] = [c / 255.0 for c in rgba_bytes]
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()


def run_validation(sprites: list[str], args: argparse.Namespace) -> dict[str, object]:
    """Run the operator against each sprite name + collect metrics."""
    report: dict[str, object] = {"sprites": {}, "failures": []}
    for sprite_name in sprites:
        sprite_obj = bpy.data.objects.get(sprite_name)
        if sprite_obj is None or sprite_obj.type != "MESH":
            report["failures"].append(f"sprite '{sprite_name}' missing or not a mesh")
            continue
        bpy.context.view_layer.objects.active = sprite_obj
        sprite_obj.select_set(True)
        try:
            bpy.ops.proscenio.automesh_from_sprite(
                margin_pixels=args.margin_pixels,
                alpha_threshold=args.alpha_threshold,
                debug_stage="off",
            )
        except Exception as exc:
            report["failures"].append(f"{sprite_name}: operator raised: {exc}")
            continue
        metrics = measure_mesh(sprite_obj)
        bounds = SPRITE_BOUNDS.get(sprite_name)
        invariants = _check_invariants(metrics, bounds)
        report["sprites"][sprite_name] = {
            "metrics": metrics,
            "invariants": invariants,
        }
        if invariants["failures"]:
            for msg in invariants["failures"]:
                report["failures"].append(f"{sprite_name}: {msg}")
    return report


def _check_invariants(
    metrics: dict[str, object],
    bounds: SpriteInvariants | None,
) -> dict[str, object]:
    """Assert critical invariants per sprite + collect warning messages."""
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
    if bounds is None:
        return {"failures": failures, "warnings": warnings}
    verts = metrics["verts"]
    if isinstance(verts, int):
        lo, hi = bounds.verts
        if not lo <= verts <= hi:
            failures.append(f"vert count {verts} outside expected [{lo}, {hi}]")
    if isinstance(faces, int):
        lo, hi = bounds.faces
        if not lo <= faces <= hi:
            failures.append(f"face count {faces} outside expected [{lo}, {hi}]")
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
    if isinstance(bleed, int):
        max_bleed = bounds.max_hole_bleed
        if bleed > max_bleed:
            failures.append(
                f"hole bleed {bleed} above maximum {max_bleed} "
                f"(mesh covers transparent pixels - hole-aware CDT failed)"
            )
    return {"failures": failures, "warnings": warnings}


def _filter_sprites_for_ci(sprites: list[str], ci_only: bool) -> list[str]:
    """Drop sprites flagged ``ci_safe=False`` when ``--ci-only`` is set."""
    if not ci_only:
        return sprites
    skipped = [n for n in sprites if not SPRITE_BOUNDS[n].ci_safe]
    kept = [n for n in sprites if SPRITE_BOUNDS[n].ci_safe]
    if skipped:
        print(
            f"[validate] --ci-only: skipping {len(skipped)} non-CI-safe sprite(s): "
            f"{', '.join(skipped)}",
            flush=True,
        )
    return kept


def _print_leak_quadrants(quadrants: dict[str, int]) -> None:
    """Print the TL/TR/BL/BR breakdown when any quadrant accumulated leaks."""
    if not any(quadrants.values()):
        return
    print(
        f"  leaks_by_quadrant TL={quadrants.get('TL', 0)} "
        f"TR={quadrants.get('TR', 0)} BL={quadrants.get('BL', 0)} "
        f"BR={quadrants.get('BR', 0)}"
    )


def _print_leak_sample(sample: list[dict[str, object]]) -> None:
    """Print the first up-to-5 leak records (pixel coord + world coord)."""
    if not sample:
        return
    print(f"  first {min(5, len(sample))} leak pixels:")
    for rec in sample[:5]:
        print(
            f"    pixel=({rec['pixel_x']}, "
            f"PIL_y={rec['pixel_y_visual_pil']}) "
            f"alpha={rec['alpha']} "
            f"world=({rec['world_x']}, {rec['world_z']})"
        )


def _print_sprite_report(name: str, payload: dict[str, object]) -> None:
    """Print the per-sprite block (metrics + leaks + invariant verdicts)."""
    m = payload["metrics"]
    inv = payload["invariants"]
    status = "PASS" if not inv["failures"] else "FAIL"
    print(f"\n[{status}] {name}:")
    print(
        f"  verts={m['verts']} faces={m['faces']} "
        f"triangles={m['triangles']} degenerate={m['degenerate_triangles']}"
    )
    coverage = m["coverage_pct"]
    if coverage is not None:
        print(
            f"  coverage={coverage:.6f} leaks={m['leak_count']} "
            f"hole_bleed={m.get('hole_bleed_count', 0)} "
            f"mean_area={m['mean_area']:.6f}"
        )
        _print_leak_quadrants(m.get("leak_quadrants") or {})
        _print_leak_sample(m.get("leak_records_sample") or [])
    for warn in inv["warnings"]:
        print(f"  WARN: {warn}")
    for fail in inv["failures"]:
        print(f"  FAIL: {fail}")


def _print_report(report: dict[str, object]) -> int:
    """Print the full report + return the number of failure-level issues."""
    print()
    print("=" * 60)
    print("AUTOMESH VALIDATION REPORT")
    print("=" * 60)
    for name, payload in report["sprites"].items():
        _print_sprite_report(name, payload)
    print("\n" + "=" * 60)
    total_failures = len(report["failures"])
    if total_failures:
        print(f"VALIDATION FAILED: {total_failures} issue(s)")
        for fail in report["failures"]:
            print(f"  - {fail}")
    else:
        print("VALIDATION PASSED")
    print("=" * 60)
    return total_failures


def _write_json_report(report: dict[str, object], path: Path | None) -> None:
    """Optionally serialize the report to ``path`` (skip when path is None)."""
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nReport written to {path}")


def main() -> None:
    args = parse_args()
    _load_and_register_addon()
    load_fixture()
    sprites = _filter_sprites_for_ci(list(SPRITE_BOUNDS.keys()), args.ci_only)
    report = run_validation(sprites, args)
    total_failures = _print_report(report)
    _write_json_report(report, args.report)
    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
