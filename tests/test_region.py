"""Unit tests for the authoring panel texture-region resolver.

Mocks ``bpy.types.Object`` with a dict-style stand-in so the helper is
exercised without a Blender session. Each region field reads from its
``proscenio_*`` Custom Property (idprop) via ``.get`` (spec 037). Covers both
modes (auto vs manual) and the ``manual_region_or_none`` gate used by
``sprite_frame``.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core._shared.region import (  # noqa: E402  - sys.path setup above
    compute_region_from_uvs,
    manual_region_or_none,
    resolve_region,
)


class _ObjectMock:
    """Minimal ``bpy.types.Object`` substitute with dict-style idprop access."""

    def __init__(self, idprops: dict[str, Any] | None = None) -> None:
        self._custom = dict(idprops or {})

    def __contains__(self, key: str) -> bool:
        return key in self._custom

    def __getitem__(self, key: str) -> Any:
        return self._custom[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._custom.get(key, default)


def _auto_idprops() -> dict[str, Any]:
    return {
        "proscenio_region_mode": "auto",
        "proscenio_region_x": 0.0,
        "proscenio_region_y": 0.0,
        "proscenio_region_w": 1.0,
        "proscenio_region_h": 1.0,
    }


def _manual_idprops(x: float, y: float, w: float, h: float) -> dict[str, Any]:
    return {
        "proscenio_region_mode": "manual",
        "proscenio_region_x": x,
        "proscenio_region_y": y,
        "proscenio_region_w": w,
        "proscenio_region_h": h,
    }


def test_compute_region_empty_uvs_returns_zeros() -> None:
    assert compute_region_from_uvs([]) == [0.0, 0.0, 0.0, 0.0]


def test_compute_region_min_max_bounds() -> None:
    uvs = [[0.2, 0.1], [0.8, 0.4], [0.5, 0.7]]
    assert compute_region_from_uvs(uvs) == [0.2, 0.1, 0.6, 0.6]


def test_resolve_auto_falls_back_to_uv_bounds() -> None:
    obj = _ObjectMock(_auto_idprops())
    uvs = [[0.1, 0.0], [0.4, 0.0], [0.4, 0.5], [0.1, 0.5]]
    assert resolve_region(obj, uvs) == [0.1, 0.0, 0.3, 0.5]


def test_resolve_manual_emits_idprop_values() -> None:
    obj = _ObjectMock(_manual_idprops(0.25, 0.5, 0.25, 0.25))
    uvs = [[0.0, 0.0], [1.0, 1.0]]  # ignored in manual mode
    assert resolve_region(obj, uvs) == [0.25, 0.5, 0.25, 0.25]


def test_resolve_manual_reads_each_region_idprop() -> None:
    obj = _ObjectMock(_manual_idprops(0.1, 0.2, 0.3, 0.4))
    assert resolve_region(obj, [[0.0, 0.0]]) == [0.1, 0.2, 0.3, 0.4]


def test_manual_region_or_none_returns_none_in_auto_mode() -> None:
    obj = _ObjectMock(_auto_idprops())
    assert manual_region_or_none(obj) is None


def test_manual_region_or_none_returns_tuple_in_manual_mode() -> None:
    obj = _ObjectMock(_manual_idprops(0.0, 0.5, 0.5, 0.5))
    assert manual_region_or_none(obj) == [0.0, 0.5, 0.5, 0.5]
