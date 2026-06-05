"""Unit tests for the slot system slot emission helpers.

Pure pytest, no Blender. Covers the bpy-free projection from
``SlotInput`` records into the typed ``Slot`` pydantic models the
writer emits.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.slot.slot_emit import SlotInput, build_slot, build_slots  # noqa: E402


def test_minimal_slot_emits_name_and_attachments() -> None:
    slot = build_slot(
        SlotInput(name="eye.swap", bone="", slot_default="", attachments=("a", "b"))
    )
    assert slot.name == "eye.swap"
    assert slot.attachments == ["a", "b"]
    assert slot.default == "a"  # falls back to sorted-first
    assert slot.bone is None


def test_explicit_default_overrides_sorted_fallback() -> None:
    slot = build_slot(
        SlotInput(name="s", bone="", slot_default="b", attachments=("a", "b"))
    )
    assert slot.default == "b"


def test_invalid_default_falls_back_to_sorted_first() -> None:
    """Dangling slot_default (names a child that no longer exists) does not
    block emission - the writer still ships a usable default; the panel
    surfaces the broken reference via the validation pass."""
    slot = build_slot(
        SlotInput(name="s", bone="", slot_default="zzz_missing", attachments=("b", "a"))
    )
    assert slot.default == "a"


def test_bone_emitted_only_when_set() -> None:
    with_bone = build_slot(
        SlotInput(name="s", bone="forearm.L", slot_default="", attachments=("a",))
    )
    no_bone = build_slot(
        SlotInput(name="s", bone="", slot_default="", attachments=("a",))
    )
    assert with_bone.bone == "forearm.L"
    assert no_bone.bone is None


def test_empty_attachments_omits_default() -> None:
    slot = build_slot(
        SlotInput(name="s", bone="", slot_default="", attachments=())
    )
    assert slot.attachments == []
    assert slot.default is None


def test_attachments_preserve_input_order() -> None:
    slot = build_slot(
        SlotInput(name="s", bone="", slot_default="", attachments=("c", "a", "b"))
    )
    assert slot.attachments == ["c", "a", "b"]


def test_build_slots_sorts_by_name_for_deterministic_output() -> None:
    out = build_slots(
        [
            SlotInput(name="zee", bone="", slot_default="", attachments=("a",)),
            SlotInput(name="aaa", bone="", slot_default="", attachments=("a",)),
            SlotInput(name="middle", bone="", slot_default="", attachments=("a",)),
        ]
    )
    assert [slot.name for slot in out] == ["aaa", "middle", "zee"]


def test_build_slots_empty_input_yields_empty_list() -> None:
    assert build_slots([]) == []


def test_kind_agnostic_attachments_emit_unchanged() -> None:
    """Attachments[] is just string[] - the kind lives on each Sprite,
    not on the slot. Confirm slot emission ignores any kind hint."""
    slot = build_slot(
        SlotInput(
            name="face.state",
            bone="head",
            slot_default="",
            attachments=("face.poly_open", "face.cycle_anim", "face.poly_closed"),
        )
    )
    assert slot.attachments == [
        "face.poly_open",
        "face.cycle_anim",
        "face.poly_closed",
    ]
    assert slot.bone == "head"
