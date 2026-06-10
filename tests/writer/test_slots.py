"""Pure-pytest unit tests for the slot writer walker.

The bpy substitute in conftest lets the module import. The schema-shaped
projection lives in ``core.slot.slot_emit`` (covered separately); these
tests drive the Blender-data walk - the Empty filter, the flag reads, and
the mesh-attachment collection - with hand-built fakes.
"""

from __future__ import annotations

from types import SimpleNamespace

from blender.core.slot import slot_emit
from blender.exporters.godot.writer import slots


def _mesh_child(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, type="MESH")


def _slot_empty(
    name: str,
    *,
    is_slot: bool,
    slot_default: str = "",
    bone: str = "",
    children: tuple[SimpleNamespace, ...] = (),
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        type="EMPTY",
        parent_type="BONE" if bone else "OBJECT",
        parent_bone=bone,
        children=list(children),
        proscenio=SimpleNamespace(is_slot=is_slot, slot_default=slot_default),
    )


def test_is_slot_empty_reads_pg_flag() -> None:
    yes = SimpleNamespace(type="EMPTY", proscenio=SimpleNamespace(is_slot=True))
    no = SimpleNamespace(type="EMPTY", proscenio=SimpleNamespace(is_slot=False))
    not_empty = SimpleNamespace(type="MESH", proscenio=SimpleNamespace(is_slot=True))
    assert slot_emit.is_slot_empty(yes) is True
    assert slot_emit.is_slot_empty(no) is False
    assert slot_emit.is_slot_empty(not_empty) is False


def test_read_slot_default_from_pg() -> None:
    obj = SimpleNamespace(proscenio=SimpleNamespace(slot_default="open"))
    assert slots.read_slot_default(obj) == "open"


def test_read_slot_default_empty_when_absent() -> None:
    obj = SimpleNamespace(proscenio=SimpleNamespace(slot_default=""))
    assert slots.read_slot_default(obj) == ""


def test_build_slots_for_scene_collects_mesh_attachments() -> None:
    slot_empty = _slot_empty(
        "brow.swap",
        is_slot=True,
        slot_default="brow.up",
        bone="head",
        children=(
            _mesh_child("brow.up"),
            _mesh_child("brow.down"),
            SimpleNamespace(name="rim_light", type="LIGHT"),
        ),
    )
    scene = SimpleNamespace(objects=[slot_empty])
    out = slots.build_slots_for_scene(scene)
    assert len(out) == 1
    assert out[0].name == "brow.swap"
    assert out[0].bone == "head"
    assert out[0].attachments == ["brow.up", "brow.down"]
    assert out[0].default == "brow.up"


def test_build_slots_for_scene_skips_non_slot_and_non_empty() -> None:
    non_slot = _slot_empty("plain", is_slot=False)
    a_mesh = SimpleNamespace(name="body", type="MESH", proscenio=SimpleNamespace(is_slot=True))
    scene = SimpleNamespace(objects=[non_slot, a_mesh])
    assert slots.build_slots_for_scene(scene) == []
