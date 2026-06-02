"""Codegen pipeline for the Proscenio domain models.

CLI:

    python -m proscenio_codegen schemas        # dump JSON Schema
    python -m proscenio_codegen ts             # emit TypeScript bindings
    python -m proscenio_codegen godot          # emit GDScript Resources
    python -m proscenio_codegen docs           # emit Markdown docs
    python -m proscenio_codegen all            # run every emitter

Each emitter lives in its own module (``schema_dump``, ``ts_emit``,
``godot_emit``, ``docs_emit``) and shares I/O helpers via ``_io``.
"""

from __future__ import annotations
