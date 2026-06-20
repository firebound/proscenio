# Spec 061: Blender module decomposition

A 2026-06-20 size and single-responsibility audit of `apps/blender` found the layering sound but three modules concentrating too many responsibilities in one unit, plus two small DRY duplications introduced by the sprite-bone-parent feature. This spec is behavior-preserving structural work: extract the over-loaded collaborators, fold the duplications, and audit the one module suspected of being a catch-all.

Scaffolded ahead of its STUDY. These are three independent refactors that can land on their own, plus two cheap folds; none is blocking and none changes behavior. The existing headless tests and goldens are the safety net.

## Scope

- `operators/automesh/automesh_authoring.py` (1335 lines, about 60 methods): extract the pen state machine, the input router, and the stroke store into collaborators the operator composes, leaving it as the Blender-facing modal shell.
- `importers/photoshop/planes.py` (556 lines): lift the inline shader-node build in `_attach_material` into a material-builder helper beside `core/_shared/material_images.py`, keeping `_place_and_tag` as pure orchestration.
- Automesh helper trio (`bridge.py` 902, `authoring_pipeline.py` 824, `authoring_overlay.py` 589): audit whether `bridge` is a cohesive facade or a catch-all before proposing a split.
- DRY fold: `resolve_slot_armature` and `resolve_sprite_armature` into one shared `resolve_target_armature(context, obj)`.
- DRY fold: the `_INTO_SCREEN_MIN_Y = 0.7` threshold plus its `abs(direction.y)` bone-direction check into one shared bone-orientation helper.

## Open questions (resolve before coding)

- Is `bridge.py` a cohesive facade or a catch-all that grew by accretion? Investigate before deciding whether and how to split it; the other two extractions do not depend on the answer.

## Sources

Drains the "God-files and single-responsibility hotspots (2026-06-20)" section of [`backlog-code-quality.md`](../backlog-code-quality.md). The two DRY folds are the cheapest to land while the sprite-bone-parent area is fresh; the larger extractions are trigger-gated in the backlog (do them when the file fights the next change), and this spec is the home for that work when the trigger fires.
