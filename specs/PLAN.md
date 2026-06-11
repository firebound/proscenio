# Pre-release plan

Status: active. Value-ranked sequencing for the first public release.

This plan is the value-ranked attack on every open backlog, derived from the 2026-06-10 code-verified audit (`backlog-bugs-found.md`, `backlog-manual-testing.md`, `backlog.md`, `backlog-ui-feedback.md`, `backlog-code-quality.md`). The previous revision ranked the work by what was blocking a tag; this revision re-ranks by gain to the project, then sequences that into a safe build order. The release is still the gate, but its scope is expanded by value: the tag absorbs the highest-gain capability a real user hits immediately, not just the bug floor. Forward-compatibility work gated on a future Blender release lives in `backlog-blender-6.md` and is out of scope. The full verified item inventory is in [BACKLOGS_SUMMARY.md](BACKLOGS_SUMMARY.md); the spec-by-spec breakdown of how every row is attacked is in [EXECUTION_MAP.md](EXECUTION_MAP.md).

## Release bar

- **Scope:** the complete pipeline - Photoshop -> Blender -> Godot. No partial-flow release. Expanded by value (see B4): one universal-need capability ships in the tag rather than being deferred behind the whole schema-v2 wave.
- **Quality:** zero known correctness bugs. Every reproducible bug is either fixed or consciously waived before the tag.
- **Priority:** value first. Within the gate, order by gain: stop the silently-wrong output, then fix the features that exist but lie, then ship the capability users hit on day one, then verify, then package.

## How this plan was ranked

The value lens decided *what is in* the tag, ignoring effort. The sequence below then orders that set for a safe build: stabilize and verify the base before extending it, and run the full roundtrip only after the new capability is in. So a high-value item can sit late in the sequence (B4) while still being a deliberate scope choice, not an afterthought.

Two items moved versus the prior revision:

- **`multi-polygon-truncation` promoted into output correctness (B1).** It was catalogued as a feature, but `writer/sprites.py:94` truncates a mesh to its first polygon with no warning - any multi-island sprite exports silently wrong. That is the exact failure B1 exists to stop, so it is a correctness bug, not a feature gap.
- **Sprite appearance (light subset) pulled into the tag (B4).** `modulate` / `z_index` / `flip` are a universal 2D-game need and are additive optional fields, so v1 files keep working on defaults and no migration path is needed yet. The heavy half (`mask`, `blend_mode`) needs a Godot masking strategy and stays in Wave 1.

## Blocking tier (must clear before the release tag)

### B1. Output correctness (verified open)

- **Writer exports `armatures[0]`, ignoring the active-armature picker.** The Skeleton-panel picker shipped, but `scene_discovery.py` never reads it - a multi-armature scene silently exports the wrong rig.
- **Multi-polygon mesh truncated to the first polygon.** `writer/sprites.py:94` keeps only `polygon_at(mesh, 0)` with no validation warning; any multi-island sprite exports silently wrong. Emit all polygons or, at minimum, hard-warn and refuse the partial export.
- **Validator slot noise + PG-only reads.** Slot attachments are false-positive flagged "no parent bone" (warning noise on every slot scene), and `slot_default` is still read PG-only so a CP-edited value exports unvalidated.

### B2. Broken authoring features (verified open)

- **Automesh Interactive extend / cut.** Stage 2 pen tools do nothing or spray artifacts - the core of the interactive authoring modal. Code unchanged since the 2026-06-08 report.
- **Edit Weights brush-curve presets error.** Preset buttons throw on click; the suspect curve-point rebuild sequence is unchanged. Capture the traceback, harden the rebuild.
- **Per-bone Soft / Hard inert under Bone Heat.** The default bind mode early-returns before the overrides pass, but the overrides box is always drawn - a prominent affordance that does nothing. Gate the box or apply the overrides post-bone-heat.
- **Create Slot misplacement (x2).** The slot Empty lands wrong when the seed mesh already has a parent (world translation written into a parent-local field) and when the mesh origin is unapplied (Empty at object origin, not geometry center).
- **sprite_frame_preview help orphan (regression).** Fixed once, silently regressed by the #96 restructure - `draw_subbox_header` has zero callers. Re-wire the sub-box help buttons.

### B3. Retests + verification gaps

- **Retest the code-fixed bugs in a GUI session.** The audit confirmed fixes in code for: snap-to-UV-bounds, the Drive-from-Bone triad, slot PG/CP mirror, Animation/Outliner/Skeleton row-click, atlas Apply idempotency + Edit-Mode guards, Quick Armature Z=0 plane, save-pose pre-check. Markers in `backlog-manual-testing.md` are flipped to `[~]` retest-pending; one GUI pass closes them.
- **In-editor smoke on shipped mesh / skinning features** (`backlog-manual-testing.md` 1.19-1.25) - never ran; the 2026-06-08 review surfaced most of B2 there. Every new failure is a new blocking bug.
- **Validator slot-transform-keys check:** the check exists and predates the logged failure - the original GUI repro has an unexplained root cause. Retest against `slot_swap` before closing.

### B4. Day-one capability: sprite appearance passthrough (light)

The single highest-gain capability a real user hits immediately, pulled into the tag. End-to-end `modulate` + `z_index` + `flip` on `MeshElement` / `SpriteElement`:

- Schema: add the three optional fields (additive, v1-compatible - old files default and need no migration).
- Writer: read them from the Blender source and emit them.
- Importer: stamp `Sprite2D` / `Polygon2D` modulate, `z_index`, and flip from the values.

`mask` and `blend_mode` are deferred to Wave 1: `mask` needs a Godot masking strategy and `blend_mode` lives PSD-side only today - both are heavier than the day-one bar.

### B5. Cross-app roundtrip pass

Section 4 of `backlog-manual-testing.md` - the doll full pipeline (PS -> Blender -> Godot) end to end, plus `slot_swap` / `slot_cycle`, now exercising the B4 appearance fields. The complete-flow release bar means this passes clean. The PS-side waist 1px drift and PPU=100 default are known waivers (re-measure through the UXP path during this pass).

### B6. Packaging for a real tag

- `release.yml` Photoshop job still `cp`s the retired `.jsx`; a `photoshop-v*` tag would fail. Repackage the UXP `dist/` bundle instead. (LICENSE full GPL-3.0 body: done, verified 691 lines.)

## Post-release value waves (ranked by gain)

Ordered by gain to the project, effort ignored. Each wave is a coherent push, not a strict gate on the next.

### Wave 1 - Expressiveness (what lets the tool represent real game art)

The highest-gain cluster: the format only carries a fraction of what a 2D game needs, and two tracks currently ship as lies.

- **Finish the half-built tracks first.** `sprite_frame` has no Blender export path (`grep` = zero hits); the `visibility` track still `push_warning("not implemented yet")` (`animation_builder.gd:86`) with no emission. Either complete both sides or retire them - a tool should not advertise a track it cannot fill.
- **Schema-v2 expressiveness:** multiple atlases per character (`atlas_pages`), animation event / method tracks (audio, particles), Bezier curve handles, per-key interpolation mixing, continuous-UV `texture_region` track, the heavy appearance half (`mask`, `blend_mode`).
- **Writer-side completeness:** sprite pivot / `Sprite2D.offset` from the Blender origin (schema + importer already exist; the writer never computes it), per-asset PPU end-to-end, general rig-orientation detection (XZ vs XY), auto-detect 2D rig vs 3D mesh.
- **Migration enabler:** `format-migration-path` is the prerequisite for any *breaking* schema change (field rename / removal / the Wave 3 storage split). Additive fields like B4 do not need it; the storage split does. Build it before the first breaking bump.

### Wave 2 - Project health (compounds; protects every later wave)

Each gate here prevents a class of regression - the #96 orphan is exactly what an untested restructure produces.

- **CI matrix:** Blender headless multi-version (4.2 LTS + latest) instead of the single 5.1.1 pin; Godot/Blender matrix expansion; Blender 4.3 legacy-actions path under test.
- **Lint / type gates:** ESLint in CI + pre-commit (today: typecheck + vitest only); `packages/{models,codegen}` mypy gate; finish the bpy `ignore_errors` override sweep (fake-bpy-module already adopted).
- **Coverage + fixtures:** wire `run_coverage.py` into CI, drop the bpy-bound coverage exclusions once units are comprehensive, full Godot editor-reimport test (plugin-disabled assertion), the end-to-end mixed-feature fixture.

### Wave 3 - Storage split PG-vs-CP by intent (1.0.0 target)

Collapses the dual-fallback `read_field` complexity (`writer/sprites.py:72`, `mirror.py`, `hydrate.py`) that keeps spawning validator bugs. This is a breaking change, so it lands behind the Wave 1 migration path. Block 1.0.0 on it, not the first tag.

### Wave 4 - UX polish + new authoring tools

The bulk of `backlog-ui-feedback.md` plus the new-tool backlog. First-impression wins (element-type gating, "preserve weights on regen" readout, the Mesh Generation defaults/renames, Outliner left-align, Validation frame+unhide, Weight Transfer `max_distance` + zero-coverage warning) are cheap pull-forward candidates if a tag slips. New tools: Materials panel, slot-from-bone driver, weight-paint follow-ups (region painting, live pose preview, soft/hard runtime toggle), Quick Armature follow-ups (rotation-mode choice, pick-parent, chain naming, mirror suffix), skin coordination, IK chain helper / IK-FK switch, pose-library evolution, onion-skin overlay.

### Wave 5 - Reach (new surfaces, lowest gain-per-effort right now)

- Other DCC exporters: Krita (Phase 2), then GIMP.
- GDExtension / C# escape hatch - documented and gated on triggers; build only when a trigger is actually hit.

## Execution strategy

Work is attacked by spec, where a spec is a large thematic body of work around one area - a code domain or a pipeline stage - not a single fix. Each gets `specs/NNN-slug/` with `STUDY.md` first (understand the surface once, discover how many rows one fix closes) then `TODO.md`. A spec usually spans several priority tiers: a domain holds a blocking bug and later polish in the same files, so priority lives on the row, not the spec. Inside a spec, a PR is the smallest reviewer-verifiable change - one PR can close several rows on a shared root cause, and a large spec spans many PRs. One row per PR is the anti-pattern: it fragments shared surfaces and misses root-cause collapses (the two Create-Slot rows are one matrix fix; the brush-preset and automesh failures may share one bad curve sequence).

All 158 open rows are aggregated into 12 thematic specs plus one verification session in [EXECUTION_MAP.md](EXECUTION_MAP.md). The tiers and waves above (`[blocking]`, `W1`..`W5`) are tags on the rows inside each spec, telling its `TODO.md` what to do first. To execute the release: walk every spec, do its `[blocking]` rows; then work the waves across specs in order.

## Effort verdicts (2026-06-11)

A per-item effort evaluation ran across all 12 specs (each scored on flow value, test burden, bug surface, and underuse risk; full reasoning in each spec's STUDY.md, rolled up in [EXECUTION_MAP.md](EXECUTION_MAP.md)). Of ~160 assessed items: **73 now, 5 defer, 49 gate, 33 drop**. Roughly half the backlog (gate + drop) is not scheduled work - the owner's bloat instinct was correct.

This re-weights the plan. The **now** set is the real near-term scope, and it is dominated by output-correctness bugfixes and completions of half-built surfaces, not new features. The blocking tier holds; the day-one appearance pull (B4) survived evaluation as a draw-order correctness repair, not new capability. The **drop** set is 33 rows proposed for pruning from the backlog files (the aspirational weight-paint cluster, the Quick-Armature precision items that duplicate Blender Edit Mode, new tag types with no consuming runtime, the materials/onion-skin surfaces, coverage-polish bookkeeping). The **gate** set stays in the backlog but moves behind written triggers, so no imagined-demand feature gets built ahead of a real signal. New capability concentrates in schema-expressiveness, and even there only the additive day-one slice is now; the Spine-parity wave gates.

## Backlog map (where things live)

- [`backlog-bugs-found.md`](backlog-bugs-found.md) - reproducible bugs (B1 / B2 source).
- [`backlog-manual-testing.md`](backlog-manual-testing.md) - hands-on verification checklists (B3 / B5 source).
- [`backlog.md`](backlog.md) - features (B4 + Waves 1-5 source).
- [`backlog-ui-feedback.md`](backlog-ui-feedback.md) - polish / copy / layout (mostly Wave 4).
- [`backlog-code-quality.md`](backlog-code-quality.md) - toolchain gates (Wave 2).
- [`backlog-blender-6.md`](backlog-blender-6.md) - gated on Blender 6 (out of scope for this release).
