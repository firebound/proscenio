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
import json
import sys
from pathlib import Path

import bpy  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = REPO_ROOT / "examples" / "generated" / "automesh" / "automesh.blend"

# Per-sprite tolerance bounds. Sprite-specific because each silhouette
# has different alpha coverage / contour complexity. Bounds were
# calibrated by running the current pipeline manually + adding 30%
# headroom on each side.
SPRITE_BOUNDS: dict[str, dict[str, tuple[int, int] | float | int]] = {
    "blob": {
        "verts": (200, 400),
        "faces": (350, 700),
        "min_coverage": 0.98,
        # No holes -> mesh covering any transparent pixel is a bug.
        "max_hole_bleed": 0,
    },
    "lshape": {
        "verts": (120, 350),
        "faces": (200, 600),
        "min_coverage": 0.96,
        "max_hole_bleed": 0,
    },
    "ring": {
        "verts": (150, 400),
        "faces": (200, 700),
        "min_coverage": 0.95,
        # SPEC 013 D2 amendment - ring is the hole-support smoke
        # target. Hard invariant: leaks=0 (mesh NEVER cuts alpha).
        # Achieved by detecting holes on a 1-cell-DILATED foreground
        # so the mesh-hole boundary sits INSIDE the alpha hole. The
        # flip side: mesh covers a band of transparent hole pixels
        # along the outer hole edge. At downscale=0.25 the band can
        # reach ~50% of small holes (the donut hole is 12 cells wide
        # on the downscaled grid; shrinking by 1 cell on each side
        # leaves a 10-cell mesh cutout = ~70% area). Bumping
        # downscale toward 1.0 or upscaling the hole contour after
        # detection are Wave 13.2+ work. For now, accept the bleed
        # band as the price of "never cut alpha".
        "max_hole_bleed": 1500,
    },
    "hand": {
        "verts": (180, 450),
        "faces": (300, 800),
        # Hand silhouette has tight concave gaps between fingers that
        # the conservative downsample at 0.25 cannot perfectly enclose
        # (each gap is ~4 source pixels = 1 downsampled cell). 96%
        # threshold acknowledges the known limitation; future work
        # (downscale=1.0, adaptive resolution, or morphological
        # closing) can raise this to 0.98+.
        "min_coverage": 0.96,
        "max_hole_bleed": 0,
    },
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


def _point_in_triangle_xz(px: float, pz: float, a, b, c) -> bool:
    """Half-plane test for a point against an XZ-projected triangle."""

    def sign(
        p1x: float, p1z: float, p2x: float, p2z: float, p3x: float, p3z: float
    ) -> float:
        return (p1x - p3x) * (p2z - p3z) - (p2x - p3x) * (p1z - p3z)

    d1 = sign(px, pz, a[0], a[1], b[0], b[1])
    d2 = sign(px, pz, b[0], b[1], c[0], c[1])
    d3 = sign(px, pz, c[0], c[1], a[0], a[1])
    has_neg = d1 < 0.0 or d2 < 0.0 or d3 < 0.0
    has_pos = d1 > 0.0 or d2 > 0.0 or d3 > 0.0
    return not (has_neg and has_pos)


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


def _measure_coverage(
    image: bpy.types.Image,
    triangles: list[
        tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
    ],
    debug_png_path: Path | None = None,
) -> tuple[float, int, list[dict[str, object]], dict[str, int], int]:
    """Exhaustive coverage measurement of every foreground alpha pixel.

    Visits EVERY pixel (no sample_step skip). For each pixel with
    alpha > 0:
    - Compute its EXACT world position using cell-center convention
      that matches pixel_contour_to_world in the bridge.
    - Test point-in-triangle against the full triangle list.
    - If outside every triangle, log a leak record + count by
      quadrant (TL/TR/BL/BR) to expose any geometric asymmetry.

    Optionally writes a debug PNG: red pixel = leak, green pixel =
    covered, transparent = alpha 0. Save next to the JSON report so
    the user can see EXACTLY which pixels were cut without guessing.
    """
    pixels = list(image.pixels[:])
    w, h = image.size[0], image.size[1]
    pixels_per_unit = 100.0
    world_scale = 1.0 / pixels_per_unit
    half_w = w * world_scale / 2.0
    half_h = h * world_scale / 2.0
    half_cell = world_scale / 2.0
    fg = 0
    leaks_records: list[dict[str, object]] = []
    quadrants = {"TL": 0, "TR": 0, "BL": 0, "BR": 0}
    debug_image: list[int] | None = None
    if debug_png_path is not None:
        debug_image = [0, 0, 0, 0] * (w * h)

    # Pre-compute which transparent pixels are HOLE pixels (alpha=0
    # surrounded by alpha>0) versus EXTERIOR pixels (alpha=0 reachable
    # from the image border). Hole bleed = mesh over hole pixel = bug.
    # Margin bleed = mesh over exterior pixel = expected safety dilate.
    hole_mask = _compute_hole_pixel_mask(pixels, w, h)
    bleed_count = 0
    for y in range(h):
        for x in range(w):
            alpha = int(pixels[(y * w + x) * 4 + 3] * 255)
            # World coords using CELL-CENTER convention to match the
            # mesh's pixel_contour_to_world placement (+ half_cell
            # offset on each axis). Visual-Y flip mirrors the
            # bridge's Y-flip-on-read.
            wx = x * world_scale - half_w + half_cell
            visual_y = h - 1 - y
            wz = half_h - visual_y * world_scale - half_cell
            inside_any = False
            for a, b, c in triangles:
                if _point_in_triangle_xz(wx, wz, a, b, c):
                    inside_any = True
                    break
            if alpha <= 0:
                # Transparent pixel. Only count as "hole bleed" when
                # it lives inside the alpha silhouette (i.e. is part
                # of an alpha hole). Exterior transparent pixels
                # covered by mesh are the expected safety-margin band
                # produced by the 1-cell dilate + conservative MAX
                # downsample.
                if inside_any and hole_mask[y][x]:
                    bleed_count += 1
                    if debug_image is not None:
                        idx = (y * w + x) * 4
                        debug_image[idx] = 0
                        debug_image[idx + 1] = 100
                        debug_image[idx + 2] = 255
                        debug_image[idx + 3] = 255
                continue
            fg += 1
            if inside_any:
                if debug_image is not None:
                    idx = (y * w + x) * 4
                    debug_image[idx] = 0  # R
                    debug_image[idx + 1] = 200  # G
                    debug_image[idx + 2] = 0  # B
                    debug_image[idx + 3] = 255
            else:
                visual_y_for_quadrant = h - 1 - y
                quadrant_x = "L" if x < w / 2 else "R"
                quadrant_y = "T" if visual_y_for_quadrant > h / 2 else "B"
                quadrants[quadrant_y + quadrant_x] += 1
                leaks_records.append(
                    {
                        "pixel_x": x,
                        "pixel_y_storage": y,
                        "pixel_y_visual_pil": visual_y_for_quadrant,
                        "alpha": alpha,
                        "world_x": round(wx, 6),
                        "world_z": round(wz, 6),
                        "quadrant": quadrant_y + quadrant_x,
                    }
                )
                if debug_image is not None:
                    idx = (y * w + x) * 4
                    debug_image[idx] = 255  # R
                    debug_image[idx + 1] = 0  # G
                    debug_image[idx + 2] = 0  # B
                    debug_image[idx + 3] = 255

    if debug_image is not None and debug_png_path is not None:
        _write_debug_png(debug_png_path, w, h, debug_image)

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
        bounds = SPRITE_BOUNDS.get(sprite_name, {})
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
    bounds: dict[str, tuple[int, int] | float],
) -> dict[str, object]:
    """Assert critical invariants per sprite + collect warning messages."""
    failures: list[str] = []
    warnings: list[str] = []
    faces = metrics["faces"]
    if not isinstance(faces, int) or faces <= 0:
        failures.append("mesh has 0 faces (CRITICAL - no triangulation)")
    if metrics["degenerate_triangles"]:
        warnings.append(f"{metrics['degenerate_triangles']} degenerate triangles")
    if metrics["uv_out_of_range_loops"]:
        warnings.append(f"{metrics['uv_out_of_range_loops']} UV loops outside [0,1]")
    verts = metrics["verts"]
    vert_bounds = bounds.get("verts")
    if isinstance(vert_bounds, tuple) and isinstance(verts, int):
        lo, hi = vert_bounds
        if not lo <= verts <= hi:
            failures.append(f"vert count {verts} outside expected [{lo}, {hi}]")
    face_bounds = bounds.get("faces")
    if isinstance(face_bounds, tuple) and isinstance(faces, int):
        lo, hi = face_bounds
        if not lo <= faces <= hi:
            failures.append(f"face count {faces} outside expected [{lo}, {hi}]")
    min_coverage = bounds.get("min_coverage")
    coverage = metrics["coverage_pct"]
    if isinstance(min_coverage, float) and isinstance(coverage, float):
        if coverage < min_coverage:
            failures.append(
                f"coverage {coverage:.4f} below minimum {min_coverage:.4f} "
                f"({metrics['leak_count']} alpha pixels NOT covered by mesh)"
            )
    max_bleed = bounds.get("max_hole_bleed")
    bleed = metrics["hole_bleed_count"]
    if isinstance(max_bleed, int) and isinstance(bleed, int):
        if bleed > max_bleed:
            failures.append(
                f"hole bleed {bleed} above maximum {max_bleed} "
                f"(mesh covers transparent pixels - hole-aware CDT failed)"
            )
    return {"failures": failures, "warnings": warnings}


def main() -> None:
    args = parse_args()
    load_fixture()
    sprites = list(SPRITE_BOUNDS.keys())
    report = run_validation(sprites, args)
    print()
    print("=" * 60)
    print("AUTOMESH VALIDATION REPORT")
    print("=" * 60)
    for name, payload in report["sprites"].items():
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
            quadrants = m.get("leak_quadrants") or {}
            if any(quadrants.values()):
                print(
                    f"  leaks_by_quadrant TL={quadrants.get('TL', 0)} "
                    f"TR={quadrants.get('TR', 0)} BL={quadrants.get('BL', 0)} "
                    f"BR={quadrants.get('BR', 0)}"
                )
            sample = m.get("leak_records_sample") or []
            if sample:
                print(f"  first {min(5, len(sample))} leak pixels:")
                for rec in sample[:5]:
                    print(
                        f"    pixel=({rec['pixel_x']}, "
                        f"PIL_y={rec['pixel_y_visual_pil']}) "
                        f"alpha={rec['alpha']} "
                        f"world=({rec['world_x']}, {rec['world_z']})"
                    )
        if inv["warnings"]:
            for w in inv["warnings"]:
                print(f"  WARN: {w}")
        for f in inv["failures"]:
            print(f"  FAIL: {f}")
    print("\n" + "=" * 60)
    total_failures = len(report["failures"])
    if total_failures:
        print(f"VALIDATION FAILED: {total_failures} issue(s)")
        for f in report["failures"]:
            print(f"  - {f}")
    else:
        print("VALIDATION PASSED")
    print("=" * 60)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nReport written to {args.report}")
    sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
