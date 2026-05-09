"""Assemble simple_psd.blend by running the addon importer (SPEC 006 Wave 6.5).

Run with::

    blender --background --python scripts/fixtures/simple_psd/build_blend.py

This is the smallest end-to-end exercise of the SPEC 006 importer:

1. Loads ``examples/simple_psd/simple_psd.photoshop_manifest.json``
   (committed alongside the fixture).
2. Calls the addon's ``import_manifest()`` to stamp planes + armature.
3. Saves ``examples/simple_psd/simple_psd.blend``.

The fixture's golden ``.proscenio`` is then produced by running
``scripts/fixtures/_shared/export_proscenio.py`` against the resulting
blend, the same flow used by the doll / blink_eyes / shared_atlas
fixtures. ``run_tests.py`` auto-discovers the new fixture once the
golden is committed.

Run ``draw_layers.py`` first or this script aborts on missing PNGs
(the importer's resolver checks each layer / frame path).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
ADDON_DIR = REPO_ROOT / "apps/blender"
ADDON_PACKAGE = "proscenio"
FIXTURE_DIR = REPO_ROOT / "examples" / "simple_psd"
MANIFEST_PATH = FIXTURE_DIR / "simple_psd.photoshop_manifest.json"
BLEND_PATH = FIXTURE_DIR / "simple_psd.blend"


def main() -> None:
    if not MANIFEST_PATH.exists():
        print(f"[build_simple_psd] missing {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    _load_addon_as_package()
    _wipe_blend()
    _run_importer()
    _save_blend()
    print(f"[build_simple_psd] wrote {BLEND_PATH}")


def _load_addon_as_package() -> None:
    """Register ``apps/blender/`` under sys.modules as ``proscenio``.

    Mirrors ``apps/blender/tests/run_tests.py``: the addon's submodules
    use relative imports rooted at the manifest package name, but the
    folder on disk has a hyphen which is not a valid identifier.
    """
    if ADDON_PACKAGE in sys.modules:
        return
    init_path = ADDON_DIR / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        ADDON_PACKAGE,
        init_path,
        submodule_search_locations=[str(ADDON_DIR)],
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not build import spec for {init_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[ADDON_PACKAGE] = module
    spec.loader.exec_module(module)


def _wipe_blend() -> None:
    for collection in (
        bpy.data.objects,
        bpy.data.meshes,
        bpy.data.armatures,
        bpy.data.materials,
        bpy.data.images,
        bpy.data.actions,
    ):
        while collection:
            collection.remove(collection[0])


def _run_importer() -> None:
    from proscenio.importers.photoshop import import_manifest  # type: ignore[import-not-found]

    result = import_manifest(MANIFEST_PATH, placement="centered")
    print(
        f"[build_simple_psd] importer stamped {len(result.meshes)} mesh(es), "
        f"{len(result.spritesheets)} spritesheet(s)"
    )


def _save_blend() -> None:
    BLEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[build_simple_psd] FAILED: {exc}", file=sys.stderr)
        raise
