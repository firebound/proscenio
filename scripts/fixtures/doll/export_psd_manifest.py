"""Export the doll fixture as a SPEC 006 v1 PSD manifest (roundtrip tooling).

Run with::

    blender --background examples/doll/doll.blend \\
        --python scripts/fixtures/export_doll_psd_manifest.py

Walks every ``MESH`` object in ``doll.blend``, projects its world XZ
bounding box onto a Photoshop-style top-left canvas at
``PIXELS_PER_UNIT``, and emits a manifest matching
``schemas/psd_manifest.schema.json`` (format_version=1, kind=polygon
for every mesh). Output sits at
``examples/doll/doll.psd_manifest.json`` and references the existing
``examples/doll/layers/<name>.png`` files (rendered by
``render_doll_layers.py``).

Pipeline role: the Wave 6.0.5 roundtrip-tooling deliverable. The
generated manifest feeds the new JSX importer
(``photoshop-exporter/proscenio_import.jsx``) so the doll fixture can
be opened as a real PSD with every body part placed at the correct
position. That PSD then drives the SPEC 006 PSD → Blender importer
(Wave 6.3) end-to-end, closing the loop.

Conventions
-----------
- Blender world axes: X horizontal, Z vertical (figure stands upright
  at z=0). Y is depth into the screen.
- PSD canvas: top-left origin, +X right, +Y down. Pixels.
- Conversion::

      psd.x = (mesh.world.min_x - global.min_x) * PIXELS_PER_UNIT + PAD
      psd.y = (global.max_z   - mesh.world.max_z) * PIXELS_PER_UNIT + PAD
      psd.w = (mesh.world.max_x - mesh.world.min_x) * PIXELS_PER_UNIT
      psd.h = (mesh.world.max_z - mesh.world.min_z) * PIXELS_PER_UNIT

- ``z_order``: meshes sorted by world Y ascending (lowest Y = closest
  to camera = frontmost = z_order 0). Ties broken by mesh name.
- Skipped: meshes whose bounding box is empty (or whose name is in
  ``SKIP_MESHES``, mirroring ``render_doll_layers.py``).
- Sprite_frame: not emitted in v1. The doll's eye meshes are single
  polygon quads; if a future authored ``.blend`` carries hframed eyes
  the script will need extending.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "doll"
LAYERS_DIR = FIXTURE_DIR / "render_layers"
MANIFEST_OUT = FIXTURE_DIR / "photoshop_export" / "doll.psd_manifest.json"

PIXELS_PER_UNIT = 100.0
CANVAS_PADDING_PX = 32
SKIP_MESHES: set[str] = {"joints"}
MANIFEST_FORMAT_VERSION = 1


def main() -> None:
    targets = _collect_meshes()
    if not targets:
        print("[export_doll_psd_manifest] no MESH objects in scene", file=sys.stderr)
        sys.exit(1)
    bboxes = {obj.name: _world_bbox(obj) for obj in targets}
    bboxes = {name: bbox for name, bbox in bboxes.items() if bbox is not None}
    if not bboxes:
        print("[export_doll_psd_manifest] no usable bboxes", file=sys.stderr)
        sys.exit(1)
    global_min, global_max = _aggregate_bbox(bboxes.values())
    canvas_size = _canvas_size(global_min, global_max)
    z_sorted = _sort_by_world_depth(bboxes, targets)
    layers = [
        _layer_entry(obj_name, bboxes[obj_name], global_min, global_max, z_order)
        for z_order, obj_name in enumerate(z_sorted)
    ]
    missing = [layer for layer in layers if not (LAYERS_DIR / f"{layer['name']}.png").exists()]
    if missing:
        names = ", ".join(layer["name"] for layer in missing)
        print(
            f"[export_doll_psd_manifest] WARNING — missing layer PNG(s): {names}\n"
            f"  Run scripts/fixtures/render_doll_layers.py first to regenerate.",
            file=sys.stderr,
        )
    manifest = {
        "format_version": MANIFEST_FORMAT_VERSION,
        "doc": "doll.psd",
        "size": list(canvas_size),
        "pixels_per_unit": PIXELS_PER_UNIT,
        "layers": layers,
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"[export_doll_psd_manifest] wrote {MANIFEST_OUT} "
        f"({len(layers)} layer(s), canvas {canvas_size[0]}x{canvas_size[1]} px)"
    )


def _collect_meshes() -> list[bpy.types.Object]:
    """Return every renderable mesh object in scene order, skipping aux meshes."""
    out: list[bpy.types.Object] = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        if obj.name in SKIP_MESHES:
            continue
        if obj.hide_render:
            continue
        out.append(obj)
    return out


def _world_bbox(obj: bpy.types.Object) -> tuple[Vector, Vector] | None:
    """Return (min, max) of the object's world-space axis-aligned bbox.

    Returns ``None`` for degenerate (zero-volume) bboxes — the caller
    skips them so empty meshes do not poison the manifest.
    """
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [v.x for v in corners]
    ys = [v.y for v in corners]
    zs = [v.z for v in corners]
    bbox_min = Vector((min(xs), min(ys), min(zs)))
    bbox_max = Vector((max(xs), max(ys), max(zs)))
    if (bbox_max - bbox_min).length < 1e-6:
        return None
    return bbox_min, bbox_max


def _aggregate_bbox(
    bboxes: list[tuple[Vector, Vector]],
) -> tuple[Vector, Vector]:
    """Union every bbox into a single (min, max) pair."""
    min_v = Vector((float("inf"),) * 3)
    max_v = Vector((float("-inf"),) * 3)
    for bb_min, bb_max in bboxes:
        min_v = Vector((min(min_v.x, bb_min.x), min(min_v.y, bb_min.y), min(min_v.z, bb_min.z)))
        max_v = Vector((max(max_v.x, bb_max.x), max(max_v.y, bb_max.y), max(max_v.z, bb_max.z)))
    return min_v, max_v


def _canvas_size(global_min: Vector, global_max: Vector) -> tuple[int, int]:
    width_units = global_max.x - global_min.x
    height_units = global_max.z - global_min.z
    width = int(round(width_units * PIXELS_PER_UNIT)) + 2 * CANVAS_PADDING_PX
    height = int(round(height_units * PIXELS_PER_UNIT)) + 2 * CANVAS_PADDING_PX
    return width, height


def _sort_by_world_depth(
    bboxes: dict[str, tuple[Vector, Vector]],
    targets: list[bpy.types.Object],
) -> list[str]:
    """Sort meshes by world Y midpoint ascending (frontmost first)."""

    def key(name: str) -> tuple[float, str]:
        bb_min, bb_max = bboxes[name]
        depth = (bb_min.y + bb_max.y) / 2.0
        return depth, name

    return sorted(bboxes.keys(), key=key)


def _layer_entry(
    name: str,
    bbox: tuple[Vector, Vector],
    global_min: Vector,
    global_max: Vector,
    z_order: int,
) -> dict[str, object]:
    """Project a world-space bbox to PSD-space top-left position + size."""
    bb_min, bb_max = bbox
    x = (bb_min.x - global_min.x) * PIXELS_PER_UNIT + CANVAS_PADDING_PX
    y = (global_max.z - bb_max.z) * PIXELS_PER_UNIT + CANVAS_PADDING_PX
    w = (bb_max.x - bb_min.x) * PIXELS_PER_UNIT
    h = (bb_max.z - bb_min.z) * PIXELS_PER_UNIT
    return {
        "kind": "polygon",
        "name": name,
        "path": f"../render_layers/{name}.png",
        "position": [int(round(x)), int(round(y))],
        "size": [max(1, int(round(w))), max(1, int(round(h)))],
        "z_order": z_order,
    }


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[export_doll_psd_manifest] FAILED: {exc}", file=sys.stderr)
        raise
