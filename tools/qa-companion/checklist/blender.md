# Blender addon - manual-test checklist

Maintained by the QA Companion tool (tools/qa-companion): one block per item. `status` / `note` / `shots` are the recorded walk; `review` is your verdict on the test itself (keep / rephrase / drop / todo). Edit here or via the tool.

## Outliner panel

### BL-OUTLN-01 · Outliner subpanel foldout (header)
- status: pass
- review: drop
- observe: Panel is DEFAULT_CLOSED on first open; clicking the header expands it to reveal filter row + list; clicking again collapses.
- intent: Sprite-centric flat list replacing Blender's outliner for big rigs; collapsed by default.
- code: apps/blender/panels/outliner.py:127-139
- note:
  it works but this is useless as a test item since it can be condensed:
  behavior should work across all panels

### BL-OUTLN-02 · Status badge button (Blender-only mark)
- status: pending
- review: keep
- observe: Shows the custom Blender-only mark (feature_status 'outliner' = BLENDER_ONLY); hover surfaces the blender-only band tooltip; click opens the status_legend help popup (via proscenio.status_info > proscenio.help).
- intent: UNDOCUMENTED
- code: apps/blender/panels/_helpers.py:83 (draw via draw_subpanel_header, outliner.py:139)

### BL-OUTLN-04 · Outliner filter (search text field, VIEWZOOM icon)
- status: pending
- review: keep
- observe: Rows whose object name (lowercased) does not contain the substring are hidden live as you type; clearing the field shows all Proscenio-relevant rows again.
- intent: Type a substring to filter the list live; empty shows every Proscenio-relevant object.
- code: apps/blender/panels/outliner.py:148 (prop) + filter_items:95,117

### BL-OUTLN-05 · Favorites-only toggle (SOLO_ON icon next to filter)
- status: pending
- review: keep
- observe: When enabled, only rows whose object has is_outliner_favorite=True remain visible; disabling restores the full filtered list. Note: favorites are NOT reordered to the top (see finding).
- intent: Toggle next to the filter that hides everything except favorited rows.
- code: apps/blender/panels/outliner.py:149 (prop) + filter_items:100-116

### BL-OUTLN-06 · Outliner UIList (template_list, 8 rows)
- status: pending
- review: keep
- observe: Rows sorted by category rank then name: rank0 slot Empty 'LINK_BLEND [slot] <name>'; rank1 attachment mesh 'OBJECT_DATAMODE   -> <name>'; rank2 sprite mesh 'MESH_DATA <name>[ @ <bone>]'; rank3 armature 'ARMATURE_DATA [arm] <name>'. Cameras/lights/etc (rank 9) are hidden.
- intent: Flat list: slots first (with [slot] prefix and indented attachments), sprite meshes, then armatures last ([arm]).
- code: apps/blender/panels/outliner.py:150-158 (template_list) + draw_item:40-84

### BL-OUTLN-09 · Sprite-mesh bone-parent suffix label (' @ <bone>')
- status: pending
- review: keep
- observe: Row label reads '<name> @ <parent_bone>'; meshes not bone-parented show just '<name>'. Doc never mentions the '@ bone' affordance.
- intent: UNDOCUMENTED
- code: apps/blender/panels/outliner.py:62-63

### BL-OUTLN-10 · Native 'Filter by Name' field (UIList expand arrows)
- status: pending
- review: keep
- observe: Native filter_name is applied (lowercased substring) only when the Proscenio search bar is empty; the Proscenio bar wins when both are set. Doc never mentions Blender's native UIList filter row.
- intent: UNDOCUMENTED
- code: apps/blender/panels/outliner.py:96-99 (self.filter_name honored)

### BL-OUTLN-11 · Native UIList sort/invert/name toggles (expand arrows)
- status: pending
- review: keep
- observe: filter_items always returns its own category-then-name order via flt_neworder, so the custom sort overrides native sort; the native invert-filter toggle (Show inactive) may still flip which rows are shown. Doc never mentions these controls.
- intent: UNDOCUMENTED
- code: apps/blender/panels/outliner.py:150-158 (template_list) + filter_items:120-124

### BL-OUTLN-12 · active_outliner_index list highlight
- status: pending
- review: keep
- observe: The UIList active-row highlight follows the clicked object via active_outliner_index. Doc never mentions a persistent active-row highlight; index is computed against bpy.data.objects order, not the displayed order (see finding).
- intent: UNDOCUMENTED
- code: apps/blender/properties/scene_props.py:484-489 + selection.py:153-167

### BL-OUTLN-13 · 'Proscenio scene props not registered' fallback label
- status: pending
- review: keep
- observe: Panel body shows an ERROR-icon label 'Proscenio scene props not registered' and draws nothing else. Doc never mentions this failure label.
- intent: UNDOCUMENTED
- code: apps/blender/panels/outliner.py:143-146

### BL-OUTLN-03 · Help '?' button (header)
- status: pending
- review: keep
- pre: Outliner subpanel header visible.
- steps:
  1. Click the '?' (QUESTION) icon at the right of the 'Outliner' header.
- observe: A 480px-wide popup opens titled 'Outliner' with the summary, sections, and an 'Open online docs' link resolving to the outliner doc page (topic 'outliner' exists in help_topics).
- intent: Open an explanation of the Outliner panel section.
- code: apps/blender/panels/_helpers.py:84 (topic='outliner', help_dispatch.py:50-97)

### BL-OUTLN-07 · Row click (proscenio.select_outliner_object)
- status: pending
- review: keep
- pre: Outliner expanded with at least one visible row.
- steps:
  1. Click on a row label (the embossless button spanning the row text).
- observe: All other objects are deselected; the clicked object becomes the sole selection and the active object (select_only); active_outliner_index is synced to that object's index in bpy.data.objects. If the object was deleted, a warning is reported and the op cancels.
- intent: Click a row to make that object active and selected.
- code: apps/blender/panels/outliner.py:71-77 + operators/selection.py:40-59

### BL-OUTLN-08 · Per-row favorite toggle (SOLO_OFF / SOLO_ON, proscenio.toggle_outliner_favorite)
- status: pending
- review: keep
- pre: Outliner expanded with at least one visible row.
- steps:
  1. Click the SOLO icon at the right end of a row > click again to unpin.
- observe: Icon flips SOLO_OFF<->SOLO_ON; obj.proscenio.is_outliner_favorite flips and is undoable (REGISTER, UNDO). If the object's PropertyGroup is unregistered, a warning is reported and the op cancels. The row is NOT moved to the top (see finding).
- intent: SOLO icon pins a row as a favorite (so it survives the Favorites-only filter).
- code: apps/blender/panels/outliner.py:78-84 + operators/selection.py:170-197

## Element panel (Active Sprite / Active Mesh, type, region, drive-from-bone, reproject UV)

### BL-ELEM-01 · Element panel empty-state label "select a mesh or sprite element"
- status: pending
- review: keep
- observe: Panel body shows only the INFO-icon label 'select a mesh or sprite element'; no element_type selector, no subpanels.
- intent: Per-element settings panel; shows a prompt when no mesh/sprite is active.
- code: apps/blender/panels/element.py:49-50

### BL-ELEM-02 · Element panel "proscenio property group not registered" error label
- status: pending
- review: keep
- observe: ERROR-icon label 'proscenio property group not registered'; no further controls drawn.
- intent: UNDOCUMENTED (registration-gap guard).
- code: apps/blender/panels/element.py:53-55

### BL-ELEM-03 · Element type selector (Mesh / Sprite) - Weight Paint locked variant
- status: pending
- review: keep
- observe: element_type dropdown is shown but greyed/disabled; INFO label 'element type is locked in Weight Paint mode'; no other element fields or subpanels.
- intent: Element type decides the Godot node; UNDOCUMENTED that it is locked in Weight Paint mode.
- code: apps/blender/panels/element.py:56-61

### BL-ELEM-04 · Element type dropdown (Mesh / Sprite)
- status: pending
- review: keep
- observe: Choosing Mesh shows the Active Mesh subpanel; choosing Sprite shows the Active Sprite subpanel (poll swaps which subpanel appears); element_type Custom Property mirrors on change.
- intent: Mesh exports a Polygon2D (deformable cutout w/ UVs+weights); Sprite exports a Sprite2D (hframes x vframes grid).
- code: apps/blender/panels/element.py:62 (prop element_type, items object_props.py:26-34)

### BL-ELEM-05 · Element panel inline validation issue rows
- status: pending
- review: keep
- observe: One alert/INFO row per issue (e.g. 'sprite element mesh is N verts / M face(s), not a single quad...'); rows naming an object are clickable select-issue buttons.
- intent: Surfaces validation issues for the active element (UNDOCUMENTED on the doc page).
- code: apps/blender/panels/element.py:63-64; apps/blender/core/validation/active_element.py:9

### BL-ELEM-06 · Element subpanel header status badge (Godot-ready mark)
- status: pending
- review: keep
- observe: Custom Godot icon (GODOT_READY band) shown; hovering surfaces the band tooltip via proscenio.status_info; clicking opens the band info.
- intent: UNDOCUMENTED (status-band badge surfaced on every subpanel header).
- code: apps/blender/panels/_helpers.py:46-69, 83; element.py:44

### BL-ELEM-08 · Active Mesh subpanel - poly/vertex-group count label
- status: pending
- review: keep
- observe: Label '<N> polygon(s), <M> vertex group(s)' reflecting the mesh's polygon count and vertex_groups length.
- intent: UNDOCUMENTED read-out (doc only says mesh exports as Polygon2D).
- code: apps/blender/panels/_draw_mesh.py:19-22

### BL-ELEM-11 · Isolated material checkbox
- status: pending
- review: keep
- observe: material_isolated bool toggles; Custom Property mirrors; affects Pack Atlas behavior (material kept on this object).
- intent: UNDOCUMENTED on element doc; when packing, keep this sprite's own material instead of linking to the shared PackedAtlas material.
- code: apps/blender/panels/_draw_mesh.py:24; object_props.py:157-167

### BL-ELEM-12 · Exclude from atlas checkbox
- status: pending
- review: keep
- observe: exclude_from_atlas bool toggles; Custom Property mirrors; object skipped by Pack Atlas.
- intent: UNDOCUMENTED on element doc; keep this sprite out of Pack Atlas entirely (UVs/material untouched, ships own texture).
- code: apps/blender/panels/_draw_mesh.py:25; object_props.py:168-178

### BL-ELEM-13 · Active Mesh header status badge + "?" help
- status: pending
- review: keep
- observe: Godot-ready badge shown; help opens topic 'active_mesh' (anchor element#active-mesh).
- intent: UNDOCUMENTED; status badge + help (topic 'active_mesh').
- code: apps/blender/panels/element.py:84; _helpers.py:83-85

### BL-ELEM-14 · hframes field (Horizontal frames)
- status: pending
- review: keep
- observe: hframes int (min 1, soft_max 64); region readout 'frame: WxH px (hf x vf grid)' updates; CP mirrors.
- intent: Spritesheet grid columns.
- code: apps/blender/panels/_draw_sprite.py:23; object_props.py:79-86

### BL-ELEM-15 · vframes field (Vertical frames)
- status: pending
- review: keep
- observe: vframes int (min 1, soft_max 64); frame-size readout updates; CP mirrors.
- intent: Spritesheet grid rows.
- code: apps/blender/panels/_draw_sprite.py:24; object_props.py:87-94

### BL-ELEM-16 · frame field (Initial frame)
- status: pending
- review: keep
- observe: frame int (min 0) stored; written as Sprite2D rest frame at export; CP mirrors.
- intent: The cell shown at rest pose; animation tracks override it.
- code: apps/blender/panels/_draw_sprite.py:25; object_props.py:95-103

### BL-ELEM-17 · centered checkbox
- status: pending
- review: keep
- observe: centered bool (default True) toggles; mapped to Sprite2D.centered on export; CP mirrors.
- intent: Godot Sprite2D.centered: texture centred on origin, or its top-left at the origin.
- code: apps/blender/panels/_draw_sprite.py:26; object_props.py:104-109

### BL-ELEM-18 · Active Sprite atlas/region readout labels
- status: pending
- review: keep
- observe: If no image linked: 'atlas: not linked in material'. Else 'atlas: WxH px', 'region: WxH px (full atlas/manual)', 'frame: WxH px (hf x vf grid)'.
- intent: UNDOCUMENTED; shows atlas size, region size, and frame size for the sprite.
- code: apps/blender/panels/_draw_sprite.py:27,31-54

### BL-ELEM-21 · Active Sprite header status badge + "?" help
- status: pending
- review: keep
- observe: Godot-ready badge; help opens topic 'active_sprite' (anchor element#active-sprite).
- intent: UNDOCUMENTED; status badge + help (topic 'active_sprite').
- code: apps/blender/panels/element.py:108; _helpers.py:83-85

### BL-ELEM-22 · Texture Region mode dropdown (Auto / Manual)
- status: pending
- review: keep
- observe: Auto: shows hint label only. Manual: reveals X/Y/W/H rows (+ Snap button for mesh). CP mirrors.
- intent: Auto reads region from UV bounds at export; Manual reads region_x/y/w/h verbatim.
- code: apps/blender/panels/_draw_region.py:20; object_props.py:110-120

### BL-ELEM-23 · Texture Region Auto-mode hint label
- status: pending
- review: keep
- observe: Mesh: 'computed from UV bounds at export'. Sprite: 'omitted at export - full atlas used' (INFO icon).
- intent: Auto reads region from UV bounds at export (mesh) / full atlas used (sprite).
- code: apps/blender/panels/_draw_region.py:30-36

### BL-ELEM-24 · region_x field (X)
- status: pending
- review: keep
- observe: region_x float clamped [0,1], precision 4; readout updates; CP mirrors.
- intent: Manual region origin X, normalized [0,1] of atlas width.
- code: apps/blender/panels/_draw_region.py:23; object_props.py:121-129

### BL-ELEM-25 · region_y field (Y)
- status: pending
- review: keep
- observe: region_y float clamped [0,1], precision 4; CP mirrors.
- intent: Manual region origin Y, normalized [0,1] of atlas height.
- code: apps/blender/panels/_draw_region.py:24; object_props.py:130-138

### BL-ELEM-26 · region_w field (Width)
- status: pending
- review: keep
- observe: region_w float clamped [0,1] (default 1.0), precision 4; sprite readout 'region: WxH px (manual)' updates; CP mirrors.
- intent: Manual region width, normalized [0,1] of atlas width.
- code: apps/blender/panels/_draw_region.py:26; object_props.py:139-147

### BL-ELEM-27 · region_h field (Height)
- status: pending
- review: keep
- observe: region_h float clamped [0,1] (default 1.0), precision 4; CP mirrors.
- intent: Manual region height, normalized [0,1] of atlas height.
- code: apps/blender/panels/_draw_region.py:27; object_props.py:148-156

### BL-ELEM-30 · Texture Region header status badge + "?" help
- status: pending
- review: keep
- observe: Godot-ready badge; help opens topic 'texture_region' (anchor element#texture-region).
- intent: UNDOCUMENTED; status badge + help (topic 'texture_region').
- code: apps/blender/panels/element.py:132; _helpers.py:83-85

### BL-ELEM-31 · Drive from Bone - Target dropdown
- status: pending
- review: keep
- observe: driver_target enum (Frame index / Region X/Y/W/H, default region_x); selection drives which proscenio.* gets the driver and which value the readout shows; CP mirrors.
- intent: Wires a driver into a sprite proscenio.* property (frame / region_x/y/w/h).
- code: apps/blender/panels/_draw_driver_shortcut.py:21; object_props.py:180-185

### BL-ELEM-32 · Drive from Bone - Armature picker
- status: pending
- review: keep
- observe: Picker lists ARMATURE objects only (poll is_armature); selecting one populates the Bone dropdown; CP mirrors.
- intent: Pick the armature whose pose bone supplies the driver value.
- code: apps/blender/panels/_draw_driver_shortcut.py:22; object_props.py:186-191; _dynamic_items.py:29-31

### BL-ELEM-33 · Drive from Bone - Bone dropdown
- status: pending
- review: keep
- observe: Lists every bone of the picked armature. Sentinel '(pick an armature first)' when no armature; '(armature has no bones)' when empty.
- intent: Pick the pose bone whose transform feeds the driver.
- code: apps/blender/panels/_draw_driver_shortcut.py:23; object_props.py:192-196; _dynamic_items.py:44-63

### BL-ELEM-34 · Drive from Bone - Axis dropdown
- status: pending
- review: keep
- observe: driver_source_axis enum; PG default ROT_Y; list order ROT_Z, ROT_X, ROT_Y, LOC_X/Y/Z; CP mirrors.
- intent: Pose bone transform channel feeding the driver (ROT_Z/X/Y, LOC_X/Y/Z).
- code: apps/blender/panels/_draw_driver_shortcut.py:24; object_props.py:197-202

### BL-ELEM-35 · Drive from Bone - In Min / In Max fields
- status: pending
- review: keep
- observe: driver_in_min (default -1.5708) / driver_in_max (default 1.5708) floats; feed build_driver_expression on Drive.
- intent: Two-range linear map input: bone-channel values mapped to output min/max.
- code: apps/blender/panels/_draw_driver_shortcut.py:29-31; object_props.py:203-218

### BL-ELEM-36 · Drive from Bone - Out Min / Out Max fields
- status: pending
- review: keep
- observe: driver_out_min (0.0) / driver_out_max (1.0) floats; build_driver_expression sorts the output band so inverted ranges clamp correctly.
- intent: Two-range linear map output: target value at the input min/max.
- code: apps/blender/panels/_draw_driver_shortcut.py:32-34; object_props.py:219-230

### BL-ELEM-37 · Drive from Bone - Expression field (Advanced)
- status: pending
- review: keep
- observe: driver_expression string (default 'var') shown instead of the four range fields; used verbatim on Drive when Advanced on.
- intent: Raw driver expression fallback ('var' = bone channel) shown when Advanced is on.
- code: apps/blender/panels/_draw_driver_shortcut.py:26-27; object_props.py:240-248

### BL-ELEM-38 · Drive from Bone - Advanced expression toggle
- status: pending
- review: keep
- observe: On: hides In/Out rows, shows Expression field. Off: shows the four range fields.
- intent: Use the raw expression instead of the two-range linear map.
- code: apps/blender/panels/_draw_driver_shortcut.py:35; object_props.py:231-239

### BL-ELEM-39 · Drive from Bone - live Value readout
- status: pending
- review: keep
- observe: Label 'Value: <n>' - whole for int target (frame), 3-decimal for region channels; absent if getattr(props, target) is None.
- intent: UNDOCUMENTED; inline read-back of the driven target property's current value.
- code: apps/blender/panels/_draw_driver_shortcut.py:37,46-59

### BL-ELEM-43 · Drive from Bone header status badge + "?" help
- status: pending
- review: keep
- observe: Godot-ready badge; help opens topic 'drive_from_bone' (anchor element#drive-from-bone).
- intent: Wires a driver between a pose bone and a sprite proscenio.* property (help topic 'drive_from_bone').
- code: apps/blender/panels/element.py:156; _helpers.py:83-85

### BL-ELEM-07 · Element subpanel header "?" help button
- status: pending
- review: keep
- pre: Active MESH
- steps:
  1. Click the QUESTION-mark icon on the Element panel header
- observe: proscenio.help fires with topic='active_element'; the Element help popup/section opens (maps to docs anchor 'element').
- intent: UNDOCUMENTED (opens the in-panel help topic for 'active_element').
- code: apps/blender/panels/_helpers.py:84-85; element.py:44 (topic 'active_element')

### BL-ELEM-09 · Reproject UV button
- status: pending
- review: keep
- pre: Active MESH (element_type=mesh) in OBJECT mode (operator poll requires OBJECT)
- steps:
  1. Select a mesh element in Object Mode > Active Mesh subpanel > click Reproject UV
- observe: UVs re-unwrapped via smart_project (angle_limit default 1.15192); selection/active restored; INFO report 'reprojected UVs on <name>'; redo panel exposes Angle limit. May rotate/mirror UVs.
- intent: UNDOCUMENTED on element doc; re-projects the mesh UVs (Smart UV Project) so the texture lines up after vertex edits.
- code: apps/blender/panels/_draw_mesh.py:23; apps/blender/operators/uv_authoring.py:22-80

### BL-ELEM-10 · Reproject UV - disabled/poll-fail path
- status: pending
- review: keep
- pre: Active MESH in EDIT mode (or non-mesh active)
- steps:
  1. Enter Edit Mode on the mesh > Active Mesh subpanel still drawn only in object-context; invoke proscenio.reproject_sprite_uv
- observe: Operator poll returns False (button/op unavailable) because context.mode != OBJECT; no UV change.
- intent: UNDOCUMENTED; operator is OBJECT-mode only.
- code: apps/blender/operators/uv_authoring.py:49-56

### BL-ELEM-19 · Setup Preview button (sprite preview shader)
- status: pending
- review: keep
- pre: Active sprite MESH whose material lacks the slicer node group
- steps:
  1. Active Sprite subpanel > click Setup Preview
- observe: Setup button enabled only when no slicer present; firing adds the SpriteFrameSlicer node group; Setup greys out, Remove enables.
- intent: UNDOCUMENTED; installs the SpriteFrameSlicer material-preview shader.
- code: apps/blender/panels/_draw_sprite.py:66-77 (op proscenio.setup_sprite_frame_preview)

### BL-ELEM-20 · Remove Preview button (sprite preview shader)
- status: pending
- review: keep
- pre: Active sprite MESH whose material carries the slicer node group
- steps:
  1. Active Sprite subpanel > click Remove Preview
- observe: Remove enabled only when slicer present; firing strips the node group; Remove greys out, Setup re-enables.
- intent: UNDOCUMENTED; removes the SpriteFrameSlicer material-preview shader.
- code: apps/blender/panels/_draw_sprite.py:78-83 (op proscenio.remove_sprite_frame_preview)

### BL-ELEM-28 · Snap to UV bounds button
- status: pending
- review: keep
- pre: Active MESH with element_type=mesh, region_mode=manual, OBJECT mode, mesh has UV layer + polygons
- steps:
  1. Mesh element > region_mode=Manual > click Snap to UV bounds
- observe: region_x/y/w/h overwritten with UV bounds (v flipped to Godot space via compute_region_from_uvs); INFO report 'snapped region to UV bounds (...)'. Warn report if no UV/polygons or PG missing.
- intent: Fills the manual region fields from the current UV.
- code: apps/blender/panels/_draw_region.py:28-29; apps/blender/operators/uv_authoring.py:83-131

### BL-ELEM-29 · Snap to UV bounds - absence for sprite elements
- status: pending
- review: keep
- pre: Active MESH with element_type=sprite, region_mode=manual
- steps:
  1. Sprite element > region_mode=Manual > inspect Texture Region box
- observe: X/Y/W/H fields shown but NO Snap to UV bounds button (sprite path omits it).
- intent: Doc implies Snap fills manual fields from UV generally; code hides it for sprite element_type.
- code: apps/blender/panels/_draw_region.py:28 (gated on element_type=='mesh')

### BL-ELEM-40 · Drive from Bone button (create driver)
- status: pending
- review: keep
- pre: Active sprite/mesh MESH; armature picked with at least one bone; a bone selected (row enabled only then)
- steps:
  1. Pick armature + bone + axis + ranges/target > click Drive from Bone
- observe: Driver added on proscenio.<target>; stale sibling drivers off same (armature,bone) purged; SCRIPTED expression set; INFO report 'driver on <sprite>.proscenio.<target> <- <arm>:<bone>.<axis>'. Redo panel exposes operator props.
- intent: Materializes a Blender driver from the picked bone channel into proscenio.<target>; re-running replaces it.
- code: apps/blender/panels/_draw_driver_shortcut.py:39-43; apps/blender/operators/driver.py:96-262

### BL-ELEM-41 · Drive from Bone button - disabled (no bone) path
- status: pending
- review: keep
- pre: Active MESH; no armature or no bone selected
- steps:
  1. Drive from Bone with empty Armature/Bone > observe button
- observe: row.enabled False -> Drive from Bone button greyed; cannot fire.
- intent: UNDOCUMENTED; button is disabled until a bone is picked.
- code: apps/blender/panels/_draw_driver_shortcut.py:40-42

### BL-ELEM-42 · Drive from Bone - error reports (bad armature/bone)
- status: pending
- review: keep
- pre: Invoke proscenio.create_driver with armature_name unset/non-armature or bone not in armature
- steps:
  1. Force-run create_driver via redo panel with mismatched armature/bone
- observe: report_error 'pick a source armature in the panel' or "bone '<x>' not in armature '<y>'"; returns CANCELLED; no driver added.
- intent: UNDOCUMENTED; operator validates armature/bone before adding the driver.
- code: apps/blender/operators/driver.py:197-204

## Slots panel + slot operators

### BL-SLOT-01 · Slots panel header status badge (slot_system)
- status: pending
- review: keep
- observe: Hover shows the godot-ready band tooltip; click opens the status-legend help popup (proscenio.status_info -> proscenio.help topic='status_legend').
- intent: UNDOCUMENTED - status icon for the slot_system feature band (godot-ready).
- code: apps/blender/panels/slots.py:51-52 -> _helpers.py:46-69

### BL-SLOT-02 · Slots panel '?' help button
- status: pending
- review: keep
- observe: A 480px-wide help popup opens for the 'slot_system' topic (title + summary + sections, 'Open online docs' button).
- intent: UNDOCUMENTED - opens the slot_system help popup.
- code: apps/blender/panels/slots.py:51-52 -> _helpers.py:84-86

### BL-SLOT-03 · 'no slots yet - select meshes and Create Slot' empty-state label
- status: pending
- review: keep
- observe: An INFO-icon label 'no slots yet - select meshes and Create Slot' is shown instead of a list.
- intent: Parent panel lists every slot; when none exist it prompts to create one.
- code: apps/blender/panels/slots.py:58-59

### BL-SLOT-05 · Per-slot mesh-child count badge (number + OUTLINER_OB_MESH icon)
- status: pending
- review: keep
- observe: Number equals the count of direct children with type=='MESH'; updates after adding/removing attachments and a redraw.
- intent: UNDOCUMENTED - shows the count of MESH children for the slot on its row.
- code: apps/blender/panels/slots.py:71-72

### BL-SLOT-06 · Tip box (Pose Mode / Object Mode hint, 2 lines)
- status: pending
- review: keep
- observe: Box (scale_y 0.8) shows 'Pose Mode + active bone: slot anchored to the bone' (INFO) and 'Object Mode + meshes: slot wraps the selection' (BLANK1). Static text, always present.
- intent: UNDOCUMENTED - static hint explaining how Create Slot anchors (pose-bone vs mesh selection).
- code: apps/blender/panels/slots.py:74-77

### BL-SLOT-08 · Create Slot redo 'Slot name' field
- status: pending
- review: keep
- observe: The Empty is renamed to the typed value on re-execute; empty value falls back to '<bone>.slot' or 'slot'.
- intent: Name of the new Empty; defaults to '<bone>.slot' or 'slot'.
- code: apps/blender/operators/slot/create.py:58-62,116-119

### BL-SLOT-09 · Active Slot subpanel header status badge (active_slot)
- status: pending
- review: keep
- observe: Hover shows godot-ready tooltip; click opens the status-legend popup.
- intent: UNDOCUMENTED - status icon for the active_slot feature band (godot-ready).
- code: apps/blender/panels/slots.py:101-102 -> _helpers.py:46-69

### BL-SLOT-10 · Active Slot subpanel '?' help button
- status: pending
- review: keep
- observe: Help popup for the 'active_slot' topic opens.
- intent: UNDOCUMENTED - opens the active_slot help popup.
- code: apps/blender/panels/slots.py:101-102 -> _helpers.py:84-86

### BL-SLOT-12 · Slot name label ('Slot "<name>"', LINK_BLEND)
- status: pending
- review: keep
- observe: Shows 'Slot \'<empty.name>\''.
- intent: UNDOCUMENTED - read-only header showing the active slot's name.
- code: apps/blender/panels/slots.py:117

### BL-SLOT-13 · Parent bone readout label ('bone: <name>' / '(unparented)', BONE_DATA)
- status: pending
- review: keep
- observe: Shows the parent_bone name when parent_type=='BONE', else '(unparented)'.
- intent: UNDOCUMENTED - read-only readout of the slot's parent bone.
- code: apps/blender/panels/slots.py:115,118-121 -> validation/active_slot.py:63-73

### BL-SLOT-14 · 'no parent bone' alert warning row
- status: pending
- review: keep
- observe: A red (alert) ERROR-icon row 'no parent bone - attachments will not follow any bone' appears; absent when bone-parented.
- intent: UNDOCUMENTED - alert when the slot has no bone parent (attachments won't follow a bone).
- code: apps/blender/panels/slots.py:122-128

### BL-SLOT-15 · 'Attachments (N):' label
- status: pending
- review: keep
- observe: N equals the number of sorted MESH children; OUTLINER_OB_MESH icon.
- intent: Lists the slot's child attachments (heading shows count).
- code: apps/blender/panels/slots.py:131

### BL-SLOT-16 · 'empty slot - add child meshes' alert label
- status: pending
- review: keep
- observe: A red (alert) INFO-icon row 'empty slot - add child meshes' appears.
- intent: UNDOCUMENTED - alert shown when the active slot has no MESH children.
- code: apps/blender/panels/slots.py:132-135

### BL-SLOT-18 · Attachment name label (per attachment)
- status: pending
- review: keep
- observe: Shows child.name verbatim.
- intent: UNDOCUMENTED - read-only name of each child attachment in the list.
- code: apps/blender/panels/slots.py:149

### BL-SLOT-19 · Attachment kind label (mesh/sprite, MESH_DATA/IMAGE_DATA)
- status: pending
- review: keep
- observe: Shows 'mesh' (MESH_DATA) or 'sprite' (IMAGE_DATA) per the child's proscenio.element_type; defaults to 'mesh' when props missing.
- intent: UNDOCUMENTED - read-only element_type of each attachment.
- code: apps/blender/panels/slots.py:28-37,150-151

### BL-SLOT-22 · Active-slot validation issue rows (clickable [name] message)
- status: pending
- review: keep
- observe: ERROR rows tint red (INFO rows plain); rows naming an object are clickable buttons '[name] message' that run proscenio.select_issue_object to select that object.
- intent: UNDOCUMENTED - surfaces per-slot validation issues (no children, broken default, child-bone mismatch, transform keys on child).
- code: apps/blender/panels/slots.py:167-168 -> _helpers.py:127-150 -> validation/active_slot.py:15-35

### BL-SLOT-04 · Slot row button (per slot, label = slot name, LINK_BLEND icon)
- status: pending
- review: keep
- pre: At least one slot Empty in the scene.
- steps:
  1. Open Slots panel > click a slot row.
- observe: That slot Empty becomes the sole selected + active object; the row shows depressed (depress=slot is active); the Active Slot subpanel appears. Missing/non-slot name reports a warning 'slot "<name>" not found' and CANCELLED.
- intent: Each row selects/activates that slot so the Active Slot subpanel surfaces its attachments.
- code: apps/blender/panels/slots.py:62-70 -> operators/slot/select.py:36-44

### BL-SLOT-07 · Create Slot button (ADD icon)
- status: pending
- review: keep
- pre: context.scene not None. Optionally: Pose Mode with active bone, OR Object Mode with meshes selected.
- steps:
  1. Pose Mode w/ active bone: click Create Slot. OR Object Mode: select meshes, click Create Slot.
- observe: A PLAIN_AXES Empty (size 0.1) named '<bone>.slot' (or 'slot') is linked to scene.collection, is_slot=True, parented BONE to active armature/bone (or wraps selected meshes via parent_keep_world centered on geometry center), and becomes sole selection; reports 'created slot ... wrapping N attachment(s)' or 'created empty slot ...'. Redo panel exposes 'Slot name' field.
- intent: Creates a slot Empty; with no mesh selected anchors at the active pose bone, with meshes selected wraps them as attachments under a fresh Empty parented to the active mesh's bone.
- code: apps/blender/panels/slots.py:78 -> operators/slot/create.py:68-114

### BL-SLOT-11 · Active Slot subpanel visibility (poll)
- status: pending
- review: keep
- steps:
  1. Make a slot Empty active (e.g. click its row) vs make a non-slot object active.
- observe: Subpanel appears only when active_object is non-None and is_slot_empty; hidden otherwise. Parent Slots panel stays visible regardless.
- intent: Shown when a slot Empty is the active object; lists the slot's child attachments.
- code: apps/blender/panels/slots.py:96-99

### BL-SLOT-17 · SOLO star toggle (per attachment, SOLO_ON/SOLO_OFF)
- status: pending
- review: keep
- pre: Slot Empty active with >=1 MESH child.
- steps:
  1. Click the star at the left of an attachment row.
- observe: props.slot_default set to that child's name; row shows filled SOLO_ON (embossed) for the default and SOLO_OFF for others; reports 'slot "<empty>" default = "<name>"'. Non-child name reports warning + CANCELLED. With no explicit default, the first sorted child shows SOLO_ON.
- intent: Marks which attachment is visible at scene load (the default visible child).
- code: apps/blender/panels/slots.py:138-148 -> operators/slot/attachment.py:70-104

### BL-SLOT-20 · Keyframe attachment button (per attachment, KEYFRAME_HLT)
- status: pending
- review: keep
- pre: Slot Empty active with the named attachment as a MESH child; a frame chosen.
- steps:
  1. Move the playhead to a frame > click the keyframe icon on an attachment row.
- observe: Sets empty[PROSCENIO_SLOT_INDEX]=index, inserts a keyframe at current frame, forces all keys on that fcurve to CONSTANT interpolation; reports 'keyed "<name>" (index N) at frame F'. Non-child name reports warning + CANCELLED.
- intent: UNDOCUMENTED - keys the chosen attachment visible from the current frame (the constant-interp slot swap exported as a Godot slot_attachment track).
- code: apps/blender/panels/slots.py:152-157 -> operators/slot/attachment.py:107-152

### BL-SLOT-21 · Add Selected Mesh button (ADD icon)
- status: pending
- review: keep
- pre: Slot Empty active AND at least one other MESH object also selected.
- steps:
  1. Select a slot Empty (active) plus a mesh > click Add Selected Mesh.
- observe: Each selected MESH is re-parented to the Empty via parent_keep_world (world transform preserved); reports 'added N attachment(s) to slot "<empty>"'. Button is poll-disabled (greyed) when no qualifying mesh is selected.
- intent: Adds the selected mesh as a new attachment (re-parents the selected mesh into the active slot Empty).
- code: apps/blender/panels/slots.py:159-165 -> operators/slot/attachment.py:40-67

## Skeleton panel: armature picker, bone list, pose helpers, Quick Armature, IK, authoring camera, pose library

### BL-SKEL-01 · Skeleton subpanel status badge (Godot-ready)
- status: pending
- review: keep
- observe: Custom Godot mark icon shows; hovering surfaces the band tooltip (proscenio.status_info with band='godot_ready').
- intent: UNDOCUMENTED - feature-band badge; Skeleton maps to GODOT_READY.
- code: apps/blender/panels/skeleton.py:83-84 -> _helpers.py:46-69

### BL-SKEL-02 · Skeleton subpanel '?' help button
- status: pending
- review: keep
- observe: proscenio.help fires with topic='skeleton'; help surface for docs/02-blender-addon/04-skeleton opens.
- intent: UNDOCUMENTED - opens the 'skeleton' help topic.
- code: apps/blender/panels/skeleton.py:84 -> _helpers.py:84-86

### BL-SKEL-03 · Active Armature picker (PointerProperty dropdown)
- status: pending
- review: keep
- observe: scene.proscenio.active_armature set to chosen object (poll=is_armature limits choices to armatures); clearing falls back to QuickRig auto-detect. Armature/Pose subpanels react to the pick.
- intent: The project-wide armature picker; single source of truth that bind/automesh/export target.
- code: apps/blender/panels/skeleton.py:94-96 -> scene_props.py:496-509

### BL-SKEL-04 · Exports: <name> (picked / first in scene) label
- status: pending
- review: keep
- observe: Shows '(picked)' when active_armature set, '(first in scene - no rig picked)' otherwise; EXPORT icon.
- intent: UNDOCUMENTED - read-only readout of what the writer will export.
- code: apps/blender/panels/skeleton.py:97-101

### BL-SKEL-05 · 'no Armature in scene - use Quick Armature below' warning
- status: pending
- review: keep
- observe: INFO-iconned label 'no Armature in scene - use Quick Armature below' appears.
- intent: UNDOCUMENTED - presence check telling the user to author a rig.
- code: apps/blender/panels/skeleton.py:103-105

### BL-SKEL-06 · 'no rig picked' info box + 'Use existing instead:' label
- status: pending
- review: keep
- observe: Boxed INFO label 'no rig picked - skeleton ops will create a new Proscenio.QuickRig' plus 'Use existing instead:' sublabel.
- intent: UNDOCUMENTED - warns that skeleton ops will create a new Proscenio.QuickRig.
- code: apps/blender/panels/skeleton.py:106-112

### BL-SKEL-08 · Armature subpanel status badge (Godot-ready) + '?' help
- status: pending
- review: keep
- observe: Godot mark badge (status_info band='godot_ready'); '?' fires proscenio.help topic='armature' (skeleton#armature).
- intent: UNDOCUMENTED - band badge + help topic 'armature'.
- code: apps/blender/panels/skeleton.py:139-140 -> _helpers.py:72-86

### BL-SKEL-09 · Armature 'Armature '<name>' - N bone(s)' header label
- status: pending
- review: keep
- observe: Label shows the picked armature name and exact bone count.
- intent: Read-only count of bones the writer would export for the picked rig.
- code: apps/blender/panels/skeleton.py:148-149

### BL-SKEL-10 · Bone list (PROSCENIO_UL_bones template_list)
- status: pending
- review: keep
- observe: Each row shows depth-indented bone name (BONE_DATA icon) plus a comma list of 'connected'/'relative' flags where set.
- intent: Read-only list of every bone (indented by depth) with connected/relative flags; inspection only, never edits the .proscenio.
- code: apps/blender/panels/skeleton.py:150-158, 25-65

### BL-SKEL-12 · Pose Mode subpanel status badge (blender-only) + '?' help
- status: pending
- review: keep
- observe: Blender mark badge (band='blender_only'); '?' opens help topic='pose_mode' (skeleton#pose-mode).
- intent: UNDOCUMENTED badge; doc says Pose Mode ops are 'blender-only'. Help topic 'pose_mode'.
- code: apps/blender/panels/skeleton.py:172-173 -> _helpers.py:72-86

### BL-SKEL-13 · 'enter Pose mode to bake / save poses' info label
- status: pending
- review: keep
- observe: INFO label shown and the four pose operators are hidden.
- intent: UNDOCUMENTED - gate message when not in Pose mode.
- code: apps/blender/panels/skeleton.py:177-179

### BL-SKEL-18 · Quick Armature subpanel status badge (blender-only) + '?' help
- status: pending
- review: keep
- observe: Blender mark badge (band='blender_only'); '?' opens help topic='quick_armature' (skeleton#quick-armature).
- intent: UNDOCUMENTED badge; Quick Armature is blender-only. Help topic 'quick_armature'.
- code: apps/blender/panels/skeleton.py:207-208 -> _helpers.py:72-86

### BL-SKEL-28 · Quick Armature: 3D preview overlay (line, anchor, axis guide, press-point marker)
- status: pending
- review: keep
- observe: Orange(connected)/cyan(unparented)/yellow(disconnected)/red(outside-canvas) line head->cursor, anchor circle, dashed parent link (disconnected), faint press-point marker (connected).
- intent: UNDOCUMENTED - live GPU preview of the bone being drawn, colour-coded by chord.
- code: apps/blender/operators/armature/_overlay.py:47-141

### BL-SKEL-29 · Quick Armature: 'outside canvas' cursor warning tooltip (2D)
- status: pending
- review: keep
- observe: Red 'outside canvas' tooltip near cursor; preview turns red; PRESS over overlay ignored, RELEASE cancels in-flight drag.
- intent: UNDOCUMENTED - warns when the cursor leaves the invoking viewport canvas.
- code: apps/blender/operators/armature/_overlay.py:144-167

### BL-SKEL-30 · Quick Armature: status-bar + viewport-header chord cheatsheet
- status: pending
- review: keep
- observe: Both render EVENT_* icon chords: LMB drag=connected/unparented (per default_chain), Shift+drag, Alt+drag=disconnected, X/Z=axis lock, Ctrl=grid snap, Ctrl+Z=undo, Enter=confirm, Esc=exit.
- intent: UNDOCUMENTED in 04-skeleton (links to walkthrough cheatsheet) - icon-rich chord vocabulary.
- code: apps/blender/operators/armature/quick_armature.py:739-758,892-917 -> _status_bar.py:23-47

### BL-SKEL-31 · Quick Armature F3-redo: 'Lock to Front Orthographic' operator prop
- status: pending
- review: keep
- observe: When ON, view snaps to Front Ortho on invoke and restores pre-snap view on exit (unless user orbited mid-modal). When OFF, view is untouched.
- intent: Per-invoke override: switch to Front Ortho on invoke and restore on exit (sets the front-ortho lock).
- code: apps/blender/operators/armature/quick_armature.py:95-103,221-222,657-710

### BL-SKEL-32 · Quick Armature option: 'Lock to Front Orthographic' (PG default)
- status: pending
- review: keep
- observe: scene.proscenio.quick_armature.lock_to_front_ortho persists and seeds the modal's invoke default (note: only overridable per-invoke via the operator prop).
- intent: The options box sets the front-ortho lock.
- code: apps/blender/panels/skeleton.py:217 -> scene_props.py:29-37

### BL-SKEL-33 · Quick Armature option: 'Default = chain connected'
- status: pending
- review: keep
- observe: quick_armature.default_chain persists; modal reads it at invoke to set no-modifier vs Shift chord semantics and the cheatsheet labels.
- intent: The options box sets the chain default.
- code: apps/blender/panels/skeleton.py:218 -> scene_props.py:46-56

### BL-SKEL-34 · Quick Armature option: 'Bone name prefix'
- status: pending
- review: keep
- observe: quick_armature.name_prefix persists; modal sanitizes it (whitespace stripped, empty->'qbone') and names bones '<prefix>.000', '<prefix>.001'.
- intent: The options box sets the name prefix.
- code: apps/blender/panels/skeleton.py:219 -> scene_props.py:38-45

### BL-SKEL-35 · Quick Armature option: 'Snap increment'
- status: pending
- review: keep
- observe: quick_armature.snap_increment persists; modal uses it as the Ctrl-held world-unit grid step.
- intent: The options box sets the grid snap.
- code: apps/blender/panels/skeleton.py:220 -> scene_props.py:57-67

### BL-SKEL-07 · Use existing armature button(s) (one per scene armature)
- status: pending
- review: keep
- pre: Armatures exist, picker empty (the 'no rig picked' box).
- steps:
  1. Click a per-armature button in the 'Use existing instead' column.
- observe: proscenio.set_active_armature runs; scene.proscenio.active_armature = that object; box disappears, picker now shows it. Empty/missing/non-armature names warn and CANCEL.
- intent: UNDOCUMENTED - one-click set the explicit Proscenio target to a named armature.
- code: apps/blender/panels/skeleton.py:113-120 -> skeleton_target.py:36-52

### BL-SKEL-11 · Bone row click (select_bone_by_name)
- status: pending
- review: keep
- pre: Picked armature with bones; row visible.
- steps:
  1. Click a bone name in the UIList.
- observe: proscenio.select_bone_by_name runs: only the armature is selected, bones.active set, in Pose mode only that pose bone selected, active_bone_index synced. Missing armature/bone warns + CANCELs.
- intent: Click a bone to select it in the viewport.
- code: apps/blender/panels/skeleton.py:52-58 -> selection.py:62-93

### BL-SKEL-14 · Bake Current Pose button
- status: pending
- review: keep
- pre: Pose mode, active object is the armature.
- steps:
  1. Enter Pose mode > click 'Bake Current Pose'.
- observe: loc/rot(quat+euler)/scale keyframes inserted on every pose bone of context.active_object at frame_current; report 'baked pose at frame N for M bone(s)'.
- intent: Keys every bone at the playhead (those keys do export).
- code: apps/blender/panels/skeleton.py:180 -> pose_library.py:117-147

### BL-SKEL-15 · Toggle IK button
- status: pending
- review: keep
- pre: Pose mode; an active pose bone.
- steps:
  1. Select a pose bone > click 'Toggle IK' (click again to remove).
- observe: First click: creates a non-deform control bone '<bone>.IK' at the chain tip and a 'Proscenio IK' constraint (chain_count=2) targeting it. Second click removes both (our control bones only).
- intent: Adds or removes a test IK constraint.
- code: apps/blender/panels/skeleton.py:181 -> authoring_ik.py:73-128

### BL-SKEL-16 · Bake IK to Keyframes button
- status: pending
- review: keep
- pre: Pose mode; active pose bone carries an IK constraint.
- steps:
  1. Select an IK-constrained bone > click 'Bake IK to Keyframes'.
- observe: Chain bones selected; bpy.ops.nla.bake over action/scene range with visual_keying + clear_constraints; report 'baked IK chain ... over frames a-b'. No-IK bone path is poll-gated off.
- intent: UNDOCUMENTED - bakes the active bone's IK chain to keyframes (visual keying) and clears the IK constraint.
- code: apps/blender/panels/skeleton.py:182 -> authoring_ik.py:173-218

### BL-SKEL-17 · Save Pose to Library button
- status: pending
- review: keep
- pre: Pose mode; active armature with pose bones; a writable Asset Library configured.
- steps:
  1. Enter Pose mode > click 'Save Pose to Library'.
- observe: Wraps poselib.create_pose_asset with name '<action>.<frame>'/'<armature>.<frame>' into the first writable library. Without a writable library: ERROR report + CANCEL.
- intent: Stores the pose as a Blender asset.
- code: apps/blender/panels/skeleton.py:183-187 -> pose_library.py:27-94

### BL-SKEL-19 · Quick Armature button (modal launch)
- status: pending
- review: keep
- pre: Active area is a 3D viewport (operator poll).
- steps:
  1. Open Quick Armature subpanel > click 'Quick Armature'.
- observe: Modal starts: ensures/creates Proscenio.QuickRig target, snapshots view+selection, optionally snaps Front Ortho, registers preview + cheatsheet overlays, reports 'modal active'.
- intent: Modal viewport tool that draws bones one press-drag at a time onto the Y=0 picture plane without entering Edit Mode.
- code: apps/blender/panels/skeleton.py:212 -> quick_armature.py:150-231

### BL-SKEL-20 · Quick Armature: LMB press-drag (default chord = connected/unparented)
- status: pending
- review: keep
- pre: Modal active, cursor inside the invoking viewport canvas.
- steps:
  1. Press LMB inside viewport, drag, release.
- observe: A bone is created on Y=0 (head snaps to parent tail when connected). Bone shorter than tolerance reports 'bone too short, skipped'. Chord label honours default_chain (ON=connected, OFF=unparented).
- intent: Draws a bone head->tail; default no-modifier drag chains onto the previous bone.
- code: apps/blender/operators/armature/quick_armature.py:262-263,364-425,523-589

### BL-SKEL-21 · Quick Armature: Shift+LMB-drag chord
- status: pending
- review: keep
- pre: Modal active; at least one prior bone for chaining.
- steps:
  1. Hold Shift, press-drag-release in the viewport.
- observe: Mode flips relative to default_chain: with default_chain ON, Shift => unparented root; with OFF, Shift => connected chain. Preview tints cyan(unparented).
- intent: Hold Shift to chain onto the previous bone (per bl_description) / start a new root (per default_chain ON).
- code: apps/blender/operators/armature/quick_armature.py:380-391, _status_bar.py:40-42, core resolve_press_mode

### BL-SKEL-22 · Quick Armature: Alt+LMB-drag chord (disconnected)
- status: pending
- review: keep
- pre: Modal active; a prior bone exists.
- steps:
  1. Hold Alt, press-drag-release.
- observe: Bone parented to last but head left at press point; dashed parent-link line drawn; preview tinted yellow (disconnected).
- intent: UNDOCUMENTED in 04-skeleton (cheatsheet in walkthrough) - parented but free head.
- code: apps/blender/operators/armature/quick_armature.py:382-391, _status_bar.py:42, _overlay.py:59-62

### BL-SKEL-23 · Quick Armature: X / Z axis-lock keys
- status: pending
- review: keep
- pre: Modal active.
- steps:
  1. Press X (then Z) with no modifiers during the modal.
- observe: Axis lock toggles X/Z/off; a red(X)/blue(Z) guideline through the head; tail clamps to that axis; report 'axis lock = X/Z/off'.
- intent: UNDOCUMENTED in 04-skeleton - constrain the drag to the X or Z world axis (Y=0 plane).
- code: apps/blender/operators/armature/quick_armature.py:251-253,266-275,859-872 -> _overlay.py:123-141

### BL-SKEL-24 · Quick Armature: Ctrl (grid snap)
- status: pending
- review: keep
- pre: Modal active.
- steps:
  1. Hold Ctrl while moving/pressing/releasing.
- observe: Cursor/head/tail X,Z snap to multiples of snap_increment (default 1.0); preview follows snapped point.
- intent: UNDOCUMENTED in 04-skeleton - hold Ctrl to snap head/tail to the snap_increment grid.
- code: apps/blender/operators/armature/quick_armature.py:244,312-313,377-378,467-468

### BL-SKEL-25 · Quick Armature: Ctrl+Z undo / Ctrl+Shift+Z redo (in-modal)
- status: pending
- review: keep
- pre: Modal active; >=1 bone authored this session.
- steps:
  1. Author a bone > press Ctrl+Z (then Ctrl+Shift+Z).
- observe: Ctrl+Z removes the last session bone (report 'undone'); Ctrl+Shift+Z recreates it; empty stacks report 'nothing to undo/redo'.
- intent: UNDOCUMENTED in 04-skeleton - in-session undo/redo of authored bones.
- code: apps/blender/operators/armature/quick_armature.py:245-250,591-636,851-856

### BL-SKEL-26 · Quick Armature: Enter / Numpad-Enter confirm
- status: pending
- review: keep
- pre: Modal active.
- steps:
  1. Press Enter (or Numpad Enter).
- observe: Modal exits FINISHED; overlays/handlers removed, view+selection restored, report 'confirmed (N bone(s) authored)'.
- intent: UNDOCUMENTED in 04-skeleton - confirm and exit the modal keeping authored bones.
- code: apps/blender/operators/armature/quick_armature.py:239-240,803-822,847-848

### BL-SKEL-27 · Quick Armature: Esc / RMB cancel
- status: pending
- review: keep
- pre: Modal active.
- steps:
  1. Press Esc or right-click.
- observe: Modal exits. With no in-flight drag and no bone drawn yet it CANCELs; an empty auto-created QuickRig is swept; view/selection restored; report 'cancelled (N bone(s))'.
- intent: Esc or right-click to exit (per bl_description).
- code: apps/blender/operators/armature/quick_armature.py:236-238,803-822,843-844

### BL-SKEL-36 · Preview Camera (create_ortho_camera) - listed in surface, drawn in Helpers panel
- status: pending
- review: keep
- pre: Any scene with proscenio props.
- steps:
  1. (Helpers panel) click 'Preview Camera', or F3 'Preview Camera'.
- observe: Creates/updates Proscenio.PreviewCam at (0,-10,0) facing +Y, type ORTHO, ortho_scale = max(res_x,res_y)/ppu; sets scene.camera, selects it. NOTE: not rendered on the Skeleton surface.
- intent: UNDOCUMENTED in 04-skeleton - adds/focuses an ortho camera sized to pixels_per_unit.
- code: apps/blender/operators/armature/authoring_camera.py:16-53; drawn at apps/blender/panels/helpers.py:32

### BL-SKEL-37 · Set Bone Mode (set_bone_mode) - listed in surface, belongs to Skinning panel
- status: pending
- review: keep
- pre: Active object is a MESH (operator poll).
- steps:
  1. (Skinning panel bind sub-box) toggle a per-bone mode row.
- observe: Writes obj['proscenio_bone_modes'] JSON; CLEAR drops the override. NOTE: this control does NOT appear on the Skeleton panel - it is INTERNAL and Skinning-owned.
- intent: UNDOCUMENTED in 04-skeleton - overrides per-bone bind mode SOFT/HARD/CLEAR (a Skinning feature).
- code: apps/blender/operators/skinning/set_bone_mode.py:23-62

## Mesh Generation panel: automesh one-click + interactive modal + debug pipeline

### BL-MESH-01 · Parent panel empty-state label: "select a mesh to generate or edit"
- status: pending
- review: keep
- observe: Panel body shows only the INFO-icon line "select a mesh to generate or edit"; no props/buttons drawn
- intent: UNDOCUMENTED (guard label shown when no MESH is active)
- code: apps/blender/panels/mesh_generation.py:63

### BL-MESH-02 · Parent panel sprite-guard labels: "mesh tools are mesh-only (this is a sprite)" + "to rig a sprite, parent it to a bone: Ctrl+P > Bone"
- status: pending
- review: keep
- observe: Two INFO lines appear; no automesh props/buttons; subpanels hidden (their poll returns False for sprites)
- intent: UNDOCUMENTED (warn-not-hide: a sprite element is a Blender mesh but meshing replaces its quad)
- code: apps/blender/panels/mesh_generation.py:68-69

### BL-MESH-03 · Picker readout row ("Picker: <armature>" / "Picker: (none - set in Skeleton panel)")
- status: pending
- review: keep
- observe: With armature: ARMATURE_DATA icon + "Picker: <name>"; without: INFO icon + "(none - set in Skeleton panel)"
- intent: Parent panel holds the picker readout
- code: apps/blender/panels/mesh_generation.py:72 -> _helpers.py:111

### BL-MESH-04 · Interior Mode selector (automesh_interior_mode: Simple / Dense)
- status: pending
- review: keep
- observe: Enum value flips; the dense-only fields in Automesh-from-Alpha grey/ungrey; interactive modal stage count changes (5 vs 6) on next run
- intent: Parent holds the Interior Mode selector (Simple = sparse, Dense = filled)
- code: apps/blender/panels/mesh_generation.py:74 (prop) / properties/scene_props.py:137

### BL-MESH-05 · Mesh Generation panel header status badge
- status: pending
- review: keep
- observe: Hover shows band tooltip; click opens the status-legend help popup (via proscenio.status_info -> proscenio.help topic=status_legend)
- intent: UNDOCUMENTED (band badge for feature 'mesh_generation' = blender-only)
- code: apps/blender/panels/mesh_generation.py:57 -> _helpers.py:46/83

### BL-MESH-06 · Mesh Generation panel header "?" help button
- status: pending
- review: keep
- observe: invoke_popup opens the mesh_generation help topic (title/summary/sections + Open online docs)
- intent: UNDOCUMENTED (help button; topic 'mesh_generation')
- code: apps/blender/panels/mesh_generation.py:57 -> _helpers.py:84

### BL-MESH-07 · Automesh from Alpha subpanel header (status badge + "?" help)
- status: pending
- review: keep
- observe: Badge tooltip on hover; "?" opens the automesh_alpha help popup
- intent: UNDOCUMENTED (subpanel header badge + help, topic 'automesh_alpha')
- code: apps/blender/panels/mesh_generation.py:93 -> _helpers.py:72

### BL-MESH-08 · Trace resolution (automesh_resolution)
- status: pending
- review: keep
- observe: Value clamps to 0.01-1.0; feeds downscale_factor on next Automesh from Alpha run (finer/coarser outline)
- intent: Image downscale factor; higher traces a finer silhouette but costs more; sets outline fidelity, not vertex count
- code: apps/blender/panels/mesh_generation.py:156 / scene_props.py:80

### BL-MESH-09 · Alpha threshold (automesh_alpha_threshold)
- status: pending
- review: keep
- observe: Value clamps 0-255; raising it (e.g. 127) drops faint anti-alias edge pixels on next run
- intent: UNDOCUMENTED (pixels with alpha strictly above this contribute to the silhouette; default 1)
- code: apps/blender/panels/mesh_generation.py:157 / scene_props.py:95

### BL-MESH-10 · Boundary margin (annulus) (automesh_margin_pixels, drawn label "Margin (px)" on operator redo)
- status: pending
- review: keep
- observe: Value clamps 0-100; >0 produces dilated-outer + eroded-inner annulus topology on next run
- intent: UNDOCUMENTED (source-pixel margin that builds an annulus topology; 0 = single-contour flat fill)
- code: apps/blender/panels/mesh_generation.py:158 / scene_props.py:109

### BL-MESH-11 · Contour vertices (automesh_contour_vertices)
- status: pending
- review: keep
- observe: Value clamps 8-512; sets target outer-contour vertex count after smoothing+resample (inner uses half)
- intent: Use Contour vertices for the outline vertex count
- code: apps/blender/panels/mesh_generation.py:159 / scene_props.py:125

### BL-MESH-12 · Interior spacing (automesh_interior_spacing)
- status: pending
- review: keep
- observe: World-unit Steiner grid spacing; lower = denser interior; also read by the interactive modal in SIMPLE mode (resample + fold snap radius)
- intent: Use Interior spacing for the fill
- code: apps/blender/panels/mesh_generation.py:163 / scene_props.py:161

### BL-MESH-13 · Preserve base quad (preserve_base_quad)
- status: pending
- review: keep
- observe: ON keeps the proscenio_base_sprite quad corners as loose verts; OFF removes them on next run
- intent: UNDOCUMENTED (keep/delete the 4 original quad corner verts after automesh; OFF deletes)
- code: apps/blender/panels/mesh_generation.py:165 / scene_props.py:205

### BL-MESH-14 · Preserve weights on regen (preserve_on_regen) - alpha subpanel mirror
- status: pending
- review: keep
- observe: ON: weights snapshot + reproject (INFO reports reprojected/auto-seed counts); OFF: weights wiped (legacy)
- intent: UNDOCUMENTED (when ON, regen snapshots weights, rebuilds mesh, reprojects via UV anchors)
- code: apps/blender/panels/mesh_generation.py:168 / scene_props.py:287

### BL-MESH-15 · Density follows bones (automesh_density_under_bones) - dense-only greyed column
- status: pending
- review: keep
- observe: Greyed/inactive in Simple mode; in Dense, ON enables bone-aware interior fill (requires picker armature with deform bones at run)
- intent: Dense only, off by default; packs more triangles near the picker's bones
- code: apps/blender/panels/mesh_generation.py:173 (active=is_dense) / scene_props.py:174

### BL-MESH-16 · Bone influence radius (automesh_bone_radius) - dense+density-on greyed sub-column
- status: pending
- review: keep
- observe: Active only when both conditions hold; feeds bone_density_radius on next run
- intent: UNDOCUMENTED (world-unit radius around each bone segment where density subdivision applies)
- code: apps/blender/panels/mesh_generation.py:176 (active=is_dense and density_under_bones) / scene_props.py:184

### BL-MESH-17 · Bone density factor (automesh_bone_factor) - dense+density-on greyed sub-column
- status: pending
- review: keep
- observe: Active only when both conditions hold; feeds bone_density_factor on next run
- intent: UNDOCUMENTED (multiplier for interior density near bones; 1-8)
- code: apps/blender/panels/mesh_generation.py:177 (active=is_dense and density_under_bones) / scene_props.py:194

### BL-MESH-20 · Automesh Interactive subpanel header (status badge + "?" help)
- status: pending
- review: keep
- observe: Badge tooltip; "?" opens automesh_interactive help popup
- intent: UNDOCUMENTED (subpanel header badge + help, topic 'automesh_interactive')
- code: apps/blender/panels/mesh_generation.py:116 -> _helpers.py:72

### BL-MESH-21 · Interactive subpanel label "Interactive trace and edit"
- status: pending
- review: keep
- observe: Read-only label "Interactive trace and edit" rendered at top of subpanel body
- intent: UNDOCUMENTED (static descriptive label)
- code: apps/blender/panels/mesh_generation.py:195

### BL-MESH-22 · Loops field (authoring_inner_loop_count, label "Loops")
- status: pending
- review: keep
- observe: Value clamps 0-10; controls inner-loop count consumed at the INNER_LOOPS stage of the modal (DENSE only; SIMPLE has no inner-loops stage)
- intent: UNDOCUMENTED (concentric inner polylines via erosion; only used by DENSE modal)
- code: apps/blender/panels/mesh_generation.py:198 / scene_props.py:310

### BL-MESH-23 · Spacing field (authoring_inner_loop_spacing, label "Spacing")
- status: pending
- review: keep
- observe: Value clamps; feeds inner_loop_spacing in _snapshot_params; only affects DENSE inner-loops stage
- intent: UNDOCUMENTED (world-unit gap between adjacent inner loops in the modal)
- code: apps/blender/panels/mesh_generation.py:199 / scene_props.py:322

### BL-MESH-24 · Cut margin field (authoring_cut_margin, label "Cut margin")
- status: pending
- review: keep
- observe: Value clamps; widens/narrows the CDT-hole corridor that cut strokes carve at APPLY
- intent: UNDOCUMENTED (corridor width carved by cut strokes; clamped to 0.01 min)
- code: apps/blender/panels/mesh_generation.py:201 / scene_props.py:333

### BL-MESH-25 · Preserve weights on regen (preserve_on_regen) - interactive subpanel mirror
- status: pending
- review: keep
- observe: Same scene prop as the alpha mirror (BL-MESH-14); APPLY of the modal reprojects weights when ON, wipes when OFF
- intent: UNDOCUMENTED (mirror of the regen weight-preserve toggle next to the interactive trigger)
- code: apps/blender/panels/mesh_generation.py:205 / scene_props.py:287

### BL-MESH-26 · Author Mesh (interactive) button enabled/greyed state
- status: pending
- review: keep
- observe: Enabled only when obj is MESH with data and at least one material TEX_IMAGE node carrying an image; greyed otherwise
- intent: Button greys out when active obj is not MESH or has no image texture (UX cue mirroring modal invoke validation)
- code: apps/blender/panels/mesh_generation.py:206-212 / _authoring_button_enabled:217

### BL-MESH-27 · Interactive subpanel "select a mesh first" label
- status: pending
- review: keep
- observe: INFO line "select a mesh first" below the button
- intent: UNDOCUMENTED (fallback INFO label when no mesh active)
- code: apps/blender/panels/mesh_generation.py:213-214

### BL-MESH-34 · Modal: live param re-snapshot timer tick
- status: pending
- review: keep
- observe: On next timer tick the current stage recomputes + overlay refreshes; flipping Interior Mode mid-modal rebuilds the stage list (snaps off INNER_LOOPS to EDIT_OUTLINE when switching to Simple)
- intent: UNDOCUMENTED (panel param edits during the modal recompute the current stage live)
- code: apps/blender/operators/automesh/automesh_authoring.py:348,355

### BL-MESH-37 · Modal pen chords: X/Z axis-lock, wheel/0-9 subdivisions, Alt+click delete, Ctrl+Z undo
- status: pending
- review: keep
- observe: Axis lock toggles guide line; subdiv count updates tooltip + ghost verts (capped at 20); Alt+click removes hovered stroke; Ctrl+Z drops last pen vert, else last committed stroke
- intent: UNDOCUMENTED (pen editing chords surfaced only in the modal statusbar)
- code: apps/blender/operators/automesh/automesh_authoring.py:599-624 / _status_bar.py:36-40

### BL-MESH-38 · Modal statusbar chord layout + GPU viewport overlays + cursor tooltip
- status: pending
- review: keep
- observe: Statusbar shows "Automesh: N/M Name" + stage chords (next/back/cancel + pen chords on pen stages); viewport draws contour/steiner/preview overlays; cursor tooltip reflects held modifier
- intent: UNDOCUMENTED (GPU overlay + bottom-bar chord hints + per-cursor tooltip)
- code: apps/blender/operators/automesh/automesh_authoring.py:1305 / _status_bar.py:19-43

### BL-MESH-39 · Debug Pipeline subpanel header (status badge + "?" help)
- status: pending
- review: keep
- observe: Subpanel only visible with debug mode on; badge tooltip; "?" opens debug_pipeline help popup
- intent: A developer aid, shown only with debug mode on
- code: apps/blender/panels/mesh_generation.py:139 / poll:135 -> debug_mode_enabled

### BL-MESH-40 · Debug stage enum (debug_stage)
- status: pending
- review: keep
- observe: Non-final stages skip the bmesh write and emit a wireframe companion into Proscenio.Debug; INFO reports "automesh DEBUG '<stage>': ..."; Off/Final run the full pipeline
- intent: Pick a stage of the trace; the next run leaves a wireframe companion in the Proscenio.Debug collection
- code: apps/blender/panels/mesh_generation.py:244 / scene_props.py:346 / automesh.py:150,308

### BL-MESH-18 · Automesh from Alpha button (proscenio.automesh_from_alpha)
- status: pending
- review: keep
- pre: Active mesh element with a TEX_IMAGE material image of nonzero size
- steps:
  1. Set params > click "Automesh from Alpha" (MOD_REMESH icon)
- observe: Mesh rebuilt from alpha contour; INFO report "automesh built: N outer + N inner + N interior = N total, N faces"; REGISTER/UNDO so F3 redo re-iterates params
- intent: A one-shot trace: walks the image alpha contour into an annulus mesh; re-runs preserve the UV-pinned base quad
- code: apps/blender/panels/mesh_generation.py:178 / operators/automesh/automesh.py:62,193

### BL-MESH-19 · Automesh from Alpha - no-image / zero-size / sprite / non-mesh failure paths
- status: pending
- review: keep
- pre: Active mesh with no material image, OR a zero-size image, OR a sprite element
- steps:
  1. Run the operator on each failure case (sprite via F3 search since panel hides button)
- observe: Sprite: WARN + CANCELLED; no image: ERROR "no image texture" + CANCELLED; zero size: ERROR + CANCELLED; large image (>4096): WARN but still proceeds
- intent: UNDOCUMENTED (preflight guards reporting and cancelling)
- code: apps/blender/operators/automesh/automesh.py:195-209,257-279

### BL-MESH-28 · Author Mesh (interactive) - launch modal (proscenio.automesh_authoring)
- status: pending
- review: keep
- pre: Active mesh element with a TEX_IMAGE image; pose mode not required
- steps:
  1. Click "Author Mesh (interactive)"
- observe: Modal starts (RUNNING_MODAL): session captured, GPU overlay registered, timer added, statusbar chord row appears; stage 1/N OUTER overlay drawn
- intent: A modal preview of the same trace; advance through stages; nothing written until the final stage commits
- code: apps/blender/panels/mesh_generation.py:208 / operators/automesh/automesh_authoring.py:170,210

### BL-MESH-29 · Modal invoke guards (non-mesh / sprite / no-image)
- status: pending
- review: keep
- pre: Active object not MESH, OR a sprite element, OR mesh without image
- steps:
  1. Invoke on each invalid case
- observe: Non-mesh/no-image: ERROR + CANCELLED; sprite: WARN + CANCELLED; setup exception: ERROR + state restored + CANCELLED
- intent: UNDOCUMENTED (invoke-time validation; modal also has setup-failure restore)
- code: apps/blender/operators/automesh/automesh_authoring.py:211-229,321-324

### BL-MESH-30 · Modal: ENTER / NUMPAD_ENTER (advance stage)
- status: pending
- review: keep
- pre: Modal running, not on last stage
- steps:
  1. Press Enter to step OUTER -> EDIT_OUTLINE -> [INNER_LOOPS] -> EDIT_INTERIOR_POINTS -> PREVIEW_INTERIOR -> APPLY
- observe: Stage label increments (N/M); stage-specific compute runs; overlay refreshes; INFO reports e.g. "<N> outer verts"; on APPLY it commits and finishes
- intent: Advance through the stages; commit only on the final stage
- code: apps/blender/operators/automesh/automesh_authoring.py:344,987

### BL-MESH-31 · Modal: BACKSPACE (retreat stage)
- status: pending
- review: keep
- pre: Modal running, not on first stage
- steps:
  1. Advance a few stages > press BACKSPACE
- observe: Stage decrements to previous in the active-mode order; pen stages reset draw state; overlay refreshes; INFO stage-entry report
- intent: Step back through the stages without committing
- code: apps/blender/operators/automesh/automesh_authoring.py:346,1068

### BL-MESH-32 · Modal: ESC (cancel session)
- status: pending
- review: keep
- pre: Modal running at any stage
- steps:
  1. Press ESC
- observe: Overlay unregistered, timer removed, statusbar removed, captured session restored; INFO "Authoring modal restored"; CANCELLED (no geometry change)
- intent: ESC cancels; nothing is written
- code: apps/blender/operators/automesh/automesh_authoring.py:342 / _finish:1264

### BL-MESH-33 · Modal: APPLY commit (final stage ENTER)
- status: pending
- review: keep
- pre: Modal on PREVIEW_INTERIOR; ENTER to APPLY
- steps:
  1. Reach last-but-one stage > press ENTER
- observe: apply_mesh writes geometry; INFO "Authoring applied: N verts, N faces"; dropped-vert WARN if any stroke verts fell outside; on CDT ValueError reports error and stays (no commit)
- intent: Commit the final mesh after confirming the last stage
- code: apps/blender/operators/automesh/automesh_authoring.py:1015-1038

### BL-MESH-35 · Modal Stage 2 (EDIT_OUTLINE) toggle-pen: Shift-tap extend / Ctrl-tap cut
- status: pending
- review: keep
- pre: Modal on EDIT_OUTLINE stage
- steps:
  1. Tap Shift (enter extend-pen) or tap Ctrl (cut-pen) > LMB place verts / drag free-draw > RMB or Enter to finish
- observe: Tooltip shows "Extend/Cut pen ..."; committed extend reshapes the spliced outer preview; committed cut reports running "N cut(s)" (corridor carved only at APPLY)
- intent: Cut / extend the outline as a modal stage
- code: apps/blender/operators/automesh/automesh_authoring.py:365,458,486

### BL-MESH-36 · Modal Stage 4 (EDIT_INTERIOR_POINTS) toggle-pen: click point / Shift-fold / Ctrl-cut
- status: pending
- review: keep
- pre: Modal on EDIT_INTERIOR_POINTS stage
- steps:
  1. Plain LMB click = drop a Steiner point; tap Shift = fold-pen; tap Ctrl = cut-pen; draw + finish
- observe: Points/strokes persist via write_user_strokes; tooltip flips warn-red when a gesture aims outside the silhouette; strokes feed the triangulation preview / Steiner cloud
- intent: Place interior points as a modal stage
- code: apps/blender/operators/automesh/automesh_authoring.py:452,539,933

### BL-MESH-41 · Clear Debug Companions button (proscenio.clear_automesh_debug)
- status: pending
- review: keep
- pre: Debug Pipeline subpanel open; companions exist in Proscenio.Debug for the active sprite
- steps:
  1. Click "Clear Debug Companions" (TRASH icon)
- observe: All debug companions for the active object removed; INFO "removed N debug companion(s) for '<name>'"; REGISTER/UNDO
- intent: Clear Debug Companions removes the wireframe companions
- code: apps/blender/panels/mesh_generation.py:245 / automesh.py:339,356

## Weight Paint panel: five bind modes, Edit Weights modal, brush preset, copy weights, sidecar IO, snapshot restore

### BL-WPAINT-01 · Mesh-only hint label ('select a mesh element (Weight Paint is mesh-only)')
- status: pending
- review: keep
- observe: Panel body shows only the INFO-icon label 'select a mesh element (Weight Paint is mesh-only)'; all subpanels (Bind/Edit/Snapshot/Transfer) are absent (their poll returns False).
- intent: The panel is mesh-only - it warns when the active element is a sprite.
- code: apps/blender/panels/weight_paint.py:51

### BL-WPAINT-02 · Picker readout row ('Picker: <armature>' / '(none - set in Skeleton panel)')
- status: pending
- review: keep
- observe: With picker set: 'Picker: <armature name>' with ARMATURE_DATA icon. Without: 'Picker: (none - set in Skeleton panel)' with INFO icon.
- intent: Surfaces the picker readout (shared affordance with Mesh Generation).
- code: apps/blender/panels/weight_paint.py:53 -> _helpers.py:111

### BL-WPAINT-03 · Weight Paint header status badge
- status: pending
- review: keep
- observe: Status-band icon shows; hovering surfaces the band-specific tooltip via proscenio.status_info; clicking is emboss=False info-only.
- intent: UNDOCUMENTED
- code: apps/blender/panels/weight_paint.py:46 -> _helpers.py:83

### BL-WPAINT-04 · Weight Paint header '?' help button
- status: pending
- review: keep
- observe: proscenio.help fires with topic 'weight_paint' (resolves to docs anchor weight-paint).
- intent: UNDOCUMENTED (help affordance maps to weight-paint doc page).
- code: apps/blender/panels/weight_paint.py:46 -> _helpers.py:84

### BL-WPAINT-05 · Bind subpanel header status badge + '?' help button
- status: pending
- review: keep
- observe: proscenio.help fires with topic 'bind' (anchor weight-paint#bind); status badge surfaces band tooltip.
- intent: UNDOCUMENTED (per-subpanel help/status affordance).
- code: apps/blender/panels/weight_paint.py:72 -> _helpers.py:83-85

### BL-WPAINT-06 · Mode dropdown (Bind mode enum: Bone Heat / Proximity / Envelope / Single nearest / Empty)
- status: pending
- review: keep
- observe: Five entries selectable; selection persists on scene.proscenio.skinning.bind_init_mode and seeds bind_mesh.invoke(); changing it also toggles whether the per-bone override box draws rows vs the Bone-Heat hint.
- intent: Mode picks the bind algorithm; Bone Heat is native default, the other four are F3-redo fallbacks.
- code: apps/blender/panels/weight_paint.py:174 (prop) ; properties/scene_props.py:218 (enum def)

### BL-WPAINT-07 · Target label ('Target: <picker>' / 'Target: (no picker armature)')
- status: pending
- review: keep
- observe: ARMATURE_DATA-icon label reads 'Target: <picker name>' or 'Target: (no picker armature)'.
- intent: Shows the target armature the mesh will bind to.
- code: apps/blender/panels/weight_paint.py:176

### BL-WPAINT-08 · Per-bone overrides box header label ('Per-bone Soft/Hard overrides:')
- status: pending
- review: keep
- observe: A box appears titled 'Per-bone Soft/Hard overrides:'. With 0 bones the box does not draw (early return at line 211).
- intent: Per-bone Soft/Hard overrides a single bone's falloff; no override uses the mode default family.
- code: apps/blender/panels/weight_paint.py:213

### BL-WPAINT-09 · Override box Bone-Heat hint ('applies only to the planar modes - Bone Heat ignores these')
- status: pending
- review: keep
- observe: Box shows only the INFO hint 'applies only to the planar modes - Bone Heat ignores these'; NO per-bone Soft/Hard/Clear rows are drawn.
- intent: A bone with no override uses the mode default; overrides apply only to planar modes (Bone Heat returns before override pass).
- code: apps/blender/panels/weight_paint.py:215 ; bone_modes.py:59 overrides_apply_under_bind_mode

### BL-WPAINT-15 · Edit Weights subpanel header status badge + '?' help button
- status: pending
- review: keep
- observe: proscenio.help topic 'edit_weights' (anchor weight-paint#edit-weights).
- intent: UNDOCUMENTED (per-subpanel affordance).
- code: apps/blender/panels/weight_paint.py:97 -> _helpers.py:83-85

### BL-WPAINT-16 · Active group label ('Active group: <name>')
- status: pending
- review: keep
- observe: Reads 'Active group: <vg name>' or '(none)' (no groups) or '(no mesh)'.
- intent: UNDOCUMENTED (shows the vertex group the modal will paint).
- code: apps/blender/panels/weight_paint.py:262 ; _active_group_label:282

### BL-WPAINT-20 · Edit Weights status-bar overlay (ESC=exit / mirror = picker.proscenio_mirror_x)
- status: pending
- review: keep
- observe: Status bar shows BRUSHES_ALL 'Edit Weights:', EVENT_ESC 'exit', MOD_MIRROR 'mirror = picker.proscenio_mirror_x'.
- intent: UNDOCUMENTED (modal status-bar hint chips).
- code: apps/blender/operators/skinning/edit_weights.py:228 _draw_statusbar_edit_weights

### BL-WPAINT-21 · 'bind first to enable' hint label
- status: pending
- review: keep
- observe: INFO-icon label 'bind first to enable' is shown beneath the (disabled) Edit Weights button.
- intent: Bind first - the Edit Weights button is disabled until then.
- code: apps/blender/panels/weight_paint.py:272-273

### BL-WPAINT-22 · 'Brush curve preset:' label
- status: pending
- review: keep
- observe: Label 'Brush curve preset:' shown above the four preset buttons (drawn even when mesh unbound).
- intent: The brush-curve presets shape the brush for common 2D tasks.
- code: apps/blender/panels/weight_paint.py:275

### BL-WPAINT-27 · Viewport display box - 'Weight Opacity' slider
- status: pending
- review: keep
- observe: Drives space overlay.weight_paint_mode_opacity; weight color fades over the mesh. (Opacity 0 not fully invisible - see hint.)
- intent: UNDOCUMENTED (native overlay opacity so the texture shows through while painting).
- code: apps/blender/panels/weight_paint.py:317

### BL-WPAINT-28 · Viewport display box - 'Zero Weights' dropdown
- status: pending
- review: keep
- observe: Drives tool_settings.vertex_group_user; zero-weight verts shaded per the chosen mode.
- intent: UNDOCUMENTED (native Zero Weights display - tool_settings.vertex_group_user).
- code: apps/blender/panels/weight_paint.py:320

### BL-WPAINT-29 · Viewport display hint label ('opacity 0 is not fully invisible (Blender 145603)')
- status: pending
- review: keep
- observe: INFO-icon caveat label about Blender issue 145603 is shown.
- intent: UNDOCUMENTED (upstream-bug caveat).
- code: apps/blender/panels/weight_paint.py:321

### BL-WPAINT-30 · Snapshot subpanel header status badge + '?' help button
- status: pending
- review: keep
- observe: proscenio.help topic 'snapshot' (anchor weight-paint#snapshot).
- intent: UNDOCUMENTED (per-subpanel affordance).
- code: apps/blender/panels/weight_paint.py:121 -> _helpers.py:83-85

### BL-WPAINT-31 · 'Preserve weights on regen' checkbox
- status: pending
- review: keep
- observe: Toggles scene.proscenio.skinning.preserve_on_regen (default ON); consumed by the Automesh-from-Alpha hook on the next regen, not by this panel directly.
- intent: Snapshots weights by UV before an automesh re-run and reprojects them; off = the regen wipes paint.
- code: apps/blender/panels/weight_paint.py:337 ; scene_props.py:287

### BL-WPAINT-32 · 'Show provenance overlay' checkbox
- status: pending
- review: keep
- observe: Toggles scene.proscenio.skinning.show_provenance_overlay. Outside the modal nothing is drawn - no draw handler is added/removed by this toggle (only edit_weights.invoke registers/forces the overlay). See finding.
- intent: UNDOCUMENTED on this surface (doc mentions a provenance overlay only inside the Edit Weights modal).
- code: apps/blender/panels/weight_paint.py:338 ; scene_props.py:299

### BL-WPAINT-33 · Provenance counts pill ('N paint / N seed / N reprojected') or 'no snapshot' hint
- status: pending
- review: keep
- observe: Before bind: INFO 'no snapshot (run Bind first)'. After: 'X paint / Y seed / Z reprojected' counted from sidecar entries by provenance.
- intent: The weight snapshot stores per-vertex weights + provenance; counts recomputed live from the JSON on the mesh.
- code: apps/blender/panels/weight_paint.py:339-349 ; _sidecar_counts:363

### BL-WPAINT-37 · Weight Transfer subpanel header status badge + '?' help button
- status: pending
- review: keep
- observe: proscenio.help topic 'weight_transfer' (anchor weight-paint#weight-transfer).
- intent: UNDOCUMENTED (per-subpanel affordance).
- code: apps/blender/panels/weight_paint.py:144 -> _helpers.py:83-85

### BL-WPAINT-38 · 'Max Distance' field (Weight Transfer)
- status: pending
- review: keep
- observe: Edits scene.proscenio.skinning.weight_transfer_max_distance (default 0.5, min 0); the value seeds the Copy operator on click.
- intent: Target verts beyond the Max Distance get no weights (doc lists it as F3 redo).
- code: apps/blender/panels/weight_paint.py:150 ; scene_props.py:276

### BL-WPAINT-10 · Per-bone 'Soft' toggle button (one per bone)
- status: pending
- review: keep
- pre: Picker with bones; Mode = a planar mode (Proximity/Envelope/Single nearest/Empty).
- steps:
  1. Set Mode=Proximity > click 'Soft' next to a bone
- observe: Writes obj['proscenio_bone_modes'][bone]='SOFT'; button shows depressed (depress=current=='SOFT'); the row's Clear (X) becomes enabled.
- intent: Soft shares weight smoothly with neighbours (cloth, hair).
- code: apps/blender/panels/weight_paint.py:225 -> operators/skinning/set_bone_mode.py:52

### BL-WPAINT-11 · Per-bone 'Hard' toggle button (one per bone)
- status: pending
- review: keep
- pre: Picker with bones; Mode = planar mode.
- steps:
  1. Click 'Hard' next to a bone
- observe: Writes obj['proscenio_bone_modes'][bone]='HARD'; Hard depresses, Soft un-depresses, Clear (X) enabled.
- intent: Hard gives a crisp single-nearest boundary (finger joints).
- code: apps/blender/panels/weight_paint.py:232 -> operators/skinning/set_bone_mode.py:52

### BL-WPAINT-12 · Per-bone Clear (X) button (one per bone)
- status: pending
- review: keep
- pre: Picker with bones; Mode planar; the bone HAS an override (else X is disabled).
- steps:
  1. After setting Soft/Hard on a bone, click the X on that row
- observe: Override removed from obj['proscenio_bone_modes']; Soft+Hard both un-depress; X disables (clear_sub.enabled = current != '').
- intent: UNDOCUMENTED (drops a bone override back to the bind-mode default).
- code: apps/blender/panels/weight_paint.py:241 -> operators/skinning/set_bone_mode.py:56 clear_bone_mode

### BL-WPAINT-13 · Bind to Picker Armature button
- status: pending
- review: keep
- pre: Mesh element active. Row disabled when no picker (row.enabled = picker is not None).
- steps:
  1. With picker set and a mesh selected, click 'Bind to Picker Armature'
- observe: Runs 5 pre-flight diagnoses; on success creates vertex groups + writes proscenio_weight_sidecar; status reports 'bound N mesh(es)' and per-mesh vert/bone/orphan counts. With no picker the button is greyed out.
- intent: Builds the vertex weights that deform the mesh using the selected Mode; writes weights/sidecar exported to the Polygon2D.
- code: apps/blender/panels/weight_paint.py:186 -> operators/skinning/bind_mesh.py:176 execute

### BL-WPAINT-14 · Bind F3/F9 redo panel (bind_init_mode + falloff_power + max_distance)
- status: pending
- review: keep
- pre: Just ran Bind.
- steps:
  1. After Bind, press F9 (or open redo panel) > change Bind mode / Falloff power / Max distance
- observe: Redo panel exposes the enum + falloff_power (0.5-8.0) + max_distance (-1=adaptive); re-running re-binds with the new values. invoke() seeds from scene skinning so panel + F3 agree.
- intent: Proximity/Envelope/Single-nearest/Empty are F3-redo fallbacks; falloff_power & max_distance tune Proximity.
- code: apps/blender/operators/skinning/bind_mesh.py:49-94 (props), 104 invoke

### BL-WPAINT-17 · Edit Weights button (modal entry)
- status: pending
- review: keep
- pre: Mesh active; ENABLED only when picker set AND >=1 vertex group AND sidecar present (_edit_weights_button_enabled).
- steps:
  1. After binding, click 'Edit Weights'
- observe: Enters WEIGHT_PAINT mode, applies 2D paint preset (Front Faces off, mirror from picker), shows provenance overlay (cyan/white/gray), adds status-bar hints. Disabled (greyed) before bind.
- intent: Enters a modal weight-paint session on the active group with a provenance overlay; disabled until Bind.
- code: apps/blender/panels/weight_paint.py:265 -> operators/skinning/edit_weights.py:69 invoke

### BL-WPAINT-18 · Edit Weights modal - LEFTMOUSE paint stroke (per-stroke provenance flip)
- status: pending
- review: keep
- pre: Inside Edit Weights modal.
- steps:
  1. Press+drag LMB to paint a stroke, release
- observe: On press snapshots active VG; on release flip_touched_after_stroke marks changed verts user_paint (white) and triggers area redraw; provenance overlay updates.
- intent: Tags brushed verts as user_paint in the sidecar via per-stroke diff.
- code: apps/blender/operators/skinning/edit_weights.py:114-127 modal

### BL-WPAINT-19 · Edit Weights modal - ESC exit / cancel path
- status: pending
- review: keep
- pre: Inside Edit Weights modal.
- steps:
  1. Press ESC during the modal
- observe: Pushes a single 'Edit Weights' undo, unregisters overlay handler, removes status bar, restores prior session (mode/preset/bone visibility/selection/overlay flag); reports 'Edit Weights modal restored'. Ctrl+Z then reverts the whole session.
- intent: ESC hard-exits and restores brush + bone visibility + mode + selection.
- code: apps/blender/operators/skinning/edit_weights.py:112,133 _finish(cancel=True)

### BL-WPAINT-23 · Brush preset 'Hard Edge' button
- status: pending
- review: keep
- pre: An active weight-paint brush exists (tool_settings.weight_paint.brush) - else operator poll fails.
- steps:
  1. Enter weight paint (or ensure a WP brush exists) > click 'Hard Edge'
- observe: brush.curve_distance_falloff forced to CUSTOM, falloff curve set to [(0,1),(0.95,1),(1,0)]; reports INFO 'Brush preset applied: Hard Edge'. If brush has no falloff curve, WARNING + CANCELLED.
- intent: Hard Edge brush-curve preset for common 2D tasks.
- code: apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88 execute

### BL-WPAINT-24 · Brush preset 'Soft Falloff' button
- status: pending
- review: keep
- pre: Active weight-paint brush exists.
- steps:
  1. Click 'Soft Falloff'
- observe: Curve set to linear [(0,1),(1,0)]; INFO 'Brush preset applied: Soft Falloff'.
- intent: Soft Falloff brush-curve preset.
- code: apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88

### BL-WPAINT-25 · Brush preset 'Crease' button
- status: pending
- review: keep
- pre: Active weight-paint brush exists.
- steps:
  1. Click 'Crease'
- observe: Curve set to [(0,1),(0.2,0.7),(0.5,0),(1,0)]; INFO 'Brush preset applied: Crease'.
- intent: Crease brush-curve preset.
- code: apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88

### BL-WPAINT-26 · Brush preset 'Smooth Blend' button
- status: pending
- review: keep
- pre: Active weight-paint brush exists.
- steps:
  1. Click 'Smooth Blend'
- observe: Curve set to [(0,1),(0.3,0.85),(0.7,0.15),(1,0)]; INFO 'Brush preset applied: Smooth Blend'. Note: in OBJECT mode with no WP brush, poll fails and the button is greyed.
- intent: Smooth Blend brush-curve preset.
- code: apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88

### BL-WPAINT-34 · 'Reset to Last Saved Weights' button
- status: pending
- review: keep
- pre: Mesh active; row disabled when counts is None (no sidecar).
- steps:
  1. After binding/painting, click 'Reset to Last Saved Weights'
- observe: Re-applies the sidecar to live vertex groups; INFO 'restored N verts (M groups)'. If topology hash differs: ERROR 'topology changed since last snapshot...'; if sidecar empty/corrupt: ERROR re-bind hint. Disabled with no snapshot.
- intent: Reverts the live weights to that snapshot; does NOT trigger automesh regen; topology mismatch cancels.
- code: apps/blender/panels/weight_paint.py:352 -> operators/skinning/restore_weight_snapshot.py:49

### BL-WPAINT-35 · 'Export Snapshot' button (file save dialog)
- status: pending
- review: keep
- pre: Mesh active WITH a sidecar (operator poll requires obj.get(sidecar) not None).
- steps:
  1. After bind, click 'Export Snapshot' > choose a .json path > confirm
- observe: File save dialog (.json filter); writes the sidecar JSON payload to disk; INFO 'Sidecar exported to <path>'. On unbound mesh the operator poll fails so click is a no-op.
- intent: Exports the weight snapshot to a JSON file (version-control / move between files).
- code: apps/blender/panels/weight_paint.py:359 -> operators/skinning/sidecar_io.py:50,66

### BL-WPAINT-36 · 'Import Snapshot' button (file open dialog)
- status: pending
- review: keep
- pre: Mesh element active (import poll only needs a mesh).
- steps:
  1. Click 'Import Snapshot' > pick a .json > confirm
- observe: Reads file, validates JSON, stores onto obj[proscenio_weight_sidecar]; if topology matches: applies to live weights + INFO 'imported and applied to N verts'; else INFO 'imported (stored only - topology differs...)'. Bad file/JSON: WARNING + CANCELLED.
- intent: Imports a snapshot; loads it onto the mesh and applies to live weights when topology matches; run Reset to push otherwise.
- code: apps/blender/panels/weight_paint.py:360 -> operators/skinning/sidecar_io.py:84,101

### BL-WPAINT-39 · Copy weights button ('Copy Weights to Selected', DUPLICATE icon)
- status: pending
- review: keep
- pre: Active mesh + >=1 OTHER selected mesh (operator poll); seeds max_distance from the panel field.
- steps:
  1. Select target meshes then the source mesh (active) > click the copy button
- observe: Transfers per-vert weights to each target by nearest source vert within Max Distance, creating vertex groups as needed; reports INFO/WARNING coverage summary. F9 redo exposes max_distance. Note: the panel button has no text label - only the DUPLICATE icon.
- intent: Copies weights from the active mesh to every other selected mesh by nearest world-space vertex.
- code: apps/blender/panels/weight_paint.py:151 -> operators/skinning/copy_weights_to_selected.py:41

### BL-WPAINT-40 · Copy weights F9 redo (max_distance)
- status: pending
- review: keep
- pre: Just ran Copy Weights.
- steps:
  1. After copy, press F9 > change Max Distance
- observe: Redo panel exposes Max Distance (default 0.5, min 0, soft_max 5.0); re-runs the transfer with the new radius.
- intent: Max Distance is an F3/F9 redo for a one-off tweak.
- code: apps/blender/operators/skinning/copy_weights_to_selected.py:25 max_distance prop

## Animation panel (read-only action summary)

### BL-ANIM-01 · Animation subpanel foldout (header)
- status: pending
- review: keep
- observe: Panel expands; shows either the empty-state label or the action UIList + count label. Starts collapsed on a fresh session (bl_options DEFAULT_CLOSED).
- intent: Read-only summary of every Action in the file that the writer emits as Godot AnimationPlayer entries.
- code: apps/blender/panels/animation.py:39-67

### BL-ANIM-02 · Status badge icon (header, right side)
- status: pending
- review: keep
- observe: Hover shows the godot-ready band tooltip; the icon is the custom Godot preview (falls back to built-in badge icon if preview load failed/headless). Click opens the status-legend help popup (proscenio.status_info -> proscenio.help topic 'status_legend').
- intent: UNDOCUMENTED (doc page does not describe the header status badge); feature_status maps 'animation' -> GODOT_READY so it should show the Godot mark and the godot-ready tooltip.
- code: apps/blender/panels/_helpers.py:46-69 (draw via animation.py:50-51)

### BL-ANIM-04 · 'no actions to export' empty-state label
- status: pending
- review: keep
- observe: Single row 'no actions to export' with INFO icon; the UIList and count label are NOT drawn (early return).
- intent: UNDOCUMENTED as a specific label; conveys the read-only summary is empty when no Actions exist.
- code: apps/blender/panels/animation.py:56-58

### BL-ANIM-05 · Actions UIList (PROSCENIO_UL_actions / template_list)
- status: pending
- review: keep
- observe: One row per action; visible row count = min(max(len,2),6) (min 2 rows shown even with 1 action, capped at 6). Clicking the row body sets active_action_index; the standard template_list selection highlight follows.
- intent: Lists every bpy.data.actions entry the writer would emit; selection is tracked in scene.proscenio.active_action_index.
- code: apps/blender/panels/animation.py:59-67 (template_list), 12-36 (UIList)

### BL-ANIM-10 · Per-row frame-range label '[start-end]'
- status: pending
- review: keep
- observe: Shows '[<start>-<end>]' with both ends rounded to whole frames (%.0f). For an empty/never-keyed action Blender reports frame_range (0,0) -> '[0-0]' (verify it does not raise).
- intent: UNDOCUMENTED; read-only display of the action's frame_range as integer-rounded start-end.
- code: apps/blender/panels/animation.py:27,36

### BL-ANIM-11 · 'N action(s) total' count label
- status: pending
- review: keep
- observe: Label 'N action(s) total' with INFO icon where N == len(bpy.data.actions), including orphan/zero-user actions (it counts ALL datablocks, not just exportable ones).
- intent: UNDOCUMENTED; read-only count of bpy.data.actions.
- code: apps/blender/panels/animation.py:68

### BL-ANIM-03 · Help '?' button (header)
- status: pending
- review: keep
- pre: Animation subpanel header visible.
- steps:
  1. Click the '?' (QUESTION icon) in the Animation header.
- observe: A 480px-wide popup opens titled 'Animation' with summary 'List of actions the writer would emit as Godot AnimationLibrary entries.' plus sections and any See-also/doc-url buttons (help_topics.py:184-198). Topic id 'animation' resolves (not 'unknown help topic').
- intent: UNDOCUMENTED (doc page never mentions a help button); opens the in-panel help popup for topic 'animation'.
- code: apps/blender/panels/_helpers.py:84-85 (op), apps/blender/operators/help_dispatch.py:50-97 (handler)

### BL-ANIM-06 · Action name row button (per-row, emboss=False)
- status: pending
- review: keep
- pre: At least one Action and at least one ARMATURE object in the scene.
- steps:
  1. Expand Animation subpanel > click an action's name text (the ACTION-icon label, drawn emboss=False so it looks like a plain label).
- observe: The clicked action is assigned to armatures[0].animation_data.action (animation_data_create() called if missing); active_action_index syncs to that row; scrubbing the timeline now plays the action. Undoable (REGISTER|UNDO).
- intent: UNDOCUMENTED (doc says panel is read-only; the row is in fact a click-to-assign operator). Assigns the row's action to the first scene armature so the timeline plays it.
- code: apps/blender/panels/animation.py:28-36 (draw), apps/blender/operators/selection.py:96-132 (handler)

### BL-ANIM-07 · Action row button - multiple-armature path
- status: pending
- review: keep
- pre: At least one Action and >=2 ARMATURE objects in the scene; report log level at 'info' or higher.
- steps:
  1. Create 2+ armatures > click an action row in the Animation panel.
- observe: A WARNING report appears: 'Proscenio: N armatures in scene - assigning to <name>'; the action is assigned to armatures[0] only. (Suppressed silently if log level = 'errors' - see findings.)
- intent: UNDOCUMENTED; when >1 armature exists it warns and assigns to the first armature only ('mirror the writer's heuristic').
- code: apps/blender/operators/selection.py:117-127

### BL-ANIM-08 · Action row button - no-armature failure path
- status: pending
- review: keep
- pre: At least one Action but ZERO armature objects in the scene; report log level 'info'+.
- steps:
  1. Delete all armatures > click an action row.
- observe: Operator returns CANCELLED; WARNING 'Proscenio: no armature in scene to receive the action'; no datablock changes. (Silent if log level = 'errors'.)
- intent: UNDOCUMENTED; cancels with a warning when no armature exists to receive the action.
- code: apps/blender/operators/selection.py:117-120

### BL-ANIM-09 · Action row button - stale/renamed action path
- status: pending
- review: keep
- pre: An action exists; another user/script could rename or delete it between draw and click.
- steps:
  1. Difficult to trigger manually - rename/delete the action via Python console after the panel drew but before clicking, then click the (now stale) row.
- observe: Operator returns CANCELLED; WARNING 'Proscenio: action '<name>' not found'; no assignment.
- intent: UNDOCUMENTED; cancels with a warning when the action_name no longer resolves in bpy.data.actions.
- code: apps/blender/operators/selection.py:113-116

## Atlas panel: pack / unpack / apply

### BL-ATLAS-01 · Atlas subpanel foldout header
- status: pending
- review: keep
- observe: Subpanel expands showing atlas readout label(s), pixels-per-unit readout, and the 'Atlas packer' box. bl_order=8 places it 8th.
- intent: Collapsible subpanel that surfaces atlas state + packer controls.
- code: apps/blender/panels/atlas.py:16

### BL-ATLAS-02 · Status badge icon (header_preset)
- status: pending
- review: keep
- observe: Hover shows band tooltip (atlas feature = GODOT_READY band); click opens the status-legend help dialog via proscenio.status_info -> proscenio.help topic='status_legend'.
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:28 -> _helpers.py:46 _draw_status_button

### BL-ATLAS-03 · Help '?' button (QUESTION icon)
- status: pending
- review: keep
- observe: proscenio.help popup opens titled 'Atlas' with sections Pack Atlas / Apply Packed Atlas / Unpack Atlas and a docs link.
- intent: Opens the in-panel Atlas help dialog (topic 'atlas').
- code: apps/blender/panels/atlas.py:28 -> _helpers.py:84 draw_subpanel_header

### BL-ATLAS-04 · Atlas readout label: 'no atlas linked in materials'
- status: pending
- review: keep
- observe: Label reads 'no atlas linked in materials' with INFO icon.
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:33-34

### BL-ATLAS-05 · Atlas readout label: 'packed atlas: <name>'
- status: pending
- review: keep
- observe: Label reads 'packed atlas: <stem>.atlas.png' with IMAGE icon (is_packed_atlas branch).
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:35-36

### BL-ATLAS-06 · Atlas readout label: 'source image: <name>' / '<name> (unsaved)'
- status: pending
- review: keep
- observe: Label reads 'source image: <basename>' with IMAGE_DATA icon; if the image has no filepath it reads '<image.name> (unsaved)'.
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:37-38, 99

### BL-ATLAS-07 · Pixels-per-unit readout label
- status: pending
- review: keep
- observe: Read-only label echoes scene_props.pixels_per_unit formatted with %g; editable field lives in the Export subpanel, not here.
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:39-42

### BL-ATLAS-08 · 'Atlas packer' box header label
- status: pending
- review: keep
- observe: A bordered box labeled 'Atlas packer' contains the three config fields, separator, and Pack/Apply/Unpack buttons.
- intent: UNDOCUMENTED (box grouping label)
- code: apps/blender/panels/atlas.py:51-52

### BL-ATLAS-09 · Pack padding (pack_padding_px) field
- status: pending
- review: keep
- observe: Value clamps to 0..64; consumed by Pack Atlas as int padding around each sprite slot in the composed PNG + manifest.
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:54 (prop) -> properties/scene_props.py:447

### BL-ATLAS-10 · Pack max size (pack_max_size) field
- status: pending
- review: keep
- observe: Value clamps to 64..8192; Pack fails with 'pack failed - N sprite(s) do not fit in NxN px atlas.' when sprites exceed this cap.
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:55 (prop) -> properties/scene_props.py:454

### BL-ATLAS-11 · Power-of-two atlas (pack_pot) checkbox
- status: pending
- review: keep
- observe: When on, the resulting atlas_w/atlas_h are rounded up to the next power of two; off by default.
- intent: UNDOCUMENTED
- code: apps/blender/panels/atlas.py:56 (prop) -> properties/scene_props.py:461

### BL-ATLAS-16 · 'run Pack Atlas first' disabled hint row
- status: pending
- review: keep
- observe: Where Apply would be, a disabled (greyed) row reads 'run Pack Atlas first' with INFO icon; no Apply button drawn.
- intent: UNDOCUMENTED (gates Apply until a manifest exists).
- code: apps/blender/panels/atlas.py:61-64

### BL-ATLAS-12 · Pack Atlas button
- status: pending
- review: keep
- pre: Blend saved to disk (bpy.data.filepath set); Object Mode; at least one MESH with a source image and not exclude_from_atlas
- steps:
  1. Save .blend > Object Mode > select/have sprite meshes with source images > click 'Pack Atlas'.
- observe: Writes <stem>.atlas.png + <stem>.atlas.json next to the .blend; INFO report 'packed N sprite(s) into WxH px atlas -> file.png'; UVs and materials unchanged. Apply button then appears.
- intent: Walks every sprite with a texture, runs MaxRects packing, writes <blend>.atlas.png + .atlas.json; non-destructive (UVs/materials untouched).
- code: apps/blender/panels/atlas.py:58 -> operators/atlas_pack/pack.py:36

### BL-ATLAS-13 · Pack Atlas - disabled in Edit Mode / unsaved (poll)
- status: pending
- review: keep
- pre: Unsaved file OR Edit Mode
- steps:
  1. On a never-saved file, or in Edit Mode, hover/observe the 'Pack Atlas' button.
- observe: Button greyed out (poll returns False when bpy.data.filepath empty or context.mode != 'OBJECT').
- intent: Pack requires Object Mode (Edit Mode hides UV data behind BMesh) and a saved blend.
- code: apps/blender/operators/atlas_pack/pack.py:48-51

### BL-ATLAS-14 · Pack Atlas - no eligible sprites path
- status: pending
- review: keep
- pre: Saved file, Object Mode, but no MESH has a source image (or all are exclude_from_atlas)
- steps:
  1. Remove/ exclude all textured meshes > click 'Pack Atlas'.
- observe: WARN report 'no sprite meshes with source images found'; operation CANCELLED; no PNG/JSON written.
- intent: Pack walks sprites with a texture; warns when none found.
- code: apps/blender/operators/atlas_pack/pack.py:68-72

### BL-ATLAS-15 · Pack Atlas - pack-failed (overflow) path
- status: pending
- review: keep
- pre: Saved, Object Mode; total sprite area exceeds pack_max_size^2
- steps:
  1. Set 'Pack max size' very low (e.g. 64) with large sprites > click 'Pack Atlas'.
- observe: ERROR report 'pack failed - N sprite(s) do not fit in NxN px atlas.'; CANCELLED; nothing written.
- intent: Pack fails when sprites cannot fit the max-size atlas.
- code: apps/blender/operators/atlas_pack/pack.py:82-88

### BL-ATLAS-17 · Apply Packed Atlas button
- status: pending
- review: keep
- pre: Saved blend; <blend>.atlas.json exists (Pack Atlas ran); Object Mode
- steps:
  1. After Pack Atlas, click 'Apply Packed Atlas' (FILE_REFRESH icon).
- observe: Per matching mesh: pre_pack CP + '<uv>.pre_pack' UV layer created, UVs remapped into the packed slot, material relinked to 'Proscenio.PackedAtlas' (or image swapped if material_isolated). INFO 'applied packed atlas to N sprite(s)...'. Unpack button now appears.
- intent: Snapshots pre-apply state, then rewrites every sprite's UVs and material to address the packed atlas.
- code: apps/blender/panels/atlas.py:60 -> operators/atlas_pack/apply.py:31

### BL-ATLAS-18 · Apply Packed Atlas - disabled in Edit Mode / no manifest (poll)
- status: pending
- review: keep
- pre: Edit Mode, OR manifest missing, OR unsaved
- steps:
  1. Delete the .atlas.json or enter Edit Mode > observe the Apply button.
- observe: Button absent (panel hides it when manifest missing) or greyed (poll False in Edit Mode / unsaved).
- intent: Apply requires Object Mode and an existing manifest.
- code: apps/blender/operators/atlas_pack/apply.py:44-52

### BL-ATLAS-19 · Apply Packed Atlas - manifest-not-found runtime path
- status: pending
- review: keep
- pre: Manifest existed at poll time but deleted before execute (race)
- steps:
  1. Click Apply after externally deleting the .atlas.json between draw and click.
- observe: ERROR report 'manifest not found - <stem>.atlas.json'; CANCELLED.
- intent: Apply reads <blend>.atlas.json; errors if absent.
- code: apps/blender/operators/atlas_pack/apply.py:59-62

### BL-ATLAS-20 · Apply Packed Atlas - shared 'Proscenio.PackedAtlas' material creation
- status: pending
- review: keep
- pre: Apply run; at least one mesh with material_isolated == False
- steps:
  1. Apply > inspect the material on a non-isolated sprite + the Material datablocks.
- observe: A material named 'Proscenio.PackedAtlas' exists (rebuilt: nodes cleared, Principled+TexImage(atlas)+Output linked), and non-isolated sprites' slot 0 points to it.
- intent: Links each non-isolated sprite to the shared 'Proscenio.PackedAtlas' material.
- code: apps/blender/operators/atlas_pack/apply.py:70,188-204,247-250

### BL-ATLAS-21 · Apply Packed Atlas - isolated-material path
- status: pending
- review: keep
- pre: A sprite mesh has material_isolated == True; Apply prerequisites met
- steps:
  1. Enable 'Isolated material' on a sprite (Object panel) > Pack > Apply.
- observe: That sprite keeps its own material; every TEX_IMAGE node's image is swapped to the packed atlas image instead of relinking to the shared material.
- intent: Set 'Isolated material' on a sprite to keep its own shader while drawing from the packed atlas.
- code: apps/blender/operators/atlas_pack/apply.py:243-245 -> _paths.py:61 swap_image_in_materials

### BL-ATLAS-22 · Apply Packed Atlas - sprite region rewrite (element_type=='sprite')
- status: pending
- review: keep
- pre: Object with proscenio.element_type == 'sprite' in the manifest; Apply run
- steps:
  1. Apply with a sprite-type object > inspect its proscenio.region_mode / region_x/y/w/h.
- observe: region_mode set to 'manual'; region_x/y/w/h set to slot.x/y/w/h divided by atlas_w/atlas_h (normalized slot rectangle).
- intent: A packed Sprite Frame still slices correctly; region addresses the packed slot.
- code: apps/blender/operators/atlas_pack/apply.py:168-186

### BL-ATLAS-23 · Apply Packed Atlas - re-Apply / stale-snapshot drift guard
- status: pending
- review: keep
- pre: Sprite already has a pre_pack snapshot from a prior Apply
- steps:
  1. Apply > Apply again (re-pack) > if the pre_pack UV layer was renamed/length-mismatched, observe report.
- observe: Healthy snapshot: active UVs restored from pre_pack then re-remapped (no drift). Broken snapshot: WARN 'pre-pack UV snapshot missing or out of sync...skipping Apply'; sprite skipped; summary shows '; skipped N (stale pre-pack snapshot)'.
- intent: Re-applying restores original source-image UVs from the pre_pack layer first to avoid cumulative slot shrink.
- code: apps/blender/operators/atlas_pack/apply.py:79-81,97-155

### BL-ATLAS-24 · Apply Packed Atlas - no-UV-layer skip
- status: pending
- review: keep
- pre: A mesh in the manifest has no active UV layer (element_type=='mesh')
- steps:
  1. Apply with a UV-less non-sprite mesh present in the manifest.
- observe: That mesh skipped; report suffix '; skipped N (no UV layer)'. (Note: for element_type=='sprite' it is NOT skipped - see finding.)
- intent: Sprites without UV data are skipped during rewrite.
- code: apps/blender/operators/atlas_pack/apply.py:82-84,206-216

### BL-ATLAS-25 · Apply Packed Atlas - Ctrl+Z undo
- status: pending
- review: keep
- pre: Apply just run
- steps:
  1. Apply > press Ctrl+Z.
- observe: REGISTER|UNDO pushes one undo step; Ctrl+Z reverts datablock changes (UVs, material assignment, region props). On-disk PNG/JSON remain. Confirm pre_pack CP/UV-layer state after undo (see suspected-bug finding).
- intent: Apply is undoable; Ctrl+Z reverts (per operator description); doc says Ctrl+Z does NOT revert Unpack snapshot semantics.
- code: apps/blender/operators/atlas_pack/apply.py:42

### BL-ATLAS-26 · Unpack Atlas button
- status: pending
- review: keep
- pre: At least one mesh carries a pre_pack snapshot (Apply was run); Object Mode
- steps:
  1. After Apply, click 'Unpack Atlas' (LOOP_BACK icon).
- observe: Each snapshotted mesh: pre_pack UVs restored into the original layer, the '.pre_pack' layer removed, original material + image + region_mode restored, pre_pack CP deleted. INFO 'unpacked N sprite(s) - restored pre-Apply state'. Button disappears.
- intent: Reverts a previous apply from the snapshot (survives save/reload; Ctrl+Z does not).
- code: apps/blender/panels/atlas.py:66 -> operators/atlas_pack/unpack.py:36

### BL-ATLAS-27 · Unpack Atlas - hidden when no snapshot
- status: pending
- review: keep
- pre: No mesh has a pre_pack snapshot
- steps:
  1. On a packed-but-not-applied (or freshly unpacked) file, expand Atlas subpanel.
- observe: No 'Unpack Atlas' button drawn (scene_has_pre_pack_snapshot False); poll would also block it in Edit Mode.
- intent: Unpack only available after an Apply created a snapshot.
- code: apps/blender/panels/atlas.py:65 + operators/atlas_pack/unpack.py:49-52

### BL-ATLAS-28 · Unpack Atlas - material-missing partial restore
- status: pending
- review: keep
- pre: Apply ran; then the original material datablock deleted/renamed before Unpack
- steps:
  1. Apply > delete the original material > Unpack.
- observe: WARN per object 'original material ... not found (deleted?); restored UVs only'; summary 'unpacked N; M with materials missing (UVs only): names'. Rename case is rescued via the origin marker.
- intent: Restores original material; if the original was deleted, restore UVs only.
- code: apps/blender/operators/atlas_pack/unpack.py:107-124,68-72

### BL-ATLAS-29 · Unpack Atlas - rename rescue via origin marker
- status: pending
- review: keep
- pre: Apply ran (stamps PROSCENIO_ATLAS_ORIGIN_MARKER); original material renamed
- steps:
  1. Apply > rename the original material > Unpack.
- observe: By-name lookup misses, marker scan finds the renamed material, slot 0 restored to it; counted as a successful (non-partial) restore.
- intent: A rename between Apply and Unpack still restores via the stamped origin marker.
- code: apps/blender/operators/atlas_pack/unpack.py:21-33,113-117

### BL-ATLAS-30 · Unpack Atlas - region restore
- status: pending
- review: keep
- pre: Apply ran on a sprite-type object (region was changed to manual)
- steps:
  1. Apply a sprite > Unpack > inspect proscenio.region_mode / region_x..h.
- observe: region_mode and region_x/y/w/h restored to the pre-Apply snapshot values (suppresses TypeError/ValueError on assignment).
- intent: Restores original region_mode (and region x/y/w/h).
- code: apps/blender/operators/atlas_pack/unpack.py:136-145

### BL-ATLAS-31 · Unpack Atlas - Ctrl+Z undo / survives reload
- status: pending
- review: keep
- pre: Apply ran, file saved
- steps:
  1. Apply > save > reopen .blend > Unpack works; separately, Unpack > Ctrl+Z.
- observe: Snapshot (CP + .pre_pack layer) persists across save/reload so Unpack still functions after reopen. Unpack itself is REGISTER|UNDO so Ctrl+Z reverts the unpack operation.
- intent: The snapshot survives save/reload; Ctrl+Z does not revert the original Apply.
- code: apps/blender/operators/atlas_pack/unpack.py:47

## Validation panel (export-blocking issues list)

### BL-VALID-01 · Status badge (header, godot-ready icon)
- status: pending
- review: keep
- observe: Hover shows the godot-ready band tooltip (from STATUS_BADGES); click opens the 'status_legend' help popup (480px) listing the status bands
- intent: UNDOCUMENTED
- code: apps/blender/panels/validation.py:21 -> _helpers.py:83 (_draw_status_button) -> help_dispatch.py:17 (PROSCENIO_OT_status_info)

### BL-VALID-04 · 'proscenio scene props not registered' error label
- status: pending
- review: keep
- observe: Panel shows only the label 'proscenio scene props not registered' with an ERROR icon; no Validate button, no rows
- intent: UNDOCUMENTED (registration-guard fallback)
- code: apps/blender/panels/validation.py:25-28

### BL-VALID-05 · 'run Validate to see issues' info label
- status: pending
- review: keep
- observe: Below the Validate button shows label 'run Validate to see issues' with an INFO icon
- intent: UNDOCUMENTED (empty-state prompt before first Validate run)
- code: apps/blender/panels/validation.py:33-35

### BL-VALID-06 · 'no issues - ready to export' label
- status: pending
- review: keep
- observe: Label 'no issues - ready to export' with a CHECKMARK icon; no issue rows
- intent: UNDOCUMENTED (clean-scene success state; doc only says errors block / warnings inform)
- code: apps/blender/panels/validation.py:38-40

### BL-VALID-08 · Issue row (plain label, scene-wide) - 'message'
- status: pending
- review: keep
- observe: A non-clickable label appears with the message; error severity shows ERROR icon + red alert tint, warning shows INFO icon; clicking it does nothing
- intent: Errors block the export; warnings are informational (no object means a plain, non-clickable label).
- code: apps/blender/panels/validation.py:43 -> _helpers.py:149-150 (draw_issue_row else branch)

### BL-VALID-02 · Help '?' button (header)
- status: pending
- review: keep
- pre: Validation subpanel expanded
- steps:
  1. Click the '?' icon at the right of the Validation header
- observe: A 480px popup opens titled with the 'validation' help topic; shows summary + sections; ESC/click-away closes it
- intent: UNDOCUMENTED (the '?' itself is undocumented; it opens the Validation help topic which mirrors this doc page)
- code: apps/blender/panels/validation.py:21 -> _helpers.py:84 (draw_subpanel_header) -> help_dispatch.py:50 (PROSCENIO_OT_help)

### BL-VALID-03 · Validate button
- status: pending
- review: keep
- pre: scene.proscenio registered (else the panel short-circuits to an error label and never draws the button)
- steps:
  1. Click 'Validate' with a populated scene
- observe: validation_results is repopulated and validation_ran set True; info-bar reports 'N error(s), M warning(s)' (red) / 'M warning(s)' (yellow) / 'validation OK'; issue rows render below the separator; debug log echoes each issue
- intent: Walks the scene and reports issues that would block an export (missing armature when sprites carry vertex groups, dead bone references, missing atlas files, sprite_frame meshes without hframes/vframes).
- code: apps/blender/panels/validation.py:30 -> export_flow.py:121 (PROSCENIO_OT_validate_export.execute:132)

### BL-VALID-07 · Issue row (clickable, object-scoped) - '[obj] message'
- status: pending
- review: keep
- pre: validation_ran True; at least one issue with obj_name set (e.g. an element with vertex groups that don't resolve to bones, or a missing-atlas object)
- steps:
  1. Run Validate to surface object-scoped issues > click a row showing '[Name] message'
- observe: That object becomes the sole selection and active object (deselects all others first); error rows render with ERROR icon + red alert tint, warnings with INFO icon; if the object name no longer exists a 'object \'<name>\' not found' warning is reported and selection is unchanged
- intent: Click a row to select the offending object.
- code: apps/blender/panels/validation.py:43 -> _helpers.py:142 (draw_issue_row) -> selection.py:18 (PROSCENIO_OT_select_issue_object.execute:31)

## Pipeline panel: import Photoshop manifest + export/re-export .proscenio

### BL-PIPE-01 · Pipeline panel (parent grouper) - missing-props error label
- status: pending
- review: keep
- observe: Panel renders with Import + Export subpanels nested under it. With scene props registered, body is empty (no error). Only if scene.proscenio is unregistered does the row 'proscenio scene props not registered' (ERROR icon) appear.
- intent: Pipeline groups Import + Export; doc describes the panel as the import/export ends of the stage.
- code: apps/blender/panels/pipeline.py:38-40

### BL-PIPE-02 · Pipeline header status badge (feature_id 'pipeline')
- status: pending
- review: keep
- observe: Hover shows the GODOT_READY band tooltip (pipeline maps to GODOT_READY). Click opens the 'status_legend' help popup. Badge uses the custom Godot mark icon (falls back to built-in icon if preview load failed/headless).
- intent: UNDOCUMENTED (header status badge convention not in the pipeline doc).
- code: apps/blender/panels/pipeline.py:35-36 -> apps/blender/panels/_helpers.py:46-69

### BL-PIPE-03 · Pipeline header help button '?' (topic 'pipeline_overview')
- status: pending
- review: keep
- observe: A 480px-wide popup opens titled from the 'pipeline_overview' HelpTopic with summary + sections; an 'Open online docs' button (resolves to pipeline doc anchor) is present.
- intent: UNDOCUMENTED (the in-panel '?' help affordance is not described in the doc).
- code: apps/blender/panels/pipeline.py:36 -> apps/blender/panels/_helpers.py:84-85 -> apps/blender/operators/help_dispatch.py:50-97

### BL-PIPE-04 · Import header status badge (feature_id 'import')
- status: pending
- review: keep
- observe: Hover shows BLENDER_ONLY band tooltip (import maps to BLENDER_ONLY); badge uses the custom Blender mark icon. Click opens the status_legend popup.
- intent: UNDOCUMENTED (subpanel status badge not in doc).
- code: apps/blender/panels/pipeline.py:54-55 -> apps/blender/panels/_helpers.py:46-69

### BL-PIPE-05 · Import header help button '?' (topic 'import_photoshop')
- status: pending
- review: keep
- observe: Popup opens with the 'import_photoshop' HelpTopic content (title/summary/sections) and an Open online docs button to pipeline#import.
- intent: UNDOCUMENTED (in-panel help button not described).
- code: apps/blender/panels/pipeline.py:55 -> apps/blender/panels/_helpers.py:84-85 -> apps/blender/operators/help_dispatch.py:50-97

### BL-PIPE-07 · Import file dialog: Placement (enum: Landed / Centered)
- status: pending
- review: keep
- observe: Landed shifts every stamped mesh up so the figure's lowest point sits on world Z=0; Centered keeps the figure centred on the manifest canvas centre at world origin. Default is 'landed'.
- intent: UNDOCUMENTED (placement enum exists in the importer redo/dialog sidebar but the doc never mentions Landed vs Centered).
- code: apps/blender/operators/import_photoshop.py:40-60 -> apps/blender/importers/photoshop/__init__.py:89-90 (_anchor_meshes_at_feet)

### BL-PIPE-08 · Import file dialog: Root Bone Name (text field)
- status: pending
- review: keep
- observe: The single bone created in the stub armature is named with the entered value (default 'root'); empty input falls back to 'root' (import_photoshop.py:81).
- intent: UNDOCUMENTED (the doc says everything parents to a 'stub root armature' but never exposes the bone-name override).
- code: apps/blender/operators/import_photoshop.py:62-70 -> apps/blender/importers/photoshop/__init__.py:70-73

### BL-PIPE-09 · Export header status badge (feature_id 'export')
- status: pending
- review: keep
- observe: Hover shows GODOT_READY band tooltip (export maps to GODOT_READY); badge uses the custom Godot mark icon. Click opens the status_legend popup.
- intent: UNDOCUMENTED (subpanel status badge not in doc).
- code: apps/blender/panels/pipeline.py:80-81 -> apps/blender/panels/_helpers.py:46-69

### BL-PIPE-10 · Export header help button '?' (topic 'export')
- status: pending
- review: keep
- observe: Popup opens with the 'export' HelpTopic content and an Open online docs button to pipeline#export.
- intent: UNDOCUMENTED (in-panel help button not described).
- code: apps/blender/panels/pipeline.py:81 -> apps/blender/panels/_helpers.py:84-85 -> apps/blender/operators/help_dispatch.py:50-97

### BL-PIPE-11 · Last export path (FILE_PATH field)
- status: pending
- review: keep
- observe: Field holds the sticky destination; once non-empty the 'Re-export' button appears below; value persists across save/reload of the .blend. Editing it manually changes where Re-export writes (re-export uses bpy.path.abspath of this value).
- intent: The path is sticky so Re-export skips the file dialog; saved with the .blend so the document carries its export target.
- code: apps/blender/panels/pipeline.py:88 -> apps/blender/properties/scene_props.py:403-411

### BL-PIPE-12 · Pixels per unit (number field, scene prop)
- status: pending
- review: keep
- observe: Scene-level pixels_per_unit updates (min 0.0001). Re-export uses this value as the conversion ratio. NOTE: the first 'Export (.proscenio)' run does NOT use this field (see finding) - it uses the operator's own ppu property defaulting to 100. Also auto-synced to the manifest PPU on import.
- intent: Sets the Blender-world-to-Godot-pixel ratio (default 100).
- code: apps/blender/panels/pipeline.py:89 -> apps/blender/properties/scene_props.py:412-417

### BL-PIPE-13 · Bundle textures (checkbox)
- status: pending
- review: keep
- observe: On write, every referenced texture is copied next to the .proscenio; success report gets a '; bundled N texture(s)' suffix (and 'K missing on disk' when applicable); console prints '[Proscenio] bundle -> copied .., skipped .., missing ..'. When off, no copying and no suffix.
- intent: UNDOCUMENTED (the pipeline doc never mentions a texture-bundling toggle).
- code: apps/blender/panels/pipeline.py:90 -> apps/blender/properties/scene_props.py:418-426 -> apps/blender/operators/export_flow.py:97-118

### BL-PIPE-15 · Export file dialog: Pixels per unit (operator FloatProperty)
- status: pending
- review: keep
- observe: Writer uses THIS operator value (default 100, min 0.0001), independent of the panel/scene Pixels-per-unit field. This is the only ppu the first Export honors.
- intent: Sets the Blender-world-to-Godot-pixel ratio (default 100) per the doc's Pixels-per-unit description.
- code: apps/blender/operators/export_flow.py:158-163,167

### BL-PIPE-06 · Import Photoshop Manifest (button)
- status: pending
- review: keep
- pre: A valid PSD manifest .json on disk (from the Photoshop plugin).
- steps:
  1. Pipeline > Import > click 'Import Photoshop Manifest' > pick a manifest .json in the file dialog > Import.
- observe: File dialog filters to *.json. On import, the info bar reports 'stamped N mesh(es) (armature: <name>)' plus 'skipped K' / 'composed M spritesheet(s)' when applicable; meshes appear parented to a stub armature; scene.proscenio.pixels_per_unit is synced to the manifest's PPU; operation is undoable (Ctrl+Z).
- intent: Reads a manifest from the Photoshop plugin, stamps one mesh per layer (composing spritesheets for sprite_frame groups), parents everything to a stub root armature; re-importing reuses meshes so rotation/parenting/weights survive.
- code: apps/blender/panels/pipeline.py:58-62 -> apps/blender/operators/import_photoshop.py:26-103 -> apps/blender/importers/photoshop/__init__.py:42-91

### BL-PIPE-14 · Export (.proscenio) (button)
- status: pending
- review: keep
- pre: A scene with exportable content (armature + sprites).
- steps:
  1. Pipeline > Export > click 'Export (.proscenio)' > choose destination in the file dialog > Export.
- observe: File dialog filters to *.proscenio. Validation runs first; if any error-severity issues exist the export is blocked with 'export blocked by N validation error(s) - see Validation panel.' and nothing is written. On success: JSON written, info bar 'wrote <name>' (+bundle suffix), console '[Proscenio] exported -> <path>', and last_export_path is set to the chosen path (making Re-export appear).
- intent: Runs the writer, validates against the schema, writes the JSON next to the .blend; the path is sticky.
- code: apps/blender/panels/pipeline.py:93 -> apps/blender/operators/export_flow.py:147-178

### BL-PIPE-16 · Re-export (button)
- status: pending
- review: keep
- pre: last_export_path is non-empty (a prior Export ran or the path was typed in).
- steps:
  1. Pipeline > Export > click 'Re-export'.
- observe: No file dialog. Validation gate runs; blocking errors abort with 're-export failed' path. On success the writer writes to abspath(last_export_path) using the SCENE pixels_per_unit, info bar 're-exported -> <name>' (+bundle suffix), console '[Proscenio] re-exported -> <path>'. Button is hidden when last_export_path is empty (and operator poll also returns False).
- intent: Re-export skips the file dialog (uses the sticky path).
- code: apps/blender/panels/pipeline.py:94-95 -> apps/blender/operators/export_flow.py:181-206

## Helpers panel (viewport authoring aids outside export)

### BL-HELP-01 · Helpers subpanel foldout (header)
- status: pending
- review: keep
- observe: Subpanel starts collapsed (bl_options DEFAULT_CLOSED); clicking expands it to reveal the Preview Camera button. Header reads 'Helpers'.
- intent: Collapsible 'Helpers' subpanel hosting viewport authoring aids that never touch the .proscenio.
- code: apps/blender/panels/helpers.py:16-35

### BL-HELP-02 · Status badge icon (header, blender-only band)
- status: pending
- review: keep
- observe: Icon is the custom Blender-only mark (feature 'helpers' = BLENDER_ONLY); falls back to TOOL_SETTINGS built-in if the preview PNG failed to load. Hover shows the blender-only band tooltip ('Authoring shortcut. Lives entirely on the Blender side...'); click opens the Status badges legend popup.
- intent: UNDOCUMENTED (the doc page never mentions the status badge; the help_topics 'status_legend' topic explains it).
- code: apps/blender/panels/_helpers.py:46-69 (drawn via draw_subpanel_header at helpers.py:28)

### BL-HELP-03 · Status badge click -> Status legend popup (proscenio.status_info)
- status: pending
- review: keep
- pre: Helpers header status badge visible.
- steps:
  1. Click the status badge icon on the Helpers header.
- observe: A 480px-wide popup titled 'Status badges' opens listing the four bands (godot-ready / blender-only / planned / out-of-scope) and the per-feature legend, with an 'Open online docs' button (doc_url -> .../helpers? no, status_legend anchor '#status-badges').
- intent: UNDOCUMENTED in the doc page; surfaces the 'Status badges' legend (status_legend help topic).
- code: apps/blender/operators/help_dispatch.py:42-44 (invoke calls bpy.ops.proscenio.help topic='status_legend')

### BL-HELP-04 · Help button '?' (proscenio.help, topic='helpers')
- status: pending
- review: keep
- pre: Helpers subpanel header rendered.
- steps:
  1. Click the '?' (QUESTION) icon at the far right of the 'Helpers' header.
- observe: A 480px popup opens titled 'Helpers' with summary 'Viewport authoring aids that are not part of the export pipeline.', a 'What it does' section, a 'Preview Camera' section, and an 'Open online docs' button linking to .../blender-addon/helpers.
- intent: UNDOCUMENTED in the doc page; opens the in-panel Helpers help popup. The 'helpers' help topic mirrors the doc text.
- code: apps/blender/panels/_helpers.py:84-85 (op.topic='helpers'); operator at help_dispatch.py:50-98

### BL-HELP-05 · Preview Camera button (proscenio.create_ortho_camera)
- status: pending
- review: keep
- pre: A Proscenio scene open. No specific active object/mode required. scene.proscenio.pixels_per_unit set (falls back to 100.0 if props missing).
- steps:
  1. Expand Helpers > click 'Preview Camera' (OUTLINER_OB_CAMERA icon). Re-click to test the focus/update path.
- observe: First click: creates object 'Proscenio.PreviewCam' at location (0,-10,0) rotated +90deg on X (front view), type=ORTHO, ortho_scale = max(res_x,res_y)/pixels_per_unit; sets it as scene.camera and the sole selection; INFO report "created 'Proscenio.PreviewCam' (ortho_scale=...)". Re-click: reuses the existing object, recomputes ortho_scale, reports "updated ...". Press Numpad 0 to look through it (native Blender, per the operator tooltip). REGISTER|UNDO so Ctrl+Z reverts creation.
- intent: Drops an orthographic front camera framed the way the Godot importer expects, so the viewport matches the runtime framing.
- code: apps/blender/panels/helpers.py:31-35 (button); operator at apps/blender/operators/armature/authoring_camera.py:16-53

## Diagnostics + Help system + Addon Preferences + status badges

### BL-DIAG-01 · Diagnostics panel (visibility / poll)
- status: pending
- review: keep
- observe: With Debug mode OFF the Diagnostics subpanel is absent; with Debug mode ON it appears (DEFAULT_CLOSED) at bl_order 13 below Help.
- intent: UNDOCUMENTED - the index sidebar list (panels 01-11) never mentions a Diagnostics panel; only the addon-prefs description says debug_mode 'Show the developer surface: the Diagnostics panel'.
- code: apps/blender/panels/diagnostics.py:24-26

### BL-DIAG-03 · Diagnostics header status badge (blender-only)
- status: pending
- review: keep
- observe: Custom Blender badge icon renders (or TOOL_SETTINGS built-in if preview load failed); tooltip reads the blender-only band text ('Authoring shortcut. Lives entirely on the Blender side - does NOT alter the .proscenio export').
- intent: Status badge legend: blender-only = authoring shortcut that never reaches the export (index 'Status badges').
- code: apps/blender/panels/diagnostics.py:29 -> apps/blender/panels/_helpers.py:46-69; feature_status.py:120

### BL-DIAG-06 · Help panel (visibility)
- status: pending
- review: keep
- observe: Help subpanel is always present (regardless of debug_mode), collapsed by default, sitting just above Diagnostics.
- intent: UNDOCUMENTED - the index sidebar list (panels 01-11) does not include a Help panel; the panel's own docstring calls it a 'Shortcut cheat-sheet - every Proscenio operator with its idname.'
- code: apps/blender/panels/help.py:32-41

### BL-DIAG-07 · Help panel body label 'Operators (use F3 to search):'
- status: pending
- review: keep
- observe: A QUESTION-icon label 'Operators (use F3 to search):' renders at the top of the body.
- intent: UNDOCUMENTED - read-only instructional label; doc never describes the Help cheat-sheet.
- code: apps/blender/panels/help.py:48

### BL-DIAG-08 · Help panel operator reference rows (18 label/idname pairs)
- status: pending
- review: keep
- observe: Exactly 18 rows render, each a two-label row (e.g. 'Validate' / 'proscenio.validate_export'); rows are plain read-only labels (NOT clickable operator buttons) - selecting/clicking does nothing.
- intent: UNDOCUMENTED - static two-column cheat-sheet mapping a human label to its operator idname for F3 search.
- code: apps/blender/panels/help.py:49-52 (loop over _OPERATOR_REFERENCE, help.py:11-29)

### BL-DIAG-09 · Help header status badge (blender-only)
- status: pending
- review: keep
- observe: Blender badge icon renders; tooltip shows the blender-only band text.
- intent: Status badge legend: blender-only band per index 'Status badges'.
- code: apps/blender/panels/help.py:44 -> _helpers.py:46-69; feature_status.py:119

### BL-DIAG-13 · Help popup unknown-topic fallback
- status: pending
- review: keep
- observe: Popup shows a single ERROR-icon label "unknown help topic: 'nope'" and nothing else.
- intent: Defensive: an unresolved topic id surfaces an error label rather than crashing.
- code: apps/blender/operators/help_dispatch.py:73-76

### BL-DIAG-15 · Addon Preferences - 'Developer' box label
- status: pending
- review: keep
- observe: A boxed section with a TOOL_SETTINGS-icon 'Developer' label appears, containing the two prefs below.
- intent: UNDOCUMENTED grouping label; box header for the developer prefs.
- code: apps/blender/addon_prefs.py:61-62

### BL-DIAG-16 · Addon Preferences - 'Log level' dropdown (errors/info/debug)
- status: pending
- review: keep
- observe: Changing the enum immediately calls set_min_level: 'Errors only' suppresses report_info/report_warn output, 'Debug' surfaces '[Proscenio debug]'-tagged traces; default is 'Info'. Choice persists across restart and is re-applied at register via _sync_log_level_from_prefs.
- intent: UNDOCUMENTED in the doc page; prop description: controls how much operators report to the Info log (Errors only / Info default / Debug adds per-item traces).
- code: apps/blender/addon_prefs.py:29-48 (update=_on_log_level_update -> report.set_min_level)

### BL-DIAG-17 · Addon Preferences - 'Debug mode' checkbox
- status: pending
- review: keep
- observe: ON reveals the Diagnostics subpanel (and the automesh Debug Pipeline subpanel elsewhere); OFF hides them. Has no update callback - effect appears on next panel redraw.
- intent: UNDOCUMENTED in the doc page; prop description: 'Show the developer surface: the Diagnostics panel and the automesh Debug Pipeline subpanel.' Off by default.
- code: apps/blender/addon_prefs.py:50-58; consumed by debug_mode_enabled() at addon_prefs.py:67-80 and diagnostics.py:26

### BL-DIAG-18 · Status legend popup (status_legend topic content)
- status: pending
- review: keep
- observe: Popup titled 'Status badges' lists all four bands with the same definitions as the index page; the popup is the only place godot-ready/planned/out-of-scope bands are described in-addon.
- intent: index 'Status badges': legend mapping godot-ready / blender-only / planned / out-of-scope to pipeline meaning.
- code: apps/blender/core/help_topics.py:63-96; opened via help_dispatch.py:43

### BL-DIAG-02 · Run Smoke Test (PLAY icon button)
- status: pending
- review: keep
- pre: Debug mode ON so Diagnostics panel is visible.
- steps:
  1. Open Diagnostics subpanel > click 'Run Smoke Test'
- observe: Info-area report 'Proscenio smoke test OK' (no 'Proscenio:' prefix) and system console prints '[Proscenio] Proscenio smoke test OK'; operator returns FINISHED.
- intent: UNDOCUMENTED in the doc page; operator's own bl_description: 'Print a sanity check to the system console' confirming the addon registers and dispatches.
- code: apps/blender/panels/diagnostics.py:33 -> apps/blender/operators/help_dispatch.py:108-112

### BL-DIAG-04 · Diagnostics header status badge (click)
- status: pending
- review: keep
- pre: Debug mode ON.
- steps:
  1. Open Diagnostics header > click the Blender-mark status icon
- observe: invoke_popup opens the 'Status badges' legend popup (status_legend topic) listing the four bands; clicking does NOT toggle/edit anything else.
- intent: Per-feature status: 'Click the icon to re-open this legend' (status_legend help topic).
- code: apps/blender/operators/help_dispatch.py:42-44 (PROSCENIO_OT_status_info.invoke)

### BL-DIAG-05 · Diagnostics header '?' help button
- status: pending
- review: keep
- pre: Debug mode ON.
- steps:
  1. Open Diagnostics header > click the '?' icon
- observe: A 480px help popup opens titled 'Proscenio pipeline overview' (NOT a Diagnostics-specific topic) - it shows the generic pipeline+status-badges content, not 'the matching help' the doc promises.
- intent: index line 26: each header carries a '?' that opens the matching help inline.
- code: apps/blender/panels/diagnostics.py:29 -> _helpers.py:84-85 (topic='pipeline_overview')

### BL-DIAG-10 · Help header status badge (click)
- status: pending
- review: keep
- pre: None.
- steps:
  1. Open Help header > click the status icon
- observe: 'Status badges' legend popup opens.
- intent: Click the status icon re-opens the status legend (status_legend topic).
- code: apps/blender/operators/help_dispatch.py:42-44

### BL-DIAG-11 · Help header '?' help button
- status: pending
- review: keep
- pre: None.
- steps:
  1. Open Help header > click '?'
- observe: Popup opens 'Proscenio pipeline overview' (generic), not a Help-panel-specific topic.
- intent: index line 26: '?' opens the matching help inline.
- code: apps/blender/panels/help.py:44 -> _helpers.py:84-85 (topic='pipeline_overview')

### BL-DIAG-12 · Help popup (PROSCENIO_OT_help) content rendering
- status: pending
- review: keep
- pre: Any '?' button clicked.
- steps:
  1. Click any '?' > read popup > if a 'See also' http link or 'Open online docs' button present, click it
- observe: 480px popup shows QUESTION-titled header, summary line, DOT-marked section headings + body lines; 'Open online docs' (HELP icon) opens the doc_url via wm.url_open; http see-also entries are clickable url buttons, non-http see-also entries render as indented plain labels.
- intent: help_dispatch docstring: 'Pop up an in-panel help dialog for a given topic id' rendering title, summary, sections, see-also, online-docs button.
- code: apps/blender/operators/help_dispatch.py:64-97

### BL-DIAG-14 · Status-info tooltip dispatch (PROSCENIO_OT_status_info.description)
- status: pending
- review: keep
- pre: Any panel header with a status badge.
- steps:
  1. Hover any status badge icon and read the tooltip; also observe a band whose value is invalid
- observe: Tooltip text equals STATUS_BADGES[band].tooltip for the badge's band; an invalid band value falls back to the operator bl_label 'Proscenio: Feature Status'.
- intent: Per-feature status: hovering the icon surfaces the band-specific tooltip.
- code: apps/blender/operators/help_dispatch.py:30-40
