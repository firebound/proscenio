"""Unit tests for the Custom-Property-backed proxy logic (spec 037).

Pure pytest, no Blender. The per-Object CP-canonical fields surface in
the panel through ``get``/``set`` PropertyGroup proxies that read and
write the ``proscenio_*`` idprop. The bpy-bound proxy wiring itself is
covered by the in-Blender suite; here we exercise the pure pieces it
composes from - the enum index<->identifier mapping and the frame clamp.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.idprop_proxy import enum_index_to_value, enum_value_to_index  # noqa: E402
from core._shared.sprite_grid import clamp_frame_index  # noqa: E402

_ELEMENT_TYPE_VALUES = ("mesh", "sprite")
_REGION_MODE_VALUES = ("auto", "manual")


def test_enum_value_to_index_round_trips_both_directions() -> None:
    for index, value in enumerate(_ELEMENT_TYPE_VALUES):
        assert enum_value_to_index(value, _ELEMENT_TYPE_VALUES) == index
        assert enum_index_to_value(index, _ELEMENT_TYPE_VALUES) == value


def test_enum_value_to_index_unknown_falls_back_to_default() -> None:
    # A hand-edited / legacy idprop string the items no longer contain.
    assert enum_value_to_index("polygon", _ELEMENT_TYPE_VALUES) == 0


def test_enum_value_to_index_respects_custom_default() -> None:
    assert enum_value_to_index("bogus", _REGION_MODE_VALUES, default_index=1) == 1


def test_enum_index_to_value_out_of_range_falls_back() -> None:
    assert enum_index_to_value(99, _ELEMENT_TYPE_VALUES) == "mesh"
    assert enum_index_to_value(-1, _ELEMENT_TYPE_VALUES) == "mesh"


def test_enum_index_to_value_custom_default() -> None:
    assert enum_index_to_value(99, _REGION_MODE_VALUES, default_index=1) == "manual"


def test_frame_setter_clamp_pulls_into_grid() -> None:
    """The frame setter clamps against the live grid - shrinking it pulls in."""
    # 4x2 grid: 8 cells, last index 7.
    assert clamp_frame_index(5, 4, 2) == 5
    # Shrink to 2x1 (2 cells, last index 1): a stored 5 clamps to 1.
    assert clamp_frame_index(5, 2, 1) == 1
    # 1x1 grid clamps everything to 0.
    assert clamp_frame_index(9, 1, 1) == 0
    # Negative never escapes below 0.
    assert clamp_frame_index(-3, 4, 2) == 0
