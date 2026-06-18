# Godot importer robustness backlog

Code-read defects in the Godot import path (`apps/godot/addons/proscenio/`), promoted from the QA Companion audit on 2026-06-15 ([findings.md](../tools/qa-companion/findings.md)). These were found by reading, not yet reproduced in the editor; each cites the exact code. Most share one root: the builders trust the document shape with no validation, so malformed or duplicate-name input silently corrupts the rig or aborts the whole import. A single defensive pass over the builders closes the cluster.

## Non-destructive reimporter is an empty stub (decision needed)

**What:** The doc and `reimporter.gd`'s own header promise a diff/merge reimport that preserves user edits to the generated scene, but `reimporter.gd` is an empty `RefCounted` with no code - no diff is ever performed. "Wrapper-scene safety" is purely a side effect of Godot scene instancing (`importer.gd` `_import` overwrites the `.scn` wholesale every reimport; direct edits to the generated scene are clobbered, only edits in a separate wrapper survive).

**Where:** `apps/godot/addons/proscenio/reimporter.gd:1-10`; `apps/godot/addons/proscenio/importer.gd` (`_import` overwrite).

**Decision:** product call - either build the diff/merge reimporter, or drop the non-destructive claim from the doc and the file header and document the wrapper-scene pattern as the supported path. Severity high (a promised feature a user can hit). Tied to the Blender side's "re-import rebuilds the armature" item in [backlog-bugs-found.md](backlog-bugs-found.md).

## Malformed polygon or UV point aborts the whole import

**What:** `mesh_builder` reads `p[0]`/`p[1]` for polygon points and `u[0]`/`u[1]` for UVs with no length guard; a point or UV entry with fewer than two floats throws an out-of-bounds error that aborts the entire import (the sprite path uses `>= 2` guards, the mesh path does not). Root cause is upstream: the generated `ProscenioParseHelpers._parse_vec2_array` does not enforce a 2-element length.

**Where:** `apps/godot/addons/proscenio/builders/mesh_builder.gd:60-61` (polygon), `:83-84` (uv); `apps/godot/addons/proscenio/schema_bindings/proscenio_parse_helpers.gd` (`_parse_vec2_array`).

**Fix:** one length guard in `_parse_vec2_array` (skip/clamp short entries) closes both; or mirror the sprite-side `size() >= 2` checks. Severity medium.

## Duplicate bone names silently orphan a bone

**What:** `skeleton_builder` keys `bones[json_name]` by raw name with no collision check; two bones sharing a name overwrite the dict entry, so the first bone's parent linkage is lost and its node can be orphaned or re-rooted.

**Where:** `apps/godot/addons/proscenio/builders/skeleton_builder.gd:30,32-42`.

**Fix:** detect a name collision and warn (or disambiguate) before keying the dict. Severity medium.

## Animation target lookup binds across the whole tree

**What:** `sprite_frame` / `slot_attachment` track targets resolve via `character_root.find_child(target, true, false)` across the entire scene, so a track can bind to a same-named node in an unrelated subtree (a bone or slot child) instead of the intended element.

**Where:** `apps/godot/addons/proscenio/builders/animation_builder.gd:62,80`.

**Fix:** scope the lookup to the intended element kind/subtree, or resolve by a full path rather than the first same-named node. Severity medium.

## Skinned mesh with all-missing bones renders undeformed but skeleton-bound

**What:** `_apply_skinning` sets `poly.skeleton` and clears bones before validating that any weight resolves; if every weight references a missing bone the Polygon2D is left with a skeleton path and zero bone weights, yielding an undeformed mesh that is still bound to the skeleton (silently wrong, no warning). The #116 topology change to a sibling node did not address this.

**Where:** `apps/godot/addons/proscenio/builders/mesh_builder.gd:15-27`.

**Fix:** resolve the weights first; only set `poly.skeleton`/`clear_bones` when at least one bone resolves, else skip skinning with a warning. Severity medium.

## Empty or mismatched slot default hides every attachment

**What:** attachment visibility is `visible = (sanitized_name == slot_default)`; if a slot omits `default` (empty string) or the default never matches an attachment name, every attachment in the slot imports hidden with no warning.

**Where:** `apps/godot/addons/proscenio/builders/sprite_attach_util.gd:53`; `slot_builder.gd:65`.

**Fix:** warn when no attachment matches the default, and/or fall back to showing the first attachment. Severity medium.

## Bone parent resolution uses the raw name while everything else is sanitized

**What:** parent resolution keys on the raw JSON `parent` name, while weight/slot/animation lookups use `NodeNameUtil.sanitize`; a parent reference already in sanitized form (e.g. `upper_arm_L` when the bone is `upper_arm.L`) silently fails and roots the child at the skeleton.

**Where:** `apps/godot/addons/proscenio/builders/skeleton_builder.gd:33-42`.

**Fix:** sanitize both sides of the parent lookup consistently. Severity low.

## Per-key interpolation field is parsed but never honored (dead field)

**What:** `ProscenioKey.interp` is parsed but never read by the animation builder; interpolation is hardcoded per property (CUBIC / CUBIC_ANGLE / NEAREST), so a per-key `interp` authored in the document is silently ignored.

**Where:** `apps/godot/addons/proscenio/builders/animation_builder.gd:113-119`.

**Fix:** either honor `key.interp` per track or remove the field from the schema. Severity low (benign; sensible hardcoded defaults). Behavior is fine, the authoring knob is dead.
