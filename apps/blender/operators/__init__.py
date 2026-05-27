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
- skeleton_target   - Set Proscenio active armature pointer (SPEC 012.2)
- automesh          - PNG sprite -> annulus mesh (SPEC 013 Wave 13.1)
- automesh_authoring - PROSCENIO_OT_automesh_authoring modal (SPEC 013.2 interactive-modal)
- bind_mesh         - PROSCENIO_OT_bind_mesh_to_armature (SPEC 013.2 Wave 13.2)
- restore_weight_snapshot - PROSCENIO_OT_restore_weight_snapshot (SPEC 013.2 sidecar)
- edit_weights      - PROSCENIO_OT_edit_weights_modal (SPEC 013.2 paint)
- set_bone_mode     - PROSCENIO_OT_set_bone_mode per-bone SOFT/HARD toggle (SPEC 013 O1)
- sidecar_io        - PROSCENIO_OT_export_sidecar / import_sidecar file-dialog IO (SPEC 013 O3)
- brush_preset      - PROSCENIO_OT_set_brush_preset curve presets for weight-paint (SPEC 013 O4)
- slot              - Create Slot, Add Attachment, Set Default, preview shader
- atlas_pack        - Pack, Apply, Unpack
- import_photoshop  - single-operator file (Import Photoshop Manifest)
"""

from __future__ import annotations

from . import (
    atlas_pack,
    authoring_camera,
    authoring_ik,
    automesh,
    automesh_authoring,
    bind_mesh,
    brush_preset,
    driver,
    edit_weights,
    export_flow,
    help_dispatch,
    import_photoshop,
    pose_library,
    quick_armature,
    restore_weight_snapshot,
    selection,
    set_bone_mode,
    sidecar_io,
    skeleton_target,
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
    skeleton_target.register()
    quick_armature.register()
    automesh.register()
    automesh_authoring.register()
    bind_mesh.register()
    restore_weight_snapshot.register()
    edit_weights.register()
    set_bone_mode.register()
    sidecar_io.register()
    brush_preset.register()
    slot.register()
    atlas_pack.register()
    import_photoshop.register()


def unregister() -> None:
    import_photoshop.unregister()
    atlas_pack.unregister()
    slot.unregister()
    brush_preset.unregister()
    sidecar_io.unregister()
    set_bone_mode.unregister()
    edit_weights.unregister()
    restore_weight_snapshot.unregister()
    bind_mesh.unregister()
    automesh_authoring.unregister()
    automesh.unregister()
    quick_armature.unregister()
    skeleton_target.unregister()
    pose_library.unregister()
    driver.unregister()
    uv_authoring.unregister()
    authoring_ik.unregister()
    authoring_camera.unregister()
    selection.unregister()
    export_flow.unregister()
    help_dispatch.unregister()
