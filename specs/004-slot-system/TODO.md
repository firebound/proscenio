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
- [x] D13 — sprite_frame preview shader (Material Preview mode) bundled with Wave 4.1.
- [x] D14 — slots are kind-agnostic; polygon + sprite_frame children compose under the same slot machinery.

## Wave 4.1 — writer + authoring panel + preview shader (Blender side)

Branch: `feat/spec-004.1-slots-blender`.

**Slot system core** (D1–D12 + D14):

- [ ] `properties/__init__.py` gains `is_slot: BoolProperty` + `slot_default: StringProperty` on `ProscenioObjectProps`.
- [ ] `operators/__init__.py` gains `PROSCENIO_OT_create_slot` (D8 two-path: bare creation under active bone, or wrap N selected meshes in a fresh Empty).
- [ ] Active Sprite subpanel renders a Slots section when `active_object.type == "EMPTY"` and `is_slot == True`: list of attachment children, default picker, "Add attachment" button (parents the active mesh into the slot Empty), reorder buttons (D12 z-order). Children kind-mixed (polygon + sprite_frame) -- D14.
- [ ] Writer (`exporters/godot/writer.py`) walks scene Empties, emits `slots[]` array. Each slot's `bone` = Empty's `parent_bone`; `attachments` = ordered child mesh names (per D12); `default` = `slot_default` or first child. Sprites continue to emit normally in `sprites[]` regardless of slot membership (D6).
- [ ] Validation rules per D9 + D10 — surfaced in Validation subpanel via existing `Issue` + click-to-select.
- [ ] `core/feature_status.py` flips `slot_system` from `PLANNED` to `GODOT_READY`.
- [ ] `core/help_topics.py` adds a `slot_system` topic (what slots do, how to author, how Godot consumes them, contrast with driver shortcut, the two PS-import flows that compose under one slot per D14).
- [ ] Tests: writer round-trip on a hand-built slot fixture (`tests/test_slot_writer.py`) covering polygon-only, sprite_frame-only, and mixed-kind slots; validation rules (`tests/test_slot_validation.py`).

**Sprite_frame preview shader** (D13):

- [ ] `core/sprite_frame_shader.py` -- pure Python helper that builds a reusable shader-node group ("Proscenio Sprite Frame Slicer") with input sockets `Frame`, `H Frames`, `V Frames` and a wired `Image Texture` lookup. Math: `cell_w = 1/hframes`, `cell_x = frame % hframes`, etc. The group is parametrized so the same node tree can serve every sprite_frame mesh in the scene.
- [ ] `PROSCENIO_OT_setup_sprite_frame_preview` operator -- inserts the slicer between `TexCoord` and `TexImage` of the active mesh's first image-textured material; wires drivers from `obj.proscenio.frame / hframes / vframes` onto the matching shader inputs. Idempotent: re-runs detect an existing slicer and refresh drivers.
- [ ] `PROSCENIO_OT_remove_sprite_frame_preview` -- bypasses the slicer (keeps the texture wired straight to BSDF), drops the drivers, leaves the node group present so other materials still reference it.
- [ ] Active Sprite subpanel surfaces "Setup Preview Material" / "Remove Preview Material" button when `sprite_type == "sprite_frame"` and a material is linked.
- [ ] `core/help_topics.py` `active_sprite` topic gains a "Material preview (Z-key cycles to Material Preview mode)" caveat sentence.
- [ ] Tests: `tests/test_sprite_frame_shader.py` -- verify the math helpers (`cell_offset_x(frame, hframes)`, etc.) without booting Blender. Shader-node creation itself stays bpy-bound (manual smoke test on doll's eye fixture).

## Wave 4.2 — Godot importer + animation track

Branch: `feat/spec-004.2-slots-godot`.

- [ ] `apps/godot/addons/proscenio/builders/slot_builder.gd` — reads `slots[]` from manifest, builds a `Node2D` per slot under the skeleton, populates with attachment children (delegated back to `polygon_builder.gd` / `sprite_frame_builder.gd`), sets `visible` per default.
- [ ] `polygon_builder.gd` / `sprite_frame_builder.gd` patch: when a sprite name appears in any `slots[].attachments[]`, route it under the slot Node2D instead of the skeleton root.
- [ ] `animation_builder.gd` adds `slot_attachment` track handling: at each key, finds the named child of the slot, sets `visible = true`, hides siblings. Track interpolation = `INTERPOLATION_NEAREST` (constant step).
- [ ] GUT tests: `apps/godot/tests/test_slots.gd` — slot structure (Node2D parent + children), default visibility, animation track flips visibility on the right child, multi-slot scene.

## Wave 4.3 — fixtures + docs (in flight)

Branch: `feat/spec-004.3-slots-fixtures`.

**Drive-bys** (CI broken on main after Wave 4.2 merge):

- [x] `apps/godot/tests/fixtures/slots_demo.proscenio` — add the missing `texture_region` field on each polygon entry (PolygonSprite schema requires it).
- [x] `examples/authored/doll/doll.blend` — re-fix `waist` mesh's vertex group (`waist` -> `spine`); the rename done in Wave 4.1 did not persist into main. Regenerate `doll.expected.proscenio` golden.

**Writer extension** (uncovered while authoring slot_cycle):

- [x] `exporters/godot/writer.py`: `_build_slot_animations` walks slot Empties for `proscenio_slot_index` fcurve keyframes and emits `slot_attachment` tracks (D5: constant interp, target = slot name, `attachment` field per key resolved via the slot's `attachments[]` list). `_merge_slot_animations_into` consolidates per-action so bone-transform + slot-attachment tracks under the same action name share one Animation in Godot.

**slot_cycle fixture (shipped)**:

- [x] `scripts/fixtures/slot_cycle/draw_layers.py` — Pillow renders 3 colored 32x32 squares (red/green/blue) into `pillow_layers/`.
- [x] `scripts/fixtures/slot_cycle/build_blend.py` — bpy assembles 1-bone armature + slot Empty (parent_type=OBJECT to armature, `is_slot=True`, `slot_default="attachment_red"`) + 3 polygon attachments + `cycle` action keyframing `proscenio_slot_index` 0/1/2 across 24 frames. Empty is object-parented (not bone-parented) so the XZ-plane attachments are not rotated by Blender's bone Y-axis alignment -- mirrors the doll fixture's parenting pattern.
- [x] `examples/slot_cycle/slot_cycle.blend` — generated.
- [x] `examples/slot_cycle/slot_cycle.expected.proscenio` — golden (3 sprites + 1 slot + 1 cycle animation with `slot_attachment` track).
- [x] `examples/slot_cycle/godot/SlotCycle.tscn` + `.gd` — wrapper per SPEC 001 with autoplay defaulting to `cycle`.
- [x] `examples/slot_cycle/.gitignore` — ignores `*.actual.proscenio`.
- [x] `examples/slot_cycle/README.md` — fixture overview + slot setup table + build instructions.
- [x] `apps/blender/tests/run_tests.py` auto-discovers it (5/5 fixtures pass).

**Docs**:

- [x] `STATUS.md` — flip SPEC 004 row to shipped + bump fixture count to 5.
- [x] `scripts/fixtures/README.md` — `slot_cycle/` entry in the layout + script-output map.
- [x] Update `examples/authored/doll/README.md` brow row from "future home for slots" to a forward-looking note pointing at `examples/slot_cycle/` for the live slot demo.

## Wave 4.4 — close-out (planned)

Branch: `feat/spec-004.4-close-out`. Bundles the Wave-4.3 deferred items into one final SPEC 004 PR so the spec ships fully closed before SPEC 005 close-out + SPEC 008 design pass.

- [ ] `examples/authored/doll/`: promote `brow.L` and `brow.R` to slots with brow-up / brow-down attachments. Author sibling `brow.L.up` / `brow.R.up` meshes; existing `brow.L` / `brow.R` become the "down" defaults. Weight paint each pair to the same brow bone the doll already exposes. Add a `brow_raise` action keyframing each slot's `proscenio_slot_index` 0 -> 1 -> 0.
- [ ] Re-export `examples/authored/doll/doll.expected.proscenio` golden so it includes the new slots[] + brow_raise animation.
- [ ] `examples/authored/doll/README.md`: brow row updated from "live slot demo coming" to "two slots (`brow.L.swap` / `brow.R.swap`) drive the brow_raise action".
- [ ] `.ai/skills/godot-dev.md`: new "Slots" subsection -- worked example with `Node2D` parent + `visible`-toggled children + `slot_attachment` track expansion. Short (one screen of text + the doll brow scene tree).
- [ ] `format-spec.md` (defer if the doc still does not exist) -- slot section listing the Slot schema shape + the slot_attachment track contract. Cross-references SPEC 004.

## Out of scope

See [STUDY.md](STUDY.md) "Out of scope" for the deferred list (skins, procedural attachments, per-attachment weights, crossfade, live-link).

## Blocked on

Nothing. Schema is ready, SPEC 005 panel infrastructure (PropertyGroup + Validation + status badges + help topics) is mature enough to host the new Slots authoring UI without new framework work.
