"""Headless test for mixed-flow auto-snapshot.

Covers the gap where users bind via Ctrl+P Armature Auto Weights (no
proscenio_weight_sidecar written) and then trigger an automesh regen.
Without the fallback, the regen wiped all weights silently.
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


def test_native_ctrlp_bind_then_automesh_regen_preserves_weights(automesh_fixture):
    """Mixed flow: Blender native bind (no sidecar) + automesh regen
    must preserve weights via on-the-fly sidecar build.
    """
    obj = _activate("hand")
    bpy.context.scene.proscenio.active_armature = bpy.data.objects["automesh.hand_rig"]
    bpy.context.scene.proscenio.skinning.preserve_on_regen = True
    # Clear any sidecar the fixture may have stamped.
    if "proscenio_weight_sidecar" in obj:
        del obj["proscenio_weight_sidecar"]
    # Assign weights to vertex groups manually, mimicking bone-heat bind.
    rig = bpy.data.objects["automesh.hand_rig"]
    for bone in rig.data.bones:
        if bone.name not in obj.vertex_groups:
            obj.vertex_groups.new(name=bone.name)
        for vert in list(obj.data.vertices)[:3]:
            obj.vertex_groups[bone.name].add([vert.index], 1.0, "REPLACE")
    # Run automesh regen - should reproject via on-the-fly sidecar.
    bpy.ops.proscenio.automesh_from_alpha(resolution=0.25)
    # After regen, vertex_groups must still have weights (NOT empty).
    total_assigned = 0
    for vert in obj.data.vertices:
        for vg in obj.vertex_groups:
            try:
                w = vg.weight(vert.index)
                if w > 1e-6:
                    total_assigned += 1
            except RuntimeError:
                continue
    assert total_assigned > 0, "weights lost during regen - mixed-flow auto-snapshot failed"
