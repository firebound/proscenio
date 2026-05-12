"""Custom Property key registry (SPEC 009 wave 9.1).

Single source of truth for every Blender Custom Property key the
Proscenio addon reads or writes. The literal strings used to be
scattered across ``writer.py``, slot operators, atlas-pack operators,
panel helpers, and fixture scripts; centralising them here removes the
drift risk and makes "rename a CP key" a one-liner.

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
