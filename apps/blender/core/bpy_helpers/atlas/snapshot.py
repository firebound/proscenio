"""Pre-pack snapshot scene query (bpy-bound).

Lives in core so the atlas panel can ask "does this scene have a
pre-pack atlas snapshot?" without importing across the
``panels -> operators`` boundary. The operator side
(``operators/atlas_pack``) still owns writing and reading the
per-object snapshot Custom Property; this is the read-only scene-level
predicate the UI needs to decide whether to show the Unpack button.
"""

from __future__ import annotations

import bpy

from ..._shared.cp_keys import PROSCENIO_PRE_PACK


def scene_has_pre_pack_snapshot(scene: bpy.types.Scene) -> bool:
    """True when at least one mesh in ``scene`` carries a pre-pack snapshot."""
    return any(PROSCENIO_PRE_PACK in obj for obj in scene.objects if obj.type == "MESH")
