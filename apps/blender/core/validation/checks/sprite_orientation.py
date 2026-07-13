"""Sprite-orientation check: warn for a sprite quad tilted off the picture plane.

Distinct from mesh-flatness (which catches a genuinely 3D mesh): a sprite quad
can be perfectly planar yet tilted so its face turns edge-on to the camera - a
snap bone parent (Ctrl+P > Bone without Keep Transform) to an in-plane bone, or
a hand-rotated object. The rest transform (spec 080) then projects to a
foreshortened / skewed placement. A keep-transform bone parent, an in-plane
rotation, and every flat authored sprite keep the quad facing the camera and do
not warn - which is why this replaces the old blanket "in-plane bone" panel
caveat with a check that fires on the actual geometry problem.
"""

from __future__ import annotations

from ..._shared.cp_keys import PROSCENIO_TYPE
from ..._shared.pg_cp_fallback import read_field
from ...godot_export_math import sprite_off_picture_plane
from .._shared import name_of
from ..issue import Issue


def validate_sprite_orientation(obj: object) -> list[Issue]:
    """Warn when a sprite element's quad is tilted off the picture plane."""
    if str(read_field(obj, cp_key=PROSCENIO_TYPE, default="mesh")) != "sprite":
        return []
    matrix_world = getattr(obj, "matrix_world", None)
    if matrix_world is None:
        return []
    if not sprite_off_picture_plane(matrix_world):
        return []
    return [
        Issue(
            "warning",
            "sprite is tilted off the picture plane - its quad turns edge-on to "
            "the camera, so the exported rest transform comes out foreshortened; "
            "keep the sprite facing front (a Keep-Transform bone bind stays flat)",
            name_of(obj),
        )
    ]
