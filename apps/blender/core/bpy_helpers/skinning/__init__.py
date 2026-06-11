"""bpy-bound skinning helpers (the weight-paint productivity follow-up)."""

from .automesh_hook import (
    maybe_post_regen_reproject,
    maybe_pre_regen_snapshot,
    reproject_stored_sidecar,
    snapshot_live_vgroups,
)
from .bind_apply import apply_bind
from .bone_collection_visibility import BoneCollectionSnapshot
from .bone_collection_visibility import restore as restore_bone_visibility
from .bone_collection_visibility import snapshot as snapshot_bone_visibility
from .diagnose_collect import collect_diagnoses_for_object
from .modal_session import EditWeightsSession
from .modal_session import capture as capture_session
from .modal_session import restore as restore_session
from .paint_preset_bind import (
    apply_paint_preset,
    read_mirror_flag,
    restore_paint_preset,
    snapshot_paint_preset,
)
from .sidecar_io import apply_sidecar, per_vert_uv_anchors, snapshot_sidecar
from .stroke_diff import StrokeDiffTracker
from .weight_overlay import register_handler, unregister_handler

__all__ = [
    "BoneCollectionSnapshot",
    "EditWeightsSession",
    "StrokeDiffTracker",
    "apply_bind",
    "apply_paint_preset",
    "apply_sidecar",
    "capture_session",
    "collect_diagnoses_for_object",
    "maybe_post_regen_reproject",
    "maybe_pre_regen_snapshot",
    "per_vert_uv_anchors",
    "read_mirror_flag",
    "register_handler",
    "reproject_stored_sidecar",
    "restore_bone_visibility",
    "restore_paint_preset",
    "restore_session",
    "snapshot_bone_visibility",
    "snapshot_live_vgroups",
    "snapshot_paint_preset",
    "snapshot_sidecar",
    "unregister_handler",
]
