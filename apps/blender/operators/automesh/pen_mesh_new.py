"""From-blank pen mesh creation (spec 070).

Creates a Proscenio mesh element from a chosen image - the same textured quad an
import would build - then launches the interactive authoring modal in from-blank
mode so the artist draws the outline point by point over the image. This is the
Spine / Moho model the STUDY locked: a mesh always overlays a texture region, so
"from blank" means "from an image with no mesh yet", not "from nothing".

Note: like every other ``bpy.types.Operator`` in the addon this file does NOT use
``from __future__ import annotations`` - Blender's RNA metaclass evaluates the
operator's property annotations eagerly, and PEP 563 would leave them as strings.
"""

from pathlib import Path
from typing import ClassVar

import bpy
from bpy.props import StringProperty

from ...core._shared.props_access import resolve_pixels_per_unit  # type: ignore[import-not-found]
from ...core._shared.report import report_error, report_info  # type: ignore[import-not-found]

# The element-build reuses the photoshop importer's quad + material + tag helpers
# so a from-blank pen element is byte-identical to an imported mesh element (quad,
# UV-mapped image material, placement tag, element_type) and re-imports / exports
# the same way. The only difference is it carries no manifest origin.
from ...importers.photoshop.planes import (  # type: ignore[import-not-found]
    _attach_material,
    _ensure_mesh,
    _tag_element_type,
)
from .automesh_authoring import PROSCENIO_OT_automesh_authoring


def create_pen_mesh_element(
    context: bpy.types.Context, image_path: Path, name: str
) -> bpy.types.Object:
    """Build + activate a Proscenio mesh element from ``image_path``.

    Raises ``RuntimeError`` (image load failed) or ``ValueError`` (no pixels) so
    the operator surfaces the reason. The element is the imported-mesh shape: a
    UV-mapped quad sized from the image and the scene pixels-per-unit, the unlit
    image material, the placement tag (so APPLY's UVs land in real texture space),
    and ``element_type="mesh"``.
    """
    image = bpy.data.images.load(str(image_path), check_existing=True)
    width_px, height_px = int(image.size[0]), int(image.size[1])
    if width_px <= 0 or height_px <= 0:
        raise ValueError("image has no pixel dimensions")
    ppu = resolve_pixels_per_unit(context)
    size = (width_px / ppu, height_px / ppu)
    obj = _ensure_mesh(name, size)
    _attach_material(obj, image_path)
    _tag_element_type(obj, "mesh")
    for other in context.selected_objects:
        other.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj


def _launch_authoring_from_blank(context: bpy.types.Context) -> bool:
    """Invoke the authoring modal in from-blank mode in a VIEW_3D, if one exists.

    The operator may execute from the file-browser context (after the image
    picker), so resolve a real VIEW_3D area + WINDOW region and override into it.
    Returns False when no 3D viewport is open (the caller then tells the user to
    open Author Mesh manually).
    """
    screen = context.screen
    if screen is None:
        return False
    for area in screen.areas:
        if area.type != "VIEW_3D":
            continue
        region = next((r for r in area.regions if r.type == "WINDOW"), None)
        if region is None:
            continue
        PROSCENIO_OT_automesh_authoring._launch_from_blank = True
        with context.temp_override(window=context.window, area=area, region=region):
            bpy.ops.proscenio.automesh_authoring("INVOKE_DEFAULT")
        return True
    return False


class PROSCENIO_OT_pen_mesh_new(bpy.types.Operator):
    """Create a mesh element from an image and open the pen to draw its outline."""

    bl_idname = "proscenio.pen_mesh_new"
    bl_label = "Proscenio: New Pen Mesh"
    bl_description = (
        "Pick an image and draw a new mesh element over it point by point with the "
        "pen, like Spine / Illustrator. Creates the element, then opens the "
        "interactive authoring pen on a blank outline"
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    filepath: StringProperty(subtype="FILE_PATH")  # type: ignore[valid-type]
    name: StringProperty(  # type: ignore[valid-type]
        name="Name",
        description="Name for the new mesh element",
        default="PenMesh",
    )

    def invoke(self, context: bpy.types.Context, _event: bpy.types.Event) -> set[str]:
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        if not self.filepath or not Path(self.filepath).is_file():
            report_error(self, "pick an image file to draw the mesh over")
            return {"CANCELLED"}
        try:
            obj = create_pen_mesh_element(context, Path(self.filepath), self.name)
        except (RuntimeError, ValueError) as exc:
            report_error(self, f"could not create pen mesh: {exc}")
            return {"CANCELLED"}
        if _launch_authoring_from_blank(context):
            report_info(self, f"created '{obj.name}' - draw its outline with the pen")
        else:
            report_info(
                self,
                f"created '{obj.name}' - open Mesh Generation > Author Mesh to draw it",
            )
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_pen_mesh_new,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
