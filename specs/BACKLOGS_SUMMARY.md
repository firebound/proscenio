# Backlogs summary

One-line index of every backlog item, grouped by plugin and area. Each line is a short descriptor (<=10 words); the canonical detail lives in the `specs/backlog-*` files. Tags: `(bug)` reproducible defect, `(ui)` polish/copy/layout, `(quality)` toolchain/typing, otherwise a feature. Blocking items for the first release are called out in [`specs/PLAN.md`](PLAN.md). Blender-6-gated work is excluded (see `specs/backlog-blender-6.md`).

## Blender Addon

### Writer / exporter

- (bug) Reads rotation_euler[2] but bones keyframe [1]; dead tracks.
- (bug) Drops bone-local Z for horizontal bones.
- (bug) Identity matrix for hidden meshes; attachments at origin.
- Multi-polygon mesh truncated to first polygon only.
- General rig-orientation detection (XZ vs XY plane).
- Auto-detect 2D rig vs 3D mesh.
- Blender 4.3 legacy-actions fcurves compatibility, untested.

### Format / schema

- Bezier curve handles not transmitted to Godot.
- Multiple atlases per character (atlas_pages array).
- Animation events / method tracks (audio, particles).
- Per-key interpolation mixing in one track.
- Format detection + v1-to-v2 migration path.
- Bone physics joint-chain export (cape, hair).
- Path-constraint export (PathFollow2D).
- Continuous UV animation (texture_region track).
- sprite_frame track: Blender export path missing.
- visibility track: implement both sides or retire.
- Sprite appearance: modulate / z_index / flip / blend_mode passthrough.
- Sprite pivot / Sprite2D.offset from Blender origin.
- IK constraints round-trip Blender to Godot.
- NLA strips flattened to baked Actions.
- Storage split PG-vs-CP by intent (target 1.0.0).

### Active Sprite panel

- (ui) Show selected mesh name in header.
- (ui) Make sub-blocks individually collapsible accordion.
- (ui) Clamp Initial frame to [0, hframes*vframes-1].
- (ui) Rename "Initial frame" to "Frame".
- (ui) Clarify centered-vs-origin distinction in help.

### Drive from Bone

- (bug) LOCAL_SPACE returns 0 for world-Z rotation.
- (bug) Residual seed keyframes clamp driver output.
- (bug) F9 target switch adds driver, not migrate.
- (ui) Replace raw expression with two editable ranges.
- (ui) Inline driver-value readout + Inspect/Reset buttons.
- (ui) Sticky/pinned panel while editing pose bone.
- Drive slot attachment from a bone.

### Active Slot / Slots panel

- (bug) PG<->CP mirror not firing for slot fields.
- (bug) Create-slot Empty misplaced when seed has parent.
- (bug) Create-slot Empty misplaced when origin unapplied.
- (ui) Standardize slots list to native UIList.
- (ui) Clarify Path A vs Path B affordance.
- (ui) Warn when slot has no parent bone.
- (ui) Keyframe-active-attachment authoring button.

### Mesh Generation panel

- (bug) Automesh Interactive extend/cut broken or artifacts.
- (ui) Rename deceptive "Mesh resolution" field.
- (ui) Default "Density follows bones" OFF.
- (ui) Group "Interior spacing" with other numeric values.
- (ui) Surface "preserve weights on regen" where regen runs.
- (ui) Rename "Automesh (modal)" to action-oriented copy.
- Element-type gating: warn on sprite, validate quad.
- Sprite rigid single-bone bind (weight-paint is mesh-only).

### Weight Paint panel

- (bug) Brush-curve presets throw on click.
- (bug) Per-bone Soft/Hard inert under Bone Heat default.
- (bug) Weight Transfer: no warning when targets out-of-range.
- (ui) Bind subpanel does not show target armature.
- (ui) Flat-mesh weight display hides texture.
- (ui) Cannot clear a per-bone override.
- (ui) Reorder Bind button after overrides box.
- (ui) Sidecar Import does not apply to live weights.
- (ui) Unify "Snapshot" + "Sidecar IO" naming.
- (ui) Surface Weight Transfer max_distance in panel.
- Weight-preserving PSD re-import (snapshot around manifest reimport).
- Soft/Hard runtime per-bone toggle (Adobe Animate lift).
- Bone strength region painting (Moho lift).
- Multi-mesh batch bind.
- Weight transfer between sprites operator.
- Live pose-mode preview in weight paint.
- Sidecar import/export to file.
- Brush curve presets dropdown.
- Auto-Patch joint cover at articulations.
- Cubism Glue seam-bind equivalent.
- Smart-Bone corrective drivers.
- Mirror humanoid binding.
- Bezier brush stroke for alpha-boundary trace.

### Skeleton panel

- (bug) Row click does not select bone in viewport.
- (ui) Remove useless "length" field.
- (ui) Show indented hierarchy instead of parent string.
- (ui) Inline bone rename.
- (ui) Name which armature the writer uses; selector.
- Bone-collections management from the panel.
- Richer bone-hierarchy editing (beyond read-only readout).

### Quick Armature

- (bug) Bones always created on Z=0 plane.
- (bug) Empty QuickRig not removed on cancel (legacy).
- (ui) No preview line during drag (first-cut polish residual).
- (ui) Clamp/color preview line under panel overlays.
- Rotation-mode choice (Euler-Y vs quaternion) + safe swap.
- Pick-parent-in-viewport during modal.
- Chain-aware bone naming suffixes.
- Mirror auto-suffix _L/_R with X-Mirror.
- Numeric length input (Tab to type).
- Local-axis lock (press axis twice).
- Help topic for quick_armature_defaults.
- Headless undo / axis-lock interaction tests.

### Atlas panel

- (bug) Apply not idempotent; UVs shrink each click.
- (bug) Apply silently skips/wipes UVs in Edit Mode.
- (bug) Material rename breaks Unpack restoration silently.
- (ui) Add packing controls (strip whitespace, edge padding, rotation).
- (ui) Show PPU through the pipeline.
- (ui) Clarify discovered-source vs packed atlas label.
- (ui) Per-object pack/unpack state visibility.
- (ui) Document material-identity-by-name limitation.
- Atlas region authoring helper (snap UV by name).
- Exclude sprites from shared atlas pack.
- Validate sprite_frame UV covers full sheet.
- Export bundle: gather .proscenio + textures into folder.
- MaxRects: try multiple heuristics for density.
- Shrink-to-fit / configurable start_size.

### Outliner panel

- (bug) Native UIList filter field does not filter.
- (ui) Indented tree (armature > slots > attachments).
- (ui) Left-align mesh names.

### Validation panel

- (bug) Does not detect transform keys on slot attachments.
- (bug) Flags slot attachments as "no parent bone" (false positive).
- (bug) Reads PG only, ignores raw Custom-Property edits.
- (ui) Move/duplicate Validate button into Validation panel.
- (ui) Frame + unhide offending object on issue click.

### Animation panel

- (bug) Row click does not assign action to armature.

### IK workflow

- (ui) Toggle IK creates constraint without target.
- (ui) No bake-action gate before export.
- IK/FK runtime switch (Rigify-style).
- IK chain helper (one-click constraint stack).

### Help / status badges

- (bug) sprite_frame_preview help topic orphan (no UI entry).
- (ui) Subpanels reuse parent help topic; add per-tool.
- (ui) See-also refs not clickable.
- (ui) Replace Help panel with single popup button.
- (ui) Add GitHub link + version in Help.
- (ui) Merge Diagnostics into Help panel.
- i18n: populate per-locale translation tables.
- Migrate inline see-also refs to online URLs.
- Expand addon reference pages with screenshots.
- Docs-URL as a preference (when second target appears).

### Pose library

- (bug) Save Pose fails without writable asset library; no guidance.
- One-click apply-pose-to-selection.
- Auto-categorise poses by armature name.
- Pose-asset thumbnails via Proscenio preview camera.

### Other / proposed

- Camera orthographic preview helper.
- Onion-skin overlay for animators.
- Joystick / slider multi-pose blend widget.
- Materials panel (interpolation, blend-mode, bulk path fix).
- Validator internal naming sprites-vs-elements rename.
- Panel-helper consolidation (cross-module dupes).

## Photoshop Plugin

### Tags panel / tag system

- (bug) Advanced-fields form cannot clear a set tag.
- Nested [merge] collapses silently (revisit with warning).
- [name:pre*suf] parsed but planner does not rewrite.
- kind:"mesh" equals "polygon" downstream until mesh-deformation ships.
- [slice] Cocos-style 9-slice tag.
- Head-turner view groups (Character Animator).
- Pseudo-keyword auto-tagging (Head, Mouth, Eye).
- [isolated] warp-independent flag.

### Exporter / roundtrip

- (bug) PPU not round-tripped; defaults to 100 (waived).
- (bug) waist height drifts -1px on PS round-trip.
- Stable layer identity in PngWrite.layerPath (dup names).
- JSX-to-UXP png-writer findLayerByPath (shipped).
- Doll-roundtrip oracle re-run against schema v2.
- Dedicated origin/pivot fixture.
- Spectrum web-component shadow-DOM init cost.
- Migrate flat fixtures into psd_to_blender/blender_to_godot buckets.

### Other DCC exporters

- JSX exporter port from coa_tools2.
- Krita exporter (Phase 2).
- GIMP exporter (lower priority).

## Godot Plugin

### Importer / builders

- (bug) Animations import dead tracks (writer rotation-axis bug).
- (bug) Slot attachments render at origin (writer matrix bug).
- Node-name collision polish (Bone2D vs Polygon2D).
- Plugin-uninstall warning UI / CI guard.
- project.godot warning tuning for JSON boundary.
- Annotate :Variant on JSON-boundary lookups.
- Sprite2D region_filter_clip for packed sprite_frame.

## Cross-cutting

### Tests / CI

- Wire run_coverage.py + combine into CI.
- Drop bpy-bound coverage exclusions when units comprehensive.
- Edge-polish ~8 pure modules at 89-93%.
- Blender headless multi-version matrix (4.2 LTS + latest).
- Godot full editor-reimport test (plugin-disabled assertion).
- Godot/Blender CI matrix expansion.
- End-to-end mixed-feature fixture (atlas+sprite_frame+slots+drive).

### Code quality

- (quality) ESLint never runs in CI or pre-commit.
- (quality) packages/models + packages/codegen have no mypy gate.
- (quality) mypy ignore_errors exempts large bpy-bound subtrees.
- bpy stubs via fake-bpy-module / bpy-stubgen.
- Docusaurus wiring of generated schema docs.

### Repo / packaging

- LICENSE full GPL-3.0 body.
- Release workflow Photoshop job stale (.jsx -> UXP dist).
- Issue + PR templates.
- scripts/install-dev.ps1 to automate dev junctions.

### Architecture revisits (not slated)

- GDExtension / C# escape hatch (documented, gated on triggers).
