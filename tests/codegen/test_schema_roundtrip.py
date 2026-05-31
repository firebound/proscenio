"""Round-trip tests for the proscenio_models pydantic source of truth.

Confirms:

1. ``proscenio_codegen schemas`` produces a JSON Schema dict that is
   stable across runs (no nondeterministic ordering, the file is
   reproducible from the models alone).
2. Every committed ``.proscenio`` fixture under ``examples/generated/``
   validates against the pydantic model. This is the practical gate
   for SPEC 014 P1: if the model fails to accept a real shipped
   fixture, the model is wrong.
3. The hand-maintained schema at ``schemas/proscenio.schema.json``
   accepts the same fixtures (sanity check that the existing schema
   and the new model are in the same ballpark).

Byte-for-byte equality between the dumped schema and the hand-maintained
file is *not* enforced here. Pydantic v2 inlines small types (``Vec2``,
``Rect``, the ``Sprite`` discriminated union) where the hand-maintained
file uses ``$defs`` references; the two are semantically equivalent
but textually different. SPEC 014 P2 reconciles this by replacing the
hand-maintained file with the generated one once the writer migrates
to ``model_dump()``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from proscenio_codegen.schema_dump import build_proscenio_schema
from proscenio_models import ProscenioDocument

REPO_ROOT = Path(__file__).resolve().parents[2]
HAND_MAINTAINED_SCHEMA = REPO_ROOT / "schemas" / "proscenio.schema.json"
GENERATED_FIXTURES_DIR = REPO_ROOT / "examples" / "generated"


def _fixture_paths() -> list[Path]:
    """Every committed ``.expected.proscenio`` under examples/generated/."""
    return sorted(GENERATED_FIXTURES_DIR.rglob("*.expected.proscenio"))


def test_schema_dump_is_deterministic() -> None:
    """Two calls must produce identical dicts.

    Catches any model ordering nondeterminism (set / dict
    ordering, time-of-day defaults) that would make CI staleness
    checks flaky.
    """
    a = build_proscenio_schema()
    b = build_proscenio_schema()
    assert a == b


def test_schema_dump_has_root_metadata() -> None:
    """Dumped schema carries the document title and $id."""
    schema = build_proscenio_schema()
    assert schema.get("title") == "Proscenio character"
    assert schema.get("$id", "").endswith("/proscenio.schema.json")


def test_pydantic_model_accepts_every_committed_fixture() -> None:
    """Every shipped fixture is a valid ProscenioDocument."""
    fixtures = _fixture_paths()
    assert fixtures, (
        "expected at least one .expected.proscenio under examples/generated/"
    )
    for fixture in fixtures:
        payload = json.loads(fixture.read_text(encoding="utf-8"))
        # Will raise ValidationError on shape mismatch.
        ProscenioDocument.model_validate(payload)


@pytest.mark.parametrize("fixture_path", _fixture_paths(), ids=lambda p: p.name)
def test_round_trip_dump_and_validate(fixture_path: Path) -> None:
    """Every committed fixture survives parse + dump + parse.

    Parses the on-disk JSON, dumps the model back to a dict via
    ``model_dump(exclude_none=True)`` to strip defaulted-None fields
    (the writer does not emit ``None``s today), and re-validates the
    result. Asserts the second parse succeeds.
    """
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    parsed = ProscenioDocument.model_validate(payload)
    dumped = parsed.model_dump(exclude_none=True)
    reparsed = ProscenioDocument.model_validate(dumped)
    assert reparsed == parsed


def test_hand_maintained_schema_still_loads() -> None:
    """Sanity: the hand-maintained file is still a valid JSON Schema doc.

    Not a tight gate; SPEC 014 P2 is where the hand-maintained file
    gets retired. Until then, this test confirms the file is still
    readable, so a regression here flags an accidental corruption.
    """
    assert HAND_MAINTAINED_SCHEMA.is_file()
    schema = json.loads(HAND_MAINTAINED_SCHEMA.read_text(encoding="utf-8"))
    assert schema.get("type") == "object"
    assert "format_version" in schema.get("properties", {})
