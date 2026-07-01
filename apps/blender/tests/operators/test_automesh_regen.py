"""Headless tests for the automesh sidecar hook."""

from __future__ import annotations

import json

import bpy


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def _set_picker(name: str) -> None:
    bpy.context.scene.proscenio.active_armature = bpy.data.objects[name]


def _set_preserve(value: bool) -> None:
    bpy.context.scene.proscenio.skinning.preserve_on_regen = value


def _read_sidecar(obj: bpy.types.Object) -> dict:
    payload = obj.get("proscenio_weight_sidecar")
    assert payload is not None
    return json.loads(payload)


def _mark_all_entries_user_paint(obj: bpy.types.Object) -> None:
    """Stand in for a prior paint pass: tag every stored entry user_paint."""
    payload = json.loads(obj["proscenio_weight_sidecar"])
    for entry in payload["entries"]:
        entry["provenance"] = "user_paint"
    obj["proscenio_weight_sidecar"] = json.dumps(payload)


def _add_named_snapshot(obj: bpy.types.Object, name: str) -> None:
    """Stand in for a saved restore point: append a manual snapshot."""
    payload = json.loads(obj["proscenio_weight_sidecar"])
    payload.setdefault("snapshots", []).append(
        {"name": name, "kind": "manual", "entries": payload["entries"]}
    )
    obj["proscenio_weight_sidecar"] = json.dumps(payload)


def test_automesh_regen_preserves_user_paint_provenance(automesh_fixture):
    """A changed-topology regen must carry the painted-vs-auto provenance across
    the reproject, not flatten every vert to auto_seed/reprojected."""
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    # Bind first so the sidecar has populated entries to snapshot.
    bpy.ops.proscenio.bind_mesh_to_armature()
    pre = _read_sidecar(obj)
    assert len(pre["entries"]) > 0
    _mark_all_entries_user_paint(obj)  # the artist painted these weights
    # Regen with a different resolution to force topology change.
    bpy.ops.proscenio.automesh_from_alpha(resolution=0.5)
    post = _read_sidecar(obj)
    # Post-regen sidecar must have entries equal to new vert count.
    assert len(post["entries"]) == len(obj.data.vertices)
    provenances = {entry["provenance"] for entry in post["entries"]}
    assert "user_paint" in provenances, "regen demoted painted weights, losing their provenance"


def test_noop_regen_preserves_user_paint_and_snapshots(automesh_fixture):
    """An identical-topology no-op regen must NOT discard the per-vert provenance
    or the saved weight snapshots. The pre-regen snapshot rebuilt a flat
    auto_seed sidecar with an empty snapshots list, so even a no-op regen wiped
    both."""
    from proscenio.core.bpy_helpers.skinning.automesh_hook import (  # type: ignore[import-not-found]
        maybe_post_regen_reproject,
        maybe_pre_regen_snapshot,
    )

    obj = _activate("hand")
    armature = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    bpy.ops.proscenio.bind_mesh_to_armature()
    _mark_all_entries_user_paint(obj)
    _add_named_snapshot(obj, "before tweak")

    # Drive the hook directly with no mesh change in between -> identical topology.
    prior = maybe_pre_regen_snapshot(obj, armature)
    assert prior is not None
    counters = maybe_post_regen_reproject(obj, armature, prior)
    assert counters["topology_changed"] == 0, "expected an identical-topology no-op regen"

    post = _read_sidecar(obj)
    provenances = {entry["provenance"] for entry in post["entries"]}
    assert "user_paint" in provenances, "no-op regen lost the painted provenance"
    names = [s["name"] for s in post["snapshots"]]
    assert names == ["before tweak"], "no-op regen dropped the saved snapshots"


def test_changed_topology_regen_reprojects_snapshots(automesh_fixture):
    """A topology-changing regen must REPROJECT carried snapshots onto the new
    topology, not carry the old-topology entries raw. A raw carry leaves stale
    entries on a sidecar stamped with the new hash, and a later restore (which
    guards only on the top-level hash) applies them by index = scrambled weights."""
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    bpy.ops.proscenio.bind_mesh_to_armature()
    _add_named_snapshot(obj, "before tweak")
    old_entry_count = len(_read_sidecar(obj)["entries"])
    # Regen at a different resolution -> new topology, new vert count.
    bpy.ops.proscenio.automesh_from_alpha(resolution=0.5)
    post = _read_sidecar(obj)
    new_vert_count = len(obj.data.vertices)
    assert new_vert_count != old_entry_count, "test needs a real topology change"
    names = [s["name"] for s in post["snapshots"]]
    assert names == ["before tweak"], "regen dropped the saved snapshot"
    snap_entry_count = len(post["snapshots"][0]["entries"])
    assert snap_entry_count == new_vert_count, "snapshot not reprojected to the new topology"


def _make_other_rig(name: str, bone_name: str) -> bpy.types.Object:
    """A second armature with a single deform bone of a distinct name.

    Stands in for the picker being switched to a different rig between bind and
    regen: its deform-bone names share nothing with the bound sidecar's keys.
    """
    arm = bpy.data.armatures.new(f"{name}_data")
    obj = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bone = arm.edit_bones.new(bone_name)
    edit_bone.head = (0.0, 0.0, 0.0)
    edit_bone.tail = (0.0, 0.0, 1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def test_regen_under_a_switched_rig_flags_the_mismatch(automesh_fixture):
    """Binding to rig A then regenerating under rig B must NOT silently claim the
    weights were preserved: rig B has none of A's bone groups, so the carried
    entries (keyed by A's bones) would orphan to a weightless mesh. The hook must
    flag the divergence so the caller can warn instead of lying about preserve."""
    from proscenio.core.bpy_helpers.skinning.automesh_hook import (  # type: ignore[import-not-found]
        maybe_post_regen_reproject,
        maybe_pre_regen_snapshot,
    )

    obj = _activate("hand")
    rig_a = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    bpy.ops.proscenio.bind_mesh_to_armature()  # entries keyed by rig A's deform bones
    rig_b = _make_other_rig("regen.other_rig", "zz_unrelated_bone")

    prior = maybe_pre_regen_snapshot(obj, rig_a)
    assert prior is not None
    counters = maybe_post_regen_reproject(obj, rig_b, prior)
    assert counters["rig_mismatch"] == 1, "rig switch not flagged - weights orphan silently"


def test_corrupt_sidecar_regen_warns_provenance_loss(automesh_fixture):
    """When the existing sidecar is corrupt, the pre-regen snapshot falls back to
    rebuilding from live vgroups - which loses the painted-vs-auto provenance the
    corrupt CP carried. That loss must be surfaced as a WARNING, not swallowed."""
    from types import SimpleNamespace

    from proscenio.core.bpy_helpers.skinning.automesh_hook import (  # type: ignore[import-not-found]
        maybe_pre_regen_snapshot,
    )

    obj = _activate("hand")
    armature = bpy.data.objects["automesh.hand_rig"]
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    bpy.ops.proscenio.bind_mesh_to_armature()
    _mark_all_entries_user_paint(obj)  # there WAS painted provenance to lose
    obj["proscenio_weight_sidecar"] = "{ not valid sidecar json"  # now unrecoverable

    reports: list[tuple[tuple[str, ...], str]] = []
    op = SimpleNamespace(report=lambda level, msg: reports.append((tuple(level), msg)))
    prior = maybe_pre_regen_snapshot(obj, armature, op=op)
    assert prior is not None, "fallback should still snapshot the live vgroup weights"
    warned = any("WARNING" in level for level, _ in reports)
    assert warned, "corrupt-sidecar provenance loss was not surfaced as a warning"


def test_automesh_regen_with_preserve_off_skips_hook(automesh_fixture):
    obj = _activate("hand")
    _set_picker("automesh.hand_rig")
    _set_preserve(True)
    bpy.ops.proscenio.bind_mesh_to_armature()
    pre_hash = _read_sidecar(obj)["mesh_topology_hash"]
    # Turn the auto-flow off, then regen with a forcing parameter change.
    _set_preserve(False)
    bpy.ops.proscenio.automesh_from_alpha(resolution=0.5)
    post = _read_sidecar(obj)
    # With preserve OFF, hook is no-op: sidecar stays from BEFORE the regen
    # (the operator did not re-stamp; topology hash points to OLD topology).
    assert post["mesh_topology_hash"] == pre_hash
