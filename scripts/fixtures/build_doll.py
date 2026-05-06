"""Build the doll showcase fixture from scratch (SPEC 007 step 3).

Run with::

    blender --background --python scripts/fixtures/build_doll.py

Idempotent: deletes the existing ``examples/doll/`` outputs and rewrites
them deterministically. Generates:

- ``layers/*.png`` — one PNG per region of the body, drawn by
  ``_doll_meshes`` using the shared ``_draw`` shape rasterizer. Visual
  style is geometric primitives (circles / rectangles / triangles /
  trapezoids) colored regionally for instant visual debugging.
- ``layers/eye_*.png`` + ``eye_spritesheet.png`` — sprite_frame frames
  for the eyes (open / partial / closing / closed).
- ``doll.blend`` — the full 37-bone humanoid armature, all sprite
  meshes parented + weighted, four actions (idle / wave / blink / walk).

Compose order:

1. ``_wipe_blend`` — clean slate
2. ``_doll_armature.build`` — 37 bones
3. ``_doll_meshes.build_all`` — sprite planes + materials + PNGs
4. eye sprite_frame setup (uses the same blink eye PNG generator)
5. ``_doll_weights.apply`` — vertex groups + weights
6. ``_doll_actions.build_all`` — 4 actions
7. ``_save_blend``
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _draw import Canvas, circle, save_as_png  # noqa: E402

import _doll_actions  # noqa: E402
import _doll_armature  # noqa: E402
import _doll_meshes  # noqa: E402
import _doll_weights  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = REPO_ROOT / "examples" / "doll"
LAYERS_DIR = FIXTURE_DIR / "layers"
SHEET_PATH = LAYERS_DIR / "eye_spritesheet.png"
BLEND_PATH = FIXTURE_DIR / "doll.blend"

EYE_FRAME_W = 32
EYE_FRAME_H = 32
EYE_HFRAMES = 4
EYE_VFRAMES = 1
EYE_SHEET_W = EYE_FRAME_W * EYE_HFRAMES
EYE_SHEET_H = EYE_FRAME_H * EYE_VFRAMES
PIXELS_PER_UNIT = 100.0

WHITE = (0.95, 0.95, 0.95, 1.0)
PUPIL = (0.10, 0.10, 0.10, 1.0)
TRANSPARENT = (0.0, 0.0, 0.0, 0.0)

EYE_FRAMES = ((0, 1.0), (1, 0.6), (2, 0.2), (3, 0.0))


def main() -> None:
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)
    _wipe_blend()
    armature_obj = _doll_armature.build()
    sprite_objs = _doll_meshes.build_all(armature_obj)
    _add_eye_sprite_frames(sprite_objs, armature_obj)
    _doll_weights.apply(sprite_objs, armature_obj)
    _doll_actions.build_all(armature_obj, sprite_objs)
    _save_blend()
    print(f"[doll] wrote {BLEND_PATH}")
    print(f"[doll] wrote {len(sprite_objs)} sprite PNGs under {LAYERS_DIR}")


def _wipe_blend() -> None:
    for collection in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.actions,
    ):
        for item in list(collection):
            collection.remove(item)


def _draw_eye_frame(canvas: Canvas, open_ratio: float) -> None:
    cx = canvas.width / 2.0
    cy = canvas.height / 2.0
    iris_r = canvas.width / 2.0 - 2
    pupil_r = iris_r * 0.4
    open_h = (canvas.height * open_ratio) / 2.0
    circle(canvas, cx, cy, iris_r, WHITE)
    circle(canvas, cx, cy, pupil_r, PUPIL)
    if open_h < canvas.height / 2.0:
        for y in range(canvas.height):
            if abs(y + 0.5 - cy) > open_h:
                for x in range(canvas.width):
                    canvas.set(x, y, TRANSPARENT)


def _generate_eye_pngs() -> bpy.types.Image:
    """Per-frame PNGs + spritesheet. Returns the spritesheet Image."""
    for idx, open_ratio in EYE_FRAMES:
        canvas = Canvas.empty(EYE_FRAME_W, EYE_FRAME_H)
        _draw_eye_frame(canvas, open_ratio)
        save_as_png(canvas, f"eye_{idx}", LAYERS_DIR / f"eye_{idx}.png")
    sheet = Canvas.empty(EYE_SHEET_W, EYE_SHEET_H)
    for idx, open_ratio in EYE_FRAMES:
        sub = Canvas.empty(EYE_FRAME_W, EYE_FRAME_H)
        _draw_eye_frame(sub, open_ratio)
        x_offset = idx * EYE_FRAME_W
        for y in range(EYE_FRAME_H):
            for x in range(EYE_FRAME_W):
                src = (y * EYE_FRAME_W + x) * 4
                dst = (y * EYE_SHEET_W + x_offset + x) * 4
                sheet.pixels[dst : dst + 4] = sub.pixels[src : src + 4]
    return save_as_png(sheet, "eye_spritesheet", SHEET_PATH)


def _add_eye_sprite_frames(
    sprite_objs: dict[str, bpy.types.Object], armature_obj: bpy.types.Object
) -> None:
    """Build the two sprite_frame eye meshes referencing the spritesheet."""
    sheet_image = _generate_eye_pngs()
    for eye_name, parent_bone in (("eye.L", "eye.L"), ("eye.R", "eye.R")):
        w = EYE_FRAME_W / PIXELS_PER_UNIT
        h = EYE_FRAME_H / PIXELS_PER_UNIT
        mesh = bpy.data.meshes.new(eye_name)
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

        obj = bpy.data.objects.new(eye_name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = armature_obj
        obj.parent_type = "BONE"
        obj.parent_bone = parent_bone

        mat = bpy.data.materials.new(name=f"{eye_name}.mat")
        mat.use_nodes = True
        nt = mat.node_tree
        while nt.nodes:
            nt.nodes.remove(nt.nodes[0])
        out = nt.nodes.new(type="ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
        tex = nt.nodes.new(type="ShaderNodeTexImage")
        tex.image = sheet_image
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
        mesh.materials.append(mat)

        if hasattr(obj, "proscenio"):
            obj.proscenio.sprite_type = "sprite_frame"
            obj.proscenio.hframes = EYE_HFRAMES
            obj.proscenio.vframes = EYE_VFRAMES
            obj.proscenio.frame = 0
            obj.proscenio.centered = True
        obj["proscenio_type"] = "sprite_frame"
        obj["proscenio_hframes"] = EYE_HFRAMES
        obj["proscenio_vframes"] = EYE_VFRAMES
        obj["proscenio_frame"] = 0
        obj["proscenio_centered"] = True

        sprite_objs[eye_name] = obj


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[doll] FAILED: {exc}", file=sys.stderr)
        raise
