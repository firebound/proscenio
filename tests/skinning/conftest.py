"""Shared scaffolding for the pure-pytest skinning tests.

The skinning helpers under ``apps/blender/core/skinning/`` and
``core/bpy_helpers/skinning/`` are imported as the top-level ``core``
package (``from core.skinning... import ...``). Putting ``apps/blender``
on ``sys.path`` here - before any test module imports - lets every
sibling test drop its own ``REPO_ROOT`` + ``sys.path.insert`` bootstrap.

conftest is imported by pytest ahead of the test modules in this
directory, so the path is in place by the time their module-level
imports run.
"""

from __future__ import annotations

import sys
from pathlib import Path

_BLENDER_ROOT = Path(__file__).resolve().parents[2] / "apps" / "blender"

if str(_BLENDER_ROOT) not in sys.path:
    sys.path.insert(0, str(_BLENDER_ROOT))
