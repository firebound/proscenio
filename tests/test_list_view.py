"""Unit tests for the shared list-view filter/sort + row-cap helpers.

Pure pytest, no Blender. ``compute_list_filter`` is the bpy-free core every
Proscenio UIList routes ``filter_items`` through (name search + visibility +
sort -> the flag/order pair template_list wants); ``clamped_rows`` is the
shared row cap.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.list_view import clamped_rows, compute_list_filter  # noqa: E402

_BIT = 1 << 30  # a stand-in for UIList.bitflag_filter_item


def _rows(*names: str) -> list[SimpleNamespace]:
    return [SimpleNamespace(name=n) for n in names]


def test_default_shows_every_row_keeping_source_order() -> None:
    rows = _rows("Charlie", "alpha", "Bravo")
    flags, neworder = compute_list_filter(rows, bitflag=_BIT)

    assert flags == [_BIT, _BIT, _BIT]
    # No sort_key -> source (collection) order kept; the bones rely on this so
    # the hierarchy order survives. Empty neworder is Blender's "no reorder".
    assert neworder == []


def test_explicit_name_sort_reorders() -> None:
    rows = _rows("Charlie", "alpha", "Bravo")
    _, neworder = compute_list_filter(rows, bitflag=_BIT, sort_key=lambda r: r.name.lower())

    # neworder[source_index] = post-sort position; case-insensitive name sort
    # gives alpha(1) < Bravo(2) < Charlie(0).
    assert neworder == [2, 0, 1]


def test_name_filter_is_case_insensitive_substring() -> None:
    rows = _rows("LeftArm", "RightLeg", "Spine")
    flags, _ = compute_list_filter(rows, bitflag=_BIT, name_filter="le")

    # "le" matches LeftArm and RightLeg, not Spine.
    assert flags == [_BIT, _BIT, 0]


def test_visible_predicate_drops_rows_before_name_filter() -> None:
    rows = _rows("keep", "drop_me")
    flags, _ = compute_list_filter(
        rows,
        bitflag=_BIT,
        visible=lambda row: not row.name.startswith("drop"),
    )

    assert flags == [_BIT, 0]


def test_custom_sort_key_orders_neworder() -> None:
    rows = _rows("a", "bb", "ccc")
    # Sort by descending name length: ccc(2) < bb(1) < a(0) in new order.
    _, neworder = compute_list_filter(rows, bitflag=_BIT, sort_key=lambda r: -len(r.name))

    assert neworder == [2, 1, 0]


def test_custom_name_of_reads_the_chosen_field() -> None:
    rows = [SimpleNamespace(label="findable"), SimpleNamespace(label="other")]
    flags, _ = compute_list_filter(
        rows,
        bitflag=_BIT,
        name_filter="find",
        name_of=lambda r: r.label,
        sort_key=lambda r: r.label,
    )

    assert flags == [_BIT, 0]


def test_empty_rows_returns_empty_pair() -> None:
    assert compute_list_filter([], bitflag=_BIT) == ([], [])


def test_clamped_rows_bounds_the_count() -> None:
    assert clamped_rows(0, minimum=3, maximum=8) == 3
    assert clamped_rows(5, minimum=3, maximum=8) == 5
    assert clamped_rows(99, minimum=3, maximum=8) == 8
