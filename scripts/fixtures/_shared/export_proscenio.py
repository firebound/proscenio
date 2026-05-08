"""Headless re-exporter — runs the addon's writer over a fixture .blend.

Companion to the SPEC 007 builders. After ``build_<fixture>.py`` produces
the ``.blend``, this script opens it and writes the ``.proscenio`` golden
to ``<fixture_dir>/<fixture>.expected.proscenio``.

Run with::

    blender --background <fixture>.blend \\
        --python scripts/fixtures/export_proscenio.py

The script discovers the open .blend via ``bpy.data.filepath``, derives
the output path from the .blend stem, and invokes
``proscenio.exporters.godot.writer.export``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[3]
ADDON_PATH = REPO_ROOT / "blender-addon"
ADDON_PACKAGE = "proscenio"  # matches blender-addon/blender_manifest.toml `id`


def _load_addon_as_package() -> None:
    """Register ``blender-addon/`` under sys.modules as ``proscenio``.

    The addon ships as a Blender extension named ``proscenio`` (per its
    manifest), and its submodules use relative imports rooted at that
    package name (e.g. ``from ...core import region``). Loading the
    extension via Blender's ``addon_utils`` is fragile in headless mode,
    so instead we install the directory as a synthetic package under
    that name. Subsequent ``from proscenio.X import Y`` calls resolve
    naturally.
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


def main() -> None:
    blend = bpy.data.filepath
    if not blend:
        print(
            "[export_proscenio] no .blend open — pass it via the command line",
            file=sys.stderr,
        )
        sys.exit(1)
    blend_path = Path(blend)
    out_path = blend_path.parent / f"{blend_path.stem}.expected.proscenio"

    _load_addon_as_package()
    from proscenio.exporters.godot import writer  # type: ignore[import-not-found]

    writer.export(out_path, pixels_per_unit=100.0)
    print(f"[export_proscenio] wrote {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[export_proscenio] FAILED: {exc}", file=sys.stderr)
        raise
