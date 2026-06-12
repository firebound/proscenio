# Pre-release plan

Status: active. Value-ranked sequencing for the first public release.

This plan is the value-ranked attack on every open backlog, derived from the 2026-06-10 code-verified audit. The 027-035 wave that cleared most of the blocking tier shipped in PRs #104-#113 (2026-06-11); this revision marks what landed and what remains. The full item inventory is in [BACKLOGS_SUMMARY.md](BACKLOGS_SUMMARY.md); the thematic-spec breakdown and the shipped-wave record are in [EXECUTION_MAP.md](EXECUTION_MAP.md); the carved-out not-now work is in [GATED.md](GATED.md), [DEFERRED.md](DEFERRED.md), and [DROPPED.md](DROPPED.md).

## Release bar

- **Scope:** the complete pipeline - Photoshop -> Blender -> Godot. No partial-flow release. Expanded by value (see B4): one universal-need capability ships in the tag rather than being deferred behind the whole schema-v2 wave.
- **Quality:** zero known correctness bugs. Every reproducible bug is either fixed or consciously waived before the tag.
- **Priority:** value first. Within the gate, order by gain: stop the silently-wrong output, then fix the features that exist but lie, then ship the capability users hit on day one, then verify, then package.

## Blocking tier (must clear before the release tag)

Status after the 027-035 wave: the code blockers shipped; what remains before the tag is the GUI verification session (B3 / B5) and the one help-surface orphan (in the still-open ui-help-surfaces spec).

### B1. Output correctness - SHIPPED (#104, spec 027)

Writer honours the active-armature picker (shared `resolve_export_armature`), multi-polygon meshes export whole (`MeshElement.polygons`, additive at v1), and the validator slot noise + PG-only reads are fixed. The `slot-transform-keys` check is code-fixed but rides a GUI retest (B3).

### B2. Broken authoring features - SHIPPED except the help orphan

- Automesh Interactive extend / cut: fix shipped (#106, crossing-splice); **GUI retest pending** (B3).
- Edit Weights brush-curve presets, per-bone Soft/Hard under Bone Heat: shipped (#107).
- Create Slot misplacement (x2): shipped (#109, geometry-center via `matrix_world`).
- **sprite_frame_preview help orphan: still open** - it belongs to the ui-help-surfaces spec (036), the one blocking row not in the 027-035 wave. Re-wire the sub-box help buttons there.

### B3. Retests + verification gaps - PENDING (the verification session)

One GUI pass closes the code-fixed retests: `slot-transform-keys`, `automesh-interactive-extend-cut` (manual-testing 1.23 / 1.25), `skeleton-row-click-select`, `pose-save-library-precheck`, `waist-1px-drift`, and the 036 reproject-uv perf retest. Markers live in [manual-testing.md](manual-testing.md). Every new failure here is a new blocking bug.

### B4. Day-one capability: sprite appearance passthrough (light) - SHIPPED (#105, spec 028)

End-to-end `modulate` + `z_index` + `flip` on `MeshElement` / `SpriteElement`, derived from native Blender state. `mask` and `blend_mode` stayed back: `mask` is [gated](GATED.md) (needs a Godot masking strategy), `blend_mode` is [deferred](DEFERRED.md) to Wave 1.

### B5. Cross-app roundtrip pass - PENDING (the verification session)

Section 4 of [manual-testing.md](manual-testing.md): the doll full pipeline (PS -> Blender -> Godot) end to end, plus `slot_swap` / `slot_cycle`, exercising the B4 appearance fields. The PS-side waist 1px drift and PPU=100 default are known waivers (re-measure through the UXP path during this pass).

### B6. Packaging for a real tag - SHIPPED (#112, spec 035)

`release.yml` repackages the UXP `dist/` bundle (the stale `.jsx` `cp` is gone), with a `workflow_dispatch` dry-run so the job is exercised tagless and input expansion routed through env vars.

## Post-release value waves

The detailed wave items were evaluated in the 2026-06-11 effort pass and relocated: each now lives in [GATED.md](GATED.md) (behind a trigger), [DEFERRED.md](DEFERRED.md) (sequenced second-stage), or [DROPPED.md](DROPPED.md) (declined). The shape of the remaining roadmap:

- **Wave 1 - Expressiveness.** The half-built tracks shipped or retired (#105: sprite_frame export path in, visibility track out). The Spine-parity remainder (Bezier handles, per-key interp, event tracks, multi-atlas, constraints, bone physics, the migration-path enabler, blend_mode, mask) is in GATED/DEFERRED, owned by the schema-expressiveness domain.
- **Wave 2 - Project health.** The cheap gates shipped (#112: ESLint in CI, models/codegen mypy, the saved-scene assert, release repackage; #113: the mixed-feature fixture). The CI matrix, coverage-CI, and fixture-bucket items are in GATED; the coverage-polish bookkeeping is in DROPPED.
- **Wave 3 - Storage split (1.0.0).** The active [storage-split spec](EXECUTION_MAP.md) (037); lands behind the Wave 1 migration path, blocks 1.0.0, not the first tag.
- **Wave 4 - UX polish + new tools.** The active [ui-help-surfaces spec](EXECUTION_MAP.md) (036) carries the help/docs + panel-polish surface; the new-tool candidates (Materials, slot-from-bone driver, weight-paint follow-ups, Quick Armature follow-ups, IK helpers, pose-library evolution, onion-skin) are split across GATED / DROPPED.
- **Wave 5 - Reach.** The active [reach spec](EXECUTION_MAP.md) (038): Krita / GIMP exporters and the GDExtension escape hatch, all gated on triggers.

## Execution strategy

Work is attacked by spec, where a spec is a large thematic body of work around one area - a code domain or a pipeline stage - not a single fix. Each gets `specs/NNN-slug/` with `STUDY.md` first (understand the surface once, discover how many rows one fix closes) then `TODO.md`. A spec usually spans several priority tiers, so priority lives on the row, not the spec. Inside a spec, a PR is the smallest reviewer-verifiable change - one PR can close several rows on a shared root cause. The 027-035 wave proved the pattern: nine specs, nine-plus PRs, each closing a cluster of rows, verified against code before the spec folder was pruned.

To finish the release gate from here: run the verification session (B3 / B5) and close the ui-help-surfaces blocking orphan (B2). The post-release waves proceed by their triggers in GATED.md.

## Effort verdicts (2026-06-11)

A per-item effort evaluation ran across the 12 thematic specs (each scored on flow value, test burden, bug surface, and underuse risk; reasoning in each spec's STUDY.md). Of ~160 assessed items: roughly **73 now, 5 defer, 49 gate, 33 drop** - about half the backlog (gate + drop) is not scheduled work. The 027-035 share of the **now** column shipped in this wave; the gate / defer / drop shares were relocated to their named homes. The owner's bloat instinct was correct: new capability concentrates in schema-expressiveness, and even there only the additive day-one slice shipped now while the Spine-parity wave gates.

## Backlog map (where things live)

- [`backlog-bugs-found.md`](backlog-bugs-found.md) - reproducible bugs (now: the retest queue + the 036 / upstream bugs).
- [`manual-testing.md`](manual-testing.md) - hands-on verification checklists (B3 / B5 source).
- [`backlog.md`](backlog.md) - features owned by the not-yet-started specs (036 / 037 / 038) + architecture notes.
- [`backlog-ui-feedback.md`](backlog-ui-feedback.md) - polish / copy / layout (the ui-help-surfaces surface).
- [`backlog-code-quality.md`](backlog-code-quality.md) - toolchain gates (now: the wheel-staleness gap).
- [`backlog-ik-ergonomics.md`](backlog-ik-ergonomics.md) - IK authoring ergonomics (post-031 session feedback).
- [`backlog-photoshop-performance.md`](backlog-photoshop-performance.md) - UXP Tags-panel performance.
- [`backlog-blender-6.md`](backlog-blender-6.md) - gated on Blender 6 (out of scope for this release).
- [`GATED.md`](GATED.md) / [`DEFERRED.md`](DEFERRED.md) / [`DROPPED.md`](DROPPED.md) - the carved-out 027-035 not-now work.
