# Pre-release plan

Status: active. North-star sequencing for the first public release.

This plan is the blocking-tier view derived from the 2026-06-10 code-verified audit of every backlog (`backlog-bugs-found.md`, `backlog-manual-testing.md`, `backlog.md`, `backlog-ui-feedback.md`, `backlog-code-quality.md`). The audit confirmed that the writer output-correctness bugs and most of the broken-authoring tier from the previous plan revision were already fixed in May 2026 and removed them from the backlogs; what remains below is verified-open as of the audit. Forward-compatibility work gated on a future Blender release lives in `backlog-blender-6.md` and is out of scope for this release. The full verified item inventory is in [BACKLOGS_SUMMARY.md](BACKLOGS_SUMMARY.md).

## Release bar

- **Scope:** the complete pipeline - Photoshop -> Blender -> Godot. No partial-flow release.
- **Quality:** zero known correctness bugs. Every reproducible bug is either fixed or consciously waived before the tag.
- **Priority:** user experience first. Resolve what already exists (the shipped features and their rough edges) before adding new capability.

## Sequencing

1. **Output-correctness bugs first.** A silently-wrong `.proscenio` is the worst failure.
2. **Broken authoring features.** Tools that exist but do not work for the primary 2D workflow.
3. **Retests + verification gaps.** Confirm the code-fixed items in a GUI session; run the smoke sets that never ran.
4. **Packaging.** The mechanics of cutting a real tag.
5. **Should tier** - cheap UX wins that strongly improve first impression.
6. **Defer tier** - everything post-launch.

## Blocking tier (must clear before the release tag)

### B1. Output correctness (verified open)

- **Writer exports `armatures[0]`, ignoring the active-armature picker.** The Skeleton-panel picker shipped, but `scene_discovery.py` never reads it - a multi-armature scene silently exports the wrong rig. Found by the 2026-06-10 audit. (medium-high)
- **Validator slot noise + PG-only reads.** Slot attachments are false-positive flagged "no parent bone" (warning noise on every slot scene), and `slot_default` is still read PG-only so a CP-edited value exports unvalidated. (medium)

### B2. Broken authoring features (verified open)

- **Automesh Interactive extend / cut.** Stage 2 pen tools do nothing or spray artifacts - the core of the interactive authoring modal. Code unchanged since the 2026-06-08 report. (medium-high)
- **Edit Weights brush-curve presets error.** Preset buttons throw on click; the suspect curve-point rebuild sequence is unchanged. Capture the traceback, harden the rebuild. (medium)
- **Per-bone Soft / Hard inert under Bone Heat.** The default bind mode early-returns before the overrides pass, but the overrides box is always drawn - a prominent affordance that does nothing. Gate the box or apply the overrides post-bone-heat. (medium)
- **Create Slot misplacement (x2).** The slot Empty lands wrong when the seed mesh already has a parent (world translation written into a parent-local field) and when the mesh origin is unapplied (Empty at object origin, not geometry center). (medium)
- **sprite_frame_preview help orphan (regression).** Fixed once, silently regressed by the #96 restructure - `draw_subbox_header` has zero callers. Re-wire the sub-box help buttons. (low-medium)

### B3. Retests + verification gaps

- **Retest the code-fixed bugs in a GUI session.** The audit confirmed fixes in code for: snap-to-UV-bounds, the Drive-from-Bone triad, slot PG/CP mirror, Animation/Outliner/Skeleton row-click, atlas Apply idempotency + Edit-Mode guards, Quick Armature Z=0 plane, save-pose pre-check. Markers in `backlog-manual-testing.md` are flipped to `[~]` retest-pending; one GUI pass closes them.
- **In-editor smoke on shipped mesh / skinning features** (`backlog-manual-testing.md` 1.19-1.25) - never ran; the 2026-06-08 review surfaced most of B2 there. Every new failure is a new blocking bug.
- **Validator slot-transform-keys check:** the check exists and predates the logged failure - the original GUI repro has an unexplained root cause. Retest against slot_swap before closing.

### B4. Cross-app roundtrip pass

Section 4 of `backlog-manual-testing.md` - the doll full pipeline (PS -> Blender -> Godot) end to end, plus `slot_swap` / `slot_cycle`. The complete-flow release bar means this passes clean. The PS-side waist 1px drift and PPU=100 default are known waivers (re-measure through the UXP path during this pass).

### B5. Packaging for a real tag

- `release.yml` Photoshop job still `cp`s the retired `.jsx`; a `photoshop-v*` tag would fail. Repackage the UXP `dist/` bundle instead. (LICENSE full GPL-3.0 body: done, verified 691 lines.)

## Should tier (cheap UX wins; strongly improve first impression)

- Element-type gating: Automesh warns (not silently runs) on a sprite element; validate the sprite-stays-a-quad contract.
- Surface "preserve weights on regen" in the Mesh Generation panel where the regen actually runs; rename the deceptive "Mesh resolution"; default "Density follows bones" OFF.
- Left-align list names (Outliner); frame + unhide the offending object on Validation issue click.
- Weight Transfer: surface `max_distance` in the panel + warn on zero-coverage targets.
- Skeleton-panel warning names the armature actually used (pairs with the B1 picker fix).

## Defer tier (post-release)

- **Format / schema v2 features:** modulate / z_index / blend-mode passthrough, Bezier handles, NLA flatten, IK round-trip, sprite pivot / offset writer-side, per-asset PPU, multi-atlas, sprite_frame + visibility track export paths.
- **Storage split by intent** (PG-canonical vs CP-canonical) - targets 1.0.0 specifically; block 1.0.0 on it, not the first tag.
- **Code-quality gates:** ESLint in CI, `packages/{models,codegen}` mypy gate, the bpy `ignore_errors` sweep (fake-bpy-module already adopted) - internal health.
- **The bulk of `backlog-ui-feedback.md`** polish (copy, layout, defaults).
- **New authoring tools:** Materials panel, slot-from-bone driver, weight-paint follow-ups (region painting, live pose preview), Quick Armature follow-ups (rotation-mode choice, pick-parent, chain naming), onion-skin, pose-library evolution.
- **Other DCC exporters:** Krita / GIMP ports.

## Backlog map (where things live)

- [`backlog-bugs-found.md`](backlog-bugs-found.md) - reproducible bugs (B1 / B2 source).
- [`backlog-manual-testing.md`](backlog-manual-testing.md) - hands-on verification checklists (B3 / B4 source).
- [`backlog.md`](backlog.md) - features (mostly Defer tier).
- [`backlog-ui-feedback.md`](backlog-ui-feedback.md) - polish / copy / layout (mostly Should / Defer).
- [`backlog-code-quality.md`](backlog-code-quality.md) - toolchain gates (Defer tier).
- [`backlog-blender-6.md`](backlog-blender-6.md) - gated on Blender 6 (out of scope for this release).
