"""Mount apps/blender as the ``proscenio`` package + register classes.

Used by the headless validator to make ``bpy.ops.proscenio.*`` resolve
in a Blender session that does not have the addon installed (CI runner,
fresh dev machine). Mirrors the module-load pattern in
``apps/blender/tests/run_tests.py`` plus the extra register() step
that operator access needs.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ADDON_PACKAGE = "proscenio"
REPO_ROOT = Path(__file__).resolve().parents[2]
ADDON_PATH = REPO_ROOT / "apps" / "blender"


def ensure_core_on_sys_path() -> None:
    """Add ``apps/blender`` to ``sys.path`` so ``from core.*`` imports work.

    Mirrors the same trick the pytest suite uses. Idempotent.
    """
    addon_path_str = str(ADDON_PATH)
    if addon_path_str not in sys.path:
        sys.path.insert(0, addon_path_str)


def load_and_register_addon() -> None:
    """Mount the addon as ``proscenio`` + call its register() entry."""
    if ADDON_PACKAGE not in sys.modules:
        init_path = ADDON_PATH / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            ADDON_PACKAGE,
            init_path,
            submodule_search_locations=[str(ADDON_PATH)],
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not build import spec for {init_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[ADDON_PACKAGE] = module
        spec.loader.exec_module(module)
    sys.modules[ADDON_PACKAGE].register()
