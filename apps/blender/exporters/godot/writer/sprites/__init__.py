"""Element emission facade: mesh (polygon body) + sprite (frame metadata) + weights.

Split into ``mesh_element`` / ``sprite_element`` / ``weights`` with a shared
``_common`` for the appearance derivers; the public names stay importable from
``...writer.sprites`` so callers and tests are unchanged. The internal helpers
below are re-exported too because the pure writer tests reach them by attribute
(``sprites._derive_modulate`` etc.), so the split stays invisible to them.
"""

from __future__ import annotations

from ._common import _derive_modulate, _derive_z_index, resolve_sprite_bone
from .mesh_element import _build_polygon_topology, _per_sprite_texture, build_element
from .sprite_element import (
    _compute_sprite_offset,
    _derive_flips,
    _derive_rest_transform,
    build_sprite,
)
from .weights import _resolve_known_groups, _vertex_bone_weights, build_sprite_weights

__all__ = [
    "_build_polygon_topology",
    "_compute_sprite_offset",
    "_derive_flips",
    "_derive_modulate",
    "_derive_rest_transform",
    "_derive_z_index",
    "_per_sprite_texture",
    "_resolve_known_groups",
    "_vertex_bone_weights",
    "build_element",
    "build_sprite",
    "build_sprite_weights",
    "resolve_sprite_bone",
]
