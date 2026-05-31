"""Round-trip tests for the proscenio_models pydantic source of truth.

Confirms:

1. ``proscenio_codegen schemas`` produces a JSON Schema dict that is
   stable across runs (no nondeterministic ordering, the file is
   reproducible from the models alone).
2. Every committed ``.proscenio`` fixture under ``examples/generated/``
   validates against the pydantic model. This is the practical gate
   for SPEC 014: if the model fails to accept a real shipped fixture,
   the model is wrong.
3. ``model_dump_json(exclude_unset=True)`` reproduces each golden
   byte-for-byte. This is the load-bearing gate for the writer
   migration: any drift between the pydantic field order and the
   writer's historical dict insertion order would surface here before
   the Blender exporter regenerates a single fixture.
4. The dumped JSON Schema at ``packages/models/schemas/proscenio.schema.json``
   is on disk and parseable - the writer-side validation chain relies
   on it staying in lockstep with the pydantic models.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from proscenio_codegen.schema_dump import build_proscenio_schema
from proscenio_models import ProscenioDocument

REPO_ROOT = Path(__file__).resolve().parents[2]
PROSCENIO_SCHEMA = (
    REPO_ROOT / "packages" / "models" / "schemas" / "proscenio.schema.json"
)
PSD_MANIFEST_SCHEMA = (
    REPO_ROOT / "packages" / "models" / "schemas" / "psd_manifest.schema.json"
)
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


@pytest.mark.parametrize("fixture_path", _fixture_paths(), ids=lambda p: p.name)
def test_model_dump_json_reproduces_goldens(fixture_path: Path) -> None:
    """Pydantic's ``model_dump_json(exclude_unset=True)`` must reproduce
    the goldens byte-for-byte after a parse round-trip.

    The writer migration in SPEC 014 P2 swaps the hand-rolled
    ``json.dumps(doc, indent=2)`` for the pydantic emit path; this
    test is the load-bearing gate that catches any field-order or
    serialization drift between the model and the historical writer.

    Strip trailing whitespace before comparing because some goldens
    were generated on Windows (CRLF) and pydantic always writes LF.
    """
    golden_text = fixture_path.read_text(encoding="utf-8")
    payload = json.loads(golden_text)
    parsed = ProscenioDocument.model_validate(payload)
    actual = parsed.model_dump_json(indent=2, exclude_unset=True)
    # Normalize line endings; ignore trailing newline differences.
    assert actual.rstrip("\n") == golden_text.rstrip("\n").replace("\r\n", "\n")


def test_proscenio_schema_on_disk_matches_models() -> None:
    """The on-disk .proscenio schema dump matches the in-memory build."""
    assert PROSCENIO_SCHEMA.is_file(), (
        "Run `python -m proscenio_codegen schemas` to regenerate."
    )
    on_disk = json.loads(PROSCENIO_SCHEMA.read_text(encoding="utf-8"))
    in_memory = build_proscenio_schema()
    assert on_disk == in_memory, (
        "Dumped .proscenio schema drifted from the pydantic models. "
        "Run `python -m proscenio_codegen schemas`."
    )


def test_psd_manifest_schema_on_disk_matches_models() -> None:
    """The on-disk PSD manifest schema dump matches the in-memory build."""
    from proscenio_codegen.schema_dump import build_psd_manifest_schema

    assert PSD_MANIFEST_SCHEMA.is_file(), (
        "Run `python -m proscenio_codegen schemas` to regenerate."
    )
    on_disk = json.loads(PSD_MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    in_memory = build_psd_manifest_schema()
    assert on_disk == in_memory, (
        "Dumped PSD manifest schema drifted from the pydantic models. "
        "Run `python -m proscenio_codegen schemas`."
    )
