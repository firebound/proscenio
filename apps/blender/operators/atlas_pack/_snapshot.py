"""Pre-pack UV-layer snapshot helpers for atlas packing."""

from __future__ import annotations

from typing import Any

import bpy

from ...core._shared.cp_keys import PROSCENIO_PRE_PACK  # type: ignore[import-not-found]
from ...core._shared.json_cp import read_json_dict_cp  # type: ignore[import-not-found]


def duplicate_active_uv_layer(obj: bpy.types.Object) -> str:
    """Duplicate the active UV layer to ``<name>.pre_pack`` for later restore.

    No-op when the snapshot already exists. Returns the snapshot layer
    name or an empty string when there was no active UV layer.
    """
    mesh = obj.data
    uv_layers = getattr(mesh, "uv_layers", None)
    if uv_layers is None:
        return ""
    active = uv_layers.active
    if active is None or len(active.data) == 0:
        return ""
    snap_name = f"{active.name}.pre_pack"
    if snap_name in uv_layers:
        return snap_name
    snap = uv_layers.new(name=snap_name, do_init=False)
    if snap is None:
        return ""
    for i, loop in enumerate(active.data):
        snap.data[i].uv = loop.uv
    uv_layers.active = active
    return str(snap.name)


def pre_pack_snapshot_for(obj: bpy.types.Object) -> dict[str, Any] | None:
    """Read the pre-pack snapshot stored as a Custom Property, or ``None``."""
    return read_json_dict_cp(obj, PROSCENIO_PRE_PACK) or None
