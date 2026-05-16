"""Pure helpers for inspecting viewport state (SPEC 012.1).

bpy-free. Operates on plain matrix data (sequences of sequences) so
unit tests can verify the Front-Orthographic detection without a
Blender session.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


_DEFAULT_TOLERANCE = 1e-4


def is_front_ortho(
    view_perspective: str,
    view_matrix_3x3: Sequence[Sequence[float]],
    tolerance: float = _DEFAULT_TOLERANCE,
) -> bool:
    """Return ``True`` when the supplied region view is Front Orthographic.

    Front Orthographic in Blender has ``view_perspective == "ORTHO"``
    and a 3x3 view-matrix rotation indistinguishable from the identity
    (the camera looks down -Y, with X right and Z up - the canonical
    Proscenio picture plane).
    """
    if view_perspective != "ORTHO":
        return False
    if len(view_matrix_3x3) < 3:
        return False
    delta_sq = 0.0
    for row_index in range(3):
        row = view_matrix_3x3[row_index]
        if len(row) < 3:
            return False
        for col_index in range(3):
            expected = 1.0 if row_index == col_index else 0.0
            diff = float(row[col_index]) - expected
            delta_sq += diff * diff
    return delta_sq < tolerance * tolerance
