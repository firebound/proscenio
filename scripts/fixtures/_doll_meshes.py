"""Doll sprite meshes — loads PNGs from disk and builds bpy objects (SPEC 007).

Pure bpy module. PNGs must already exist under
``examples/doll/layers/`` (run ``draw_doll.py`` first). Each region of
the doll gets a quad mesh sized in pixels / pixels_per_unit, parented
+ bone-typed to the appropriate armature bone, materialed with a
TEX_IMAGE node referencing the on-disk PNG.

The sprite list mirrors ``draw_doll.SPRITES`` — keep the two in sync.
"""

from __future__ import annotations

from pathlib import Path

import bpy

LAYERS_DIR = Path(__file__).resolve().parents[2] / "examples" / "doll" / "layers"
PIXELS_PER_UNIT = 100.0

# (sprite_name, w_px, h_px, parent_bone, sprite_type)
# Mirrors draw_doll.SPRITES — no draw_kind here because PNGs are loaded
# from disk; the visual was settled at draw time.
SPRITES: tuple[tuple[str, int, int, str, str], ...] = (
    ("head_base", 96, 96, "head", "polygon"),
    ("brow.L", 24, 6, "brow.L", "polygon"),
    ("brow.R", 24, 6, "brow.R", "polygon"),
    ("ear.L", 16, 24, "ear.L", "polygon"),
    ("ear.R", 16, 24, "ear.R", "polygon"),
    ("jaw", 48, 16, "jaw", "polygon"),
    ("lip.T", 32, 6, "lip.T", "polygon"),
    ("lip.B", 32, 6, "lip.B", "polygon"),
    ("neck", 32, 24, "neck", "polygon"),
    ("spine_block", 80, 144, "spine.001", "polygon"),
    ("breast.L", 36, 36, "breast.L", "polygon"),
    ("breast.R", 36, 36, "breast.R", "polygon"),
    ("pelvis_block", 96, 64, "root", "polygon"),
    ("shoulder.L", 32, 32, "shoulder.L", "polygon"),
    ("shoulder.R", 32, 32, "shoulder.R", "polygon"),
    ("upper_arm.L", 24, 80, "upper_arm.L", "polygon"),
    ("upper_arm.R", 24, 80, "upper_arm.R", "polygon"),
    ("forearm.L", 22, 72, "forearm.L", "polygon"),
    ("forearm.R", 22, 72, "forearm.R", "polygon"),
    ("hand.L", 24, 24, "hand.L", "polygon"),
    ("hand.R", 24, 24, "hand.R", "polygon"),
    ("finger.001.L", 8, 16, "finger.001.L", "polygon"),
    ("finger.001.R", 8, 16, "finger.001.R", "polygon"),
    ("finger.002.L", 8, 12, "finger.002.L", "polygon"),
    ("finger.002.R", 8, 12, "finger.002.R", "polygon"),
    ("thigh.L", 28, 96, "thigh.L", "polygon"),
    ("thigh.R", 28, 96, "thigh.R", "polygon"),
    ("shin.L", 26, 96, "shin.L", "polygon"),
    ("shin.R", 26, 96, "shin.R", "polygon"),
    ("foot.L", 32, 16, "foot.L", "polygon"),
    ("foot.R", 32, 16, "foot.R", "polygon"),
)


def _make_quad_mesh(name: str, w_px: int, h_px: int) -> bpy.types.Mesh:
    """Quad sized so width / height in Blender units match pixels / ppu."""
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
    """Build every doll polygon sprite mesh + material. Returns dict by name.

    Loads each PNG from ``examples/doll/layers/<name>.png``. Sprite_frame
    eye meshes are added by the orchestrator (build_doll.py) since they
    share a single spritesheet image.
    """
    out: dict[str, bpy.types.Object] = {}

    for name, w_px, h_px, parent_bone, sprite_type in SPRITES:
        png_path = LAYERS_DIR / f"{name}.png"
        image = bpy.data.images.load(str(png_path), check_existing=True)
        image.name = name

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
