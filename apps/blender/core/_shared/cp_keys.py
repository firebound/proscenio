"""Custom Property key registry.

Single source of truth for every Blender Custom Property key the
Proscenio addon reads or writes.

Why a module of bare constants instead of an Enum: Custom Property
access in Blender is dict-style (``obj["proscenio_is_slot"]``); a
string constant matches that idiom. An Enum would require ``.value``
on every read.

Pure Python - no bpy import. Lets the writer's headless path consume
the same keys without registering the addon.
"""

from __future__ import annotations

# Per-Object slot anchor flag. Mirrors ProscenioObjectProps.is_slot.
PROSCENIO_IS_SLOT = "proscenio_is_slot"

# Per-Object default attachment name (slot Empty CP). Mirrors
# ProscenioObjectProps.slot_default.
PROSCENIO_SLOT_DEFAULT = "proscenio_slot_default"

# Per-Object bone the slot follows (slot Empty CP). Mirrors
# ProscenioObjectProps.slot_bone; the Godot importer parents the slot Node2D
# under that Bone2D so attachments track the bone.
PROSCENIO_SLOT_BONE = "proscenio_slot_bone"

# Per-Object outliner-favorite pin (the outliner subpanel). Mirrors
# ProscenioObjectProps.is_outliner_favorite.
PROSCENIO_OUTLINER_FAVORITE = "proscenio_outliner_favorite"

# Per-Object slot index keyed by the action's slot_attachment animation.
# Read by writer._build_slot_attachment_track via fcurve data_path
# '["proscenio_slot_index"]'.
PROSCENIO_SLOT_INDEX = "proscenio_slot_index"

# Pre-pack snapshot of UV layers / material refs, written by
# PROSCENIO_OT_pack_atlas, restored by PROSCENIO_OT_unpack_atlas.
PROSCENIO_PRE_PACK = "proscenio_pre_pack"

# Origin marker stamped on a sprite's pre-Apply material by
# PROSCENIO_OT_apply_packed_atlas, carrying the material's apply-time name.
# PROSCENIO_OT_unpack_atlas rescue-scans for it when the snapshot's by-name
# lookup misses after a rename (the value survives a rename; the name does
# not). A deleted material, or its old name reused by a different material,
# is the residual identity-by-name edge the atlas help topic documents.
PROSCENIO_ATLAS_ORIGIN_MARKER = "proscenio_atlas_origin"

# Legacy Custom Property mirrors of the per-Object PropertyGroup.
# Writer reads these as fallbacks when the PropertyGroup is not
# registered (headless contexts).
PROSCENIO_TYPE = "proscenio_type"
PROSCENIO_HFRAMES = "proscenio_hframes"
PROSCENIO_VFRAMES = "proscenio_vframes"
PROSCENIO_FRAME = "proscenio_frame"
PROSCENIO_CENTERED = "proscenio_centered"
PROSCENIO_REGION_MODE = "proscenio_region_mode"
PROSCENIO_REGION_X = "proscenio_region_x"
PROSCENIO_REGION_Y = "proscenio_region_y"
PROSCENIO_REGION_W = "proscenio_region_w"
PROSCENIO_REGION_H = "proscenio_region_h"
PROSCENIO_MATERIAL_ISOLATED = "proscenio_material_isolated"
# Whole-number draw order (the Y Location layer). The writer negates it into the
# Godot z_index; the addon also positions the object at Y = order * spacing.
# Authoring-only, never a schema field. Mirrors ProscenioObjectProps.y_draw_order.
PROSCENIO_Y_DRAW_ORDER = "proscenio_y_draw_order"

# Default Blender-units gap between consecutive Y Location (Draw Order) layers.
# Matches Blender's default 3D-view ``clip_start`` (0.01) so the layer gap clears
# the depth-buffer precision of the perspective authoring viewport at the usual
# camera distance - 0.001 is marginal there, 0.01 is comfortable, and the gap is
# invisible in the front-ortho deliverable view (ortho drops depth). The addon
# preference ``y_location_spacing`` overrides it; the bpy-free validation core
# falls back to this when no preference value is threaded in. Kept here (the one
# pure-Python shared module both sides import) so the preference default and the
# validation default never drift.
DEFAULT_Y_LOCATION_SPACING = 0.01

# Skinning sidecar + bind metadata. The weight sidecar is the per-Object JSON
# store of bind/paint provenance; bone modes, envelope radius, and the mirror
# flag are bind-time inputs read by the skinning operators and bpy helpers.
PROSCENIO_WEIGHT_SIDECAR = "proscenio_weight_sidecar"
PROSCENIO_BONE_MODES = "proscenio_bone_modes"
PROSCENIO_ENVELOPE_RADIUS = "proscenio_envelope_radius"
PROSCENIO_MIRROR_X = "proscenio_mirror_x"

# Automesh authoring strokes. Per-Object JSON Custom Properties holding the
# user's interactive Steiner points and cut / extend strokes; read back to
# rebuild the authored mesh on APPLY.
PROSCENIO_USER_STEINERS = "proscenio_user_steiners"
PROSCENIO_USER_STROKES = "proscenio_user_strokes"
PROSCENIO_USER_OUTER_STROKES = "proscenio_user_outer_strokes"

# Photoshop import tags. Stamped onto imported meshes by the photoshop
# importer: the source-layer origin marker (``psd:<layer>``), the manifest
# kind hint, and the manifest-declared blend mode kept for downstream writers.
PROSCENIO_IMPORT_ORIGIN = "proscenio_import_origin"
PROSCENIO_PSD_KIND = "proscenio_psd_kind"
PROSCENIO_BLEND_MODE = "proscenio_blend_mode"
# The quad placement (width, height, offset_x, offset_z) baked at import.
# A re-import with the same placement is an art retouch - the mesh, any
# automesh densification, and painted weights are left untouched.
PROSCENIO_IMPORT_PLACEMENT = "proscenio_import_placement"
# Absolute source manifest path stamped on every imported object, so a
# per-Element reimport (the Element panel button) resolves its origin file
# without a picker. Per-object - two manifests imported into one scene each
# carry their own source - mirroring the per-object origin layer marker.
PROSCENIO_IMPORT_MANIFEST = "proscenio_import_manifest"
