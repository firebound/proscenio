"""Assemble the doll showcase .blend (SPEC 007 step 3, Blender side).

Run with::

    blender --background --python scripts/fixtures/build_doll.py

Loads PNGs produced by ``draw_doll.py`` from disk and assembles the
full ``.blend``: 37-bone armature + ~25 sprite meshes (polygon +
sprite_frame eyes) + multi-bone weights + 4 actions
(idle / wave / blink / walk).

Run ``draw_doll.py`` first or this script aborts on missing PNGs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
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
PIXELS_PER_UNIT = 100.0


def main() -> None:
    if not SHEET_PATH.exists():
        print(
            f"[build_doll] missing {SHEET_PATH} — run draw_doll.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _doll_armature.build()
    sprite_objs = _doll_meshes.build_all(armature_obj)
    _add_eye_sprite_frames(sprite_objs, armature_obj)
    _doll_weights.apply(sprite_objs, armature_obj)
    _doll_actions.build_all(armature_obj, sprite_objs)
    _save_blend()
    print(f"[build_doll] wrote {BLEND_PATH}")
    print(f"[build_doll] used {len(sprite_objs)} sprite mesh(es)")


def _wipe_blend() -> None:
    for collection in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.actions,
    ):
        while collection:
            collection.remove(collection[0])


def _add_eye_sprite_frames(
    sprite_objs: dict[str, bpy.types.Object], armature_obj: bpy.types.Object
) -> None:
    """Build the two sprite_frame eye meshes referencing the spritesheet."""
    sheet_image = bpy.data.images.load(str(SHEET_PATH), check_existing=True)
    sheet_image.name = "eye_spritesheet"
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
        print(f"[build_doll] FAILED: {exc}", file=sys.stderr)
        raise
