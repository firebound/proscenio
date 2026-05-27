"""Headless: copy_weights_to_selected operator (O7)."""
from __future__ import annotations

import bpy


def test_copy_weights_to_selected_duplicate_mesh(automesh_fixture):
    """Source mesh painted; target mesh receives weights via copy operator."""
    src = bpy.data.objects["hand"]
    # Bind source to armature so it has vertex groups
    bpy.context.scene.proscenio.active_armature = bpy.data.objects["automesh.hand_rig"]
    bpy.context.view_layer.objects.active = src
    for other in bpy.context.selected_objects:
        other.select_set(False)
    src.select_set(True)
    bpy.ops.proscenio.bind_mesh_to_armature()
    assert len(src.vertex_groups) > 0
    # Duplicate the mesh (same world position - guarantees nearest-vert match)
    new_mesh = src.data.copy()
    dup = bpy.data.objects.new("hand_target", new_mesh)
    bpy.context.scene.collection.objects.link(dup)
    dup.location = src.location  # same position so nearest is straightforward
    # Select both, with src active (= source)
    for other in bpy.context.selected_objects:
        other.select_set(False)
    src.select_set(True)
    dup.select_set(True)
    bpy.context.view_layer.objects.active = src
    # Run the operator
    bpy.ops.proscenio.copy_weights_to_selected(max_distance=1.0)
    # Verify dup has vertex groups now
    assert len(dup.vertex_groups) > 0, "target missing vertex groups after copy"
    # At least some verts in dup should have weights
    weighted_verts = 0
    for vert in dup.data.vertices:
        for vg in dup.vertex_groups:
            try:
                if vg.weight(vert.index) > 1e-6:
                    weighted_verts += 1
                    break
            except RuntimeError:
                continue
    assert weighted_verts > 0, "no verts received weights from copy"
