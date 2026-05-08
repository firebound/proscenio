# SPEC 004 — TODO

Slot system implementation. See [STUDY.md](STUDY.md) for the full design + decisions D1–D12. Three coarse waves, one PR each — no further sub-division (lesson learned from SPEC 005's 5.1.x.x.x sprawl).

## Decision lock-in

- [x] D1 — slot identity = Empty Object + child meshes + `proscenio.is_slot = True`.
- [x] D2 — default attachment via `proscenio.slot_default: StringProperty` (empty = first child sorted).
- [x] D3 — slot bone = Empty's `parent_bone`; children must share it (validation warning on mismatch).
- [x] D4 — Godot scene shape = `Node2D` parent + `visible`-toggled attachment children.
- [x] D5 — track key shape uses existing `Key.attachment` field; `slot_attachment` track type; `interp = "constant"` default.
- [x] D6 — slot/sprite binding via existing `slots[].attachments[]` list; no new Sprite field.
- [x] D7 — authoring UI lives inside the Active Sprite subpanel when active object is a slot Empty.
- [x] D8 — promote-to-slot via `PROSCENIO_OT_create_slot` operator (two paths: empty selection or N meshes).
- [x] D9 — validation: ≥1 child, shared parent_bone, slot_default exists, name uniqueness.
- [x] D10 — slot child cannot also carry bone_transform keyframes (validation warning).
- [x] D11 — no schema bump (`slots[]` + `slot_attachment` already in `format_version=1`).
- [x] D12 — Godot child z-order follows attachment array order in the manifest.

## Wave 4.1 — writer + authoring panel (Blender side)

Branch: `feat/spec-004.1-slots-blender`.

- [ ] `properties/__init__.py` gains `is_slot: BoolProperty` + `slot_default: StringProperty` on `ProscenioObjectProps`.
- [ ] `operators/__init__.py` gains `PROSCENIO_OT_create_slot` (D8 two-path: bare creation under active bone, or wrap N selected meshes in a fresh Empty).
- [ ] Active Sprite subpanel renders a Slots section when `active_object.type == "EMPTY"` and `is_slot == True`: list of attachment children, default picker, "Add attachment" button (parents the active mesh into the slot Empty).
- [ ] Writer (`exporters/godot/writer.py`) walks scene Empties, emits `slots[]` array. Each slot's `bone` = Empty's `parent_bone`; `attachments` = sorted child mesh names; `default` = `slot_default` or first child.
- [ ] Validation rules per D9 + D10 — surfaced in Validation subpanel via existing `Issue` + click-to-select.
- [ ] `core/feature_status.py` flips `slot_system` from `PLANNED` to `GODOT_READY`.
- [ ] `core/help_topics.py` adds a `slot_system` topic (what slots do, how to author, how Godot consumes them, contrast with driver shortcut).
- [ ] Tests: writer round-trip on a hand-built slot fixture (`tests/test_slot_writer.py`), validation rules (`tests/test_slot_validation.py`).

## Wave 4.2 — Godot importer + animation track

Branch: `feat/spec-004.2-slots-godot`.

- [ ] `godot-plugin/addons/proscenio/builders/slot_builder.gd` — reads `slots[]` from manifest, builds a `Node2D` per slot under the skeleton, populates with attachment children (delegated back to `polygon_builder.gd` / `sprite_frame_builder.gd`), sets `visible` per default.
- [ ] `polygon_builder.gd` / `sprite_frame_builder.gd` patch: when a sprite name appears in any `slots[].attachments[]`, route it under the slot Node2D instead of the skeleton root.
- [ ] `animation_builder.gd` adds `slot_attachment` track handling: at each key, finds the named child of the slot, sets `visible = true`, hides siblings. Track interpolation = `INTERPOLATION_NEAREST` (constant step).
- [ ] GUT tests: `godot-plugin/tests/test_slots.gd` — slot structure (Node2D parent + children), default visibility, animation track flips visibility on the right child, multi-slot scene.

## Wave 4.3 — fixtures + docs

Branch: `feat/spec-004.3-slots-fixtures`.

- [ ] `examples/doll/`: promote `brow.L` and `brow.R` to slots with brow-up/brow-down attachments. Re-author the doll's existing brow meshes as the default attachments; add brow-up sibling meshes as alternates.
- [ ] `examples/slot_cycle/` — minimal new fixture: 1 armature, 1 slot Empty, 3 attachment meshes (red/green/blue squares), 1 action that cycles attachment per keyframe. Mirrors the SPEC 007 fixture layout (drawn via Pillow + assembled via `build_blend.py`).
- [ ] `examples/slot_cycle/godot/SlotCycle.tscn` + `.gd` (wrapper per SPEC 001).
- [ ] `examples/slot_cycle/slot_cycle.expected.proscenio` (golden via `_shared/export_proscenio.py`).
- [ ] `STATUS.md` — flip SPEC 004 row to shipped + bump fixture count to 5.
- [ ] `.ai/skills/godot-plugin-dev.md` — new "Slots" subsection with the wrapper + animation example.
- [ ] `format-spec.md` (if it exists, otherwise schema docstring) — slot section moves from "schema-only" to live behavior.
- [ ] Update `examples/doll/README.md` brow row from "future home for slots" to "demonstrates the slot system".

## Out of scope

See [STUDY.md](STUDY.md) "Out of scope" for the deferred list (skins, procedural attachments, per-attachment weights, crossfade, live-link).

## Blocked on

Nothing. Schema is ready, SPEC 005 panel infrastructure (PropertyGroup + Validation + status badges + help topics) is mature enough to host the new Slots authoring UI without new framework work.
