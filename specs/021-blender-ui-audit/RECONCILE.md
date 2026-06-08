# Phase A - reconciliation

Every standing UX item tagged against current code + shipped specs. Source items are [`../backlog-ui-feedback.md`](../backlog-ui-feedback.md) (polish) and the UI-relevant entries in [`../backlog-bugs-found.md`](../backlog-bugs-found.md) (behavior). Status legend in [`STUDY.md`](STUDY.md#legend): FEITO / REAL / MUDOU / OBSOLETO / VERIFICAR.

Areas follow the source file's own section order. `src` is the line in `backlog-ui-feedback.md` unless prefixed `bugs:` (then it is `backlog-bugs-found.md`).

## Cross-panel / general

| src | Item | Status | Evidence / residual |
| --- | --- | --- | --- |
| 12 | Drag-and-drop reorder of subpanels | VERIFICAR | No panel sets `bl_order`; child panels render in registration order ([`panels/__init__.py:68-78`](../../apps/blender/panels/__init__.py#L68-L78)). Open: does Blender 5.1 already let the user drag-reorder `bl_parent_id` subpanels natively? If yes -> OBSOLETO; if no -> Bucket A needs `bl_order` plumbing. Settle in the Phase B in-editor session. |
| 13 | Everything nests under "Pipeline v0.1.0" | REAL | Confirmed. `PROSCENIO_PT_main` draws the version label ([`panels/__init__.py:52-59`](../../apps/blender/panels/__init__.py#L52-L59)) and every subpanel sets `bl_parent_id="PROSCENIO_PT_main"` (e.g. [`active_element.py:46`](../../apps/blender/panels/active_element.py#L46)), so all tools visually indent under the version banner. A root `?` help button now sits beside it (partial mitigation), but the proposed fix (move the version to a footer / Help panel) is not done. Bucket A. |
| 14 | "sprite" nomenclature overloaded | FEITO | Closed by spec 019 across all apps. Enum `ELEMENT_TYPE_ITEMS` kinds `mesh`/`sprite` ([`object_props.py:26-34`](../../apps/blender/properties/object_props.py#L26-L34)); models `MeshElement`/`SpriteElement` + `elements[]` ([`proscenio.py:73,119,277`](../../packages/models/src/proscenio_models/proscenio.py#L73)); Godot `mesh_builder.gd`/`sprite_builder.gd`; PS `kind: "mesh" \| "sprite"` ([`tag-parser.ts:28`](../../apps/photoshop/src/lib/tag-parser.ts#L28)). The shipped names differ from this item's proposal (`element_type` + Godot-anchored `mesh`/`sprite`, not `mesh_type`/`cutout_mesh`), but the overload is resolved. The item's TODO checklist boxes in spec 019 were never ticked despite the code shipping - housekeeping only. |

General rule item "all lists left-align" (src 91) is filed under its origin area (Outliner) below.

## Pending Phase A (not yet reconciled)

Areas remaining from the source files, to reconcile next in this same format:

- Active Sprite (now Active Element) - src 16-37
- Active Slot - src 39-48
- Skeleton - src 50-61
- Toggle IK / IK workflow - src 63-72
- Quick Armature - src 74-85 (cross-check against PR #50 ship - much may be FEITO)
- Outliner (incl. the left-align rule) - src 87-91
- Animation - src 93-95
- Atlas - src 97-124
- Materials panel (proposed) - src 126-143
- Pipeline cross-tool / PPU - src 145-155 (Bucket B candidates)
- Validation - src 157-160
- Export - src 162-164
- Help / status badges - src 166-175
- Diagnostics - src 177-179
- UI-relevant behavior bugs - `backlog-bugs-found.md` (selectors that do not drive the viewport, validator false positives/noise, orphan help topic, edit-mode poll guards)
- Skinning panel - no source items; assessed fresh in Phase B (per STUDY Q2)
