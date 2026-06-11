"""Unit tests for proscenio_models field-level validators."""

from __future__ import annotations

import pytest
from proscenio_models import Key, MeshElement, SpriteElement, Track
from pydantic import ValidationError


def _quad_kwargs() -> dict[str, object]:
    return {
        "name": "blob",
        "texture_region": [0.0, 0.0, 1.0, 1.0],
        "polygon": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        "uv": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
    }


def _sprite_kwargs() -> dict[str, object]:
    return {"type": "sprite", "name": "head", "bone": "neck", "hframes": 1, "vframes": 1}


def test_mesh_element_accepts_multi_face_polygons() -> None:
    element = MeshElement(**_quad_kwargs(), polygons=[[0, 1, 2], [0, 2, 3]])
    assert element.polygons == [[0, 1, 2], [0, 2, 3]]


def test_mesh_element_omits_polygons_by_default() -> None:
    element = MeshElement(**_quad_kwargs())
    assert element.polygons is None


def test_mesh_element_rejects_out_of_range_polygon_index() -> None:
    with pytest.raises(ValidationError, match="out of range"):
        MeshElement(**_quad_kwargs(), polygons=[[0, 1, 4]])


def test_mesh_element_round_trips_appearance() -> None:
    element = MeshElement(**_quad_kwargs(), modulate=[1.0, 0.5, 0.25, 1.0], z_index=3)
    back = MeshElement.model_validate_json(element.model_dump_json())
    assert back.modulate == [1.0, 0.5, 0.25, 1.0]
    assert back.z_index == 3


def test_mesh_element_omits_appearance_by_default() -> None:
    element = MeshElement(**_quad_kwargs())
    assert element.modulate is None
    assert element.z_index is None
    dumped = element.model_dump(exclude_unset=True)
    assert "modulate" not in dumped
    assert "z_index" not in dumped


def test_mesh_element_rejects_modulate_of_wrong_length() -> None:
    # Match the length error, not the extra-forbidden one, so the test only
    # passes once the field exists and carries the 4-component constraint.
    with pytest.raises(ValidationError, match="at least 4 items"):
        MeshElement(**_quad_kwargs(), modulate=[1.0, 1.0, 1.0])


def test_mesh_element_rejects_out_of_bounds_z_index() -> None:
    with pytest.raises(ValidationError, match="less than or equal to 4096"):
        MeshElement(**_quad_kwargs(), z_index=99999)


def test_mesh_element_rejects_a_negative_color_channel() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to 0"):
        MeshElement(**_quad_kwargs(), modulate=[-0.1, 1.0, 1.0, 1.0])


def test_sprite_element_round_trips_appearance() -> None:
    element = SpriteElement(
        **_sprite_kwargs(), modulate=[1.0, 0.5, 0.25, 1.0], z_index=-2, flip_h=True, flip_v=False
    )
    back = SpriteElement.model_validate_json(element.model_dump_json())
    assert back.modulate == [1.0, 0.5, 0.25, 1.0]
    assert back.z_index == -2
    assert back.flip_h is True
    assert back.flip_v is False


def test_track_rejects_the_retired_visibility_type() -> None:
    # The slot system owns show/hide; the visibility track was an unimplemented
    # stub on both sides and is retired.
    with pytest.raises(ValidationError):
        Track(type="visibility", target="mouth", keys=[])


def test_key_rejects_the_retired_visible_field() -> None:
    with pytest.raises(ValidationError, match="visible"):
        Key(time=0.0, visible=True)


def test_sprite_element_omits_appearance_by_default() -> None:
    element = SpriteElement(**_sprite_kwargs())
    assert element.modulate is None
    assert element.z_index is None
    assert element.flip_h is None
    assert element.flip_v is None
    dumped = element.model_dump(exclude_unset=True)
    assert not ({"modulate", "z_index", "flip_h", "flip_v"} & dumped.keys())
