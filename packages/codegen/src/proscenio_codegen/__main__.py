"""CLI entry point for the codegen pipeline.

Subcommands:

- ``schemas`` - dump JSON Schema from the pydantic models.
- ``ts`` - emit TypeScript bindings from the dumped JSON Schemas via
  ``json-schema-to-typescript``; output lands under
  ``apps/photoshop/src/schema_bindings/``.
- ``godot`` - emit GDScript ``Resource`` classes from the pydantic
  models directly; output lands under
  ``apps/godot/addons/proscenio/schema_bindings/``.
- ``docs`` - emit Markdown reference for every dumped schema via
  ``@adobe/jsonschema2md``; output lands under
  ``docs/content/api/schemas/`` for Docusaurus (or any other Markdown
  reader) to pick up.
- ``all`` - run every emitter in order.

Exit code 0 on success, non-zero on emitter failure. The expected
operator invocation is::

    python -m proscenio_codegen schemas
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable

from proscenio_codegen.docs_emit import emit_docs
from proscenio_codegen.godot_emit import emit_godot_resources
from proscenio_codegen.schema_dump import emit_all_schemas
from proscenio_codegen.ts_emit import emit_ts_bindings


def _run_schemas() -> int:
    for target in emit_all_schemas():
        print(f"[codegen] wrote {target}")
    return 0


def _run_ts() -> int:
    for target in emit_ts_bindings():
        print(f"[codegen] wrote {target}")
    return 0


def _run_godot() -> int:
    for target in emit_godot_resources():
        print(f"[codegen] wrote {target}")
    return 0


def _run_docs() -> int:
    for target in emit_docs():
        print(f"[codegen] wrote {target}")
    return 0


def _run_all() -> int:
    rc = _run_schemas()
    if rc != 0:
        return rc
    rc = _run_ts()
    if rc != 0:
        return rc
    rc = _run_godot()
    if rc != 0:
        return rc
    return _run_docs()


_EMITTERS: dict[str, Callable[[], int]] = {
    "schemas": _run_schemas,
    "ts": _run_ts,
    "godot": _run_godot,
    "docs": _run_docs,
    "all": _run_all,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="proscenio-codegen",
        description="Emit JSON Schema and language bindings from the Proscenio pydantic models.",
    )
    parser.add_argument(
        "emitter",
        choices=sorted(_EMITTERS),
        help="Which artifact to emit. `all` runs every emitter in order.",
    )
    args = parser.parse_args(argv)
    return _EMITTERS[args.emitter]()


if __name__ == "__main__":
    sys.exit(main())
