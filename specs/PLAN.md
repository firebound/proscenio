# Pre-release plan

Status: active. North-star sequencing for the first public release.

## Release bar (locked 2026-06-08)

- **Scope:** the complete pipeline - Photoshop -> Blender -> Godot. No partial-flow release.
- **Quality:** zero known bugs. Every reproducible bug in [`backlog-bugs-found.md`](backlog-bugs-found.md) is either fixed or consciously waived before the tag.
- **Priority:** user experience first. Resolve what already exists (the shipped specs + their rough edges) before adding new capability from [`backlog.md`](backlog.md).

## Sequencing

0. **Close the open specs first.** 023 (help / docs / i18n) and 024 (preferences) are partially opened (STUDY only). Land their basics so the `apps/blender` UI/UX series (019 naming, 022 structure, 023 help, 024 preferences) is complete before we touch blockers.
1. **Blockers** - the Blocking tier below.
2. **Backlog** - the should / defer tiers, worked after the specs and blockers clear.

## Blocking tier (must clear before the release tag)

1. **Verification gap on the shipped mesh / skinning features.** Automesh, bind, weight paint, and interactive authoring shipped with headless coverage, but the in-editor smoke ([`backlog-manual-testing.md`](backlog-manual-testing.md) 1.19-1.25) never ran. The 2026-06-08 manual review already surfaced real bugs there (interactive extend / cut broken, brush-curve presets error, per-bone Soft / Hard inert under the default Bone Heat mode). Run the smoke set; fix what it surfaces.
2. **Writer output-correctness bugs (silent wrong `.proscenio`).** `rotation_euler[2]` vs `[1]` (kills Front-Ortho Y-axis rotation animation), identity matrix for `hide_viewport` meshes (slot attachments land at origin), the slot PG <-> CP mirror gap. These ship a broken document without an error - top of the bug list.
3. **Quick Armature Z=0 plane.** The operator is unusable in Front Ortho (the primary 2D view). Fix or mark not-ready.
4. **Packaging for a real tag.** Full GPL-3.0 body in `LICENSE`; the `release.yml` Photoshop job still references the retired `.jsx` (a `photoshop-v*` tag would fail).
5. **Cross-app roundtrip pass.** Section 4 of `backlog-manual-testing.md` (doll full pipeline PS -> Blender -> Godot). The complete-flow release bar means this passes end to end.

## Should tier (cheap UX wins; strongly improve first impression)

- Per-subpanel help topics + clickable see-also (spec 023).
- Validate button inside the Validation panel; left-align every list; surface "preserve weights on regen" where the regen runs; rename the deceptive "Mesh resolution".
- Element-type gating (Automesh warns on a sprite element).

## Defer tier (post-release)

- Format / schema v2 features (modulate / z_index / blend-mode, bezier, NLA, IK round-trip, sprite pivot / offset).
- Code-quality gates (eslint in CI, models / codegen mypy, bpy `ignore_errors` sweep) - internal health.
- The bulk of `backlog-ui-feedback.md` polish.
- Split PG-vs-CP storage by intent (targets 1.0.0, not necessarily the first release).

## Backlog map (where things live)

- [`backlog-bugs-found.md`](backlog-bugs-found.md) - reproducible bugs (Blocking-tier source).
- [`backlog-manual-testing.md`](backlog-manual-testing.md) - hands-on verification checklists (Blocking-tier source).
- [`backlog.md`](backlog.md) - features (mostly Defer tier).
- [`backlog-ui-feedback.md`](backlog-ui-feedback.md) - polish / copy / layout (mostly Should / Defer).
- [`backlog-code-quality.md`](backlog-code-quality.md) - toolchain gates (Defer tier).
- [`backlog-blender-6.md`](backlog-blender-6.md) - gated on Blender 6 (out of scope).
