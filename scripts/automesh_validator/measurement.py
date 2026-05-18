"""Mesh measurement + per-sprite operator invocation.

Owns the bmesh inspection (vert / face / triangle / UV / degenerate
counts), the active-material image lookup, and the per-sprite run
loop that drives ``bpy.ops.proscenio.automesh_from_sprite`` against
the fixture + collects metrics.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bpy  # type: ignore[import-not-found]

from .coverage import measure_coverage
from .invariants import SPRITE_BOUNDS, check_invariants

DEGENERATE_AREA_EPSILON = 1e-8
REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "examples" / "generated" / "automesh" / "automesh.blend"


def load_fixture() -> None:
    """Open the automesh fixture .blend in the headless session."""
    if not FIXTURE_PATH.exists():
        sys.exit(f"[validate] FAIL: fixture not found at {FIXTURE_PATH}")
    bpy.ops.wm.open_mainfile(filepath=str(FIXTURE_PATH))


def _first_tex_image_in_material(
    mat: bpy.types.Material | None,
) -> bpy.types.Image | None:
    """Return the first TEX_IMAGE node's image in ``mat``, or None."""
    if mat is None or not mat.use_nodes:
        return None
    for node in mat.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            return node.image
    return None


def _resolve_image(obj: bpy.types.Object) -> bpy.types.Image | None:
    """Find the first TEX_IMAGE node image across the mesh's materials.

    Priority: the active material first (matches what the operator
    uses), then every other material slot. Returns ``None`` when no
    material exposes a texture - the operator's pre-flight catches
    this case earlier with an actionable error.
    """
    if obj.data is None:
        return None
    found = _first_tex_image_in_material(getattr(obj, "active_material", None))
    if found is not None:
        return found
    for mat in obj.data.materials:
        found = _first_tex_image_in_material(mat)
        if found is not None:
            return found
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

    uv_out_of_range = 0
    if mesh.uv_layers.active is not None:
        # 1e-3 epsilon tolerates float rounding around the [0, 1]
        # edges without flagging legitimate boundary verts.
        for uv in mesh.uv_layers.active.data:
            if any(not (-1e-3 <= component <= 1.0 + 1e-3) for component in uv.uv):
                uv_out_of_range += 1

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
            measure_coverage(image, triangles, debug_png)
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
        # Non-zero indicates hole-aware CDT failed to exclude an
        # alpha gap. Zero is the invariant for hole-supporting
        # sprites (ring etc.).
        "hole_bleed_count": bleed_count,
    }


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
            op_result = bpy.ops.proscenio.automesh_from_sprite(
                margin_pixels=args.margin_pixels,
                alpha_threshold=args.alpha_threshold,
                debug_stage="off",
            )
        except Exception as exc:
            report["failures"].append(f"{sprite_name}: operator raised: {exc}")
            continue
        # bpy.ops returns a set containing one of FINISHED / CANCELLED
        # / RUNNING_MODAL / PASS_THROUGH. CANCELLED is silent (no
        # exception) but means the operator aborted before writing to
        # the mesh - measuring the unchanged mesh would produce a false
        # PASS. Treat anything except FINISHED as a failure.
        if "FINISHED" not in op_result:
            report["failures"].append(
                f"{sprite_name}: operator returned {sorted(op_result)} "
                "(expected {'FINISHED'}); mesh not updated"
            )
            continue
        metrics = measure_mesh(sprite_obj)
        bounds = SPRITE_BOUNDS.get(sprite_name)
        invariants = check_invariants(metrics, bounds)
        report["sprites"][sprite_name] = {
            "metrics": metrics,
            "invariants": invariants,
        }
        if invariants["failures"]:
            for msg in invariants["failures"]:
                report["failures"].append(f"{sprite_name}: {msg}")
    return report
