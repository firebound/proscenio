"""Revert a mesh element to its original imported plane (spec 071).

The escape hatch for "start this element's mesh over": it rebuilds the original
textured quad from the ``PROSCENIO_IMPORT_PLACEMENT`` tag the import stamped
(and never mutates), drops the automesh geometry, and wipes the skinning data +
authoring strokes - leaving a clean plane ready to re-author. Distinct from
per-element PSD re-import (which rebuilds a *deformed* mesh and reprojects
weights); revert deliberately goes back to the bare quad.

Restricted to PSD-imported mesh elements (those carrying the placement tag); an
incorporated / hand-built element has no original imported plane, so revert
warns and no-ops there (a bounding-box rebuild is logged as a follow-on).
"""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core._shared.cp_keys import (  # type: ignore[import-not-found]
    PROSCENIO_BONE_MODES,
    PROSCENIO_ENVELOPE_RADIUS,
    PROSCENIO_IMPORT_PLACEMENT,
    PROSCENIO_MANUAL_CONTOUR,
    PROSCENIO_MIRROR_X,
    PROSCENIO_USER_OUTER_STROKES,
    PROSCENIO_USER_STEINERS,
    PROSCENIO_USER_STROKES,
    PROSCENIO_WEIGHT_SIDECAR,
)
from ..core._shared.props_access import element_type_of  # type: ignore[import-not-found]
from ..core._shared.report import report_info, report_warn  # type: ignore[import-not-found]
from ..importers.photoshop.planes import _build_quad  # type: ignore[import-not-found]

# Custom Properties a revert clears: the skinning bind metadata, the automesh
# authoring strokes, and the Manual Mesh source contour (spec 070 C2). The import
# identity (placement / origin / manifest) + element_type + material are KEPT.
_WIPE_CP_KEYS = (
    PROSCENIO_WEIGHT_SIDECAR,
    PROSCENIO_BONE_MODES,
    PROSCENIO_ENVELOPE_RADIUS,
    PROSCENIO_MIRROR_X,
    PROSCENIO_USER_STEINERS,
    PROSCENIO_USER_STROKES,
    PROSCENIO_USER_OUTER_STROKES,
    PROSCENIO_MANUAL_CONTOUR,
)


def _parse_placement(raw: object) -> tuple[float, float, float, float] | None:
    """Coerce the stored ``[width, height, offset_x, offset_z]`` to floats; None
    when absent or malformed (an element with no original plane to rebuild)."""
    if raw is None:
        return None
    try:
        return (float(raw[0]), float(raw[1]), float(raw[2]), float(raw[3]))  # type: ignore[index]
    except (TypeError, IndexError, ValueError, KeyError):
        return None


class PROSCENIO_OT_revert_to_plane(bpy.types.Operator):
    """Revert this mesh element to its original imported textured plane."""

    bl_idname = "proscenio.revert_to_plane"
    bl_label = "Proscenio: Revert to Plane"
    bl_description = (
        "Rebuild the original imported quad with its texture and drop the "
        "generated mesh - the automesh / hand-drawn geometry, the weights, and "
        "the authoring strokes are cleared. The escape hatch to start this "
        "element's mesh over (PSD-imported mesh elements only)"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        obj = context.active_object
        return (
            obj is not None
            and obj.type == "MESH"
            and obj.data is not None
            and element_type_of(obj) == "mesh"
        )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        """Warn-no-op a no-placement element, else raise a destructive-action
        confirm before the wipe (the mesh + weights are not recoverable here)."""
        obj = context.active_object
        if obj is None or _parse_placement(obj.get(PROSCENIO_IMPORT_PLACEMENT)) is None:
            report_warn(
                self,
                "no original plane recorded for this element (not a PSD import) - "
                "nothing to revert to",
            )
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        layout.label(text="Revert this element to its original plane?", icon="ERROR")
        col = layout.column(align=True)
        col.label(text="This DESTROYS the generated mesh and its weight paint:")
        col.label(text="- the automesh / hand-drawn geometry")
        col.label(text="- all vertex groups + bound weights")
        col.label(text="- the authoring strokes")
        layout.label(text="The image + placement are kept. This cannot be undone.", icon="INFO")

    def execute(self, context: bpy.types.Context) -> set[str]:
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            report_warn(self, "active object must be a mesh element")
            return {"CANCELLED"}
        placement = _parse_placement(obj.get(PROSCENIO_IMPORT_PLACEMENT))
        if placement is None:
            report_warn(
                self,
                "no original plane recorded for this element (not a PSD import) - "
                "nothing to revert to",
            )
            return {"CANCELLED"}

        width, height, offset_x, offset_z = placement
        n_groups = len(obj.vertex_groups)
        n_cps = sum(1 for key in _WIPE_CP_KEYS if key in obj)

        _build_quad(obj, (width, height), (offset_x, offset_z))
        _wipe_skinning_and_authoring(obj)

        report_info(
            self,
            f"Reverted to plane: cleared {n_groups} vertex groups, {n_cps} authoring "
            "keys; image + placement kept",
        )
        return {"FINISHED"}


def _wipe_skinning_and_authoring(obj: bpy.types.Object) -> None:
    """Drop every vertex group (deform + ``proscenio_base_sprite``) and the
    skinning / authoring Custom Properties, keeping the import identity +
    material (spec 071 decision 2A)."""
    obj.vertex_groups.clear()
    for key in _WIPE_CP_KEYS:
        if key in obj:
            del obj[key]


_classes: tuple[type, ...] = (PROSCENIO_OT_revert_to_plane,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
