"""Unit tests for the SPEC 005 PropertyGroup hydration logic.

Mocks ``bpy.types.Object`` via :class:`SimpleNamespace` so the hydration
helper is exercised without a Blender session. The Blender side of the
addon (PointerProperty wiring, register/unregister, decorators) is out
of scope here — covered by the manual smoke test.

Run from the repo root:

    pytest tests/test_properties.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "blender-addon"))

from core.hydrate import hydrate_object  # noqa: E402  — sys.path setup above


class _ObjectMock:
    """Minimal ``bpy.types.Object`` substitute that supports ``in`` and ``[]``.

    The hydration helper uses ``custom_key in obj`` and ``obj[custom_key]``
    to read raw Custom Properties; both are dunder methods on the Blender
    Object. ``proscenio`` is a sibling attribute that mimics the
    PointerProperty target.
    """

    def __init__(
        self,
        custom_props: dict[str, Any] | None = None,
        proscenio: Any = None,
    ) -> None:
        self._custom = dict(custom_props or {})
        self.proscenio = proscenio

    def __contains__(self, key: str) -> bool:
        return key in self._custom

    def __getitem__(self, key: str) -> Any:
        return self._custom[key]


def _empty_props() -> SimpleNamespace:
    return SimpleNamespace(
        sprite_type="polygon",
        hframes=1,
        vframes=1,
        frame=0,
        centered=True,
    )


def test_hydrate_skips_object_without_proscenio() -> None:
    obj = _ObjectMock(custom_props={"proscenio_type": "sprite_frame"}, proscenio=None)
    hydrate_object(obj)  # must not raise — silent skip


def test_hydrate_copies_sprite_type_when_present() -> None:
    props = _empty_props()
    obj = _ObjectMock(
        custom_props={"proscenio_type": "sprite_frame"},
        proscenio=props,
    )
    hydrate_object(obj)
    assert props.sprite_type == "sprite_frame"


def test_hydrate_copies_full_sprite_frame_metadata() -> None:
    props = _empty_props()
    obj = _ObjectMock(
        custom_props={
            "proscenio_type": "sprite_frame",
            "proscenio_hframes": 4,
            "proscenio_vframes": 2,
            "proscenio_frame": 3,
            "proscenio_centered": False,
        },
        proscenio=props,
    )
    hydrate_object(obj)
    assert props.sprite_type == "sprite_frame"
    assert props.hframes == 4
    assert props.vframes == 2
    assert props.frame == 3
    assert props.centered is False


def test_hydrate_leaves_defaults_when_custom_props_absent() -> None:
    props = _empty_props()
    obj = _ObjectMock(custom_props={}, proscenio=props)
    hydrate_object(obj)
    # Untouched — every field still equals the default.
    assert props.sprite_type == "polygon"
    assert props.hframes == 1
    assert props.vframes == 1
    assert props.frame == 0
    assert props.centered is True


def test_hydrate_partial_overrides() -> None:
    props = _empty_props()
    obj = _ObjectMock(
        custom_props={"proscenio_hframes": 8},
        proscenio=props,
    )
    hydrate_object(obj)
    assert props.hframes == 8
    # Fields the user did not author stay at default.
    assert props.sprite_type == "polygon"
    assert props.vframes == 1


def test_hydrate_swallows_type_errors() -> None:
    """Setting a string into an int slot must not break hydration."""

    class _StrictProps:
        """Mocks the Blender PropertyGroup's strict typed setattr."""

        sprite_type = "polygon"
        hframes = 1

        def __setattr__(self, name: str, value: Any) -> None:
            if name == "hframes" and not isinstance(value, int):
                raise TypeError(f"hframes wants int, got {type(value).__name__}")
            object.__setattr__(self, name, value)

    props = _StrictProps()
    obj = _ObjectMock(
        custom_props={
            "proscenio_type": "sprite_frame",
            "proscenio_hframes": "not-an-int",  # bogus on purpose
        },
        proscenio=props,
    )
    hydrate_object(obj)
    # sprite_type still applied; hframes left at the default.
    assert props.sprite_type == "sprite_frame"
    assert props.hframes == 1
