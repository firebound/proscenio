"""Unit tests for the mirror-all-fields semantics.

Guards the bug where per-field update callbacks only fired when the user
touched that specific field, so defaults never mirrored and Reload
Scripts restored only what had been touched. Every callback now delegates
to ``mirror_all_fields`` so the Custom Property set is always a complete
snapshot of the PropertyGroup. Also covers ``hydrate_object`` against the
region_* legacy keys.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.hydrate import OBJECT_PROPS, hydrate_object  # noqa: E402
from core.mirror import mirror_all_fields  # noqa: E402


class _ObjectMock:
    """``bpy.types.Object`` substitute with __setitem__ for CP writes."""

    def __init__(self, proscenio: Any | None = None) -> None:
        self._custom: dict[str, Any] = {}
        self.proscenio = proscenio

    def __contains__(self, key: str) -> bool:
        return key in self._custom

    def __getitem__(self, key: str) -> Any:
        return self._custom[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._custom[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._custom.get(key, default)


def _full_props() -> SimpleNamespace:
    return SimpleNamespace(
        element_type="sprite",
        hframes=4,
        vframes=2,
        frame=1,
        centered=False,
        region_mode="manual",
        region_x=0.1,
        region_y=0.2,
        region_w=0.3,
        region_h=0.4,
    )


def test_mirror_all_writes_every_field() -> None:
    obj = _ObjectMock(proscenio=_full_props())
    mirror_all_fields(obj.proscenio, obj)
    assert obj["proscenio_type"] == "sprite"
    assert obj["proscenio_hframes"] == 4
    assert obj["proscenio_vframes"] == 2
    assert obj["proscenio_frame"] == 1
    assert obj["proscenio_centered"] is False
    assert obj["proscenio_region_mode"] == "manual"
    assert obj["proscenio_region_x"] == pytest.approx(0.1)
    assert obj["proscenio_region_y"] == pytest.approx(0.2)
    assert obj["proscenio_region_w"] == pytest.approx(0.3)
    assert obj["proscenio_region_h"] == pytest.approx(0.4)


def test_mirror_all_skips_missing_attributes() -> None:
    """A PropertyGroup that only has element_type still mirrors that one field."""
    obj = _ObjectMock(proscenio=SimpleNamespace(element_type="mesh"))
    mirror_all_fields(obj.proscenio, obj)
    assert obj["proscenio_type"] == "mesh"
    # Missing fields not written:
    assert "proscenio_hframes" not in obj
    assert "proscenio_region_x" not in obj


def test_mirror_all_swallows_caster_errors() -> None:
    """Bogus value (None where int wanted) does not break the rest."""
    props = _full_props()
    props.hframes = None  # type: ignore[assignment]  - bogus on purpose
    obj = _ObjectMock(proscenio=props)
    mirror_all_fields(props, obj)
    assert "proscenio_hframes" not in obj  # caster raised -> skipped
    # Other fields still mirrored:
    assert obj["proscenio_type"] == "sprite"
    assert obj["proscenio_region_x"] == pytest.approx(0.1)


def test_hydrate_round_trip_with_region_fields() -> None:
    """Mirror + hydrate is a stable round trip for the full field set."""
    src = _full_props()
    obj = _ObjectMock(proscenio=src)
    mirror_all_fields(src, obj)

    # Now simulate Reload Scripts: PG resets to defaults, hydrate from CPs.
    fresh = SimpleNamespace(
        element_type="mesh",
        hframes=1,
        vframes=1,
        frame=0,
        centered=True,
        region_mode="auto",
        region_x=0.0,
        region_y=0.0,
        region_w=1.0,
        region_h=1.0,
    )
    obj.proscenio = fresh
    hydrate_object(obj)

    assert fresh.element_type == src.element_type
    assert fresh.hframes == src.hframes
    assert fresh.region_mode == src.region_mode
    assert fresh.region_x == pytest.approx(src.region_x)
    assert fresh.region_h == pytest.approx(src.region_h)


def test_object_props_mapping_includes_region_keys() -> None:
    """Hydrate's mapping must cover all region_* legacy CP keys."""
    keys = {pair[0] for pair in OBJECT_PROPS}
    assert "proscenio_region_mode" in keys
    assert "proscenio_region_x" in keys
    assert "proscenio_region_y" in keys
    assert "proscenio_region_w" in keys
    assert "proscenio_region_h" in keys
