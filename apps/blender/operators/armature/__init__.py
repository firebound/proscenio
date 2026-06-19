"""Armature authoring operators.

Subpackage with:

- authoring_camera  - Preview Camera (ortho)
- authoring_ik      - Toggle IK chain
- skeleton_target   - Set Proscenio active armature pointer
- rotation_mode     - Convert bone rotation to XYZ Euler
- quick_armature    - Quick Armature modal (the Quick Armature shortcut)
"""

from __future__ import annotations

from . import authoring_camera, authoring_ik, quick_armature, rotation_mode, skeleton_target


def register() -> None:
    authoring_camera.register()
    authoring_ik.register()
    skeleton_target.register()
    rotation_mode.register()
    quick_armature.register()


def unregister() -> None:
    quick_armature.unregister()
    rotation_mode.unregister()
    skeleton_target.unregister()
    authoring_ik.unregister()
    authoring_camera.unregister()
