"""Pure-pytest unit tests for the slot writer walker.

The bpy substitute in conftest lets the module import. The schema-shaped
projection lives in ``core.slot.slot_emit`` (covered separately); these
tests drive the Blender-data walk - the Empty filter, the flag reads, and
the mesh-attachment collection - with hand-built fakes.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from blender.core._shared.cp_keys import PROSCENIO_SLOT_ATTACHMENT_ORDER
from blender.core.slot import slot_emit
from blender.exporters.godot.writer import slot_animations, slots

# spec 037: the writer reads each per-Object field from its ``proscenio_*``
# Custom Property (idprop) via ``obj.get``. ``_Obj`` is a bpy-Object stand-in
# whose ``.get`` derives the idprop value from a ``proscenio=`` namespace, so
# the test data stays readable while exercising the real idprop read path.
_FIELD_TO_CP = {"element_type": "proscenio_type"}


def _cp_key(field: str) -> str:
    return _FIELD_TO_CP.get(field, f"proscenio_{field}")


class _Obj(SimpleNamespace):
    """A fake bpy Object: attribute access plus idprop-style ``.get``."""

    def get(self, key, default=None):  # noqa: ANN001, ANN201
        pg = getattr(self, "proscenio", None)
        if pg is None:
            return default
        for field, value in vars(pg).items():
            if _cp_key(field) == key:
                return value
        return default


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
    return _Obj(
        name=name,
        type="EMPTY",
        parent_type="BONE" if bone else "OBJECT",
        parent_bone=bone,
        children=list(children),
        proscenio=SimpleNamespace(is_slot=is_slot, slot_default=slot_default),
    )


def test_is_slot_empty_reads_pg_flag() -> None:
    yes = _Obj(type="EMPTY", proscenio=SimpleNamespace(is_slot=True))
    no = _Obj(type="EMPTY", proscenio=SimpleNamespace(is_slot=False))
    not_empty = _Obj(type="MESH", proscenio=SimpleNamespace(is_slot=True))
    assert slot_emit.is_slot_empty(yes) is True
    assert slot_emit.is_slot_empty(no) is False
    assert slot_emit.is_slot_empty(not_empty) is False


def test_read_slot_default_from_pg() -> None:
    obj = _Obj(proscenio=SimpleNamespace(slot_default="open"))
    assert slots.read_slot_default(obj) == "open"


def test_read_slot_default_empty_when_absent() -> None:
    obj = _Obj(proscenio=SimpleNamespace())
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
    a_mesh = _Obj(name="body", type="MESH", proscenio=SimpleNamespace(is_slot=True))
    scene = SimpleNamespace(objects=[non_slot, a_mesh])
    assert slots.build_slots_for_scene(scene) == []


# -- slot_attachment keyframe binding (O3: resolve the keyed index against the
#    snapshotted name order, not the live child list) --------------------------


class _SlotObj(SimpleNamespace):
    """A slot Empty stand-in with a dict-style ``.get`` over raw idprops."""

    def get(self, key, default=None):  # noqa: ANN001, ANN201
        return getattr(self, "_cps", {}).get(key, default)


def _mesh(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, type="MESH")


def test_resolve_attachment_order_prefers_the_snapshot() -> None:
    # The snapshot names survive a later child delete: live children shrank to
    # [axe] but the keyed index still resolves against the stored order.
    obj = _SlotObj(
        _cps={PROSCENIO_SLOT_ATTACHMENT_ORDER: json.dumps(["sword", "axe"])},
        children=[_mesh("axe")],
    )
    assert slot_animations._resolve_attachment_order(obj) == ("sword", "axe")


def test_resolve_attachment_order_falls_back_to_live_children() -> None:
    obj = _SlotObj(
        _cps={},
        children=[_mesh("a"), _mesh("b"), SimpleNamespace(name="cam", type="LIGHT")],
    )
    assert slot_animations._resolve_attachment_order(obj) == ("a", "b")


def test_resolve_attachment_order_falls_back_on_malformed_snapshot() -> None:
    corrupt = _SlotObj(
        _cps={PROSCENIO_SLOT_ATTACHMENT_ORDER: "{not json"}, children=[_mesh("a")]
    )
    non_list = _SlotObj(
        _cps={PROSCENIO_SLOT_ATTACHMENT_ORDER: json.dumps({"a": 1})},
        children=[_mesh("a")],
    )
    assert slot_animations._resolve_attachment_order(corrupt) == ("a",)
    assert slot_animations._resolve_attachment_order(non_list) == ("a",)


def test_build_slot_attachment_track_resolves_index_against_the_order() -> None:
    obj = _SlotObj(
        name="weapon",
        _cps={PROSCENIO_SLOT_ATTACHMENT_ORDER: json.dumps(["sword", "axe"])},
        children=[_mesh("axe")],  # sword deleted; only axe remains live
    )
    kp = SimpleNamespace(co=SimpleNamespace(x=5.0, y=1.0))  # index 1 at frame 5
    fcurve = SimpleNamespace(data_path='["proscenio_slot_index"]', keyframe_points=[kp])
    action = SimpleNamespace(fcurves=[fcurve], layers=[])
    track = slot_animations._build_slot_attachment_track(obj, action, fps=24)
    assert track is not None
    assert [k.attachment for k in track.keys] == ["axe"]  # order[1], not live[1]
    assert all(k.interp == "constant" for k in track.keys)


def test_build_slot_attachment_track_none_without_mesh_children() -> None:
    obj = _SlotObj(
        name="empty_slot", _cps={}, children=[SimpleNamespace(name="cam", type="LIGHT")]
    )
    action = SimpleNamespace(fcurves=[], layers=[])
    assert slot_animations._build_slot_attachment_track(obj, action, fps=24) is None
