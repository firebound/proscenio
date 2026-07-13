"""Headless writer test: a multi-face mesh exports every face, not just the first.

Runs INSIDE Blender via ``run_operator_tests.py``. Builds real meshes (no
.blend fixture) and drives the writer's ``build_element`` so the bpy matrix /
mesh-polygon path - the part pure pytest cannot exercise - is covered. Before
the multi-polygon fix the writer emitted only ``polygon_at(mesh, 0)``, so a
triangulated or multi-island mesh silently truncated to its first face.
"""

from __future__ import annotations

import bmesh
import bpy
import pytest

from .conftest import _load_addon_as_package

_QUAD_CORNERS = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 1.0), (0.0, 0.0, 1.0)]


@pytest.fixture
def addon() -> None:
    """Mount the addon and start from an empty file.

    Skips when the bundled ``proscenio_models`` predates the ``polygons``
    field - Blender installs the wheel from ``apps/blender/wheels/`` into an
    isolated site-packages, so a stale cached install would fail the emit
    rather than exercise it. Rebuild via
    ``uv build packages/models --wheel --out-dir apps/blender/wheels``.
    """
    _load_addon_as_package()
    from proscenio_models import MeshElement

    if "polygons" not in MeshElement.model_fields:
        pytest.skip("bundled proscenio_models predates the polygons field")
    bpy.ops.wm.read_homefile(use_empty=True)


def _new_mesh_object(name: str, faces: list[tuple[int, ...]]) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new(co) for co in _QUAD_CORNERS]
    for face in faces:
        bm.faces.new([verts[i] for i in face])
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def test_multi_face_mesh_exports_every_face(addon: None) -> None:
    from proscenio.exporters.godot.writer.sprites import build_element

    # Quad split into two triangles sharing the 0->2 diagonal.
    obj = _new_mesh_object("blob", [(0, 1, 2), (0, 2, 3)])
    element = build_element(obj, {}, ppu=100.0)

    assert element.type == "mesh"
    assert len(element.polygon) == 4  # all four unique verts, not the first three
    assert element.polygons == [[0, 1, 2], [0, 2, 3]]


def test_single_face_mesh_omits_polygons(addon: None) -> None:
    from proscenio.exporters.godot.writer.sprites import build_element

    obj = _new_mesh_object("quad", [(0, 1, 2, 3)])
    element = build_element(obj, {}, ppu=100.0)

    assert len(element.polygon) == 4
    assert element.polygons is None  # single face keeps the field-less shape


def _rotated_bone_rig() -> tuple[bpy.types.Object, dict]:
    """A one-bone rig whose bone points +Z (Godot rest rotation -90) plus its
    world dict, so a bone-local bake visibly rotates the polygon off absolute."""
    from proscenio.exporters.godot.writer.skeleton import compute_bone_world_godot

    arm_data = bpy.data.armatures.new("rig")
    arm = bpy.data.objects.new("rig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm_data.edit_bones.new("b")
    eb.head = (0.5, 0.0, 0.5)
    eb.tail = (0.5, 0.0, 1.5)  # +Z: in-plane bone, rest rotation -90 in Godot
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm, compute_bone_world_godot(arm, 100.0)


def _bind_constraint(obj: bpy.types.Object, arm: bpy.types.Object, bone: str) -> None:
    con = obj.constraints.new(type="CHILD_OF")
    con.name = "Proscenio Sprite Follow"
    con.target = arm
    con.subtarget = bone


def test_slot_attachment_mesh_bakes_absolute_not_bone_local(addon: None) -> None:
    # A rigid mesh that is a slot attachment (parent is a slot Empty) imports
    # under the slot Node2D, not the Bone2D - so even with a bone follow it must
    # bake ABSOLUTE, matching a plain object-parented mesh, never bone-local.
    from proscenio.exporters.godot.writer.sprites import build_element

    arm, world = _rotated_bone_rig()

    reference = _new_mesh_object("ref", [(0, 1, 2, 3)])  # object-parented, no bone
    reference_poly = build_element(reference, world, ppu=100.0).polygon

    slot = bpy.data.objects.new("hand.slot", None)
    bpy.context.scene.collection.objects.link(slot)
    slot.proscenio.is_slot = True
    attachment = _new_mesh_object("club", [(0, 1, 2, 3)])
    attachment.parent = slot
    _bind_constraint(attachment, arm, "b")

    bound = _new_mesh_object("free", [(0, 1, 2, 3)])  # bone-bound, NOT in a slot
    _bind_constraint(bound, arm, "b")

    attachment_poly = build_element(attachment, world, ppu=100.0).polygon
    bound_poly = build_element(bound, world, ppu=100.0).polygon

    # The slot attachment bakes absolute (identical to the object-only reference);
    # the non-slot bone-bound mesh bakes bone-local, which the +Z bone rotates
    # off the absolute coordinates.
    assert attachment_poly == reference_poly
    assert bound_poly != reference_poly
