"""Headless tests for the revert-to-plane operator (spec 071).

Rebuild the original imported quad from the placement tag + wipe the skinning /
authoring data, keeping the import identity + material. The no-placement element
warns and no-ops.
"""

from __future__ import annotations

import bpy


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def test_revert_rebuilds_quad_and_wipes_skinning(automesh_fixture):
    """A generated + weighted element with a placement tag reverts to a 4-vert /
    1-face quad; vertex groups + authoring strokes are gone; placement + material
    are kept."""
    obj = _activate("hand")
    # Preconditions: a placement tag (PSD-import identity), a deform group, and an
    # authoring-stroke CP standing in for the generated state revert must clear.
    obj["proscenio_import_placement"] = [2.0, 3.0, 0.0, 0.0]
    obj.vertex_groups.new(name="bone.001")
    obj["proscenio_user_strokes"] = "[]"
    obj["proscenio_manual_contour"] = "{}"
    mat_count = len(obj.data.materials)

    assert bpy.ops.proscenio.revert_to_plane() == {"FINISHED"}

    assert len(obj.data.vertices) == 4
    assert len(obj.data.polygons) == 1
    assert len(obj.vertex_groups) == 0
    assert "proscenio_user_strokes" not in obj
    assert "proscenio_manual_contour" not in obj
    assert "proscenio_import_placement" in obj  # import identity kept
    assert len(obj.data.materials) == mat_count  # image material rides along


def test_revert_warns_no_op_without_placement(automesh_fixture):
    """An element with no placement tag (incorporated / hand-built) has no
    original plane to rebuild: revert warns and leaves the mesh untouched."""
    obj = _activate("hand")
    if "proscenio_import_placement" in obj:
        del obj["proscenio_import_placement"]
    n_verts = len(obj.data.vertices)

    assert bpy.ops.proscenio.revert_to_plane() == {"CANCELLED"}
    assert len(obj.data.vertices) == n_verts  # untouched


def test_revert_to_plane_registered(automesh_fixture):
    assert hasattr(bpy.ops.proscenio, "revert_to_plane")
