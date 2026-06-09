"""Unit tests for the code-modularity work - core._shared.pg_cp_fallback helpers.

Pure pytest, no Blender. The fallback contract: PropertyGroup field
wins, Custom Property literal as legacy fallback, ``default`` as last
resort.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.pg_cp_fallback import read_bool_flag, read_field  # noqa: E402


class FakeObj:
    """SimpleNamespace-like with a ``.get`` method (mirrors bpy Object)."""

    def __init__(
        self,
        proscenio: Any | None = None,
        cps: dict[str, Any] | None = None,
    ) -> None:
        self.proscenio = proscenio
        self._cps = cps or {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._cps.get(key, default)


def test_read_field_pg_wins_over_cp() -> None:
    pg = SimpleNamespace(element_type="sprite")
    obj = FakeObj(proscenio=pg, cps={"proscenio_type": "mesh"})
    value = read_field(
        obj, pg_field="element_type", cp_key="proscenio_type", default="mesh"
    )
    assert value == "sprite"


def test_read_field_cp_fallback_when_pg_missing() -> None:
    obj = FakeObj(proscenio=None, cps={"proscenio_type": "sprite"})
    value = read_field(
        obj, pg_field="element_type", cp_key="proscenio_type", default="mesh"
    )
    assert value == "sprite"


def test_read_field_default_when_neither_present() -> None:
    obj = FakeObj()
    value = read_field(
        obj, pg_field="element_type", cp_key="proscenio_type", default="mesh"
    )
    assert value == "mesh"


def test_read_field_default_when_pg_field_is_none() -> None:
    pg = SimpleNamespace()  # no element_type attribute
    obj = FakeObj(proscenio=pg, cps={"proscenio_type": "sprite"})
    # PG missing the field falls through to CP.
    value = read_field(
        obj, pg_field="element_type", cp_key="proscenio_type", default="mesh"
    )
    assert value == "sprite"


def test_read_field_pg_explicit_zero_wins_over_cp() -> None:
    """A+A presence rule: an explicit falsy PG value (0) wins - it does NOT
    fall through to the Custom Property the way a truthiness rule would."""
    obj = FakeObj(proscenio=SimpleNamespace(frame=0), cps={"proscenio_frame": 5})
    value = read_field(obj, pg_field="frame", cp_key="proscenio_frame", default=-1)
    assert value == 0


def test_read_field_pg_empty_string_wins_over_cp() -> None:
    """Explicit empty-string PG value wins (is-not-None, not truthiness)."""
    obj = FakeObj(
        proscenio=SimpleNamespace(slot_default=""),
        cps={"proscenio_slot_default": "open"},
    )
    value = read_field(
        obj, pg_field="slot_default", cp_key="proscenio_slot_default", default="x"
    )
    assert value == ""


def test_read_field_pg_none_value_falls_through_to_cp() -> None:
    """A None PG value (not just an absent attr) falls through to the CP."""
    obj = FakeObj(proscenio=SimpleNamespace(frame=None), cps={"proscenio_frame": 5})
    value = read_field(obj, pg_field="frame", cp_key="proscenio_frame", default=-1)
    assert value == 5


def test_read_bool_flag_pg_true() -> None:
    pg = SimpleNamespace(is_slot=True)
    obj = FakeObj(proscenio=pg)
    assert read_bool_flag(obj, pg_field="is_slot", cp_key="proscenio_is_slot") is True


def test_read_bool_flag_cp_fallback() -> None:
    obj = FakeObj(proscenio=None, cps={"proscenio_is_slot": True})
    assert read_bool_flag(obj, pg_field="is_slot", cp_key="proscenio_is_slot") is True


def test_read_bool_flag_false_default() -> None:
    obj = FakeObj()
    assert read_bool_flag(obj, pg_field="is_slot", cp_key="proscenio_is_slot") is False


def test_read_bool_flag_pg_false_suppresses_cp_true() -> None:
    """PG-first: explicit False on the PG must NOT fall through to CP."""
    pg = SimpleNamespace(is_slot=False)
    obj = FakeObj(proscenio=pg, cps={"proscenio_is_slot": True})
    assert read_bool_flag(obj, pg_field="is_slot", cp_key="proscenio_is_slot") is False


def test_read_bool_flag_pg_missing_falls_back_to_cp() -> None:
    pg = SimpleNamespace()  # no is_slot attribute
    obj = FakeObj(proscenio=pg, cps={"proscenio_is_slot": True})
    assert read_bool_flag(obj, pg_field="is_slot", cp_key="proscenio_is_slot") is True
