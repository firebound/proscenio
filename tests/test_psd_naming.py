"""Unit tests for the PSD layer naming convention helpers (SPEC 006 Wave 6.2).

Pure Python; no Blender. Locked rules in
``apps/blender/core/psd_naming.py``.

Run from the repo root::

    pytest tests/test_psd_naming.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core import psd_naming  # noqa: E402


def test_match_pure_digit_returns_empty_base() -> None:
    result = psd_naming.match_indexed_frame("0")
    assert result is not None
    assert result.base == ""
    assert result.index == 0


def test_match_frame_prefix_underscore_or_dash() -> None:
    a = psd_naming.match_indexed_frame("frame_3")
    b = psd_naming.match_indexed_frame("frame-3")
    assert a == b
    assert a is not None and a.index == 3 and a.base == ""


def test_match_group_prefix_carries_base() -> None:
    result = psd_naming.match_indexed_frame("eye_2")
    assert result is not None
    assert result.base == "eye"
    assert result.index == 2


def test_match_returns_none_for_non_indexed_name() -> None:
    assert psd_naming.match_indexed_frame("torso") is None
    assert psd_naming.match_indexed_frame("bare-name") is None
    assert psd_naming.match_indexed_frame("") is None


def test_match_rejects_pure_digit_with_extra_text() -> None:
    assert psd_naming.match_indexed_frame("0_eye") is None


def test_uniform_indexed_group_pure_digits() -> None:
    assert psd_naming.is_uniform_indexed_group(["0", "1", "2", "3"])


def test_uniform_indexed_group_frame_prefix() -> None:
    assert psd_naming.is_uniform_indexed_group(["frame_0", "frame_1"])


def test_uniform_indexed_group_with_shared_base() -> None:
    assert psd_naming.is_uniform_indexed_group(["eye_0", "eye_1", "eye_2"])


def test_uniform_indexed_group_rejects_mixed_conventions() -> None:
    assert not psd_naming.is_uniform_indexed_group(["0", "frame_1"])


def test_uniform_indexed_group_rejects_mixed_bases() -> None:
    assert not psd_naming.is_uniform_indexed_group(["eye_0", "lip_1"])


def test_uniform_indexed_group_rejects_non_zero_start() -> None:
    assert not psd_naming.is_uniform_indexed_group(["1", "2", "3"])


def test_uniform_indexed_group_rejects_gap() -> None:
    assert not psd_naming.is_uniform_indexed_group(["0", "1", "3"])


def test_uniform_indexed_group_rejects_single_child() -> None:
    assert not psd_naming.is_uniform_indexed_group(["0"])


def test_uniform_indexed_group_rejects_non_indexed_child() -> None:
    assert not psd_naming.is_uniform_indexed_group(["0", "1", "torso"])


def test_group_by_index_suffix_groups_by_base() -> None:
    grouped = psd_naming.group_by_index_suffix(
        ["eye_0", "eye_1", "eye_2", "lip_0", "lip_1", "torso"]
    )
    assert set(grouped) == {"eye", "lip", ""}
    assert grouped["eye"] == [(0, "eye_0"), (1, "eye_1"), (2, "eye_2")]
    assert grouped["lip"] == [(0, "lip_0"), (1, "lip_1")]
    assert grouped[""] == [(-1, "torso")]


def test_group_by_index_suffix_sorts_out_of_order_input() -> None:
    grouped = psd_naming.group_by_index_suffix(["eye_2", "eye_0", "eye_1"])
    assert grouped["eye"] == [(0, "eye_0"), (1, "eye_1"), (2, "eye_2")]
