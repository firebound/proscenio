"""Unit tests for SPEC 009 wave 9.1 -- core.cp_keys constants.

Pure pytest, no Blender. Confirms every constant is a non-empty string
and they are pairwise distinct (no two PG fields point at the same CP
key).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "blender-addon"))

from core import cp_keys  # noqa: E402


def _public_keys() -> dict[str, str]:
    return {
        name: value
        for name, value in vars(cp_keys).items()
        if name.isupper() and isinstance(value, str)
    }


def test_every_constant_is_proscenio_prefixed() -> None:
    for name, value in _public_keys().items():
        assert value.startswith("proscenio_"), f"{name} not prefixed: {value!r}"


def test_no_duplicate_values() -> None:
    values = list(_public_keys().values())
    assert len(values) == len(set(values))


def test_known_keys_present() -> None:
    expected = {
        "PROSCENIO_IS_SLOT",
        "PROSCENIO_SLOT_DEFAULT",
        "PROSCENIO_SLOT_INDEX",
        "PROSCENIO_PRE_PACK",
        "PROSCENIO_TYPE",
        "PROSCENIO_HFRAMES",
        "PROSCENIO_VFRAMES",
        "PROSCENIO_FRAME",
    }
    assert expected.issubset(_public_keys().keys())
