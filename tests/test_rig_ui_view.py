"""Unit tests for the Rig UI view-model: bone-collection tree -> render rows.

Pure pytest, no Blender. ``rig_ui_rows`` flattens a (possibly nested) bone
collection tree into the ordered rows the Rig UI subpanel draws: a branch
collection becomes a header row whose select buttons are its direct children
(then each branch child recurses into its own header row, depth-first), while a
top-level leaf becomes a single headerless button row.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.rig_ui_view import rig_ui_rows  # noqa: E402


def _col(name: str, children: list[SimpleNamespace] | None = None) -> SimpleNamespace:
    return SimpleNamespace(name=name, children=children or [])


def test_top_level_leaf_is_one_headerless_self_button_row() -> None:
    # A childless top-level collection draws as a single row, no header, the
    # collection both the eye/theme target and its own select button.
    rows = rig_ui_rows([_col("Bones")])
    assert len(rows) == 1
    row = rows[0]
    assert row.header is None
    assert row.collection_name == "Bones"
    assert row.member_names == ("Bones",)
    assert row.is_top_level is True


def test_branch_is_header_row_with_direct_children_as_buttons() -> None:
    arms = _col("arms", [_col("arm.L"), _col("arm.R")])
    rows = rig_ui_rows([arms])
    assert len(rows) == 1
    row = rows[0]
    assert row.header == "arms"
    assert row.collection_name == "arms"
    assert row.member_names == ("arm.L", "arm.R")


def test_branch_child_recurses_into_its_own_header_row() -> None:
    # arm.L itself owns children -> it is a button under "arms" AND a header row
    # of its own below (depth-first, pre-order). arm.R is a leaf: button only.
    arms = _col("arms", [_col("arm.L", [_col("fingers.L")]), _col("arm.R")])
    rows = rig_ui_rows([arms])
    assert [(r.header, r.member_names) for r in rows] == [
        ("arms", ("arm.L", "arm.R")),
        ("arm.L", ("fingers.L",)),
    ]


def test_deep_nesting_recurses_every_branch_depth_first() -> None:
    # arms > arm.L > fingers.L > thumb.L, plus a sibling subtree under arm.R.
    tree = _col(
        "arms",
        [
            _col("arm.L", [_col("fingers.L", [_col("thumb.L")])]),
            _col("arm.R", [_col("fingers.R")]),
        ],
    )
    rows = rig_ui_rows([tree])
    assert [r.header for r in rows] == ["arms", "arm.L", "fingers.L", "arm.R"]
    # Each branch row lists exactly its direct children as buttons.
    by_header = {r.header: r.member_names for r in rows}
    assert by_header["arms"] == ("arm.L", "arm.R")
    assert by_header["arm.L"] == ("fingers.L",)
    assert by_header["fingers.L"] == ("thumb.L",)
    assert by_header["arm.R"] == ("fingers.R",)


def test_multiple_top_level_collections_keep_input_order() -> None:
    rows = rig_ui_rows(
        [_col("arms", [_col("arm.L")]), _col("Bones"), _col("legs", [_col("leg.L")])]
    )
    assert [r.header if r.header is not None else r.collection_name for r in rows] == [
        "arms",
        "Bones",
        "legs",
    ]


def test_only_top_level_rows_are_flagged_for_the_theme_selector() -> None:
    # is_top_level is true for rows from a top-level collection (they carry the
    # color control), false for every recursed sub-collection row.
    tree = _col("arms", [_col("arm.L", [_col("fingers.L")]), _col("arm.R")])
    rows = rig_ui_rows([tree, _col("Bones")])
    flags = {
        r.header if r.header is not None else r.collection_name: r.is_top_level
        for r in rows
    }
    assert flags == {"arms": True, "arm.L": False, "Bones": True}


def test_empty_input_is_no_rows() -> None:
    assert rig_ui_rows([]) == []
    assert rig_ui_rows(None) == []
