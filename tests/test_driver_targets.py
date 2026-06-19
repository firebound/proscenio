"""Unit tests for the driver target-property catalog.

Pure pytest, no Blender. ``driver_target_label`` maps a driven
``proscenio.<prop>`` data path back to the UI label the Drive-from-Bone list
shows; the catalog is the single source the create operator + the list share.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.armature.driver_targets import (  # noqa: E402
    DRIVER_TARGET_PROPERTIES,
    driver_target_label,
)


def test_known_data_path_maps_to_label() -> None:
    assert driver_target_label("proscenio.region_x") == "Region X"
    assert driver_target_label("proscenio.frame") == "Frame index"


def test_unknown_data_path_returns_the_raw_path() -> None:
    assert driver_target_label("proscenio.mystery") == "proscenio.mystery"


def test_every_catalog_key_resolves_to_its_label() -> None:
    for key, label, _desc in DRIVER_TARGET_PROPERTIES:
        assert driver_target_label(f"proscenio.{key}") == label
