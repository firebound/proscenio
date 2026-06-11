"""Feature-readiness taxonomy for Proscenio panels.

Source of truth for the small status badges the sidebar shows next to
every subpanel + every operator row. Pure Python - no bpy imports --
so the dispatch table can be exercised under plain pytest, and so the
addon UI module can read the human-facing label/icon/tooltip without
re-deriving them per draw tick.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FeatureStatus(Enum):
    """Readiness band for a Proscenio feature."""

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
            "Authoring shortcut. Lives entirely on the Blender side - "
            "does NOT alter the .proscenio export."
        ),
    ),
    FeatureStatus.PLANNED: StatusBadge(
        icon="EXPERIMENTAL",
        short_label="planned",
        tooltip=("Designed but not yet implemented. The UI surface exists today as a placeholder."),
    ),
    FeatureStatus.OUT_OF_SCOPE: StatusBadge(
        icon="CANCEL",
        short_label="out-of-scope",
        tooltip=(
            "Intentionally not exported. Authored in Blender for the user's own workflow only."
        ),
    ),
}


# Per-feature mapping. Keys are stable identifiers used by the panel +
# the help-topic table. Adding a new feature = adding a row here +
# (optionally) a help topic + (optionally) a panel-side render.
FEATURE_STATUS: dict[str, FeatureStatus] = {
    "active_element": FeatureStatus.GODOT_READY,
    "skeleton": FeatureStatus.GODOT_READY,
    "animation": FeatureStatus.GODOT_READY,
    "atlas": FeatureStatus.GODOT_READY,
    "validation": FeatureStatus.GODOT_READY,
    "export": FeatureStatus.GODOT_READY,
    "element_type": FeatureStatus.GODOT_READY,
    "sprite_frame_metadata": FeatureStatus.GODOT_READY,
    "texture_region": FeatureStatus.GODOT_READY,
    "snap_region_to_uv": FeatureStatus.BLENDER_ONLY,
    "reproject_uv": FeatureStatus.BLENDER_ONLY,
    "drive_from_bone": FeatureStatus.GODOT_READY,
    "bake_current_pose": FeatureStatus.BLENDER_ONLY,
    "toggle_ik": FeatureStatus.BLENDER_ONLY,
    "quick_armature": FeatureStatus.BLENDER_ONLY,
    "create_ortho_camera": FeatureStatus.BLENDER_ONLY,
    "outliner": FeatureStatus.BLENDER_ONLY,
    "pack_atlas": FeatureStatus.GODOT_READY,
    "apply_packed_atlas": FeatureStatus.GODOT_READY,
    "unpack_atlas": FeatureStatus.BLENDER_ONLY,
    "import_photoshop": FeatureStatus.BLENDER_ONLY,
    # GODOT_READY because the writer emits slots[] even before the Godot
    # importer consumes them - a documented no-op on the Godot side until then.
    "slot_system": FeatureStatus.GODOT_READY,
    "sprite_frame_preview": FeatureStatus.BLENDER_ONLY,
    # Pose assets live in the Asset Browser and never reach the .proscenio.
    "pose_library": FeatureStatus.BLENDER_ONLY,
    "uv_animation": FeatureStatus.PLANNED,
    "live_link": FeatureStatus.PLANNED,
    "ik_constraint_export": FeatureStatus.OUT_OF_SCOPE,
    "shape_key_animation": FeatureStatus.OUT_OF_SCOPE,
    "element": FeatureStatus.GODOT_READY,
    "active_mesh": FeatureStatus.GODOT_READY,
    "active_sprite": FeatureStatus.GODOT_READY,
    "armature": FeatureStatus.GODOT_READY,
    "pose_mode": FeatureStatus.BLENDER_ONLY,
    "mesh_generation": FeatureStatus.BLENDER_ONLY,
    "automesh_alpha": FeatureStatus.BLENDER_ONLY,
    "automesh_interactive": FeatureStatus.BLENDER_ONLY,
    "debug_pipeline": FeatureStatus.BLENDER_ONLY,
    "weight_paint": FeatureStatus.GODOT_READY,
    "bind": FeatureStatus.GODOT_READY,
    "edit_weights": FeatureStatus.BLENDER_ONLY,
    "snapshot": FeatureStatus.BLENDER_ONLY,
    "sidecar_io": FeatureStatus.BLENDER_ONLY,
    "weight_transfer": FeatureStatus.GODOT_READY,
    "pipeline": FeatureStatus.GODOT_READY,
    "import": FeatureStatus.BLENDER_ONLY,
    "active_slot": FeatureStatus.GODOT_READY,
    "helpers": FeatureStatus.BLENDER_ONLY,
    "help": FeatureStatus.BLENDER_ONLY,
    "diagnostics": FeatureStatus.BLENDER_ONLY,
}


def status_for(feature_id: str) -> FeatureStatus:
    """Return the status band for a known feature id.

    Unknown feature ids fall back to ``BLENDER_ONLY`` so a row always
    renders some badge instead of crashing the panel during draw - a
    missing entry is a documentation bug, not a fatal one.
    """
    return FEATURE_STATUS.get(feature_id, FeatureStatus.BLENDER_ONLY)


def badge_for(feature_id: str) -> StatusBadge:
    """Return the renderable badge metadata for a feature id."""
    return STATUS_BADGES[status_for(feature_id)]
