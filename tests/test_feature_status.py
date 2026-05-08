"""Unit tests for the SPEC 005.1.d.5 feature-status taxonomy.

Pure pytest, no Blender. Confirms the dispatch table is well-formed +
covers every panel surface the UI module references.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "blender-addon"))

from core.feature_status import (  # noqa: E402
    FEATURE_STATUS,
    STATUS_BADGES,
    FeatureStatus,
    badge_for,
    status_for,
)


def test_every_status_has_a_badge() -> None:
    for status in FeatureStatus:
        assert status in STATUS_BADGES, f"missing badge for {status}"


def test_badge_fields_are_non_empty() -> None:
    for status, badge in STATUS_BADGES.items():
        assert badge.icon, f"empty icon for {status}"
        assert badge.short_label, f"empty short_label for {status}"
        assert badge.tooltip, f"empty tooltip for {status}"


def test_known_features_resolve_to_expected_status() -> None:
    assert status_for("active_sprite") == FeatureStatus.GODOT_READY
    assert status_for("drive_from_bone") == FeatureStatus.BLENDER_ONLY
    assert status_for("toggle_ik") == FeatureStatus.BLENDER_ONLY
    assert status_for("slot_system") == FeatureStatus.GODOT_READY
    assert status_for("uv_animation") == FeatureStatus.PLANNED
    assert status_for("ik_constraint_export") == FeatureStatus.OUT_OF_SCOPE


def test_unknown_feature_falls_back_to_blender_only() -> None:
    assert status_for("nonexistent_feature_id") == FeatureStatus.BLENDER_ONLY


def test_badge_for_returns_renderable_metadata() -> None:
    badge = badge_for("active_sprite")
    assert badge.icon == "CHECKMARK"
    assert badge.short_label == "godot-ready"


def test_panel_subpanel_ids_all_have_status() -> None:
    """Every subpanel-header feature id the panel module touches must exist."""
    panel_subpanel_ids = [
        "active_sprite",
        "skeleton",
        "animation",
        "atlas",
        "validation",
        "export",
    ]
    for fid in panel_subpanel_ids:
        assert fid in FEATURE_STATUS, f"missing FEATURE_STATUS row for subpanel {fid!r}"


def test_no_duplicate_feature_ids() -> None:
    assert len(FEATURE_STATUS) == len(set(FEATURE_STATUS.keys()))
