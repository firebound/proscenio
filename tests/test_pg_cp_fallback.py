"""Unit tests for SPEC 009 wave 9.1 -- core.pg_cp_fallback helpers.

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
sys.path.insert(0, str(REPO_ROOT / "blender-addon"))

from core.pg_cp_fallback import read_bool_flag, read_field  # noqa: E402


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
    pg = SimpleNamespace(sprite_type="sprite_frame")
    obj = FakeObj(proscenio=pg, cps={"proscenio_type": "polygon"})
    value = read_field(
        obj, pg_field="sprite_type", cp_key="proscenio_type", default="polygon"
    )
    assert value == "sprite_frame"


def test_read_field_cp_fallback_when_pg_missing() -> None:
    obj = FakeObj(proscenio=None, cps={"proscenio_type": "sprite_frame"})
    value = read_field(
        obj, pg_field="sprite_type", cp_key="proscenio_type", default="polygon"
    )
    assert value == "sprite_frame"


def test_read_field_default_when_neither_present() -> None:
    obj = FakeObj()
    value = read_field(
        obj, pg_field="sprite_type", cp_key="proscenio_type", default="polygon"
    )
    assert value == "polygon"


def test_read_field_default_when_pg_field_is_none() -> None:
    pg = SimpleNamespace()  # no sprite_type attribute
    obj = FakeObj(proscenio=pg, cps={"proscenio_type": "sprite_frame"})
    # PG missing the field falls through to CP.
    value = read_field(
        obj, pg_field="sprite_type", cp_key="proscenio_type", default="polygon"
    )
    assert value == "sprite_frame"


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
