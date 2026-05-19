"""Shared fixtures for headless operator pytest (SPEC 013.2 bind, Q7).

Runs INSIDE Blender via ``run_operator_tests.py``. Each test gets
a fresh-loaded automesh fixture .blend so state never leaks
between tests.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Generator
from pathlib import Path

import bpy
import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
ADDON_PATH = REPO_ROOT / "apps" / "blender"
ADDON_PACKAGE = "proscenio"
FIXTURE_PATH = REPO_ROOT / "examples" / "generated" / "automesh" / "automesh.blend"


def _load_addon_as_package() -> None:
    """Mount apps/blender as ``proscenio`` package + register classes.

    Mirrors ``run_tests.py:_load_addon_as_package`` but also calls
    ``register()`` so ``bpy.ops.proscenio.*`` resolves at test time.
    """
    if ADDON_PACKAGE in sys.modules:
        return
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
    module.register()


@pytest.fixture
def automesh_fixture() -> Generator[None, None, None]:
    """Fresh-load the automesh.blend fixture for each test."""
    _load_addon_as_package()
    if not FIXTURE_PATH.exists():
        pytest.skip(f"fixture missing at {FIXTURE_PATH}")
    bpy.ops.wm.open_mainfile(filepath=str(FIXTURE_PATH))
    yield
