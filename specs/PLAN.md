# Pre-release plan

Status: active. North-star sequencing for the first public release.

This plan is the blocking-tier view derived from a full sweep of every backlog (`backlog-bugs-found.md`, `backlog-manual-testing.md`, `backlog.md`, `backlog-ui-feedback.md`, `backlog-code-quality.md`). Forward-compatibility work gated on a future Blender release lives in `backlog-blender-6.md` and is out of scope for this release - it is intentionally excluded here. The full activity inventory, grouped by plugin and area, is in [`BACKLOGS_SUMMARY.md`](./BACKLOGS_SUMMARY.md).

## Release bar

- **Scope:** the complete pipeline - Photoshop -> Blender -> Godot. No partial-flow release.
- **Quality:** zero known correctness bugs. Every reproducible bug is either fixed or consciously waived before the tag.
- **Priority:** user experience first. Resolve what already exists (the shipped features and their rough edges) before adding new capability.

## Sequencing

1. **Output-correctness bugs first.** A silently-wrong `.proscenio` is the worst failure - it ships a broken document with no error. Clear these before anything else.
2. **Broken authoring features.** Tools that exist but do not work for the primary 2D workflow.
3. **Verification gaps.** Run the in-editor smoke set that never ran; fix what it surfaces.
4. **Packaging.** The mechanics of cutting a real tag.
5. **Should tier** - cheap UX wins that strongly improve first impression.
6. **Defer tier** - everything post-launch.

## Blocking tier (must clear before the release tag)

### B1. Writer output-correctness (silent wrong `.proscenio`)

The writer ships broken documents without raising an error - top of the list.

- **Rotation axis mismatch.** `animations.py` reads `rotation_euler[2]` (Z) but the project convention keyframes `[1]` (Y, camera-axis in Front Ortho). Every rotation animation on a convention-following rig produces a dead track. (HIGH)
- **Bone-local Z dropped for horizontal bones.** `_resolve_pose_entry` assumes vertical bones; horizontal bones lose their translation tracks silently. (medium)
- **Identity matrix for hidden meshes.** `hide_viewport=True` attachments read a stale identity `matrix_world`, so slot attachments land at world origin in Godot instead of tracking the slot. (medium-high)
- **Slot PG <-> CP mirror gap.** `is_slot`, `slot_default`, `is_outliner_favorite` have no `update` callback and are absent from `OBJECT_MIRROR_MAP`. The headless writer reads stale CPs - wrong `slot_default` / `is_slot` in the output. (HIGH)

### B2. Broken authoring features

- **Quick Armature Z=0 plane.** `mouse_event_to_z0_point` projects onto Z=0; in Front Ortho (the primary 2D view) every bone collapses horizontal. The operator is unusable for the main workflow. Fix the plane, or mark not-ready. (HIGH)
- **Drive from Bone triad.** Three combined bugs make the feature appear fully broken: `LOCAL_SPACE` returns 0 for world-Z rotation, residual seed keyframes clamp the driver output, and an F9 target switch adds a second driver instead of migrating. (HIGH x2 + medium)
- **Automesh Interactive extend / cut.** Stage 2 pen tools do nothing or spray mesh artifacts - the core of the interactive authoring modal. (medium-high)
- **Atlas Apply correctness.** Non-idempotent re-click shrinks UVs each time; runs silently in Edit Mode and wipes UV data; material rename between Apply and Unpack breaks restoration silently. Add `poll() == OBJECT` guards + idempotency. (medium-high)
- **Edit Weights brush-curve presets error.** The preset buttons throw on click; capture the traceback and harden the curve-point rebuild. (medium)
- **Per-bone Soft / Hard inert under Bone Heat.** The default bind mode never reads the per-bone overrides, but the box is always shown - a prominent affordance that does nothing. Gate or apply. (medium)

### B3. Verification gap on shipped mesh / skinning features

Automesh, bind, weight paint, and interactive authoring shipped with headless coverage only; the in-editor smoke (`backlog-manual-testing.md` 1.19-1.25) never ran. The 2026-06-08 review already surfaced real bugs there (most of B2). Run the full smoke set on a GUI Blender; every layout regression or failure found is a new blocking bug.

### B4. Cross-app roundtrip pass

Section 4 of `backlog-manual-testing.md` - the doll full pipeline (PS -> Blender -> Godot) end to end, plus `slot_swap` / `slot_cycle`. The complete-flow release bar means this passes clean.

### B5. Packaging for a real tag

- Full GPL-3.0 body in `LICENSE` (ships header + placeholder today).
- `release.yml` Photoshop job still `cp`s the retired `.jsx`; a `photoshop-v*` tag would fail. Repackage the UXP `dist/` bundle instead.
- Note: the JSX-era PPU=100 roundtrip drift is a known PS-roundtrip quirk, not a blocker - waive it explicitly for this release.

## Should tier (cheap UX wins; strongly improve first impression)

- Per-subpanel help topics + clickable see-also (the help text exists at the panel level only today; subpanels reuse the parent topic).
- Move / duplicate the **Validate** button into the Validation panel (today it only lives in Export).
- Left-align every list; surface "preserve weights on regen" where the regen actually runs; rename the deceptive "Mesh resolution".
- Element-type gating: Automesh warns (not silently runs) on a sprite element.
- Skeleton / Animation / Outliner row-click drives the viewport (select bone, assign action) - selectors that store an index but do nothing today.

## Defer tier (post-release)

- **Format / schema v2 features:** modulate / z_index / blend-mode passthrough, Bezier handles, NLA flatten, IK round-trip, sprite pivot / offset, per-asset PPU, multi-atlas. All additive-optional or a `format_version=2` concern.
- **Storage split by intent** (PG-canonical vs CP-canonical) - targets 1.0.0 specifically, so the public surface ships the final storage contract; block it on landing before 1.0.0, not before the first tag.
- **Code-quality gates:** ESLint in CI, `packages/{models,codegen}` mypy gate, the bpy `ignore_errors` sweep - internal health, no user impact.
- **The bulk of `backlog-ui-feedback.md`** polish (copy, layout, defaults).
- **New authoring tools:** Materials panel, slot-from-bone driver, weight-paint productivity follow-ups, Quick Armature follow-ups, onion-skin, pose-library evolution.
- **Other DCC exporters:** Krita / GIMP ports.

## Backlog map (where things live)

- [`backlog-bugs-found.md`](backlog-bugs-found.md) - reproducible bugs (B1 / B2 source).
- [`backlog-manual-testing.md`](backlog-manual-testing.md) - hands-on verification checklists (B3 / B4 source).
- [`backlog.md`](backlog.md) - features (mostly Defer tier).
- [`backlog-ui-feedback.md`](backlog-ui-feedback.md) - polish / copy / layout (mostly Should / Defer).
- [`backlog-code-quality.md`](backlog-code-quality.md) - toolchain gates (Defer tier).
- [`backlog-blender-6.md`](backlog-blender-6.md) - gated on Blender 6 (out of scope for this release).
