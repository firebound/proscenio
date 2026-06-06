"""Skinning operators.

Subpackage with:

- bind_mesh                - PROSCENIO_OT_bind_mesh_to_armature
- restore_weight_snapshot  - PROSCENIO_OT_restore_weight_snapshot
- edit_weights             - PROSCENIO_OT_edit_weights_modal
- set_bone_mode            - per-bone SOFT/HARD bind-mode toggle
- sidecar_io               - export / import the weight sidecar
- brush_preset             - brush curve presets for weight paint
- copy_weights_to_selected - KNN weight copy across meshes
"""

from __future__ import annotations

from . import (
    bind_mesh,
    brush_preset,
    copy_weights_to_selected,
    edit_weights,
    restore_weight_snapshot,
    set_bone_mode,
    sidecar_io,
)


def register() -> None:
    bind_mesh.register()
    restore_weight_snapshot.register()
    edit_weights.register()
    set_bone_mode.register()
    sidecar_io.register()
    brush_preset.register()
    copy_weights_to_selected.register()


def unregister() -> None:
    copy_weights_to_selected.unregister()
    brush_preset.unregister()
    sidecar_io.unregister()
    set_bone_mode.unregister()
    edit_weights.unregister()
    restore_weight_snapshot.unregister()
    bind_mesh.unregister()
