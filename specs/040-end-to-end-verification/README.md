# Spec 040: End-to-end verification - dashboard

Roll-up of the manual-test surface. See [STUDY.md](STUDY.md) for the format and method,
[TODO.md](TODO.md) for the build / maintenance plan. Walk this before every release tag.

Inventory pass landed 2026-06-13: **452 items** across the three apps + cross-app flows,
**176 audit findings** (10 high-severity). Every item starts `pending` - the human walk
fills in Status.

## Coverage

| Surface | Checklist | Items | Pass | Fail | Blocked | n/a | Pending | Findings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Blender addon | [checklist/blender.md](checklist/blender.md) | 285 | 0 | 0 | 0 | 0 | 285 | 116 |
| Photoshop plugin | [checklist/photoshop.md](checklist/photoshop.md) | 91 | 0 | 0 | 0 | 0 | 91 | 40 |
| Godot plugin | [checklist/godot.md](checklist/godot.md) | 64 | 0 | 0 | 0 | 0 | 64 | 20 |
| Cross-app flows | [checklist/flows.md](checklist/flows.md) | 12 | 0 | 0 | 0 | 0 | 12 | 0 |
| **Total** | | **452** | **0** | **0** | **0** | **0** | **452** | **176** |

_Update the counts as items are walked. A `fail` is a release blocker - move it to the
roster below and file a row in [backlog-bugs-found.md](../backlog-bugs-found.md)._

## Failing / blocked roster

Items at `fail`, `regressed`, or `blocked` - the release blockers. Each cites its repro and
the [backlog-bugs-found.md](../backlog-bugs-found.md) row it promoted to.

None walked yet - all items pending.

## High-severity findings (audit, code-read)

Surfaced by the inventory pass against documented intent. These are code-analysis findings,
not yet manually reproduced (except the Photoshop export blocker, which a user hit live).
Full per-file Findings tables live at the bottom of each checklist.

| # | App | Type | Finding | Code |
| --- | --- | --- | --- | --- |
| 1 | PS | suspected-bug | **Manifest export dies whole if one layer fails** - `writeLayerPng` has no try/catch, so any UXP rejection rejects the modal and the manifest is never written. **The reported blocker.** -> filed in [backlog-bugs-found.md](../backlog-bugs-found.md). | png-writer.ts:29-77; export-flow.ts:118-155 |
| 2 | PS | suspected-bug | **All-or-nothing atomicity gate** - manifest written only if every PNG ok; a layer renamed/reordered after preview (byte-exact name match) suppresses the manifest for the whole doc. | export-flow.ts:120-137; _layer-find.ts:22-31 |
| 3 | PS | suspected-bug | `[spritesheet]` group + kind dropdown - any kind edit rewrites the group to `[sprite]`, silently losing the frames semantics; dropdown not disabled for groups. | tag-writer.ts:73-80; tag-parser.ts:117-119 |
| 4 | PS | suspected-bug | `findLayerByPath` first-match - two siblings with identical names route every select/edit to the first; the duplicate is silently mis-edited. | _layer-find.ts:22-24 |
| 5 | GD | unimplemented | `reimporter.gd` is an empty stub - its header (and the "non-destructive reimport" doc) promises a diff/merge that does not exist. | reimporter.gd:1-10 |
| 6 | GD | suspected-bug | Mesh polygon point parse reads `p[0]/p[1]` with no length guard - a short point aborts the whole import. | mesh_builder.gd:60-61 |
| 7 | GD | suspected-bug | Mesh UV parse reads `u[0]/u[1]` unguarded - a malformed uv crashes the import (sprite offset has the guard, mesh does not). | mesh_builder.gd:83-84 |
| 8 | BL | suspected-bug | **Pixels-per-unit panel field ignored by the first Export** - `PROSCENIO_OT_export_godot` uses its own ExportHelper default (100), not the scene/panel value; only Re-export reads the scene value. | export_flow.py:158-167; pipeline.py:89 |
| 9 | BL | drift | Outliner favorite does NOT reorder to the top - doc + property description say it pins to the top, but `filter_items` sorts purely by (category, name). | outliner.py:120; object_props.py:253 |
| 10 | BL | drift | Validation doc lists 4 checks; the validator emits many more (bone orientation, IK-bake, non-flat mesh, sprite-UV, duplicate slot, vertex-group resolution). Doc badly out of date. | core/validation/export.py:42-76 |

The remaining 166 findings (medium / low: drift, undocumented, unimplemented, dead) live in
each checklist's Findings table. Doc-coverage gaps (undocumented controls) dominate the
Photoshop tail - the plugin's Tags / Validate / Debug panels are largely undocumented.
