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

import sys
from pathlib import Path

import bpy

REPO_ROOT = Path(__file__).resolve().parents[2]
ADDON_PATH = REPO_ROOT / "blender-addon"

# Make the addon's package importable. The addon is normally loaded as a
# Blender extension; here we import directly so the script runs even when
# the extension is not enabled in the headless environment.
sys.path.insert(0, str(ADDON_PATH))


def main() -> None:
    blend = bpy.data.filepath
    if not blend:
        print("[export_proscenio] no .blend open — pass it via the command line", file=sys.stderr)
        sys.exit(1)
    blend_path = Path(blend)
    out_path = blend_path.parent / f"{blend_path.stem}.expected.proscenio"

    # Import lazily so the script can boot even with no addon registered.
    from exporters.godot import writer  # type: ignore[import-not-found]

    writer.export(out_path, pixels_per_unit=100.0)
    print(f"[export_proscenio] wrote {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[export_proscenio] FAILED: {exc}", file=sys.stderr)
        raise
