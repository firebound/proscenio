"""Custom preview icons loaded through ``bpy.utils.previews``.

Ships the per-engine badge marks (``icons/godot.png``, ``icons/blender.png``)
so the GODOT_READY and BLENDER_ONLY status bands render a distinct glyph
instead of a generic built-in icon. Loaded once at addon register; the
panel header reads the ``icon_value`` off this collection and falls back
to the band's built-in icon when a load is unavailable (headless mounts,
missing file), so a failed load degrades instead of crashing the draw.
"""

from __future__ import annotations

from pathlib import Path

import bpy.utils.previews

# icons/ sits at the addon root: core/bpy_helpers/preview_icons.py
#   parents[0]=bpy_helpers [1]=core [2]=addon root
_ICONS_DIR = Path(__file__).resolve().parents[2] / "icons"

_BADGES = ("godot", "blender")

_collection = None  # bpy.utils.previews ImagePreviewCollection, or None when unloaded


def _icon_id(name: str) -> int:
    """Return the ``icon_value`` for a loaded badge, or 0 when unavailable.

    0 is Blender's "no icon" sentinel; callers fall back to a built-in
    icon when it is returned.
    """
    if _collection is None:
        return 0
    preview = _collection.get(name)
    return int(preview.icon_id) if preview is not None else 0


def godot_icon_id() -> int:
    """Return the ``icon_value`` for the Godot badge, or 0 when unavailable."""
    return _icon_id("godot")


def blender_icon_id() -> int:
    """Return the ``icon_value`` for the Blender-only badge, or 0 when unavailable."""
    return _icon_id("blender")


def register() -> None:
    """Create the preview collection + load the per-engine badge marks."""
    global _collection
    _collection = bpy.utils.previews.new()
    for name in _BADGES:
        png = _ICONS_DIR / f"{name}.png"
        if png.exists():
            _collection.load(name, str(png), "IMAGE")


def unregister() -> None:
    """Drop the preview collection."""
    global _collection
    if _collection is not None:
        bpy.utils.previews.remove(_collection)
        _collection = None
