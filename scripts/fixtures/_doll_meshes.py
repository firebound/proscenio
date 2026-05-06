"""Doll sprite meshes — geometric primitives drawn into PNGs (SPEC 007).

Each region of the doll gets a per-PNG mesh placed at the parent bone's
position. Visual style is locked by SPEC 007 D10: squares, circles,
triangles, rectangles, trapezoids — colored regionally for instant
weight-paint debugging.

The function ``build_all`` is the entry point — it creates one
``bpy.types.Object`` per region with an attached material whose image
node points at the corresponding PNG under ``examples/doll/layers/``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _draw import (  # noqa: E402
    Canvas,
    border,
    circle,
    fill,
    rect,
    save_as_png,
    trapezoid,
    triangle,
)

LAYERS_DIR = (
    Path(__file__).resolve().parents[2] / "examples" / "doll" / "layers"
)
PIXELS_PER_UNIT = 100.0

# Color palette
BEIGE = (0.93, 0.78, 0.68, 1.0)
DARK_BROWN = (0.30, 0.20, 0.15, 1.0)
WHITE = (0.95, 0.95, 0.95, 1.0)
PUPIL = (0.10, 0.10, 0.10, 1.0)
RED = (0.85, 0.20, 0.20, 1.0)
NAVY = (0.10, 0.18, 0.45, 1.0)
BLUE = (0.20, 0.40, 0.85, 1.0)
LIGHT_BLUE = (0.40, 0.60, 0.95, 1.0)
GREEN = (0.20, 0.65, 0.30, 1.0)
GREEN_PALE = (0.55, 0.78, 0.55, 1.0)
GOLD = (0.85, 0.65, 0.20, 1.0)
BROWN = (0.50, 0.30, 0.15, 1.0)
BORDER = (0.0, 0.0, 0.0, 1.0)
TRANSPARENT = (0.0, 0.0, 0.0, 0.0)

# (name, w_px, h_px, parent_bone, sprite_type, draw_fn_kind)
SPRITES: tuple[tuple[str, int, int, str, str, str], ...] = (
    ("head_base", 96, 96, "head", "polygon", "head"),
    ("brow.L", 24, 6, "brow.L", "polygon", "brow"),
    ("brow.R", 24, 6, "brow.R", "polygon", "brow"),
    ("ear.L", 16, 24, "ear.L", "polygon", "ear"),
    ("ear.R", 16, 24, "ear.R", "polygon", "ear"),
    ("jaw", 48, 16, "jaw", "polygon", "jaw"),
    ("lip.T", 32, 6, "lip.T", "polygon", "lip"),
    ("lip.B", 32, 6, "lip.B", "polygon", "lip"),
    ("neck", 32, 24, "neck", "polygon", "neck"),
    ("spine_block", 80, 144, "spine.001", "polygon", "torso"),
    ("breast.L", 36, 36, "breast.L", "polygon", "breast"),
    ("breast.R", 36, 36, "breast.R", "polygon", "breast"),
    ("pelvis_block", 96, 64, "root", "polygon", "pelvis"),
    ("shoulder.L", 32, 32, "shoulder.L", "polygon", "shoulder"),
    ("shoulder.R", 32, 32, "shoulder.R", "polygon", "shoulder"),
    ("upper_arm.L", 24, 80, "upper_arm.L", "polygon", "limb"),
    ("upper_arm.R", 24, 80, "upper_arm.R", "polygon", "limb"),
    ("forearm.L", 22, 72, "forearm.L", "polygon", "limb"),
    ("forearm.R", 22, 72, "forearm.R", "polygon", "limb"),
    ("hand.L", 24, 24, "hand.L", "polygon", "hand"),
    ("hand.R", 24, 24, "hand.R", "polygon", "hand"),
    ("finger.001.L", 8, 16, "finger.001.L", "polygon", "finger"),
    ("finger.001.R", 8, 16, "finger.001.R", "polygon", "finger"),
    ("finger.002.L", 8, 12, "finger.002.L", "polygon", "finger"),
    ("finger.002.R", 8, 12, "finger.002.R", "polygon", "finger"),
    ("thigh.L", 28, 96, "thigh.L", "polygon", "limb_gold"),
    ("thigh.R", 28, 96, "thigh.R", "polygon", "limb_gold"),
    ("shin.L", 26, 96, "shin.L", "polygon", "limb_gold"),
    ("shin.R", 26, 96, "shin.R", "polygon", "limb_gold"),
    ("foot.L", 32, 16, "foot.L", "polygon", "foot"),
    ("foot.R", 32, 16, "foot.R", "polygon", "foot"),
)

# sprite_frame meshes (eyes — 4 frames each, drawn by build_blink_eyes
# convention).
SPRITE_FRAME_REGIONS = (
    ("eye.L", "eye.L"),
    ("eye.R", "eye.R"),
)


def _draw(kind: str, canvas: Canvas) -> None:
    """Dispatch to the correct geometric primitive for a region."""
    w, h = canvas.width, canvas.height
    fill(canvas, TRANSPARENT)
    if kind == "head":
        circle(canvas, w / 2.0, h / 2.0, w / 2.0 - 1, BEIGE)
    elif kind == "brow":
        rect(canvas, 0, 0, w, h, DARK_BROWN)
    elif kind == "ear":
        triangle(canvas, (0, 0), (w, h / 2.0), (0, h), BEIGE)
    elif kind == "jaw":
        rect(canvas, 0, 0, w, h, BEIGE)
    elif kind == "lip":
        rect(canvas, 0, 0, w, h, RED)
    elif kind == "neck":
        rect(canvas, 0, 0, w, h, BEIGE)
    elif kind == "torso":
        rect(canvas, 0, 0, w, h, BLUE)
    elif kind == "breast":
        circle(canvas, w / 2.0, h / 2.0, w / 2.0 - 1, LIGHT_BLUE)
    elif kind == "pelvis":
        trapezoid(canvas, 0, 0, w, w * 0.6, h, NAVY)
    elif kind == "shoulder":
        circle(canvas, w / 2.0, h / 2.0, w / 2.0 - 1, GREEN)
    elif kind == "limb":
        rect(canvas, 0, 0, w, h, GREEN)
    elif kind == "limb_gold":
        rect(canvas, 0, 0, w, h, GOLD)
    elif kind == "hand":
        rect(canvas, 0, 0, w, h, GREEN_PALE)
    elif kind == "finger":
        rect(canvas, 0, 0, w, h, GREEN_PALE)
    elif kind == "foot":
        trapezoid(canvas, 0, 0, w, w * 0.7, h, BROWN)
    border(canvas, BORDER)


def _make_quad_mesh(name: str, w_px: int, h_px: int) -> bpy.types.Mesh:
    w = w_px / PIXELS_PER_UNIT
    h = h_px / PIXELS_PER_UNIT
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        vertices=[
            (-w / 2, 0.0, -h / 2),
            (w / 2, 0.0, -h / 2),
            (w / 2, 0.0, h / 2),
            (-w / 2, 0.0, h / 2),
        ],
        edges=[],
        faces=[(0, 1, 2, 3)],
    )
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    uv.data[0].uv = (0.0, 0.0)
    uv.data[1].uv = (1.0, 0.0)
    uv.data[2].uv = (1.0, 1.0)
    uv.data[3].uv = (0.0, 1.0)
    return mesh


def _make_image_material(name: str, image: bpy.types.Image) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=f"{name}.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = image
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def build_all(armature_obj: bpy.types.Object) -> dict[str, bpy.types.Object]:
    """Build every doll sprite mesh + material. Returns a dict by sprite name.

    Each PNG is drawn fresh; each mesh is parented to its declared bone.
    """
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    out: dict[str, bpy.types.Object] = {}

    for name, w_px, h_px, parent_bone, sprite_type, kind in SPRITES:
        canvas = Canvas.empty(w_px, h_px)
        _draw(kind, canvas)
        png_path = LAYERS_DIR / f"{name}.png"
        image = save_as_png(canvas, name, png_path)

        mesh = _make_quad_mesh(name, w_px, h_px)
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = armature_obj
        obj.parent_type = "BONE"
        obj.parent_bone = parent_bone

        mat = _make_image_material(name, image)
        mesh.materials.append(mat)

        if hasattr(obj, "proscenio"):
            obj.proscenio.sprite_type = sprite_type
        obj["proscenio_type"] = sprite_type

        out[name] = obj

    return out
