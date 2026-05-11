"""Render every mesh in ``doll.blend`` to its own flat PNG layer (SPEC 007).

Run with::

    blender --background examples/authored/doll/doll.blend \\
        --python scripts/fixtures/doll/render_layers.py

Walks every ``MESH`` object in the scene and renders each to
``examples/authored/doll/01_to_photoshop/render_layers/<object_name>.png`` from a front-orthographic
camera, with transparent background and Workbench flat shading. The
result is a stack of 2D layers — one per mesh — that the rest of the
pipeline (preview composite, .proscenio export) consumes the same way
it consumed the previous Pillow-drawn PNGs.

Pipeline role: the ``.blend`` is the authored source of truth for the
fixture's visual; this script flattens it into the per-region PNG
layers that mimic the future Photoshop-driven workflow (one layer per
body part).

Camera setup
------------
- Orthographic, looking along +Y (matches the Blender front view).
- Per-mesh framing: position + ``ortho_scale`` follow the mesh world
  bounding box on the X / Z axes, plus a small padding so anti-aliased
  edges do not clip.
- Render resolution = bbox extent × ``PIXELS_PER_UNIT`` (default 100),
  so pixels stay square across all rendered layers.

Render setup
------------
- Engine: Workbench (fast, no lighting computed).
- Shading: ``FLAT`` light + ``MATERIAL`` color, so each mesh shows its
  authored material colour as a flat 2D fill.
- World: transparent (PNG alpha preserved).

Skipped objects
---------------
- Non-mesh objects (armature, lights, cameras, empties).
- Meshes whose name is in ``SKIP_MESHES`` (joint visualisers etc).
- Meshes whose render visibility is already disabled in the file.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parents[3]
LAYERS_DIR = (
    REPO_ROOT / "examples" / "authored" / "doll" / "01_to_photoshop" / "render_layers"
)

PIXELS_PER_UNIT = 1000.0
PADDING_UNITS = 0.02  # 20 px @ ppu=1000 -- keeps outline anti-aliasing safe
CAMERA_DISTANCE = 10.0

SKIP_MESHES: set[str] = {"joints"}


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    _configure_render(scene)
    _sync_material_viewport_colors()
    cam_obj = _setup_camera(scene)
    targets = _collect_targets(scene)
    if not targets:
        print("[render_doll_layers] no MESH objects to render", file=sys.stderr)
        sys.exit(1)
    visibility_save = {obj.name: obj.hide_render for obj in scene.objects}
    try:
        _hide_non_render_objects(scene)
        for target in targets:
            _render_one(scene, cam_obj, target, targets)
        print(f"[render_doll_layers] wrote {len(targets)} layer(s) under {LAYERS_DIR}")
    finally:
        for obj in scene.objects:
            if obj.name in visibility_save:
                obj.hide_render = visibility_save[obj.name]


def _configure_render(scene: bpy.types.Scene) -> None:
    """Workbench + flat material colour + transparent background + no AA."""
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 15
    scene.render.dither_intensity = 0.0
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_specular_highlight = False
    # Disable anti-aliasing -- Workbench defaults to 8x AA, which blurs
    # pixel-art edges. "OFF" gives nearest-neighbor crisp output.
    scene.display.render_aa = "OFF"


def _sync_material_viewport_colors() -> None:
    """Copy each material's Principled BSDF ``Base Color`` to its viewport color.

    Workbench's ``MATERIAL`` color mode reads ``material.diffuse_color``
    (the *viewport display* color), not the surface shader. Authors set
    Base Color when they paint a material, so we mirror that into the
    viewport slot before rendering — gives flat-shaded layers in the
    color the artist intended without forcing them to fill in two
    fields per material.
    """
    for mat in bpy.data.materials:
        if not mat.use_nodes or mat.node_tree is None:
            continue
        for node in mat.node_tree.nodes:
            if node.type != "BSDF_PRINCIPLED":
                continue
            base = node.inputs.get("Base Color")
            if base is None or base.is_linked:
                break
            mat.diffuse_color = tuple(base.default_value)
            break


def _setup_camera(scene: bpy.types.Scene) -> bpy.types.Object:
    """Reuse a camera named ``layer_cam`` if present; otherwise create one."""
    cam_obj = bpy.data.objects.get("layer_cam")
    if cam_obj is None or cam_obj.type != "CAMERA":
        cam_data = bpy.data.cameras.new("layer_cam")
        cam_obj = bpy.data.objects.new("layer_cam", cam_data)
        scene.collection.objects.link(cam_obj)
    cam_obj.data.type = "ORTHO"
    # Front view: camera at -Y looking toward +Y, up = +Z. Matches the
    # Blender Numpad-1 front projection.
    cam_obj.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
    scene.camera = cam_obj
    return cam_obj


def _collect_targets(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    """Mesh objects we should render, in scene order."""
    targets: list[bpy.types.Object] = []
    for obj in scene.objects:
        if obj.type != "MESH":
            continue
        if obj.name in SKIP_MESHES:
            continue
        if obj.hide_render:
            continue
        targets.append(obj)
    return targets


def _hide_non_render_objects(scene: bpy.types.Scene) -> None:
    """Hide everything that is not a mesh from the render output.

    Armatures, empties, lights and skipped meshes (e.g. ``joints``) all
    get ``hide_render = True``. The per-target loop later toggles only
    the meshes that should appear in the current pass.
    """
    for obj in scene.objects:
        if obj.type == "CAMERA":
            continue
        if obj.type != "MESH" or obj.name in SKIP_MESHES:
            obj.hide_render = True


def _render_one(
    scene: bpy.types.Scene,
    cam_obj: bpy.types.Object,
    target: bpy.types.Object,
    targets: list[bpy.types.Object],
) -> None:
    """Isolate ``target``, frame the camera around it, render to PNG."""
    for mesh_obj in targets:
        mesh_obj.hide_render = mesh_obj is not target
    bbox_min, bbox_max = _world_bbox(target)
    cx = (bbox_min.x + bbox_max.x) / 2.0
    cz = (bbox_min.z + bbox_max.z) / 2.0
    width = (bbox_max.x - bbox_min.x) + 2.0 * PADDING_UNITS
    height = (bbox_max.z - bbox_min.z) + 2.0 * PADDING_UNITS
    if width <= 0.0 or height <= 0.0:
        print(f"[render_doll_layers] {target.name} has zero bbox — skipped")
        return
    cam_obj.location = (cx, -CAMERA_DISTANCE, cz)
    cam_obj.data.ortho_scale = max(width, height)
    res_x = max(1, int(round(width * PIXELS_PER_UNIT)))
    res_y = max(1, int(round(height * PIXELS_PER_UNIT)))
    # When width != height, ortho_scale spans the longer axis. Set
    # resolution_y proportionally so pixels stay square.
    scale_axis = max(width, height)
    scene.render.resolution_x = max(
        1, int(round(scale_axis * PIXELS_PER_UNIT * res_x / max(res_x, res_y)))
    )
    scene.render.resolution_y = max(
        1, int(round(scale_axis * PIXELS_PER_UNIT * res_y / max(res_x, res_y)))
    )
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(LAYERS_DIR / f"{target.name}.png")
    bpy.ops.render.render(write_still=True)


def _world_bbox(obj: bpy.types.Object) -> tuple[Vector, Vector]:
    """Return (min, max) of the object's world-space axis-aligned bounding box."""
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [v.x for v in corners]
    ys = [v.y for v in corners]
    zs = [v.z for v in corners]
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[render_doll_layers] FAILED: {exc}", file=sys.stderr)
        raise
