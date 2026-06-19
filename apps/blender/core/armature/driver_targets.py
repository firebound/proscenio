"""Driver target-property catalog (pure).

The ``proscenio.*`` properties a bone driver can write to, with UI labels +
descriptions. Shared by the create-driver operator (the ``EnumProperty`` items)
and the Drive-from-Bone panel (the existing-driver list labels) so the drivable
target set has one definition.
"""

from __future__ import annotations

#: (key, label, description) for each drivable ``proscenio`` property.
DRIVER_TARGET_PROPERTIES: tuple[tuple[str, str, str], ...] = (
    ("frame", "Frame index", "Sprite-frame index - driven 0..hframes*vframes"),
    ("region_x", "Region X", "Texture region origin X (0..1)"),
    ("region_y", "Region Y", "Texture region origin Y (0..1)"),
    ("region_w", "Region W", "Texture region width (0..1)"),
    ("region_h", "Region H", "Texture region height (0..1)"),
)

_LABEL_BY_DATA_PATH = {f"proscenio.{key}": label for key, label, _ in DRIVER_TARGET_PROPERTIES}


def driver_target_label(data_path: str) -> str:
    """Human label for a driven ``proscenio`` data path, or the raw path if unknown."""
    return _LABEL_BY_DATA_PATH.get(data_path, data_path)
