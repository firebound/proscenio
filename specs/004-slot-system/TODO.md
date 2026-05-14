# SPEC 004 - TODO

Slot system implementation. See [STUDY.md](STUDY.md) for the full design + decisions D1–D12. Three coarse waves, one PR each - no further sub-division (lesson learned from SPEC 005's 5.1.x.x.x sprawl).

## Decision lock-in

- [x] D1 - slot identity = Empty Object + child meshes + `proscenio.is_slot = True`.
- [x] D2 - default attachment via `proscenio.slot_default: StringProperty` (empty = first child sorted).
- [x] D3 - slot bone = Empty's `parent_bone`; children must share it (validation warning on mismatch).
- [x] D4 - Godot scene shape = `Node2D` parent + `visible`-toggled attachment children.
- [x] D5 - track key shape uses existing `Key.attachment` field; `slot_attachment` track type; `interp = "constant"` default.
- [x] D6 - slot/sprite binding via existing `slots[].attachments[]` list; no new Sprite field.
- [x] D7 - authoring UI lives inside the Active Sprite subpanel when active object is a slot Empty.
- [x] D8 - promote-to-slot via `PROSCENIO_OT_create_slot` operator (two paths: empty selection or N meshes).
- [x] D9 - validation: ≥1 child, shared parent_bone, slot_default exists, name uniqueness.
- [x] D10 - slot child cannot also carry bone_transform keyframes (validation warning).
- [x] D11 - no schema bump (`slots[]` + `slot_attachment` already in `format_version=1`).
- [x] D12 - Godot child z-order follows attachment array order in the manifest.
- [x] D13 - sprite_frame preview shader (Material Preview mode) bundled with Wave 4.1.
- [x] D14 - slots are kind-agnostic; polygon + sprite_frame children compose under the same slot machinery.

## Wave 4.1 - writer + authoring panel + preview shader (Blender side)

Branch: `feat/spec-004.1-slots-blender`. **Shipped**.

**Slot system core** (D1-D12 + D14):

- [x] `properties/object_props.py` carries `is_slot: BoolProperty` + `slot_default: StringProperty` on `ProscenioObjectProps`. PR 49 also fixed the PG <-> CP mirror for both fields.
- [x] `operators/slot/create.py` ships `PROSCENIO_OT_create_slot` with the D8 two-path behavior (bare creation under active bone, or wrap N selected meshes in a fresh Empty).
- [x] `panels/active_slot.py` renders the slot authoring section when the active Empty has `is_slot=True`: attachment list, default picker (SOLO_ON/OFF star), "Add Selected Mesh" button. Reorder/z-order surfaces via list order (D12) - PR 49 added the row-click sync helper.
- [x] `exporters/godot/writer/slots.py` walks the scene's Empties and emits `slots[]`. `slot_animations.py` merges per-action so bone-transform + slot-attachment tracks share one Animation in Godot (D6).
- [x] Validation D9 + D10 live in `core/validation/active_slot.py` + the Validation subpanel, surfaced via the `Issue` + click-to-select path.
- [x] `core/feature_status.py` carries `slot_system: GODOT_READY`.
- [x] `core/help_topics.py` carries the `slot_system` topic.
- [x] Tests: `tests/test_slot_emit.py` + `tests/test_slot_validation.py` cover round-trip + validation rules. Headless run via `apps/blender/tests/run_tests.py` exercises `slot_cycle` and `slot_swap` end-to-end (7/7 PASS).

**Sprite_frame preview shader** (D13):

- [x] `core/bpy_helpers/sprite_frame_shader.py` ships the reusable "Proscenio Sprite Frame Slicer" node group with the parametrized `Frame` / `H Frames` / `V Frames` math.
- [x] `operators/slot/preview_shader.py` ships `PROSCENIO_OT_setup_sprite_frame_preview` (idempotent slicer insertion + driver wiring).
- [x] Same module ships `PROSCENIO_OT_remove_sprite_frame_preview` (drops drivers, keeps the node group available).
- [x] `panels/_draw_sprite_frame.py` surfaces "Setup Preview" / "Remove Preview" buttons when `sprite_type == "sprite_frame"`. PR 49 added the `?` help-button affordance to the sub-box header.
- [x] `core/help_topics.py` ships the standalone `sprite_frame_preview` topic with the Z-key Material Preview caveat. (Landed as its own topic rather than nested inside `active_sprite`; same UX outcome.)
- [x] Tests: `tests/test_sprite_frame_math.py` covers the math helpers (`cell_offset_x`, etc.) without booting Blender.

## Wave 4.2 - Godot importer + animation track

Branch: `feat/spec-004.2-slots-godot`. **Shipped**.

- [x] `apps/godot/addons/proscenio/builders/slot_builder.gd` builds the `Node2D` per slot under the skeleton, attaches children via the polygon / sprite_frame builders, and toggles `visible` per default.
- [x] `polygon_builder.gd` + `sprite_frame_builder.gd` route into the slot Node2D when the sprite name appears in any `slots[].attachments[]`.
- [x] `animation_builder.gd` ships `slot_attachment` track handling: NEAREST interp, sibling visibility flip per key.
- [x] GUT coverage: `apps/godot/tests/test_importer.gd` carries the slot-structure + default-visibility + multi-slot assertions (38 slot references). Standalone `test_slots.gd` was not split out - the existing importer suite already exercises every assertion the TODO planned.

## Wave 4.3 - fixtures + docs (in flight)

Branch: `feat/spec-004.3-slots-fixtures`.

**Drive-bys** (CI broken on main after Wave 4.2 merge):

- [x] `apps/godot/tests/fixtures/slots_demo.proscenio` - add the missing `texture_region` field on each polygon entry (PolygonSprite schema requires it).
- [x] `examples/authored/doll/00_blender_base/doll_base.blend` - re-fix `waist` mesh's vertex group (`waist` -> `spine`); the rename done in Wave 4.1 did not persist into main. Regenerate `doll_base.expected.proscenio` golden.

**Writer extension** (uncovered while authoring slot_cycle):

- [x] `exporters/godot/writer.py`: `_build_slot_animations` walks slot Empties for `proscenio_slot_index` fcurve keyframes and emits `slot_attachment` tracks (D5: constant interp, target = slot name, `attachment` field per key resolved via the slot's `attachments[]` list). `_merge_slot_animations_into` consolidates per-action so bone-transform + slot-attachment tracks under the same action name share one Animation in Godot.

**slot_cycle fixture (shipped)**:

- [x] `scripts/fixtures/slot_cycle/draw_layers.py` - Pillow renders 3 colored 32x32 squares (red/green/blue) into `pillow_layers/`.
- [x] `scripts/fixtures/slot_cycle/build_blend.py` - bpy assembles 1-bone armature + slot Empty (parent_type=OBJECT to armature, `is_slot=True`, `slot_default="attachment_red"`) + 3 polygon attachments + `cycle` action keyframing `proscenio_slot_index` 0/1/2 across 24 frames. Empty is object-parented (not bone-parented) so the XZ-plane attachments are not rotated by Blender's bone Y-axis alignment - mirrors the doll fixture's parenting pattern.
- [x] `examples/generated/slot_cycle/slot_cycle.blend` - generated.
- [x] `examples/generated/slot_cycle/slot_cycle.expected.proscenio` - golden (3 sprites + 1 slot + 1 cycle animation with `slot_attachment` track).
- [x] `examples/generated/slot_cycle/godot/SlotCycle.tscn` + `.gd` - wrapper per SPEC 001 with autoplay defaulting to `cycle`.
- [x] `examples/generated/slot_cycle/.gitignore` - ignores `*.actual.proscenio`.
- [x] `examples/generated/slot_cycle/README.md` - fixture overview + slot setup table + build instructions.
- [x] `apps/blender/tests/run_tests.py` auto-discovers it (5/5 fixtures pass).

**Docs**:

- [x] `STATUS.md` - flip SPEC 004 row to shipped + bump fixture count to 5.
- [x] `scripts/fixtures/README.md` - `slot_cycle/` entry in the layout + script-output map.
- [x] Update `examples/authored/doll/README.md` brow row from "future home for slots" to a forward-looking note pointing at `examples/generated/slot_cycle/` for the live slot demo.

## Wave 4.4 - close-out

Branch: `feat/spec-004.4-close-out`. Bundles the Wave-4.3 deferred items into one final SPEC 004 PR. **Shipped** - all live demo coverage migrated to `examples/generated/slot_cycle/` + `examples/generated/slot_swap/` and the docs landed alongside.

- [x] ~~doll brow promotion to slots + `brow_raise` action~~ - **Retired**. Slot demo coverage moved to `examples/generated/slot_cycle/` (3-attachment cycle) and `examples/generated/slot_swap/` (single-slot bone swing). Decision recorded in `examples/authored/doll/README.md` (the brow row now points at both generated fixtures).
- [x] ~~Re-export `doll.expected.proscenio` with slots[] + brow_raise~~ - **Retired** alongside the brow promotion above.
- [x] `examples/authored/doll/README.md` brow row updated to reference `slot_swap` + `slot_cycle` as the live slot demos.
- [x] `.ai/skills/godot-dev.md` ships the "Slots (SPEC 004)" subsection at line 116 with the `Node2D` parent + visibility-toggled children + `slot_attachment` track shape.
- [x] `.ai/skills/format-spec.md` mentions slots in the schema table + interpolation list. A dedicated slot subsection is **deferred** - the field-level rows are enough for the format contract; promote to a full subsection only when a second consumer beyond Godot needs the contract documented in one place.

## Out of scope

See [STUDY.md](STUDY.md) "Out of scope" for the deferred list (skins, procedural attachments, per-attachment weights, crossfade, live-link).

## Blocked on

Nothing. Schema is ready, SPEC 005 panel infrastructure (PropertyGroup + Validation + status badges + help topics) is mature enough to host the new Slots authoring UI without new framework work.
