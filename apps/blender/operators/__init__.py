"""Proscenio operators package (SPEC 009 wave 9.2).

Each topical concern lives in its own submodule with its own
``register`` / ``unregister``. This file orchestrates the package:
imports every submodule, calls them in order on ``register()``, in
reverse order on ``unregister()``.

Submodules:

- help_dispatch     - status badge proxy, help popup, smoke test
- export_flow       - Validate, Export, Re-export
- selection         - select issue, select outliner, toggle favorite
- authoring_camera  - Preview Camera (ortho)
- authoring_ik      - Toggle IK chain
- uv_authoring      - Reproject UV, Snap region to UV
- driver            - Drive sprite from bone (5.1.d.1)
- pose_library      - Save Pose to Library, Bake Current Pose
- quick_armature    - Quick Armature modal (5.1.d.3)
- slot              - Create Slot, Add Attachment, Set Default, preview shader
- atlas_pack        - Pack, Apply, Unpack
- import_photoshop  - single-operator file (Import Photoshop Manifest)
"""

from __future__ import annotations

from . import (
    atlas_pack,
    authoring_camera,
    authoring_ik,
    driver,
    export_flow,
    help_dispatch,
    import_photoshop,
    pose_library,
    quick_armature,
    selection,
    slot,
    uv_authoring,
)


def register() -> None:
    help_dispatch.register()
    export_flow.register()
    selection.register()
    authoring_camera.register()
    authoring_ik.register()
    uv_authoring.register()
    driver.register()
    pose_library.register()
    quick_armature.register()
    slot.register()
    atlas_pack.register()
    import_photoshop.register()


def unregister() -> None:
    import_photoshop.unregister()
    atlas_pack.unregister()
    slot.unregister()
    quick_armature.unregister()
    pose_library.unregister()
    driver.unregister()
    uv_authoring.unregister()
    authoring_ik.unregister()
    authoring_camera.unregister()
    selection.unregister()
    export_flow.unregister()
    help_dispatch.unregister()
