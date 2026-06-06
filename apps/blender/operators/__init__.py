"""Proscenio operators package.

Each topical concern lives in its own submodule (or feature subpackage) with
its own ``register`` / ``unregister``. This file orchestrates the package:
imports every submodule, calls them in order on ``register()``, in reverse
order on ``unregister()``.

Submodules / subpackages:

- help_dispatch     - status badge proxy, help popup, smoke test
- export_flow       - Validate, Export, Re-export
- selection         - select issue, select outliner, toggle favorite
- armature/         - Preview Camera, Toggle IK, set active armature, Quick Armature
- uv_authoring      - Reproject UV, Snap region to UV
- driver            - Drive sprite from bone (the Drive-from-Bone shortcut)
- pose_library      - Save Pose to Library, Bake Current Pose
- automesh/         - automesh + automesh_authoring modal
- skinning/         - bind, restore / edit weights, set bone mode, sidecar IO, brush, copy
- slot              - Create Slot, Add Attachment, Set Default, preview shader
- atlas_pack        - Pack, Apply, Unpack
- import_photoshop  - single-operator file (Import Photoshop Manifest)
"""

from __future__ import annotations

from . import (
    armature,
    atlas_pack,
    automesh,
    driver,
    export_flow,
    help_dispatch,
    import_photoshop,
    pose_library,
    selection,
    skinning,
    slot,
    uv_authoring,
)


def register() -> None:
    help_dispatch.register()
    export_flow.register()
    selection.register()
    armature.register()
    uv_authoring.register()
    driver.register()
    pose_library.register()
    automesh.register()
    skinning.register()
    slot.register()
    atlas_pack.register()
    import_photoshop.register()


def unregister() -> None:
    import_photoshop.unregister()
    atlas_pack.unregister()
    slot.unregister()
    skinning.unregister()
    automesh.unregister()
    pose_library.unregister()
    driver.unregister()
    uv_authoring.unregister()
    armature.unregister()
    selection.unregister()
    export_flow.unregister()
    help_dispatch.unregister()
