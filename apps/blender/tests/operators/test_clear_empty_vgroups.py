"""Headless tests for the clear-empty-vertex-groups operator (spec 044)."""

from __future__ import annotations

import bpy


def _activate(name: str) -> bpy.types.Object:
    obj = bpy.data.objects[name]
    bpy.context.view_layer.objects.active = obj
    for other in bpy.context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    return obj


def test_clear_empty_vgroups_removes_only_empty(automesh_fixture):
    obj = _activate("hand")
    # A guaranteed-weighted group must survive; a guaranteed-empty one must go.
    keep = obj.vertex_groups.new(name="keep_me")
    keep.add([0], 0.5, "REPLACE")
    obj.vertex_groups.new(name="drop_me")  # no weights -> empty

    result = bpy.ops.proscenio.clear_empty_vertex_groups()

    assert "FINISHED" in result
    names = {vg.name for vg in obj.vertex_groups}
    assert "keep_me" in names, "a group with a nonzero weight must not be removed"
    assert "drop_me" not in names, "a group with no nonzero weight must be removed"


def test_clear_empty_vgroups_cancels_when_none_empty(automesh_fixture):
    obj = _activate("hand")
    # Strip to a single weighted group so nothing is empty.
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)
    only = obj.vertex_groups.new(name="only_weighted")
    only.add([0], 1.0, "REPLACE")

    result = bpy.ops.proscenio.clear_empty_vertex_groups()

    assert "CANCELLED" in result, "nothing to clear should cancel, not delete"
    assert {vg.name for vg in obj.vertex_groups} == {"only_weighted"}


def test_clear_empty_vgroups_poll_requires_groups(automesh_fixture):
    obj = _activate("hand")
    for vg in list(obj.vertex_groups):
        obj.vertex_groups.remove(vg)

    assert bpy.ops.proscenio.clear_empty_vertex_groups.poll() is False
