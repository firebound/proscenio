"""Shared bpy helpers for the fixture ``build_blend.py`` scripts.

Pure bpy glue reused by the per-fixture builders so the same logic is not
copy-pasted into every ``build_<fixture>.py``. Runs only inside Blender
(``blender --background --python ...``); ``bpy`` is imported lazily so the
module can be imported on a host without Blender for inspection.
"""

from __future__ import annotations

import sys


def rewrite_images_to_relpath(log_prefix: str) -> None:
    """Rewrite every loaded image filepath to a ``//``-relative path.

    Call after ``save_as_mainfile`` has put the .blend on disk (so
    ``bpy.path.relpath`` has a base to resolve against); the caller saves
    again afterward. Keeps the committed .blend machine-independent instead
    of baking a developer's repo root into it.

    ``log_prefix`` is the ``[build_<fixture>]`` tag used in the stderr note
    when a path cannot be made relative.
    """
    import bpy

    for img in bpy.data.images:
        if not img.filepath:
            continue
        try:
            img.filepath = bpy.path.relpath(img.filepath)
        except ValueError as exc:
            # bpy.path.relpath raises ValueError on Windows when the image
            # lives on a different drive letter from the .blend; the absolute
            # path still resolves, only the portability promise weakens.
            print(
                f"{log_prefix} keeping absolute path for {img.name} ({exc})",
                file=sys.stderr,
            )
