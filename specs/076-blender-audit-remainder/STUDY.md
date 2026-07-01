# Spec 076 STUDY: Blender code-audit remainder (low-sev bugs + performance + test-quality)

## Why

Sibling spec [074-blender-code-audit-remediation](../074-blender-code-audit-remediation/STUDY.md) shipped the high- and medium-severity correctness bugs (Phase 1-2, PRs #180/#181) and the whole quick-win cleanup theme - dead-code, DRY folds, misplaced-pure-logic moves, dependency accessors (Phase 3, PR #181/#182). What it did NOT ship - the low-severity bug tail, the performance items, the test-quality gaps, the one dead-module removal, and the two correctness items that were deferred behind a design decision - is regrouped here so 074 could be pruned as "its shipped scope is done". This spec owns the remainder; the structural-decomposition theme stays in [075](../075-blender-structural-decomposition/TODO.md).

Everything here traces to the 2026-06-28 code audit ([backlog/code-audit/](../backlog/code-audit/)), adversarially verified. The audit's own headline stands: the Blender app is structurally healthy; these are refinement-grade findings, a slow-burn cleanup backlog, not a remediation list. The two deferred correctness items are the exception - real bugs, held only because the correct fix needs a design call (see Open items O3/O4).

## Scope

- **Low-severity bugs (11)** - writer + importer + shader + atlas correctness edges, each behind a guard test. See [TODO](TODO.md) Phase A.
- **Performance (4)** - quadratic-to-linear rewrites in the automesh geometry + Steiner + alpha-grid paths, each behavior-equivalence-tested. (`depsgraph-handler-linear-scans` already landed with 074's `handlers-sync-index-to-active` fold; `perimeter-length-dup` dissolves into `arc-length-resample-quadratic`.)
- **Test-quality (the one medium + hardenings + organization)** - `edit-weights-modal-lifecycle` coverage (the audit's single medium finding, and the D6 dependency spec 075 Phase C waits on), plus the weak-assertion hardenings, the coverage adds, and the automesh-test-monolith split.
- **Dead-module removal (1)** - delete the orphaned `psd_naming.py` (O2 resolved: delete).
- **Two deferred correctness bugs** - `keyframe-slot-index-drift` (O3) and `animated-delta-rest-rotation` (O4); each needs its design decision locked before implementation.

Out of scope: the structural god-module / SRP decomposition (spec 075); anything the audit refuted ([backlog/code-audit/refuted.md](../backlog/code-audit/refuted.md)).

## No functionality lost (the constraint carried from 074)

Same rule as 074 (D2): no item ships without a green guard - where the audit found NO GUARD, write the regression test first (reproduce -> fix -> pass). The export goldens (8/8, byte-identical) pin every writer-touching change; the in-Blender `run_operator_tests.py` suite pins the operator/importer changes.

## Decisions (locked, carried from 074)

| # | Decision | Rationale |
| --- | --- | --- |
| D1 | **Sequence low-risk first.** Phase A (low-sev bugs) + Phase B (perf) + Phase C (test-quality) can each be one gates-green PR; the two deferred correctness items are their own PRs once O3/O4 are locked. | Matches the 074 phasing that shipped cleanly. |
| D2 | **No item ships without a green guard.** | Carried from 074; the honest bar for "behaviour-preserving / fixed". |
| D3 | **Phase C (test-quality) unblocks spec 075 Phase C.** `edit-weights-modal-lifecycle` is the coverage 075's D6 waits on before the large operator splits. Land it early if 075's large splits are wanted sooner. | A split is "behaviour-preserving" only to the extent tests prove it. |

## Open items (the two that block implementation)

- **O3 - `keyframe-slot-index-drift` binding mechanism.** A slot-attachment keyframe today binds to the child's POSITIONAL index, so deleting an earlier attachment slides every later keyframe onto the wrong attachment. The fix binds to the attachment NAME, but there are two mechanisms:
  - **(A) string Custom Property read by the writer** - the attachment name round-trips through the export; robust to reorder/delete. Cost: touches the export round-trip + regenerates the `slot_swap` / `slot_cycle` goldens.
  - **(B) a stable-order field keeping the integer fcurve** - a persisted index->name map that survives reordering; the export stays as-is. Cost: less invasive on the format but carries extra state that can desync.
  - **Recommendation: (A)** - the name is the attachment's real identity; the two-golden regen is a small, one-time cost.
  - GUARD: rewrite `test_keyframe_slot_attachment` (it currently pins the buggy positional contract) + add a "key `axe`, delete an earlier child, assert export still resolves `axe`" case.

- **O4 - `animated-delta-rest-rotation` correction depth.** When a bone's PARENT is rotated and the child carries a screen-vertical position key, the parent-local projection is wrong and the motion reads sideways in Godot. A correct fix needs a per-frame posed-parent sample (scene-step), not a formula tweak.
  - **(A) implement the per-frame bake** - correct in every case; cost: real work (scene-step, like `sprite_frame_animations._bake_track`).
  - **(B) rest-rotation fast path + documented limitation** - apply the correction only when the parent has no rotation fcurves (the common case), document the gap. Cost: cheap; leaves a known hole.
  - **Recommendation: (B) now, (A) on demand** - the "parent animated in rotation + child screen-vertical position" case is rare; the fast path covers the overwhelming majority for a fraction of the cost.
  - GUARD: fixture - parent bone with a rotation key + child with a screen-vertical location key; assert the child's parent-local position matches the runtime-equivalent.

## Code anchors (verified at HEAD; locate by symbol if drifted)

`skeleton.py` (bone-length scale) / `sprites.py _compute_sprite_offset` (flipv) / `sprite_frame_animations.py` (frame-collapse + `_bake_track`) / `bundle.py bundle_textures` / `bind_diagnosis.py diagnose_isolated_islands` / `authoring_ik.py` (prebend) / `spritesheet_shader.py` (modulo + slicer drivers) / `unpack.py` (stuck CP) / `importers/photoshop/__init__.py` (feet-landing name-over-tag) / `slot_emit.py _resolve_default` / `geometry.py` (arc-length + inner-rotation) / `bridge.py` (steiner + alpha-grid) / `edit_weights.py` (modal lifecycle) / `attachment.py keyframe_slot_attachment` + `slot_animations.py` (O3) / `animations.py _resolve_pose_entry` (O4) / `core/psd/psd_naming.py` (delete). Gates per project: `uv run ruff check` + `ruff format --check` + `uv run mypy --config-file apps/blender/pyproject.toml` + repo-root `uv run pytest tests/` + in-Blender `run_operator_tests.py` + `run_tests.py` goldens (8/8).
