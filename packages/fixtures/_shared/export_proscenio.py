"""Headless re-exporter - runs the addon's writer over a fixture .blend.

Companion to the fixture builders. After ``build_<fixture>.py`` produces
the ``.blend``, this script opens it and writes the ``.proscenio`` golden
to ``<fixture_dir>/<fixture>.expected.proscenio``.

Run with::

    blender --background <fixture>.blend \\
        --python packages/fixtures/export_proscenio.py

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
ADDON_PATH = REPO_ROOT / "apps/blender"
ADDON_PACKAGE = "proscenio"  # matches apps/blender/blender_manifest.toml `id`
MODELS_SRC = REPO_ROOT / "packages" / "models" / "src"


def _prefer_source_models() -> None:
    """Make the in-repo ``proscenio_models`` win over the installed extension copy.

    Same shim as run_tests.py: the auto-enabled extension bundles a
    version-keyed ``proscenio_models`` wheel that Blender never re-unpacks on
    a same-version field change, and it is already imported at enable. Without
    this, a golden regenerated right after a model change silently drops the
    new fields.
    """
    if not MODELS_SRC.is_dir():
        print(
            f"[export_proscenio] WARN: models source not at {MODELS_SRC}; "
            "using the installed copy",
            file=sys.stderr,
        )
        return
    sys.path.insert(0, str(MODELS_SRC))
    for name in [
        m for m in sys.modules if m == "proscenio_models" or m.startswith("proscenio_models.")
    ]:
        del sys.modules[name]


def _load_addon_as_package() -> None:
    """Register ``apps/blender/`` under sys.modules as ``proscenio``.

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
            "[export_proscenio] no .blend open - pass it via the command line",
            file=sys.stderr,
        )
        sys.exit(1)
    blend_path = Path(blend)
    out_path = blend_path.parent / f"{blend_path.stem}.expected.proscenio"

    _prefer_source_models()
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
