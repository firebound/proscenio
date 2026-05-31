"""Headless automesh validator entry point (the weight-paint-automesh first cut).

Thin shim. Actual code lives under ``scripts/automesh_validator/``:

- ``addon_loader.py`` mounts ``apps/blender`` as the ``proscenio``
  package and registers operator classes.
- ``invariants.py`` owns ``SpriteInvariants`` + ``SPRITE_BOUNDS`` +
  ``check_invariants``.
- ``coverage.py`` runs the per-pixel coverage + hole-bleed check
  and writes the RGBA debug PNG.
- ``measurement.py`` invokes the operator per sprite + collects
  metrics.
- ``report.py`` prints the console report + optional JSON dump.
- ``cli.py`` parses args + orchestrates the run.

Run via headless Blender::

    blender --background --python scripts/validate_automesh.py \\
        -- --ci-only

The ``--`` separates Blender args from script args. CI invokes the
``--ci-only`` form so heavyweight fixtures (swirl) are skipped; the
plain form runs every sprite for local smoke.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Mount the validator package on sys.path so the imports resolve when
# Blender invokes this file directly (Blender's --python adds only
# the file's directory; the package sits at the same level).
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# Mount apps/blender on sys.path so the validator's bpy-free helper
# imports (``from core.geometry_2d import ...``) resolve. Same trick
# the pytest suite uses under ``tests/test_*.py``.
from automesh_validator.addon_loader import ensure_core_on_sys_path  # noqa: E402

ensure_core_on_sys_path()

from automesh_validator.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
