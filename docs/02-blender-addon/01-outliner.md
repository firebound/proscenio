# Outliner

A sprite-centric flat list of the objects Proscenio cares about - slots, sprite meshes, attachments, and armatures - so you do not have to scroll Blender's native outliner on a big rig.

Filtering is Blender's native Filter by Name (open the UIList's filter arrows); the only control in the panel header is the favorites toggle. Click a row to make that object active and selected; Shift / Ctrl-click extends or toggles the selection, and a marker shows on every selected row, not just the active one. The SOLO icon pins a row as a favorite, and the favorites toggle hides everything else. Slots render first with a `[slot]` prefix and their attachments indented under them; a mesh parented to a bone shows `@ <bone>`; armatures render last with `[arm]`. Only the armature picked in the [Skeleton](04-skeleton.md) panel appears, so a stray rig does not crowd the list. Blender's native sort-by-name toggle flattens the parenting tree to a plain alphabetical list (and drops the indent with it).

This panel is **blender-only** - favorites, filter, and selection state never reach the export.
