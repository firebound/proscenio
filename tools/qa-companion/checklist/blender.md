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
- status: pass
- review: keep
- pre: Any header with a '?' help button.
- steps:
  1. Click a '?' icon and read the popup.
  2. If the popup has an 'Open online docs' button or a 'See also' web link, click it.
- observe: A help popup opens with a title, a summary line, and section headings with body text. 'Open online docs' opens the doc page in a browser; 'See also' web links are clickable buttons, and non-link references show as plain indented labels.
- intent: The help popup renders its title, sections, links, and the online-docs button correctly.
- code: apps/blender/operators/help_dispatch.py:64-97

### BL-CHROME-05 · Each panel's '?' opens the matching help topic
- status: pass
- review: keep
- pre: Each panel/subpanel header that has a '?' button.
- steps:
  1. Click '?' on each panel and confirm the popup title matches that panel.
- observe: Every header opens the help topic for its own panel (Outliner, Active Element, Slots, Skeleton, Mesh Generation, Weight Paint, Animation, Atlas, Validation, Pipeline, Helpers, and their subpanels). Known defect: the Diagnostics and Help headers both open the generic 'pipeline overview' topic instead of their own.
- intent: Each panel routes its '?' to the correct help topic; this also surfaces the Diagnostics/Help wrong-topic defect.
- code: apps/blender/panels/_helpers.py:84-85; apps/blender/operators/help_dispatch.py:50-97; apps/blender/panels/diagnostics.py:29; apps/blender/panels/help.py:44

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
- status: pass
- review: keep
- pre: The addon Preferences open.
- steps:
  1. Turn 'Debug mode' ON in addon prefs, then redraw the N-panel.
  2. Turn it OFF and redraw again.
- observe: With Debug mode ON the Diagnostics panel and the automesh Debug Pipeline subpanel appear; with it OFF both disappear. The change shows up on the next panel redraw, not instantly.
- intent: The debug-only developer surface is hidden until Debug mode is enabled.
- code: apps/blender/addon_prefs.py:50-58,67-80; apps/blender/panels/diagnostics.py:24-26; apps/blender/panels/mesh_generation.py:135

### BL-CHROME-09 · Header icons drop and titles truncate when the N-panel is narrow
- status: todo
- review: keep
- pre: Any Proscenio panel; drag the N-panel divider to narrow it.
- steps:
  1. Narrow the N-panel until the headers get cramped.
- observe: As the panel narrows, the right-side status badge + '?' help icons drop out of every Proscenio panel header (rather than overlapping the title), and the native bl_label titles truncate (lose characters) like Blender's own. The Skeleton header (a custom draw_header) instead drops its '<name>' suffix and keeps the base 'Skeleton' when narrow. Widening brings the icons and the name back.
- intent: Narrow headers shed their extra icons; native titles truncate and the Skeleton header drops its name suffix, matching Blender's narrow-header behaviour; nothing overlaps.
- code: apps/blender/panels/_helpers.py draw_subpanel_header (_HEADER_ICONS_MIN_WIDTH gate)

## Outliner panel

### BL-OUTLN-SWEEP · Outliner panel inventory (visual pass)
- status: pass
- review: keep
- pre: Outliner subpanel expanded, with a scene that has at least one slot, attachment, sprite mesh, and armature.
- observe: The Outliner shows, in order: a favorites-only toggle (star icon), and the object list (up to 8 rows). Text search is Blender's native 'Filter by Name' under the list's expand arrows - there is no separate Proscenio search field. Each row is labeled by category: slots as '[slot] <name>', attachments indented as '-> <name>', sprite meshes as '<name>' (with '@ <bone>' when bone-parented), and armatures as '[arm] <name>'. Cameras, lights, and other objects do not appear.
- intent: Confirm the Outliner renders its favorites toggle and category-labeled list; behavior lives in the named tests.
- code: apps/blender/panels/outliner.py:40-69,118-137

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

### BL-OUTLN-03 · List is sorted by category then name
- status: pass
- review: keep
- observe: Rows are grouped by category and then alphabetically: slots first (with attachments indented under them), then sprite meshes, then armatures last. Cameras, lights, and other objects are not listed.
- intent: The list always shows a fixed category order (slots, then sprites, then armatures) regardless of scene order.
- code: apps/blender/panels/outliner.py:150-158 (template_list) + draw_item:40-84

### BL-OUTLN-04 · Native 'Filter by Name' is the only search
- status: pass
- review: keep
- steps:
  1. Confirm the panel header shows only the favorites-only star toggle - no separate Proscenio search text field.
  2. Type into Blender's native 'Filter by Name' field (the expand arrows on the list).
- observe: There is no Proscenio search box in the header; the native 'Filter by Name' is the single search and it filters the list as you type.
- intent: Spec 043 removed the redundant Proscenio search bar; only Blender's built-in list filter remains (no precedence to reconcile).
- code: apps/blender/panels/outliner.py filter_items (self.filter_name only)

### BL-OUTLN-05 · Custom sort overrides Blender's native sort
- status: pass
- review: keep
- observe: The list always shows the Proscenio category-then-name order, even with the native sort toggles open. The native invert-filter toggle can still flip which rows are shown.
- intent: The custom category-then-name order overrides Blender's native list sort.
- code: apps/blender/panels/outliner.py:150-158 (template_list) + filter_items:120-124

### BL-OUTLN-06 · Active row highlight follows click and viewport selection
- status: todo
- review: keep
- pre: a scene with several Proscenio objects; type something into the native 'Filter by Name' so the list is sorted/filtered (not raw scene order).
- steps:
  1. Click different rows in the list.
  2. Now select one of those objects directly in the 3D viewport.
- observe: The highlighted active row follows whichever object you last clicked, landing on the correct visual row even with the list filtered/sorted. Selecting an object in the viewport moves the highlight to that object's row too. Selecting a non-Proscenio object (camera, light) leaves the highlight where it was.
- intent: The active-row highlight stays in sync with the active object in both directions - clicking a row and selecting in the viewport (spec 043).
- code: apps/blender/properties/_handlers.py sync_outliner_to_active_object + core/outliner_view.py source_index_for_name + selection.py:153-167

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
- status: todo
- review: keep
- pre: Outliner expanded with a Proscenio object listed (e.g. a Quick Armature rig).
- steps:
  1. Select the object and delete it (X / Delete), or undo its creation with Ctrl+Z.
- observe: The row disappears from the Outliner immediately - a deleted/undone object that lingers in bpy.data is no longer in the view layer, so it is filtered out. (It does not stay as a ghost row that warns 'not in the current view layer' on click.)
- intent: The list reflects the real scene; objects removed from the view layer drop out.
- code: apps/blender/panels/outliner.py filter_items (view-layer membership) + core/outliner_view.py row_visible

## Element panel (Active Sprite / Active Mesh, type, region, drive-from-bone, reproject UV)

### BL-ELEM-ROOT-SWEEP · Element panel root inventory (visual pass)
- status: pass
- review: keep
- pre: A mesh or sprite element active.
- observe: With a mesh or sprite active, the panel root shows an element-type dropdown (Mesh / Sprite). With nothing active it shows 'select a mesh or sprite element'. In Weight Paint mode the dropdown is greyed out with the label 'element type is locked in Weight Paint mode'. Any validation issues for the element render one row each; rows that name an object are clickable to select it.
- intent: Confirm the Element root renders the type dropdown, the empty-state and locked-state labels, and inline validation rows.
- code: apps/blender/panels/element.py:49-64; apps/blender/core/validation/active_element.py:9
- note: absorbs the old per-field root items; locked-mode behavior is BL-ELEM-ROOT-02.

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

### BL-ELEM-MESH-SWEEP · Active Mesh subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: A mesh element (type Mesh) active.
- observe: The Active Mesh subpanel shows a polygon/vertex-group count read-out ('<N> polygon(s), <M> vertex group(s)'), a Reproject UV button, an Isolated material checkbox, and an Exclude from atlas checkbox.
- intent: Confirm the Active Mesh subpanel renders its read-out, button, and two checkboxes; behavior lives in the named tests and atlas flows.
- code: apps/blender/panels/_draw_mesh.py:19-25
- note: Isolated material and Exclude from atlas behavior is covered in FLOW-ATLAS-01; Reproject behavior is BL-ELEM-MESH-01..02.

### BL-ELEM-MESH-01 · Reproject UV re-unwraps the mesh
- status: pass
- review: keep
- pre: A mesh element (type Mesh) selected in Object Mode.
- steps:
  1. With the mesh selected in Object Mode, open Active Mesh and click Reproject UV.
- observe: The mesh's UVs are re-unwrapped (Smart UV Project), and your selection and active object are left as they were. A confirmation names the mesh. The redo panel lets you tweak the Angle limit. The UVs may end up rotated or mirrored.
- intent: Reproject UV recomputes the mesh UVs so the texture lines up again after editing vertices.
- code: apps/blender/panels/_draw_mesh.py:23; apps/blender/operators/uv_authoring.py:22-80
- note: a projeção funciona, mas a utilidade da ferramenta não está clara.

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
- status: pass
- review: keep
- pre: A sprite element (type Sprite) active.
- observe: The Active Sprite subpanel shows the Horizontal frames, Vertical frames, and Frame fields, a Centered checkbox, the atlas/region/frame read-out labels ('atlas: not linked in material' when no image is linked, otherwise 'atlas: WxH px', 'region: WxH px', 'frame: WxH px'), and the Setup Preview and Remove Preview buttons.
- intent: Confirm the Active Sprite subpanel renders the grid fields, the centered toggle, the size read-outs, and the preview buttons; behavior lives in the named tests.
- code: apps/blender/panels/_draw_sprite.py:23-83
- note: absorbs the per-field sprite items; their behavior is the BL-ELEM-SPRITE-NN tests.

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

### BL-ELEM-SPRITE-02 · Frame sets the resting cell
- status: pass
- review: keep
- steps:
  1. In Active Sprite, set Frame to a cell index.
- observe: The field accepts a frame index (0 or higher) and keeps it.
- intent: Frame chooses which cell the sprite shows at rest pose; animation tracks override it at export.
- code: apps/blender/panels/_draw_sprite.py:25; object_props.py:95-103

### BL-ELEM-SPRITE-03 · Centered places the sprite on its origin
- status: pass
- review: keep
- steps:
  1. Toggle the Centered checkbox.
- observe: The checkbox toggles on and off (on by default).
- intent: Centered decides whether the exported Sprite2D is centred on its origin or has its top-left corner at the origin.
- code: apps/blender/panels/_draw_sprite.py:26; object_props.py:104-109

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
- status: pass
- review: keep
- pre: A sprite or mesh element active.
- observe: The Drive from Bone subpanel shows, in order: a Target dropdown (Frame index / Region X/Y/W/H); an Armature picker (armatures only); a Bone dropdown (with a hint when no armature is picked yet, or when the armature has no bones); an Axis dropdown; the In/Out range fields (or an Expression field when Advanced is on) with the Advanced toggle; a live 'Value' read-out; and the Drive from Bone button.
- intent: Confirm the subpanel renders all its controls; behavior lives in BL-ELEM-DRIVER-01..03.
- code: apps/blender/panels/_draw_driver_shortcut.py:21-59
- note: absorbs the old per-field driver items (target, armature, bone, axis, ranges, expression, advanced toggle, value read-out).

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

## Slots panel + slot operators

### BL-SLOTS-PARENT-SWEEP · Slots parent panel inventory (visual pass)
- status: pass
- review: keep
- pre: Slots panel expanded with at least one slot present.
- observe: When there are no slots it shows 'no slots yet - select meshes and Create Slot'. Otherwise each slot is a row with its name, a slot icon, and a badge counting its direct mesh children. A tip box explains the two ways to create a slot ('Pose Mode + active bone: slot anchored to the bone' and 'Object Mode + meshes: slot wraps the selection'). At the bottom is the Create Slot button.
- intent: Confirm the Slots parent panel renders the empty state, the per-slot rows with child counts, the tip box, and the Create Slot button.
- code: apps/blender/panels/slots.py:58-78

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
- code: apps/blender/panels/slots.py:62-70 -> operators/slot/select.py:36-44

### BL-SLOTS-ACTIVE-SWEEP · Active Slot subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: A slot Empty active with at least one mesh child.
- observe: The Active Slot subpanel shows a header naming the slot ('Slot "<name>"'), a line saying which bone it is parented to (or '(unparented)'), an 'Attachments (N):' heading with the child count, and one row per attachment showing the child's name and whether it is a mesh or a sprite. Alert rows appear for an unparented slot or a slot with no children.
- intent: Confirm the Active Slot subpanel renders the slot header, parent-bone line, attachment count and rows, and the alert rows; behavior lives in the named tests.
- code: apps/blender/panels/slots.py:115-151
- note: reescrito - antes estava ilegível ("incompreensível o que é pra observar").

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

### BL-SLOTS-ACTIVE-03 · Warning row when the slot has no children
- status: pass
- review: keep
- pre: A slot Empty active.
- observe: A red alert row, 'empty slot - add child meshes', appears only when the active slot has no mesh children.
- intent: An empty slot is flagged so you know to add attachments to it.
- code: apps/blender/panels/slots.py:132-135

### BL-SLOTS-ACTIVE-04 · Star marks the slot's default attachment
- status: pass
- review: keep
- pre: A slot Empty active with at least one mesh child.
- steps:
  1. Click the star at the left of an attachment row.
- observe: That attachment becomes the slot's default: its star fills and looks pressed while the others stay empty, and a confirmation names it. With no default set yet, the first attachment shows as the default. Naming a non-child reports a warning and changes nothing.
- intent: The star marks which attachment is visible when the scene loads (the default visible child). (default attachment exercised by FLOW-SLOTCYCLE-01)
- code: apps/blender/panels/slots.py:138-148 -> operators/slot/attachment.py:70-104

### BL-SLOTS-ACTIVE-05 · Add Selected Mesh attaches meshes to the slot
- status: pass
- review: keep
- pre: A slot Empty active and at least one other mesh also selected.
- steps:
  1. Select a slot Empty (active) plus a mesh, then click Add Selected Mesh.
- observe: Each selected mesh is re-parented into the slot Empty, keeping its on-screen position, and a confirmation reports how many were added. With no qualifying mesh selected, the button is greyed out.
- intent: Add Selected Mesh re-parents the selected meshes into the active slot as new attachments.
- code: apps/blender/panels/slots.py:159-165 -> operators/slot/attachment.py:40-67

### BL-SLOTS-ACTIVE-06 · Per-slot validation issue rows are clickable
- status: pass
- review: keep
- pre: A slot Empty active that has a validation issue (no children, broken default, child/bone mismatch, or transform keys on a child).
- observe: Validation issue rows render under the attachments; error rows tint red and warning rows stay plain. Rows that name an object are clickable and select that object when clicked.
- intent: Per-slot validation issues are surfaced and let you jump to the offending object.
- code: apps/blender/panels/slots.py:167-168 -> _helpers.py:127-150 -> validation/active_slot.py:15-35

## Skeleton panel: armature picker, bone list, pose helpers, Quick Armature, IK, authoring camera, pose library

### BL-SKEL-PARENT-SWEEP · Skeleton parent panel inventory (visual pass)
- status: pass
- review: keep
- pre: Skeleton panel expanded; toggle scene state (armature present or absent, rig picked or not) to surface each read-out.
- observe: The parent panel shows the Active Armature picker (armatures only) and an 'Exports: <name>' line that says '(picked)' when an armature is chosen or '(first in scene - no rig picked)' otherwise. When no armature exists it warns 'no Armature in scene - use Quick Armature below'. When armatures exist but none is picked it shows a boxed note 'no rig picked - skeleton ops will create a new Proscenio.QuickRig' with a 'Use existing instead' list.
- intent: Confirm the Skeleton parent panel renders the picker, the exports read-out, and the no-armature/no-rig notices; behavior lives in the named tests.
- code: apps/blender/panels/skeleton.py:94-112

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
- status: todo
- review: keep
- pre: A rig picked.
- observe: The subpanel is titled 'Active Armature' (was 'Armature'); the Skeleton parent panel header reads 'Skeleton: <name>' with the picked rig at a normal width, dropping to just 'Skeleton' when the N-panel is narrowed (the name disappears, the base title stays). The subpanel body shows the bone count ('N bone(s)') and a read-only bone list where each bone name is left-aligned and indented by its depth (the indent is now visible - names were centered before), and tagged 'connected' or 'disconnected' (a parented child not connected to its parent) and/or 'relative' on the right where those flags apply.
- intent: Confirm the renamed subpanel, the 'Skeleton: <name>' header that drops the name when narrow, the bone-count body, and the connected/disconnected/relative flags; behavior lives in the named test.
- code: apps/blender/panels/skeleton.py:25-65,148-158

### BL-SKEL-ARMATURE-01 · Clicking a bone selects it in the viewport
- status: pass
- review: keep
- pre: A rig picked with bones; a bone row visible.
- steps:
  1. Click a bone name in the bone list.
- observe: The armature is selected and that bone becomes active. In Pose mode only that pose bone is selected. A missing armature or bone reports a warning and changes nothing.
- intent: Clicking a bone in the list selects it in the viewport.
- code: apps/blender/panels/skeleton.py:52-58 -> selection.py:62-93

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

### BL-SKEL-POSE-02 · Toggle IK adds and removes a test IK constraint
- status: pending
- review: todo
- pre: In Pose mode with an active pose bone.
- steps:
  1. Select a pose bone and click Toggle IK, then click it again.
- observe: The first click adds a control bone at the chain tip and an IK constraint pointing at it. The second click removes both.
- intent: Toggle IK adds or removes a test IK constraint on the selected chain (export consequence is GAP-IK).
- code: apps/blender/panels/skeleton.py:181 -> authoring_ik.py:73-128

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
- status: pass
- review: keep
- pre: Quick Armature subpanel expanded.
- observe: The subpanel shows the Quick Armature launch button and four option fields that each keep their value: Lock to Front Orthographic, Default = chain connected, Bone name prefix, and Snap increment.
- intent: Confirm the Quick Armature subpanel renders its four options and they persist; the modal behaviour is BL-SKEL-QUICKARM-01.
- code: apps/blender/panels/skeleton.py:217-220 -> scene_props.py:29-67

### BL-SKEL-QUICKARM-01 · Quick Armature modal walk (consolidated)
- status: todo
- review: keep
- pre: The mouse is over a 3D viewport; the Quick Armature subpanel is open.
- steps:
  1. Click Quick Armature to start. It creates or reuses the QuickRig target, remembers your view and selection, optionally snaps to Front Ortho, and shows the preview and cheat-sheet overlays.
  2. Draw a bone: press, drag, and release the left mouse button inside the viewport. A bone is created (its head snaps to the previous bone's tail when chaining); a too-short drag is skipped with a message.
  3. Hold Shift while dragging to flip between chaining and starting a new root; the preview tints to show the unparented mode.
  4. Hold Alt while dragging to parent to the previous bone but start the new bone at the cursor; a dashed link line shows the disconnected parent.
  5. Press X then Z to lock drawing to the X or Z axis (press again to clear); a coloured guideline shows the locked axis.
  6. Hold Ctrl while drawing to snap the bone ends to the grid increment; the preview follows the snapped point.
  7. Press Ctrl+Z to undo the last bone you drew, Ctrl+Shift+Z to redo it; undoing or redoing past the ends reports there is nothing to do.
  8. Press Enter to finish (the status-bar hint reads 'finish'): the overlays clear, your view and selection are restored, and a confirmation reports how many bones you authored.
  9. Press Esc or right-click: with nothing drawn the hint reads 'cancel (discards empty rig)' and it removes the auto-created empty rig; once a bone is authored the hint reads 'exit (keeps bones)' and the bones survive (labels-only - Esc is not destructive). Your view and selection are restored either way.
  10. The redo panel's 'Lock to Front Orthographic' option, when on, snaps to Front Ortho on launch and restores your prior view on exit; off leaves the view alone.
- observe: Each chord behaves as its step describes; the live preview overlay tracks the active chord (different tints for chaining, unparented, and disconnected, plus an 'outside canvas' warning when the cursor leaves the viewport). The chord cheat-sheet shows on the bottom status bar only - the 3D viewport header no longer carries a duplicate strip (spec 045), and after exiting + reopening the file no leftover strip lingers. The confirm / exit hints differ ('finish' vs 'cancel'/'exit') and the Esc hint changes once a bone is authored.
- intent: One session covers launch, the draw/chain/disconnect chords, axis lock, grid snap, in-modal undo/redo, finish, cancel, the front-ortho option, the live overlay, and the status-bar-only cheat-sheet with dynamic finish/exit hints.
- code: apps/blender/panels/skeleton.py:212 -> apps/blender/operators/armature/quick_armature.py (modal + _exit + _draw_statusbar_quick_armature); _overlay.py:47-167; _status_bar.py emit_chord_layout

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
- status: pass
- review: keep
- pre: Mesh Generation panel expanded; switch the active object between a mesh, a sprite, and nothing to surface each guard.
- observe: With no mesh active it shows 'select a mesh to generate or edit'. With a sprite active it shows 'mesh tools are mesh-only (this is a sprite)' plus a hint to parent the sprite to a bone, and hides the subpanels. With a mesh active it shows a target read-out ('Target: Skeleton <armature>' or 'Target: Skeleton (none - pick a rig there)') and the Interior Mode selector (Simple / Dense).
- intent: Confirm the parent panel renders the empty-state and sprite guards, the picker read-out, and the Interior Mode selector; behavior lives in the named tests.
- code: apps/blender/panels/mesh_generation.py:63-74 -> _helpers.py:111

### BL-MESH-ALPHA-SWEEP · Automesh-from-Alpha subpanel inventory (visual pass)
- status: pass
- review: keep
- pre: A mesh element active; Automesh from Alpha subpanel expanded.
- observe: The subpanel shows the trace settings (Trace resolution, Alpha threshold, Margin in pixels, Contour vertices, Interior spacing), the Preserve base quad and Preserve weights on regen checkboxes, and the dense-only column 'Density follows bones' with its Bone influence radius and Bone density factor sub-fields. The dense-only column is greyed in Simple mode, and the bone sub-fields are active only in Dense mode with density on. At the bottom is the Automesh button, greyed unless the mesh has an image texture.
- intent: Confirm the Automesh-from-Alpha subpanel renders all its trace settings and the enable/grey rules; behavior lives in the named tests.
- code: apps/blender/panels/mesh_generation.py:156-178; scene_props.py:80-205,287
- note: Preserve weights on regen behavior -> GAP-REGEN-PRESERVE.

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
  2. Press Backspace to step back to the previous stage; the overlay refreshes and pen stages reset their draw state.
  3. Press Esc to cancel: the overlay and status bar are removed, your session is restored, and no geometry changes.
  4. On the final stage, press Enter to commit: the mesh is written and a confirmation reports the vertex and face counts (with a warning if any drawn points fell outside).
  5. Flip the Interior Mode mid-modal: the stage list rebuilds (Simple drops the inner-loops stage).
- observe: Each key behaves as its step describes, and the mesh only changes on the final commit.
- intent: One walk over the modal stage transitions, cancel, commit, and live re-snapshot.
- code: apps/blender/operators/automesh/automesh_authoring.py:342-348,355,987,1015-1038,1068,1264

### BL-MESH-INTERACTIVE-04 · Author Mesh pen editing (consolidated)
- status: pending
- review: todo
- pre: The Author Mesh modal is on a pen stage.
- steps:
  1. On the edit-outline stage, tap Shift for the extend pen or Ctrl for the cut pen; click to place points or drag to free-draw, then right-click or Enter to finish. The tooltip names the active pen; extend reshapes the outline, cut marks a corridor that is carved at apply.
  2. On the edit-interior stage, click to drop an interior point, tap Shift for the fold pen or Ctrl for the cut pen, then draw and finish. The tooltip turns red when a gesture aims outside the silhouette.
  3. While penning: press X or Z to lock to an axis, use the mouse wheel or number keys to set subdivisions, Alt+click to remove a stroke, and Ctrl+Z to drop the last point or stroke.
- observe: Each pen gesture behaves per its step; the status bar shows the stage and chords, the viewport draws the contour and preview overlays, and the cursor tooltip reflects the held modifier.
- intent: One walk over outline and interior pen editing, the pen chords, and the overlay/status-bar/cursor feedback.
- code: apps/blender/operators/automesh/automesh_authoring.py:365,452,458,486,539,599-624,933,1305; _status_bar.py:19-43

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
- status: todo
- review: keep
- pre: A mesh element active with a target armature set in Skeleton and the mesh bound (to surface every read-out); inspect the Bind, Edit Weights, Snapshot, and Weight Transfer subpanels.
- observe: With a sprite active it shows 'select a mesh element (Weight Paint is mesh-only)' and no subpanels. With a mesh it shows a target read-out ('Target: Skeleton <armature>' or 'Target: Skeleton (none - pick a rig there)') and the subpanels: Bind has a Mode dropdown (Bone Heat / Proximity / Envelope / Single nearest / Empty), then under Proximity only a Max Distance and a Falloff Power field, a per-bone Soft/Hard overrides box, a Bone Heat hint, and the Bind button (no separate target line - the parent read-out covers it); Edit Weights has an active-group label, the Edit Weights button (which reads 'Exit Painting Mode' while in weight-paint mode; with a 'bind first to enable' hint when disabled), the brush curve-preset buttons, and a Clear Empty Vertex Groups button; Brush has the four curve-preset buttons and a viewport-display box (Weight Opacity slider, Zero Weights dropdown, and a caveat about opacity 0); Snapshot has a Preserve weights on regen checkbox and a provenance line ('N paint / N seed / N reprojected' or 'no snapshot - run Bind first'); Weight Transfer has a Max Distance field.
- intent: Confirm the Weight Paint subpanels render their controls and enable/grey rules; behavior lives in the named tests.
- code: apps/blender/panels/weight_paint.py:51-53,174-360; _helpers.py:111
- note:
  Preserve weights on regen behavior -> GAP-REGEN-PRESERVE; modal-entry enable predicate -> FLOW-DOLL-02 / BL-WPAINT-EDIT-01.
  (2026-06-17 spec 044: max_distance + falloff_power now draw under Proximity; Clear Empty Vertex Groups button added to Bind.)

### BL-WPAINT-BIND-01 · Mode dropdown picks the bind algorithm
- status: pass
- review: keep
- steps:
  1. Open the Bind Mode dropdown and pick each of the five modes.
- observe: All five modes are selectable and the choice sticks. Switching to a planar mode (Proximity / Envelope / Single nearest / Empty) shows the per-bone override box, while Bone Heat shows the hint that overrides do not apply to it.
- intent: The Mode dropdown chooses how the mesh is bound to the bones - Bone Heat is the default, the other four are fallbacks tuned via the redo panel.
- code: apps/blender/panels/weight_paint.py:174 (prop); properties/scene_props.py:218 (enum def)

### BL-WPAINT-BIND-02 · Per-bone Soft / Hard / Clear overrides (consolidated)
- status: pass
- review: keep
- pre: A target armature with bones; Mode set to a planar mode (Proximity / Envelope / Single nearest / Empty).
- steps:
  1. Click Soft next to a bone.
  2. Click Hard next to the same bone.
  3. Click the X (Clear) on a bone that has an override.
- observe: Soft and Hard each set that bone's override and look pressed (only one at a time), and Clear becomes available. Clearing removes the override, un-presses both, and disables the X again. Overrides apply only to the planar modes - Bone Heat ignores them.
- intent: Soft blends a bone's weight smoothly with neighbours, Hard gives a crisp single-bone boundary, and Clear drops back to the bind-mode default.
- code: apps/blender/panels/weight_paint.py:225,232,241 -> operators/skinning/set_bone_mode.py:52,56

### BL-WPAINT-BIND-03 · Bind to Target Armature builds the weights
- status: todo
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
- status: todo
- review: keep
- pre: Inside the Edit Weights modal.
- steps:
  1. Press and drag the left mouse button to paint a stroke, then release.
- observe: At the end of the stroke (on release), the vertices you touched turn white (user-painted) and the provenance overlay updates without having to leave and re-enter the mode. Live-during-the-stroke is not expected - the overlay refreshes at stroke end.
- intent: Painting a stroke tags the touched vertices as hand-edited in the snapshot and the overlay repaints at stroke end.
- code: apps/blender/operators/skinning/edit_weights.py modal (RELEASE -> _tag_redraw_view3d, all VIEW_3D areas)

### BL-WPAINT-EDIT-02 · Edit Weights exits and restores (Esc + native mode exit)
- status: todo
- review: keep
- pre: Inside the Edit Weights modal.
- steps:
  1. Press Esc during the modal.
  2. Re-enter, then this time leave weight-paint mode via Blender's own control (Tab, the mode dropdown, or a pie menu) instead of Esc.
- observe: Both exits restore your prior state (mode, brush preset, bone visibility, selection, overlay), with a confirmation that the session was restored; a single Ctrl+Z then reverts the whole session. After a native-control exit the provenance overlay and its flag do not linger (the modal's mode-watch timer ends the session).
- intent: Esc and a native mode exit both cleanly end Edit Weights and restore brush, bone visibility, mode, selection, and the overlay flag.
- code: apps/blender/operators/skinning/edit_weights.py modal (ESC + TIMER mode-watch) -> _finish

### BL-WPAINT-EDIT-03 · Edit Weights button flips to Exit Painting Mode
- status: todo
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

### BL-WPAINT-XFER-01 · Copy Weights to Selected transfers weights
- status: pass
- review: keep
- pre: An active mesh plus at least one other selected mesh.
- steps:
  1. Select the target meshes, then the source mesh (active), and click the copy-weights button.
  2. Press F9 and change Max Distance to re-run with a different radius.
- observe: Each target mesh receives the source's weights by nearest vertex within the Max Distance, creating vertex groups as needed, with a coverage summary report. The button shows only the copy icon (no text). The redo panel exposes Max Distance.
- intent: Copy Weights copies the active mesh's weights onto every other selected mesh by nearest world-space vertex.
- code: apps/blender/panels/weight_paint.py:151 -> operators/skinning/copy_weights_to_selected.py:25,41

## Animation panel (read-only action summary)

### BL-ANIM-SWEEP · Animation panel inventory (visual pass)
- status: todo
- review: keep
- pre: Animation subpanel expanded; test with zero actions and with at least one action.
- observe: A target read-out ('Target: Skeleton <armature>' or 'Target: Skeleton (none - pick a rig there)') heads the panel, matching Mesh Generation and Weight Paint. With no actions it then shows 'no actions to export' and no list. With actions it shows the action list (one row per action, between 2 and 6 rows visible), each row labeled with the action name and its frame range '[start-end]' (rounded to whole frames; an empty action shows '[0-0]'), and a 'N action(s) total' count below.
- intent: Confirm the Animation panel renders the target read-out, the empty state, the action list with frame ranges, and the total count; row-click behavior lives in the named tests.
- code: apps/blender/panels/animation.py:12-36,56-68

### BL-ANIM-01 · Clicking an action row assigns it to the picked armature
- status: todo
- review: keep
- pre: At least one action; an armature picked in the Skeleton panel.
- steps:
  1. Expand the Animation subpanel and click an action's name.
- observe: The clicked action is assigned to the Skeleton-picked armature (which then plays it when you scrub the timeline), and that row becomes active. The action looks like a plain label but acts as a button. It is undoable.
- intent: The action rows are click-to-assign and target the picker (the single source of truth), even though the panel reads as read-only.
- code: apps/blender/panels/animation.py:28-36 (draw), apps/blender/operators/selection.py (handler -> resolve_skeleton_target)

### BL-ANIM-02 · Assigning targets the picked armature, not the first in scene
- status: todo
- review: keep
- pre: At least one action; two or more armatures in the scene; one of them picked in the Skeleton panel.
- steps:
  1. With two or more armatures present and one picked, click an action row.
- observe: The action is assigned to the picked armature regardless of scene order; the other armatures are untouched, and there is no 'N armatures in scene' warning (the picker disambiguates). (Spec 045 removed the first-armature heuristic.)
- intent: The Skeleton picker, not a scene scan, decides which armature receives the action.
- code: apps/blender/operators/selection.py (resolve_skeleton_target)

### BL-ANIM-03 · Assigning with no armature picked cancels with a warning
- status: todo
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

## Validation panel (export-blocking issues list)

### BL-VALID-SWEEP · Validation panel inventory (visual pass)
- status: pending
- review: keep
- pre: Validation subpanel expanded; surface each state (before Validate, a clean scene, and a scene with issues).
- observe: The subpanel shows the Validate button, a 'run Validate to see issues' label before the first run, a 'no issues - ready to export' label on a clean scene, and issue rows otherwise (object rows render '[Name] message', scene-wide rows render a plain non-clickable label, with errors tinted red and warnings plain).
- intent: Confirm the Validation panel renders the button, the before/clean labels, and the issue rows; the Validate run and clickable rows live in the named tests.
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

### BL-VALID-02 · Clicking an issue row selects the offending object
- status: pending
- review: keep
- pre: Validate has been run and produced at least one object-scoped issue.
- steps:
  1. Run Validate, then click a row showing '[Name] message'.
- observe: That object becomes the only selected and active object. Error rows show in red, warnings plain. If the named object no longer exists, a warning appears and the selection is unchanged.
- intent: Clicking an object-scoped issue row jumps your selection to the offending object.
- code: apps/blender/panels/validation.py:43 -> _helpers.py:142 (draw_issue_row) -> selection.py:18 (PROSCENIO_OT_select_issue_object.execute:31)

## Pipeline panel: import Photoshop manifest + export/re-export .proscenio

### BL-PIPE-SWEEP · Pipeline panel inventory (visual pass)
- status: pending
- review: keep
- pre: Pipeline panel expanded with the scene properties registered.
- observe: The panel groups an Import subpanel and an Export subpanel. The Export subpanel shows the Last export path field, the Pixels-per-unit field, and the Bundle textures checkbox. The Import dialog's Placement and Root Bone Name fields are covered in the named tests below.
- intent: Confirm the Pipeline panel renders its Import/Export structure and the Export fields; field semantics live in the named tests.
- code: apps/blender/panels/pipeline.py:88-95

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

### BL-PIPE-EXPORT-01 · Last export path is sticky and enables Re-export
- status: pending
- review: keep
- steps:
  1. Export once, then look at the Last export path field; edit it and re-export.
- observe: The field holds the last export destination, and once it is set a Re-export button appears. The value persists across save and reload, and editing it changes where Re-export writes.
- intent: The export path is remembered so Re-export skips the file dialog, and is saved with the blend so the document carries its export target.
- code: apps/blender/panels/pipeline.py:88 -> apps/blender/properties/scene_props.py:403-411

### BL-PIPE-EXPORT-02 · Pixels per unit (scene field)
- status: pending
- review: keep
- steps:
  1. Change the Pixels-per-unit field and re-export.
- observe: The scene pixels-per-unit value updates (minimum just above 0). Re-export uses it as the world-to-pixel ratio. The first Export does not use this field - it uses the dialog's own value (default 100). It is also synced from the manifest on import.
- intent: Pixels per unit sets the Blender-world-to-Godot-pixel ratio used by Re-export (default 100).
- code: apps/blender/panels/pipeline.py:89 -> apps/blender/properties/scene_props.py:412-417

### BL-PIPE-EXPORT-03 · Bundle textures copies textures beside the export
- status: pending
- review: keep
- steps:
  1. Turn Bundle textures on and export; then turn it off and export.
- observe: With it on, every referenced texture is copied next to the .proscenio file and the success report adds 'bundled N texture(s)' (noting any missing on disk). With it off, no textures are copied and there is no suffix.
- intent: Bundle textures copies the referenced textures alongside the exported .proscenio (undocumented).
- code: apps/blender/panels/pipeline.py:90 -> apps/blender/properties/scene_props.py:418-426 -> apps/blender/operators/export_flow.py:97-118

### BL-PIPE-EXPORT-04 · Export dialog Pixels per unit (first export)
- status: pending
- review: keep
- steps:
  1. Run the first Export and set the Pixels per unit in the export file dialog.
- observe: The writer uses this dialog value (default 100), independent of the panel/scene Pixels-per-unit field. This is the only pixels-per-unit the first Export honors.
- intent: The export dialog's Pixels per unit sets the world-to-pixel ratio for the first export.
- code: apps/blender/operators/export_flow.py:158-163,167

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
- code: apps/blender/panels/helpers.py:31-35 (button); operator at apps/blender/operators/armature/authoring_camera.py:16-53

## Diagnostics + Help system + Addon Preferences

### BL-HELP-PANEL-SWEEP · Help cheat-sheet inventory (visual pass)
- status: pending
- review: keep
- pre: Help subpanel expanded (always present, sitting just above Diagnostics).
- observe: The Help subpanel shows an 'Operators (use F3 to search):' heading and exactly 18 two-label rows (a friendly name and its operator id, e.g. 'Validate' / 'proscenio.validate_export'). The rows are plain read-only labels, not clickable buttons.
- intent: Confirm the Help cheat-sheet renders its heading and the 18 operator reference rows.
- code: apps/blender/panels/help.py:11-29,32-52

### BL-PREFS-SWEEP · Addon Preferences inventory (visual pass)
- status: pending
- review: keep
- pre: Addon Preferences open.
- observe: The preferences show a 'Developer' box grouping a Log level dropdown (errors / info / debug) and a Debug mode checkbox.
- intent: Confirm the addon preferences render the Developer box with the Log level and Debug mode controls; their effects live in BL-DIAG-02 and BL-CHROME-08.
- code: apps/blender/addon_prefs.py:29-62

### BL-DIAG-01 · Run Smoke Test prints a sanity check
- status: pending
- review: keep
- pre: Debug mode on so the Diagnostics panel is visible.
- steps:
  1. Open the Diagnostics subpanel and click Run Smoke Test.
- observe: A 'Proscenio smoke test OK' message appears in the info area and the system console, and the operator finishes successfully.
- intent: Run Smoke Test confirms the addon is registered and dispatching operators correctly.
- code: apps/blender/panels/diagnostics.py:33 -> apps/blender/operators/help_dispatch.py:108-112

### BL-DIAG-02 · Log level controls how much operators report
- status: pending
- review: keep
- pre: Addon Preferences open.
- steps:
  1. Change the Log level dropdown between Errors only, Info, and Debug.
- observe: 'Errors only' suppresses the info and warning messages, 'Debug' adds extra per-item trace lines, and 'Info' (the default) is in between. The choice persists across restart.
- intent: Log level controls how verbose the operators' info-log reporting is (Errors only / Info / Debug).
- code: apps/blender/addon_prefs.py:29-48 (update=_on_log_level_update -> report.set_min_level)
