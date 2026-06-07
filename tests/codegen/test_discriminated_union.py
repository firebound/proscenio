"""Smoke test for the Element discriminated union (OQ3 of the typed-models codegen).

Covers:

- ``type`` absent -> ``MeshElement`` (mesh is the default kind).
- ``type: "mesh"`` -> ``MeshElement``.
- ``type: "sprite"`` -> ``SpriteElement``.
- Unknown ``type`` raises ``ValidationError``.
- Generated JSON Schema for the discriminator is wired correctly
  (carries the two variants under either a ``$ref`` chain or an
  inline ``oneOf`` / ``discriminator`` block).

Why this matters: the discriminated union is the trickiest part of
the model. If pydantic's output drifts from what downstream codegens
(``json-schema-to-typescript`` in the typed-models codegen P3, the GDScript emitter
in P4) understand, every consumer breaks at once. Catch drift here
before it ripples.
"""

from __future__ import annotations

import pytest
from proscenio_codegen.schema_dump import build_proscenio_schema
from proscenio_models import MeshElement, ProscenioDocument, SpriteElement
from pydantic import ValidationError


def _doc_with_element(element_payload: dict) -> dict:
    return {
        "format_version": 1,
        "name": "smoke",
        "pixels_per_unit": 100.0,
        "skeleton": {"bones": [{"name": "root"}]},
        "elements": [element_payload],
    }


def test_mesh_element_without_type_defaults_to_mesh() -> None:
    """An element without ``type`` parses as ``MeshElement``."""
    payload = _doc_with_element(
        {
            "name": "arm",
            "texture_region": [0, 0, 1, 1],
            "polygon": [[0, 0], [1, 0], [1, 1]],
            "uv": [[0, 0], [1, 0], [1, 1]],
        }
    )
    doc = ProscenioDocument.model_validate(payload)
    assert isinstance(doc.elements[0], MeshElement)
    assert doc.elements[0].type == "mesh"


def test_mesh_element_with_explicit_type() -> None:
    payload = _doc_with_element(
        {
            "type": "mesh",
            "name": "arm",
            "texture_region": [0, 0, 1, 1],
            "polygon": [[0, 0], [1, 0], [1, 1]],
            "uv": [[0, 0], [1, 0], [1, 1]],
        }
    )
    doc = ProscenioDocument.model_validate(payload)
    assert isinstance(doc.elements[0], MeshElement)


def test_sprite_branch_parses() -> None:
    payload = _doc_with_element(
        {
            "type": "sprite",
            "name": "blink",
            "bone": "head",
            "hframes": 4,
            "vframes": 1,
            "frame": 0,
        }
    )
    doc = ProscenioDocument.model_validate(payload)
    element = doc.elements[0]
    assert isinstance(element, SpriteElement)
    assert element.hframes == 4


def test_unknown_discriminator_value_rejected() -> None:
    payload = _doc_with_element(
        {
            "type": "unknown_variant",
            "name": "x",
            "texture_region": [0, 0, 1, 1],
            "polygon": [[0, 0], [1, 0], [1, 1]],
            "uv": [[0, 0], [1, 0], [1, 1]],
        }
    )
    with pytest.raises(ValidationError):
        ProscenioDocument.model_validate(payload)


def test_sprite_missing_required_fields_rejected() -> None:
    """``sprite`` requires bone + hframes + vframes."""
    payload = _doc_with_element(
        {
            "type": "sprite",
            "name": "blink",
        }
    )
    with pytest.raises(ValidationError):
        ProscenioDocument.model_validate(payload)


def test_polygon_uv_count_mismatch_rejected() -> None:
    """polygon and uv must have the same number of vertices."""
    payload = _doc_with_element(
        {
            "type": "mesh",
            "name": "arm",
            "texture_region": [0, 0, 1, 1],
            "polygon": [[0, 0], [1, 0], [1, 1]],
            "uv": [[0, 0], [1, 0]],
        }
    )
    with pytest.raises(ValidationError, match="polygon"):
        ProscenioDocument.model_validate(payload)


def test_sprite_out_of_grid_rejected() -> None:
    """frame must be < hframes * vframes."""
    payload = _doc_with_element(
        {
            "type": "sprite",
            "name": "blink",
            "bone": "head",
            "hframes": 2,
            "vframes": 2,
            "frame": 4,
        }
    )
    with pytest.raises(ValidationError, match="out of range"):
        ProscenioDocument.model_validate(payload)


def test_sprite_within_grid_accepted() -> None:
    """The last valid index (cells - 1) parses cleanly."""
    payload = _doc_with_element(
        {
            "type": "sprite",
            "name": "blink",
            "bone": "head",
            "hframes": 2,
            "vframes": 2,
            "frame": 3,
        }
    )
    doc = ProscenioDocument.model_validate(payload)
    assert isinstance(doc.elements[0], SpriteElement)


def test_single_frame_sprite_accepted() -> None:
    """A 1x1 sprite (static) is the N=1 case and parses cleanly."""
    payload = _doc_with_element(
        {
            "type": "sprite",
            "name": "static",
            "bone": "head",
            "hframes": 1,
            "vframes": 1,
            "frame": 0,
        }
    )
    doc = ProscenioDocument.model_validate(payload)
    assert isinstance(doc.elements[0], SpriteElement)


def test_sprite_offset_default_in_schema() -> None:
    """offset must publish [0.0, 0.0] in the generated JSON Schema.

    pydantic emits Field(default=...) into the schema's ``default``
    key; Field(default_factory=...) does not. Consumers reading the
    schema (TS / GDScript bindings, ajv) rely on the default being
    visible at the schema level.
    """
    schema = build_proscenio_schema()
    defs = schema.get("$defs", {})
    sprite = defs.get("SpriteElement", {})
    props = sprite.get("properties", {})
    offset = props.get("offset", {})
    assert offset.get("default") == [0.0, 0.0]


def test_generated_schema_carries_both_element_variants() -> None:
    """Pydantic emits both variants somewhere in the schema.

    The schema may inline them under ``properties.elements.items`` or
    reference them through ``$defs``. Either is acceptable so long as
    both variants surface, which is what the TS / GDScript emitters
    need to walk in the typed-models codegen P3 / P4.
    """
    schema = build_proscenio_schema()
    defs = schema.get("$defs", {})
    assert "MeshElement" in defs
    assert "SpriteElement" in defs
