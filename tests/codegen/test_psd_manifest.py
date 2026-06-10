"""Smoke tests for the PSD manifest pydantic model.

Locks:

- `UintPair` rejects negative integers (the name implies unsigned).
- Unknown `kind` values surface as a ValidationError rather than
  silently routing to a non-existent variant.
- The two kinds route to their own classes: `mesh` -> `MeshLayer`,
  `sprite` -> `SpriteLayer`.
- A `sprite` layer accepts a single frame (the static case).
"""

from __future__ import annotations

import pytest
from proscenio_models import PsdManifest
from pydantic import ValidationError


def _doc_with_layer(layer_payload: dict[str, object]) -> dict[str, object]:
    return {
        "format_version": 1,
        "doc": "smoke.psd",
        "size": [100, 100],
        "pixels_per_unit": 100,
        "layers": [layer_payload],
    }


def test_mesh_layer_parses() -> None:
    doc = PsdManifest.model_validate(
        _doc_with_layer(
            {
                "kind": "mesh",
                "name": "arm",
                "path": "arm.png",
                "position": [0, 0],
                "size": [10, 10],
                "z_order": 0,
            }
        )
    )
    assert doc.layers[0].kind == "mesh"  # type: ignore[union-attr]


def test_sprite_layer_parses() -> None:
    doc = PsdManifest.model_validate(
        _doc_with_layer(
            {
                "kind": "sprite",
                "name": "blink",
                "position": [0, 0],
                "size": [10, 10],
                "z_order": 0,
                "frames": [
                    {"index": 0, "path": "blink_0.png"},
                    {"index": 1, "path": "blink_1.png"},
                ],
            }
        )
    )
    assert doc.layers[0].kind == "sprite"  # type: ignore[union-attr]


def test_single_frame_sprite_layer_parses() -> None:
    """A `[sprite]` layer yields one frame (the static sprite case)."""
    doc = PsdManifest.model_validate(
        _doc_with_layer(
            {
                "kind": "sprite",
                "name": "static",
                "position": [0, 0],
                "size": [10, 10],
                "z_order": 0,
                "frames": [{"index": 0, "path": "static.png"}],
            }
        )
    )
    assert len(doc.layers[0].frames) == 1  # type: ignore[union-attr]


def test_unknown_kind_rejected() -> None:
    """Unexpected ``kind`` values must fail validation."""
    payload = _doc_with_layer(
        {
            "kind": "phantom_variant",
            "name": "x",
            "position": [0, 0],
            "size": [1, 1],
            "z_order": 0,
        }
    )
    with pytest.raises(ValidationError):
        PsdManifest.model_validate(payload)


def test_negative_uint_pair_rejected_on_anchor() -> None:
    """UintPair items must be non-negative."""
    payload = {
        "format_version": 1,
        "doc": "smoke.psd",
        "size": [100, 100],
        "pixels_per_unit": 100,
        "anchor": [-1, 0],
        "layers": [],
    }
    with pytest.raises(ValidationError):
        PsdManifest.model_validate(payload)


def test_negative_uint_pair_rejected_on_layer_position() -> None:
    """Negative position coordinates fail validation."""
    payload = _doc_with_layer(
        {
            "kind": "mesh",
            "name": "x",
            "path": "x.png",
            "position": [0, -5],
            "size": [1, 1],
            "z_order": 0,
        }
    )
    with pytest.raises(ValidationError):
        PsdManifest.model_validate(payload)
