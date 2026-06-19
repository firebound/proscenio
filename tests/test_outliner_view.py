"""Unit tests for the Outliner view-model row-visibility + membership rules.

Pure pytest, no Blender. ``row_visible`` is the bpy-free predicate the
Outliner's ``filter_items`` uses to decide whether a source row is shown
(it drops rows whose object left the view layer, fails the membership rule,
the favorites filter, or the name filter). ``is_proscenio_member`` is the
membership rule: a free mesh must carry element data and an armature must be
the picked one.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.outliner_view import (  # noqa: E402
    RANK_ARMATURE,
    RANK_ATTACHMENT,
    RANK_ELEMENT_MESH,
    RANK_HIDDEN,
    RANK_SLOT,
    category_rank,
    hierarchy_sort_key,
    is_proscenio_member,
    outliner_depth,
    outliner_sort_key,
    row_visible,
)


def _obj(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name)


def test_visible_when_relevant_and_in_view_layer() -> None:
    assert (
        row_visible(
            _obj("arm"),
            in_view_layer=True,
            rank=RANK_ELEMENT_MESH,
            is_member=True,
            is_favorite=False,
            favorites_only=False,
            filter_text="",
        )
        is True
    )


def test_hidden_when_not_a_member() -> None:
    # A raw mesh (or a non-picked armature) is a valid category but not a
    # member, so its row drops out.
    assert (
        row_visible(
            _obj("Cube"),
            in_view_layer=True,
            rank=RANK_ELEMENT_MESH,
            is_member=False,
            is_favorite=False,
            favorites_only=False,
            filter_text="",
        )
        is False
    )


def test_hidden_when_not_in_view_layer() -> None:
    # The bug: a deleted object lingers in bpy.data.objects but leaves the
    # view layer; its row must drop out of the list.
    assert (
        row_visible(
            _obj("Proscenio.QuickRig"),
            in_view_layer=False,
            rank=RANK_ARMATURE,
            is_member=True,
            is_favorite=False,
            favorites_only=False,
            filter_text="",
        )
        is False
    )


def test_hidden_when_rank_is_hidden() -> None:
    assert (
        row_visible(
            _obj("Camera"),
            in_view_layer=True,
            rank=RANK_HIDDEN,
            is_member=True,
            is_favorite=False,
            favorites_only=False,
            filter_text="",
        )
        is False
    )


def test_hidden_when_favorites_only_and_not_favorite() -> None:
    assert (
        row_visible(
            _obj("arm"),
            in_view_layer=True,
            rank=RANK_ELEMENT_MESH,
            is_member=True,
            is_favorite=False,
            favorites_only=True,
            filter_text="",
        )
        is False
    )


def test_hidden_when_filter_text_does_not_match() -> None:
    assert (
        row_visible(
            _obj("arm"),
            in_view_layer=True,
            rank=RANK_ELEMENT_MESH,
            is_member=True,
            is_favorite=False,
            favorites_only=False,
            filter_text="leg",
        )
        is False
    )


def test_filter_text_matches_case_insensitively() -> None:
    assert (
        row_visible(
            _obj("LeftArm"),
            in_view_layer=True,
            rank=RANK_ELEMENT_MESH,
            is_member=True,
            is_favorite=False,
            favorites_only=False,
            filter_text="arm",
        )
        is True
    )


# --- membership rule ----------------------------------------------------------


def _authored_mesh(name: str) -> SimpleNamespace:
    # Carries the proscenio_type Custom Property (import / Incorporate stamp).
    return SimpleNamespace(
        name=name,
        get=lambda key, default=None: {"proscenio_type": "mesh"}.get(key, default),
    )


def test_member_authored_mesh() -> None:
    obj = _authored_mesh("torso")
    assert (
        is_proscenio_member(obj, rank=RANK_ELEMENT_MESH, picked_armature_name=None)
        is True
    )


def test_not_member_raw_mesh_without_marker() -> None:
    # A hand-modelled mesh has no proscenio_type Custom Property at all.
    obj = SimpleNamespace(name="Cube")
    assert (
        is_proscenio_member(obj, rank=RANK_ELEMENT_MESH, picked_armature_name=None)
        is False
    )


def test_not_member_mesh_with_absent_marker_value() -> None:
    # The Custom Property read returns None (key absent) - still not a member.
    obj = SimpleNamespace(name="Cube", get=lambda key, default=None: default)
    assert (
        is_proscenio_member(obj, rank=RANK_ELEMENT_MESH, picked_armature_name=None)
        is False
    )


def test_member_picked_armature() -> None:
    obj = _obj("Rig")
    assert (
        is_proscenio_member(obj, rank=RANK_ARMATURE, picked_armature_name="Rig") is True
    )


def test_not_member_unpicked_armature() -> None:
    obj = _obj("StrayRig")
    assert (
        is_proscenio_member(obj, rank=RANK_ARMATURE, picked_armature_name="Rig")
        is False
    )


def test_not_member_armature_when_nothing_picked() -> None:
    obj = _obj("Rig")
    assert (
        is_proscenio_member(obj, rank=RANK_ARMATURE, picked_armature_name=None) is False
    )


def test_member_slot_and_attachment_always() -> None:
    assert (
        is_proscenio_member(
            _obj("hand.slot"), rank=RANK_SLOT, picked_armature_name=None
        )
        is True
    )
    assert (
        is_proscenio_member(
            _obj("sword"), rank=RANK_ATTACHMENT, picked_armature_name=None
        )
        is True
    )


# --- hierarchy ordering -------------------------------------------------------


def test_outliner_depth_by_rank() -> None:
    assert outliner_depth(RANK_ARMATURE) == 0  # root
    assert outliner_depth(RANK_SLOT) == 1  # under the armature
    assert outliner_depth(RANK_ELEMENT_MESH) == 1  # loose, under the armature
    assert outliner_depth(RANK_ATTACHMENT) == 2  # under its slot


def _slot(name: str) -> SimpleNamespace:
    return SimpleNamespace(
        name=name, type="EMPTY", proscenio=SimpleNamespace(is_slot=True)
    )


def test_hierarchy_sort_lays_out_the_parenting_tree() -> None:
    # armature, then each slot followed by its attachments (by slot name), then
    # the loose meshes - armature -> slot -> slot mesh, then free meshes.
    arm = SimpleNamespace(name="Rig", type="ARMATURE")
    hand = _slot("hand")
    sword = SimpleNamespace(name="sword", type="MESH", parent=hand)
    back = _slot("back")
    shield = SimpleNamespace(name="shield", type="MESH", parent=back)
    torso = SimpleNamespace(name="torso", type="MESH", parent=arm)
    objs = [torso, shield, arm, sword, back, hand]
    ordered = sorted(objs, key=lambda o: hierarchy_sort_key(o, rank=category_rank(o)))
    # "back" sorts before "hand"; each slot is immediately followed by its
    # attachment; the loose "torso" lands last.
    assert [o.name for o in ordered] == [
        "Rig",
        "back",
        "shield",
        "hand",
        "sword",
        "torso",
    ]


def test_outliner_sort_key_alpha_flattens_to_plain_name_order() -> None:
    # With the native 'sort by name' toggle on, the parenting tree is dropped:
    # every kind sorts together by name (case-insensitive).
    arm = SimpleNamespace(name="Zebra", type="ARMATURE")
    hand = _slot("hand")
    sword = SimpleNamespace(name="sword", type="MESH", parent=hand)
    torso = SimpleNamespace(name="alpha_torso", type="MESH", parent=arm)
    objs = [arm, hand, sword, torso]
    ordered = sorted(
        objs, key=lambda o: outliner_sort_key(o, rank=category_rank(o), sort_alpha=True)
    )
    assert [o.name for o in ordered] == ["alpha_torso", "hand", "sword", "Zebra"]


def test_outliner_sort_key_tree_when_alpha_off() -> None:
    # Toggle off: the key is exactly the parenting-tree key.
    hand = _slot("hand")
    glove = SimpleNamespace(name="glove", type="MESH", parent=hand)
    rank = category_rank(glove)
    assert outliner_sort_key(glove, rank=rank, sort_alpha=False) == hierarchy_sort_key(
        glove, rank=rank
    )


def test_hierarchy_sort_keeps_a_slot_with_its_attachments() -> None:
    # An attachment groups under its parent slot's name, not its own.
    hand = _slot("hand")
    glove = SimpleNamespace(name="aaa_glove", type="MESH", parent=hand)
    key = hierarchy_sort_key(glove, rank=category_rank(glove))
    # Section 1 (slots), grouped by the slot name "hand", sub-rank 1 (after the slot).
    assert key == (1, "hand", 1, "aaa_glove")
