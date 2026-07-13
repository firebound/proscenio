"""Assemble the bone_attach .blend (step 2, Blender side).

Run with::

    blender --background --python packages/fixtures/bone_attach/build_blend.py

Loads ``examples/generated/bone_attach/pillow_layers/badge.png`` produced by
``draw_layers.py`` and builds the spec 080 sprite rest-transform fixture:

- 1-bone armature (``anchor``), tail +Z (up) - the bone therefore exports a
  -90 degree Godot rest rotation, the exact shape that used to lay a
  bone-parented sprite on its side.
- 1 sprite quad (``badge``) REAL bone-parented keep-transform (the
  firebound_guy authoring shape, kept as the power-user fallback), with all
  three placement components the document used to drop:
  - object origin away from the bone head (position),
  - an authored in-plane rotation (rotation),
  - a quad centre away from the object origin (pivot offset, which must
    survive the pull-back into the rotated node frame).
- 1 sprite quad (``pin``) bound the constraint-first way (spec 080 D4): a
  ``Proscenio Sprite Follow`` Child Of whose inverse cancels the bone REST -
  the golden pins that the writer resolves the bone from the constraint and
  emits the same rest-transform fields.

Run ``draw_layers.py`` first or this script aborts on the missing PNG.
"""

from __future__ import annotations

import sys
from pathlib import Path

import bpy
from mathutils import Matrix

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = REPO_ROOT / "examples" / "generated" / "bone_attach"
BADGE_PATH = FIXTURE_DIR / "pillow_layers" / "badge.png"
BLEND_PATH = FIXTURE_DIR / "bone_attach.blend"

BADGE_PX = 32
PIXELS_PER_UNIT = 100.0

# Bone: +Z (up) from head (0.4, 0, 0.2) - Godot rest (40, -20), rotation -pi/2.
BONE_HEAD = (0.4, 0.0, 0.2)
BONE_TAIL = (0.4, 0.0, 0.8)

# Sprite object origin, away from the bone head by (0.15, 0.25) Blender units
# - Godot position (55, -45), a (15, -25) px gap the document used to drop.
BADGE_ORIGIN = (0.55, 0.0, 0.45)
# Authored in-plane rotation (about world +Y): Godot rotation +0.35 rad.
BADGE_ROT_Y = 0.35
# Quad centre away from the object origin in LOCAL space: pivot offset
# (5, -10) px after the pull-back into the node frame.
QUAD_CENTER = (0.05, 0.1)


def main() -> None:
    if not BADGE_PATH.exists():
        print(
            f"[build_bone_attach] missing {BADGE_PATH} - run draw_layers.py first",
            file=sys.stderr,
        )
        sys.exit(1)
    _wipe_blend()
    armature_obj = _build_armature()
    _build_badge_sprite(armature_obj)
    _build_pin_sprite(armature_obj)
    _save_blend()
    _rewrite_image_to_relpath()
    bpy.ops.wm.save_mainfile()
    print(f"[build_bone_attach] wrote {BLEND_PATH}")


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


def _build_armature() -> bpy.types.Object:
    arm_data = bpy.data.armatures.new("bone_attach.armature")
    arm_obj = bpy.data.objects.new("bone_attach.armature", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    # Tail +Z (up): rest rotation -90deg in Godot. Before spec 080 this was
    # the forbidden shape for sprite attaches (the sprite inherited the -90);
    # this fixture exists to pin that it now renders upright.
    bone = arm_data.edit_bones.new("anchor")
    bone.head = BONE_HEAD
    bone.tail = BONE_TAIL
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def _build_badge_sprite(armature_obj: bpy.types.Object) -> bpy.types.Object:
    w = BADGE_PX / PIXELS_PER_UNIT
    h = BADGE_PX / PIXELS_PER_UNIT
    cx, cz = QUAD_CENTER
    mesh = bpy.data.meshes.new("badge")
    # Standard XZ picture-plane quad, deliberately NOT centred on the object
    # origin: the (cx, cz) local centre becomes the Sprite2D pivot offset.
    mesh.from_pydata(
        vertices=[
            (cx - w / 2, 0.0, cz - h / 2),
            (cx + w / 2, 0.0, cz - h / 2),
            (cx + w / 2, 0.0, cz + h / 2),
            (cx - w / 2, 0.0, cz + h / 2),
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

    obj = bpy.data.objects.new("badge", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = BADGE_ORIGIN
    obj.rotation_euler = (0.0, BADGE_ROT_Y, 0.0)
    bpy.context.view_layer.update()

    # Real BONE parent, keep-transform (the programmatic form of Blender's
    # "Set Parent > Bone, Keep Transform" and of the addon's
    # parent_to_bone_keep_world): snapshot the world matrix, parent, restore.
    world = obj.matrix_world.copy()
    obj.parent = armature_obj
    obj.parent_type = "BONE"
    obj.parent_bone = "anchor"
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.matrix_world = world
    bpy.context.view_layer.update()

    mat = bpy.data.materials.new(name="badge.mat")
    mat.use_nodes = True
    nt = mat.node_tree
    while nt.nodes:
        nt.nodes.remove(nt.nodes[0])
    out = nt.nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new(type="ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(BADGE_PATH), check_existing=True)
    tex.interpolation = "Closest"  # pixel-art: nearest-neighbor, no bilinear blur
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    mesh.materials.append(mat)

    obj["proscenio_type"] = "sprite"
    obj["proscenio_hframes"] = 1
    obj["proscenio_vframes"] = 1
    obj["proscenio_frame"] = 0
    obj["proscenio_centered"] = True
    return obj


def _build_pin_sprite(armature_obj: bpy.types.Object) -> bpy.types.Object:
    """A second sprite bound via the Proscenio Child Of follow (constraint-first).

    Mirrors what the Bind to Bone operator authors: object-parent untouched,
    a named CHILD_OF whose inverse cancels the bone REST. Origin sits away
    from the bone head, no authored rotation - the golden pins position-only
    emission through the constraint resolution path.
    """
    w = BADGE_PX / PIXELS_PER_UNIT
    mesh = bpy.data.meshes.new("pin")
    mesh.from_pydata(
        vertices=[
            (-w / 2, 0.0, -w / 2),
            (w / 2, 0.0, -w / 2),
            (w / 2, 0.0, w / 2),
            (-w / 2, 0.0, w / 2),
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

    obj = bpy.data.objects.new("pin", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = (0.1, 0.0, 0.8)
    bpy.context.view_layer.update()

    con = obj.constraints.new(type="CHILD_OF")
    con.name = "Proscenio Sprite Follow"
    con.target = armature_obj
    con.subtarget = "anchor"
    con.inverse_matrix = (
        armature_obj.matrix_world @ armature_obj.data.bones["anchor"].matrix_local
    ).inverted()

    mesh.materials.append(bpy.data.materials["badge.mat"])

    obj["proscenio_type"] = "sprite"
    obj["proscenio_hframes"] = 1
    obj["proscenio_vframes"] = 1
    obj["proscenio_frame"] = 0
    obj["proscenio_centered"] = True
    return obj


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


def _rewrite_image_to_relpath() -> None:
    """After save_as, rewrite image filepath to ``//pillow_layers/...``.

    ``bpy.path.relpath`` needs the .blend to already be on disk so its
    filepath can serve as the base; the first ``save_as`` sets that base,
    this helper rewrites + the caller saves again (cross-machine safe).
    """
    rel = bpy.path.relpath(str(BADGE_PATH))
    for img in bpy.data.images:
        if img.filepath:
            img.filepath = rel


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_bone_attach] FAILED: {exc}", file=sys.stderr)
        raise
