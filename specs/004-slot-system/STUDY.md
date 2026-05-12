# SPEC 004 — Slot system (sprite swap)

Status: **design locked**. Implementation waves below.

## Problem

A "slot" is a named attachment point that presents one of N sprites at a time, switched at runtime: head expressions (normal/angry/dead), equipment swaps (sword/staff/empty), forearm front/back swap when the bone passes a rotation threshold. The driver shortcut shipped in SPEC 005.1.d.1 covers gradual parameter mapping (iris scroll, region nudge) but is the wrong primitive for hard texture swaps -- a `FloatProperty` driven from a bone radian saturates at the clamp and cannot represent N discrete states.

The schema already carries the slot shape:

- `slots: [{name, bone, default, attachments[]}]` on the root document.
- Track type `slot_attachment` with key data `attachment: string` (sprite name).
- Importer + writer ignore both today.

SPEC 004 closes the loop: writer emits, importer realizes, panel authors.

## Reference: similar tools

- **Spine** -- "Slot Attachments" + an `attachment` animation track. Each slot has multiple attachments; animation can swap which one is shown. Industry standard for cutout 2D rigs.
- **DragonBones** -- "Display" list per slot, swapped via animation events.
- **COA Tools** -- `slot_object` operator that bundles sprites into a swappable group; `slot_index` integer is keyframable.
- **Toon Boom Harmony** -- "Drawing Substitution" with explicit swap-table keys.
- **Live2D** -- different paradigm (parameter-driven deformers, not discrete swap); inspirational only.

The shared pattern across the discrete-swap tools: a parent group + N sibling visuals + an animation track that picks which sibling is currently shown. SPEC 004 follows that pattern.

## Decisions locked

| ID | Decision | Choice |
| --- | --- | --- |
| D1 | Slot identity in Blender | **Empty Object as slot anchor + child meshes as attachments.** The Empty carries `proscenio.is_slot = True`. Each direct child mesh is one attachment. Empty over Collection because Empty has world transform + bone parent links, integrates with the armature posing chain cleanly; Collections are organizational only. |
| D2 | Default attachment | **`proscenio.slot_default: StringProperty`** on the Empty, names one of the children. Empty string = first child by sorted name. Writer emits in `slots[].default`. |
| D3 | Slot bone binding | **Empty's `parent_bone` (Blender bone-parenting) becomes `slots[].bone`.** All attachment children must share the same bone parent (validated at export -- mismatch = warning, not error, since users may have legitimate reasons during authoring). |
| D4 | Godot scene shape | **`Node2D` parent + N attachment children (`Polygon2D` / `Sprite2D`); `visible` toggled.** No new node type, no GDExtension. Default attachment starts `visible = true`, others `false`. |
| D5 | Track key shape | **Existing `Key.attachment: string` field, `slot_attachment` track type.** `target` = slot name (not sprite name). `interp` defaults to `constant` (no in-between -- swap is binary). |
| D6 | Slot-attachment binding in `.proscenio` | **Existing `slots[].attachments[]` list of sprite names.** No new field on Sprite. Importer cross-references the slot list to know which sprites belong to which slot. Sprites authored as slot attachments are still emitted in the top-level `sprites[]` array; the slot list adds a grouping layer. |
| D7 | Authoring panel surface | **New "Slots" section in the Active Sprite subpanel when the active object is an Empty with `is_slot = True`.** Lists attachment children, picker for default, "Add attachment" / "Promote to slot" operators. Same subpanel as Active Sprite (no new top-level subpanel) -- slots are object-scoped, not scene-scoped. |
| D8 | "Promote to slot" workflow | **`PROSCENIO_OT_create_slot` operator.** Two paths: (a) with no selection, creates a new Empty parented to the active pose bone, ready to receive children; (b) with N meshes selected, parents them to a new Empty + flags it as a slot. Empty named `<bone>.slot` by default, renameable. |
| D9 | Validation rules | **Slot Empty must have ≥1 child mesh; all children must share `parent_bone` if the Empty has one; `slot_default` must name an existing child (or be empty); slot names unique scene-wide.** Surfaces in the Validation panel via the existing `Issue` machinery. |
| D10 | Slot interaction with bone tracks | **A mesh can be either a slot attachment OR a regular bone-parented sprite, not both.** Validator warns when a slot child carries `bone_transform` keyframes -- the slot toggles `visible`, bone keys still apply but won't propagate visually as the user might expect (only the visible child is seen). Out of scope for v1: per-attachment skeleton wiring (each attachment carrying its own bone targets). |
| D11 | Schema bump | **None.** The `slots[]` array + `slot_attachment` track type were already in `format_version=1`. SPEC 004 adds *behavior*, not schema. Backward compatible: pre-004 `.proscenio` files lacking `slots[]` keep working. |
| D12 | Slot order in the Godot scene | **Z-order follows attachment array order in the manifest.** First attachment is rendered behind, last on top -- matches Blender's outliner top-down ordering after `proscenio.attachment_order` operator (a small reorder helper on the Slots panel). |
| D13 | Sprite_frame preview shader | **Bundle a Material Preview-mode shader graph with Wave 4.1.** A single mesh's spritesheet is sliced live in the viewport using a generated shader-node group: `[TexCoord] -> [Math: cell offset] -> [Image Texture] -> [BSDF]`. Drivers wire `obj.proscenio.frame / hframes / vframes` into the offset Math nodes so the visible cell tracks the panel + animation values without reload. Operator `PROSCENIO_OT_setup_sprite_frame_preview` toggles the slicer on/off per material; idempotent re-runs replace the existing slicer. Out of scope: padding-aware atlases, cycles material, Workbench compatibility (Workbench evaluates only `diffuse_color`, no shader nodes). |
| D14 | Attachment kind agnosticism | **Slots are kind-agnostic.** `slots[].attachments[]` is just `string[]` of mesh names; the kind (`polygon` / `sprite_frame`) lives on each entry of the top-level `sprites[]` array. Importer dispatches per attachment by reading the matching Sprite entry's `kind`. This means a single slot can mix polygon (weight-painted) + sprite_frame (texture-sliced) children freely -- e.g. an eye slot with two polygon attachments (open / closed) plus one sprite_frame attachment (4-cell glow cycle). The two SPEC 006 input flows (PS layer stack and PS sprite_frame layer group) compose under the same slot machinery without any cross-flow conversion. |

## Out of scope

- **Skin systems** beyond a flat slot list (Spine "Skins" -- swap multiple slots in lockstep). Future SPEC if a real use case appears.
- **Procedural / runtime attachment generation.** Slots are static -- the attachment list is fixed at export time.
- **Per-attachment skeleton wiring.** A swappable head with its own per-vertex weights vs the default head's weights is an SPEC 003 successor item, not SPEC 004 territory.
- **Crossfade / smooth slot transitions.** Slots are hard cuts (`interp = "constant"`); a future SPEC could add a `slot_blend` track type for crossfade, but that bumps `format_version` and is intentionally deferred.
- **Slot-aware live-link** (Blender ↔ Godot real-time slot preview). Backlog under "Architecture revisits".

## Surface (LOC estimate)

| Wave | LOC | Files |
| --- | --- | --- |
| 4.1 -- writer + authoring panel + preview shader | ~500 | `properties/`, `operators/`, `panels/`, `core/validation.py`, `core/exporters/godot/writer.py`, `core/sprite_frame_shader.py` (new -- preview shader-node group builder) |
| 4.2 -- Godot importer + animation track | ~200 | `apps/godot/addons/proscenio/builders/slot_builder.gd`, `animation_builder.gd` patch, GUT tests |
| 4.3 -- fixtures + docs | ~250 | `examples/authored/doll/` (brow slots), `examples/generated/slot_cycle/` (minimal slot fixture), `examples/<slot_cycle>.expected.proscenio`, godot wrapper, `STATUS.md`, `format-spec.md`, `.ai/skills/godot-dev.md` |

Total estimated ~950 LOC across three waves. Each wave is one PR -- no further sub-division (avoids the 5.1.x.x.x nesting that grew accidentally during SPEC 005).

## Successor considerations

- **Skin systems** (multi-slot lockstep swap) become natural after SPEC 004 ships; revisit if demand is concrete.
- **Animation events** (backlog) often co-author with slot transitions (sound cue when sword swap fires); independent SPECs but document the pairing in their respective STUDYs.
- **Per-attachment weights** -- a swappable head with its own vertex weights -- gets discussed when the first user hits the limitation. Until then, attachments share the default's weight setup (or stay rigid-attached).
