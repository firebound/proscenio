# Execution map

Status: active. The full backlog, aggregated into thematic specs.

Every one of the 158 open rows in [BACKLOGS_SUMMARY.md](BACKLOGS_SUMMARY.md) is folded into **12 thematic specs** plus one verification session. A spec is a large, coherent body of work around one area (a code domain or a pipeline stage), not a single fix. It gets `specs/NNN-slug/` with `STUDY.md` (understand the surface once) then `TODO.md` (the rows below, sequenced).

A spec usually spans several priority tiers: a domain has a blocking bug *and* later polish in the same files. So priority lives on the row, not the spec. This is the operational companion to [PLAN.md](PLAN.md): the plan ranks *what to do first* (the `[blocking]` / `[w1]`..`[w5]` tags below), this map says *which spec owns each row*. Inside a spec's `TODO.md`, do the `[blocking]` rows first, then the wave order.

Tags: `[blocking]` clears before the tag; `[w1]`..`[w5]` post-release wave; `[retest]` a GUI re-check folded into the verification session; `[pf]` a first-impression pull-forward candidate (lift into the tag if it slips).

## Coverage ledger

- **158 rows**, all mapped: 157 into the 12 specs, 1 upstream-watch (`qa-gizmo-crash`).
- Heaviest specs: **rigging-and-posing** (27 rows), **ui-help-surfaces** (23), **project-health** (20), **skinning-weight-paint** (19), **schema-expressiveness** (18). Each phases internally by tier.
- Smallest: **storage-split** (1, but architecturally distinct and 1.0.0-gated).

## Verdict rollup (2026-06-11 effort evaluation)

Each spec's STUDY.md now carries a per-item assessment (flow value / test burden / bug surface / underuse risk) and a verdict: **now** (ship in the near-term push), **defer** (real value, sequenced second stage), **gate** (build only when a written trigger fires - the trigger lives in the spec's TODO.md), **drop** (value does not justify the cost - proposed for pruning from the backlog files). Counts are assessed lines (a few backlog rows split into halves, e.g. appearance light/heavy, PPU x3), so the total runs slightly above 158.

| Spec | now | defer | gate | drop | Headline |
| --- | --- | --- | --- | --- | --- |
| [027 export-correctness](027-export-correctness/STUDY.md) | 5 | 0 | 0 | 0 | All five output-integrity bugs ship now. |
| [028 schema-expressiveness](028-schema-expressiveness/STUDY.md) | 5 | 2 | 11 | 1 | Light appearance + half-built completions now; the Spine-parity expressiveness wave gates behind real triggers. |
| [029 mesh-authoring](029-mesh-authoring/STUDY.md) | 7 | 0 | 1 | 1 | Extend/cut fix + panel polish now; manual hull gates; rigid-bind drops (native bone-parenting covers it). |
| [030 skinning-weight-paint](030-skinning-weight-paint/STUDY.md) | 12 | 0 | 1 | 6 | Bind bugfixes + panel polish + PSD-reimport protection now; the aspirational tool-survey cluster mostly drops. |
| [031 rigging-and-posing](031-rigging-and-posing/STUDY.md) | 8 | 0 | 9 | 10 | Flagship driver + IK export-protection now; the Quick-Armature precision cluster drops (Edit Mode is its precision tier). |
| [032 slot-attachments](032-slot-attachments/STUDY.md) | 5 | 1 | 1 | 0 | Placement fix + keyframe button now; skins gate on a real two-variant character. |
| [033 atlas-packing](033-atlas-packing/STUDY.md) | 9 | 1 | 3 | 3 | PPU roundtrip + atlas hygiene now; per-asset PPU gates; density tuning drops. |
| [034 photoshop-plugin](034-photoshop-plugin/STUDY.md) | 2 | 0 | 6 | 3 | tag-form-clear bug now; new tags gate or drop (no consuming runtime). |
| [035 project-health](035-project-health/STUDY.md) | 6 | 0 | 9 | 5 | Five cheap high-value gates + the mixed fixture now; coverage-polish and the Godot matrix drop. |
| [036 ui-help-surfaces](036-ui-help-surfaces/STUDY.md) | 14 | 1 | 5 | 3 | Blocking help-orphan + one batched polish PR now; all three new surfaces drop or gate. |
| [037 storage-split](037-storage-split/STUDY.md) | 0 | 0 | 1 | 0 | Gates on the migration-path enabler + the 1.0.0 window; blocks 1.0.0, not the first tag. |
| [038 reach](038-reach/STUDY.md) | 0 | 0 | 2 | 1 | A fence, correctly placed: Krita/GDExtension gate on demand; GIMP drops. |
| **Total** | **73** | **5** | **49** | **33** | ~51% of assessed items are not scheduled work (gate + drop). |

The near-term scope is the **now** column. The **drop** column (33 items) is a pruning proposal - rows to delete from the backlog files, pending owner approval. Every **gate** has a concrete trigger; none proceeds on imagination.

## Root-cause collapses (one spec, several rows close together)

- **slot placement** - the two Create-Slot rows are one matrix fix (confirmed in slot-attachments).
- **curve rebuild** - CLOSED as two distinct bugs: the brush-preset throw mutates a live bpy `CurveMapPoints` collection; the automesh extend/cut failure is bpy-free polyline splice surgery (`core/automesh/outer_splice.py`) failing silently. No shared code.
- **PPU** - one concept across Blender / atlas / Photoshop, owned by atlas-packing.
- **IK** - five rows are one constraint system inside rigging-and-posing.
- **constraints** - bone-physics + path + transform share one geometry shape inside schema-expressiveness.

---

## 027 - export-correctness

The `.proscenio` is never silently wrong. Writer + validator output integrity.
Surface: `writer/`, `scene_discovery.py`, `validation/`, roundtrip fixtures.

- `[blocking]` writer-ignores-picker - reads `armatures[0]`, never the picker.
- `[blocking]` multi-polygon-truncation - mesh cut to first polygon, no warning (promoted from Defer).
- `[blocking]` validator slot-no-parent-bone false positive.
- `[blocking]` validator-pg-only - `slot_default` read PG-only, CP edits unvalidated.
- `[blocking] [retest]` validator slot-transform-keys - check predates the logged failure.

## 028 - schema-expressiveness

What lets the format carry real game art. Schema v2 fields + writer emission + Godot importer/builders.
Surface: `proscenio.py` models, `writer/`, `importer.gd`, builders, `migrations/`.

- `[blocking]` sprite-appearance (light: modulate / z_index / flip) - day-one value-pull; additive optional fields, no migration.
- `[w1]` sprite-appearance (heavy: mask / blend_mode) - needs a Godot masking strategy.
- `[w1]` finish the half-built tracks: sprite-frame-export-path, visibility-track-both-sides (ship as lies today).
- `[w1]` animation fidelity: bezier-curve-preservation, per-key-interp-mixing, animation-event-tracks, texture-region-track.
- `[w1]` multi-atlas-pages (schema array), sprite-pivot-offset (writer-side compute), nla-strips-to-actions.
- `[w1]` constraint-export: bone-physics, path-constraint, transform-constraint (one geometry shape).
- `[w1]` rig-orientation-detection, auto-detect-2d-vs-3d.
- `[w1]` format-migration-path - the enabler gating every breaking schema bump (storage-split, renames).
- `[w4]` Godot importer polish: node-name-collision-polish, sprite2d-region-filter-clip.

## 029 - mesh-authoring

Mesh authoring: the interactive modal and the generation panel.
Surface: `automesh_authoring.py`, `authoring_pipeline.py`, `scene_props.py`, `mesh_generation.py`.

- `[blocking]` automesh-interactive-extend-cut - Stage 2 pen tools dead/artifacting (root-cause cross-check with skinning-weight-paint).
- `[w4] [pf]` mesh-resolution-rename, density-follows-bones-default-off, preserve-weights-readout, element-type-gating.
- `[w4]` interior-spacing-grouping, automesh-modal-copy, sprite-rigid-single-bone-bind, manual-hull-pen-tool.

## 030 - skinning-weight-paint

The whole weight-paint domain: bind correctness, panel UX, advanced tools.
Surface: `weight_paint.py`, `bind_apply.py`, brush code.

- `[blocking]` brush-curve-presets-error, per-bone-overrides-inert-bone-heat (root-cause cross-check with mesh-authoring).
- `[w4] [pf]` weight-transfer-max-distance-panel.
- `[w4]` weight-transfer-no-coverage-warning, bind-shows-target-armature, flat-mesh-weight-display, clear-per-bone-override, bind-button-after-overrides, sidecar-import-live-apply, snapshot-sidecar-naming.
- `[w4]` advanced (sequence by demand): weight-preserving-psd-reimport, soft-hard-runtime-toggle, bone-strength-region-painting, live-pose-preview, auto-patch-joint-cover, cubism-glue-seam-bind, smart-bone-corrective-drivers, mirror-humanoid-binding, bezier-brush-stroke.

## 031 - rigging-and-posing

Rig authoring and animation setup: bone creation, skeleton management, drivers, IK, poses. Heaviest spec - phases hard by tier.
Surface: `quick_armature.py`, `skeleton.py`, `selection.py`, `_draw_driver_shortcut.py`, `authoring_ik.py`, `pose_library.py`.

- `[retest]` skeleton-row-click-select, pose-save-library-precheck.
- `[w4] [pf]` skeleton-armature-picker name (pairs with export-correctness picker fix).
- `[w4]` quick-armature: preview-clamp-color, rotation-mode, pick-parent-viewport, chain-naming-suffixes, mirror-suffix, numeric-length, local-axis-lock, defaults-help-topic, headless-undo-axis-tests.
- `[w4]` skeleton: inline-rename, bone-collections, hierarchy-editing.
- `[w4]` drive-from-bone: expression-two-ranges, driver-readout-inspect-reset, sticky-panel, drive-slot-from-bone.
- `[w4]` ik-workflow (one constraint system): ik-round-trip, ik-toggle-no-target, ik-bake-gate, ik-fk-switch, ik-chain-helper.
- `[w4]` pose-library: apply-to-selection, auto-categorise, thumbnails.

## 032 - slot-attachments

The slot / attachment system: placement, panel, skins.
Surface: `slot/create.py`, `panels/slots.py`, `operators/slot/`.

- `[blocking]` create-slot-parented-seed + create-slot-origin-unapplied (one matrix fix closes both).
- `[w4]` slots-native-uilist, path-a-b-affordance, slot-no-bone-warning, keyframe-active-attachment, skin-coordination.

## 033 - atlas-packing

Atlas authoring, packing heuristics, and PPU through the pipeline.
Surface: `panels/atlas.py`, `atlas_packer.py`, `pack.py`, PPU plumbing.

- `[w1]` ppu-end-to-end: per-asset-ppu, ppu-visibility, ppu-roundtrip (one concept, three tools).
- `[w4]` unpack-material-rename (partial bug), packing-controls, discovered-vs-packed-label, per-object-pack-state, document-material-identity, atlas-region-helper, exclude-from-atlas, validate-spriteframe-uv, export-bundle, maxrects-heuristics, shrink-start-size.

## 034 - photoshop-plugin

The PS-side tag system and export roundtrip.
Surface: `tag-parser.ts`, `planner.ts`, `manifest.ts`.

- `[retest]` waist-1px-drift (re-measure through UXP).
- `[w4]` tag system: tag-form-clear (bug), nested-merge-warning, name-pattern-rewrite, kind-mesh-vs-polygon, slice-9slice-tag, head-turner-groups, pseudo-keyword-tagging, isolated-flag.
- `[w4]` roundtrip: stable-layer-identity, spectrum-shadow-dom.

## 035 - project-health

The toolchain that protects every other spec, plus cutting the tag.
Surface: `ci.yml`, `pyproject` mypy, coverage config, `packages/fixtures`, `release.yml`, `.github/`, `scripts/`.

- `[blocking]` release-photoshop-stale - `release.yml` still `cp`s the retired `.jsx`; repackage UXP `dist/`.
- `[w2]` CI: blender-multi-version-matrix, ci-matrix-expansion, blender-43-legacy-actions, godot-editor-reimport-test, plugin-uninstall-warning.
- `[w2]` lint / type: eslint-not-in-ci, models-codegen-no-mypy, mypy-ignore-errors-subtrees, bpy-stubs-override-sweep.
- `[w2]` coverage: run-coverage-ci, drop-bpy-coverage-exclusions, edge-polish-pure-modules.
- `[w2]` fixtures: mixed-feature-fixture, flat-fixture-buckets, simple-psd-slot-cycle-abs-paths (portability bug), origin-pivot-fixture, doll-oracle-v2.
- `[w4]` repo: issue-pr-templates, install-dev-script.

## 036 - ui-help-surfaces

Editor UI not tied to a single tool domain: help/docs, small panel polish, and the new panels.
Surface: `panels/*`, help system, `docs/`, `outliner.py`, `object_props.py`, `uv_authoring.py`.

- `[blocking]` sprite-frame-preview-help-orphan - `draw_subbox_header` regressed to zero callers.
- `[w4]` active-sprite: reproject-uv-orientation (replace `smart_project`; perf retest), header-mesh-name, clamp-initial-frame, rename-initial-frame, centered-vs-origin-help.
- `[w4] [pf]` outliner left-align-names, validation frame-unhide-on-click.
- `[w4]` outliner indented-tree; validation validator-element-rename.
- `[w4]` help/docs: see-also-clickable, help-panel-popup-button, merge-diagnostics-help, i18n-locale-tables, see-also-online-urls, addon-docs-screenshots, docs-url-preference, guide-doc-rename-sweep.
- `[w4]` cross-panel: panel-helper-consolidation, subpanel-drag-reorder (subpanel half upstream-limited).
- `[w4]` new surfaces: materials-panel, onion-skin-overlay, joystick-slider-blend.

## 037 - storage-split

Collapse the dual-fallback PG-vs-CP storage by intent. Architecturally distinct, 1.0.0-gated, breaking.
Surface: `mirror.py`, `hydrate.py`, writer `read_field`.

- `[w3]` pg-cp-storage-split - lands behind the schema-expressiveness migration path; blocks 1.0.0, not the first tag.

## 038 - reach

New surfaces with the lowest gain-per-effort right now.
Surface: new `apps/`.

- `[w5]` krita-exporter (Phase 2), gimp-exporter, gdextension-escape-hatch (gated on triggers).

---

## Verification session (not a spec)

One GUI pass closes the `[retest]` rows above (skeleton-row-click, pose-save-precheck, validator slot-transform-keys, waist-1px-drift, reproject-uv perf) plus the cross-app roundtrip bar: doll PS->Blender->Godot end to end, `slot_swap`, `slot_cycle`. Known waivers re-measured here: waist 1px, PPU=100.

## Upstream-watch (no spec)

- qa-gizmo-crash - Blender/AMD internals; defensive try/except shipped; watch only.
