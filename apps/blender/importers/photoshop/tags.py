"""Custom-property taggers for stamped Photoshop-import objects."""

from __future__ import annotations

import bpy

from ...core._shared.cp_keys import (
    PROSCENIO_BLEND_MODE,
    PROSCENIO_IMPORT_ORIGIN,
    PROSCENIO_PSD_KIND,
    PROSCENIO_Y_DRAW_ORDER,
)


def _tag_origin(obj: bpy.types.Object, layer_name: str) -> None:
    obj[PROSCENIO_IMPORT_ORIGIN] = f"psd:{layer_name}"


def _tag_draw_order(obj: bpy.types.Object, z_order: int) -> None:
    """Seed ``y_draw_order`` from the PSD layer order.

    Writes the Custom Property (the headless writer reads it) and, when the
    PropertyGroup is registered, the idprop directly - bypassing the field's
    update callback, which keys off ``context.active_object`` and would target
    the wrong object mid-import. The object's Y was already positioned by the
    placement, so no reposition is needed here.
    """
    order = int(z_order)
    obj[PROSCENIO_Y_DRAW_ORDER] = order
    props = getattr(obj, "proscenio", None)
    if props is not None:
        props["y_draw_order"] = order


def _tag_kind(obj: bpy.types.Object, kind: str) -> None:
    """Stamp the manifest ``kind`` so downstream writers can branch on it."""
    obj[PROSCENIO_PSD_KIND] = kind


def _tag_blend_mode(obj: bpy.types.Object, blend_mode: str | None) -> None:
    """Preserve the manifest-declared blend mode for downstream writers."""
    if blend_mode is None:
        return
    obj[PROSCENIO_BLEND_MODE] = blend_mode


def _tag_element_type(
    obj: bpy.types.Object,
    element_type: str,
    hframes: int = 1,
    vframes: int = 1,
) -> None:
    """Tag the mesh's element type via PropertyGroup if present, custom-prop fallback."""
    if hasattr(obj, "proscenio"):
        obj.proscenio.element_type = element_type
        obj.proscenio.hframes = hframes
        obj.proscenio.vframes = vframes
        if element_type == "sprite":
            obj.proscenio.frame = 0
            obj.proscenio.centered = True
    obj["proscenio_type"] = element_type
    obj["proscenio_hframes"] = hframes
    obj["proscenio_vframes"] = vframes
    if element_type == "sprite":
        obj["proscenio_frame"] = 0
        obj["proscenio_centered"] = True
