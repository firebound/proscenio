# Dropped work

Items where value does not justify cost. Removed from the live backlog during the 2026-06-11 reconciliation (the durable number-to-topic map is `index.md`). Kept here, not deleted, so a pruned item never loses its reasoning - a future reader sees it was considered and consciously declined. Re-propose only if the premise changes (a new consuming runtime, a schema feature it would ride, a real demand signal). Companion homes: [gated.md](gated.md), [deferred.md](deferred.md), [decisions.md](decisions.md). One line each: item - the decisive reason.

## Schema expressiveness

- **visibility-track-both-sides** - Slot-attachment tracks already animate show/hide, and the writer never emitted it; retirement (schema literal + importer stub removed) shipped in #105.

## Mesh authoring

- **sprite-rigid-single-bone-bind** - Native Ctrl+P > Bone already is the rigid single-bone bind; the element-gating warning + help sentence (#106) cover discovery with no new operator.

## Skinning and weight paint

High test burden, no demand signal, several cannot round-trip the importer-only Godot runtime.

- **bone-strength-region-painting** - Duplicates the shipped Envelope bind + native bone envelopes; Moho itself treats region binding as the non-default refinement.
- **live-pose-preview** - Native Blender already poses bones live inside Weight Paint mode; the help line documents the native combo.
- **cubism-glue-seam-bind** - Cannot round-trip: Godot has no vertex-stitch runtime constraint, so glue would author data the export discards.
- **smart-bone-corrective-drivers** - Needs a morph / vertex track the schema lacks and `Polygon2D` cannot play; revisit only inside a future schema-level morph feature.
- **mirror-humanoid-binding** - Cutout limbs are separate asymmetric drawings (3/4 view), so there is no symmetric mesh to mirror; brush X-mirror covers the single-mesh case.
- **bezier-brush-stroke** - Polyline + arc-length resample already smooth contours; highest-burden test class (stroke feel) with zero demand.

## Rigging and posing

Quick-Armature precision (Edit Mode is its precision tier) + panel features one native editor away.

- **qa-preview-clamp-color (clamp half)** - The red-line + tooltip half shipped; the clamp is cosmetic geometry on a modal.
- **qa-numeric-length** - A text-entry state machine inside the modal; Edit Mode E + typed length covers precision one Tab away.
- **qa-local-axis-lock** - Local equals global in the XZ-locked, origin-anchored workflow, so the double-press has no reachable case.
- **qa-defaults-help-topic** - Field tooltips self-describe; the existing quick_armature topic is the home.
- **skeleton-inline-rename** - Row-click owns the click; row-click + F2 is the native rename path.
- **skeleton-bone-collections** - Duplicates the native Bone Collections panel one editor away.
- **skeleton-hierarchy-editing** - Edit Mode is the hierarchy editor; the readout is read-only by design.
- **ik-fk-switch** - A film-rig technique; the export is baked and the toggle covers authoring, so a runtime switch has no consumer.
- **pose-apply-to-selection** - The native Asset Shelf apply already targets selected bones.
- **pose-thumbnails** - Native auto-preview ships with pose assets; flat-render swatches are cosmetic.

## Atlas packing

- **packing-controls (strip whitespace)** - Sources arrive trimmed, no offset channel compensates the shift, and stripping corrupts sprite_frame full-sheet grids. (Edge-padding sibling shipped in #110.)
- **packing-controls (rotation)** - Godot cannot consume rotated atlas regions (`AtlasTexture` / `region_rect` cannot express rotation), so it is a Polygon2D-only footgun.
- **maxrects-heuristics** - BSSF is already the strongest single heuristic (~94% occupancy); trying all buys low single-digit density at multiplied pack time.

## Photoshop plugin

Tag types with no consuming runtime, mostly Character Animator face-puppetry concepts that contradict the locked explicit-bracket design.

- **slice-9slice-tag** - Godot configures nine-patch insets engine-side on a plain texture, so the tag would round-trip editor settings through four layers for no authoring win.
- **head-turner-groups** - Character Animator face puppetry bound to a head-turn runtime Proscenio lacks; slot attachments already express view swapping.
- **pseudo-keyword-tagging** - Implicit match-inside-name tagging collides with arbitrary artist naming and contradicts the locked explicit-bracket design.

## Blender UI

- **outliner-hierarchy-tree** (the foldable widget) - Dropped 2026-06-17 (user call): Blender exposes no Python tree widget (native Tree View is C-only, [blender #118201](https://projects.blender.org/blender/blender/issues/118201)), so a *foldable / collapsible* tree could only be simulated inside the flat `UIList`. Kept the standard `UIList` with native name-search + scroll + left-aligned rows (spec 036). The list now sorts + indents by the scene parenting tree (armature -> slot -> attachment, then loose meshes) instead of the old flat by-category grouping - a sort-order change, not the dropped widget. Re-propose the foldable widget only if Blender exposes a Python tree widget, or the flat list proves unworkable on a real deep rig.
- **subpanel-drag-reorder** - Sibling top-level panels already reorder by native header-drag (`bl_order` only sets the initial order); `bl_parent_id` subpanels cannot be reordered, an upstream Blender limit. Both halves are closed - one ships free, one is not ours to fix.
- **onion-skin-overlay** - Free extensions (B Onion Skin) already ghost rigged characters and Blender has an open upstream design task ([T102217](https://developer.blender.org/T102217)); a Proscenio overlay would be the largest GUI-test surface in the addon for zero pipeline impact. Re-propose only if a cutout-animation session proves the ecosystem tools insufficient.
- **texture-region-hide-for-mesh** - The premise was false: `resolve_region` honours a mesh's manual region and Snap-to-UV bounds is mesh-only, so hiding the Texture Region subpanel for a mesh element would drop a working control. Re-propose only if `Polygon2D` stops consuming the region.

## Project health

Coverage / CI bookkeeping that protects no behavior, plus one duplicate ledger row.

- **ci-matrix-expansion** - No version-specific code path on the Godot side; a multi-version leg doubles heavy CI to catch nothing (the Blender half is in the matrix gate).
- **bpy-stubs-override-sweep** - Duplicate ledger row of the gated `mypy-ignore-errors-subtrees`; the remaining work lives in that gate.
- **drop-bpy-coverage-exclusions** - Denominator bookkeeping gated on an unscheduled comprehensive-units project; removing exclusions protects no behavior.
- **edge-polish-pure-modules** - One to six edge lines per module at 89-93%; diminishing returns.
- **doll-oracle-v2** - The structural pytest already pins the v2 manifest; a byte-equal capture only locks whitespace + key order, firing on intentional serialization changes.
