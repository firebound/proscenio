"""JSON Schema emitter.

Calls ``model_json_schema()`` on each pydantic root model in
``proscenio_models`` and writes the result under
``packages/models/schemas/``. The schema lives next to the models
that produced it so the source-of-truth chain is one folder hop.
"""

from __future__ import annotations

from pathlib import Path

from proscenio_models import ProscenioDocument, PsdManifest

from proscenio_codegen._io import REPO_ROOT, dumps_json, write_atomic

SCHEMAS_DIR = REPO_ROOT / "packages" / "models" / "schemas"
PROSCENIO_SCHEMA_FILENAME = "proscenio.schema.json"
PSD_MANIFEST_SCHEMA_FILENAME = "psd_manifest.schema.json"


def build_proscenio_schema() -> dict[str, object]:
    """Return the ``.proscenio`` JSON Schema as a dict."""
    return ProscenioDocument.model_json_schema()


def build_psd_manifest_schema() -> dict[str, object]:
    """Return the PSD manifest JSON Schema as a dict."""
    return PsdManifest.model_json_schema()


def emit_proscenio_schema(schemas_dir: Path = SCHEMAS_DIR) -> Path:
    target = schemas_dir / PROSCENIO_SCHEMA_FILENAME
    payload = dumps_json(build_proscenio_schema())
    write_atomic(target, payload)
    return target


def emit_psd_manifest_schema(schemas_dir: Path = SCHEMAS_DIR) -> Path:
    target = schemas_dir / PSD_MANIFEST_SCHEMA_FILENAME
    payload = dumps_json(build_psd_manifest_schema())
    write_atomic(target, payload)
    return target


def emit_all_schemas(schemas_dir: Path = SCHEMAS_DIR) -> list[Path]:
    """Emit every schema this codegen owns. Returns paths written."""
    return [
        emit_proscenio_schema(schemas_dir),
        emit_psd_manifest_schema(schemas_dir),
    ]
