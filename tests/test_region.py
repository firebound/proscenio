"""Unit tests for the SPEC 005.1.c.1 texture-region resolver.

Mocks ``bpy.types.Object`` with :class:`SimpleNamespace`-flavored stand-ins so
the helper is exercised without a Blender session. Covers both modes (auto
vs manual), the legacy Custom Property fallback, and the ``manual_region_or_none``
gate used by ``sprite_frame``.

Run from the repo root:

    pytest tests/test_region.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.region import (  # noqa: E402  - sys.path setup above
    compute_region_from_uvs,
    manual_region_or_none,
    resolve_region,
)


class _ObjectMock:
    """Minimal ``bpy.types.Object`` substitute supporting ``in`` / ``[]``."""

    def __init__(
        self,
        custom_props: dict[str, Any] | None = None,
        proscenio: SimpleNamespace | None = None,
    ) -> None:
        self._custom = dict(custom_props or {})
        self.proscenio = proscenio

    def __contains__(self, key: str) -> bool:
        return key in self._custom

    def __getitem__(self, key: str) -> Any:
        return self._custom[key]


def _auto_props() -> SimpleNamespace:
    return SimpleNamespace(
        region_mode="auto",
        region_x=0.0,
        region_y=0.0,
        region_w=1.0,
        region_h=1.0,
    )


def _manual_props(x: float, y: float, w: float, h: float) -> SimpleNamespace:
    return SimpleNamespace(
        region_mode="manual",
        region_x=x,
        region_y=y,
        region_w=w,
        region_h=h,
    )


def test_compute_region_empty_uvs_returns_zeros() -> None:
    assert compute_region_from_uvs([]) == [0.0, 0.0, 0.0, 0.0]


def test_compute_region_min_max_bounds() -> None:
    uvs = [[0.2, 0.1], [0.8, 0.4], [0.5, 0.7]]
    assert compute_region_from_uvs(uvs) == [0.2, 0.1, 0.6, 0.6]


def test_resolve_auto_falls_back_to_uv_bounds() -> None:
    obj = _ObjectMock(proscenio=_auto_props())
    uvs = [[0.1, 0.0], [0.4, 0.0], [0.4, 0.5], [0.1, 0.5]]
    assert resolve_region(obj, uvs) == [0.1, 0.0, 0.3, 0.5]


def test_resolve_manual_emits_property_group_values() -> None:
    obj = _ObjectMock(proscenio=_manual_props(0.25, 0.5, 0.25, 0.25))
    uvs = [[0.0, 0.0], [1.0, 1.0]]  # ignored in manual mode
    assert resolve_region(obj, uvs) == [0.25, 0.5, 0.25, 0.25]


def test_resolve_manual_falls_back_to_custom_props_without_property_group() -> None:
    obj = _ObjectMock(
        custom_props={
            "proscenio_region_mode": "manual",
            "proscenio_region_x": 0.1,
            "proscenio_region_y": 0.2,
            "proscenio_region_w": 0.3,
            "proscenio_region_h": 0.4,
        },
        proscenio=None,
    )
    assert resolve_region(obj, [[0.0, 0.0]]) == [0.1, 0.2, 0.3, 0.4]


def test_manual_region_or_none_returns_none_in_auto_mode() -> None:
    obj = _ObjectMock(proscenio=_auto_props())
    assert manual_region_or_none(obj) is None


def test_manual_region_or_none_returns_tuple_in_manual_mode() -> None:
    obj = _ObjectMock(proscenio=_manual_props(0.0, 0.5, 0.5, 0.5))
    assert manual_region_or_none(obj) == [0.0, 0.5, 0.5, 0.5]
