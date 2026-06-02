"""Staleness gate for the TypeScript binding emitter.

Mirrors ``test_godot_emit``: the committed ``schema_bindings/*.ts`` must
reproduce from the current pydantic models (via the schemas the models
dump). Skipped when Node / npx is absent - the Photoshop build job is the
gate there. The comparison reads through ``read_text`` so it is
line-ending agnostic; only real content drift fails the assertion.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
from proscenio_codegen.ts_emit import (
    PHOTOSHOP_BINDINGS_DIR,
    SCHEMAS_DIR,
    emit_ts_bindings,
)


def _node_available() -> bool:
    return shutil.which("npx") is not None or shutil.which("npx.cmd") is not None


@pytest.mark.skipif(
    not _node_available(),
    reason="ts emit requires Node + npx on PATH; skipped on host without it",
)
def test_committed_ts_bindings_match_emit() -> None:
    """The checked-in .ts bindings reproduce from the current schemas.

    Catches a contributor who edited a generated file by hand, or changed a
    model without re-running ``python -m proscenio_codegen ts``.
    """
    if not PHOTOSHOP_BINDINGS_DIR.is_dir():
        pytest.skip("schema_bindings/ not committed yet")

    with tempfile.TemporaryDirectory() as tmp_str:
        fresh = Path(tmp_str)
        emit_ts_bindings(SCHEMAS_DIR, fresh)
        for committed in PHOTOSHOP_BINDINGS_DIR.glob("*.ts"):
            fresh_file = fresh / committed.name
            assert fresh_file.is_file(), f"emitter no longer produces {committed.name}"
            assert fresh_file.read_text(encoding="utf-8") == committed.read_text(
                encoding="utf-8"
            ), (
                f"{committed.name} differs from the schema-derived emit. "
                "Run `python -m proscenio_codegen ts`."
            )
