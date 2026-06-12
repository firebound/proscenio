# Dropped work

Items where the value does not justify the cost. Removed from the live backlog during the 2026-06-11 reconciliation of specs 027-035 (those specs shipped their near-term work and their folders were pruned; see [_index.md](_index.md)). Kept here, not deleted, so a pruned item never loses its reasoning: a future reader sees it was considered and consciously declined, not forgotten. Organized by originating domain, mirroring [EXECUTION_MAP.md](EXECUTION_MAP.md).

Re-propose any of these only if its premise changes (a new consuming runtime, a schema feature it would ride, a real demand signal). Companion homes: [GATED.md](GATED.md) (held behind a trigger), [DEFERRED.md](DEFERRED.md) (sequenced second-stage), [decisions.md](decisions.md) (locked calls).

## 028 - schema-expressiveness

- **visibility-track-both-sides** - The visibility animation track (implement both sides or retire). Dropped and executed: the format advertised a track neither side implemented (the writer never emitted it, the importer only logged "not implemented yet"), and slot-attachment tracks already animate show/hide, so finishing it would build a duplicate mechanism plus hide-keyframe authoring that collides with the writer's `hide_viewport` export dance. The retirement (schema literal + importer stub removed) shipped in #105; this row records why the track will not come back.

## 029 - mesh-authoring

- **sprite-rigid-single-bone-bind** - A dedicated bind path / operator for sprites (since weight paint is mesh-only). Dropped: native Blender bone-parenting (Ctrl+P > Bone) already is the rigid single-bone bind, so a dedicated operator would wrap a one-keystroke native action. The element-gating warning plus the help sentence pointing sprites at native bone-parenting (both shipped in #106) cover the discovery need with zero new operators.

## 030 - skinning-weight-paint

The aspirational weight-paint cluster: high test burden, no demand signal, and several cannot round-trip through the importer-only Godot runtime.

- **bone-strength-region-painting** - Bone strength region painting (Moho influence gizmo). Dropped: duplicates the shipped Envelope bind plus native bone envelopes with a new gizmo surface; Moho itself treats region binding as the non-default refinement.
- **live-pose-preview** - Live pose-mode preview in weight paint. Dropped: native Blender already poses bones live inside Weight Paint mode; the shipped help line documents the native combo instead of rebuilding it in a modal.
- **cubism-glue-seam-bind** - Cubism Glue seam-bind equivalent. Dropped: cannot round-trip - Godot has no vertex-stitch runtime constraint, so glue would author data the export must discard.
- **smart-bone-corrective-drivers** - Smart-Bone corrective drivers. Dropped: requires a morph / vertex track the schema does not have and `Polygon2D` cannot play; re-propose only inside a future schema-level morph feature.
- **mirror-humanoid-binding** - Mirror humanoid binding. Dropped: cutout limbs are separate asymmetric drawings (3/4-view standard), so there is no symmetric mesh to mirror and no symmetric fixture, and brush X-mirror already covers the single-mesh case.
- **bezier-brush-stroke** - Bezier brush stroke for alpha-boundary trace. Dropped: silhouette authoring belongs to the mesh-authoring spec, polyline strokes plus arc-length resample already smooth contours, and it is the highest-burden test class (stroke feel) with zero demand signal.

## 031 - rigging-and-posing

The Quick-Armature precision cluster (Blender Edit Mode is its precision tier) plus the panel features that duplicate a native one editor away.

- **qa-preview-clamp-color (clamp half)** - Clamp the preview line under panel overlays. Dropped: the red-line + tooltip half shipped; the clamp half is cosmetic geometry on a modal.
- **qa-numeric-length** - Numeric length entry (Tab to type) during the modal. Dropped: a text-entry state machine inside the modal; Edit Mode E plus a typed length already covers precision one Tab away.
- **qa-local-axis-lock** - Local-axis lock (press axis twice). Dropped: local equals global in the XZ-locked, origin-anchored workflow, so the double-press distinction has no reachable case.
- **qa-defaults-help-topic** - A help topic for the quick_armature defaults. Dropped: the field tooltips self-describe; the existing quick_armature topic is the home.
- **skeleton-inline-rename** - Inline bone rename in the Skeleton panel. Dropped: row-click owns the click, and row-click plus F2 is the native rename path.
- **skeleton-bone-collections** - Bone-collection management from the panel. Dropped: duplicates the native Bone Collections panel one editor away.
- **skeleton-hierarchy-editing** - Richer bone-hierarchy editing beyond the read-only readout. Dropped: Edit Mode is the hierarchy editor; the readout is read-only by design.
- **ik-fk-switch** - IK/FK runtime switch (Rigify-style). Dropped: a film-rig technique; the export is baked and the toggle covers authoring, so a runtime switch has no consumer.
- **pose-apply-to-selection** - One-click apply-pose-to-selection. Dropped: the native Asset Shelf apply already targets selected bones.
- **pose-thumbnails** - Pose-asset thumbnails via the preview camera. Dropped: native auto-preview ships with pose assets; flat-render swatches are cosmetic.

## 033 - atlas-packing

- **packing-controls (strip whitespace)** - Strip transparent pixels around each sprite before packing. Dropped: sources already arrive trimmed (UXP trim plus UV-bounds slices), no offset channel exists to compensate the geometry shift, and stripping would corrupt sprite_frame full-sheet grids. (The edge-padding sibling of this control shipped in #110; only strip-whitespace and rotation are dropped.)
- **packing-controls (rotation)** - Rotate sprites 90 degrees for denser packing. Dropped: Godot cannot consume rotated atlas regions (`AtlasTexture` / `region_rect` cannot express rotation), so rotation is a Polygon2D-only footgun bought for marginal density.
- **maxrects-heuristics** - Try multiple MaxRects heuristics for density. Dropped: BSSF is already the strongest single heuristic (~94% occupancy); trying them all buys low single-digit density at multiplied pack time.

## 034 - photoshop-plugin

Tag types with no consuming runtime, mostly Adobe Character Animator face-puppetry concepts that contradict the locked explicit-bracket design.

- **slice-9slice-tag** - `[slice]` Cocos-style 9-slice tag. Dropped: 9-slice is scalable-UI furniture in every engine doc, the pipeline ships rigged characters, and Godot configures nine-patch insets engine-side on a plain texture, so the tag would round-trip editor settings through parser, manifest, importer, and builder for no authoring win.
- **head-turner-groups** - Head-turner view groups (Character Animator). Dropped: Character Animator face puppetry bound to a face-rig template and a head-turn runtime Proscenio does not have; slot attachments already express view swapping in this model.
- **pseudo-keyword-tagging** - Pseudo-keyword auto-tagging (Head, Mouth, Eye). Dropped: implicit match-inside-name tagging (Character Animator matches "Ah" inside "My Ah") collides with arbitrary artist naming and contradicts the locked explicit-bracket design that already shipped.

## 035 - project-health

Coverage / CI bookkeeping that protects no behavior, plus one duplicate ledger row.

- **ci-matrix-expansion** - Godot / Blender CI matrix expansion. Dropped: no version-specific code path or support claim on the Godot side; a multi-version leg doubles heavy CI to catch nothing (the Blender half lives in the matrix gate).
- **bpy-stubs-override-sweep** - Drop the remaining bpy `ignore_errors` overrides. Dropped: a duplicate ledger row of the gated `mypy-ignore-errors-subtrees` (the stubs-adoption half already shipped in PR #80), so the remaining work lives in that gate, not here.
- **drop-bpy-coverage-exclusions** - Drop bpy-bound coverage exclusions when units are comprehensive. Dropped: denominator bookkeeping gated on an unscheduled comprehensive-units project; removing exclusions protects no behavior.
- **edge-polish-pure-modules** - Edge-polish ~8 pure modules at 89-93%. Dropped: one to six edge lines per module at 89-93%; the backlog already wrote it off as diminishing returns.
- **doll-oracle-v2** - Doll-roundtrip oracle re-run against schema v2. Dropped: the structural pytest already pins the v2 manifest; a byte-equal capture only locks whitespace and key order, firing on intentional serialisation changes - churn, not protection.
