"""Unit tests for proscenio_models field-level validators."""

from __future__ import annotations

import pytest
from proscenio_models import MeshElement
from pydantic import ValidationError


def _quad_kwargs() -> dict[str, object]:
    return {
        "name": "blob",
        "texture_region": [0.0, 0.0, 1.0, 1.0],
        "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        "uv": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
    }


def test_mesh_element_accepts_multi_face_polygons() -> None:
    element = MeshElement(**_quad_kwargs(), polygons=[[0, 1, 2], [0, 2, 3]])
    assert element.polygons == [[0, 1, 2], [0, 2, 3]]


def test_mesh_element_omits_polygons_by_default() -> None:
    element = MeshElement(**_quad_kwargs())
    assert element.polygons is None


def test_mesh_element_rejects_out_of_range_polygon_index() -> None:
    with pytest.raises(ValidationError, match="out of range"):
        MeshElement(**_quad_kwargs(), polygons=[[0, 1, 4]])
