"""Shared poll + invoke preconditions for the two automesh authoring modals.

Both the interactive Automesh authoring modal and the Manual Draw modal gate on
the same thing: an active MESH object carrying an image texture, with no other
authoring modal already live (the two are mutually exclusive). This is the one
home for that poll + the invoke-time validation so the operators stay in
lockstep instead of drifting two hand-maintained copies of the same checks.
"""

from __future__ import annotations

import bpy

from ...core._shared.material_images import first_material_image  # type: ignore[import-not-found]
from ...core._shared.props_access import element_type_of  # type: ignore[import-not-found]
from ...core._shared.report import report_error, report_warn  # type: ignore[import-not-found]
from ._authoring_modal_guard import other_running


def poll_mesh_with_image(context: bpy.types.Context, modal_name: str) -> bool:
    """True when the active object is a MESH with an image and no rival modal runs.

    ``modal_name`` is the caller's own guard name so ``other_running`` reports the
    OTHER authoring modal (the two are mutually exclusive).
    """
    obj = context.active_object
    if obj is None or obj.type != "MESH" or obj.data is None:
        return False
    if other_running(modal_name):
        return False
    return first_material_image(obj) is not None


def validate_authoring_invoke(
    operator: bpy.types.Operator,
    context: bpy.types.Context,
    modal_name: str,
) -> bpy.types.Object | None:
    """Validate invoke preconditions; return the mesh, or None after reporting.

    Mesh present, not a sprite element, carries an image, no rival modal live.
    On any failure it reports the matching error / warning on ``operator`` and
    returns None so the caller returns CANCELLED.
    """
    obj = context.active_object
    if obj is None or obj.type != "MESH":
        report_error(operator, "active object must be a mesh")
        return None
    if element_type_of(obj) == "sprite":
        report_warn(
            operator,
            "active object is a sprite element - mesh authoring is mesh-only; it "
            "would replace its quad. To attach a sprite to a bone, parent it with "
            "Ctrl+P > Bone instead",
        )
        return None
    if first_material_image(obj) is None:
        report_error(
            operator,
            "active mesh has no image texture - add a material with a TEX_IMAGE node first",
        )
        return None
    if other_running(modal_name):
        report_warn(operator, "an authoring modal is already running - finish it first")
        return None
    return obj
