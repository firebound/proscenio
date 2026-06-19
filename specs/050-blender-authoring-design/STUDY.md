# Spec 050: Blender authoring design decisions

Three authoring calls, decided 2026-06-18 with the maintainer. The calls are locked below; [TODO.md](TODO.md) sequences them. They migrate to [`decisions.md`](../decisions.md) when this spec ships (the repo records locked calls at prune time, not while a spec is in flight).

Started as five questions. One returned to the backlog: **qa-quickarm-interaction-revision** - the modal interaction redesign needs more decision time, so it is a `DECIDIR` item in [`backlog.md`](../backlog.md). The **sprite-centered-vs-origin** question resolved on inspection into a concrete contract cleanup rather than a design fork (the origin already flows to the sprite pivot, and is a no-op for meshes) - it stays in this spec as item 4 below.

## Scope

- **qa-rotation-mode** - guard a rotation-mode swap on a driven bone, and give a one-click convert-to-Euler.
- **proscenio-y-depth-layers** - a manual depth control on top of the PSD-order Y spacing.
- **incorporate-blender-mesh-as-element** - a button to adopt a hand-authored Blender mesh into the flow.
- **sprite-origin-cleanup** - make the PS `[origin]` sprite-only, drop the vestigial manual `centered` toggle, and pin the sprite origin -> pivot round-trip with a test.

## Decisions

### 1. qa-rotation-mode

**Code anchors:** `operators/driver.py` (wiring a bone driver forces `rotation_mode = "XYZ"` and reads ROT_*); the writer collapses Euler/quaternion for export, so the export is already correct both ways; `core/validation/` (the lazy export validator).

**The risk:** a bone's `rotation_mode` is not controllable from the addon, and changing it on a bone that already drives a sprite can silently change how the driver reads the rotation (quaternion components are not radians), breaking the animation.

**Locked call: validate on export (option C) + add a convert-to-Euler operator.**
- The export validator warns when a driven bone's `rotation_mode` does not match the mode its driver assumes - lazy/inline validation, matching the project pattern (`decisions.md` "Blender authoring panel"). It targets the real risk without restricting authoring.
- A **Convert rotation to Euler** operator sets `rotation_mode = "XYZ"` (Blender converts the stored values natively), with a scope of **the active bone** or **all bones in the armature**. This is the one-click fix when the warning fires, and the cheap way to standardize a rig.

**Size:** S (the validator check) + S (the convert operator). Headless-testable both.

### 2. proscenio-y-depth-layers

**Code anchors:** `importers/photoshop/planes.py` (`_layer_placement` sets object `Y = z_order * Z_EPSILON`, 0.001 per layer, to avoid viewport z-fight); `exporters/godot/writer/sprites.py` (`_derive_z_index` reads `obj.location.y`, negates it, emits `z_index`). The import already prevents z-fight; the gap is manual control.

**Locked call: a manual per-object Depth Offset (option B), authoring-only.**
- A `depth_offset` float on the element, added to the PSD-order-derived Y before the writer negates it into `z_index`. Stays Blender-side; **no schema change** (the writer already reads Y). Lets the artist nudge or reorder a plane without re-importing, while the PS order remains the default.
- Surfaced as a field in the element/outliner panel.

**Size:** S. Headless-testable (the offset feeds `_derive_z_index`).

### 3. incorporate-blender-mesh-as-element

**Code anchors:** `panels/element.py` (the `element_type` selector; the empty-state "select a mesh or sprite element" line); `properties/object_props.py` (`ELEMENT_TYPE_ITEMS`, the sprite-only fields); `core/validation/active_element.py` (a valid element is a MESH with a known `element_type`); the `create_slot` operator is the existing button-plus-dialog precedent.

**Locked call: a button with a smart Mesh/Sprite dialog (option B), mirroring Create Slot.**
- A button (shown in the Element panel when the active object is a plain mesh with no Proscenio element data) runs an operator that offers a Mesh / Sprite choice. A quad (4 verts / 1 face) defaults to **Sprite** (hframes = vframes = 1, centered); anything else defaults to **Mesh**; the user can override. It sets `element_type` + the sensible defaults - the same fields the Element panel already controls. No schema impact.
- This is a button on screen exactly like Create Slot (a button + its adjust/redo dialog), confirmed as the wanted shape.

**Size:** M (operator + modal/redo dialog + the geometry heuristic + property set).

### 4. sprite-origin-cleanup

**Code anchors:** `importers/photoshop/planes.py:217-230` (`_layer_placement` sets the object location from `[origin]` and bakes the geometry offset); `exporters/godot/writer/sprites.py:136-169` (`_compute_sprite_offset` derives `Sprite2D.offset` from origin-vs-quad-centre) + `:313-315` (`centered`); `apps/godot/addons/proscenio/builders/sprite_builder.gd:46-49` (Godot applies `centered` + `offset`); `packages/models/src/proscenio_models/psd_manifest.py` (`MeshLayer.origin` exists today); the PS planner/parser that emits `[origin]`.

**Not a design fork - a contract cleanup.** Reading all three hops: the PS `[origin]` already flows to the Sprite2D pivot end to end. For a mesh it is a downstream no-op - Polygon2D has no pivot, the verts bake absolute or bone-local, and the import compensates for wherever the origin sits, so the origin cancels. The asymmetry is the proof: the mesh export uses world / bone space (origin cancels), the sprite export uses `centre - origin` explicitly (origin becomes the offset).

**Locked call:**
- Make `[origin]` **sprite-only**: the PS plugin stops emitting it for mesh layers (drop `MeshLayer.origin`), or the Blender importer / validator warns when a mesh carries one.
- Drop the **vestigial manual `centered` toggle** from the authoring UI: the writer's offset assumes `centered=true`, so a manual flip breaks placement; keep it an internal constant.
- Add a **round-trip test** PS `[origin]` -> Sprite2D pivot, so the wiring is pinned (today's confidence is code-read, not a run).

**Size:** S each. The round-trip test is the highest-value piece.

## Verdict summary

**4 items locked, all "now".** None blocks the others. The convert-to-Euler operator rides the qa-rotation validator PR. See [TODO.md](TODO.md) for the sequencing. The locked calls move to [`decisions.md`](../decisions.md) when the spec ships.
