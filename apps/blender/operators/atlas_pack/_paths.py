"""Atlas-pack output path derivation."""

from __future__ import annotations

from pathlib import Path

import bpy


def packed_atlas_paths(blend_path: str) -> tuple[Path, Path]:
    """Return ``(atlas_png_path, manifest_json_path)`` next to the .blend."""
    blend = Path(blend_path) if blend_path else Path("untitled.blend")
    stem = blend.stem if blend.stem else "atlas_packed"
    folder = blend.parent if blend_path else Path(bpy.path.abspath("//"))
    return folder / f"{stem}.atlas.png", folder / f"{stem}.atlas.json"
