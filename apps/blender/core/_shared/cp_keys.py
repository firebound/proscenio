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
