"""JSON Schema emitter.

Calls ``model_json_schema()`` on each pydantic root model in
``proscenio_models`` and writes the result under
``packages/models/schemas/``. The schema lives next to the models
that produced it so the source-of-truth chain is one folder hop.
"""

from __future__ import annotations

from pathlib import Path

from proscenio_models import ProscenioDocument

from proscenio_codegen._io import REPO_ROOT, dumps_json, write_atomic

SCHEMAS_DIR = REPO_ROOT / "packages" / "models" / "schemas"
PROSCENIO_SCHEMA_FILENAME = "proscenio.schema.json"


def build_proscenio_schema() -> dict[str, object]:
    """Return the ``.proscenio`` JSON Schema as a dict.

    Exposed separately from the file-emit path so the round-trip
    tests can introspect the schema without touching disk.
    """
    return ProscenioDocument.model_json_schema()


def emit_proscenio_schema(schemas_dir: Path = SCHEMAS_DIR) -> Path:
    """Write the ``.proscenio`` JSON Schema to disk.

    Returns the path written. Atomic via tempfile + rename; safe
    against ctrl-C mid-write.
    """
    target = schemas_dir / PROSCENIO_SCHEMA_FILENAME
    payload = dumps_json(build_proscenio_schema())
    write_atomic(target, payload)
    return target
