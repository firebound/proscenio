"""Proscenio operators package.

Each topical concern lives in its own submodule (or feature subpackage) with
its own ``register`` / ``unregister``. This file orchestrates the package:
imports every submodule, calls them in order on ``register()``, in reverse
order on ``unregister()``.

Submodules / subpackages:

- help_dispatch     - status badge proxy, help popup, smoke test
- export_flow       - Validate, Export, Re-export
- incorporate       - adopt a hand-authored Blender mesh as an element
- helpers           - Re-space planes (apply the Y Location spacing)
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
- reimport_element  - re-import one Element from its source manifest entry
- revert_to_plane   - revert a mesh element to its original imported plane
"""

from __future__ import annotations

from . import (
    armature,
    atlas_pack,
    automesh,
    driver,
    export_flow,
    help_dispatch,
    helpers,
    import_photoshop,
    incorporate,
    pose_library,
    reimport_element,
    revert_to_plane,
    selection,
    skinning,
    slot,
    sprite,
    uv_authoring,
)


def register() -> None:
    help_dispatch.register()
    export_flow.register()
    incorporate.register()
    selection.register()
    helpers.register()
    armature.register()
    uv_authoring.register()
    driver.register()
    pose_library.register()
    automesh.register()
    skinning.register()
    slot.register()
    sprite.register()
    atlas_pack.register()
    import_photoshop.register()
    reimport_element.register()
    revert_to_plane.register()


def unregister() -> None:
    revert_to_plane.unregister()
    reimport_element.unregister()
    import_photoshop.unregister()
    atlas_pack.unregister()
    sprite.unregister()
    slot.unregister()
    skinning.unregister()
    automesh.unregister()
    pose_library.unregister()
    driver.unregister()
    uv_authoring.unregister()
    armature.unregister()
    helpers.unregister()
    selection.unregister()
    incorporate.unregister()
    export_flow.unregister()
    help_dispatch.unregister()
