# Spec 061: Blender module decomposition - TODO

Three independent refactors plus the two folds. PR 1 is cheap and lands now while the area is fresh; PR 2 and PR 3 are trigger-gated and ride the next functional touch of their files.

## PR 1 - DRY folds (now, while sprite-bone-parent is fresh)

- [ ] Extract `resolve_target_armature(context, obj)` (parent-if-ARMATURE, then picker, then export) and route both `core/bpy_helpers/slot/bone_follow.py:28` `resolve_slot_armature` and `core/bpy_helpers/sprite/bone_attach.py:26` `resolve_sprite_armature` through it.
- [ ] Extract one shared bone-orientation helper for the `_INTO_SCREEN_MIN_Y = 0.7` threshold plus the `abs(direction.y)` check, and route both `bone_parent_collapses` (slot) and `bone_in_picture_plane` (sprite) through it.

## PR 2 - planes material extraction (rides the next importer-material change)

- [ ] Lift the `_attach_material` shader-node build (Emission / Mix / Transparent wiring) out of `importers/photoshop/planes.py` into a material-builder helper beside `core/_shared/material_images.py`, leaving `_place_and_tag` as pure orchestration. The flat-material and PSD-import goldens guard it.

## PR 3 - automesh_authoring split (rides the next automesh-authoring feature or bug)

- [ ] Investigate `bridge.py` first: confirm whether it is a cohesive facade or a catch-all.
- [ ] Extract the pen state machine, the input router (`_neutral_event` / `_draw_event` / `_pen_*`), and the stroke store from `operators/automesh/automesh_authoring.py` into collaborators the operator composes, leaving the operator as the modal shell. The existing headless operator pytest is the safety net.
