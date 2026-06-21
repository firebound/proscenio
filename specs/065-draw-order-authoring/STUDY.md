# Spec 065: Y Location draw-order authoring

The depth a plane sits at - its Y in Blender, its `z_index` in Godot - was authored through two disconnected mechanisms. The Photoshop import stamped `object.location.y = z_order * 0.001` to encode the PSD layer order, and a separate authoring-only `depth_offset` float nudged the exported `z_index` without moving the object. Two hardcoded `0.001` constants (the importer's `Z_EPSILON` and the writer's `_DEPTH_EPSILON`) had to agree by hand, and the order an artist saw in the viewport (the Y position) was divorced from the number they edited (the offset).

This spec collapses that into one authoritative field. `Y Location (Draw Order)` is a whole-number layer the artist edits in the Element panel and the Outliner; it positions the object in Y (`order * spacing`) so stacked planes physically separate and never z-fight, and it is the value the writer negates into the Godot `z_index`. The per-layer gap becomes one configurable addon preference instead of two buried literals. Because the artist edits depth by the number (not by dragging Y), a manual Y drag now diverges from the stored order, so validation flags it.

## Locked decisions

- **Name.** The field is labelled `Y Location (Draw Order)` (identifier `y_draw_order`): it is the Blender Y location, authored as the draw order that becomes the Godot `z_index`. It replaces `depth_offset` outright - the float field, its Custom Property, and the writer's additive offset term all go.
- **The integer is the source of truth, not a view of Y.** `y_draw_order` is a stored `IntProperty`. Its update callback writes `object.location.y = order * spacing`; the writer reads the integer directly (`z_index = -order or None`) and never divides Y by the spacing. Consequence: the export is independent of the spacing preference - changing the spacing only re-spreads planes in the viewport, it can never shift the exported order. A manual Y drag does not reorder (the integer is master); it is surfaced by validation instead. This was chosen over a computed proxy of the real Y (which would keep the export coupled to a mutable preference and let a stray drag silently reorder).
- **The field stays a clean integer.** Editing `5` puts the object at `Y = 5 * spacing` (e.g. `0.005`); the tiny spacing lives only on the hidden Y. The artist always configures with whole numbers.
- **Spacing is a single addon preference.** `y_location_spacing` (default `0.001`, the old `Z_EPSILON`/`_DEPTH_EPSILON` value; `min` just above zero) replaces both hardcoded constants. The canonical default lives once as `DEFAULT_Y_LOCATION_SPACING` in the bpy-free `core/_shared/cp_keys` so the validation core and the preference share it.
- **Re-import resyncs the order for the meshes it already repositions.** Import sets `y_draw_order = z_order`. A re-import re-applies the PSD placement (position and order) to non-slot meshes exactly as it already re-applies their world position; slot-attached meshes are left alone (the slot owns them). The old separate `depth_offset` nudge that survived a re-import has no analogue - the order is one number now, and the PSD layer order is its source on import.
- **Helper panel hosts the viewport-legibility tools.** The 3D-view camera clip (`clip_start` + `clip_end`, native `space_data` properties) and a `Re-space planes` operator (rewrites every element's `Y = order * spacing`, applying a changed preference) join the Preview Camera there. Both are about seeing the layered stack correctly: enough clip range and depth resolution for tiny gaps, and a way to apply a new gap.
- **The Outliner shows the order inline.** Each plane row (mesh / attachment) draws an editable `y_draw_order` field so the stack can be read and reordered from the list. Slot and armature rows have no `z_index` and show nothing.
- **Validation warns on divergence.** When `round(object.location.y / spacing) != y_draw_order` the element validator emits a warning ("object was moved in Y; re-space or update the order"). Warning severity - it never blocks export, which reads the integer regardless. The spacing is injected as a parameter so the validation core stays bpy-free and testable; the panel reads the preference and passes it.

## Scope

- Replace `depth_offset` with `y_draw_order` end to end: property, Custom Property key, hydrate + mirror maps, Element panel, writer.
- Add the `y_location_spacing` preference and its reader, and the shared `DEFAULT_Y_LOCATION_SPACING`.
- Drive the object Y from the field (update callback); drive the import Y + order from the spacing.
- Add the Helper-panel camera clip and the `Re-space planes` operator.
- Add the Outliner order column.
- Add the divergence validation warning (active-element and export sweeps).
- Update the `slot_swap` fixture to stamp the order (preserving the existing `z_index` golden values 1 and 2).

## Sources

A live design call from chat (2026-06-21), not a backlog drain. No deferred or gated remainder.
