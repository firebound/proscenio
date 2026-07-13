"""Pure-pytest unit tests for the slot writer walker.

The bpy substitute in conftest lets the module import. The schema-shaped
projection lives in ``core.slot.slot_emit`` (covered separately); these
tests drive the Blender-data walk - the Empty filter, the flag reads, and
the mesh-attachment collection - with hand-built fakes.
"""

from __future__ import annotations

from types import SimpleNamespace

from blender.core._shared.action_fcurves import (
    object_action_fcurves,
    object_fcurves_in_action,
)
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


def _follow_con(bone: str, name: str = "Proscenio Slot Follow") -> SimpleNamespace:
    return SimpleNamespace(name=name, type="CHILD_OF", subtarget=bone)


def test_build_slots_bone_resolves_constraint_first() -> None:
    # Spec 080 D5: the Proscenio Child Of IS the binding - it wins over both
    # the legacy slot_bone field and a raw bone parent.
    slot_empty = _slot_empty(
        "hand.swap",
        is_slot=True,
        bone="stale_parent",
        children=(_mesh_child("club"),),
    )
    slot_empty.constraints = [_follow_con("arm")]
    slot_empty.proscenio.slot_bone = "stale_field"
    scene = SimpleNamespace(objects=[slot_empty])
    out = slots.build_slots_for_scene(scene)
    assert out[0].bone == "arm"


def test_build_slots_bone_falls_back_to_legacy_field_then_parent() -> None:
    # Pre-080 file: no constraint - the slot_bone field still exports.
    with_field = _slot_empty("a.swap", is_slot=True, children=(_mesh_child("a"),))
    with_field.proscenio.slot_bone = "arm"
    # Older still: only a raw bone parent.
    with_parent = _slot_empty(
        "b.swap", is_slot=True, bone="head", children=(_mesh_child("b"),)
    )
    scene = SimpleNamespace(objects=[with_field, with_parent])
    out = slots.build_slots_for_scene(scene)
    assert out[0].bone == "arm"
    assert out[1].bone == "head"


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
# cross-read. The walker iterates EVERY action, so one attachment keyed across
# several animations exports a distinct timeline per animation (the spec's core).


def _hide_render_curve(points: list[tuple[float, float]]) -> SimpleNamespace:
    """A ``hide_render`` fcurve fake; ``points`` are ``(frame, value)`` (1.0 = hidden)."""
    kps = [SimpleNamespace(co=SimpleNamespace(x=f, y=v)) for f, v in points]
    return SimpleNamespace(data_path="hide_render", keyframe_points=kps)


def _object_slot(mesh_name: str, handle: int) -> SimpleNamespace:
    """A 4.4+ Object action-slot fake, identified by the mesh name like Blender."""
    return SimpleNamespace(
        target_id_type="OBJECT",
        name_display=mesh_name,
        identifier=f"OB{mesh_name}",
        handle=handle,
    )


def _slotted_action(
    name: str,
    frame_range: tuple[float, float],
    spec: dict[str, tuple[int, list[tuple[float, float]]]],
) -> SimpleNamespace:
    """One 4.4+ slotted action datablock; ``spec`` maps mesh name -> (handle, points).

    Builds the real Blender shape: an ``action.slots`` collection (each slot an
    Object slot identified by the mesh name) plus one channelbag per slot keyed
    by ``slot_handle``. A flattened read would see every channelbag per mesh;
    scoped reading matches the slot by identity and sees one each.
    """
    slots_out = []
    channelbags = []
    for mesh_name, (handle, points) in spec.items():
        slots_out.append(_object_slot(mesh_name, handle))
        channelbags.append(
            SimpleNamespace(slot_handle=handle, fcurves=[_hide_render_curve(points)])
        )
    strip = SimpleNamespace(channelbags=channelbags)
    return SimpleNamespace(
        name=name,
        fcurves=[],
        slots=slots_out,
        layers=[SimpleNamespace(strips=[strip])],
        frame_range=frame_range,
    )


def _slotted_action_two_meshes() -> SimpleNamespace:
    """One slotted ``swing`` action: club (handle 1) shown, sword (handle 2) hidden."""
    return _slotted_action(
        "swing",
        (1.0, 1.0),
        {"club": (1, [(1.0, 0.0)]), "sword": (2, [(1.0, 1.0)])},
    )


def _mesh_on_slot(name: str, action: SimpleNamespace, handle: int) -> _Obj:
    return _Obj(
        name=name,
        type="MESH",
        animation_data=SimpleNamespace(
            action=action, action_slot=SimpleNamespace(handle=handle)
        ),
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


def test_object_action_fcurves_yields_nothing_when_layered_but_no_slot() -> None:
    # A mesh bound to a layered (4.4+) action but with no action_slot has no slot
    # handle to match on. It must yield NOTHING, not flatten every channelbag -
    # otherwise a slot writer processing one mesh would read every sibling's
    # visibility curves (spec 079 R4).
    action = _slotted_action_two_meshes()  # two channelbags: club (1), sword (2)
    orphan = _Obj(
        name="club",
        type="MESH",
        animation_data=SimpleNamespace(action=action, action_slot=None),
    )
    assert list(object_action_fcurves(orphan)) == []


def test_object_fcurves_in_action_reads_a_non_active_action_by_slot_identity() -> None:
    # club's ACTIVE action is `attack`, but its visibility in `idle` lives in the
    # idle datablock's slot. Scoped-by-identity reading must reach it even though
    # club is not actively bound to idle - the crux of multi-animation export.
    idle = _slotted_action("idle", (1.0, 1.0), {"club": (10, [(1.0, 1.0)])})
    attack = _slotted_action("attack", (1.0, 1.0), {"club": (20, [(1.0, 0.0)])})
    club = _Obj(name="club", type="MESH", animation_data=SimpleNamespace(action=attack))
    seen = [
        [(kp.co.x, kp.co.y) for kp in fc.keyframe_points]
        for fc in object_fcurves_in_action(club, idle)
    ]
    assert seen == [[(1.0, 1.0)]]  # hidden in idle, read from the non-active action


def test_object_fcurves_in_action_flat_action_only_for_its_active_binder() -> None:
    # A legacy 4.2 flat action has no slot identity; it belongs to its active
    # binder. A sibling not bound to it must read nothing (no cross-read).
    flat = SimpleNamespace(name="idle", fcurves=[_hide_render_curve([(1.0, 0.0)])])
    owner = _Obj(name="club", type="MESH", animation_data=SimpleNamespace(action=flat))
    stranger = _Obj(
        name="torch", type="MESH", animation_data=SimpleNamespace(action=None)
    )
    assert [fc.data_path for fc in object_fcurves_in_action(owner, flat)] == [
        "hide_render"
    ]
    assert list(object_fcurves_in_action(stranger, flat)) == []


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


def _patch_actions(monkeypatch: object, actions: list[SimpleNamespace]) -> None:
    """Point the walker's ``iter_actions`` at ``actions`` (the file's action set)."""
    monkeypatch.setattr(slot_animations, "iter_actions", lambda: iter(actions))  # type: ignore[attr-defined]


def test_build_slot_animations_does_not_cross_read_a_shared_slotted_action(
    monkeypatch: object,
) -> None:
    action = _slotted_action_two_meshes()
    club = _mesh_on_slot("club", action, handle=1)
    sword = _mesh_on_slot("sword", action, handle=2)
    empty = _slot_empty("weapon", is_slot=True, children=(club, sword))
    scene = SimpleNamespace(objects=[empty], render=SimpleNamespace(fps=24))
    _patch_actions(monkeypatch, [action])
    anims = slot_animations.build_slot_animations(scene)
    assert len(anims) == 1
    assert anims[0].name == "swing"
    keys = anims[0].tracks[0].keys
    # Frame 1: club shown, sword hidden -> a single "club" key, not a double count.
    assert [k.attachment for k in keys] == ["club"]


def test_build_slot_animations_emits_one_animation_per_action(
    monkeypatch: object,
) -> None:
    # The spec's core: one attachment keyed across two animations exports a
    # distinct slot_attachment timeline per animation. `idle` hides both weapons
    # (-> "(none)"); `attack` shows the club.
    idle = _slotted_action(
        "idle", (1.0, 1.0), {"club": (1, [(1.0, 1.0)]), "torch": (2, [(1.0, 1.0)])}
    )
    attack = _slotted_action(
        "attack", (1.0, 12.0), {"club": (3, [(1.0, 0.0)]), "torch": (4, [(1.0, 1.0)])}
    )
    # Each mesh actively binds only one action (attack, the last authored); the
    # idle timeline is reachable only by scanning every action by slot identity.
    club = _Obj(name="club", type="MESH", animation_data=SimpleNamespace(action=attack))
    torch = _Obj(
        name="torch", type="MESH", animation_data=SimpleNamespace(action=attack)
    )
    empty = _slot_empty("weapon", is_slot=True, children=(club, torch))
    scene = SimpleNamespace(objects=[empty], render=SimpleNamespace(fps=24))
    _patch_actions(monkeypatch, [idle, attack])

    anims = slot_animations.build_slot_animations(scene)
    by_name = {a.name: a for a in anims}
    assert set(by_name) == {"idle", "attack"}
    idle_keys = by_name["idle"].tracks[0].keys
    attack_keys = by_name["attack"].tracks[0].keys
    assert [k.attachment for k in idle_keys] == [slot_animations.NONE_ATTACHMENT]
    assert [k.attachment for k in attack_keys] == ["club"]
