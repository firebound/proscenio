# Correctness findings (apps/blender) - verdicts

> **STATUS: verified + partially shipped.** The phase-3 deep correctness pass produced 40 candidate leads; spec 074 verified them against the real code and shipped the confirmed high- and medium-severity bugs (PRs #180 / #181). The low-severity tail, the performance items, and the two decision-gated bugs moved to [spec 076](../../076-blender-audit-remainder/TODO.md). This file now records the verdicts rather than "pending".

The finder dimensions that never ran under the original token limit (custom-property/storage-proxy contract, orphaned-datablock lifecycle, error-paths/swallowed-exceptions deeper pass, type-safety escape hatches, Blender version-compat 4.2 vs 5.x) are still un-swept; a future correctness pass can resume `wf_9067a358-8eb`.

## Resolved - shipped in spec 074 (PRs #180, #181)

**Phase 1 (high severity, PR #180):** `bone-frame0-negative-time` (clamp `time = max(0.0, ...)`), `redo-wrong-parent` (redo reparents to the record, not the live chain), the modal-guard lockout pair `finish-flag-clear-last` + `manual-draw-invoke-leak` (clear the run guard first / suppress-wrap each cleanup), and the automesh-regen provenance cluster `regen-wipes-provenance` + `noop-regen-overwrites-provenance` + `regen-drops-snapshots` (read per-vert provenance from the prior sidecar; carry `snapshots` forward).

**Phase 2 (medium, PR #181):** `regen-rerig-false-preserve` (flag `rig_mismatch`), `vgroup-fallback-wipes-provenance` (warn the loss), `restore-snapshot-baseline-names` (rebuild groups from the snapshot's own weights), `tablet-pressure-resets-tracker` (gate the pressure-dip on `_stroke_active`), `register-overlay-partial-leak` + `refresh-overlay-partial-leak` + `automesh-invoke-partial-leak` + `edit-weights-no-cancel` (the modal-lifecycle leak fixes), `unweighted-vertex-zero-column` (deterministic real-bone fallback), and `feet-landing-ignores-origin-offset` (read the true lowest quad vertex, honouring a sprite `[origin]`).

Each shipped behind a green guard (TDD red -> green); the 8/8 export goldens stayed byte-identical.

## Open leads - moved to spec 076

### Decision-gated (lock O3 / O4 first)

- **keyframe-slot-index-drift** `[high / medium]` - [attachment.py:187-199](../../../apps/blender/operators/slot/attachment.py#L187) - `keyframe_slot_attachment` stores a POSITIONAL index over `empty.children` order; deleting/reparenting an earlier child shifts every later key onto the wrong attachment. Bind to NAME. **O3 fork** (string CP vs stable-order field) - see [spec 076 STUDY](../../076-blender-audit-remainder/STUDY.md).
- **animated-delta-rest-rotation** `[medium / medium]` - [animations.py:248](../../../apps/blender/exporters/godot/writer/animations.py#L248) - `_resolve_pose_entry` rotates into parent-local using the parent's STATIC rest rotation; when the parent is itself animated to rotate, a screen-space translation reads off-axis. Needs a per-frame posed-parent sample. **O4 fork** (full bake vs fast-path + documented limitation) - see spec 076 STUDY.

### Low-severity bugs (spec 076 Phase A)

- **bone-length-armature-scale** `[low / medium]` - [skeleton.py:113](../../../apps/blender/exporters/godot/writer/skeleton.py#L113) - length uses armature-LOCAL rest length while head/tail inherit object scale; with non-unit un-applied scale the bars mismatch joint spacing.
- **flipv-offset-double-count** `[low / low]` - [sprites.py:130](../../../apps/blender/exporters/godot/writer/sprites.py#L130) - `_compute_sprite_offset` pushes local_center through a matrix that already contains the negative scale Godot applies independently; off-center + flip_v double-counts the mirror.
- **direct-frame-collapse-no-grid** `[medium / low]` - [sprite_frame_animations.py:149-169](../../../apps/blender/exporters/godot/writer/sprite_frame_animations.py#L149) - unset grid -> `max_frame=0` -> `raw % 1 = 0` collapses the whole sprite_frame animation to one key; the frame-bake path does not validate the grid.
- **bundle-filename-collision** `[low / medium]` - [bundle.py:40-47](../../../apps/blender/exporters/godot/writer/bundle.py#L40) - two distinct images collapsing to the same basename: the second's source is never copied, export references wrong bytes.
- **bind-diagnosis-index-crash** `[low / low]` - [bind_diagnosis.py:113-132](../../../apps/blender/core/skinning/bind_diagnosis.py#L113) - `diagnose_isolated_islands` indexes `parent` with raw face members; an out-of-range face index raises IndexError (pure public fn, no guard).
- **inplane-prebend-root-anchor** `[low / medium]` - [authoring_ik.py:388-392](../../../apps/blender/operators/armature/authoring_ik.py#L388) - slice `members[1:]` still nudges the root anchor; should be `members[1:-1]`.
- **spritesheet-shader-no-modulo** `[low / high]` - [spritesheet_shader.py:110-118](../../../apps/blender/core/bpy_helpers/spritesheet/spritesheet_shader.py#L110) - the row path lacks the MODULO-by-vframes the canonical `cell_offset_y` has; an out-of-range frame yields an out-of-grid row.
- **drop-slicer-drivers-dead** `[low / medium]` - [spritesheet_shader.py:349-362](../../../apps/blender/core/bpy_helpers/spritesheet/spritesheet_shader.py#L349) - reads the wrong datablock (`material.animation_data` not `material.node_tree.animation_data`) and matches a data_path the real driver never has; would leak orphan drivers if node-remove order changed.
- **corrupt-prepack-stuck-cp** `[low / medium]` - [unpack.py:60-64](../../../apps/blender/operators/atlas_pack/unpack.py#L60) - a corrupt `PROSCENIO_PRE_PACK` JSON `continue`s before the `del`, so the stale key stays and Unpack is a permanent no-op.
- **feet-landing-name-over-tag** `[low / medium]` - [__init__.py:300](../../../apps/blender/importers/photoshop/__init__.py#L300) - the layer lookup tries name first then the tag - reverse of the authoritative tag-primary ordering; a `.001`-suffixed or renamed object matches a different layer's size.
- **slot-default-min-name** `[low / low]` - [slot_emit.py:95-108](../../../apps/blender/core/slot/slot_emit.py#L95) - `_resolve_default` falls back to `min(attachments)` (alphabetical) while the array is child-order; benign (Godot resolves default by name).
- **driver-source-bone-enum-remap** `[low / low]` - [_dynamic_items.py:40](../../../apps/blender/properties/_dynamic_items.py#L40) - `driver_source_bone` EnumProperty emits 3-tuples (no explicit ids), so Blender stores the selection by positional index; a bone rename/reorder silently re-maps it to a different bone. (Sibling of the O3 positional-index class - triage the fix alongside it.)
- **degenerate-close-corrupt-state** `[medium / medium]` - [vertex_pen.py:178-188](../../../apps/blender/core/bpy_helpers/automesh/vertex_pen.py#L178) - `_snap` allows closing with `len(points) >= 2`; a 2-vert close leaves `[p0,p1,p0]`, `ring()` returns None, `_apply` warns without re-arming, so a stray duplicate vert + edge_subdiv persist into the next CDT. Close should require `len >= 3` (the inline pen already does).
- **commit-contour-outer-not-manual** `[low / medium]` - [automesh_authoring.py:993-1015](../../../apps/blender/operators/automesh/automesh_authoring.py#L993) - `_commit_contour` sets `output.outer` but never `outer_is_manual = True`; latent (the contour tool was removed) but a live trap if a manual-contour tool is re-added.

### Performance (spec 076 Phase B)

- **arc-length-resample-quadratic** `[medium / high]` - [geometry.py:132-138](../../../apps/blender/core/automesh/geometry.py#L132) - `edge_index_start_distance` re-walks edges every advance, O(N^2) per slider drag on the UI thread. Carry `accumulated` incrementally (dissolves the `perimeter-length-dup` DRY cluster).
- **steiner-filter-quadratic** `[medium / high]` - [bridge.py:564-581](../../../apps/blender/core/bpy_helpers/automesh/bridge.py#L564) - every interior point tested against all holes + the full boundary, O(points * holes * hole_verts). Bbox-reject per hole first.
- **read-alpha-grid-full-walk** `[medium / medium]` - [bridge.py:166-239](../../../apps/blender/core/bpy_helpers/automesh/bridge.py#L166) - pure-Python pixel reads over every source pixel regardless of downscale, re-run on each slider drag. Cache the `AlphaGrid` per (image, downscale) across a modal session.
- **find-best-inner-rotation-quadratic** `[low / medium]` - [geometry.py:226-235](../../../apps/blender/core/automesh/geometry.py#L226) - O(N^2) over a user-slider N that can reach the hundreds. Cap the search window or correct the docstring.

### Already resolved in the cleanup

- **depsgraph-handler-linear-scans** - the outliner + slots syncs gained the bone variant's fast-path identity guard when `handlers-sync-index-to-active` folded (spec 074 Phase 3, PR #182). No work left.
