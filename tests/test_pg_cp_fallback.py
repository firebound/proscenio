"""Unit tests for the core._shared.pg_cp_fallback helpers.

Pure pytest, no Blender. Since the storage split (spec 037) each
per-Object field has one home - its ``proscenio_*`` Custom Property
(idprop) - so the reader is idprop-only: the value when present, the
``default`` otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.pg_cp_fallback import read_bool_flag, read_field  # noqa: E402


class FakeObj:
    """``bpy.types.Object`` substitute exposing dict-style ``.get``."""

    def __init__(self, cps: dict[str, Any] | None = None) -> None:
        self._cps = cps or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._cps.get(key, default)


class NoGetObj:
    """An object without ``.get`` - reads as absent (default)."""


def test_read_field_returns_idprop_value() -> None:
    obj = FakeObj(cps={"proscenio_type": "sprite"})
    assert read_field(obj, cp_key="proscenio_type", default="mesh") == "sprite"


def test_read_field_default_when_absent() -> None:
    obj = FakeObj()
    assert read_field(obj, cp_key="proscenio_type", default="mesh") == "mesh"


def test_read_field_default_when_idprop_is_none() -> None:
    obj = FakeObj(cps={"proscenio_frame": None})
    assert read_field(obj, cp_key="proscenio_frame", default=-1) == -1


def test_read_field_explicit_zero_wins_over_default() -> None:
    """A stored 0 is a real value - it must not fall through to the default."""
    obj = FakeObj(cps={"proscenio_frame": 0})
    assert read_field(obj, cp_key="proscenio_frame", default=-1) == 0


def test_read_field_explicit_empty_string_wins_over_default() -> None:
    obj = FakeObj(cps={"proscenio_slot_default": ""})
    assert read_field(obj, cp_key="proscenio_slot_default", default="x") == ""


def test_read_field_no_get_object_returns_default() -> None:
    assert read_field(NoGetObj(), cp_key="proscenio_type", default="mesh") == "mesh"


def test_read_bool_flag_true() -> None:
    obj = FakeObj(cps={"proscenio_is_slot": True})
    assert read_bool_flag(obj, cp_key="proscenio_is_slot") is True


def test_read_bool_flag_false_when_absent() -> None:
    assert read_bool_flag(FakeObj(), cp_key="proscenio_is_slot") is False


def test_read_bool_flag_explicit_false() -> None:
    obj = FakeObj(cps={"proscenio_is_slot": False})
    assert read_bool_flag(obj, cp_key="proscenio_is_slot") is False


def test_read_bool_flag_coerces_idprop_int() -> None:
    """idprops store bool as int 0/1 - the flag read must coerce to bool."""
    obj = FakeObj(cps={"proscenio_is_slot": 1})
    assert read_bool_flag(obj, cp_key="proscenio_is_slot") is True


def test_read_bool_flag_no_get_object_returns_false() -> None:
    assert read_bool_flag(NoGetObj(), cp_key="proscenio_is_slot") is False
