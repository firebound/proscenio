# Spec 051: Godot importer hardening - TODO

Three small PRs over `apps/godot/addons/proscenio/builders/`. None blocks another.

## PR 1 - builder input guards

- [ ] Add one shared length-guarded helper for packed 2D points and route `mesh_builder.gd:60-61` (polygon `p[0]/p[1]`) and `:83-84` (UV `u[0]/u[1]`) through it, matching `skeleton_builder.gd:47` `_vec2_from_packed`.
- [ ] Resolve weights first in `mesh_builder.gd:15-29`; only set `poly.skeleton` + `clear_bones` and bind once at least one weight resolves, so an all-missing-bone mesh is not bound undeformed.
- [ ] Warn or disambiguate on a duplicate bone name in `skeleton_builder.gd:30` instead of overwriting the lookup dict silently.

## PR 2 - resolution and animation fidelity

- [ ] Scope the animation-target lookup in `animation_builder.gd:53,80`; `find_child(target, true, false)` can bind to an unrelated subtree. Narrow it the way the `sprite_frame` path narrows by `Sprite2D` type.
- [ ] Warn (or fall back to the first attachment) in `sprite_attach_util.gd` `resolve_sprite_parent` when the slot default matches nothing, instead of `visible = name == default` hiding all.
- [ ] In `animation_builder.gd:148-154`, set `value_track_set_update_mode(idx, UPDATE_DISCRETE)` on the `sprite_frame` index track (currently only NEAREST interp, fragile under blend/seek).
- [ ] Resolve the dead per-key `interp` field in the same block: honor `key.interp` or drop it from the schema. Pick drop unless honoring is cheap, since the fidelity case is gated.

## PR 3 - regression test

- [ ] In `apps/godot/tests/test_slot_anchor.gd:77-85`, assert `slot.get_parent() == child_bone` before the position checks; today a regression that parents to the skeleton root still yields a near-zero rest position and passes.
