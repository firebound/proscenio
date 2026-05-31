"""CLI entry point for the codegen pipeline.

Subcommands:

- ``schemas`` - dump JSON Schema from the pydantic models.
- ``ts`` / ``godot`` / ``docs`` - placeholders for SPEC 014 P3-P5;
  they print a "not implemented yet" notice and exit 0 so a future
  CI step can wire them in once the emitters land.
- ``all`` - run every emitter in order.

Exit code 0 on success, non-zero on emitter failure. The expected
operator invocation is::

    python -m proscenio_codegen schemas
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable

from proscenio_codegen.schema_dump import emit_proscenio_schema


def _run_schemas() -> int:
    target = emit_proscenio_schema()
    print(f"[codegen] wrote {target}")
    return 0


def _run_pending(name: str) -> int:
    print(
        f"[codegen] {name} emitter not implemented yet (planned for a later SPEC 014 phase)"
    )
    return 0


def _run_all() -> int:
    rc = _run_schemas()
    if rc != 0:
        return rc
    for name in ("ts", "godot", "docs"):
        rc = _run_pending(name)
        if rc != 0:
            return rc
    return 0


_EMITTERS: dict[str, Callable[[], int]] = {
    "schemas": _run_schemas,
    "ts": lambda: _run_pending("ts"),
    "godot": lambda: _run_pending("godot"),
    "docs": lambda: _run_pending("docs"),
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
