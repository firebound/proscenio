# Outliner

An element-centric flat list of the objects Proscenio cares about - slots, attachments, element meshes, and armatures - so you select one fast on a big rig without scrolling Blender's native outliner. This panel is **blender-only**: favorites, the filter, and selection state never reach the export. It sits second in the sidebar and is collapsed by default.

The body is a single Blender `UIList`. The only control in the panel header row is the `Favorites only` toggle (the SOLO icon); searching and sorting are Blender's own list affordances, reached from the list's filter arrows.

**What the rows show.** Each row is a left-aligned button that names one object behind a kind icon; clicking it selects that object. The kind sets the icon, the label prefix, and the indent, so the list reads as the rig at a glance:

- A **slot** Empty renders first with a `[slot]` name prefix and the `LINK_BLEND` icon. Its attachments indent beneath it.
- A **slot attachment** (a mesh parented under a slot Empty) renders with an arrow name prefix and the `OBJECT_DATAMODE` icon, indented under its slot.
- An **element mesh** (a Proscenio mesh or sprite) renders with the `MESH_DATA` icon. When it is parented to a single bone it gains an `@ <bone>` suffix naming that bone.
- An **armature** renders last with an `[arm]` name prefix and the `ARMATURE_DATA` icon.

The indent mirrors the scene parenting tree: the armature is the root, slots and loose element meshes sit one level under it, and a slot's attachments sit under the slot.

**What the list filters in.** The list is sourced from `bpy.data.objects`, then narrowed to just the rig so unrelated scene objects stay out of the way:

- Cameras, lights, and other non-Proscenio kinds never appear.
- A raw hand-modelled mesh appears only once it carries element data (after import or `Incorporate`); until then it is hidden.
- Only the armature picked in the [Skeleton](04-skeleton.md) panel appears, so a second rig in the scene does not crowd the list.
- A row whose object has left the view layer (a deleted or undone datablock that lingers in `bpy.data`) drops out rather than persisting as a dead row.

Slot Empties and any mesh parented under them always belong, because a slot and its children are part of the rig by construction.

**Favorites and filtering.** The SOLO icon at the right edge of each row pins that object as a favorite. The `Favorites only` toggle in the panel header then hides every non-favorite row, so you can carve a big rig down to the handful of objects you are working on. Favorites are per-object flags; they persist with the `.blend` and, like the rest of this panel, never reach the export.

Name search is Blender's native Filter by Name: open the list's filter arrows and type. The native sort-by-name toggle (A-Z) flattens the parenting tree into a plain alphabetical list and drops the indent with it, so reach for it when you want to scan by name rather than by hierarchy.

**Selecting from the list.** A plain click replaces the selection and makes the clicked object active, matching Blender's single-click default. <kbd>Shift</kbd> + click extends the selection and <kbd>Ctrl</kbd> + click toggles the clicked row, mirroring the viewport and native-outliner modifiers. A selection marker shows on every selected row, not just the active one, because Blender's list highlight marks only the active row.
