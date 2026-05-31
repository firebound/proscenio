"""Headless automesh validator entry point.

Thin shim. Actual code lives in the ``proscenio_validator`` package
under ``packages/validator/src/proscenio_validator/``:

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

    blender --background --python packages/validator/scripts/validate_automesh.py \\
        -- --ci-only

The ``--`` separates Blender args from script args. CI invokes the
``--ci-only`` form so heavyweight fixtures (swirl) are skipped; the
plain form runs every sprite for local smoke.

Blender's bundled Python does not see the uv workspace install, so
this shim manually adds ``packages/validator/src`` to ``sys.path`` to
resolve the ``proscenio_validator`` package.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Mount the validator package on sys.path so ``proscenio_validator``
# resolves under Blender's bundled Python (which does not honour the
# uv workspace install).
_VALIDATOR_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_VALIDATOR_SRC) not in sys.path:
    sys.path.insert(0, str(_VALIDATOR_SRC))

# Mount apps/blender on sys.path so the validator's bpy-free helper
# imports (``from core.geometry_2d import ...``) resolve. Same trick
# the pytest suite uses under ``tests/test_*.py``.
from proscenio_validator.addon_loader import ensure_core_on_sys_path  # noqa: E402

ensure_core_on_sys_path()

from proscenio_validator.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
