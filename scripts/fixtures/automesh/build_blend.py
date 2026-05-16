"""Assemble the automesh .blend (SPEC 013 Wave 13.1 fixture).

Run with::

    blender --background --python scripts/fixtures/automesh/build_blend.py

Loads 4 PNGs produced by ``draw_layers.py`` from disk and builds:

- 3-bone arm armature (``automesh.arm``: ``shoulder`` -> ``elbow`` ->
  ``wrist``) positioned across the X axis at Z=0 so the hand sprite
  sits under the chain - exercises SPEC 013 D15 density-under-bones
  end-to-end (the hand mesh gets thicker triangulation near each
  bone segment when automesh runs against the picker).
- 4 sprite plane meshes (``hand``, ``blob``, ``lshape``, ``ring``),
  each 200x200 px (2.0 world units side at PPU=100), each with its
  own image-textured material referencing the matching PNG. Sprites
  are spread across the workbench so the user can select one at a
  time without overlapping geometry.
- ``hand`` is parented to ``automesh.arm`` (other sprites stay free
  to keep the smoke checklist's "automesh without picker" case
  trivially testable - select blob / lshape / ring + run automesh
  + verify uniform interior density falls back gracefully).

The fixture exists to feed ``tests/MANUAL_TESTING.md`` section
1.15 (T1-T16) end-to-end. Regenerate by re-running ``draw_layers.py``
then this script when the smoke checklist needs an updated baseline.

Run ``draw_layers.py`` first or this script aborts on missing PNGs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "automesh"
LAYERS_DIR = FIXTURE_DIR / "pillow_layers"
BLEND_PATH = FIXTURE_DIR / "automesh.blend"

FRAME = 200
PIXELS_PER_UNIT = 100.0
SPRITE_SIZE = FRAME / PIXELS_PER_UNIT


def main() -> None:
    expected_pngs = ("hand.png", "blob.png", "lshape.png", "ring.png")
    missing = [LAYERS_DIR / name for name in expected_pngs if not (LAYERS_DIR / name).exists()]
    if missing:
        names = ", ".join(str(p.name) for p in missing)
        print(
            f"[build_automesh] missing PNG(s): {names} - run draw_layers.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_arm_chain()
    sprite_layout = (
        ("hand", -3.0, 0.0, True),
        ("blob", 0.0, 0.0, False),
        ("lshape", 3.0, 0.0, False),
        ("ring", 0.0, -3.0, False),
    )
    for name, cx, cz, parent_to_arm in sprite_layout:
        _build_sprite_quad(name, cx, cz, armature_obj if parent_to_arm else None)
    _save_blend()
    _rewrite_image_to_relpath()
    bpy.ops.wm.save_mainfile()
    print(f"[build_automesh] wrote {BLEND_PATH}")


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


def _build_arm_chain() -> bpy.types.Object:
    """3-bone arm chain along world +X positioned over the hand sprite.

    The hand sprite sits at world X=-3, Z=0 with 2.0-unit extent.
    Bones span shoulder (X=-4, Z=0) -> elbow (X=-3.3, Z=0) ->
    wrist (X=-2.6, Z=0) so they actually cross the hand mesh's bbox
    in the X axis, which is the configuration density-under-bones
    needs to make a visible difference in the triangulation.
    """
    arm_data = bpy.data.armatures.new("automesh.arm")
    arm_obj = bpy.data.objects.new("automesh.arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    shoulder = arm_data.edit_bones.new("shoulder")
    shoulder.head = (-4.0, 0.0, 0.0)
    shoulder.tail = (-3.3, 0.0, 0.0)
    elbow = arm_data.edit_bones.new("elbow")
    elbow.head = (-3.3, 0.0, 0.0)
    elbow.tail = (-2.6, 0.0, 0.0)
    elbow.parent = shoulder
    elbow.use_connect = True
    wrist = arm_data.edit_bones.new("wrist")
    wrist.head = (-2.6, 0.0, 0.0)
    wrist.tail = (-2.0, 0.0, 0.0)
    wrist.parent = elbow
    wrist.use_connect = True
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_sprite_quad(
    name: str,
    cx: float,
    cz: float,
    parent_armature: bpy.types.Object | None,
) -> bpy.types.Object:
    """Build a 2.0x2.0 unit sprite quad at (cx, 0, cz)."""
    png_path = LAYERS_DIR / f"{name}.png"
    half = SPRITE_SIZE / 2.0
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        vertices=[
            (-half, 0.0, -half),
            (half, 0.0, -half),
            (half, 0.0, half),
            (-half, 0.0, half),
        ],
        edges=[],
        faces=[(0, 1, 2, 3)],
    )
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    uv.data[0].uv = (1.0, 0.0)
    uv.data[1].uv = (0.0, 0.0)
    uv.data[2].uv = (0.0, 1.0)
    uv.data[3].uv = (1.0, 1.0)

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (cx, 0.0, cz)
    if parent_armature is not None:
        obj.parent = parent_armature
        obj.parent_type = "OBJECT"

    mat = bpy.data.materials.new(name=f"{name}.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(png_path), check_existing=True)
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mesh.materials.append(mat)

    if hasattr(obj, "proscenio"):
        obj.proscenio.sprite_type = "polygon"
        obj.proscenio.centered = True
    obj["proscenio_type"] = "polygon"
    obj["proscenio_centered"] = True
    return obj


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_image_to_relpath() -> None:
    """After save_as, rewrite every image filepath to ``//pillow_layers/...``."""
    for img in bpy.data.images:
        if not img.filepath:
            continue
        try:
            img.filepath = bpy.path.relpath(img.filepath)
        except ValueError:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_automesh] FAILED: {exc}", file=sys.stderr)
        raise
