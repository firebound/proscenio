"""Unit tests for the driver target-property catalog.

Pure pytest, no Blender. A driver targets each field's ``["proscenio_<key>"]``
Custom Property (idprop) data path (spec 037); ``driver_target_label`` maps
that path back to the UI label the Drive-from-Bone list shows, and the catalog
is the single source the create operator + the list share.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.armature.driver_targets import (  # noqa: E402
    DRIVER_TARGET_PROPERTIES,
    driver_data_path,
    driver_target_label,
    is_proscenio_driver_path,
)


def test_driver_data_path_is_the_idprop_path() -> None:
    assert driver_data_path("frame") == '["proscenio_frame"]'
    assert driver_data_path("region_x") == '["proscenio_region_x"]'


def test_is_proscenio_driver_path_matches_only_proscenio_idprops() -> None:
    assert is_proscenio_driver_path('["proscenio_frame"]') is True
    assert is_proscenio_driver_path("location") is False
    assert is_proscenio_driver_path("proscenio.frame") is False


def test_known_data_path_maps_to_label() -> None:
    assert driver_target_label('["proscenio_region_x"]') == "Region X"
    assert driver_target_label('["proscenio_frame"]') == "Frame index"


def test_unknown_data_path_returns_the_raw_path() -> None:
    assert driver_target_label('["proscenio_mystery"]') == '["proscenio_mystery"]'


def test_every_catalog_key_resolves_to_its_label() -> None:
    for key, label, _desc in DRIVER_TARGET_PROPERTIES:
        assert driver_target_label(driver_data_path(key)) == label
