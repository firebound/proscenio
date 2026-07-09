# Changelog

All notable changes to Proscenio are recorded here. The three apps ship in
lockstep under one product version; per-app detail is grouped under each
release. The format loosely follows Keep a Changelog. Pre-1.0 is
`0.MINOR.PATCH` with a `-beta` suffix on the beta channel; the numeric form
(`0.9.0`) is what the strict Blender and UXP manifest version fields carry,
while the `-beta` channel marker lives on the git tag and this file.

The on-disk `.proscenio` format carries its own integer `format_version`
(currently 2), independent of the product version below.

## [1.0.0] - 2026-07-08

First stable release. The Photoshop → Blender → Godot pipeline graduates from
the beta channel: the three apps ship in lockstep at `1.0.0`, and the on-disk
`.proscenio` format (`format_version` 2) is now considered stable. The beta
window (`0.9.0-beta`, `0.9.1-beta`) collected real `.blend` files and tester
feedback; this release folds in that hardening and drops the pre-1.0 caveats.

### Repository

- The product version now has a single source of truth: the root `VERSION`
  file drives every in-bundle manifest through
  `scripts/maintenance/sync_version.py`, CI fails on drift, and the release
  workflow refuses a tag that disagrees with `VERSION`.

## [0.9.1-beta] - 2026-06-22

Beta bugfix: Blender 4.2 LTS compatibility.

### Blender add-on

- Fixed the "Apply Brush Curve Preset" operator failing to register on Blender
  4.2 (Python 3.11): its enum items were built by a comprehension inside the
  property annotation, which `get_type_hints` cannot resolve on 3.11, so the
  operator silently dropped out of the UI. The full 4.2 LTS headless suite now
  passes (201 operator tests + 8/8 goldens), so the `4.2.0` minimum is
  verified rather than only declared.

## [0.9.0-beta] - 2026-06-21

First public beta. The full pipeline - author in Photoshop, rig and skin in
Blender, import as native Godot scenes - is feature-complete and polished. The
beta window collects real `.blend` files and tester feedback before the 1.0
gate; the one breaking internal change (storage-split) lands during the window
without moving the on-disk format.

### Blender add-on

- Sidebar authoring panel: Pipeline (Import / Validate / Export), Element,
  Skeleton, Slots, Outliner, Animation, Atlas, Helpers, About.
- Rigging and posing: Quick Armature, editable IK chains, drivers, pose
  library; control bones (.IK / .pole) stay out of the Godot export.
- Skinning: weight-paint ergonomics, automesh (alpha trace), Proximity bind,
  named weight snapshots.
- Y Location draw-order authoring: an integer order positions the plane in Y
  and negates straight into the Godot `z_index`.
- Export to the `.proscenio` format behind a validation pass that warns on the
  known authoring mistakes instead of shipping silently wrong output.
- Bundled pydantic / `proscenio_models` wheels; runs on Blender 4.2 LTS and 5.x.

### Photoshop UXP plugin

- Per-layer tag system and tagging UI; export to a PSD manifest plus PNGs.
- Import and re-import resilience: per-entry guards, data-loss guards on the
  filename template and tag fields, and staleness handling across the panels.

### Godot plugin

- One-time editor import of `.proscenio` into native nodes: Skeleton2D,
  Bone2D, Polygon2D, Sprite2D, AnimationPlayer.
- Slot attachments, per-vertex skinning weights, and sprite-frame / transform
  animation tracks.
- Defensive import builders (length-guarded parsing, weight-first bind, scoped
  lookups); wrapper-scene reimport overwrites the generated scene while a user
  wrapper scene with scripts and extras survives.

### Known beta-window work

- `037 storage-split` (consolidate the dual PropertyGroup / Custom-Property
  storage to one canonical home per field) lands during the window; the disk
  format does not move.
- Field-validate the one-shot migrator against real pre-split `.blend` files.
- Re-measure the doll PSD round-trip drift through the UXP png-writer.
- Walk the QA Companion checklist over the changed areas.
