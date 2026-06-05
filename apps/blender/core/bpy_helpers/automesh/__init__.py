"""bpy-bound bridge for the automesh.

Domain package wrapping the pure-Python pipeline in
``apps/blender/core/automesh/`` with the bits that need real
Blender data: image pixel reads, world-coord conversion, bmesh
construction via Constrained Delaunay, vertex-group preservation
for re-runs, debug companion emission per pipeline stage.

External callers (operators, headless validator, tests) import
the public surface through this package; internal split between
``bridge`` / ``debug`` is implementation detail.
"""

from __future__ import annotations

from .base_sprite import BASE_SPRITE_GROUP_NAME
from .bridge import _STAGE_BY_INDEX as _STAGE_BY_INDEX
from .bridge import (
    AutomeshBuildParams,
    AutomeshOverrides,
    DebugStage,
    build_automesh,
    collect_bone_segments,
    pixel_contour_to_world,
    read_alpha_grid,
)
from .debug import (
    clear_debug_objects,
    emit_bridges_debug,
    emit_contour_debug,
    emit_points_debug,
)

__all__ = [
    "BASE_SPRITE_GROUP_NAME",
    "AutomeshBuildParams",
    "AutomeshOverrides",
    "DebugStage",
    "build_automesh",
    "clear_debug_objects",
    "collect_bone_segments",
    "emit_bridges_debug",
    "emit_contour_debug",
    "emit_points_debug",
    "pixel_contour_to_world",
    "read_alpha_grid",
]
