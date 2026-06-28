# Blender addon - manual-test checklist

Maintained by the QA Companion tool (tools/qa-companion): one block per item. `status` / `note` / `shots` are the recorded walk; `review` is your verdict on the test itself (keep / rephrase / drop / todo). Edit here or via the tool.

Each block answers three questions in plain language: what passing it proves (`intent`), what you do (`steps`), and what you see (`observe`). Items are grouped by panel (the `## <panel>` headers, which the Feedback tab keys off), and within a panel by subpanel in UI top-to-bottom order - each subpanel's inventory sweep first, then its behavioral tests. Ids carry the subpanel: BL-<PANEL>-<SUBPANEL>-NN.

## Global chrome (test once - applies to every panel)

### BL-CHROME-01 · Subpanel foldout collapses and expands
- status: pass
- review: keep
- pre: A fresh Blender session with the addon loaded; pick any Proscenio subpanel (e.g. Outliner).
- steps:
  1. Open the N-panel and look at a subpanel header without touching it.
  2. Click the header to expand it, then click again to collapse it.
- observe: The subpanel starts collapsed on first open. Clicking the header opens the body and shows its controls; clicking again hides them. It works the same way on every Proscenio subpanel.
- intent: The foldout behaviour is shared by all subpanels, so verifying it once stands in for all of them.
- code: apps/blender/panels/_helpers.py (draw_subpanel_header); apps/blender/panels/outliner.py:127-139

### BL-CHROME-02 · Status badge shows the right icon and tooltip
- status: pass
- review: keep
- pre: Any panel or subpanel header that shows a status badge.
- steps:
  1. Hover the small status icon at the right end of a header and read the tooltip.
  2. Compare headers for different bands (a Godot-ready feature vs a Blender-only one).
- observe: Each badge shows its feature's mark (a custom Godot or Blender preview image, falling back to a built-in icon when running headless or when the preview cannot load). Hovering shows the tooltip for that band.
- intent: The badge and its tooltip are shared chrome and read correctly for each feature band.
- code: apps/blender/panels/_helpers.py:46-69,83; apps/blender/operators/help_dispatch.py:30-40; apps/blender/core/feature_status.py

### BL-CHROME-03 · Clicking the status badge opens the legend popup
- status: pass
- review: keep
- pre: Any panel header with a status badge.
- steps:
  1. Click a status badge icon.
- observe: A popup titled 'Status badges' opens listing all four bands (godot-ready, blender-only, planned, out-of-scope) with the same definitions as the index page, plus an 'Open online docs' button. This is the only place in the addon that explains the godot-ready, planned, and out-of-scope bands. Clicking the badge changes nothing else.
- intent: The badge click opens the shared status legend with the full band definitions.
- code: apps/blender/operators/help_dispatch.py:42-44; apps/blender/core/help_topics.py:63-96

### BL-CHROME-04 · Help '?' popup renders its content and links
- status: pending
- review: keep
- pre: Any header with a '?' help button.
- steps:
  1. Click a '?' icon and read the popup.
  2. If the popup has an 'Open online docs' button or a 'See also' web link, click it.
- observe: A help popup opens hugging its text - the width tracks the wrapped prose, with no empty right band. A panel '?' shows a title and one short what-and-why paragraph (no section headings); a subpanel '?' shows a title, a summary, and one focused section scoped to that control. Bullet and numbered items keep their own lines with a hanging indent on wrapped continuations. 'Open online docs' opens the matching doc page (a subpanel's button deep-links to its H2 section); 'See also' web links are clickable buttons, and non-link references show as plain indented labels.
- intent: The help popup hugs its text (width derived from the wrap budget), renders the two-tier copy (a shallow panel overview versus a focused subpanel section), and deep-links to the mirrored doc page or section.
- code: apps/blender/operators/help_dispatch.py draw (reflow_paragraph + iface) + apps/blender/core/help_topics.py
- note: help-popup-width: bodies became single paragraphs reflowed at draw time + the 31 topics were re-edited. Re-walk a few popups to confirm the reflow + revised copy read correctly.

### BL-CHROME-05 · Each panel's '?' opens the matching help topic
- status: regressed
- review: keep
- pre: Each panel/subpanel header that has a '?' button.
- steps:
  1. Click '?' on each panel and confirm the popup title matches that panel.
- observe: Every header opens the help topic for its own panel (Pipeline first, with its Import / Validate / Export subpanels, then Element, Slots, Skeleton, Mesh Generation, Weight Paint, Outliner, Animation, Atlas, Helpers, and their subpanels). There is no standalone Validation panel (it is the Pipeline > Validate subpanel) and no standalone Help/Diagnostics panel - the About footer carries an 'Open help' button (not a '?' header), which opens the pipeline overview.
- intent: Each panel routes its '?' to the correct help topic after the panel restructure.
- code: apps/blender/panels/_helpers.py:84-85; apps/blender/operators/help_dispatch.py:50-97
- note: panel-restructure: Pipeline is first + absorbs Validate; Help panel removed (Open help moved to About). Re-walk the sweep.

### BL-CHROME-06 · Help popup handles an unknown topic gracefully
- status: n/a
- review: keep
- pre: A way to open the help popup with a topic id that does not exist.
- steps:
  1. Open the help popup with a made-up topic id.
- observe: The popup shows a single error line "unknown help topic: '<id>'" and nothing else; no crash.
- intent: An unresolved help topic shows a clean error instead of crashing.
- code: apps/blender/operators/help_dispatch.py:73-76
- note: não está claro como reproduzir isso (não existe proscenio.help no F3).

### BL-CHROME-07 · Panel body shows a guard when scene props are missing
- status: n/a
- review: keep
- pre: The Proscenio scene properties are not registered (does not happen in a normal run; confirm by reading the code).
- steps:
  1. With the scene properties unregistered, open any panel body.
- observe: The panel body collapses to a single error line ('proscenio scene props not registered', or 'proscenio property group not registered' on the Element and Pipeline panels) and draws no other controls.
- intent: When the addon's scene properties are missing, panels fail safe with a clear message instead of erroring.
- code: apps/blender/panels/validation.py:25-28; apps/blender/panels/outliner.py:143-146; apps/blender/panels/element.py:53-55; apps/blender/panels/pipeline.py:38-40
- note: não está claro como reproduzir isso.

### BL-CHROME-08 · Debug mode reveals the developer-only surface
- status: regressed
- review: keep
- pre: The addon Preferences open.
- steps:
  1. Turn 'Debug mode' ON in addon prefs, then redraw the N-panel.
  2. Turn it OFF and redraw again.
- observe: With Debug mode ON a 'Run Smoke Test' button appears in the About footer and the automesh Debug Pipeline subpanel appears; with it OFF both disappear. There is no standalone Diagnostics panel anymore. The change shows up on the next panel redraw, not instantly.
- intent: The debug-only developer surface is hidden until Debug mode is enabled.
- code: apps/blender/addon_prefs.py:50-58,67-80; apps/blender/panels/__init__.py (About draw, debug_mode_enabled); apps/blender/panels/mesh_generation.py:135
- note: panel-restructure removed the Diagnostics panel; the smoke test now lives in the About footer (BL-DIAG-01). Re-walk.

### BL-CHROME-09 · Header icons drop and titles truncate when the N-panel is narrow
- status: pending
- review: keep
- pre: Any Proscenio panel; drag the N-panel divider to narrow it.
- steps:
  1. Narrow the N-panel until the headers get cramped.
- observe: As the panel narrows, the right-side status badge + '?' help icons drop out of every Proscenio panel header (rather than overlapping the title), and the native bl_label titles truncate (lose characters) like Blender's own. The Skeleton and Element headers (custom draw_header) instead drop their '<name>' suffix and keep the base 'Skeleton' / 'Element' when narrow. Widening brings the icons and the name back.
- intent: Narrow headers shed their extra icons; native titles truncate and the Skeleton and Element headers drop their name suffix, matching Blender's narrow-header behaviour; nothing overlaps.
- code: apps/blender/panels/_helpers.py draw_subpanel_header (_HEADER_ICONS_MIN_WIDTH gate)

## Outliner panel

### BL-OUTLN-SWEEP · Outliner panel inventory (visual pass)
- status: pending
- review: keep
- pre: Outliner subpanel expanded, with a scene that has the picked armature, at least one slot + attachment, an authored sprite/mesh, plus a raw hand-modelled mesh and a second (unpicked) armature.
- observe: The Outliner shows, in order: a favorites-only toggle (star icon), and the object list (up to 8 rows). Text search is Blender's native 'Filter by Name' under the list's expand arrows - there is no separate Proscenio search field. Each row carries, left to right: a selection marker (a filled radio dot when the object is selected, an empty one otherwise), the name, a 'Y Location (Draw Order)' integer field on plane rows (element meshes + attachments; dropped when the N-panel is narrow), and the favorite star, with the name indented by its depth in the parenting tree. Names are labeled by kind: armature as '[arm] <name>', slots as '[slot] <name>', attachments as '-> <name>', element meshes as '<name>' (with '@ <bone>' when bone-parented). Only Proscenio members appear: an element mesh shows once it carries element data (imported or Incorporated), the armature only when it is the one picked in the Skeleton panel, plus slots and their attachments. The raw mesh, the unpicked armature, cameras, and lights do not appear.
- intent: Confirm the Outliner renders its favorites toggle, the per-row selection marker, the depth-indented names, the inline draw-order field on plane rows, and that only Proscenio members (authored meshes + the picked armature + slots/attachments) are listed; behavior lives in the named tests.
- code: apps/blender/panels/outliner.py draw_item (sel marker + name + order + star) + filter_items
- note: blender-authoring-ux: members-only filter + parenting-tree order + depth indent. draw-order-authoring added the inline Y Location (Draw Order) field on plane rows. Re-walk the inventory.

### BL-OUTLN-01 · Filter the list by typing
- status: pass
- review: keep
- steps:
  1. Open the list's native 'Filter by Name' field (the expand arrows at the bottom of the list) and type part of an object's name.
  2. Clear the field.
- observe: As you type, rows whose name does not contain what you typed disappear; only matching rows stay. Clearing the field brings every Proscenio-relevant row back.
- intent: Typing in Blender's native filter narrows the list live to matching objects; an empty filter shows everything relevant. (Spec 043 removed the separate Proscenio search field; the native one is now the only search.)
- code: apps/blender/panels/outliner.py filter_items (self.filter_name)

### BL-OUTLN-02 · Favorites-only toggle hides the rest
- status: pass
- review: keep
- steps:
  1. Mark a few rows as favorites (the star), then turn on the favorites-only toggle next to the filter.
  2. Turn the toggle off again.
- observe: With the toggle on, only favorited rows stay visible; turning it off restores the full filtered list. Favorited rows are not moved to the top.
- intent: The favorites-only toggle hides everything except favorited rows.
- code: apps/blender/panels/outliner.py:149 (prop) + filter_items:100-116
- note: favoritos não sobem para o topo (achado conhecido).

### BL-OUTLN-03 · List is ordered by the scene parenting tree
- status: pending
- review: keep
- observe: Rows read as the parenting tree, regardless of scene order: the picked armature first (root), then each slot immediately followed by its own attachments (slots ordered by name, the slot row before its attachments), then the loose element meshes - and each row is indented by its depth (armature flush, slots + loose meshes one level in, attachments two). Cameras, lights, raw meshes, and unpicked armatures are not listed.
- intent: The list lays out armature -> slot -> slot mesh, then loose meshes (the scene parenting), not a flat by-category grouping.
- code: apps/blender/core/outliner_view.py hierarchy_sort_key + outliner_depth; apps/blender/panels/outliner.py filter_items (sort_key) + draw_item (indent)
- note: blender-authoring-ux: changed from the old category-then-name order to the parenting tree. Re-walk.

### BL-OUTLN-04 · Native 'Filter by Name' is the only search
- status: pass
- review: keep
- steps:
  1. Confirm the panel header shows only the favorites-only star toggle - no separate Proscenio search text field.
  2. Type into Blender's native 'Filter by Name' field (the expand arrows on the list).
- observe: There is no Proscenio search box in the header; the native 'Filter by Name' is the single search and it filters the list as you type.
- intent: Spec 043 removed the redundant Proscenio search bar; only Blender's built-in list filter remains (no precedence to reconcile).
- code: apps/blender/panels/outliner.py filter_items (self.filter_name only)

### BL-OUTLN-05 · Native 'sort by name' switches tree vs alphabetical
- status: pending
- review: keep
- steps:
  1. With the native sort controls (the list's expand arrows) showing, leave 'sort by name' (the A-Z button) off and read the order.
  2. Turn the A-Z button on and read the order again.
- observe: Off, the list is the parenting-tree order (armature -> slot -> attachments -> loose, indented by depth). On, the list flattens to a plain alphabetical order by name (every kind interleaved, the depth indent dropped). The native reverse arrow is not wired (no effect). The native invert-filter toggle can still flip which rows are shown.
- intent: The native A-Z 'sort by name' toggle switches the order between the parenting tree (off) and a flat alphabetical list (on); reverse is not wired.
- code: apps/blender/core/outliner_view.py outliner_sort_key; apps/blender/panels/outliner.py filter_items + draw_item (use_filter_sort_alpha)
- note: blender-authoring-ux: the A-Z toggle now works (was inert). Re-walk both states.

### BL-OUTLN-11 · Only Proscenio members are listed
- status: pending
- review: keep
- pre: A scene with the picked armature, a slot + attachment, an authored element mesh, a raw hand-modelled mesh (Add > Mesh, never Incorporated), and a second unpicked armature.
- steps:
  1. Read the Outliner rows.
  2. Incorporate the raw mesh (Element panel) and pick the second armature in the Skeleton panel; read the rows again.
- observe: At first the raw mesh and the unpicked armature are absent; the picked armature, slot, attachment, and authored mesh are present. After incorporating the mesh it appears (it now carries element data); after picking the second armature the listed armature switches to it (only the picked one ever shows).
- intent: The Outliner lists only Proscenio members - an element mesh once it carries the proscenio_type marker, the armature only when it is the Skeleton-picked one, plus slots and their attachments.
- code: apps/blender/core/outliner_view.py is_proscenio_member; apps/blender/panels/outliner.py filter_items
- note: blender-authoring-ux. Logic pinned by tests/test_outliner_view.py; this is the GUI walk.

### BL-OUTLN-06 · Active row highlight follows click and viewport selection
- status: pending
- review: keep
- pre: a scene with several Proscenio objects; type something into the native 'Filter by Name' so the list is sorted/filtered (not raw scene order).
- steps:
  1. Click different rows in the list.
  2. Now select one of those objects directly in the 3D viewport.
- observe: The highlighted active row follows whichever object you last clicked, landing on the correct visual row even with the list filtered/sorted. Selecting an object in the viewport moves the highlight to that object's row too. Selecting a non-Proscenio object (camera, light) leaves the highlight where it was.
- intent: The active-row highlight stays in sync with the active object in both directions - clicking a row and selecting in the viewport (spec 043).
- code: apps/blender/properties/_handlers.py sync_outliner_to_active_object + core/outliner_view.py source_index_for_name + selection.py:153-167
- note: cross-list-deselect: the same viewport-follow now drives the Slots list (highlight follows the active slot object) and the Skeleton bone list (highlight follows the picked armature's active bone), via sync_slots_to_active_object + sync_bone_index_to_active_bone. While re-walking, select a slot / a bone in the viewport and confirm those lists' highlights track too, instead of staying lit on a stale row.

### BL-OUTLN-07 · Clicking a row selects that object
- status: pass
- review: keep
- pre: Outliner expanded with at least one visible row.
- steps:
  1. Click a row's label.
- observe: Everything else is deselected and the clicked object becomes the only selected and active object, with its row highlighted. If the object was meanwhile deleted, a warning appears and nothing changes.
- intent: Clicking a row makes that object the active selection.
- code: apps/blender/panels/outliner.py:71-77 + operators/selection.py:40-59

### BL-OUTLN-08 · Star toggles a row as a favorite
- status: pass
- review: keep
- pre: Outliner expanded with at least one visible row.
- steps:
  1. Click the star at the right end of a row, then click it again.
- observe: The star fills and empties as you click, marking the row as a favorite and unmarking it. The favorite state survives undo. If that object's Proscenio data is unregistered, a warning appears and nothing changes. The row does not move to the top.
- intent: The star pins a row as a favorite so it survives the favorites-only filter.
- code: apps/blender/panels/outliner.py:78-84 + operators/selection.py:170-197

### BL-OUTLN-09 · Deleted / undone objects leave the list
- status: pending
- review: keep
- pre: Outliner expanded with a Proscenio object listed (e.g. a Quick Armature rig).
- steps:
  1. Select the object and delete it (X / Delete), or undo its creation with Ctrl+Z.
- observe: The row disappears from the Outliner immediately - a deleted/undone object that lingers in bpy.data is no longer in the view layer, so it is filtered out. (It does not stay as a ghost row that warns 'not in the current view layer' on click.)
- intent: The list reflects the real scene; objects removed from the view layer drop out.
- code: apps/blender/panels/outliner.py filter_items (view-layer membership) + core/outliner_view.py row_visible

### BL-OUTLN-10 · Shift extends, Ctrl toggles the selection
- status: pending
- review: keep
- pre: Outliner expanded with at least three visible rows.
- steps:
  1. Click a row (plain click).
  2. Shift-click a second row.
  3. Ctrl-click a third row, then Ctrl-click it again.
- observe: The plain click selects only that object (its selection marker fills, the others empty), and it becomes active. Shift-click on the second row keeps the first selected and adds the second, which becomes active - both markers now filled. Ctrl-click on the third row adds it (marker fills, it becomes active); a second Ctrl-click on it removes it (marker empties) while the rest stay as they were. The viewport selection matches the markers throughout. Clicking a stale row (object left the view layer) warns and changes nothing, in every mode.
- intent: A plain click replaces the selection; Shift extends it and Ctrl toggles the clicked row, mirroring the viewport and native Outliner (spec 046). The per-row marker tracks the real object selection.
- code: apps/blender/operators/selection.py PROSCENIO_OT_select_outliner_object (invoke reads event.shift/ctrl) + core/bpy_helpers/_shared/select.py select_add/select_toggle

### BL-OUTLN-12 · Inline draw-order field reorders plane rows
- status: pending
- review: keep
- pre: Outliner expanded, the N-panel wide enough to show the order field, with two element meshes (or attachments) and the armature listed.
- steps:
  1. On a plane row (an element mesh or attachment), edit the 'Y Location (Draw Order)' integer field - including to a negative value.
  2. Narrow the N-panel until the field disappears, then widen it back.
- observe: The field shows the object's draw-order layer and edits it in place, even on a non-active row (it moves that row's object, not the active one). Slot and armature rows have no field. Below a narrow panel width the field is dropped (the name + star stay); it returns when widened. The order remains editable in the Element panel regardless.
- intent: The Outliner exposes the draw order inline so the stack reads and reorders from the list; the field targets its own row's object (id_data, not the active object) and hides in a narrow panel where its number would clip.
- code: apps/blender/panels/outliner.py draw_item (order column + _OUTLINER_ORDER_MIN_WIDTH) + properties/object_props.py (_y_draw_order_update via id_data)
- note: draw-order-authoring.

## Element panel (Active Sprite / Active Mesh, type, region, drive-from-bone, reproject UV)

### BL-ELEM-ROOT-SWEEP · Element panel root inventory (visual pass)
- status: regressed
- review: keep
- pre: A mesh or sprite element active.
- observe: The panel header reads 'Element: <name>' of the active element (dropping to plain 'Element' when nothing is active or the N-panel is narrow), mirroring the Skeleton header. With a mesh or sprite active, the panel root shows an element-type dropdown (Mesh / Sprite) and a 'Y Location (Draw Order)' integer field. An element imported from a PSD (one carrying an import origin) also shows a 'Re-import from PSD' button (icon FILE_REFRESH) below the fields. A hand-authored mesh with no Proscenio element data also shows a boxed 'hand-authored mesh - not a Proscenio element yet' note with an 'Incorporate as Element' button above the type dropdown. With nothing active it shows 'select a mesh or sprite element'. In Weight Paint mode the dropdown is greyed out with the label 'element type is locked in Weight Paint mode'. Any validation issues for the element render one row each; rows that name an object are clickable to select it.
- intent: Confirm the Element root renders the 'Element: <name>' header, the type dropdown, the Y Location (Draw Order) field, the Re-import from PSD button for an imported element, the Incorporate-as-Element note for an unincorporated mesh, the empty-state and locked-state labels, and inline validation rows.
- code: apps/blender/panels/element.py:62-99; apps/blender/core/validation/active_element.py:9
- note: absorbs the old per-field root items; locked-mode behavior is BL-ELEM-ROOT-02. panel-restructure added the 'Element: <name>' header (mirrors Skeleton); the body no longer repeats the name. blender-authoring-design added the Incorporate button; draw-order-authoring replaced the float Depth offset with the integer Y Location (Draw Order) field that positions the object in Y. element-individual-reimport added the Re-import from PSD button (its own walk is BL-ELEM-ROOT-07). Re-walk.

### BL-ELEM-ROOT-01 · Element type chooses the subpanel and the Godot node
- status: pass
- review: keep
- steps:
  1. Set the element type to Mesh, then to Sprite, watching which subpanel appears.
- observe: Choosing Mesh shows the Active Mesh subpanel; choosing Sprite shows the Active Sprite subpanel. The choice sticks.
- intent: The element type decides the export node - Mesh exports a deformable Polygon2D (UVs and weights), Sprite exports a framed Sprite2D - and swaps the matching subpanel into view.
- code: apps/blender/panels/element.py:62 (prop element_type, items object_props.py:26-34)

### BL-ELEM-ROOT-02 · Element type is locked in Weight Paint mode
- status: pass
- review: keep
- steps:
  1. Enter Weight Paint mode on a bound mesh and look at the Element panel.
- observe: The element-type dropdown is greyed out and the label 'element type is locked in Weight Paint mode' appears; no other element fields or subpanels draw.
- intent: The element type cannot be changed mid-weight-paint, so a bound mesh cannot switch to a sprite while you are painting it.
- code: apps/blender/panels/element.py:56-61

### BL-ELEM-ROOT-03 · Y Location (Draw Order) positions the plane and sets the export draw order
- status: pending
- review: keep
- pre: A mesh or sprite element active.
- steps:
  1. In the Element root, set Y Location (Draw Order) to a non-zero integer (e.g. 2), then to -1, then back to 0.
  2. Grab the object and move it in Y by hand, then look at the validation rows.
- observe: The field is a whole number. Changing it moves the object in Y (number times the Y Location spacing from the addon preferences) - a higher number sits further back, a negative one in front; 0 is the front layer. The Godot export draws it in that order regardless of the literal Y. After a manual Y drag that leaves the layer, a warning row appears ('object Y ... does not match Y Location (Draw Order) ...; ... run Re-space planes'); editing the number back, or Re-space Planes (Helpers), clears it.
- intent: Y Location (Draw Order) is one authoritative integer: it positions the object in Y so stacked planes separate (no z-fight) and it becomes the Godot z_index. The export reads the integer, not the literal Y, so the spacing only spreads planes in the viewport; a manual Y drag is flagged rather than silently reordering.
- code: apps/blender/panels/element.py:93; apps/blender/properties/object_props.py (_y_draw_order_update); apps/blender/exporters/godot/writer/sprites.py (_derive_z_index); apps/blender/core/validation/active_element.py (_validate_draw_order_position)
- note: draw-order-authoring replaced the float Depth offset. Writer + divergence pinned by tests/writer/test_sprites.py + tests/test_validation.py; the Y-positioning + re-space by apps/blender/tests/operators/test_draw_order.py. This is the GUI-presence walk.

### BL-ELEM-ROOT-04 · Incorporate as Element adopts a hand-authored mesh
- status: pending
- review: keep
- pre: A plain mesh modelled in Blender (Add > Mesh), with no Proscenio element data, active.
- steps:
  1. With the plain mesh active, open the Element panel and click 'Incorporate as Element'.
  2. In the redo panel, switch the Element type between Auto, Mesh, and Sprite.
- observe: Before incorporating, the panel shows the 'not a Proscenio element yet' note with the button. Clicking it adopts the mesh: a single quad (4 verts / 1 face) Auto-detects as Sprite, anything denser as Mesh. The redo panel exposes the Auto / Mesh / Sprite choice; choosing Sprite (or Auto on a quad) reveals Horizontal / Vertical frames. After incorporating, the note and button disappear and the normal element fields show.
- intent: Incorporate adopts a hand-authored mesh as a Proscenio element, Auto-detecting Sprite for a single quad and Mesh otherwise, with an override - mirroring the Create Slot button-plus-dialog shape.
- code: apps/blender/operators/incorporate.py; apps/blender/panels/element.py:78-85
- note: blender-authoring-design. Heuristic + execute pinned by tests/operators/test_incorporate_element.py; this is the GUI button + redo-dialog walk.

### BL-ELEM-ROOT-05 · Pixel art toggle switches texture interpolation
- status: pending
- review: todo
- pre: An imported element (sprite or mesh) with a textured material, viewed magnified in the viewport.
- steps:
  1. With the element active, tick 'Pixel art' in the Active Sprite / Active Mesh body, then untick it.
- observe: The checkbox is off by default. Ticking it sets the object's image-texture nodes to Closest (crisp, nearest-neighbor) so a magnified texture stops looking blurry; unticking restores Linear (smooth). Fresh imports stay on Linear (the importer is unchanged), so this is the per-element opt-in. The exported .proscenio is byte-identical either way - the toggle is authoring-only.
- intent: The per-element Pixel art toggle flips texture interpolation between Closest and Linear without touching the schema; the importer default is intentionally Linear, not Closest.
- code: apps/blender/properties/object_props.py (pixel_art) -> core/_shared/material_images.py; surfaced in panels/_draw_sprite.py + _draw_mesh.py

### BL-ELEM-ROOT-06 · Edited element fields survive undo and a disable / save / enable cycle
- status: todo
- review: keep
- pre: A sprite element active in a fresh session.
- steps:
  1. In the Element panel set Element type to Sprite, set Horizontal frames to 3 and Frame to 2.
  2. Press Ctrl+Z several times, then Ctrl+Shift+Z (redo) back to your values.
  3. Save the .blend. Disable the Proscenio addon in Preferences, then re-enable it.
  4. Re-open the panel and read the fields back; export and confirm the .proscenio.
- observe: Each field edit is a single undo step that round-trips cleanly (no stuck or doubled value). After save + disable + re-enable the fields read back exactly as set, with no re-entry needed, and the export matches. Storage lives in one place now (the proscenio_* Custom Property the panel proxies), so there is no mirror to fall out of sync and no hydrate step to lose untouched fields.
- intent: After the storage split (spec 037) every CP-canonical field has one home (its idprop) behind a get/set panel proxy; this confirms the GUI-only behaviours headless tests cannot - undo through the proxy and the disable/save/enable persistence cycle.
- code: apps/blender/properties/object_props.py (get/set proxies); apps/blender/core/_shared/pg_cp_fallback.py; pinned mechanically by apps/blender/tests/operators/test_storage_proxy.py
- note: storage-split. The proxy round-trip, frame clamp, and Drive-from-Bone idprop path are test-covered; this item is the undo + re-enable GUI walk only.

### BL-ELEM-ROOT-07 · Re-import from PSD refreshes only the active Element
- status: pending
- review: todo
- pre: A figure imported from a PSD manifest with at least two element layers; re-export one source layer's PNG from Photoshop with changed art (and optionally a changed bound). Paint weights on a different (sibling) element first.
- steps:
  1. With one imported element active, open the Element panel and click 'Re-import from PSD'.
  2. Watch the active element refresh; then inspect the sibling element you painted.
  3. Rename or delete that source layer in the PSD/manifest and click 'Re-import from PSD' again.
- observe: The button shows only for elements imported from a PSD (those carrying an import origin). Clicking it refreshes just the active element's art in place with no file picker (the manifest path is remembered from import); a same-bounds change keeps its painted weights, a changed bound reprojects them. The sibling element is untouched (its mesh and painted weights unchanged) and does not shift position. When the source layer no longer resolves (renamed/removed), a warning reports the element was left as is and nothing changes. If the remembered manifest file is gone, the file picker opens to re-pick it.
- intent: A per-element re-import scopes the spec 055 re-import contract to one manifest entry - refresh this element, preserve or reproject its weights, touch no sibling - so an artist who fixed one layer does not have to re-import the whole document.
- code: apps/blender/operators/reimport_element.py; apps/blender/importers/photoshop/__init__.py (reimport_element); apps/blender/panels/element.py (Re-import button)
- note: element-individual-reimport. Resolution + 055 contract + no re-anchor pinned by tests/operators/test_psd_reimport_single.py; this is the GUI button + remembered-path + picker-fallback walk.

### BL-ELEM-MESH-SWEEP · Active Mesh subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: A mesh element (type Mesh) active.
- observe: The Active Mesh subpanel shows a polygon/vertex-group count read-out ('<N> polygon(s), <M> vertex group(s)'), a Reproject UV button, an Isolated material checkbox, and an Exclude from atlas checkbox.
- intent: Confirm the Active Mesh subpanel renders its read-out, button, and two checkboxes; behavior lives in the named tests and atlas flows.
- code: apps/blender/panels/_draw_mesh.py:19-25
- note: Isolated material and Exclude from atlas behavior is covered in FLOW-ATLAS-01; Reproject behavior is BL-ELEM-MESH-01..02.

### BL-ELEM-MESH-01 · Reproject UV re-unwraps the mesh
- status: regressed
- review: keep
- pre: A mesh element (type Mesh) selected in Object Mode, with a known UV layout (e.g. an imported quad).
- steps:
  1. With the mesh selected in Object Mode, open Active Mesh and click Reproject UV.
  2. Open the UV editor and compare the result against the original layout.
- observe: The mesh's UVs are re-projected with a deterministic planar projection - U follows X, V follows Z for the picture-plane quad, so the texture is upright and NOT rotated or mirrored (the old Smart UV Project rotated/flipped it). Selection and active object are unchanged; no Edit-Mode flicker. A confirmation names the mesh. There is no Angle-limit field in the redo panel anymore.
- intent: Reproject UV recomputes the mesh UVs from its geometry so the texture lines up again after editing vertices, without disturbing the authored orientation.
- code: apps/blender/panels/_draw_mesh.py:23; apps/blender/operators/uv_authoring.py (planar_uv_from_positions)
- note: spec 036 PR2 replaced Smart UV Project with the deterministic planar projection; re-walk to confirm the orientation no longer flips. The purpose is now documented in the Texture Region help (Reproject-UV-vs-region).

### BL-ELEM-MESH-02 · Reproject UV is Object-Mode only
- status: pass
- review: keep
- pre: A mesh element in Edit Mode (or a non-mesh object active).
- steps:
  1. Enter Edit Mode on the mesh and try to run Reproject UV.
- observe: The action is unavailable (the button is greyed and the operator does nothing) because it only runs in Object Mode; the UVs are unchanged.
- intent: Reproject UV stays disabled outside Object Mode so it cannot run against Edit-Mode data.
- code: apps/blender/operators/uv_authoring.py:49-56

### BL-ELEM-SPRITE-SWEEP · Active Sprite subpanel inventory (visual pass)
- status: pending
- review: keep
- pre: A sprite element (type Sprite) active.
- observe: The Active Sprite subpanel shows the Horizontal frames, Vertical frames, and Frame fields, the atlas/region/frame read-out labels ('atlas: not linked in material' when no image is linked, otherwise 'atlas: WxH px', 'region: WxH px', 'frame: WxH px'), and the Setup Preview and Remove Preview buttons. There is no Centered checkbox (it was retired to a fixed internal constant).
- intent: Confirm the Active Sprite subpanel renders the grid fields, the size read-outs, and the preview buttons, and no longer shows a Centered toggle; behavior lives in the named tests.
- code: apps/blender/panels/_draw_sprite.py:18-29
- note: absorbs the per-field sprite items; their behavior is the BL-ELEM-SPRITE-NN tests. blender-authoring-design dropped the Centered toggle - re-walk to confirm it is gone.

### BL-ELEM-SPRITE-01 · Horizontal and Vertical frames set the spritesheet grid
- status: pass
- review: keep
- steps:
  1. In Active Sprite, change Horizontal frames and Vertical frames.
  2. Read the 'frame: WxH px' read-out.
- observe: Both fields accept whole numbers (at least 1). The 'frame:' read-out updates to the new cell size as you change the grid.
- intent: Horizontal and Vertical frames define the columns and rows of the spritesheet grid, which sets the frame (cell) size.
- code: apps/blender/panels/_draw_sprite.py:23-24; object_props.py:79-94
- note: era teste só do tipo sprite (escrita ruim corrigida).

### BL-ELEM-SPRITE-02 · Frame sets the resting cell and clamps to the grid
- status: regressed
- review: keep
- steps:
  1. In Active Sprite, set Frame to a cell index inside the grid.
  2. Set Frame above the last cell index (e.g. 99 on a 2x2 grid, whose last index is 3).
  3. Shrink hframes or vframes so the current Frame falls outside the new grid.
- observe: The field is labelled Frame (was 'Initial frame'). It accepts an in-range index and keeps it. An out-of-range value clamps to the last valid cell (hframes x vframes, minus 1). Shrinking the grid pulls a now-out-of-range Frame back into range automatically.
- intent: Frame chooses which cell the sprite shows at rest pose (animation tracks override it at export), clamped to the valid grid so the export never carries an index Godot rejects.
- code: apps/blender/panels/_draw_sprite.py:25; object_props.py (frame + _clamp_frame_and_update); core/_shared/sprite_grid.py
- note: spec 036 PR3 renamed Initial frame to Frame and added the grid clamp; re-walk the clamp + reclamp.

### BL-ELEM-SPRITE-04 · Sprite read-out shows atlas, region, and frame sizes
- status: pass
- review: keep
- steps:
  1. With a sprite whose material has an image, read the size labels; then on one with no image linked, read again.
- observe: With no image linked, it reads 'atlas: not linked in material'. With an image, it shows the atlas size, the region size, and the frame size in pixels.
- intent: The sprite read-out tells you the atlas, region, and frame dimensions so you can confirm the slicing without leaving the panel.
- code: apps/blender/panels/_draw_sprite.py:27,31-54

### BL-ELEM-SPRITE-05 · Setup Preview and Remove Preview toggle the slicer shader
- status: pass
- review: keep
- pre: A sprite mesh active.
- steps:
  1. With no preview shader yet, click Setup Preview.
  2. Then click Remove Preview.
- observe: Setup Preview is available only when there is no preview shader; clicking it installs the sprite-frame preview shader, then greys out while Remove Preview enables. Remove Preview is available only when the shader is present; clicking it strips the shader and re-enables Setup Preview.
- intent: Setup/Remove Preview install and remove the in-viewport sprite-frame preview shader, and only one is active at a time.
- code: apps/blender/panels/_draw_sprite.py:66-83 (proscenio.setup_sprite_frame_preview / remove_sprite_frame_preview)
- note: consigo mudar pra sprite, fazer a divisão e setar o preview; funciona.

### BL-ELEM-REGION-SWEEP · Texture Region subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: A mesh or sprite element active.
- observe: The Texture Region subpanel shows a mode dropdown (Auto / Manual). In Auto it shows only a hint ('computed from UV bounds at export' for a mesh, 'omitted at export - full atlas used' for a sprite). In Manual it shows the X / Y / W / H fields, plus a Snap to UV bounds button for a mesh element (absent for a sprite element).
- intent: Confirm the Texture Region subpanel renders the mode dropdown, the auto hints, the manual fields, and the mesh-only Snap button; behavior lives in the named tests.
- code: apps/blender/panels/_draw_region.py:20-36
- note: absorbs the per-field region items; clamp and snap behavior is the BL-ELEM-REGION-NN tests.

### BL-ELEM-REGION-01 · Auto vs Manual region mode
- status: pass
- review: keep
- steps:
  1. Set the region mode to Auto, then to Manual.
- observe: Auto shows only the hint label. Manual reveals the X / Y / W / H fields (and, for a mesh, the Snap button).
- intent: Auto derives the texture region from the UV bounds at export, while Manual lets you type the region rectangle yourself.
- code: apps/blender/panels/_draw_region.py:20; object_props.py:110-120

### BL-ELEM-REGION-02 · Manual region X/Y/W/H accept a normalized rectangle
- status: pass
- review: keep
- pre: An element with region mode set to Manual.
- steps:
  1. In Manual mode, set the X, Y, W, and H fields.
  2. On a sprite, read the 'region:' read-out.
- observe: Each field accepts a value between 0 and 1; out-of-range entries clamp into that range. On a sprite the 'region: WxH px' read-out updates from the manual rectangle.
- intent: The manual region defines the slice rectangle as fractions (0..1) of the atlas, so the element draws from the right part of the texture.
- code: apps/blender/panels/_draw_region.py:23-27; object_props.py:121-156
- note: consolida os quatro campos X/Y/W/H que estavam repetidos.

### BL-ELEM-REGION-03 · Snap to UV bounds fills the manual region from the UV
- status: pass
- review: keep
- pre: A mesh element (type Mesh) with region mode Manual, in Object Mode, with a UV layer and polygons.
- steps:
  1. On a mesh in Manual mode, click Snap to UV bounds.
- observe: The X / Y / W / H fields are overwritten to match the mesh's current UV bounds, and a confirmation reports it. If the mesh has no UV layer or polygons, a warning appears and nothing changes.
- intent: Snap to UV bounds fills the manual region rectangle from the mesh's actual UVs so you do not have to type it.
- code: apps/blender/panels/_draw_region.py:28-29; apps/blender/operators/uv_authoring.py:83-131
- note: o uso do UV bounds / texture region não está claro, mas funciona.

### BL-ELEM-REGION-04 · Snap is hidden for sprite elements
- status: pass
- review: keep
- pre: A sprite element with region mode Manual.
- steps:
  1. On a sprite in Manual mode, look at the Texture Region box.
- observe: The X / Y / W / H fields are shown, but there is no Snap to UV bounds button.
- intent: Snap is mesh-only; a sprite has no per-vertex UV to snap from, so the button is omitted.
- code: apps/blender/panels/_draw_region.py:28 (gated on element_type=='mesh')

### BL-ELEM-DRIVER-SWEEP · Drive from Bone subpanel inventory (visual pass)
- status: pending
- review: keep
- pre: A sprite or mesh element active.
- observe: The Drive from Bone subpanel shows, in order: a Target dropdown (Frame index / Region X/Y/W/H); an Armature picker (armatures only); a Bone dropdown (with a hint when no armature is picked yet, or when the armature has no bones); an Axis dropdown; the In/Out range fields (or an Expression field when Advanced is on) with the Advanced toggle; a live 'Value' read-out; the Drive from Bone button; and - when the element already has drivers - a 'Drivers (N):' list, one row per driver showing its target label + source bone with an X to remove it.
- intent: Confirm the subpanel renders all its controls + the existing-driver list; behavior lives in BL-ELEM-DRIVER-01..04.
- code: apps/blender/panels/_draw_driver_shortcut.py (draw_box + _draw_driver_list)
- note: driver-management: the existing-drivers list + remove were added. Re-walk the inventory (the list shows only when a driver exists).

### BL-ELEM-DRIVER-01 · Drive a sprite property from a bone
- status: pass
- review: keep
- pre: A sprite/mesh element is active; the scene has an armature with at least one bone.
- steps:
  1. In Drive from Bone, pick the armature, then the bone, then the axis.
  2. Choose the target property (Frame index, or Region X/Y/W/H) and set the In/Out range (or flip Advanced and type an expression).
  3. Click Drive from Bone.
  4. Pose or rotate the chosen bone and watch the Value read-out and the sprite.
- observe: The target property follows the bone through the mapped range - the Value read-out updates as you pose, and the sprite's frame or region edge changes with it. A confirmation names the link. Running Drive from Bone again on the same bone replaces the driver instead of adding a second one.
- intent: Posing a chosen bone moves a sprite property (frame or region edge), so art can be rigged to the skeleton.
- code: apps/blender/panels/_draw_driver_shortcut.py:22-43; apps/blender/operators/driver.py:96-262
- note: tudo de driver from bone funciona (walk do mantenedor).

### BL-ELEM-DRIVER-02 · Drive from Bone is disabled until a bone is picked
- status: pass
- review: keep
- pre: A mesh element is active with no armature/bone chosen in the subpanel.
- steps:
  1. Open Drive from Bone with the Armature/Bone left empty.
- observe: The Drive from Bone button is greyed out and cannot be clicked until a bone is selected.
- intent: The action stays disabled until it has a valid bone to read from.
- code: apps/blender/panels/_draw_driver_shortcut.py:40-42

### BL-ELEM-DRIVER-03 · Bad armature or bone is rejected
- status: pass
- review: keep
- pre: A driver create is triggered with a missing armature or a bone that is not in the armature.
- steps:
  1. Trigger Drive from Bone with a mismatched armature/bone (e.g. via the redo panel).
- observe: An error explains the problem ('pick a source armature' or 'bone not in armature') and no driver is created.
- intent: Invalid input is caught instead of silently adding a broken driver.
- code: apps/blender/operators/driver.py:197-204

### BL-ELEM-DRIVER-04 · Existing-driver list lists and removes drivers
- status: pending
- review: keep
- pre: A sprite element that already has one or more proscenio.* bone drivers (run BL-ELEM-DRIVER-01 first, ideally for two different target properties).
- steps:
  1. Read the 'Drivers (N):' list under the Drive from Bone button.
  2. Click the X on one row.
- observe: The list shows one row per existing driver - the target label (Region X, Frame index, ...) and the source bone. Clicking the X removes that one driver (the row disappears, the others stay) and reports it; the list hides entirely when no drivers remain.
- intent: The subpanel can view and remove the element's drivers, not only replace the single one the create path manages.
- code: apps/blender/panels/_draw_driver_shortcut.py _draw_driver_list + apps/blender/operators/driver.py PROSCENIO_OT_remove_driver + core/bpy_helpers/armature/driver_list.py

## Slots panel + slot operators

### BL-SLOTS-PARENT-SWEEP · Slots parent panel inventory (visual pass)
- status: pass
- review: keep
- pre: Slots panel expanded with at least one slot present.
- observe: When there are no slots it shows 'no slots yet - select meshes and Create Slot'. Otherwise the slots render in a native list widget (up to 5 rows, with the standard expand arrows for search/scroll); each row shows the slot name left-aligned with a slot icon, and a badge counting its direct mesh children on the right. A tip box explains the two ways to create a slot ('Pose Mode + active bone: slot anchored to the bone' and 'Object Mode + meshes: slot wraps the selection'). At the bottom is the Create Slot button.
- intent: Confirm the Slots parent panel renders the empty state, the native slot list with per-row child counts, the tip box, and the Create Slot button.
- code: apps/blender/panels/slots.py PROSCENIO_PT_slots.draw (template_list) + PROSCENIO_UL_slots

### BL-SLOTS-PARENT-01 · Create Slot makes a slot Empty
- status: pass
- review: keep
- pre: A scene is open. Optionally: Pose Mode with an active bone, or Object Mode with meshes selected.
- steps:
  1. In Pose Mode with an active bone, click Create Slot. Or in Object Mode, select meshes and click Create Slot.
- observe: A small Empty appears, named after the bone ('<bone>.slot') or just 'slot'. In Pose Mode it is parented to the active bone; in Object Mode it wraps the selected meshes (centred on them, keeping their world positions). It becomes the only selection, and a confirmation reports how many attachments it wrapped. The redo panel lets you rename it.
- intent: Create Slot makes a slot Empty - anchored to the active bone when posing, or wrapping the selected meshes as attachments. (also exercised by FLOW-SLOTSWAP-01)
- code: apps/blender/panels/slots.py:78 -> operators/slot/create.py:68-114

### BL-SLOTS-PARENT-02 · Create Slot redo can rename the Empty
- status: pass
- review: keep
- pre: Just ran Create Slot.
- steps:
  1. After Create Slot, open the redo panel and type a Slot name.
- observe: The Empty is renamed to what you typed. Leaving the name blank falls back to '<bone>.slot' or 'slot'.
- intent: The redo panel lets you name the new slot Empty, defaulting to the bone-based name.
- code: apps/blender/operators/slot/create.py:58-62,116-119

### BL-SLOTS-PARENT-03 · Clicking a slot row activates that slot
- status: pass
- review: keep
- pre: At least one slot in the scene.
- steps:
  1. Open the Slots panel and click a slot row.
- observe: That slot becomes the only selected and active object, its row looks pressed, and the Active Slot subpanel appears below. If the named slot no longer exists, a warning appears and nothing changes.
- intent: Each row selects and activates its slot so the Active Slot subpanel shows its attachments. (also exercised by FLOW-SLOTSWAP-01)
- code: apps/blender/panels/slots.py PROSCENIO_UL_slots.draw_item -> operators/slot/select.py:36-55

### BL-SLOTS-PARENT-04 · Filter and scroll the slot list
- status: pending
- review: keep
- pre: A scene with several slots (more than fit in the visible rows is ideal).
- steps:
  1. Open the list's native 'Filter by Name' field (the expand arrows at the bottom of the list) and type part of a slot's name.
  2. Clear the field; with many slots, drag the list scrollbar.
- observe: As you type, only slots whose name contains the text stay; non-slot objects never appear regardless. Clearing the field brings every slot back, sorted by name. With more slots than visible rows the list scrolls within its fixed height instead of growing the panel. Clicking a row still highlights and activates the correct slot even while a filter is active.
- intent: The slot list is the native widget (spec 046): name filter, scroll, and a highlight that lands on the right row under a filter. The slot-only filter is a strict subset of the Outliner's.
- code: apps/blender/panels/slots.py PROSCENIO_UL_slots.filter_items + core/outliner_view.py source_index_for_name

### BL-SLOTS-ACTIVE-SWEEP · Active Slot subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: A slot Empty active with at least one mesh child.
- observe: The Active Slot subpanel shows a header naming the slot ('Slot "<name>"'), the follow state and Bind/Unbind button, an 'Attachments (N):' heading with the child count, then a boxed attachment list - one row per child with a default-star toggle, the child name, a mesh/sprite kind label, and a keyframe button. The box holds the rows at a slightly reduced height so a long list grows the panel slowly rather than unboundedly. Below it a button row offers 'Attach Mesh' and 'Add Selected'. A validator error row appears under the list for a slot with no children.
- intent: Confirm the Active Slot subpanel renders the slot header, follow state, attachment count, the boxed attachment list with its per-row affordances, the Attach Mesh / Add Selected buttons, and the validator rows; behavior lives in the named tests.
- code: apps/blender/panels/slots.py PROSCENIO_PT_active_slot.draw
- note: reescrito - antes estava ilegível ("incompreensível o que é pra observar"); atualizado para a lista de attachments em caixa e os dois botões de anexar (spec 046).

### BL-SLOTS-ACTIVE-01 · Active Slot subpanel appears only for a slot Empty
- status: pass
- review: keep
- steps:
  1. Make a slot Empty active, then make a non-slot object active.
- observe: The Active Slot subpanel appears only when the active object is a slot Empty; otherwise it is hidden. The parent Slots panel stays visible either way.
- intent: The Active Slot subpanel is shown only when a slot Empty is active, so it always describes the current slot.
- code: apps/blender/panels/slots.py:96-99

### BL-SLOTS-ACTIVE-02 · Warning row when the slot has no parent bone
- status: pass
- review: keep
- pre: A slot Empty active.
- observe: A red alert row, 'no parent bone - attachments will not follow any bone', appears only when the active slot is unparented; it is absent when the slot is bone-parented.
- intent: An unparented slot is flagged so you know its attachments will not follow any bone.
- code: apps/blender/panels/slots.py:122-128

### BL-SLOTS-ACTIVE-03 · Error row when the slot has no children
- status: pending
- review: keep
- pre: A slot Empty active.
- observe: A red validator error row, 'slot "<name>" has no MESH children', appears under the attachments only when the active slot has no mesh children. (Spec 046 removed the older inline 'empty slot - add child meshes' INFO line - the validator's error row is now the single signal, and it carries error severity.)
- intent: An empty slot is flagged once, by the validator, so you know to add attachments to it.
- code: apps/blender/core/validation/active_slot.py:28-29 (drawn by PROSCENIO_PT_active_slot.draw validation loop)

### BL-SLOTS-ACTIVE-04 · Star marks the slot's default attachment
- status: pass
- review: keep
- pre: A slot Empty active with at least one mesh child.
- steps:
  1. Click the star at the left of an attachment row.
- observe: That attachment becomes the slot's default: its star fills and looks pressed while the others stay empty, and a confirmation names it. With no default set yet, the first attachment shows as the default. Naming a non-child reports a warning and changes nothing.
- intent: The star marks which attachment is visible when the scene loads (the default visible child). (default attachment exercised by FLOW-SLOTCYCLE-01)
- code: apps/blender/panels/slots.py:138-148 -> operators/slot/attachment.py:70-104

### BL-SLOTS-ACTIVE-05 · Add Selected re-parents selected meshes into the slot
- status: pass
- review: keep
- pre: A slot Empty active and at least one other mesh also selected.
- steps:
  1. Select a slot Empty (active) plus a mesh, then click Add Selected.
- observe: Each selected mesh is re-parented into the slot Empty, keeping its on-screen position, and a confirmation reports how many were added. With no qualifying mesh selected, the button is greyed out.
- intent: Add Selected re-parents the selected meshes into the active slot as new attachments (the fast path when a mesh is already selected; the picker is BL-SLOTS-ACTIVE-07).
- code: apps/blender/panels/slots.py PROSCENIO_PT_active_slot.draw -> operators/slot/attachment.py PROSCENIO_OT_add_slot_attachment

### BL-SLOTS-ACTIVE-06 · Per-slot validation issue rows are clickable
- status: pass
- review: keep
- pre: A slot Empty active that has a validation issue (no children, broken default, child/bone mismatch, or transform keys on a child).
- observe: Validation issue rows render under the attachments; error rows tint red and warning rows stay plain. Rows that name an object are clickable and select that object when clicked.
- intent: Per-slot validation issues are surfaced and let you jump to the offending object.
- code: apps/blender/panels/slots.py PROSCENIO_PT_active_slot.draw validation loop -> _helpers.py draw_issue_row -> validation/active_slot.py:15-35

### BL-SLOTS-ACTIVE-07 · Attach Mesh picker attaches by name
- status: pending
- review: keep
- pre: A slot Empty active and nothing else selected (the single-selection case the picker exists for).
- steps:
  1. With only the slot active, click Attach Mesh.
  2. In the dialog, pick a mesh by name from the search field and confirm.
- observe: A dialog opens with a mesh-name search field. Confirming re-parents the chosen mesh into the active slot, keeping its on-screen position, and a confirmation names it. Picking a non-mesh (or a name that is not a mesh) warns and changes nothing. The button is available whenever a slot is active, even with no other object selected - unlike Add Selected, which needs a mesh selected first.
- intent: The picker breaks the single-selection deadlock (you cannot have the slot active AND a target mesh selected at once), attaching a mesh chosen by name without touching the active object (spec 046). The bone half stays the separate Bind to Bone dialog.
- code: apps/blender/operators/slot/attachment.py PROSCENIO_OT_attach_mesh_to_slot (invoke_props_dialog + prop_search)

## Skeleton panel: armature picker, bone list, pose helpers, Quick Armature, IK, authoring camera, pose library

### BL-SKEL-PARENT-SWEEP · Skeleton parent panel inventory (visual pass)
- status: pass
- review: keep
- pre: Skeleton panel expanded; toggle scene state (armature present or absent, rig picked or not) to surface each read-out.
- observe: The parent panel shows the Active Armature picker (armatures only). When no armature exists it warns 'no Armature in scene - use Quick Armature below'. When armatures exist but none is picked it shows a boxed note 'no rig picked - skeleton ops will create a new Proscenio.QuickRig' with a 'Use existing instead' list. The 'Exports: <name>' read-out is NO longer here - it moved to Pipeline > Export.
- intent: Confirm the Skeleton parent panel renders the picker and the no-armature/no-rig notices; behavior lives in the named tests.
- code: apps/blender/panels/skeleton.py:94-112
- note: panel-restructure moved the 'Exports: <name>' read-out to Pipeline > Export; re-walk to confirm it is gone here and present there (BL-PIPE-SWEEP).

### BL-SKEL-PARENT-01 · Active Armature picker sets the project rig
- status: pass
- review: keep
- steps:
  1. Pick an armature in the Active Armature picker, then clear it.
- observe: Only armatures are offered. Picking one sets it as the project rig and the Armature and Pose subpanels react to it. Clearing it falls back to auto-detecting a QuickRig.
- intent: The Active Armature picker is the single source of truth for which rig bind, automesh, and export target. (also FLOW-DOLL-02)
- code: apps/blender/panels/skeleton.py:94-96 -> scene_props.py:496-509

### BL-SKEL-PARENT-02 · 'Use existing' buttons pick a scene armature
- status: pass
- review: keep
- pre: Armatures exist but the picker is empty (the 'no rig picked' box is showing).
- steps:
  1. Click one of the per-armature buttons in the 'Use existing instead' list.
- observe: That armature becomes the project rig: the box disappears and the picker now shows it. A missing or non-armature name reports a warning and changes nothing.
- intent: The 'Use existing' buttons let you set the project rig to a named scene armature in one click. (also FLOW-DOLL-02)
- code: apps/blender/panels/skeleton.py:113-120 -> skeleton_target.py:36-52

### BL-SKEL-ARMATURE-SWEEP · Active Armature subpanel inventory (visual pass)
- status: pending
- review: todo
- pre: A rig picked.
- observe: The subpanel is titled 'Active Armature' (was 'Armature'); the Skeleton parent panel header reads 'Skeleton: <name>' with the picked rig at a normal width, dropping to just 'Skeleton' when the N-panel is narrowed (the name disappears, the base title stays). The subpanel body shows the bone count ('N bone(s)') and a read-only bone list. Each row reads left to right: in Pose / Edit mode a selection marker (a filled radio dot when the bone is selected, an empty one otherwise); a non-interactive connectivity icon (a linked icon when the bone is connected to its parent, an unlinked icon for a parented-but-disconnected child, a generic bone icon for a root); the bone name left-aligned and indented by its depth (the indent zeroes when the list is sorted A-Z); then a right cluster of three flat (borderless) toggles - a relative-parent pin (filled when the bone uses relative parenting, hollow when not), a Godot export toggle (an export icon when the bone is exported, a cancel icon and depressed when it is excluded), and a favorite star (filled / hollow). The list carries Blender's native 'Filter by Name' search under its expand arrows. Below the list sits a row of two buttons: 'Active to Euler' and 'All to Euler'.
- intent: Confirm the renamed subpanel, the 'Skeleton: <name>' header that drops the name when narrow, the bone-count body, the native search, the per-row selection marker, the left connectivity icon, and the right cluster (relative-parent pin, Godot export toggle, favorite star); behavior lives in the named tests.
- code: apps/blender/panels/skeleton.py PROSCENIO_UL_bones (_bone_connectivity_icon + _draw_bone_flags) + ProscenioListMixin (draw_select_marker)
- note: skeleton-rig-ui: the row was split left (connectivity icon, non-interactive) / right (interactive relative-pin + export-exclude + favorite). The old text 'connected'/'disconnected'/'relative' tags are gone. Re-walk the inventory.

### BL-SKEL-ARMATURE-01 · Clicking a bone selects it in the viewport
- status: pending
- review: keep
- pre: A rig picked with bones; a bone row visible.
- steps:
  1. Click a bone name in the bone list.
- observe: The armature is selected and that bone becomes active. A plain click replaces the bone selection (in Pose / Edit mode only that bone stays selected). A missing armature or bone reports a warning and changes nothing.
- intent: Clicking a bone in the list selects it in the viewport.
- code: apps/blender/panels/skeleton.py -> selection.py PROSCENIO_OT_select_bone_by_name -> core/bpy_helpers/_shared/bone_select.py
- note: bone-multiselect: the click path now routes through the bone-select helpers (plain/extend/toggle). Re-walk plain-click selection.

### BL-SKEL-ARMATURE-02 · Shift extends, Ctrl toggles the bone selection
- status: pending
- review: keep
- pre: Pose (or Edit) mode on a rig with at least three bones; bone rows visible.
- steps:
  1. Click bone A (plain), then Shift-click bone B, then Ctrl-click bone B, then Ctrl-click bone C.
- observe: Plain click selects only A. Shift-click adds B (A stays selected), B becomes active. Ctrl-click on B (selected) deselects only B, leaving A. Ctrl-click on C (unselected) adds C and makes it active. The per-row radio markers track which bones are selected. In Object mode there is no per-bone selection - a click just moves the active bone (no markers).
- intent: The bone list mirrors the Outliner's Shift/Ctrl multi-select where bone selection is real (Pose / Edit); Object mode stays single active.
- code: apps/blender/operators/selection.py PROSCENIO_OT_select_bone_by_name (invoke reads event.shift/ctrl) + core/bpy_helpers/_shared/bone_select.py

### BL-SKEL-ARMATURE-03 · Convert rotation to Euler clears the driven-bone warning
- status: pending
- review: keep
- pre: A rig picked; a sprite element driven from one of its bones via Drive from Bone (the bone left in its default Quaternion rotation mode).
- steps:
  1. Run Pipeline > Validate and read the issues list.
  2. Select the driving bone (or leave it active), then click 'Active to Euler' in the Active Armature subpanel. Re-run Validate.
  3. Set the bone back to Quaternion, then click 'All to Euler' and re-run Validate.
- observe: Before converting, Validate shows a warning that the bone drives the sprite's rotation but is not in XYZ Euler (the driver reads XYZ). 'Active to Euler' converts the active bone to XYZ Euler and the warning clears for it; 'All to Euler' converts every bone in the armature. The pose does not visibly change (Blender converts the stored rotation). A status report names how many bones were converted.
- intent: The export validator warns when a sprite-driving bone is not in XYZ Euler, and Convert rotation to Euler (active bone or whole armature) is the one-click fix that clears it.
- code: apps/blender/operators/armature/rotation_mode.py; apps/blender/core/validation/export.py _validate_driver_rotation_modes
- note: blender-authoring-design. Validator + operator pinned by tests/test_validation_export.py and tests/operators/test_rotation_mode.py; this is the GUI loop across Skeleton + Validate.

### BL-SKEL-ARMATURE-04 · Per-bone export toggle keeps a bone out of the Godot export
- status: pending
- review: todo
- pre: A rig picked with at least one deform bone; ready to export a .proscenio.
- steps:
  1. In the Active Armature bone list, click a deform bone's export toggle so it shows the excluded (cancel) icon and depresses.
  2. Export via Pipeline > Export and inspect the generated skeleton.
  3. Click the export toggle on a non-deform bone (e.g. an .IK control), then set up Drive from Bone on a sprite from a deform bone and re-check that source bone's export toggle.
- observe: A deform bone toggled off (cancel icon, depressed) is omitted from the exported Godot skeleton - its deform children reparent to the nearest still-exported ancestor rather than disappearing. A bone left on (export icon) exports as before. Clicking the toggle on a non-deform bone is refused with a warning (it is already out of the export, so no hidden state is stored). Creating a Drive-from-Bone driver does NOT change its source bone's export toggle - the source may be a real deform bone, so it is never auto-excluded. The toggle has no viewport effect - it only governs the Godot export.
- intent: The per-bone export toggle (combined with use_deform) gates whether a deform bone reaches the Godot skeleton; excluded bones are skipped with their deform children reparented, the toggle refuses non-deform bones, and a Drive-from-Bone source is left untouched.
- code: apps/blender/operators/selection.py PROSCENIO_OT_toggle_bone_export; apps/blender/exporters/godot/writer/skeleton.py <- core/bone_export.py bone_is_exported; apps/blender/operators/driver.py create_driver
- note: skeleton-rig-ui: new authoring control. Export-skip + reparent + non-deform refusal pinned by tests/test_bone_export.py and tests/operators/ (toggle, non-deform reject, driver leaves-untouched, export-leak guard).

### BL-SKEL-RIGUI-SWEEP · Rig UI subpanel inventory (visual pass)
- status: pending
- review: todo
- pre: A rig picked.
- observe: The Rig UI subpanel renders one row per bone collection as a tree. A top-level collection with children is a header row; its direct-child collections render as a grouped button row under it, and each child branch recurses into its own header row below (grouped by header, not indented). A top-level collection with no children is a single self-button row. Every row reads left to right: a fixed-width eye toggle (the collection's viewport visibility), one or more equal-width select buttons that split the middle, and a fixed-width theme selector - a colored dot (the collection's shared theme color, or an empty circle when its bones share no one theme), the theme number, and a color-picker icon. The picker icon is live only on top-level rows (one color control per tree); nested rows reserve the column but the picker is inert. When the rig has no bone collections the subpanel shows an INFO notice 'no bone collections - add them in Blender's Bone Collections panel' instead of vanishing. The eye, select buttons, and theme selector line up in the same columns across every row regardless of depth or theme.
- intent: Confirm the Rig UI subpanel renders the recursive collection tree (header + grouped child buttons at every depth), the per-row eye / select / theme-selector columns aligned across rows, the top-level-only color picker, and the empty-state notice when no collections exist.
- code: apps/blender/panels/skeleton.py PROSCENIO_PT_rig_ui (_draw_row + _draw_swatch) <- core/rig_ui_view.py rig_ui_rows
- note: skeleton-rig-ui: new subpanel. Custom bone-shape widgets were dropped (native display_type dropdown instead). Walk a rig with 3+ levels of nested collections.

### BL-SKEL-RIGUI-01 · Eye hides, select picks, color tints a whole collection tree
- status: pending
- review: todo
- pre: A rig picked with at least one top-level bone collection that has nested child collections.
- steps:
  1. Click a collection row's eye toggle.
  2. Click a select button on a collection row (top-level and a nested one).
  3. On a top-level row, click the color picker and choose a theme color.
- observe: The eye toggles that collection's viewport visibility. A select button selects every bone of that collection (replacing the current selection), including bones in its nested children for a parent collection. Picking a color on a top-level row re-tints every bone in that collection's whole subtree (the dot and theme number update on the parent and its nested rows); nested rows have no live picker of their own. A missing or empty collection reports a warning and changes nothing.
- intent: The eye drives collection visibility, the select button selects the collection's bones (recursive for a parent), and the single top-level color picker tints the entire subtree (one color control per tree).
- code: apps/blender/operators/selection.py PROSCENIO_OT_select_bone_collection; apps/blender/operators/armature/bone_appearance.py PROSCENIO_OT_color_bone_collection <- core/bpy_helpers/_shared/bone_collections.py iter_collection_bones
- note: skeleton-rig-ui: select + color both resolve a collection's bones recursively (BoneCollection.bones_recursive). Pinned by tests/operators/test_bone_display_ops.py.

### BL-SKEL-POSE-SWEEP · Pose Mode subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: A rig picked; toggle in and out of Pose mode.
- observe: Out of Pose mode the subpanel shows a gate label 'enter Pose mode to bake / save poses' and the four pose operators (Bake Current Pose, Toggle IK, Bake IK to Keyframes, Save Pose to Library) are hidden. In Pose mode the gate label is hidden and the four operators appear.
- intent: Confirm the Pose Mode subpanel gates its four operators behind Pose mode; their behavior is covered by the GAP pose workflows.
- code: apps/blender/panels/skeleton.py:177-187
- note: pose-op behavior -> GAP-POSE-BAKE, GAP-IK, GAP-POSELIB.

### BL-SKEL-POSE-01 · Bake Current Pose keys every bone at the playhead
- status: pass
- review: keep
- pre: In Pose mode with the armature active.
- steps:
  1. In Pose mode, click Bake Current Pose.
- observe: Location, rotation, and scale keyframes are inserted on every pose bone at the current frame, and a confirmation reports the frame and how many bones were keyed.
- intent: Bake Current Pose keys every bone at the playhead (exporting those keys is GAP-POSE-BAKE).
- code: apps/blender/panels/skeleton.py:180 -> pose_library.py:117-147

### BL-SKEL-POSE-02 · Add / Remove IK Chain creates and removes a chain
- status: pending
- review: todo
- pre: In Pose mode with an active pose bone.
- steps:
  1. Select a pose bone with no IK and read the button, click it, then read and click it again.
- observe: With no Proscenio IK on the bone the button reads Add IK Chain; clicking it adds a control bone at the chain tip (joined to a "Proscenio Controls" collection with a theme color) and an IK constraint pointing at it. The button then reads Remove IK Chain; clicking it removes both. A cancelled click (no active bone) still reports even at the "errors" log level.
- intent: The button label resolves from the active bone's Proscenio IK state (Add when absent, Remove when present) and creates / removes the chain plus its themed control bone (export consequence is GAP-IK).
- code: apps/blender/panels/skeleton.py -> authoring_ik.py

### BL-SKEL-IK-01 · IK chains list, row markers, and constraint props
- status: pending
- review: todo
- pre: In Pose mode on an armature carrying at least one Proscenio IK chain.
- steps:
  1. Read the bone list and the IK chains section in the Skeleton panel.
  2. Click a chain row, then edit its influence and insert a keyframe; toggle the in-plane lock.
  3. Add or remove a chain and watch the list and markers.
- observe: A bone with a Proscenio IK constraint shows a chain marker in the bone list and its control bone shows a control glyph; the IK chains section lists each chain (tip, chain length, control) and clicking a row selects the tip. The props show chain length, a keyframable influence (the IK/FK seed - inserting a key records it), and the pole target, plus an opt-in in-plane lock. Adding or removing a chain refreshes the list and markers on the next redraw.
- intent: The panel surfaces every active IK chain from a live per-draw scan (no stored state) and exposes the curated constraint trio plus the in-plane lock, without redrawing Blender's native constraint UI.
- code: apps/blender/panels/skeleton.py -> core/bpy_helpers/armature/ik_chains.py

### BL-SKEL-POSE-03 · Bake IK to Keyframes bakes and clears the chain
- status: pending
- review: todo
- pre: In Pose mode with an active pose bone that has an IK constraint.
- steps:
  1. Select an IK-constrained bone and click Bake IK to Keyframes.
- observe: The IK chain is baked into keyframes (the posed result is keyed) and the IK constraint is removed, with a confirmation naming the frame range. A bone without IK cannot run it.
- intent: Bake IK to Keyframes converts an IK chain into plain keyframes and removes the constraint (export consequence is GAP-IK).
- code: apps/blender/panels/skeleton.py:182 -> authoring_ik.py:173-218

### BL-SKEL-POSE-04 · Save Pose to Library stores the pose as an asset
- status: pending
- review: todo
- pre: In Pose mode with a writable Asset Library configured.
- steps:
  1. In Pose mode, click Save Pose to Library.
- observe: The current pose is saved as a pose asset into the first writable library, named after the action or armature plus the frame. Without a writable library, an error appears and nothing is saved.
- intent: Save Pose to Library stores the current pose as a reusable Blender asset (reuse path is GAP-POSELIB).
- code: apps/blender/panels/skeleton.py:183-187 -> pose_library.py:27-94

### BL-SKEL-QUICKARM-SWEEP · Quick Armature subpanel inventory (visual pass)
- status: pending
- review: todo
- pre: Quick Armature subpanel expanded.
- observe: The subpanel shows the Quick Armature launch button and four option fields that each keep their value: Lock to Front Orthographic, Default = chain connected, Bone name prefix, and Snap increment. While no session is running the launch button reads 'Quick Armature' (grease-pencil icon); a collapsible 'Shortcuts' section sits below it, closed by default and empty until a session runs. While a session IS running the launch button reads 'Exit Quick Armature' (an X icon) and the expanded 'Shortcuts' section mirrors the live gesture cheat-sheet (the same chords shown on the status bar).
- intent: Confirm the Quick Armature subpanel renders its four options and they persist, the launch button swaps to 'Exit Quick Armature' while a session runs, and the collapsible 'Shortcuts' section mirrors the live cheat-sheet only during a session; the modal behaviour is BL-SKEL-QUICKARM-01.
- code: apps/blender/panels/skeleton.py PROSCENIO_PT_quick_armature (_quick_armature_is_running + _draw_quick_armature_shortcuts) -> scene_props.py
- note: skeleton-rig-ui: added the Exit toggle + the collapsible Shortcuts cheat-sheet mirror. Re-walk the inventory.

### BL-SKEL-QUICKARM-01 · Quick Armature modal walk (consolidated)
- status: pending
- review: keep
- pre: The mouse is over a 3D viewport; the Quick Armature subpanel is open.
- steps:
  1. Click Quick Armature to start. It creates or reuses the QuickRig target, enters Edit mode on it, remembers your entry mode + view + selection, optionally snaps to Front Ortho, and shows the preview and cheat-sheet overlays.
  2. Draw a bone: press, drag, and release the left mouse button inside the viewport. A bone is created (its head snaps to the previous bone's tail when chaining); a too-short drag is skipped with a message.
  3. Hold Shift while dragging to flip between chaining and starting a new root; the preview tints to show the unparented mode.
  4. Hold Alt while dragging to parent to the previous bone but start the new bone at the cursor; a dashed link line shows the disconnected parent.
  5. Press X then Z to lock drawing to the X or Z axis (press again to clear); a coloured guideline shows the locked axis.
  6. Hold Ctrl while drawing to snap the bone ends to the grid increment; the preview follows the snapped point.
  7. Press Ctrl+Z to undo the last bone you drew, Ctrl+Shift+Z to redo it; undoing or redoing past the ends reports there is nothing to do.
  8. Press Enter to finish (the status-bar hint reads 'finish'): the overlays clear, your view and selection are restored, and a confirmation reports how many bones you authored.
  9. Press Esc (or Enter): with nothing drawn the Esc hint reads 'cancel (discards empty rig)' and it removes the auto-created empty rig; once a bone is authored it reads 'exit (keeps bones)' and the bones survive (labels-only - Esc is not destructive). Right-click does NOT exit (see step 11). On exit you are returned to your entry mode and your view + selection are restored.
  10. The subpanel's 'Lock to Front Orthographic' field (also overridable per-launch in the redo panel), when on, snaps to Front Ortho on launch and restores your prior view on exit; off leaves the view alone. The field takes effect on the first launch - no redo override needed.
  11. Reparent by native selection: right-click a bone to select it (the session stays in Edit mode, so this is Blender's own bone select - it does not exit). The next connected draw chains from the selected (active) bone instead of the last one you drew; with nothing selected the chain continues from the last-authored bone as usual. There is no Tab, no Draw/Reparent modes, and no tail-tip picking.
  12. Seed from an active bone: before launching, select one bone of an existing rig (e.g. an imported figure's 'root' bone) so it is the armature's active bone, then launch Quick Armature and draw a chaining bone. The first bone parents onto that selected bone. Launch with no active bone and the first bone is unparented as usual.
  13. Exit from the panel: while the session runs the subpanel button reads 'Exit Quick Armature'; clicking it finishes the running session (it does not start a second one) - an empty session is discarded, an authored one keeps its bones.
- observe: Each chord behaves as its step describes; the live preview overlay tracks the active chord (different tints for chaining, unparented, and disconnected, plus an 'outside canvas' warning when the cursor leaves the viewport). The chord cheat-sheet shows on the bottom status bar (and is mirrored in the panel's collapsible Shortcuts section) - the 3D viewport header no longer carries a duplicate strip (spec 045), and after exiting + reopening the file no leftover strip lingers. The confirm / exit hints differ ('finish' vs 'cancel'/'exit') and the Esc hint changes once a bone is authored. Right-click selects a bone in Edit mode (reparent) rather than exiting. Step 12: a pre-selected active bone seeds the first chain bone's parent; no active bone leaves it unparented.
- intent: One session covers launch, the draw/chain/disconnect chords, axis lock, grid snap, in-modal undo/redo, finish, cancel, the front-ortho option, the live overlay, the status-bar-only cheat-sheet with dynamic finish/exit hints, and the active-bone chain seed (select the importer root, launch, draw -> chain seeds from root with no new chord).
- code: apps/blender/panels/skeleton.py:212 -> apps/blender/operators/armature/quick_armature.py (modal + Tab mode dispatch + the invoke active-bone seed + exit); core/armature/quick_armature_math.py (next_mode, resolve_pick); _overlay.py; _status_bar.py emit_chord_layout

### BL-SKEL-03 · Active Armature picker
- status: pass
- review: rephrase
- observe: scene.proscenio.active_armature set to chosen object (poll=is_armature limits choices to armatures); clearing falls back to QuickRig auto-detect. Armature/Pose subpanels react to the pick.
- intent: The project-wide armature picker; single source of truth that bind/automesh/export target. (also FLOW-DOLL-02)
- code: apps/blender/panels/skeleton.py:94-96 -> scene_props.py:496-509
- note: repetido com o sweep?

### BL-SKEL-07 · Use existing armature button(s) (one per scene armature)
- status: pass
- review: keep
- pre: Armatures exist, picker empty (the 'no rig picked' box).
- steps:
  1. Click a per-armature button in the 'Use existing instead' column.
- observe: proscenio.set_active_armature runs; scene.proscenio.active_armature = that object; box disappears, picker now shows it. Empty/missing/non-armature names warn and CANCEL.
- intent: UNDOCUMENTED - one-click set the explicit Proscenio target to a named armature. (also FLOW-DOLL-02)
- code: apps/blender/panels/skeleton.py:113-120 -> skeleton_target.py:36-52

### BL-SKEL-11 · Bone row click (select_bone_by_name)
- status: pass
- review: keep
- pre: Picked armature with bones; row visible.
- steps:
  1. Click a bone name in the UIList.
- observe: proscenio.select_bone_by_name runs: only the armature is selected, bones.active set, in Pose mode only that pose bone selected, active_bone_index synced. Missing armature/bone warns + CANCELs.
- intent: Click a bone to select it in the viewport.
- code: apps/blender/panels/skeleton.py:52-58 -> selection.py:62-93

## Mesh Generation panel: automesh one-click + interactive modal + debug pipeline

### BL-MESH-PARENT-SWEEP · Mesh Generation parent panel inventory (visual pass)
- status: pending
- review: keep
- pre: Mesh Generation panel expanded; switch the active object between a mesh, a sprite, and nothing to surface each guard.
- observe: With no mesh active it shows 'select a mesh to generate or edit'. With a sprite active it shows 'mesh tools are mesh-only (this is a sprite)' plus a hint to parent the sprite to a bone, and hides the subpanels. With a mesh active it shows a target read-out ('Target: Skeleton <armature>' or 'Target: Skeleton (none - pick a rig there)') and the trace params both entry points share: the Interior Mode selector (Simple / Dense), Contour vertices, Interior spacing, and the dense-only column 'Density follows bones' with its Bone influence radius and Bone density factor sub-fields (greyed in Simple mode; the bone sub-fields active only in Dense with density on).
- intent: Confirm the parent panel renders the empty-state and sprite guards, the picker read-out, and the shared trace params lifted up from the Automesh-from-Alpha subpanel; behavior lives in the named tests.
- code: apps/blender/panels/mesh_generation.py PROSCENIO_PT_mesh_generation.draw
- note: automesh-shared-params: Interior Mode kept + Contour vertices / Interior spacing / the dense fields moved here from Automesh-from-Alpha so the Interactive modal sees them too. Re-walk both inventories.

### BL-MESH-ALPHA-SWEEP · Automesh-from-Alpha subpanel inventory (visual pass)
- status: pending
- review: keep
- pre: A mesh element active; Automesh from Alpha subpanel expanded.
- observe: The subpanel now shows only the alpha-trace-specific settings (Trace resolution, Alpha threshold, Margin in pixels) plus the Preserve base quad and Preserve weights on regen checkboxes, then the Automesh button (greyed unless the mesh has an image texture). The shared params (Contour vertices, Interior spacing, Interior Mode, the dense fields) now live on the parent Mesh Generation panel, not here.
- intent: Confirm the Automesh-from-Alpha subpanel renders the alpha-only settings + the enable/grey rule, with the shared params no longer duplicated here; behavior lives in the named tests.
- code: apps/blender/panels/mesh_generation.py _draw_automesh_alpha
- note: automesh-shared-params: the shared trace params moved to the parent panel. Re-walk this inventory.

### BL-MESH-ALPHA-01 · Automesh from Alpha rebuilds the mesh from the image
- status: pass
- review: keep
- pre: A mesh element whose material has an image texture of nonzero size.
- steps:
  1. Set the trace settings and click Automesh from Alpha.
- observe: The mesh is rebuilt to follow the image's alpha outline, and a confirmation reports the vertex and face counts. The redo panel lets you re-run with different settings.
- intent: Automesh from Alpha traces the image's alpha edge into a fitted mesh; re-running keeps the UV-pinned base quad.
- code: apps/blender/panels/mesh_generation.py:178 -> operators/automesh/automesh.py:62,193

### BL-MESH-ALPHA-02 · Automesh from Alpha preflight guards
- status: pending
- review: todo
- pre: A mesh with no material image, or a zero-size image, or a sprite element.
- steps:
  1. Run Automesh from Alpha on each failure case (for a sprite, via F3 search since the panel hides the button).
- observe: On a sprite it warns and cancels; with no image it errors 'no image texture' and cancels; a zero-size image errors and cancels; a very large image (over 4096) warns but still runs.
- intent: Automesh from Alpha checks its inputs and refuses to run on a sprite or a mesh without a usable image.
- code: apps/blender/operators/automesh/automesh.py:195-209,257-279

### BL-MESH-INTERACTIVE-SWEEP · Interactive subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: Automesh Interactive subpanel expanded.
- observe: The subpanel shows a label 'Interactive trace and edit', the Loops, Spacing, and Cut margin fields, the Preserve weights on regen toggle, and the Author Mesh (interactive) button. The button is enabled only when a mesh with an image texture is active; otherwise a 'select a mesh first' label shows.
- intent: Confirm the Interactive subpanel renders its fields, the regen toggle, and the Author Mesh button with its enable rule; behavior lives in the named tests.
- code: apps/blender/panels/mesh_generation.py:195-214; scene_props.py:287,310-333
- note: Preserve weights on regen behavior -> GAP-REGEN-PRESERVE.

### BL-MESH-INTERACTIVE-01 · Author Mesh launches the interactive modal
- status: pending
- review: todo
- pre: A mesh element with an image texture active.
- steps:
  1. Click Author Mesh (interactive).
- observe: The interactive modal starts: an overlay appears in the viewport, a chord cheat-sheet shows in the status bar, and the first trace stage (OUTER) is drawn. Nothing is written to the mesh yet.
- intent: Author Mesh starts a live preview of the trace where you step through stages and nothing is committed until the final stage.
- code: apps/blender/panels/mesh_generation.py:208 -> operators/automesh/automesh_authoring.py:170,210

### BL-MESH-INTERACTIVE-02 · Author Mesh invoke guards
- status: pending
- review: todo
- pre: A non-mesh object active, or a sprite element, or a mesh without an image.
- steps:
  1. Try to launch Author Mesh on each invalid case.
- observe: On a non-mesh or a mesh without an image it errors and cancels; on a sprite it warns and cancels. If setup fails partway, it errors and restores the prior state.
- intent: Author Mesh refuses to launch without a valid mesh-and-image, and cleans up if setup fails.
- code: apps/blender/operators/automesh/automesh_authoring.py:211-229,321-324

### BL-MESH-INTERACTIVE-03 · Author Mesh stage machine (consolidated)
- status: pending
- review: todo
- pre: The Author Mesh modal is running.
- steps:
  1. Press Enter to advance through the stages (OUTER, edit outline, inner loops, edit interior points, preview interior, apply); the stage label counts up and the overlay refreshes each step with a count report.
  2. On the OUTER stage, press bare Tab to switch from Auto-trace to Manual contour, then click points to author the outer hull; click the first vert (or close) to finish the loop. The closed loop replaces the alpha-traced outer; pressing Tab back to Auto-trace recomputes the traced contour (reversible).
  3. Press Backspace to step back to the previous stage; the overlay refreshes and pen stages reset their draw state.
  4. Press Esc to cancel: the overlay and status bar are removed, your session is restored, and no geometry changes.
  5. On the final stage, press Enter to commit: the mesh is written and a confirmation reports the vertex and face counts (with a warning if any drawn points fell outside).
  6. Flip the Interior Mode mid-modal: the stage list rebuilds (Simple drops the inner-loops stage).
- observe: Each key behaves as its step describes, the Manual contour loop becomes the outer, and the mesh only changes on the final commit.
- intent: One walk over the modal stage transitions, cancel, commit, and live re-snapshot.
- code: apps/blender/operators/automesh/automesh_authoring.py:342-348,355,987,1015-1038,1068,1264

### BL-MESH-INTERACTIVE-04 · Author Mesh tool cycle + pen editing (consolidated)
- status: pending
- review: todo
- pre: The Author Mesh modal is on a tool stage.
- steps:
  1. Press bare Tab to cycle the active tool of the current stage; the status bar and the panel's stage indicator name the new tool. Per stage: OUTER cycles Auto-trace and Manual contour; edit-outline cycles Extend and Cut; edit-interior cycles Point, Fold, and Cut. LMB always acts with the active tool (there is no Shift/Ctrl tap-toggle anymore).
  2. On the edit-outline stage with Extend or Cut active, click to place points or drag to free-draw, then right-click or Enter to finish. Extend reshapes the outline; Cut marks a corridor that is carved at apply.
  3. On the edit-interior stage with Point active, click to drop a single interior point. Tab to Fold or Cut for the pen, then draw and finish. The overlay turns red when a pen gesture aims outside the silhouette.
  4. While a pen tool is active: press X or Z to lock to an axis, use the mouse wheel or number keys to set subdivisions, Alt+click to remove a stroke, Ctrl+Z to drop the last point or stroke, and Esc to clear the in-progress line without leaving the tool.
- observe: Bare Tab cycles the tool and re-arms the pen (or exits to a passive/point tool); each gesture behaves per its step; the status bar shows the stage, the active tool, and the Tab cycle; the viewport draws the contour and preview overlays. Blender's Ctrl+Tab and Shift+Tab are untouched.
- intent: One walk over the bare-Tab per-stage tool cycle and the outline/interior pen editing, the pen chords, and the overlay/status-bar feedback.
- code: apps/blender/operators/automesh/automesh_authoring.py (_active_tool, bare-Tab cycle, _handle_pen_event) <- core/skinning/authoring_stages.py (stage_tools / next_tool / default_tool / tool_is_pen); operators/automesh/_status_bar.py
- note: mesh-generation-interaction (spec 066): the Shift/Ctrl tap-toggle was deleted for a bare-Tab tool cycle. Re-walk the pen flow.

### BL-MESH-DEBUG-01 · Debug stage leaves a wireframe companion
- status: pass
- review: keep
- pre: Debug mode on so the Debug Pipeline subpanel is visible.
- steps:
  1. Pick a non-final stage in the Debug stage dropdown, then run Automesh from Alpha.
- observe: The run stops at the chosen stage instead of writing the final mesh, and leaves a wireframe companion object in the Proscenio.Debug collection, with a confirmation naming the stage. Setting it to Off or Final runs the full pipeline.
- intent: The debug stage lets you inspect any step of the trace as a wireframe companion.
- code: apps/blender/panels/mesh_generation.py:244 -> scene_props.py:346 -> automesh.py:150,308

### BL-MESH-DEBUG-02 · Clear Debug Companions removes the wireframes
- status: pass
- review: keep
- pre: Debug Pipeline subpanel open with debug companions present for the active object.
- steps:
  1. Click Clear Debug Companions.
- observe: All debug companions for the active object are removed, and a confirmation reports how many were cleared.
- intent: Clear Debug Companions deletes the wireframe companions left by debug runs.
- code: apps/blender/panels/mesh_generation.py:245 -> automesh.py:339,356

## Weight Paint panel: five bind modes, Edit Weights modal, brush preset, copy weights, sidecar IO, snapshot restore

### BL-WPAINT-SWEEP · Weight Paint inventory across subpanels (visual pass)
- status: pending
- review: keep
- pre: A mesh element active with a target armature set in Skeleton and the mesh bound (to surface every read-out); inspect the Bind, Edit Weights, Snapshot, and Weight Transfer subpanels.
- observe: With a sprite active it shows 'select a mesh element (Weight Paint is mesh-only)' and no subpanels. With a mesh it shows a target read-out ('Target: Skeleton <armature>' or 'Target: Skeleton (none - pick a rig there)') and the subpanels: Bind has a Mode dropdown (Bone Heat / Proximity / Envelope / Single nearest / Empty), then under Proximity only a Max Distance and a Falloff Power field, a per-bone Soft/Hard overrides list (a scrolling, height-capped list now, not an unbounded column), a Bone Heat hint, and the Bind button (no separate target line - the parent read-out covers it); Edit Weights has an active-group label, the Edit Weights button (which reads 'Exit Painting Mode' while in weight-paint mode; with a 'bind first to enable' hint when disabled), the brush curve-preset buttons, and a Clear Empty Vertex Groups button; Brush has the four curve-preset buttons and a viewport-display box (Weight Opacity slider, Zero Weights dropdown, and a caveat about opacity 0); Snapshot has a Preserve weights on regen checkbox (the standalone provenance-overlay toggle was removed - the overlay lives only inside the Edit Weights modal now), a provenance line ('N paint / N seed / N reprojected' or 'no snapshot - run Bind first'), the Reset to Last Saved Weights button, a Save Snapshot button plus - when snapshots exist - a list of save points (pinned icon = manual, recover icon = auto) each with a restore button, then Export / Import Snapshot; Weight Transfer has a Max Distance field.
- intent: Confirm the Weight Paint subpanels render their controls and enable/grey rules; behavior lives in the named tests.
- code: apps/blender/panels/weight_paint.py (_draw_bind / _draw_snapshot / _draw_named_snapshots / PROSCENIO_UL_bone_overrides); _helpers.py
- note:
  Preserve weights on regen behavior -> GAP-REGEN-PRESERVE; modal-entry enable predicate -> FLOW-DOLL-02 / BL-WPAINT-EDIT-01.
  (2026-06-17 spec 044: max_distance + falloff_power now draw under Proximity; Clear Empty Vertex Groups button added to Bind.)
  ui-polish: the per-bone override box became a scrolling list, the inert provenance-overlay toggle was dropped, and Save Snapshot + the named-snapshot list were added. Re-walk the inventory.

### BL-WPAINT-BIND-01 · Mode dropdown picks the bind algorithm
- status: pass
- review: keep
- steps:
  1. Open the Bind Mode dropdown and pick each of the five modes.
- observe: All five modes are selectable and the choice sticks. Switching to a planar mode (Proximity / Envelope / Single nearest / Empty) shows the per-bone override box, while Bone Heat shows the hint that overrides do not apply to it.
- intent: The Mode dropdown chooses how the mesh is bound to the bones - Bone Heat is the default, the other four are fallbacks tuned via the redo panel.
- code: apps/blender/panels/weight_paint.py:174 (prop); properties/scene_props.py:218 (enum def)

### BL-WPAINT-BIND-02 · Per-bone Soft / Hard / Clear overrides (consolidated)
- status: pending
- review: keep
- pre: A target armature with bones (ideally many, to see the list scroll); Mode set to a planar mode (Proximity / Envelope / Single nearest / Empty).
- steps:
  1. Click Soft next to a bone.
  2. Click Hard next to the same bone.
  3. Click the X (Clear) on a bone that has an override.
  4. With a many-bone rig, confirm the list scrolls inside its box rather than pushing the Bind button off-screen.
- observe: The overrides are a scrolling, height-capped list now (a native UIList, with the same Soft / Hard / Clear buttons per row and Blender's filter under its expand arrows). Soft and Hard each set that bone's override and look pressed (only one at a time), and Clear becomes available. Clearing removes the override, un-presses both, and disables the X again. Overrides apply only to the planar modes - Bone Heat ignores them. A many-bone rig scrolls inside the list instead of growing the panel.
- intent: Soft blends a bone's weight smoothly with neighbours, Hard gives a crisp single-bone boundary, Clear drops back to the bind-mode default, and the list scrolls instead of pushing the Bind button down.
- code: apps/blender/panels/weight_paint.py PROSCENIO_UL_bone_overrides + _draw_bone_overrides -> operators/skinning/set_bone_mode.py
- note: wpaint-override-scroll: the override box became a template_list. Re-walk the Soft/Hard/Clear buttons + the scroll on a many-bone rig.

### BL-WPAINT-BIND-03 · Bind to Target Armature builds the weights
- status: pending
- review: keep
- pre: A mesh element active; a target armature set in Skeleton (the button is greyed without one).
- steps:
  1. With the target set and a mesh selected, click Bind to Target Armature.
- observe: The mesh is bound to the armature using the chosen Mode: vertex groups are created and a weight snapshot is written, with a confirmation reporting how many meshes were bound and per-mesh vertex/bone counts. With no target armature the button is greyed out.
- intent: Bind builds the vertex weights that deform the mesh, using the selected Mode, and stores the snapshot exported to the Polygon2D. (basic bind path also exercised by FLOW-DOLL-02)
- code: apps/blender/panels/weight_paint.py:186 -> operators/skinning/bind_mesh.py:176 execute

### BL-WPAINT-BIND-04 · Bind redo panel re-binds with new settings
- status: pass
- review: keep
- pre: Just ran Bind.
- steps:
  1. After Bind, press F9 (or open the redo panel) and change Bind mode, Falloff power, or Max distance.
- observe: The redo panel exposes the mode, the falloff power, and the max distance, and re-running re-binds the mesh with the new values.
- intent: The redo panel lets you re-bind with a different mode or tune the Proximity falloff and distance without starting over.
- code: apps/blender/operators/skinning/bind_mesh.py:49-94 (props), 104 invoke

### BL-WPAINT-EDIT-01 · Edit Weights paint stroke marks verts as user-painted
- status: pending
- review: keep
- pre: Inside the Edit Weights modal.
- steps:
  1. Press and drag the left mouse button to paint a stroke, then release.
- observe: At the end of the stroke (on release), the vertices you touched turn white (user-painted) and the provenance overlay updates without having to leave and re-enter the mode. Live-during-the-stroke is not expected - the overlay refreshes at stroke end.
- intent: Painting a stroke tags the touched vertices as hand-edited in the snapshot and the overlay repaints at stroke end.
- code: apps/blender/operators/skinning/edit_weights.py modal (RELEASE -> _tag_redraw_view3d, all VIEW_3D areas)

### BL-WPAINT-EDIT-02 · Edit Weights exits and restores (Esc + native mode exit)
- status: pending
- review: keep
- pre: Inside the Edit Weights modal.
- steps:
  1. Press Esc during the modal.
  2. Re-enter, then this time leave weight-paint mode via Blender's own control (Tab, the mode dropdown, or a pie menu) instead of Esc.
- observe: Both exits restore your prior state (mode, brush preset, bone visibility, selection, overlay), with a confirmation that the session was restored; a single Ctrl+Z then reverts the whole session. After a native-control exit the provenance overlay and its flag do not linger (the modal's mode-watch timer ends the session).
- intent: Esc and a native mode exit both cleanly end Edit Weights and restore brush, bone visibility, mode, selection, and the overlay flag.
- code: apps/blender/operators/skinning/edit_weights.py modal (ESC + TIMER mode-watch) -> _finish

### BL-WPAINT-EDIT-03 · Edit Weights button flips to Exit Painting Mode
- status: pending
- review: keep
- pre: A mesh bound to a target armature.
- steps:
  1. Click Edit Weights to enter the modal.
  2. Read the button label, then click it.
- observe: While in weight-paint mode the button reads 'Exit Painting Mode'; clicking it leaves the mode and ends the modal (state restored). Out of the mode it reads 'Edit Weights' again.
- intent: The entry button doubles as the exit while in the mode, so there is one obvious in/out control.
- code: apps/blender/panels/weight_paint.py _draw_edit_weights (obj.mode == 'WEIGHT_PAINT' branch -> object.mode_set)

### BL-WPAINT-BRUSH-01 · Brush curve presets (consolidated)
- status: pass
- review: keep
- pre: An active weight-paint brush exists (otherwise the preset buttons are greyed).
- steps:
  1. Click Hard Edge, then Soft Falloff, then Crease, then Smooth Blend.
- observe: Each button sets the brush's falloff curve to its preset shape, with a confirmation naming the preset. In Object mode with no weight-paint brush, all four buttons are greyed and a click does nothing.
- intent: The four presets reshape the brush falloff for common 2D weight-painting tasks.
- code: apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88 execute

### BL-WPAINT-SNAP-01 · Reset to Last Saved Weights restores the snapshot
- status: pass
- review: keep
- pre: A mesh active with a saved weight snapshot (the button is disabled without one).
- steps:
  1. After binding or painting, click Reset to Last Saved Weights.
- observe: The live weights revert to the last snapshot, with a confirmation reporting how many vertices and groups were restored. If the mesh topology changed since the snapshot, it errors and does nothing; if the snapshot is empty or corrupt, it errors with a hint to re-bind. The button is disabled with no snapshot.
- intent: Reset reverts the live weights to the last snapshot (it does not trigger an automesh regen), and refuses if the topology no longer matches.
- code: apps/blender/panels/weight_paint.py:352 -> operators/skinning/restore_weight_snapshot.py:49

### BL-WPAINT-SNAP-02 · Export and Import weight snapshot (consolidated)
- status: pass
- review: keep
- pre: A mesh element active; Export needs an existing snapshot, Import only needs a mesh.
- steps:
  1. After bind, click Export Snapshot, choose a .json path, and confirm.
  2. Click Import Snapshot, pick a .json, and confirm.
- observe: Export writes the snapshot to the chosen JSON file with a confirmation; on an unbound mesh the Export button does nothing. Import reads and validates the JSON and stores it on the mesh: if the topology matches it applies to the live weights ('imported and applied to N verts'), otherwise it stores only ('imported - topology differs'). A bad file or bad JSON warns and cancels.
- intent: Export and Import move a weight snapshot between files as JSON for version control or sharing.
- code: apps/blender/panels/weight_paint.py:359,360 -> operators/skinning/sidecar_io.py:50,66,84,101

### BL-WPAINT-SNAP-03 · Named save points + rolling auto-snapshots (consolidated)
- status: pending
- review: keep
- pre: A bound mesh element with a target armature picked.
- steps:
  1. Click Save Snapshot, give it a name (e.g. 'pose-a'), confirm.
  2. Paint or zero some weights so the live weights differ.
  3. Click the restore button on the 'pose-a' row.
  4. Enter and exit Edit Weights a few times; watch the auto rows.
- observe: Save Snapshot prompts for a name and adds a pinned-icon row to the snapshot list (re-saving the same name overwrites it, not duplicates). The restore button on a row reapplies that save point's weights to the mesh (topology-guarded - it errors if the mesh changed). Each Edit Weights session that ends normally adds a recover-icon 'auto HH:MM:SS' row; only the last three auto rows are kept (older ones roll off), while manual rows are unbounded. Save / list / restore are disabled when the mesh has no sidecar.
- intent: Named manual save points plus a rolling last-3 auto history make the weight save-point UX explicit (which point a restore targets), beyond the single 'last saved' Reset.
- code: apps/blender/panels/weight_paint.py _draw_named_snapshots + apps/blender/operators/skinning/named_snapshot.py + core/skinning/sidecar_schema.py (NamedSnapshot, add_named_snapshot, add_auto_snapshot) + core/bpy_helpers/skinning/sidecar_io.py append_auto_snapshot
- note: wpaint-named-snapshots: new feature (manual named + rolling auto). The rolling-3 cap + JSON round-trip have pure tests; the save/restore-by-name have headless tests; the list rendering + the per-session auto capture are the GUI-only pass.

### BL-WPAINT-XFER-01 · Copy Weights to Selected transfers weights
- status: pass
- review: keep
- pre: An active mesh plus at least one other selected mesh.
- steps:
  1. Select the target meshes, then the source mesh (active), and click the copy-weights button.
  2. Press F9 and change Max Distance to re-run with a different radius.
- observe: Each target mesh receives the source's weights by nearest vertex within the Max Distance, creating vertex groups as needed, with a coverage summary report. The button shows only the copy icon (no text). The redo panel exposes Max Distance. A transfer that covers nothing (e.g. Max Distance too small for any match) cancels with a warning instead of registering a successful, undoable no-op.
- intent: Copy Weights copies the active mesh's weights onto every other selected mesh by nearest world-space vertex.
- code: apps/blender/panels/weight_paint.py:151 -> operators/skinning/copy_weights_to_selected.py:25,41

## Animation panel (read-only action summary)

### BL-ANIM-SWEEP · Animation panel inventory (visual pass)
- status: pending
- review: keep
- pre: Animation subpanel expanded; test with zero actions and with at least one action.
- observe: A target read-out ('Target: Skeleton <armature>' or 'Target: Skeleton (none - pick a rig there)') heads the panel, matching Mesh Generation and Weight Paint. With no actions it then shows 'no actions to export' and no list. With actions it shows the action list (one row per action, between 2 and 6 rows visible), each row labeled with the action name and its frame range '[start-end]' (rounded to whole frames; an empty action shows '[0-0]'), and a 'N action(s) total' count below.
- intent: Confirm the Animation panel renders the target read-out, the empty state, the action list with frame ranges, and the total count; row-click behavior lives in the named tests.
- code: apps/blender/panels/animation.py:12-36,56-68

### BL-ANIM-01 · Clicking an action row assigns it to the picked armature
- status: pending
- review: keep
- pre: At least one action; an armature picked in the Skeleton panel.
- steps:
  1. Expand the Animation subpanel and click an action's name.
- observe: The clicked action is assigned to the Skeleton-picked armature (which then plays it when you scrub the timeline), and that row becomes active. The action looks like a plain label but acts as a button. It is undoable.
- intent: The action rows are click-to-assign and target the picker (the single source of truth), even though the panel reads as read-only.
- code: apps/blender/panels/animation.py:28-36 (draw), apps/blender/operators/selection.py (handler -> resolve_skeleton_target)

### BL-ANIM-02 · Assigning targets the picked armature, not the first in scene
- status: pending
- review: keep
- pre: At least one action; two or more armatures in the scene; one of them picked in the Skeleton panel.
- steps:
  1. With two or more armatures present and one picked, click an action row.
- observe: The action is assigned to the picked armature regardless of scene order; the other armatures are untouched, and there is no 'N armatures in scene' warning (the picker disambiguates). (Spec 045 removed the first-armature heuristic.)
- intent: The Skeleton picker, not a scene scan, decides which armature receives the action.
- code: apps/blender/operators/selection.py (resolve_skeleton_target)

### BL-ANIM-03 · Assigning with no armature picked cancels with a warning
- status: pending
- review: keep
- pre: At least one action; the Skeleton picker empty (clear it via the 'x').
- steps:
  1. Clear the Active Armature picker, then click an action row.
- observe: Nothing is assigned and a warning appears ('no armature picked - pick one in the Skeleton panel'). With log level set to 'errors' the warning is suppressed.
- intent: With no rig picked, assignment cancels with a warning instead of guessing a scene armature.
- code: apps/blender/operators/selection.py (resolve_skeleton_target is None -> warn + cancel)

### BL-ANIM-04 · Clicking a stale action row cancels safely
- status: pending
- review: todo
- pre: An action exists that could be renamed or deleted between the panel drawing and your click.
- steps:
  1. Rename or delete the action via the Python console after the panel drew, then click the now-stale row.
- observe: Nothing is assigned and a warning appears ("action '<name>' not found").
- intent: If the action no longer exists when you click, the assignment cancels with a warning.
- code: apps/blender/operators/selection.py:113-116

## Atlas panel: pack / unpack / apply

### BL-ATLAS-SWEEP · Atlas readout inventory (visual pass)
- status: pending
- review: keep
- pre: Atlas subpanel expanded; vary the scene state to surface each read-out.
- observe: The subpanel shows one of four atlas read-outs ('no atlas linked in materials', 'packed atlas: <name>.atlas.png', 'source image: <name>', or '<name> (unsaved)'), a read-only pixels-per-unit echo (the editable field lives in Export), an 'Atlas packer' box with the Pack padding, Pack max size, and Power-of-two atlas fields, and a 'run Pack Atlas first' greyed hint where Apply will appear once a manifest exists.
- intent: Confirm the Atlas panel renders the four atlas read-outs, the three packer fields, and the Apply placeholder; field clamps and button behavior live in the named tests.
- code: apps/blender/panels/atlas.py:33-64,99

### BL-ATLAS-01 · Pack padding field
- status: pending
- review: keep
- steps:
  1. Set the Pack padding field.
- observe: The value accepts 0 to 64. Pack Atlas uses it as the gap (in pixels) left around each sprite in the packed image.
- intent: Pack padding sets the spacing around each sprite in the packed atlas.
- code: apps/blender/panels/atlas.py:54 (prop) -> properties/scene_props.py:447

### BL-ATLAS-02 · Pack max size field
- status: pending
- review: keep
- steps:
  1. Set the Pack max size field.
- observe: The value accepts 64 to 8192. If the sprites do not fit within this size, Pack fails with a 'do not fit' message.
- intent: Pack max size caps the atlas dimension; Pack fails if the sprites cannot fit within it.
- code: apps/blender/panels/atlas.py:55 (prop) -> properties/scene_props.py:454

### BL-ATLAS-03 · Power-of-two atlas checkbox
- status: pending
- review: keep
- steps:
  1. Toggle Power-of-two atlas and run Pack.
- observe: When on, the packed atlas dimensions are rounded up to the next power of two. It is off by default.
- intent: Power-of-two rounds the atlas dimensions up to the next power of two.
- code: apps/blender/panels/atlas.py:56 (prop) -> properties/scene_props.py:461

### BL-ATLAS-04 · Pack Atlas is disabled in Edit Mode or on an unsaved file
- status: pending
- review: keep
- pre: An unsaved file, or Edit Mode.
- steps:
  1. On a never-saved file, or in Edit Mode, look at the Pack Atlas button.
- observe: The Pack Atlas button is greyed out.
- intent: Pack requires Object Mode and a saved blend, so it is disabled otherwise.
- code: apps/blender/operators/atlas_pack/pack.py:48-51

### BL-ATLAS-05 · Pack Atlas warns when there are no eligible sprites
- status: pending
- review: keep
- pre: Saved file, Object Mode, but no mesh has a source image (or all are excluded from the atlas).
- steps:
  1. Remove or exclude all textured meshes, then click Pack Atlas.
- observe: A warning appears ('no sprite meshes with source images found') and nothing is written.
- intent: Pack warns and writes nothing when there are no textured sprites to pack.
- code: apps/blender/operators/atlas_pack/pack.py:68-72

### BL-ATLAS-06 · Pack Atlas fails when sprites overflow the max size
- status: pending
- review: keep
- pre: Saved, Object Mode, with total sprite area exceeding the max size squared.
- steps:
  1. Set Pack max size very low (e.g. 64) with large sprites, then click Pack Atlas.
- observe: An error appears ('pack failed - N sprite(s) do not fit') and nothing is written.
- intent: Pack fails cleanly when the sprites cannot fit the max-size atlas.
- code: apps/blender/operators/atlas_pack/pack.py:82-88

### BL-ATLAS-07 · Apply is disabled without a manifest or in Edit Mode
- status: pending
- review: keep
- pre: Edit Mode, or a missing manifest, or an unsaved file.
- steps:
  1. Delete the .atlas.json or enter Edit Mode, then look at the Apply button.
- observe: The Apply button is absent (when the manifest is missing) or greyed (in Edit Mode or unsaved).
- intent: Apply requires Object Mode and an existing pack manifest.
- code: apps/blender/operators/atlas_pack/apply.py:44-52

### BL-ATLAS-08 · Apply errors when the manifest disappears before running
- status: pending
- review: keep
- pre: The manifest existed when the panel drew but is deleted before you click Apply.
- steps:
  1. Externally delete the .atlas.json, then click Apply.
- observe: An error appears ('manifest not found - <name>.atlas.json') and nothing changes.
- intent: Apply errors cleanly if the manifest is gone by the time it runs.
- code: apps/blender/operators/atlas_pack/apply.py:59-62

### BL-ATLAS-09 · Apply links non-isolated sprites to the shared atlas material
- status: pending
- review: keep
- pre: Apply ran with at least one sprite whose 'Isolated material' is off.
- steps:
  1. After Apply, check the material on a non-isolated sprite and the material list.
- observe: A material named 'Proscenio.PackedAtlas' exists (built from the packed atlas image), and every non-isolated sprite uses it.
- intent: Apply points all non-isolated sprites at one shared packed-atlas material.
- code: apps/blender/operators/atlas_pack/apply.py:70,188-204,247-250

### BL-ATLAS-10 · Apply keeps an isolated sprite's own material
- status: pending
- review: keep
- pre: A sprite with 'Isolated material' on; Apply prerequisites met.
- steps:
  1. Turn on Isolated material on a sprite (Element panel), then Pack and Apply.
- observe: That sprite keeps its own material, but its texture is swapped to the packed atlas image instead of being relinked to the shared material.
- intent: Isolated material lets a sprite keep its own shader while still drawing from the packed atlas (GAP-1).
- code: apps/blender/operators/atlas_pack/apply.py:243-245 -> _paths.py:61 swap_image_in_materials

### BL-ATLAS-11 · Apply rewrites a sprite's region to its packed slot
- status: pending
- review: keep
- pre: A sprite-type object in the manifest; Apply run.
- steps:
  1. Apply with a sprite-type object, then check its region settings.
- observe: The sprite's region mode is set to Manual and its X/Y/W/H now address its slot in the packed atlas (the slot rectangle as fractions of the atlas).
- intent: A packed sprite still slices correctly because Apply repoints its region at the packed slot.
- code: apps/blender/operators/atlas_pack/apply.py:168-186

### BL-ATLAS-12 · Re-Apply guards against cumulative UV drift
- status: pending
- review: keep
- pre: A sprite that already has a snapshot from a prior Apply.
- steps:
  1. Apply, then Apply again; if the saved UV snapshot was renamed or mismatched, read the report.
- observe: With a healthy snapshot, the original UVs are restored first and then re-mapped, so re-applying does not shrink the slot over time. With a broken snapshot, that sprite is skipped with a warning ('pre-pack UV snapshot missing or out of sync') and the summary notes the skip.
- intent: Re-applying restores the original UVs first so repeated packs do not cumulatively shrink the slot.
- code: apps/blender/operators/atlas_pack/apply.py:79-81,97-155

### BL-ATLAS-13 · Apply skips a mesh with no UV layer
- status: pending
- review: keep
- pre: A non-sprite mesh in the manifest that has no active UV layer.
- steps:
  1. Apply with a UV-less non-sprite mesh present in the manifest.
- observe: That mesh is skipped and the report notes 'skipped N (no UV layer)'. A sprite-type object is not skipped this way.
- intent: A mesh without UV data is skipped during the atlas rewrite.
- code: apps/blender/operators/atlas_pack/apply.py:82-84,206-216

### BL-ATLAS-14 · Apply is undoable
- status: pending
- review: keep
- pre: Apply just run.
- steps:
  1. After Apply, press Ctrl+Z.
- observe: Ctrl+Z reverts the data changes from Apply (UVs, material assignment, region settings). The packed PNG and JSON on disk remain.
- intent: Apply can be undone with Ctrl+Z, reverting the in-file changes (not the on-disk pack files).
- code: apps/blender/operators/atlas_pack/apply.py:42

### BL-ATLAS-15 · Unpack is hidden until an Apply created a snapshot
- status: pending
- review: keep
- pre: No mesh has a pre-pack snapshot.
- steps:
  1. On a packed-but-not-applied (or freshly unpacked) file, expand the Atlas subpanel.
- observe: No Unpack Atlas button is shown. (It would also be blocked in Edit Mode.)
- intent: Unpack only appears after an Apply has created a restore snapshot.
- code: apps/blender/panels/atlas.py:65 -> operators/atlas_pack/unpack.py:49-52

### BL-ATLAS-16 · Unpack restores UVs only when the original material is gone
- status: pending
- review: keep
- pre: Apply ran, then the original material was deleted before Unpack.
- steps:
  1. Apply, delete the original material, then Unpack.
- observe: A per-object warning appears ('original material ... not found; restored UVs only') and the summary counts how many were UV-only restores.
- intent: Unpack restores the original material where it can, and falls back to UVs-only when the original was deleted.
- code: apps/blender/operators/atlas_pack/unpack.py:107-124,68-72

### BL-ATLAS-17 · Unpack rescues a renamed material via its marker
- status: pending
- review: keep
- pre: Apply ran, then the original material was renamed before Unpack.
- steps:
  1. Apply, rename the original material, then Unpack.
- observe: Even though the name no longer matches, Unpack finds the renamed material by its stamped marker and restores the sprite to it, counted as a full (non-partial) restore.
- intent: A material renamed between Apply and Unpack is still restored via its origin marker.
- code: apps/blender/operators/atlas_pack/unpack.py:21-33,113-117

### BL-ATLAS-18 · Unpack restores a sprite's region
- status: pending
- review: keep
- pre: Apply ran on a sprite-type object (its region was changed to Manual).
- steps:
  1. Apply a sprite, then Unpack, then check its region settings.
- observe: The region mode and X/Y/W/H are restored to their pre-Apply values.
- intent: Unpack restores the sprite's original region settings.
- code: apps/blender/operators/atlas_pack/unpack.py:136-145

### BL-ATLAS-19 · Unpack snapshot survives save/reload and is undoable
- status: pending
- review: keep
- pre: Apply ran, file saved.
- steps:
  1. Apply, save, reopen the .blend, and Unpack. Separately, Unpack then press Ctrl+Z.
- observe: The restore snapshot persists across save and reload, so Unpack still works after reopening. Unpack itself can be undone with Ctrl+Z.
- intent: The restore snapshot survives save/reload, and Unpack is undoable (Ctrl+Z does not revert the original Apply).
- code: apps/blender/operators/atlas_pack/unpack.py:47

## Pipeline > Validate subpanel (export-blocking issues list)

### BL-VALID-SWEEP · Validate subpanel inventory (visual pass)
- status: regressed
- review: keep
- pre: Pipeline panel expanded, the Validate subpanel (between Import and Export) expanded; surface each state (before Validate, a clean scene, and a scene with issues).
- observe: Validate is now a subpanel of Pipeline (Import / Validate / Export). It shows the Validate button, a 'run Validate to see issues' label before the first run, a 'no issues - ready to export' label on a clean scene, and issue rows otherwise (object rows render '[Name] message', scene-wide rows render a plain non-clickable label, with errors tinted red and warnings plain).
- intent: Confirm the Validate subpanel renders the button, the before/clean labels, and the issue rows under Pipeline; the Validate run and clickable rows live in the named tests.
- code: apps/blender/panels/validation.py:30-43; _helpers.py:142-150

### BL-VALID-01 · Validate lists export-blocking issues
- status: pending
- review: keep
- pre: A populated scene with the Proscenio scene properties registered.
- steps:
  1. Click Validate.
- observe: The issue list is rebuilt and a summary reports the count ('N error(s), M warning(s)', or 'validation OK' when clean). Issue rows appear below.
- intent: Validate scans the scene and lists problems that would block an export (e.g. missing armature for weighted sprites, dead bone references, missing atlas files, sprite meshes without a frame grid).
- code: apps/blender/panels/validation.py:30 -> export_flow.py:121 (PROSCENIO_OT_validate_export.execute:132)

### BL-VALID-02 · Clicking an issue row selects, reveals, and frames the offending object
- status: regressed
- review: keep
- pre: Validate has been run and produced at least one object-scoped issue. For step 2, hide the offending object (eye icon / H) before clicking.
- steps:
  1. Run Validate, then click a row showing '[Name] message'.
  2. Hide the offending object, then click its issue row again.
- observe: That object becomes the only selected and active object, and the viewport frames it. A hidden object is revealed (hide and hide-in-viewport cleared) before selecting. Error rows show in red, warnings plain. If the named object no longer exists, a warning appears and the selection is unchanged; an object outside the active view layer warns instead of raising a traceback.
- intent: Clicking an object-scoped issue row jumps your selection to the offending object, revealing and framing it so the fix is one click away.
- code: apps/blender/panels/validation.py:43 -> _helpers.py (draw_issue_row) -> selection.py (PROSCENIO_OT_select_issue_object + _frame_selected)
- note: spec 036 PR3 added the unhide + frame + view-layer guard; re-walk the reveal-hidden and out-of-view-layer paths. Deferred by the user at the post-merge walk - still needs a GUI pass.

## Pipeline panel: import manifest + validate + export/re-export .proscenio

### BL-PIPE-SWEEP · Pipeline panel inventory (visual pass)
- status: regressed
- review: keep
- pre: Pipeline panel expanded with the scene properties registered.
- observe: Pipeline is the FIRST panel in the tab and opens collapsed. It groups three subpanels in order: Import, Validate, Export. The Export subpanel leads with the 'Exports: <name> (picked / first in scene)' read-out (moved here from Skeleton), then the Last export path field, the Pixels-per-unit field, and the Bundle textures checkbox. The Import dialog and the Validate behavior are covered in the named tests below.
- intent: Confirm the Pipeline panel is first, opens collapsed, and renders its Import/Validate/Export structure incl. the export-target read-out; field semantics live in the named tests.
- code: apps/blender/panels/pipeline.py; apps/blender/panels/validation.py
- note: panel-restructure: Pipeline moved to first + DEFAULT_CLOSED, absorbed the Validate subpanel, and gained the 'Exports:' read-out in Export.

### BL-PIPE-IMPORT-01 · Import Placement (Landed vs Centered)
- status: pending
- review: keep
- steps:
  1. In the import file dialog, set Placement to Landed, then to Centered, and import.
- observe: Landed shifts the imported figure so its lowest point sits on the ground (world Z 0); Centered keeps it centred on the canvas at the world origin. The default is Landed.
- intent: Placement chooses whether the imported figure lands on the ground or stays centred (undocumented - GAP-3).
- code: apps/blender/operators/import_photoshop.py:40-60 -> apps/blender/importers/photoshop/__init__.py:89-90 (_anchor_meshes_at_feet)

### BL-PIPE-IMPORT-02 · Import Root Bone Name
- status: pending
- review: keep
- steps:
  1. In the import file dialog, type a Root Bone Name and import.
- observe: The single bone in the created stub armature takes the name you typed. Leaving it blank falls back to 'root'.
- intent: Root Bone Name names the imported stub armature's bone (undocumented - GAP-4).
- code: apps/blender/operators/import_photoshop.py:62-70 -> apps/blender/importers/photoshop/__init__.py:70-73

### BL-PIPE-IMPORT-03 · Imported cutout shows its authored color
- status: pending
- review: keep
- pre: A PSD manifest + PNGs whose art has a saturated flat-colored region whose color you can sample (e.g. examples/authored/firebound_guy). A scene on the default AgX view transform is fine - the import switches it.
- steps:
  1. Import the manifest (Pipeline > Import).
  2. In a Material Preview or Rendered viewport, sample the color of a flat-colored region on an imported plane and compare it to the source PNG.
  3. Open an imported plane's material in the Shader Editor and read the image texture's Color Space.
- observe: The imported plane shows its authored color matching the source PNG (no AgX wash, no Principled IOR sheen). The scene's View Transform reads Standard (not AgX). The material is an unlit Emission gated by the texture alpha through a Mix Shader (Transparent / Emission) with no Principled BSDF, and the image texture's Color Space reads sRGB.
- intent: Imported flat 2D cutouts display their authored color - unlit Emission + Standard view transform + sRGB texture decode - instead of the washed-out lit/AgX look.
- code: apps/blender/importers/photoshop/planes.py (_attach_material) -> apps/blender/importers/photoshop/__init__.py (_apply_flat_color_management)
- note: asserted headless by apps/blender/tests/operators/test_flat_material.py; rationale - Godot reads PNG bytes as sRGB (color is sRGB end to end).

### BL-PIPE-IMPORT-04 · Import Root Bone Length
- status: pending
- review: todo
- pre: A PSD manifest + PNGs. A second import of the same manifest into the same scene available for the re-import check.
- steps:
  1. In the import file dialog, set Root Bone Length (default 1.0) and import; select the stub armature's root bone and read its length (N-panel Item, or Edit mode).
  2. Re-import the same manifest with a different Root Bone Length and read the root bone length again.
- observe: The root bone of a freshly built stub armature takes the length you set (default 1.0 unit, not the old 0.05). On a re-import the existing root armature is reused in place, so its bone keeps the original length - the new value does not retro-resize an already-imported rig. The field rejects a zero/negative length (clamped to a tiny positive minimum).
- intent: Root Bone Length sizes the importer's stub root bone (default 1 unit, configurable per import); a re-import never resizes an existing root because build_root_armature reuses it.
- code: apps/blender/operators/import_photoshop.py (root_bone_length FloatProperty) -> apps/blender/importers/photoshop/__init__.py (import_manifest root_bone_length) -> apps/blender/importers/photoshop/armature.py (build_root_armature length)
- note: quick-armature-root-bone. Threading + reuse-keeps-length asserted headless by apps/blender/tests/operators/test_root_bone_length.py; this is the import-dialog field + re-import GUI walk.

### BL-PIPE-EXPORT-01 · Last export path is sticky and enables Re-export
- status: pending
- review: keep
- steps:
  1. Export once, then look at the Last export path field; edit it and re-export.
- observe: The field holds the last export destination, and once it is set a Re-export button appears. The value persists across save and reload, and editing it changes where Re-export writes.
- intent: The export path is remembered so Re-export skips the file dialog, and is saved with the blend so the document carries its export target.
- code: apps/blender/panels/pipeline.py:88 -> apps/blender/properties/scene_props.py:403-411

### BL-PIPE-EXPORT-02 · Pixels per unit (scene field)
- status: todo
- review: keep
- steps:
  1. Change the Pixels-per-unit field, run the first Export, and read the written pixels_per_unit.
  2. Change it again and Re-export.
- observe: The scene pixels-per-unit value updates (minimum just above 0). BOTH the first Export and Re-export use it as the world-to-pixel ratio (the export dialog no longer carries its own field). It is synced from the manifest on import, which now warns when the imported value differs from the current scene value.
- intent: Pixels per unit sets the Blender-world-to-Godot-pixel ratio used by both export and re-export (default 100).
- code: apps/blender/panels/pipeline.py:89 -> apps/blender/operators/export_flow.py (execute reads scene_props.pixels_per_unit)

### BL-PIPE-EXPORT-03 · Bundle textures copies textures beside the export
- status: pending
- review: keep
- steps:
  1. Turn Bundle textures on and export; then turn it off and export.
- observe: With it on, every referenced texture is copied next to the .proscenio file and the success report adds 'bundled N texture(s)' (noting any missing on disk). With it off, no textures are copied and there is no suffix.
- intent: Bundle textures copies the referenced textures alongside the exported .proscenio (undocumented).
- code: apps/blender/panels/pipeline.py:90 -> apps/blender/properties/scene_props.py:418-426 -> apps/blender/operators/export_flow.py:97-118

## Helpers panel (viewport authoring aids outside export)

### BL-HELP-01 · Preview Camera drops an orthographic front camera
- status: pending
- review: keep
- pre: A Proscenio scene open. No specific active object or mode required.
- steps:
  1. Expand Helpers and click Preview Camera.
  2. Click it again to test the update path, and press Numpad 0 to look through it.
- observe: The first click creates an orthographic front camera ('Proscenio.PreviewCam'), makes it the scene camera and the sole selection, and reports its creation; the ortho scale is set so the view matches the export framing. Clicking again reuses the same camera and recomputes its scale. It is undoable.
- intent: Preview Camera drops an orthographic front camera framed the way the Godot importer expects, so the viewport matches the runtime framing.
- code: apps/blender/panels/helpers.py (Preview Camera button); operator at apps/blender/operators/armature/authoring_camera.py:16-53

### BL-HELP-02 · Re-space Planes re-applies the Y Location spacing
- status: pending
- review: keep
- pre: A scene with a couple of Proscenio plane elements that carry a draw order; one of them dragged off its layer in Y (so its Element-panel validation warns).
- steps:
  1. Expand Helpers and click Re-space Planes.
- observe: Every Proscenio element's Y snaps to its draw-order layer (order times the Y Location spacing preference); the dragged plane returns to its layer and its divergence warning clears. Slot-attached meshes are left where the slot puts them. The operator reports how many planes it re-spaced and is undoable. The exported draw order does not change (it reads the integer, not the Y).
- intent: Re-space Planes applies a changed Y Location spacing to the whole scene and snaps any plane dragged off its layer back, so the viewport stack stays consistent with the authored order.
- code: apps/blender/operators/helpers.py (PROSCENIO_OT_respace_planes); pinned by apps/blender/tests/operators/test_draw_order.py
- note: draw-order-authoring.

### BL-HELP-03 · 3D-view clip range is editable in the panel
- status: pending
- review: keep
- pre: A 3D viewport with the Helpers panel expanded.
- steps:
  1. Change Clip Start and Clip End under the '3D View Clip' label.
- observe: The two fields edit the active 3D viewport's near/far clip directly (the same values as the viewport's View properties). They are the viewport's own settings, so they apply to that 3D view and are not exported.
- intent: The clip range lives in Helpers so a small Y Location spacing (tightly stacked planes) can be made to register in the depth buffer without leaving the panel.
- code: apps/blender/panels/helpers.py (context.space_data clip_start / clip_end)
- note: draw-order-authoring.

## Help system + Addon Preferences

### BL-HELP-PANEL-SWEEP · About footer inventory (visual pass)
- status: regressed
- review: keep
- pre: About panel (the footer, last in the tab) expanded.
- observe: There is no standalone Help panel anymore (it clashed with Helpers). The About footer shows the version line + repo-link icon, an 'Open help' button (opens the pipeline-overview popup), and - with Debug mode on - a 'Run Smoke Test' button below it. With Debug mode off only Open help shows.
- intent: Confirm Open help + the debug smoke test live in the About footer and no separate Help panel exists.
- code: apps/blender/panels/__init__.py (PROSCENIO_PT_main)
- note: panel-restructure removed the Help panel and folded Open help + the smoke test into About.

### BL-HELP-AFFORD · Re-wired per-section help buttons resolve
- status: pending
- review: keep
- pre: A sprite element active (for step 1); Pose Mode on the picked armature (for step 2).
- steps:
  1. In Active Sprite, expand the Material Preview sub-box and click its '?' button.
  2. In Skeleton > Pose Mode, click the '?' beside Save Pose to Library.
- observe: Each '?' opens a help popup for that specific feature - the Material Preview '?' explains the sprite-frame preview shader (its caveats), and the Save Pose '?' explains the pose-library asset flow - rather than the generic panel topic. Neither shows 'unknown help topic'.
- intent: The two help topics the #96 restructure orphaned (sprite_frame_preview, pose_library) have working in-UI entry points again.
- code: apps/blender/panels/_draw_sprite.py (Material Preview sub-box header); apps/blender/panels/skeleton.py (draw_help_button on Save Pose)
- note: spec 036 PR1 re-wired both; a reverse-coverage pytest now pins every topic to a panel/operator caller.

### BL-PREFS-SWEEP · Addon Preferences inventory (visual pass)
- status: pending
- review: keep
- pre: Addon Preferences open.
- observe: The preferences show an 'Authoring' box with a 'Y Location spacing' number field (default 0.01), and a 'Developer' box grouping a Log level dropdown (errors / info / debug) and a Debug mode checkbox.
- intent: Confirm the addon preferences render the Authoring box with the Y Location spacing field and the Developer box with the Log level and Debug mode controls; the spacing's effect lives in BL-ELEM-ROOT-03 / BL-HELP-02, the Developer effects in BL-DIAG-02 and BL-CHROME-08.
- code: apps/blender/addon_prefs.py (ProscenioAddonPreferences.draw, y_location_spacing)
- note: draw-order-authoring added the Authoring box + Y Location spacing.

### BL-DIAG-01 · Run Smoke Test prints a gated sanity check
- status: regressed
- review: keep
- pre: Debug mode on so the About footer shows the Run Smoke Test button.
- steps:
  1. Open the About panel (footer) and click Run Smoke Test.
- observe: A 'Proscenio smoke test OK' message appears in the info area and the system console, and the operator finishes successfully. With Debug mode off the button is absent.
- intent: Run Smoke Test confirms the addon is registered and dispatching operators correctly; it lives in the About footer and reports through the gated reporter.
- code: apps/blender/panels/__init__.py (About) -> apps/blender/operators/help_dispatch.py (PROSCENIO_OT_smoke_test, report_info)
- note: panel-restructure moved the smoke test from the Help panel into the About footer (still debug-only, still report_info).

### BL-DIAG-02 · Log level controls how much operators report
- status: pending
- review: keep
- pre: Addon Preferences open.
- steps:
  1. Change the Log level dropdown between Errors only, Info, and Debug.
- observe: 'Errors only' suppresses the info and warning messages, 'Debug' adds extra per-item trace lines, and 'Info' (the default) is in between. The choice persists across restart.
- intent: Log level controls how verbose the operators' info-log reporting is (Errors only / Info / Debug).
- code: apps/blender/addon_prefs.py:29-48 (update=_on_log_level_update -> report.set_min_level)
