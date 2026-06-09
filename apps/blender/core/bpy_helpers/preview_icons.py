"""Custom preview icons loaded through ``bpy.utils.previews``.

Ships the godot-ready badge mark (``icons/godot_ready.png``, the official
Godot icon) so the GODOT_READY status band can render a distinct glyph
instead of the generic ``CHECKMARK``. Loaded once at addon register; the
panel header reads the ``icon_value`` off this collection and falls back
to ``CHECKMARK`` when the load is unavailable (headless mounts, missing
file), so a failed load degrades instead of crashing the header draw.
"""

from __future__ import annotations

from pathlib import Path

import bpy.utils.previews

# icons/ sits at the addon root: core/bpy_helpers/preview_icons.py
#   parents[0]=bpy_helpers [1]=core [2]=addon root
_ICONS_DIR = Path(__file__).resolve().parents[2] / "icons"

_collection = None  # bpy.utils.previews ImagePreviewCollection, or None when unloaded


def godot_ready_icon_id() -> int:
    """Return the ``icon_value`` for the godot-ready badge, or 0 when unavailable.

    0 is Blender's "no icon" sentinel; callers fall back to a built-in
    icon when it is returned.
    """
    if _collection is None:
        return 0
    preview = _collection.get("godot_ready")
    return int(preview.icon_id) if preview is not None else 0


def register() -> None:
    """Create the preview collection + load the godot-ready mark."""
    global _collection
    _collection = bpy.utils.previews.new()
    png = _ICONS_DIR / "godot_ready.png"
    if png.exists():
        _collection.load("godot_ready", str(png), "IMAGE")


def unregister() -> None:
    """Drop the preview collection."""
    global _collection
    if _collection is not None:
        bpy.utils.previews.remove(_collection)
        _collection = None
