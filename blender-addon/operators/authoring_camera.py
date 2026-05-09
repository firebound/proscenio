"""Orthographic preview camera authoring shortcut (SPEC 005.1.b)."""

from __future__ import annotations

from typing import ClassVar

import bpy

from ..core.props_access import scene_props  # type: ignore[import-not-found]
from ..core.report import report_info  # type: ignore[import-not-found]
from ..core.select import select_only  # type: ignore[import-not-found]

_PREVIEW_CAM_NAME = "Proscenio.PreviewCam"


class PROSCENIO_OT_create_ortho_camera(bpy.types.Operator):
    """Create or focus an orthographic preview camera matching pixels_per_unit."""

    bl_idname = "proscenio.create_ortho_camera"
    bl_label = "Proscenio: Preview Camera"
    bl_description = (
        "Adds (or focuses) an orthographic camera sized to the scene's "
        "pixels_per_unit and render resolution. Use Numpad 0 to enter the view."
    )
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        scene = context.scene
        props = scene_props(context)
        ppu = float(props.pixels_per_unit) if props is not None else 100.0
        ortho_scale = max(scene.render.resolution_x, scene.render.resolution_y) / ppu

        cam_obj = bpy.data.objects.get(_PREVIEW_CAM_NAME)
        if cam_obj is None:
            cam_data = bpy.data.cameras.new(name=_PREVIEW_CAM_NAME)
            cam_obj = bpy.data.objects.new(name=_PREVIEW_CAM_NAME, object_data=cam_data)
            scene.collection.objects.link(cam_obj)
            cam_obj.location = (0.0, -10.0, 0.0)
            cam_obj.rotation_euler = (1.5707963, 0.0, 0.0)
            created = True
        else:
            created = False

        cam = cam_obj.data
        cam.type = "ORTHO"
        cam.ortho_scale = ortho_scale

        scene.camera = cam_obj
        select_only(context, cam_obj)

        verb = "created" if created else "updated"
        report_info(self, f"{verb} '{_PREVIEW_CAM_NAME}' (ortho_scale={ortho_scale:.4f})")
        return {"FINISHED"}


_classes: tuple[type, ...] = (PROSCENIO_OT_create_ortho_camera,)


def register() -> None:
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
