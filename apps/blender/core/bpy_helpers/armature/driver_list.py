"""Read the proscenio.* bone drivers off a sprite for the management list.

bpy-bound. The Drive-from-Bone panel shows one row per existing driver (its
target label + source bone) with a remove button; this turns the sprite's
``animation_data.drivers`` into those rows. The label lookup is the pure
:func:`driver_target_label`, so only the fcurve walk lives here.
"""

from __future__ import annotations

from dataclasses import dataclass

import bpy

from ...armature.driver_targets import driver_target_label  # type: ignore[import-not-found]


@dataclass(frozen=True)
class DriverRow:
    """One proscenio driver as the panel list shows it."""

    data_path: str
    label: str
    bone: str


def proscenio_driver_rows(sprite: bpy.types.Object) -> list[DriverRow]:
    """List the sprite's ``proscenio.*`` bone drivers, sorted by data path.

    Keeps only the ``proscenio.*`` data paths (the driver shortcut's own
    targets) and pulls the source bone from the first transform variable. Empty
    when the sprite has no animation data.
    """
    anim = getattr(sprite, "animation_data", None)
    if anim is None:
        return []
    rows = [
        DriverRow(
            data_path=fcurve.data_path,
            label=driver_target_label(fcurve.data_path),
            bone=_first_bone_target(fcurve.driver),
        )
        for fcurve in anim.drivers
        if fcurve.data_path.startswith("proscenio.")
    ]
    rows.sort(key=lambda row: row.data_path)
    return rows


def _first_bone_target(driver: bpy.types.Driver) -> str:
    """Source bone of ``driver``'s first transform variable, or empty string."""
    for var in driver.variables:
        for target in var.targets:
            if target.bone_target:
                return str(target.bone_target)
    return ""
