"""Headless tests for the named weight-snapshot operators.

Runs INSIDE Blender via ``run_operator_tests.py``. Covers the spec 049 named
save points: save the current weights under a name, then restore them by name
after the weights are mutated. The rolling-auto cap is covered purely in
``tests/skinning/test_named_snapshots.py``.
"""

from __future__ import annotations

import bpy
import pytest


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def _set_picker(name: str) -> None:
    bpy.context.scene.proscenio.active_armature = bpy.data.objects[name]


def _first_wrist_weight(obj: bpy.types.Object) -> float:
    wrist = obj.vertex_groups["wrist"]
    for vert in obj.data.vertices:
        for elem in vert.groups:
            if elem.group == wrist.index and elem.weight > 0.0:
                return float(elem.weight)
    return 0.0


def _bound_hand() -> bpy.types.Object:
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    bpy.ops.proscenio.bind_mesh_to_armature()
    return obj


def test_save_then_restore_named_snapshot(automesh_fixture):
    obj = _bound_hand()
    original = _first_wrist_weight(obj)
    assert original > 0.0

    result = bpy.ops.proscenio.save_weight_snapshot(snapshot_name="pose-a")
    assert "FINISHED" in result

    # Mutate: zero the wrist group on every vert.
    wrist = obj.vertex_groups["wrist"]
    for vert in obj.data.vertices:
        wrist.add([vert.index], 0.0, "REPLACE")
    assert abs(_first_wrist_weight(obj)) < 1e-9

    result = bpy.ops.proscenio.restore_named_snapshot(snapshot_name="pose-a")
    assert "FINISHED" in result
    assert abs(_first_wrist_weight(obj) - original) < 1e-3


def test_saved_snapshot_is_listed(automesh_fixture):
    from proscenio.core.bpy_helpers.skinning import read_snapshots

    obj = _bound_hand()
    bpy.ops.proscenio.save_weight_snapshot(snapshot_name="pose-a")

    listed = read_snapshots(obj)
    assert [(s.name, s.kind) for s in listed] == [("pose-a", "manual")]


def test_append_auto_snapshot_adds_when_topology_matches(automesh_fixture):
    from proscenio.core.bpy_helpers.skinning import append_auto_snapshot, read_snapshots

    obj = _bound_hand()

    assert append_auto_snapshot(obj, bpy.data.objects["automesh.hand_rig"]) is True
    autos = [s for s in read_snapshots(obj) if s.kind == "auto"]
    assert len(autos) == 1


def test_append_auto_snapshot_skips_on_topology_drift(automesh_fixture):
    import bmesh
    from proscenio.core.bpy_helpers.skinning import append_auto_snapshot, read_snapshots

    obj = _bound_hand()
    # Drift the topology without refreshing the sidecar hash (the no-preserve regen
    # case): an auto-snapshot stored now could not be restored later, so it must skip.
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.new((9.0, 9.0, 9.0))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    assert append_auto_snapshot(obj, bpy.data.objects["automesh.hand_rig"]) is False
    assert [s for s in read_snapshots(obj) if s.kind == "auto"] == []


def test_save_snapshot_cancels_on_topology_drift(automesh_fixture):
    import bmesh

    obj = _bound_hand()
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.new((9.0, 9.0, 9.0))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    # Saving against a stale-hash sidecar would produce a snapshot restore always
    # rejects, so the save is refused with a re-bind hint.
    with pytest.raises(RuntimeError, match="topology changed since bind"):
        bpy.ops.proscenio.save_weight_snapshot(snapshot_name="late")


def test_restore_named_snapshot_uses_its_own_groups_not_baseline(automesh_fixture):
    """A named snapshot stores only its per-vert entries, not its own group names.
    Restore must recreate the groups the snapshot's weights actually reference -
    not the live baseline's names, which a re-bind under a renamed deform bone
    moves out from under the snapshot. Using the baseline names there recreates
    the wrong (renamed) groups and silently drops every snapshot weight."""
    import json

    obj = _bound_hand()
    original = _first_wrist_weight(obj)
    assert original > 0.0
    bpy.ops.proscenio.save_weight_snapshot(snapshot_name="pose-a")

    # Stand in for a re-bind after a deform-bone rename (same topology): the
    # baseline's vertex_group_names drift to renamed bones while the saved
    # snapshot's entries keep the original bone keys.
    payload = json.loads(obj["proscenio_weight_sidecar"])
    payload["vertex_group_names"] = [f"{n}_renamed" for n in payload["vertex_group_names"]]
    obj["proscenio_weight_sidecar"] = json.dumps(payload)

    # Mutate live weights so the restore has to do real work.
    wrist = obj.vertex_groups["wrist"]
    for vert in obj.data.vertices:
        wrist.add([vert.index], 0.0, "REPLACE")

    result = bpy.ops.proscenio.restore_named_snapshot(snapshot_name="pose-a")
    assert "FINISHED" in result
    kept_snapshot_group = "wrist" in obj.vertex_groups
    assert kept_snapshot_group, "restore used baseline names, dropping the snapshot's groups"
    assert abs(_first_wrist_weight(obj) - original) < 1e-3


def test_restore_unknown_name_cancels(automesh_fixture):
    _bound_hand()
    with pytest.raises(RuntimeError, match="no snapshot named"):
        bpy.ops.proscenio.restore_named_snapshot(snapshot_name="does-not-exist")


def test_save_empty_name_cancels(automesh_fixture):
    _bound_hand()
    with pytest.raises(RuntimeError, match="name cannot be empty"):
        bpy.ops.proscenio.save_weight_snapshot(snapshot_name="   ")
