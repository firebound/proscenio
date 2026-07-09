"""Pure-pytest unit tests for the slot writer walker.

The bpy substitute in conftest lets the module import. The schema-shaped
projection lives in ``core.slot.slot_emit`` (covered separately); these
tests drive the Blender-data walk - the Empty filter, the flag reads, and
the mesh-attachment collection - with hand-built fakes.
"""

from __future__ import annotations

from types import SimpleNamespace

from blender.core._shared.action_fcurves import object_action_fcurves
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


# -- visibility-driven slot_attachment collapse (spec 079) --------------------
#
# The writer reads each attachment mesh's own ``hide_render`` keyframes and
# collapses them per frame into one exclusive key: 0 visible -> "(none)"; 1 ->
# that attachment; 2+ -> first in child order. Per-mesh reading is scoped to the
# mesh's own action slot so siblings sharing a 4.4+ slotted action never
# cross-read.


def _hide_render_curve(points: list[tuple[float, float]]) -> SimpleNamespace:
    """A ``hide_render`` fcurve fake; ``points`` are ``(frame, value)`` (1.0 = hidden)."""
    kps = [SimpleNamespace(co=SimpleNamespace(x=f, y=v)) for f, v in points]
    return SimpleNamespace(data_path="hide_render", keyframe_points=kps)


def _slotted_action_two_meshes() -> SimpleNamespace:
    """One 4.4+ slotted action datablock holding two meshes on distinct slots.

    Slot handle 1 (club) shown at frame 1; slot handle 2 (sword) hidden. A
    flattened read would see both curves per mesh; scoped reading sees one each.
    """
    club_cb = SimpleNamespace(slot_handle=1, fcurves=[_hide_render_curve([(1.0, 0.0)])])
    sword_cb = SimpleNamespace(slot_handle=2, fcurves=[_hide_render_curve([(1.0, 1.0)])])
    strip = SimpleNamespace(channelbags=[club_cb, sword_cb])
    return SimpleNamespace(
        name="swing", fcurves=[], layers=[SimpleNamespace(strips=[strip])], frame_range=(1.0, 1.0)
    )


def _mesh_on_slot(name: str, action: SimpleNamespace, handle: int) -> _Obj:
    return _Obj(
        name=name,
        type="MESH",
        animation_data=SimpleNamespace(action=action, action_slot=SimpleNamespace(handle=handle)),
    )


def test_object_action_fcurves_scopes_to_the_mesh_own_slot() -> None:
    action = _slotted_action_two_meshes()
    club = _mesh_on_slot("club", action, handle=1)
    seen = [
        (fc.data_path, [(kp.co.x, kp.co.y) for kp in fc.keyframe_points])
        for fc in object_action_fcurves(club)
    ]
    # Only club's own channelbag (handle 1), never sword's (handle 2).
    assert seen == [("hide_render", [(1.0, 0.0)])]


def test_collapse_single_visible_picks_that_attachment() -> None:
    track = slot_animations._build_slot_attachment_track(
        "weapon",
        ["club", "sword"],
        {"club": [(1.0, True), (12.0, False)], "sword": [(1.0, False), (12.0, True)]},
        fps=24,
    )
    assert track is not None
    assert [(k.time, k.attachment) for k in track.keys] == [
        (0.0, "club"),
        (0.458333, "sword"),
    ]
    assert all(k.interp == "constant" for k in track.keys)


def test_collapse_none_when_all_hidden() -> None:
    track = slot_animations._build_slot_attachment_track(
        "weapon",
        ["club", "sword"],
        {"club": [(1.0, False)], "sword": [(1.0, False)]},
        fps=24,
    )
    assert track is not None
    assert track.keys[0].attachment == slot_animations.NONE_ATTACHMENT


def test_collapse_two_visible_takes_first_in_child_order() -> None:
    track = slot_animations._build_slot_attachment_track(
        "weapon",
        ["club", "sword"],
        {"club": [(1.0, True)], "sword": [(1.0, True)]},
        fps=24,
    )
    assert track is not None
    assert track.keys[0].attachment == "club"  # order[0], deterministic


def test_build_slot_animations_does_not_cross_read_a_shared_slotted_action() -> None:
    action = _slotted_action_two_meshes()
    club = _mesh_on_slot("club", action, handle=1)
    sword = _mesh_on_slot("sword", action, handle=2)
    empty = _slot_empty("weapon", is_slot=True, children=(club, sword))
    scene = SimpleNamespace(objects=[empty], render=SimpleNamespace(fps=24))
    anims = slot_animations.build_slot_animations(scene)
    assert len(anims) == 1
    assert anims[0].name == "swing"
    keys = anims[0].tracks[0].keys
    # Frame 1: club shown, sword hidden -> a single "club" key, not a double count.
    assert [k.attachment for k in keys] == ["club"]
