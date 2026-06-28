"""Unit tests for the Skeleton bone-list view-model sort + depth.

Pure pytest, no Blender. ``bone_sort_key`` is the bpy-free key the Skeleton
list's ``filter_items`` uses: off the native A-Z toggle it lays the flat list
out as the parenting tree (depth-first, parent before children); on, it
collapses to a plain alphabetical order. ``bone_depth`` drives the row indent.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.bone_view import bone_depth, bone_sort_key  # noqa: E402


def _rig() -> dict[str, SimpleNamespace]:
    """A small parented rig: root -> spine -> {head, arm.L -> hand.L}; root -> leg.L."""
    root = SimpleNamespace(name="root", parent=None)
    spine = SimpleNamespace(name="spine", parent=root)
    head = SimpleNamespace(name="head", parent=spine)
    arm = SimpleNamespace(name="arm.L", parent=spine)
    hand = SimpleNamespace(name="hand.L", parent=arm)
    leg = SimpleNamespace(name="leg.L", parent=root)
    return {b.name: b for b in (root, spine, head, arm, hand, leg)}


def test_bone_depth_counts_parents() -> None:
    rig = _rig()
    assert bone_depth(rig["root"]) == 0
    assert bone_depth(rig["spine"]) == 1
    assert bone_depth(rig["hand.L"]) == 3


def test_bone_depth_zero_without_parent_attr() -> None:
    assert bone_depth(SimpleNamespace(name="loose")) == 0


def test_hierarchy_sort_is_depth_first_parent_before_children() -> None:
    # Off the A-Z toggle: each parent immediately precedes its own subtree, and
    # a whole subtree precedes a later sibling (arm.L's subtree before leg.L).
    rig = _rig()
    bones = list(rig.values())
    ordered = sorted(bones, key=lambda b: bone_sort_key(b, sort_alpha=False))
    assert [b.name for b in ordered] == [
        "root",
        "leg.L",
        "spine",
        "arm.L",
        "hand.L",
        "head",
    ]


def test_hierarchy_keeps_a_subtree_contiguous() -> None:
    # arm.L is immediately followed by its child hand.L, never split by a cousin.
    rig = _rig()
    ordered = sorted(rig.values(), key=lambda b: bone_sort_key(b, sort_alpha=False))
    names = [b.name for b in ordered]
    assert names.index("hand.L") == names.index("arm.L") + 1


def test_alpha_sort_flattens_to_plain_name_order() -> None:
    # On the A-Z toggle: the tree is dropped, every bone sorts by name.
    rig = _rig()
    ordered = sorted(rig.values(), key=lambda b: bone_sort_key(b, sort_alpha=True))
    assert [b.name for b in ordered] == [
        "arm.L",
        "hand.L",
        "head",
        "leg.L",
        "root",
        "spine",
    ]


def test_alpha_sort_is_case_insensitive() -> None:
    a = SimpleNamespace(name="Zeta", parent=None)
    b = SimpleNamespace(name="alpha", parent=None)
    ordered = sorted([a, b], key=lambda x: bone_sort_key(x, sort_alpha=True))
    assert [x.name for x in ordered] == ["alpha", "Zeta"]
