"""Feature-readiness taxonomy for Proscenio panels (SPEC 005.1.d.5).

Source of truth for the small status badges the sidebar shows next to
every subpanel + every operator row. Pure Python -- no bpy imports --
so the dispatch table can be exercised under plain pytest, and so the
addon UI module can read the human-facing label/icon/tooltip without
re-deriving them per draw tick.

Why this matters: Proscenio surfaces both authoring shortcuts (IK
toggle, Pack Atlas, Drive from Bone) AND export-contract knobs (sprite
type, texture region) in the same sidebar. Without a status badge the
user cannot tell which knob will land in the .proscenio output and
which is editor-only. The badge closes the gap with a 1-glyph + tooltip
hint per row.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FeatureStatus(Enum):
    """Readiness band for a Proscenio feature.

    The four bands cover everything the panel exposes today and leave
    room for SPEC-on-paper features (PLANNED) + opinionated
    non-features (OUT_OF_SCOPE), so the user sees a consistent badge
    even on rows that intentionally do nothing at export time.
    """

    GODOT_READY = "godot-ready"
    BLENDER_ONLY = "blender-only"
    PLANNED = "planned"
    OUT_OF_SCOPE = "out-of-scope"


@dataclass(frozen=True)
class StatusBadge:
    """Static metadata for a status band."""

    icon: str  # Blender bl_icon constant
    short_label: str
    tooltip: str


STATUS_BADGES: dict[FeatureStatus, StatusBadge] = {
    FeatureStatus.GODOT_READY: StatusBadge(
        icon="CHECKMARK",
        short_label="godot-ready",
        tooltip=(
            "Exports to .proscenio + ships in the Godot importer. "
            "Edits to this field affect the runtime scene."
        ),
    ),
    FeatureStatus.BLENDER_ONLY: StatusBadge(
        icon="TOOL_SETTINGS",
        short_label="blender-only",
        tooltip=(
            "Authoring shortcut. Lives entirely on the Blender side -- "
            "does NOT alter the .proscenio export."
        ),
    ),
    FeatureStatus.PLANNED: StatusBadge(
        icon="EXPERIMENTAL",
        short_label="planned",
        tooltip=(
            "Designed in the SPECs but not yet implemented. The UI surface "
            "exists today as a placeholder."
        ),
    ),
    FeatureStatus.OUT_OF_SCOPE: StatusBadge(
        icon="CANCEL",
        short_label="out-of-scope",
        tooltip=(
            "Intentionally not exported (see SPEC 000). Authored in Blender "
            "for the user's own workflow only."
        ),
    ),
}


# Per-feature mapping. Keys are stable identifiers used by the panel +
# the help-topic table. Adding a new feature = adding a row here +
# (optionally) a help topic + (optionally) a panel-side render.
FEATURE_STATUS: dict[str, FeatureStatus] = {
    # Subpanel headers
    "active_sprite": FeatureStatus.GODOT_READY,
    "skeleton": FeatureStatus.GODOT_READY,
    "animation": FeatureStatus.GODOT_READY,
    "atlas": FeatureStatus.GODOT_READY,
    "validation": FeatureStatus.GODOT_READY,
    "export": FeatureStatus.GODOT_READY,
    # Operators / sub-features
    "sprite_type": FeatureStatus.GODOT_READY,
    "sprite_frame_metadata": FeatureStatus.GODOT_READY,
    "texture_region": FeatureStatus.GODOT_READY,
    "snap_region_to_uv": FeatureStatus.BLENDER_ONLY,
    "reproject_uv": FeatureStatus.BLENDER_ONLY,
    "drive_from_bone": FeatureStatus.BLENDER_ONLY,
    "bake_current_pose": FeatureStatus.BLENDER_ONLY,
    "toggle_ik": FeatureStatus.BLENDER_ONLY,
    "create_ortho_camera": FeatureStatus.BLENDER_ONLY,
    "pack_atlas": FeatureStatus.GODOT_READY,
    "apply_packed_atlas": FeatureStatus.GODOT_READY,
    "unpack_atlas": FeatureStatus.BLENDER_ONLY,
    "import_photoshop": FeatureStatus.BLENDER_ONLY,
    # Future / planned -- placeholder rows ready for the SPECs that ship them.
    "slot_system": FeatureStatus.PLANNED,
    "uv_animation": FeatureStatus.PLANNED,
    "live_link": FeatureStatus.PLANNED,
    # Out-of-scope sentinels (not currently rendered, but available for
    # hovering "why is X not here" cases).
    "ik_constraint_export": FeatureStatus.OUT_OF_SCOPE,
    "shape_key_animation": FeatureStatus.OUT_OF_SCOPE,
}


def status_for(feature_id: str) -> FeatureStatus:
    """Return the status band for a known feature id.

    Unknown feature ids fall back to ``BLENDER_ONLY`` so a row always
    renders some badge instead of crashing the panel during draw -- a
    missing entry is a documentation bug, not a fatal one.
    """
    return FEATURE_STATUS.get(feature_id, FeatureStatus.BLENDER_ONLY)


def badge_for(feature_id: str) -> StatusBadge:
    """Return the renderable badge metadata for a feature id."""
    return STATUS_BADGES[status_for(feature_id)]
