"""Unit tests for the Outliner view-model row-visibility rule.

Pure pytest, no Blender. ``row_visible`` is the bpy-free predicate the
Outliner's ``filter_items`` uses to decide whether a source row is shown,
including the rule that drops rows whose object is no longer in the view
layer (a deleted / undone datablock that lingers in ``bpy.data.objects``).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.outliner_view import RANK_HIDDEN, row_visible  # noqa: E402


def _obj(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name)


def test_visible_when_relevant_and_in_view_layer() -> None:
    assert (
        row_visible(
            _obj("arm"),
            in_view_layer=True,
            rank=2,
            is_favorite=False,
            favorites_only=False,
            filter_text="",
        )
        is True
    )


def test_hidden_when_not_in_view_layer() -> None:
    # The bug: a deleted object lingers in bpy.data.objects but leaves the
    # view layer; its row must drop out of the list.
    assert (
        row_visible(
            _obj("Proscenio.QuickRig"),
            in_view_layer=False,
            rank=3,
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
            rank=2,
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
            rank=2,
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
            rank=2,
            is_favorite=False,
            favorites_only=False,
            filter_text="arm",
        )
        is True
    )
