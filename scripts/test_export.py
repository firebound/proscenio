"""Headless round-trip test for the Proscenio writer.

Run via:

    blender --background examples/dummy/dummy.blend --python scripts/test_export.py

Loads the writer directly from apps/blender/ (no extension install needed),
emits the result to apps/godot/test_dummy/dummy_from_blend.proscenio, and
mirrors the source-side atlas next to the output so the Godot dev project
finds it on reimport. The atlas-mirror step is dev-loop polish only —
production exports through the addon operator do not touch sibling files.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# Add ``apps/`` to sys.path so the blender addon imports as the top-level
# package ``blender``. The writer submodules use relative imports
# (``from ....core``) that only resolve when ``blender`` is a real package
# on sys.path -- inserting ``apps/blender`` directly would put ``exporters``
# at the top level and the relative imports would walk past it.
sys.path.insert(0, str(REPO_ROOT / "apps"))

from blender.exporters.godot import writer  # noqa: E402


def main() -> None:
    out_dir = REPO_ROOT / "apps/godot" / "test_dummy"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "dummy_from_blend.proscenio"
    writer.export(out, pixels_per_unit=100.0)
    print(f"wrote {out}  size={out.stat().st_size}")

    src_atlas = REPO_ROOT / "examples" / "dummy" / "atlas.png"
    if src_atlas.exists():
        dst_atlas = out_dir / src_atlas.name
        shutil.copy2(src_atlas, dst_atlas)
        print(f"mirrored atlas → {dst_atlas}")


if __name__ == "__main__":
    main()
    sys.stdout.flush()
