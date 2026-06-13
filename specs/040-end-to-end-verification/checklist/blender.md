# Spec 040 - Blender addon manual-test checklist

Render of the structured inventory for every user-reachable Blender addon control,
audited against its documented intent. Walk this before a release tag; check items off and
set each Status. Format legend in [../STUDY.md](../STUDY.md).

## Surface tokens

| Token | Panel / section |
| --- | --- |
| OUTLN | Outliner panel |
| ELEM | Element panel (Active Sprite / Active Mesh, type, region, drive-from-bone, reproject UV) |
| SLOT | Slots panel + slot operators |
| SKEL | Skeleton panel: armature picker, bone list, pose helpers, Quick Armature, IK, authoring camera, pose library |
| MESH | Mesh Generation panel: automesh one-click + interactive modal + debug pipeline |
| WPAINT | Weight Paint panel: five bind modes, Edit Weights modal, brush preset, copy weights, sidecar IO, snapshot restore |
| ANIM | Animation panel (read-only action summary) |
| ATLAS | Atlas panel: pack / unpack / apply |
| VALID | Validation panel (export-blocking issues list) |
| PIPE | Pipeline panel: import Photoshop manifest + export/re-export .proscenio |
| HELP | Helpers panel (viewport authoring aids outside export) |
| DIAG | Diagnostics + Help system + Addon Preferences + status badges |

## Outliner panel

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-OUTLN-01 | Outliner subpanel foldout (header) | Panel is DEFAULT_CLOSED on first open; clicking the header expands it to reveal filter row + list; clicking again collapses. | Sprite-centric flat list replacing Blender's outliner for big rigs; collapsed by default. | apps/blender/panels/outliner.py:127-139 | pending |
| BL-OUTLN-02 | Status badge button (Blender-only mark) | Shows the custom Blender-only mark (feature_status 'outliner' = BLENDER_ONLY); hover surfaces the blender-only band tooltip; click opens the status_legend help popup (via proscenio.status_info > proscenio.help). | UNDOCUMENTED | apps/blender/panels/_helpers.py:83 (draw via draw_subpanel_header, outliner.py:139) | pending |
| BL-OUTLN-04 | Outliner filter (search text field, VIEWZOOM icon) | Rows whose object name (lowercased) does not contain the substring are hidden live as you type; clearing the field shows all Proscenio-relevant rows again. | Type a substring to filter the list live; empty shows every Proscenio-relevant object. | apps/blender/panels/outliner.py:148 (prop) + filter_items:95,117 | pending |
| BL-OUTLN-05 | Favorites-only toggle (SOLO_ON icon next to filter) | When enabled, only rows whose object has is_outliner_favorite=True remain visible; disabling restores the full filtered list. Note: favorites are NOT reordered to the top (see finding). | Toggle next to the filter that hides everything except favorited rows. | apps/blender/panels/outliner.py:149 (prop) + filter_items:100-116 | pending |
| BL-OUTLN-06 | Outliner UIList (template_list, 8 rows) | Rows sorted by category rank then name: rank0 slot Empty 'LINK_BLEND [slot] <name>'; rank1 attachment mesh 'OBJECT_DATAMODE   -> <name>'; rank2 sprite mesh 'MESH_DATA <name>[ @ <bone>]'; rank3 armature 'ARMATURE_DATA [arm] <name>'. Cameras/lights/etc (rank 9) are hidden. | Flat list: slots first (with [slot] prefix and indented attachments), sprite meshes, then armatures last ([arm]). | apps/blender/panels/outliner.py:150-158 (template_list) + draw_item:40-84 | pending |
| BL-OUTLN-09 | Sprite-mesh bone-parent suffix label (' @ <bone>') | Row label reads '<name> @ <parent_bone>'; meshes not bone-parented show just '<name>'. Doc never mentions the '@ bone' affordance. | UNDOCUMENTED | apps/blender/panels/outliner.py:62-63 | pending |
| BL-OUTLN-10 | Native 'Filter by Name' field (UIList expand arrows) | Native filter_name is applied (lowercased substring) only when the Proscenio search bar is empty; the Proscenio bar wins when both are set. Doc never mentions Blender's native UIList filter row. | UNDOCUMENTED | apps/blender/panels/outliner.py:96-99 (self.filter_name honored) | pending |
| BL-OUTLN-11 | Native UIList sort/invert/name toggles (expand arrows) | filter_items always returns its own category-then-name order via flt_neworder, so the custom sort overrides native sort; the native invert-filter toggle (Show inactive) may still flip which rows are shown. Doc never mentions these controls. | UNDOCUMENTED | apps/blender/panels/outliner.py:150-158 (template_list) + filter_items:120-124 | pending |
| BL-OUTLN-12 | active_outliner_index list highlight | The UIList active-row highlight follows the clicked object via active_outliner_index. Doc never mentions a persistent active-row highlight; index is computed against bpy.data.objects order, not the displayed order (see finding). | UNDOCUMENTED | apps/blender/properties/scene_props.py:484-489 + selection.py:153-167 | pending |
| BL-OUTLN-13 | 'Proscenio scene props not registered' fallback label | Panel body shows an ERROR-icon label 'Proscenio scene props not registered' and draws nothing else. Doc never mentions this failure label. | UNDOCUMENTED | apps/blender/panels/outliner.py:143-146 | pending |

#### [ ] BL-OUTLN-03 · Help '?' button (header)
- **Intent:** Open an explanation of the Outliner panel section.
- **Code:** apps/blender/panels/_helpers.py:84 (topic='outliner', help_dispatch.py:50-97)
- **Pre:** Outliner subpanel header visible.
- **Steps:** Click the '?' (QUESTION) icon at the right of the 'Outliner' header.
- **Expect:** A 480px-wide popup opens titled 'Outliner' with the summary, sections, and an 'Open online docs' link resolving to the outliner doc page (topic 'outliner' exists in help_topics).
- **Status:** pending

#### [ ] BL-OUTLN-07 · Row click (proscenio.select_outliner_object)
- **Intent:** Click a row to make that object active and selected.
- **Code:** apps/blender/panels/outliner.py:71-77 + operators/selection.py:40-59
- **Pre:** Outliner expanded with at least one visible row.
- **Steps:** Click on a row label (the embossless button spanning the row text).
- **Expect:** All other objects are deselected; the clicked object becomes the sole selection and the active object (select_only); active_outliner_index is synced to that object's index in bpy.data.objects. If the object was deleted, a warning is reported and the op cancels.
- **Status:** pending

#### [ ] BL-OUTLN-08 · Per-row favorite toggle (SOLO_OFF / SOLO_ON, proscenio.toggle_outliner_favorite)
- **Intent:** SOLO icon pins a row as a favorite (so it survives the Favorites-only filter).
- **Code:** apps/blender/panels/outliner.py:78-84 + operators/selection.py:170-197
- **Pre:** Outliner expanded with at least one visible row.
- **Steps:** Click the SOLO icon at the right end of a row > click again to unpin.
- **Expect:** Icon flips SOLO_OFF<->SOLO_ON; obj.proscenio.is_outliner_favorite flips and is undoable (REGISTER, UNDO). If the object's PropertyGroup is unregistered, a warning is reported and the op cancels. The row is NOT moved to the top (see finding).
- **Status:** pending

## Element panel (Active Sprite / Active Mesh, type, region, drive-from-bone, reproject UV)

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-ELEM-01 | Element panel empty-state label "select a mesh or sprite element" | Panel body shows only the INFO-icon label 'select a mesh or sprite element'; no element_type selector, no subpanels. | Per-element settings panel; shows a prompt when no mesh/sprite is active. | apps/blender/panels/element.py:49-50 | pending |
| BL-ELEM-02 | Element panel "proscenio property group not registered" error label | ERROR-icon label 'proscenio property group not registered'; no further controls drawn. | UNDOCUMENTED (registration-gap guard). | apps/blender/panels/element.py:53-55 | pending |
| BL-ELEM-03 | Element type selector (Mesh / Sprite) - Weight Paint locked variant | element_type dropdown is shown but greyed/disabled; INFO label 'element type is locked in Weight Paint mode'; no other element fields or subpanels. | Element type decides the Godot node; UNDOCUMENTED that it is locked in Weight Paint mode. | apps/blender/panels/element.py:56-61 | pending |
| BL-ELEM-04 | Element type dropdown (Mesh / Sprite) | Choosing Mesh shows the Active Mesh subpanel; choosing Sprite shows the Active Sprite subpanel (poll swaps which subpanel appears); element_type Custom Property mirrors on change. | Mesh exports a Polygon2D (deformable cutout w/ UVs+weights); Sprite exports a Sprite2D (hframes x vframes grid). | apps/blender/panels/element.py:62 (prop element_type, items object_props.py:26-34) | pending |
| BL-ELEM-05 | Element panel inline validation issue rows | One alert/INFO row per issue (e.g. 'sprite element mesh is N verts / M face(s), not a single quad...'); rows naming an object are clickable select-issue buttons. | Surfaces validation issues for the active element (UNDOCUMENTED on the doc page). | apps/blender/panels/element.py:63-64; apps/blender/core/validation/active_element.py:9 | pending |
| BL-ELEM-06 | Element subpanel header status badge (Godot-ready mark) | Custom Godot icon (GODOT_READY band) shown; hovering surfaces the band tooltip via proscenio.status_info; clicking opens the band info. | UNDOCUMENTED (status-band badge surfaced on every subpanel header). | apps/blender/panels/_helpers.py:46-69, 83; element.py:44 | pending |
| BL-ELEM-08 | Active Mesh subpanel - poly/vertex-group count label | Label '<N> polygon(s), <M> vertex group(s)' reflecting the mesh's polygon count and vertex_groups length. | UNDOCUMENTED read-out (doc only says mesh exports as Polygon2D). | apps/blender/panels/_draw_mesh.py:19-22 | pending |
| BL-ELEM-11 | Isolated material checkbox | material_isolated bool toggles; Custom Property mirrors; affects Pack Atlas behavior (material kept on this object). | UNDOCUMENTED on element doc; when packing, keep this sprite's own material instead of linking to the shared PackedAtlas material. | apps/blender/panels/_draw_mesh.py:24; object_props.py:157-167 | pending |
| BL-ELEM-12 | Exclude from atlas checkbox | exclude_from_atlas bool toggles; Custom Property mirrors; object skipped by Pack Atlas. | UNDOCUMENTED on element doc; keep this sprite out of Pack Atlas entirely (UVs/material untouched, ships own texture). | apps/blender/panels/_draw_mesh.py:25; object_props.py:168-178 | pending |
| BL-ELEM-13 | Active Mesh header status badge + "?" help | Godot-ready badge shown; help opens topic 'active_mesh' (anchor element#active-mesh). | UNDOCUMENTED; status badge + help (topic 'active_mesh'). | apps/blender/panels/element.py:84; _helpers.py:83-85 | pending |
| BL-ELEM-14 | hframes field (Horizontal frames) | hframes int (min 1, soft_max 64); region readout 'frame: WxH px (hf x vf grid)' updates; CP mirrors. | Spritesheet grid columns. | apps/blender/panels/_draw_sprite.py:23; object_props.py:79-86 | pending |
| BL-ELEM-15 | vframes field (Vertical frames) | vframes int (min 1, soft_max 64); frame-size readout updates; CP mirrors. | Spritesheet grid rows. | apps/blender/panels/_draw_sprite.py:24; object_props.py:87-94 | pending |
| BL-ELEM-16 | frame field (Initial frame) | frame int (min 0) stored; written as Sprite2D rest frame at export; CP mirrors. | The cell shown at rest pose; animation tracks override it. | apps/blender/panels/_draw_sprite.py:25; object_props.py:95-103 | pending |
| BL-ELEM-17 | centered checkbox | centered bool (default True) toggles; mapped to Sprite2D.centered on export; CP mirrors. | Godot Sprite2D.centered: texture centred on origin, or its top-left at the origin. | apps/blender/panels/_draw_sprite.py:26; object_props.py:104-109 | pending |
| BL-ELEM-18 | Active Sprite atlas/region readout labels | If no image linked: 'atlas: not linked in material'. Else 'atlas: WxH px', 'region: WxH px (full atlas/manual)', 'frame: WxH px (hf x vf grid)'. | UNDOCUMENTED; shows atlas size, region size, and frame size for the sprite. | apps/blender/panels/_draw_sprite.py:27,31-54 | pending |
| BL-ELEM-21 | Active Sprite header status badge + "?" help | Godot-ready badge; help opens topic 'active_sprite' (anchor element#active-sprite). | UNDOCUMENTED; status badge + help (topic 'active_sprite'). | apps/blender/panels/element.py:108; _helpers.py:83-85 | pending |
| BL-ELEM-22 | Texture Region mode dropdown (Auto / Manual) | Auto: shows hint label only. Manual: reveals X/Y/W/H rows (+ Snap button for mesh). CP mirrors. | Auto reads region from UV bounds at export; Manual reads region_x/y/w/h verbatim. | apps/blender/panels/_draw_region.py:20; object_props.py:110-120 | pending |
| BL-ELEM-23 | Texture Region Auto-mode hint label | Mesh: 'computed from UV bounds at export'. Sprite: 'omitted at export - full atlas used' (INFO icon). | Auto reads region from UV bounds at export (mesh) / full atlas used (sprite). | apps/blender/panels/_draw_region.py:30-36 | pending |
| BL-ELEM-24 | region_x field (X) | region_x float clamped [0,1], precision 4; readout updates; CP mirrors. | Manual region origin X, normalized [0,1] of atlas width. | apps/blender/panels/_draw_region.py:23; object_props.py:121-129 | pending |
| BL-ELEM-25 | region_y field (Y) | region_y float clamped [0,1], precision 4; CP mirrors. | Manual region origin Y, normalized [0,1] of atlas height. | apps/blender/panels/_draw_region.py:24; object_props.py:130-138 | pending |
| BL-ELEM-26 | region_w field (Width) | region_w float clamped [0,1] (default 1.0), precision 4; sprite readout 'region: WxH px (manual)' updates; CP mirrors. | Manual region width, normalized [0,1] of atlas width. | apps/blender/panels/_draw_region.py:26; object_props.py:139-147 | pending |
| BL-ELEM-27 | region_h field (Height) | region_h float clamped [0,1] (default 1.0), precision 4; CP mirrors. | Manual region height, normalized [0,1] of atlas height. | apps/blender/panels/_draw_region.py:27; object_props.py:148-156 | pending |
| BL-ELEM-30 | Texture Region header status badge + "?" help | Godot-ready badge; help opens topic 'texture_region' (anchor element#texture-region). | UNDOCUMENTED; status badge + help (topic 'texture_region'). | apps/blender/panels/element.py:132; _helpers.py:83-85 | pending |
| BL-ELEM-31 | Drive from Bone - Target dropdown | driver_target enum (Frame index / Region X/Y/W/H, default region_x); selection drives which proscenio.* gets the driver and which value the readout shows; CP mirrors. | Wires a driver into a sprite proscenio.* property (frame / region_x/y/w/h). | apps/blender/panels/_draw_driver_shortcut.py:21; object_props.py:180-185 | pending |
| BL-ELEM-32 | Drive from Bone - Armature picker | Picker lists ARMATURE objects only (poll is_armature); selecting one populates the Bone dropdown; CP mirrors. | Pick the armature whose pose bone supplies the driver value. | apps/blender/panels/_draw_driver_shortcut.py:22; object_props.py:186-191; _dynamic_items.py:29-31 | pending |
| BL-ELEM-33 | Drive from Bone - Bone dropdown | Lists every bone of the picked armature. Sentinel '(pick an armature first)' when no armature; '(armature has no bones)' when empty. | Pick the pose bone whose transform feeds the driver. | apps/blender/panels/_draw_driver_shortcut.py:23; object_props.py:192-196; _dynamic_items.py:44-63 | pending |
| BL-ELEM-34 | Drive from Bone - Axis dropdown | driver_source_axis enum; PG default ROT_Y; list order ROT_Z, ROT_X, ROT_Y, LOC_X/Y/Z; CP mirrors. | Pose bone transform channel feeding the driver (ROT_Z/X/Y, LOC_X/Y/Z). | apps/blender/panels/_draw_driver_shortcut.py:24; object_props.py:197-202 | pending |
| BL-ELEM-35 | Drive from Bone - In Min / In Max fields | driver_in_min (default -1.5708) / driver_in_max (default 1.5708) floats; feed build_driver_expression on Drive. | Two-range linear map input: bone-channel values mapped to output min/max. | apps/blender/panels/_draw_driver_shortcut.py:29-31; object_props.py:203-218 | pending |
| BL-ELEM-36 | Drive from Bone - Out Min / Out Max fields | driver_out_min (0.0) / driver_out_max (1.0) floats; build_driver_expression sorts the output band so inverted ranges clamp correctly. | Two-range linear map output: target value at the input min/max. | apps/blender/panels/_draw_driver_shortcut.py:32-34; object_props.py:219-230 | pending |
| BL-ELEM-37 | Drive from Bone - Expression field (Advanced) | driver_expression string (default 'var') shown instead of the four range fields; used verbatim on Drive when Advanced on. | Raw driver expression fallback ('var' = bone channel) shown when Advanced is on. | apps/blender/panels/_draw_driver_shortcut.py:26-27; object_props.py:240-248 | pending |
| BL-ELEM-38 | Drive from Bone - Advanced expression toggle | On: hides In/Out rows, shows Expression field. Off: shows the four range fields. | Use the raw expression instead of the two-range linear map. | apps/blender/panels/_draw_driver_shortcut.py:35; object_props.py:231-239 | pending |
| BL-ELEM-39 | Drive from Bone - live Value readout | Label 'Value: <n>' - whole for int target (frame), 3-decimal for region channels; absent if getattr(props, target) is None. | UNDOCUMENTED; inline read-back of the driven target property's current value. | apps/blender/panels/_draw_driver_shortcut.py:37,46-59 | pending |
| BL-ELEM-43 | Drive from Bone header status badge + "?" help | Godot-ready badge; help opens topic 'drive_from_bone' (anchor element#drive-from-bone). | Wires a driver between a pose bone and a sprite proscenio.* property (help topic 'drive_from_bone'). | apps/blender/panels/element.py:156; _helpers.py:83-85 | pending |

#### [ ] BL-ELEM-07 · Element subpanel header "?" help button
- **Intent:** UNDOCUMENTED (opens the in-panel help topic for 'active_element').
- **Code:** apps/blender/panels/_helpers.py:84-85; element.py:44 (topic 'active_element')
- **Pre:** Active MESH
- **Steps:** Click the QUESTION-mark icon on the Element panel header
- **Expect:** proscenio.help fires with topic='active_element'; the Element help popup/section opens (maps to docs anchor 'element').
- **Status:** pending

#### [ ] BL-ELEM-09 · Reproject UV button
- **Intent:** UNDOCUMENTED on element doc; re-projects the mesh UVs (Smart UV Project) so the texture lines up after vertex edits.
- **Code:** apps/blender/panels/_draw_mesh.py:23; apps/blender/operators/uv_authoring.py:22-80
- **Pre:** Active MESH (element_type=mesh) in OBJECT mode (operator poll requires OBJECT)
- **Steps:** Select a mesh element in Object Mode > Active Mesh subpanel > click Reproject UV
- **Expect:** UVs re-unwrapped via smart_project (angle_limit default 1.15192); selection/active restored; INFO report 'reprojected UVs on <name>'; redo panel exposes Angle limit. May rotate/mirror UVs.
- **Status:** pending

#### [ ] BL-ELEM-10 · Reproject UV - disabled/poll-fail path
- **Intent:** UNDOCUMENTED; operator is OBJECT-mode only.
- **Code:** apps/blender/operators/uv_authoring.py:49-56
- **Pre:** Active MESH in EDIT mode (or non-mesh active)
- **Steps:** Enter Edit Mode on the mesh > Active Mesh subpanel still drawn only in object-context; invoke proscenio.reproject_sprite_uv
- **Expect:** Operator poll returns False (button/op unavailable) because context.mode != OBJECT; no UV change.
- **Status:** pending

#### [ ] BL-ELEM-19 · Setup Preview button (sprite preview shader)
- **Intent:** UNDOCUMENTED; installs the SpriteFrameSlicer material-preview shader.
- **Code:** apps/blender/panels/_draw_sprite.py:66-77 (op proscenio.setup_sprite_frame_preview)
- **Pre:** Active sprite MESH whose material lacks the slicer node group
- **Steps:** Active Sprite subpanel > click Setup Preview
- **Expect:** Setup button enabled only when no slicer present; firing adds the SpriteFrameSlicer node group; Setup greys out, Remove enables.
- **Status:** pending

#### [ ] BL-ELEM-20 · Remove Preview button (sprite preview shader)
- **Intent:** UNDOCUMENTED; removes the SpriteFrameSlicer material-preview shader.
- **Code:** apps/blender/panels/_draw_sprite.py:78-83 (op proscenio.remove_sprite_frame_preview)
- **Pre:** Active sprite MESH whose material carries the slicer node group
- **Steps:** Active Sprite subpanel > click Remove Preview
- **Expect:** Remove enabled only when slicer present; firing strips the node group; Remove greys out, Setup re-enables.
- **Status:** pending

#### [ ] BL-ELEM-28 · Snap to UV bounds button
- **Intent:** Fills the manual region fields from the current UV.
- **Code:** apps/blender/panels/_draw_region.py:28-29; apps/blender/operators/uv_authoring.py:83-131
- **Pre:** Active MESH with element_type=mesh, region_mode=manual, OBJECT mode, mesh has UV layer + polygons
- **Steps:** Mesh element > region_mode=Manual > click Snap to UV bounds
- **Expect:** region_x/y/w/h overwritten with UV bounds (v flipped to Godot space via compute_region_from_uvs); INFO report 'snapped region to UV bounds (...)'. Warn report if no UV/polygons or PG missing.
- **Status:** pending

#### [ ] BL-ELEM-29 · Snap to UV bounds - absence for sprite elements
- **Intent:** Doc implies Snap fills manual fields from UV generally; code hides it for sprite element_type.
- **Code:** apps/blender/panels/_draw_region.py:28 (gated on element_type=='mesh')
- **Pre:** Active MESH with element_type=sprite, region_mode=manual
- **Steps:** Sprite element > region_mode=Manual > inspect Texture Region box
- **Expect:** X/Y/W/H fields shown but NO Snap to UV bounds button (sprite path omits it).
- **Status:** pending

#### [ ] BL-ELEM-40 · Drive from Bone button (create driver)
- **Intent:** Materializes a Blender driver from the picked bone channel into proscenio.<target>; re-running replaces it.
- **Code:** apps/blender/panels/_draw_driver_shortcut.py:39-43; apps/blender/operators/driver.py:96-262
- **Pre:** Active sprite/mesh MESH; armature picked with at least one bone; a bone selected (row enabled only then)
- **Steps:** Pick armature + bone + axis + ranges/target > click Drive from Bone
- **Expect:** Driver added on proscenio.<target>; stale sibling drivers off same (armature,bone) purged; SCRIPTED expression set; INFO report 'driver on <sprite>.proscenio.<target> <- <arm>:<bone>.<axis>'. Redo panel exposes operator props.
- **Status:** pending

#### [ ] BL-ELEM-41 · Drive from Bone button - disabled (no bone) path
- **Intent:** UNDOCUMENTED; button is disabled until a bone is picked.
- **Code:** apps/blender/panels/_draw_driver_shortcut.py:40-42
- **Pre:** Active MESH; no armature or no bone selected
- **Steps:** Drive from Bone with empty Armature/Bone > observe button
- **Expect:** row.enabled False -> Drive from Bone button greyed; cannot fire.
- **Status:** pending

#### [ ] BL-ELEM-42 · Drive from Bone - error reports (bad armature/bone)
- **Intent:** UNDOCUMENTED; operator validates armature/bone before adding the driver.
- **Code:** apps/blender/operators/driver.py:197-204
- **Pre:** Invoke proscenio.create_driver with armature_name unset/non-armature or bone not in armature
- **Steps:** Force-run create_driver via redo panel with mismatched armature/bone
- **Expect:** report_error 'pick a source armature in the panel' or "bone '<x>' not in armature '<y>'"; returns CANCELLED; no driver added.
- **Status:** pending

## Slots panel + slot operators

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-SLOT-01 | Slots panel header status badge (slot_system) | Hover shows the godot-ready band tooltip; click opens the status-legend help popup (proscenio.status_info -> proscenio.help topic='status_legend'). | UNDOCUMENTED — status icon for the slot_system feature band (godot-ready). | apps/blender/panels/slots.py:51-52 -> _helpers.py:46-69 | pending |
| BL-SLOT-02 | Slots panel '?' help button | A 480px-wide help popup opens for the 'slot_system' topic (title + summary + sections, 'Open online docs' button). | UNDOCUMENTED — opens the slot_system help popup. | apps/blender/panels/slots.py:51-52 -> _helpers.py:84-86 | pending |
| BL-SLOT-03 | 'no slots yet - select meshes and Create Slot' empty-state label | An INFO-icon label 'no slots yet - select meshes and Create Slot' is shown instead of a list. | Parent panel lists every slot; when none exist it prompts to create one. | apps/blender/panels/slots.py:58-59 | pending |
| BL-SLOT-05 | Per-slot mesh-child count badge (number + OUTLINER_OB_MESH icon) | Number equals the count of direct children with type=='MESH'; updates after adding/removing attachments and a redraw. | UNDOCUMENTED — shows the count of MESH children for the slot on its row. | apps/blender/panels/slots.py:71-72 | pending |
| BL-SLOT-06 | Tip box (Pose Mode / Object Mode hint, 2 lines) | Box (scale_y 0.8) shows 'Pose Mode + active bone: slot anchored to the bone' (INFO) and 'Object Mode + meshes: slot wraps the selection' (BLANK1). Static text, always present. | UNDOCUMENTED — static hint explaining how Create Slot anchors (pose-bone vs mesh selection). | apps/blender/panels/slots.py:74-77 | pending |
| BL-SLOT-08 | Create Slot redo 'Slot name' field | The Empty is renamed to the typed value on re-execute; empty value falls back to '<bone>.slot' or 'slot'. | Name of the new Empty; defaults to '<bone>.slot' or 'slot'. | apps/blender/operators/slot/create.py:58-62,116-119 | pending |
| BL-SLOT-09 | Active Slot subpanel header status badge (active_slot) | Hover shows godot-ready tooltip; click opens the status-legend popup. | UNDOCUMENTED — status icon for the active_slot feature band (godot-ready). | apps/blender/panels/slots.py:101-102 -> _helpers.py:46-69 | pending |
| BL-SLOT-10 | Active Slot subpanel '?' help button | Help popup for the 'active_slot' topic opens. | UNDOCUMENTED — opens the active_slot help popup. | apps/blender/panels/slots.py:101-102 -> _helpers.py:84-86 | pending |
| BL-SLOT-12 | Slot name label ('Slot "<name>"', LINK_BLEND) | Shows 'Slot \'<empty.name>\''. | UNDOCUMENTED — read-only header showing the active slot's name. | apps/blender/panels/slots.py:117 | pending |
| BL-SLOT-13 | Parent bone readout label ('bone: <name>' / '(unparented)', BONE_DATA) | Shows the parent_bone name when parent_type=='BONE', else '(unparented)'. | UNDOCUMENTED — read-only readout of the slot's parent bone. | apps/blender/panels/slots.py:115,118-121 -> validation/active_slot.py:63-73 | pending |
| BL-SLOT-14 | 'no parent bone' alert warning row | A red (alert) ERROR-icon row 'no parent bone - attachments will not follow any bone' appears; absent when bone-parented. | UNDOCUMENTED — alert when the slot has no bone parent (attachments won't follow a bone). | apps/blender/panels/slots.py:122-128 | pending |
| BL-SLOT-15 | 'Attachments (N):' label | N equals the number of sorted MESH children; OUTLINER_OB_MESH icon. | Lists the slot's child attachments (heading shows count). | apps/blender/panels/slots.py:131 | pending |
| BL-SLOT-16 | 'empty slot - add child meshes' alert label | A red (alert) INFO-icon row 'empty slot - add child meshes' appears. | UNDOCUMENTED — alert shown when the active slot has no MESH children. | apps/blender/panels/slots.py:132-135 | pending |
| BL-SLOT-18 | Attachment name label (per attachment) | Shows child.name verbatim. | UNDOCUMENTED — read-only name of each child attachment in the list. | apps/blender/panels/slots.py:149 | pending |
| BL-SLOT-19 | Attachment kind label (mesh/sprite, MESH_DATA/IMAGE_DATA) | Shows 'mesh' (MESH_DATA) or 'sprite' (IMAGE_DATA) per the child's proscenio.element_type; defaults to 'mesh' when props missing. | UNDOCUMENTED — read-only element_type of each attachment. | apps/blender/panels/slots.py:28-37,150-151 | pending |
| BL-SLOT-22 | Active-slot validation issue rows (clickable [name] message) | ERROR rows tint red (INFO rows plain); rows naming an object are clickable buttons '[name] message' that run proscenio.select_issue_object to select that object. | UNDOCUMENTED — surfaces per-slot validation issues (no children, broken default, child-bone mismatch, transform keys on child). | apps/blender/panels/slots.py:167-168 -> _helpers.py:127-150 -> validation/active_slot.py:15-35 | pending |

#### [ ] BL-SLOT-04 · Slot row button (per slot, label = slot name, LINK_BLEND icon)
- **Intent:** Each row selects/activates that slot so the Active Slot subpanel surfaces its attachments.
- **Code:** apps/blender/panels/slots.py:62-70 -> operators/slot/select.py:36-44
- **Pre:** At least one slot Empty in the scene.
- **Steps:** Open Slots panel > click a slot row.
- **Expect:** That slot Empty becomes the sole selected + active object; the row shows depressed (depress=slot is active); the Active Slot subpanel appears. Missing/non-slot name reports a warning 'slot "<name>" not found' and CANCELLED.
- **Status:** pending

#### [ ] BL-SLOT-07 · Create Slot button (ADD icon)
- **Intent:** Creates a slot Empty; with no mesh selected anchors at the active pose bone, with meshes selected wraps them as attachments under a fresh Empty parented to the active mesh's bone.
- **Code:** apps/blender/panels/slots.py:78 -> operators/slot/create.py:68-114
- **Pre:** context.scene not None. Optionally: Pose Mode with active bone, OR Object Mode with meshes selected.
- **Steps:** Pose Mode w/ active bone: click Create Slot. OR Object Mode: select meshes, click Create Slot.
- **Expect:** A PLAIN_AXES Empty (size 0.1) named '<bone>.slot' (or 'slot') is linked to scene.collection, is_slot=True, parented BONE to active armature/bone (or wraps selected meshes via parent_keep_world centered on geometry center), and becomes sole selection; reports 'created slot ... wrapping N attachment(s)' or 'created empty slot ...'. Redo panel exposes 'Slot name' field.
- **Status:** pending

#### [ ] BL-SLOT-11 · Active Slot subpanel visibility (poll)
- **Intent:** Shown when a slot Empty is the active object; lists the slot's child attachments.
- **Code:** apps/blender/panels/slots.py:96-99
- **Steps:** Make a slot Empty active (e.g. click its row) vs make a non-slot object active.
- **Expect:** Subpanel appears only when active_object is non-None and is_slot_empty; hidden otherwise. Parent Slots panel stays visible regardless.
- **Status:** pending

#### [ ] BL-SLOT-17 · SOLO star toggle (per attachment, SOLO_ON/SOLO_OFF)
- **Intent:** Marks which attachment is visible at scene load (the default visible child).
- **Code:** apps/blender/panels/slots.py:138-148 -> operators/slot/attachment.py:70-104
- **Pre:** Slot Empty active with >=1 MESH child.
- **Steps:** Click the star at the left of an attachment row.
- **Expect:** props.slot_default set to that child's name; row shows filled SOLO_ON (embossed) for the default and SOLO_OFF for others; reports 'slot "<empty>" default = "<name>"'. Non-child name reports warning + CANCELLED. With no explicit default, the first sorted child shows SOLO_ON.
- **Status:** pending

#### [ ] BL-SLOT-20 · Keyframe attachment button (per attachment, KEYFRAME_HLT)
- **Intent:** UNDOCUMENTED — keys the chosen attachment visible from the current frame (the constant-interp slot swap exported as a Godot slot_attachment track).
- **Code:** apps/blender/panels/slots.py:152-157 -> operators/slot/attachment.py:107-152
- **Pre:** Slot Empty active with the named attachment as a MESH child; a frame chosen.
- **Steps:** Move the playhead to a frame > click the keyframe icon on an attachment row.
- **Expect:** Sets empty[PROSCENIO_SLOT_INDEX]=index, inserts a keyframe at current frame, forces all keys on that fcurve to CONSTANT interpolation; reports 'keyed "<name>" (index N) at frame F'. Non-child name reports warning + CANCELLED.
- **Status:** pending

#### [ ] BL-SLOT-21 · Add Selected Mesh button (ADD icon)
- **Intent:** Adds the selected mesh as a new attachment (re-parents the selected mesh into the active slot Empty).
- **Code:** apps/blender/panels/slots.py:159-165 -> operators/slot/attachment.py:40-67
- **Pre:** Slot Empty active AND at least one other MESH object also selected.
- **Steps:** Select a slot Empty (active) plus a mesh > click Add Selected Mesh.
- **Expect:** Each selected MESH is re-parented to the Empty via parent_keep_world (world transform preserved); reports 'added N attachment(s) to slot "<empty>"'. Button is poll-disabled (greyed) when no qualifying mesh is selected.
- **Status:** pending

## Skeleton panel: armature picker, bone list, pose helpers, Quick Armature, IK, authoring camera, pose library

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-SKEL-01 | Skeleton subpanel status badge (Godot-ready) | Custom Godot mark icon shows; hovering surfaces the band tooltip (proscenio.status_info with band='godot_ready'). | UNDOCUMENTED - feature-band badge; Skeleton maps to GODOT_READY. | apps/blender/panels/skeleton.py:83-84 -> _helpers.py:46-69 | pending |
| BL-SKEL-02 | Skeleton subpanel '?' help button | proscenio.help fires with topic='skeleton'; help surface for docs/02-blender-addon/04-skeleton opens. | UNDOCUMENTED - opens the 'skeleton' help topic. | apps/blender/panels/skeleton.py:84 -> _helpers.py:84-86 | pending |
| BL-SKEL-03 | Active Armature picker (PointerProperty dropdown) | scene.proscenio.active_armature set to chosen object (poll=is_armature limits choices to armatures); clearing falls back to QuickRig auto-detect. Armature/Pose subpanels react to the pick. | The project-wide armature picker; single source of truth that bind/automesh/export target. | apps/blender/panels/skeleton.py:94-96 -> scene_props.py:496-509 | pending |
| BL-SKEL-04 | Exports: <name> (picked / first in scene) label | Shows '(picked)' when active_armature set, '(first in scene - no rig picked)' otherwise; EXPORT icon. | UNDOCUMENTED - read-only readout of what the writer will export. | apps/blender/panels/skeleton.py:97-101 | pending |
| BL-SKEL-05 | 'no Armature in scene - use Quick Armature below' warning | INFO-iconned label 'no Armature in scene - use Quick Armature below' appears. | UNDOCUMENTED - presence check telling the user to author a rig. | apps/blender/panels/skeleton.py:103-105 | pending |
| BL-SKEL-06 | 'no rig picked' info box + 'Use existing instead:' label | Boxed INFO label 'no rig picked - skeleton ops will create a new Proscenio.QuickRig' plus 'Use existing instead:' sublabel. | UNDOCUMENTED - warns that skeleton ops will create a new Proscenio.QuickRig. | apps/blender/panels/skeleton.py:106-112 | pending |
| BL-SKEL-08 | Armature subpanel status badge (Godot-ready) + '?' help | Godot mark badge (status_info band='godot_ready'); '?' fires proscenio.help topic='armature' (skeleton#armature). | UNDOCUMENTED - band badge + help topic 'armature'. | apps/blender/panels/skeleton.py:139-140 -> _helpers.py:72-86 | pending |
| BL-SKEL-09 | Armature 'Armature '<name>' - N bone(s)' header label | Label shows the picked armature name and exact bone count. | Read-only count of bones the writer would export for the picked rig. | apps/blender/panels/skeleton.py:148-149 | pending |
| BL-SKEL-10 | Bone list (PROSCENIO_UL_bones template_list) | Each row shows depth-indented bone name (BONE_DATA icon) plus a comma list of 'connected'/'relative' flags where set. | Read-only list of every bone (indented by depth) with connected/relative flags; inspection only, never edits the .proscenio. | apps/blender/panels/skeleton.py:150-158, 25-65 | pending |
| BL-SKEL-12 | Pose Mode subpanel status badge (blender-only) + '?' help | Blender mark badge (band='blender_only'); '?' opens help topic='pose_mode' (skeleton#pose-mode). | UNDOCUMENTED badge; doc says Pose Mode ops are 'blender-only'. Help topic 'pose_mode'. | apps/blender/panels/skeleton.py:172-173 -> _helpers.py:72-86 | pending |
| BL-SKEL-13 | 'enter Pose mode to bake / save poses' info label | INFO label shown and the four pose operators are hidden. | UNDOCUMENTED - gate message when not in Pose mode. | apps/blender/panels/skeleton.py:177-179 | pending |
| BL-SKEL-18 | Quick Armature subpanel status badge (blender-only) + '?' help | Blender mark badge (band='blender_only'); '?' opens help topic='quick_armature' (skeleton#quick-armature). | UNDOCUMENTED badge; Quick Armature is blender-only. Help topic 'quick_armature'. | apps/blender/panels/skeleton.py:207-208 -> _helpers.py:72-86 | pending |
| BL-SKEL-28 | Quick Armature: 3D preview overlay (line, anchor, axis guide, press-point marker) | Orange(connected)/cyan(unparented)/yellow(disconnected)/red(outside-canvas) line head->cursor, anchor circle, dashed parent link (disconnected), faint press-point marker (connected). | UNDOCUMENTED - live GPU preview of the bone being drawn, colour-coded by chord. | apps/blender/operators/armature/_overlay.py:47-141 | pending |
| BL-SKEL-29 | Quick Armature: 'outside canvas' cursor warning tooltip (2D) | Red 'outside canvas' tooltip near cursor; preview turns red; PRESS over overlay ignored, RELEASE cancels in-flight drag. | UNDOCUMENTED - warns when the cursor leaves the invoking viewport canvas. | apps/blender/operators/armature/_overlay.py:144-167 | pending |
| BL-SKEL-30 | Quick Armature: status-bar + viewport-header chord cheatsheet | Both render EVENT_* icon chords: LMB drag=connected/unparented (per default_chain), Shift+drag, Alt+drag=disconnected, X/Z=axis lock, Ctrl=grid snap, Ctrl+Z=undo, Enter=confirm, Esc=exit. | UNDOCUMENTED in 04-skeleton (links to walkthrough cheatsheet) - icon-rich chord vocabulary. | apps/blender/operators/armature/quick_armature.py:739-758,892-917 -> _status_bar.py:23-47 | pending |
| BL-SKEL-31 | Quick Armature F3-redo: 'Lock to Front Orthographic' operator prop | When ON, view snaps to Front Ortho on invoke and restores pre-snap view on exit (unless user orbited mid-modal). When OFF, view is untouched. | Per-invoke override: switch to Front Ortho on invoke and restore on exit (sets the front-ortho lock). | apps/blender/operators/armature/quick_armature.py:95-103,221-222,657-710 | pending |
| BL-SKEL-32 | Quick Armature option: 'Lock to Front Orthographic' (PG default) | scene.proscenio.quick_armature.lock_to_front_ortho persists and seeds the modal's invoke default (note: only overridable per-invoke via the operator prop). | The options box sets the front-ortho lock. | apps/blender/panels/skeleton.py:217 -> scene_props.py:29-37 | pending |
| BL-SKEL-33 | Quick Armature option: 'Default = chain connected' | quick_armature.default_chain persists; modal reads it at invoke to set no-modifier vs Shift chord semantics and the cheatsheet labels. | The options box sets the chain default. | apps/blender/panels/skeleton.py:218 -> scene_props.py:46-56 | pending |
| BL-SKEL-34 | Quick Armature option: 'Bone name prefix' | quick_armature.name_prefix persists; modal sanitizes it (whitespace stripped, empty->'qbone') and names bones '<prefix>.000', '<prefix>.001'. | The options box sets the name prefix. | apps/blender/panels/skeleton.py:219 -> scene_props.py:38-45 | pending |
| BL-SKEL-35 | Quick Armature option: 'Snap increment' | quick_armature.snap_increment persists; modal uses it as the Ctrl-held world-unit grid step. | The options box sets the grid snap. | apps/blender/panels/skeleton.py:220 -> scene_props.py:57-67 | pending |

#### [ ] BL-SKEL-07 · Use existing armature button(s) (one per scene armature)
- **Intent:** UNDOCUMENTED - one-click set the explicit Proscenio target to a named armature.
- **Code:** apps/blender/panels/skeleton.py:113-120 -> skeleton_target.py:36-52
- **Pre:** Armatures exist, picker empty (the 'no rig picked' box).
- **Steps:** Click a per-armature button in the 'Use existing instead' column.
- **Expect:** proscenio.set_active_armature runs; scene.proscenio.active_armature = that object; box disappears, picker now shows it. Empty/missing/non-armature names warn and CANCEL.
- **Status:** pending

#### [ ] BL-SKEL-11 · Bone row click (select_bone_by_name)
- **Intent:** Click a bone to select it in the viewport.
- **Code:** apps/blender/panels/skeleton.py:52-58 -> selection.py:62-93
- **Pre:** Picked armature with bones; row visible.
- **Steps:** Click a bone name in the UIList.
- **Expect:** proscenio.select_bone_by_name runs: only the armature is selected, bones.active set, in Pose mode only that pose bone selected, active_bone_index synced. Missing armature/bone warns + CANCELs.
- **Status:** pending

#### [ ] BL-SKEL-14 · Bake Current Pose button
- **Intent:** Keys every bone at the playhead (those keys do export).
- **Code:** apps/blender/panels/skeleton.py:180 -> pose_library.py:117-147
- **Pre:** Pose mode, active object is the armature.
- **Steps:** Enter Pose mode > click 'Bake Current Pose'.
- **Expect:** loc/rot(quat+euler)/scale keyframes inserted on every pose bone of context.active_object at frame_current; report 'baked pose at frame N for M bone(s)'.
- **Status:** pending

#### [ ] BL-SKEL-15 · Toggle IK button
- **Intent:** Adds or removes a test IK constraint.
- **Code:** apps/blender/panels/skeleton.py:181 -> authoring_ik.py:73-128
- **Pre:** Pose mode; an active pose bone.
- **Steps:** Select a pose bone > click 'Toggle IK' (click again to remove).
- **Expect:** First click: creates a non-deform control bone '<bone>.IK' at the chain tip and a 'Proscenio IK' constraint (chain_count=2) targeting it. Second click removes both (our control bones only).
- **Status:** pending

#### [ ] BL-SKEL-16 · Bake IK to Keyframes button
- **Intent:** UNDOCUMENTED - bakes the active bone's IK chain to keyframes (visual keying) and clears the IK constraint.
- **Code:** apps/blender/panels/skeleton.py:182 -> authoring_ik.py:173-218
- **Pre:** Pose mode; active pose bone carries an IK constraint.
- **Steps:** Select an IK-constrained bone > click 'Bake IK to Keyframes'.
- **Expect:** Chain bones selected; bpy.ops.nla.bake over action/scene range with visual_keying + clear_constraints; report 'baked IK chain ... over frames a-b'. No-IK bone path is poll-gated off.
- **Status:** pending

#### [ ] BL-SKEL-17 · Save Pose to Library button
- **Intent:** Stores the pose as a Blender asset.
- **Code:** apps/blender/panels/skeleton.py:183-187 -> pose_library.py:27-94
- **Pre:** Pose mode; active armature with pose bones; a writable Asset Library configured.
- **Steps:** Enter Pose mode > click 'Save Pose to Library'.
- **Expect:** Wraps poselib.create_pose_asset with name '<action>.<frame>'/'<armature>.<frame>' into the first writable library. Without a writable library: ERROR report + CANCEL.
- **Status:** pending

#### [ ] BL-SKEL-19 · Quick Armature button (modal launch)
- **Intent:** Modal viewport tool that draws bones one press-drag at a time onto the Y=0 picture plane without entering Edit Mode.
- **Code:** apps/blender/panels/skeleton.py:212 -> quick_armature.py:150-231
- **Pre:** Active area is a 3D viewport (operator poll).
- **Steps:** Open Quick Armature subpanel > click 'Quick Armature'.
- **Expect:** Modal starts: ensures/creates Proscenio.QuickRig target, snapshots view+selection, optionally snaps Front Ortho, registers preview + cheatsheet overlays, reports 'modal active'.
- **Status:** pending

#### [ ] BL-SKEL-20 · Quick Armature: LMB press-drag (default chord = connected/unparented)
- **Intent:** Draws a bone head->tail; default no-modifier drag chains onto the previous bone.
- **Code:** apps/blender/operators/armature/quick_armature.py:262-263,364-425,523-589
- **Pre:** Modal active, cursor inside the invoking viewport canvas.
- **Steps:** Press LMB inside viewport, drag, release.
- **Expect:** A bone is created on Y=0 (head snaps to parent tail when connected). Bone shorter than tolerance reports 'bone too short, skipped'. Chord label honours default_chain (ON=connected, OFF=unparented).
- **Status:** pending

#### [ ] BL-SKEL-21 · Quick Armature: Shift+LMB-drag chord
- **Intent:** Hold Shift to chain onto the previous bone (per bl_description) / start a new root (per default_chain ON).
- **Code:** apps/blender/operators/armature/quick_armature.py:380-391, _status_bar.py:40-42, core resolve_press_mode
- **Pre:** Modal active; at least one prior bone for chaining.
- **Steps:** Hold Shift, press-drag-release in the viewport.
- **Expect:** Mode flips relative to default_chain: with default_chain ON, Shift => unparented root; with OFF, Shift => connected chain. Preview tints cyan(unparented).
- **Status:** pending

#### [ ] BL-SKEL-22 · Quick Armature: Alt+LMB-drag chord (disconnected)
- **Intent:** UNDOCUMENTED in 04-skeleton (cheatsheet in walkthrough) - parented but free head.
- **Code:** apps/blender/operators/armature/quick_armature.py:382-391, _status_bar.py:42, _overlay.py:59-62
- **Pre:** Modal active; a prior bone exists.
- **Steps:** Hold Alt, press-drag-release.
- **Expect:** Bone parented to last but head left at press point; dashed parent-link line drawn; preview tinted yellow (disconnected).
- **Status:** pending

#### [ ] BL-SKEL-23 · Quick Armature: X / Z axis-lock keys
- **Intent:** UNDOCUMENTED in 04-skeleton - constrain the drag to the X or Z world axis (Y=0 plane).
- **Code:** apps/blender/operators/armature/quick_armature.py:251-253,266-275,859-872 -> _overlay.py:123-141
- **Pre:** Modal active.
- **Steps:** Press X (then Z) with no modifiers during the modal.
- **Expect:** Axis lock toggles X/Z/off; a red(X)/blue(Z) guideline through the head; tail clamps to that axis; report 'axis lock = X/Z/off'.
- **Status:** pending

#### [ ] BL-SKEL-24 · Quick Armature: Ctrl (grid snap)
- **Intent:** UNDOCUMENTED in 04-skeleton - hold Ctrl to snap head/tail to the snap_increment grid.
- **Code:** apps/blender/operators/armature/quick_armature.py:244,312-313,377-378,467-468
- **Pre:** Modal active.
- **Steps:** Hold Ctrl while moving/pressing/releasing.
- **Expect:** Cursor/head/tail X,Z snap to multiples of snap_increment (default 1.0); preview follows snapped point.
- **Status:** pending

#### [ ] BL-SKEL-25 · Quick Armature: Ctrl+Z undo / Ctrl+Shift+Z redo (in-modal)
- **Intent:** UNDOCUMENTED in 04-skeleton - in-session undo/redo of authored bones.
- **Code:** apps/blender/operators/armature/quick_armature.py:245-250,591-636,851-856
- **Pre:** Modal active; >=1 bone authored this session.
- **Steps:** Author a bone > press Ctrl+Z (then Ctrl+Shift+Z).
- **Expect:** Ctrl+Z removes the last session bone (report 'undone'); Ctrl+Shift+Z recreates it; empty stacks report 'nothing to undo/redo'.
- **Status:** pending

#### [ ] BL-SKEL-26 · Quick Armature: Enter / Numpad-Enter confirm
- **Intent:** UNDOCUMENTED in 04-skeleton - confirm and exit the modal keeping authored bones.
- **Code:** apps/blender/operators/armature/quick_armature.py:239-240,803-822,847-848
- **Pre:** Modal active.
- **Steps:** Press Enter (or Numpad Enter).
- **Expect:** Modal exits FINISHED; overlays/handlers removed, view+selection restored, report 'confirmed (N bone(s) authored)'.
- **Status:** pending

#### [ ] BL-SKEL-27 · Quick Armature: Esc / RMB cancel
- **Intent:** Esc or right-click to exit (per bl_description).
- **Code:** apps/blender/operators/armature/quick_armature.py:236-238,803-822,843-844
- **Pre:** Modal active.
- **Steps:** Press Esc or right-click.
- **Expect:** Modal exits. With no in-flight drag and no bone drawn yet it CANCELs; an empty auto-created QuickRig is swept; view/selection restored; report 'cancelled (N bone(s))'.
- **Status:** pending

#### [ ] BL-SKEL-36 · Preview Camera (create_ortho_camera) - listed in surface, drawn in Helpers panel
- **Intent:** UNDOCUMENTED in 04-skeleton - adds/focuses an ortho camera sized to pixels_per_unit.
- **Code:** apps/blender/operators/armature/authoring_camera.py:16-53; drawn at apps/blender/panels/helpers.py:32
- **Pre:** Any scene with proscenio props.
- **Steps:** (Helpers panel) click 'Preview Camera', or F3 'Preview Camera'.
- **Expect:** Creates/updates Proscenio.PreviewCam at (0,-10,0) facing +Y, type ORTHO, ortho_scale = max(res_x,res_y)/ppu; sets scene.camera, selects it. NOTE: not rendered on the Skeleton surface.
- **Status:** pending

#### [ ] BL-SKEL-37 · Set Bone Mode (set_bone_mode) - listed in surface, belongs to Skinning panel
- **Intent:** UNDOCUMENTED in 04-skeleton - overrides per-bone bind mode SOFT/HARD/CLEAR (a Skinning feature).
- **Code:** apps/blender/operators/skinning/set_bone_mode.py:23-62
- **Pre:** Active object is a MESH (operator poll).
- **Steps:** (Skinning panel bind sub-box) toggle a per-bone mode row.
- **Expect:** Writes obj['proscenio_bone_modes'] JSON; CLEAR drops the override. NOTE: this control does NOT appear on the Skeleton panel - it is INTERNAL and Skinning-owned.
- **Status:** pending

## Mesh Generation panel: automesh one-click + interactive modal + debug pipeline

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-MESH-01 | Parent panel empty-state label: "select a mesh to generate or edit" | Panel body shows only the INFO-icon line "select a mesh to generate or edit"; no props/buttons drawn | UNDOCUMENTED (guard label shown when no MESH is active) | apps/blender/panels/mesh_generation.py:63 | pending |
| BL-MESH-02 | Parent panel sprite-guard labels: "mesh tools are mesh-only (this is a sprite)" + "to rig a sprite, parent it to a bone: Ctrl+P > Bone" | Two INFO lines appear; no automesh props/buttons; subpanels hidden (their poll returns False for sprites) | UNDOCUMENTED (warn-not-hide: a sprite element is a Blender mesh but meshing replaces its quad) | apps/blender/panels/mesh_generation.py:68-69 | pending |
| BL-MESH-03 | Picker readout row ("Picker: <armature>" / "Picker: (none - set in Skeleton panel)") | With armature: ARMATURE_DATA icon + "Picker: <name>"; without: INFO icon + "(none - set in Skeleton panel)" | Parent panel holds the picker readout | apps/blender/panels/mesh_generation.py:72 -> _helpers.py:111 | pending |
| BL-MESH-04 | Interior Mode selector (automesh_interior_mode: Simple / Dense) | Enum value flips; the dense-only fields in Automesh-from-Alpha grey/ungrey; interactive modal stage count changes (5 vs 6) on next run | Parent holds the Interior Mode selector (Simple = sparse, Dense = filled) | apps/blender/panels/mesh_generation.py:74 (prop) / properties/scene_props.py:137 | pending |
| BL-MESH-05 | Mesh Generation panel header status badge | Hover shows band tooltip; click opens the status-legend help popup (via proscenio.status_info -> proscenio.help topic=status_legend) | UNDOCUMENTED (band badge for feature 'mesh_generation' = blender-only) | apps/blender/panels/mesh_generation.py:57 -> _helpers.py:46/83 | pending |
| BL-MESH-06 | Mesh Generation panel header "?" help button | invoke_popup opens the mesh_generation help topic (title/summary/sections + Open online docs) | UNDOCUMENTED (help button; topic 'mesh_generation') | apps/blender/panels/mesh_generation.py:57 -> _helpers.py:84 | pending |
| BL-MESH-07 | Automesh from Alpha subpanel header (status badge + "?" help) | Badge tooltip on hover; "?" opens the automesh_alpha help popup | UNDOCUMENTED (subpanel header badge + help, topic 'automesh_alpha') | apps/blender/panels/mesh_generation.py:93 -> _helpers.py:72 | pending |
| BL-MESH-08 | Trace resolution (automesh_resolution) | Value clamps to 0.01-1.0; feeds downscale_factor on next Automesh from Alpha run (finer/coarser outline) | Image downscale factor; higher traces a finer silhouette but costs more; sets outline fidelity, not vertex count | apps/blender/panels/mesh_generation.py:156 / scene_props.py:80 | pending |
| BL-MESH-09 | Alpha threshold (automesh_alpha_threshold) | Value clamps 0-255; raising it (e.g. 127) drops faint anti-alias edge pixels on next run | UNDOCUMENTED (pixels with alpha strictly above this contribute to the silhouette; default 1) | apps/blender/panels/mesh_generation.py:157 / scene_props.py:95 | pending |
| BL-MESH-10 | Boundary margin (annulus) (automesh_margin_pixels, drawn label "Margin (px)" on operator redo) | Value clamps 0-100; >0 produces dilated-outer + eroded-inner annulus topology on next run | UNDOCUMENTED (source-pixel margin that builds an annulus topology; 0 = single-contour flat fill) | apps/blender/panels/mesh_generation.py:158 / scene_props.py:109 | pending |
| BL-MESH-11 | Contour vertices (automesh_contour_vertices) | Value clamps 8-512; sets target outer-contour vertex count after smoothing+resample (inner uses half) | Use Contour vertices for the outline vertex count | apps/blender/panels/mesh_generation.py:159 / scene_props.py:125 | pending |
| BL-MESH-12 | Interior spacing (automesh_interior_spacing) | World-unit Steiner grid spacing; lower = denser interior; also read by the interactive modal in SIMPLE mode (resample + fold snap radius) | Use Interior spacing for the fill | apps/blender/panels/mesh_generation.py:163 / scene_props.py:161 | pending |
| BL-MESH-13 | Preserve base quad (preserve_base_quad) | ON keeps the proscenio_base_sprite quad corners as loose verts; OFF removes them on next run | UNDOCUMENTED (keep/delete the 4 original quad corner verts after automesh; OFF deletes) | apps/blender/panels/mesh_generation.py:165 / scene_props.py:205 | pending |
| BL-MESH-14 | Preserve weights on regen (preserve_on_regen) - alpha subpanel mirror | ON: weights snapshot + reproject (INFO reports reprojected/auto-seed counts); OFF: weights wiped (legacy) | UNDOCUMENTED (when ON, regen snapshots weights, rebuilds mesh, reprojects via UV anchors) | apps/blender/panels/mesh_generation.py:168 / scene_props.py:287 | pending |
| BL-MESH-15 | Density follows bones (automesh_density_under_bones) - dense-only greyed column | Greyed/inactive in Simple mode; in Dense, ON enables bone-aware interior fill (requires picker armature with deform bones at run) | Dense only, off by default; packs more triangles near the picker's bones | apps/blender/panels/mesh_generation.py:173 (active=is_dense) / scene_props.py:174 | pending |
| BL-MESH-16 | Bone influence radius (automesh_bone_radius) - dense+density-on greyed sub-column | Active only when both conditions hold; feeds bone_density_radius on next run | UNDOCUMENTED (world-unit radius around each bone segment where density subdivision applies) | apps/blender/panels/mesh_generation.py:176 (active=is_dense and density_under_bones) / scene_props.py:184 | pending |
| BL-MESH-17 | Bone density factor (automesh_bone_factor) - dense+density-on greyed sub-column | Active only when both conditions hold; feeds bone_density_factor on next run | UNDOCUMENTED (multiplier for interior density near bones; 1-8) | apps/blender/panels/mesh_generation.py:177 (active=is_dense and density_under_bones) / scene_props.py:194 | pending |
| BL-MESH-20 | Automesh Interactive subpanel header (status badge + "?" help) | Badge tooltip; "?" opens automesh_interactive help popup | UNDOCUMENTED (subpanel header badge + help, topic 'automesh_interactive') | apps/blender/panels/mesh_generation.py:116 -> _helpers.py:72 | pending |
| BL-MESH-21 | Interactive subpanel label "Interactive trace and edit" | Read-only label "Interactive trace and edit" rendered at top of subpanel body | UNDOCUMENTED (static descriptive label) | apps/blender/panels/mesh_generation.py:195 | pending |
| BL-MESH-22 | Loops field (authoring_inner_loop_count, label "Loops") | Value clamps 0-10; controls inner-loop count consumed at the INNER_LOOPS stage of the modal (DENSE only; SIMPLE has no inner-loops stage) | UNDOCUMENTED (concentric inner polylines via erosion; only used by DENSE modal) | apps/blender/panels/mesh_generation.py:198 / scene_props.py:310 | pending |
| BL-MESH-23 | Spacing field (authoring_inner_loop_spacing, label "Spacing") | Value clamps; feeds inner_loop_spacing in _snapshot_params; only affects DENSE inner-loops stage | UNDOCUMENTED (world-unit gap between adjacent inner loops in the modal) | apps/blender/panels/mesh_generation.py:199 / scene_props.py:322 | pending |
| BL-MESH-24 | Cut margin field (authoring_cut_margin, label "Cut margin") | Value clamps; widens/narrows the CDT-hole corridor that cut strokes carve at APPLY | UNDOCUMENTED (corridor width carved by cut strokes; clamped to 0.01 min) | apps/blender/panels/mesh_generation.py:201 / scene_props.py:333 | pending |
| BL-MESH-25 | Preserve weights on regen (preserve_on_regen) - interactive subpanel mirror | Same scene prop as the alpha mirror (BL-MESH-14); APPLY of the modal reprojects weights when ON, wipes when OFF | UNDOCUMENTED (mirror of the regen weight-preserve toggle next to the interactive trigger) | apps/blender/panels/mesh_generation.py:205 / scene_props.py:287 | pending |
| BL-MESH-26 | Author Mesh (interactive) button enabled/greyed state | Enabled only when obj is MESH with data and at least one material TEX_IMAGE node carrying an image; greyed otherwise | Button greys out when active obj is not MESH or has no image texture (UX cue mirroring modal invoke validation) | apps/blender/panels/mesh_generation.py:206-212 / _authoring_button_enabled:217 | pending |
| BL-MESH-27 | Interactive subpanel "select a mesh first" label | INFO line "select a mesh first" below the button | UNDOCUMENTED (fallback INFO label when no mesh active) | apps/blender/panels/mesh_generation.py:213-214 | pending |
| BL-MESH-34 | Modal: live param re-snapshot timer tick | On next timer tick the current stage recomputes + overlay refreshes; flipping Interior Mode mid-modal rebuilds the stage list (snaps off INNER_LOOPS to EDIT_OUTLINE when switching to Simple) | UNDOCUMENTED (panel param edits during the modal recompute the current stage live) | apps/blender/operators/automesh/automesh_authoring.py:348,355 | pending |
| BL-MESH-37 | Modal pen chords: X/Z axis-lock, wheel/0-9 subdivisions, Alt+click delete, Ctrl+Z undo | Axis lock toggles guide line; subdiv count updates tooltip + ghost verts (capped at 20); Alt+click removes hovered stroke; Ctrl+Z drops last pen vert, else last committed stroke | UNDOCUMENTED (pen editing chords surfaced only in the modal statusbar) | apps/blender/operators/automesh/automesh_authoring.py:599-624 / _status_bar.py:36-40 | pending |
| BL-MESH-38 | Modal statusbar chord layout + GPU viewport overlays + cursor tooltip | Statusbar shows "Automesh: N/M Name" + stage chords (next/back/cancel + pen chords on pen stages); viewport draws contour/steiner/preview overlays; cursor tooltip reflects held modifier | UNDOCUMENTED (GPU overlay + bottom-bar chord hints + per-cursor tooltip) | apps/blender/operators/automesh/automesh_authoring.py:1305 / _status_bar.py:19-43 | pending |
| BL-MESH-39 | Debug Pipeline subpanel header (status badge + "?" help) | Subpanel only visible with debug mode on; badge tooltip; "?" opens debug_pipeline help popup | A developer aid, shown only with debug mode on | apps/blender/panels/mesh_generation.py:139 / poll:135 -> debug_mode_enabled | pending |
| BL-MESH-40 | Debug stage enum (debug_stage) | Non-final stages skip the bmesh write and emit a wireframe companion into Proscenio.Debug; INFO reports "automesh DEBUG '<stage>': ..."; Off/Final run the full pipeline | Pick a stage of the trace; the next run leaves a wireframe companion in the Proscenio.Debug collection | apps/blender/panels/mesh_generation.py:244 / scene_props.py:346 / automesh.py:150,308 | pending |

#### [ ] BL-MESH-18 · Automesh from Alpha button (proscenio.automesh_from_alpha)
- **Intent:** A one-shot trace: walks the image alpha contour into an annulus mesh; re-runs preserve the UV-pinned base quad
- **Code:** apps/blender/panels/mesh_generation.py:178 / operators/automesh/automesh.py:62,193
- **Pre:** Active mesh element with a TEX_IMAGE material image of nonzero size
- **Steps:** Set params > click "Automesh from Alpha" (MOD_REMESH icon)
- **Expect:** Mesh rebuilt from alpha contour; INFO report "automesh built: N outer + N inner + N interior = N total, N faces"; REGISTER/UNDO so F3 redo re-iterates params
- **Status:** pending

#### [ ] BL-MESH-19 · Automesh from Alpha - no-image / zero-size / sprite / non-mesh failure paths
- **Intent:** UNDOCUMENTED (preflight guards reporting and cancelling)
- **Code:** apps/blender/operators/automesh/automesh.py:195-209,257-279
- **Pre:** Active mesh with no material image, OR a zero-size image, OR a sprite element
- **Steps:** Run the operator on each failure case (sprite via F3 search since panel hides button)
- **Expect:** Sprite: WARN + CANCELLED; no image: ERROR "no image texture" + CANCELLED; zero size: ERROR + CANCELLED; large image (>4096): WARN but still proceeds
- **Status:** pending

#### [ ] BL-MESH-28 · Author Mesh (interactive) - launch modal (proscenio.automesh_authoring)
- **Intent:** A modal preview of the same trace; advance through stages; nothing written until the final stage commits
- **Code:** apps/blender/panels/mesh_generation.py:208 / operators/automesh/automesh_authoring.py:170,210
- **Pre:** Active mesh element with a TEX_IMAGE image; pose mode not required
- **Steps:** Click "Author Mesh (interactive)"
- **Expect:** Modal starts (RUNNING_MODAL): session captured, GPU overlay registered, timer added, statusbar chord row appears; stage 1/N OUTER overlay drawn
- **Status:** pending

#### [ ] BL-MESH-29 · Modal invoke guards (non-mesh / sprite / no-image)
- **Intent:** UNDOCUMENTED (invoke-time validation; modal also has setup-failure restore)
- **Code:** apps/blender/operators/automesh/automesh_authoring.py:211-229,321-324
- **Pre:** Active object not MESH, OR a sprite element, OR mesh without image
- **Steps:** Invoke on each invalid case
- **Expect:** Non-mesh/no-image: ERROR + CANCELLED; sprite: WARN + CANCELLED; setup exception: ERROR + state restored + CANCELLED
- **Status:** pending

#### [ ] BL-MESH-30 · Modal: ENTER / NUMPAD_ENTER (advance stage)
- **Intent:** Advance through the stages; commit only on the final stage
- **Code:** apps/blender/operators/automesh/automesh_authoring.py:344,987
- **Pre:** Modal running, not on last stage
- **Steps:** Press Enter to step OUTER -> EDIT_OUTLINE -> [INNER_LOOPS] -> EDIT_INTERIOR_POINTS -> PREVIEW_INTERIOR -> APPLY
- **Expect:** Stage label increments (N/M); stage-specific compute runs; overlay refreshes; INFO reports e.g. "<N> outer verts"; on APPLY it commits and finishes
- **Status:** pending

#### [ ] BL-MESH-31 · Modal: BACKSPACE (retreat stage)
- **Intent:** Step back through the stages without committing
- **Code:** apps/blender/operators/automesh/automesh_authoring.py:346,1068
- **Pre:** Modal running, not on first stage
- **Steps:** Advance a few stages > press BACKSPACE
- **Expect:** Stage decrements to previous in the active-mode order; pen stages reset draw state; overlay refreshes; INFO stage-entry report
- **Status:** pending

#### [ ] BL-MESH-32 · Modal: ESC (cancel session)
- **Intent:** ESC cancels; nothing is written
- **Code:** apps/blender/operators/automesh/automesh_authoring.py:342 / _finish:1264
- **Pre:** Modal running at any stage
- **Steps:** Press ESC
- **Expect:** Overlay unregistered, timer removed, statusbar removed, captured session restored; INFO "Authoring modal restored"; CANCELLED (no geometry change)
- **Status:** pending

#### [ ] BL-MESH-33 · Modal: APPLY commit (final stage ENTER)
- **Intent:** Commit the final mesh after confirming the last stage
- **Code:** apps/blender/operators/automesh/automesh_authoring.py:1015-1038
- **Pre:** Modal on PREVIEW_INTERIOR; ENTER to APPLY
- **Steps:** Reach last-but-one stage > press ENTER
- **Expect:** apply_mesh writes geometry; INFO "Authoring applied: N verts, N faces"; dropped-vert WARN if any stroke verts fell outside; on CDT ValueError reports error and stays (no commit)
- **Status:** pending

#### [ ] BL-MESH-35 · Modal Stage 2 (EDIT_OUTLINE) toggle-pen: Shift-tap extend / Ctrl-tap cut
- **Intent:** Cut / extend the outline as a modal stage
- **Code:** apps/blender/operators/automesh/automesh_authoring.py:365,458,486
- **Pre:** Modal on EDIT_OUTLINE stage
- **Steps:** Tap Shift (enter extend-pen) or tap Ctrl (cut-pen) > LMB place verts / drag free-draw > RMB or Enter to finish
- **Expect:** Tooltip shows "Extend/Cut pen ..."; committed extend reshapes the spliced outer preview; committed cut reports running "N cut(s)" (corridor carved only at APPLY)
- **Status:** pending

#### [ ] BL-MESH-36 · Modal Stage 4 (EDIT_INTERIOR_POINTS) toggle-pen: click point / Shift-fold / Ctrl-cut
- **Intent:** Place interior points as a modal stage
- **Code:** apps/blender/operators/automesh/automesh_authoring.py:452,539,933
- **Pre:** Modal on EDIT_INTERIOR_POINTS stage
- **Steps:** Plain LMB click = drop a Steiner point; tap Shift = fold-pen; tap Ctrl = cut-pen; draw + finish
- **Expect:** Points/strokes persist via write_user_strokes; tooltip flips warn-red when a gesture aims outside the silhouette; strokes feed the triangulation preview / Steiner cloud
- **Status:** pending

#### [ ] BL-MESH-41 · Clear Debug Companions button (proscenio.clear_automesh_debug)
- **Intent:** Clear Debug Companions removes the wireframe companions
- **Code:** apps/blender/panels/mesh_generation.py:245 / automesh.py:339,356
- **Pre:** Debug Pipeline subpanel open; companions exist in Proscenio.Debug for the active sprite
- **Steps:** Click "Clear Debug Companions" (TRASH icon)
- **Expect:** All debug companions for the active object removed; INFO "removed N debug companion(s) for '<name>'"; REGISTER/UNDO
- **Status:** pending

## Weight Paint panel: five bind modes, Edit Weights modal, brush preset, copy weights, sidecar IO, snapshot restore

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-WPAINT-01 | Mesh-only hint label ('select a mesh element (Weight Paint is mesh-only)') | Panel body shows only the INFO-icon label 'select a mesh element (Weight Paint is mesh-only)'; all subpanels (Bind/Edit/Snapshot/Transfer) are absent (their poll returns False). | The panel is mesh-only - it warns when the active element is a sprite. | apps/blender/panels/weight_paint.py:51 | pending |
| BL-WPAINT-02 | Picker readout row ('Picker: <armature>' / '(none - set in Skeleton panel)') | With picker set: 'Picker: <armature name>' with ARMATURE_DATA icon. Without: 'Picker: (none - set in Skeleton panel)' with INFO icon. | Surfaces the picker readout (shared affordance with Mesh Generation). | apps/blender/panels/weight_paint.py:53 -> _helpers.py:111 | pending |
| BL-WPAINT-03 | Weight Paint header status badge | Status-band icon shows; hovering surfaces the band-specific tooltip via proscenio.status_info; clicking is emboss=False info-only. | UNDOCUMENTED | apps/blender/panels/weight_paint.py:46 -> _helpers.py:83 | pending |
| BL-WPAINT-04 | Weight Paint header '?' help button | proscenio.help fires with topic 'weight_paint' (resolves to docs anchor weight-paint). | UNDOCUMENTED (help affordance maps to weight-paint doc page). | apps/blender/panels/weight_paint.py:46 -> _helpers.py:84 | pending |
| BL-WPAINT-05 | Bind subpanel header status badge + '?' help button | proscenio.help fires with topic 'bind' (anchor weight-paint#bind); status badge surfaces band tooltip. | UNDOCUMENTED (per-subpanel help/status affordance). | apps/blender/panels/weight_paint.py:72 -> _helpers.py:83-85 | pending |
| BL-WPAINT-06 | Mode dropdown (Bind mode enum: Bone Heat / Proximity / Envelope / Single nearest / Empty) | Five entries selectable; selection persists on scene.proscenio.skinning.bind_init_mode and seeds bind_mesh.invoke(); changing it also toggles whether the per-bone override box draws rows vs the Bone-Heat hint. | Mode picks the bind algorithm; Bone Heat is native default, the other four are F3-redo fallbacks. | apps/blender/panels/weight_paint.py:174 (prop) ; properties/scene_props.py:218 (enum def) | pending |
| BL-WPAINT-07 | Target label ('Target: <picker>' / 'Target: (no picker armature)') | ARMATURE_DATA-icon label reads 'Target: <picker name>' or 'Target: (no picker armature)'. | Shows the target armature the mesh will bind to. | apps/blender/panels/weight_paint.py:176 | pending |
| BL-WPAINT-08 | Per-bone overrides box header label ('Per-bone Soft/Hard overrides:') | A box appears titled 'Per-bone Soft/Hard overrides:'. With 0 bones the box does not draw (early return at line 211). | Per-bone Soft/Hard overrides a single bone's falloff; no override uses the mode default family. | apps/blender/panels/weight_paint.py:213 | pending |
| BL-WPAINT-09 | Override box Bone-Heat hint ('applies only to the planar modes - Bone Heat ignores these') | Box shows only the INFO hint 'applies only to the planar modes - Bone Heat ignores these'; NO per-bone Soft/Hard/Clear rows are drawn. | A bone with no override uses the mode default; overrides apply only to planar modes (Bone Heat returns before override pass). | apps/blender/panels/weight_paint.py:215 ; bone_modes.py:59 overrides_apply_under_bind_mode | pending |
| BL-WPAINT-15 | Edit Weights subpanel header status badge + '?' help button | proscenio.help topic 'edit_weights' (anchor weight-paint#edit-weights). | UNDOCUMENTED (per-subpanel affordance). | apps/blender/panels/weight_paint.py:97 -> _helpers.py:83-85 | pending |
| BL-WPAINT-16 | Active group label ('Active group: <name>') | Reads 'Active group: <vg name>' or '(none)' (no groups) or '(no mesh)'. | UNDOCUMENTED (shows the vertex group the modal will paint). | apps/blender/panels/weight_paint.py:262 ; _active_group_label:282 | pending |
| BL-WPAINT-20 | Edit Weights status-bar overlay (ESC=exit / mirror = picker.proscenio_mirror_x) | Status bar shows BRUSHES_ALL 'Edit Weights:', EVENT_ESC 'exit', MOD_MIRROR 'mirror = picker.proscenio_mirror_x'. | UNDOCUMENTED (modal status-bar hint chips). | apps/blender/operators/skinning/edit_weights.py:228 _draw_statusbar_edit_weights | pending |
| BL-WPAINT-21 | 'bind first to enable' hint label | INFO-icon label 'bind first to enable' is shown beneath the (disabled) Edit Weights button. | Bind first - the Edit Weights button is disabled until then. | apps/blender/panels/weight_paint.py:272-273 | pending |
| BL-WPAINT-22 | 'Brush curve preset:' label | Label 'Brush curve preset:' shown above the four preset buttons (drawn even when mesh unbound). | The brush-curve presets shape the brush for common 2D tasks. | apps/blender/panels/weight_paint.py:275 | pending |
| BL-WPAINT-27 | Viewport display box - 'Weight Opacity' slider | Drives space overlay.weight_paint_mode_opacity; weight color fades over the mesh. (Opacity 0 not fully invisible - see hint.) | UNDOCUMENTED (native overlay opacity so the texture shows through while painting). | apps/blender/panels/weight_paint.py:317 | pending |
| BL-WPAINT-28 | Viewport display box - 'Zero Weights' dropdown | Drives tool_settings.vertex_group_user; zero-weight verts shaded per the chosen mode. | UNDOCUMENTED (native Zero Weights display - tool_settings.vertex_group_user). | apps/blender/panels/weight_paint.py:320 | pending |
| BL-WPAINT-29 | Viewport display hint label ('opacity 0 is not fully invisible (Blender 145603)') | INFO-icon caveat label about Blender issue 145603 is shown. | UNDOCUMENTED (upstream-bug caveat). | apps/blender/panels/weight_paint.py:321 | pending |
| BL-WPAINT-30 | Snapshot subpanel header status badge + '?' help button | proscenio.help topic 'snapshot' (anchor weight-paint#snapshot). | UNDOCUMENTED (per-subpanel affordance). | apps/blender/panels/weight_paint.py:121 -> _helpers.py:83-85 | pending |
| BL-WPAINT-31 | 'Preserve weights on regen' checkbox | Toggles scene.proscenio.skinning.preserve_on_regen (default ON); consumed by the Automesh-from-Alpha hook on the next regen, not by this panel directly. | Snapshots weights by UV before an automesh re-run and reprojects them; off = the regen wipes paint. | apps/blender/panels/weight_paint.py:337 ; scene_props.py:287 | pending |
| BL-WPAINT-32 | 'Show provenance overlay' checkbox | Toggles scene.proscenio.skinning.show_provenance_overlay. Outside the modal nothing is drawn - no draw handler is added/removed by this toggle (only edit_weights.invoke registers/forces the overlay). See finding. | UNDOCUMENTED on this surface (doc mentions a provenance overlay only inside the Edit Weights modal). | apps/blender/panels/weight_paint.py:338 ; scene_props.py:299 | pending |
| BL-WPAINT-33 | Provenance counts pill ('N paint / N seed / N reprojected') or 'no snapshot' hint | Before bind: INFO 'no snapshot (run Bind first)'. After: 'X paint / Y seed / Z reprojected' counted from sidecar entries by provenance. | The weight snapshot stores per-vertex weights + provenance; counts recomputed live from the JSON on the mesh. | apps/blender/panels/weight_paint.py:339-349 ; _sidecar_counts:363 | pending |
| BL-WPAINT-37 | Weight Transfer subpanel header status badge + '?' help button | proscenio.help topic 'weight_transfer' (anchor weight-paint#weight-transfer). | UNDOCUMENTED (per-subpanel affordance). | apps/blender/panels/weight_paint.py:144 -> _helpers.py:83-85 | pending |
| BL-WPAINT-38 | 'Max Distance' field (Weight Transfer) | Edits scene.proscenio.skinning.weight_transfer_max_distance (default 0.5, min 0); the value seeds the Copy operator on click. | Target verts beyond the Max Distance get no weights (doc lists it as F3 redo). | apps/blender/panels/weight_paint.py:150 ; scene_props.py:276 | pending |

#### [ ] BL-WPAINT-10 · Per-bone 'Soft' toggle button (one per bone)
- **Intent:** Soft shares weight smoothly with neighbours (cloth, hair).
- **Code:** apps/blender/panels/weight_paint.py:225 -> operators/skinning/set_bone_mode.py:52
- **Pre:** Picker with bones; Mode = a planar mode (Proximity/Envelope/Single nearest/Empty).
- **Steps:** Set Mode=Proximity > click 'Soft' next to a bone
- **Expect:** Writes obj['proscenio_bone_modes'][bone]='SOFT'; button shows depressed (depress=current=='SOFT'); the row's Clear (X) becomes enabled.
- **Status:** pending

#### [ ] BL-WPAINT-11 · Per-bone 'Hard' toggle button (one per bone)
- **Intent:** Hard gives a crisp single-nearest boundary (finger joints).
- **Code:** apps/blender/panels/weight_paint.py:232 -> operators/skinning/set_bone_mode.py:52
- **Pre:** Picker with bones; Mode = planar mode.
- **Steps:** Click 'Hard' next to a bone
- **Expect:** Writes obj['proscenio_bone_modes'][bone]='HARD'; Hard depresses, Soft un-depresses, Clear (X) enabled.
- **Status:** pending

#### [ ] BL-WPAINT-12 · Per-bone Clear (X) button (one per bone)
- **Intent:** UNDOCUMENTED (drops a bone override back to the bind-mode default).
- **Code:** apps/blender/panels/weight_paint.py:241 -> operators/skinning/set_bone_mode.py:56 clear_bone_mode
- **Pre:** Picker with bones; Mode planar; the bone HAS an override (else X is disabled).
- **Steps:** After setting Soft/Hard on a bone, click the X on that row
- **Expect:** Override removed from obj['proscenio_bone_modes']; Soft+Hard both un-depress; X disables (clear_sub.enabled = current != '').
- **Status:** pending

#### [ ] BL-WPAINT-13 · Bind to Picker Armature button
- **Intent:** Builds the vertex weights that deform the mesh using the selected Mode; writes weights/sidecar exported to the Polygon2D.
- **Code:** apps/blender/panels/weight_paint.py:186 -> operators/skinning/bind_mesh.py:176 execute
- **Pre:** Mesh element active. Row disabled when no picker (row.enabled = picker is not None).
- **Steps:** With picker set and a mesh selected, click 'Bind to Picker Armature'
- **Expect:** Runs 5 pre-flight diagnoses; on success creates vertex groups + writes proscenio_weight_sidecar; status reports 'bound N mesh(es)' and per-mesh vert/bone/orphan counts. With no picker the button is greyed out.
- **Status:** pending

#### [ ] BL-WPAINT-14 · Bind F3/F9 redo panel (bind_init_mode + falloff_power + max_distance)
- **Intent:** Proximity/Envelope/Single-nearest/Empty are F3-redo fallbacks; falloff_power & max_distance tune Proximity.
- **Code:** apps/blender/operators/skinning/bind_mesh.py:49-94 (props), 104 invoke
- **Pre:** Just ran Bind.
- **Steps:** After Bind, press F9 (or open redo panel) > change Bind mode / Falloff power / Max distance
- **Expect:** Redo panel exposes the enum + falloff_power (0.5-8.0) + max_distance (-1=adaptive); re-running re-binds with the new values. invoke() seeds from scene skinning so panel + F3 agree.
- **Status:** pending

#### [ ] BL-WPAINT-17 · Edit Weights button (modal entry)
- **Intent:** Enters a modal weight-paint session on the active group with a provenance overlay; disabled until Bind.
- **Code:** apps/blender/panels/weight_paint.py:265 -> operators/skinning/edit_weights.py:69 invoke
- **Pre:** Mesh active; ENABLED only when picker set AND >=1 vertex group AND sidecar present (_edit_weights_button_enabled).
- **Steps:** After binding, click 'Edit Weights'
- **Expect:** Enters WEIGHT_PAINT mode, applies 2D paint preset (Front Faces off, mirror from picker), shows provenance overlay (cyan/white/gray), adds status-bar hints. Disabled (greyed) before bind.
- **Status:** pending

#### [ ] BL-WPAINT-18 · Edit Weights modal - LEFTMOUSE paint stroke (per-stroke provenance flip)
- **Intent:** Tags brushed verts as user_paint in the sidecar via per-stroke diff.
- **Code:** apps/blender/operators/skinning/edit_weights.py:114-127 modal
- **Pre:** Inside Edit Weights modal.
- **Steps:** Press+drag LMB to paint a stroke, release
- **Expect:** On press snapshots active VG; on release flip_touched_after_stroke marks changed verts user_paint (white) and triggers area redraw; provenance overlay updates.
- **Status:** pending

#### [ ] BL-WPAINT-19 · Edit Weights modal - ESC exit / cancel path
- **Intent:** ESC hard-exits and restores brush + bone visibility + mode + selection.
- **Code:** apps/blender/operators/skinning/edit_weights.py:112,133 _finish(cancel=True)
- **Pre:** Inside Edit Weights modal.
- **Steps:** Press ESC during the modal
- **Expect:** Pushes a single 'Edit Weights' undo, unregisters overlay handler, removes status bar, restores prior session (mode/preset/bone visibility/selection/overlay flag); reports 'Edit Weights modal restored'. Ctrl+Z then reverts the whole session.
- **Status:** pending

#### [ ] BL-WPAINT-23 · Brush preset 'Hard Edge' button
- **Intent:** Hard Edge brush-curve preset for common 2D tasks.
- **Code:** apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88 execute
- **Pre:** An active weight-paint brush exists (tool_settings.weight_paint.brush) - else operator poll fails.
- **Steps:** Enter weight paint (or ensure a WP brush exists) > click 'Hard Edge'
- **Expect:** brush.curve_distance_falloff forced to CUSTOM, falloff curve set to [(0,1),(0.95,1),(1,0)]; reports INFO 'Brush preset applied: Hard Edge'. If brush has no falloff curve, WARNING + CANCELLED.
- **Status:** pending

#### [ ] BL-WPAINT-24 · Brush preset 'Soft Falloff' button
- **Intent:** Soft Falloff brush-curve preset.
- **Code:** apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88
- **Pre:** Active weight-paint brush exists.
- **Steps:** Click 'Soft Falloff'
- **Expect:** Curve set to linear [(0,1),(1,0)]; INFO 'Brush preset applied: Soft Falloff'.
- **Status:** pending

#### [ ] BL-WPAINT-25 · Brush preset 'Crease' button
- **Intent:** Crease brush-curve preset.
- **Code:** apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88
- **Pre:** Active weight-paint brush exists.
- **Steps:** Click 'Crease'
- **Expect:** Curve set to [(0,1),(0.2,0.7),(0.5,0),(1,0)]; INFO 'Brush preset applied: Crease'.
- **Status:** pending

#### [ ] BL-WPAINT-26 · Brush preset 'Smooth Blend' button
- **Intent:** Smooth Blend brush-curve preset.
- **Code:** apps/blender/panels/weight_paint.py:278 -> operators/skinning/brush_preset.py:88
- **Pre:** Active weight-paint brush exists.
- **Steps:** Click 'Smooth Blend'
- **Expect:** Curve set to [(0,1),(0.3,0.85),(0.7,0.15),(1,0)]; INFO 'Brush preset applied: Smooth Blend'. Note: in OBJECT mode with no WP brush, poll fails and the button is greyed.
- **Status:** pending

#### [ ] BL-WPAINT-34 · 'Reset to Last Saved Weights' button
- **Intent:** Reverts the live weights to that snapshot; does NOT trigger automesh regen; topology mismatch cancels.
- **Code:** apps/blender/panels/weight_paint.py:352 -> operators/skinning/restore_weight_snapshot.py:49
- **Pre:** Mesh active; row disabled when counts is None (no sidecar).
- **Steps:** After binding/painting, click 'Reset to Last Saved Weights'
- **Expect:** Re-applies the sidecar to live vertex groups; INFO 'restored N verts (M groups)'. If topology hash differs: ERROR 'topology changed since last snapshot...'; if sidecar empty/corrupt: ERROR re-bind hint. Disabled with no snapshot.
- **Status:** pending

#### [ ] BL-WPAINT-35 · 'Export Snapshot' button (file save dialog)
- **Intent:** Exports the weight snapshot to a JSON file (version-control / move between files).
- **Code:** apps/blender/panels/weight_paint.py:359 -> operators/skinning/sidecar_io.py:50,66
- **Pre:** Mesh active WITH a sidecar (operator poll requires obj.get(sidecar) not None).
- **Steps:** After bind, click 'Export Snapshot' > choose a .json path > confirm
- **Expect:** File save dialog (.json filter); writes the sidecar JSON payload to disk; INFO 'Sidecar exported to <path>'. On unbound mesh the operator poll fails so click is a no-op.
- **Status:** pending

#### [ ] BL-WPAINT-36 · 'Import Snapshot' button (file open dialog)
- **Intent:** Imports a snapshot; loads it onto the mesh and applies to live weights when topology matches; run Reset to push otherwise.
- **Code:** apps/blender/panels/weight_paint.py:360 -> operators/skinning/sidecar_io.py:84,101
- **Pre:** Mesh element active (import poll only needs a mesh).
- **Steps:** Click 'Import Snapshot' > pick a .json > confirm
- **Expect:** Reads file, validates JSON, stores onto obj[proscenio_weight_sidecar]; if topology matches: applies to live weights + INFO 'imported and applied to N verts'; else INFO 'imported (stored only - topology differs...)'. Bad file/JSON: WARNING + CANCELLED.
- **Status:** pending

#### [ ] BL-WPAINT-39 · Copy weights button ('Copy Weights to Selected', DUPLICATE icon)
- **Intent:** Copies weights from the active mesh to every other selected mesh by nearest world-space vertex.
- **Code:** apps/blender/panels/weight_paint.py:151 -> operators/skinning/copy_weights_to_selected.py:41
- **Pre:** Active mesh + >=1 OTHER selected mesh (operator poll); seeds max_distance from the panel field.
- **Steps:** Select target meshes then the source mesh (active) > click the copy button
- **Expect:** Transfers per-vert weights to each target by nearest source vert within Max Distance, creating vertex groups as needed; reports INFO/WARNING coverage summary. F9 redo exposes max_distance. Note: the panel button has no text label - only the DUPLICATE icon.
- **Status:** pending

#### [ ] BL-WPAINT-40 · Copy weights F9 redo (max_distance)
- **Intent:** Max Distance is an F3/F9 redo for a one-off tweak.
- **Code:** apps/blender/operators/skinning/copy_weights_to_selected.py:25 max_distance prop
- **Pre:** Just ran Copy Weights.
- **Steps:** After copy, press F9 > change Max Distance
- **Expect:** Redo panel exposes Max Distance (default 0.5, min 0, soft_max 5.0); re-runs the transfer with the new radius.
- **Status:** pending

## Animation panel (read-only action summary)

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-ANIM-01 | Animation subpanel foldout (header) | Panel expands; shows either the empty-state label or the action UIList + count label. Starts collapsed on a fresh session (bl_options DEFAULT_CLOSED). | Read-only summary of every Action in the file that the writer emits as Godot AnimationPlayer entries. | apps/blender/panels/animation.py:39-67 | pending |
| BL-ANIM-02 | Status badge icon (header, right side) | Hover shows the godot-ready band tooltip; the icon is the custom Godot preview (falls back to built-in badge icon if preview load failed/headless). Click opens the status-legend help popup (proscenio.status_info -> proscenio.help topic 'status_legend'). | UNDOCUMENTED (doc page does not describe the header status badge); feature_status maps 'animation' -> GODOT_READY so it should show the Godot mark and the godot-ready tooltip. | apps/blender/panels/_helpers.py:46-69 (draw via animation.py:50-51) | pending |
| BL-ANIM-04 | 'no actions to export' empty-state label | Single row 'no actions to export' with INFO icon; the UIList and count label are NOT drawn (early return). | UNDOCUMENTED as a specific label; conveys the read-only summary is empty when no Actions exist. | apps/blender/panels/animation.py:56-58 | pending |
| BL-ANIM-05 | Actions UIList (PROSCENIO_UL_actions / template_list) | One row per action; visible row count = min(max(len,2),6) (min 2 rows shown even with 1 action, capped at 6). Clicking the row body sets active_action_index; the standard template_list selection highlight follows. | Lists every bpy.data.actions entry the writer would emit; selection is tracked in scene.proscenio.active_action_index. | apps/blender/panels/animation.py:59-67 (template_list), 12-36 (UIList) | pending |
| BL-ANIM-10 | Per-row frame-range label '[start-end]' | Shows '[<start>-<end>]' with both ends rounded to whole frames (%.0f). For an empty/never-keyed action Blender reports frame_range (0,0) -> '[0-0]' (verify it does not raise). | UNDOCUMENTED; read-only display of the action's frame_range as integer-rounded start-end. | apps/blender/panels/animation.py:27,36 | pending |
| BL-ANIM-11 | 'N action(s) total' count label | Label 'N action(s) total' with INFO icon where N == len(bpy.data.actions), including orphan/zero-user actions (it counts ALL datablocks, not just exportable ones). | UNDOCUMENTED; read-only count of bpy.data.actions. | apps/blender/panels/animation.py:68 | pending |

#### [ ] BL-ANIM-03 · Help '?' button (header)
- **Intent:** UNDOCUMENTED (doc page never mentions a help button); opens the in-panel help popup for topic 'animation'.
- **Code:** apps/blender/panels/_helpers.py:84-85 (op), apps/blender/operators/help_dispatch.py:50-97 (handler)
- **Pre:** Animation subpanel header visible.
- **Steps:** Click the '?' (QUESTION icon) in the Animation header.
- **Expect:** A 480px-wide popup opens titled 'Animation' with summary 'List of actions the writer would emit as Godot AnimationLibrary entries.' plus sections and any See-also/doc-url buttons (help_topics.py:184-198). Topic id 'animation' resolves (not 'unknown help topic').
- **Status:** pending

#### [ ] BL-ANIM-06 · Action name row button (per-row, emboss=False)
- **Intent:** UNDOCUMENTED (doc says panel is read-only; the row is in fact a click-to-assign operator). Assigns the row's action to the first scene armature so the timeline plays it.
- **Code:** apps/blender/panels/animation.py:28-36 (draw), apps/blender/operators/selection.py:96-132 (handler)
- **Pre:** At least one Action and at least one ARMATURE object in the scene.
- **Steps:** Expand Animation subpanel > click an action's name text (the ACTION-icon label, drawn emboss=False so it looks like a plain label).
- **Expect:** The clicked action is assigned to armatures[0].animation_data.action (animation_data_create() called if missing); active_action_index syncs to that row; scrubbing the timeline now plays the action. Undoable (REGISTER|UNDO).
- **Status:** pending

#### [ ] BL-ANIM-07 · Action row button - multiple-armature path
- **Intent:** UNDOCUMENTED; when >1 armature exists it warns and assigns to the first armature only ('mirror the writer's heuristic').
- **Code:** apps/blender/operators/selection.py:117-127
- **Pre:** At least one Action and >=2 ARMATURE objects in the scene; report log level at 'info' or higher.
- **Steps:** Create 2+ armatures > click an action row in the Animation panel.
- **Expect:** A WARNING report appears: 'Proscenio: N armatures in scene - assigning to <name>'; the action is assigned to armatures[0] only. (Suppressed silently if log level = 'errors' - see findings.)
- **Status:** pending

#### [ ] BL-ANIM-08 · Action row button - no-armature failure path
- **Intent:** UNDOCUMENTED; cancels with a warning when no armature exists to receive the action.
- **Code:** apps/blender/operators/selection.py:117-120
- **Pre:** At least one Action but ZERO armature objects in the scene; report log level 'info'+.
- **Steps:** Delete all armatures > click an action row.
- **Expect:** Operator returns CANCELLED; WARNING 'Proscenio: no armature in scene to receive the action'; no datablock changes. (Silent if log level = 'errors'.)
- **Status:** pending

#### [ ] BL-ANIM-09 · Action row button - stale/renamed action path
- **Intent:** UNDOCUMENTED; cancels with a warning when the action_name no longer resolves in bpy.data.actions.
- **Code:** apps/blender/operators/selection.py:113-116
- **Pre:** An action exists; another user/script could rename or delete it between draw and click.
- **Steps:** Difficult to trigger manually - rename/delete the action via Python console after the panel drew but before clicking, then click the (now stale) row.
- **Expect:** Operator returns CANCELLED; WARNING 'Proscenio: action '<name>' not found'; no assignment.
- **Status:** pending

## Atlas panel: pack / unpack / apply

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-ATLAS-01 | Atlas subpanel foldout header | Subpanel expands showing atlas readout label(s), pixels-per-unit readout, and the 'Atlas packer' box. bl_order=8 places it 8th. | Collapsible subpanel that surfaces atlas state + packer controls. | apps/blender/panels/atlas.py:16 | pending |
| BL-ATLAS-02 | Status badge icon (header_preset) | Hover shows band tooltip (atlas feature = GODOT_READY band); click opens the status-legend help dialog via proscenio.status_info -> proscenio.help topic='status_legend'. | UNDOCUMENTED | apps/blender/panels/atlas.py:28 -> _helpers.py:46 _draw_status_button | pending |
| BL-ATLAS-03 | Help '?' button (QUESTION icon) | proscenio.help popup opens titled 'Atlas' with sections Pack Atlas / Apply Packed Atlas / Unpack Atlas and a docs link. | Opens the in-panel Atlas help dialog (topic 'atlas'). | apps/blender/panels/atlas.py:28 -> _helpers.py:84 draw_subpanel_header | pending |
| BL-ATLAS-04 | Atlas readout label: 'no atlas linked in materials' | Label reads 'no atlas linked in materials' with INFO icon. | UNDOCUMENTED | apps/blender/panels/atlas.py:33-34 | pending |
| BL-ATLAS-05 | Atlas readout label: 'packed atlas: <name>' | Label reads 'packed atlas: <stem>.atlas.png' with IMAGE icon (is_packed_atlas branch). | UNDOCUMENTED | apps/blender/panels/atlas.py:35-36 | pending |
| BL-ATLAS-06 | Atlas readout label: 'source image: <name>' / '<name> (unsaved)' | Label reads 'source image: <basename>' with IMAGE_DATA icon; if the image has no filepath it reads '<image.name> (unsaved)'. | UNDOCUMENTED | apps/blender/panels/atlas.py:37-38, 99 | pending |
| BL-ATLAS-07 | Pixels-per-unit readout label | Read-only label echoes scene_props.pixels_per_unit formatted with %g; editable field lives in the Export subpanel, not here. | UNDOCUMENTED | apps/blender/panels/atlas.py:39-42 | pending |
| BL-ATLAS-08 | 'Atlas packer' box header label | A bordered box labeled 'Atlas packer' contains the three config fields, separator, and Pack/Apply/Unpack buttons. | UNDOCUMENTED (box grouping label) | apps/blender/panels/atlas.py:51-52 | pending |
| BL-ATLAS-09 | Pack padding (pack_padding_px) field | Value clamps to 0..64; consumed by Pack Atlas as int padding around each sprite slot in the composed PNG + manifest. | UNDOCUMENTED | apps/blender/panels/atlas.py:54 (prop) -> properties/scene_props.py:447 | pending |
| BL-ATLAS-10 | Pack max size (pack_max_size) field | Value clamps to 64..8192; Pack fails with 'pack failed - N sprite(s) do not fit in NxN px atlas.' when sprites exceed this cap. | UNDOCUMENTED | apps/blender/panels/atlas.py:55 (prop) -> properties/scene_props.py:454 | pending |
| BL-ATLAS-11 | Power-of-two atlas (pack_pot) checkbox | When on, the resulting atlas_w/atlas_h are rounded up to the next power of two; off by default. | UNDOCUMENTED | apps/blender/panels/atlas.py:56 (prop) -> properties/scene_props.py:461 | pending |
| BL-ATLAS-16 | 'run Pack Atlas first' disabled hint row | Where Apply would be, a disabled (greyed) row reads 'run Pack Atlas first' with INFO icon; no Apply button drawn. | UNDOCUMENTED (gates Apply until a manifest exists). | apps/blender/panels/atlas.py:61-64 | pending |

#### [ ] BL-ATLAS-12 · Pack Atlas button
- **Intent:** Walks every sprite with a texture, runs MaxRects packing, writes <blend>.atlas.png + .atlas.json; non-destructive (UVs/materials untouched).
- **Code:** apps/blender/panels/atlas.py:58 -> operators/atlas_pack/pack.py:36
- **Pre:** Blend saved to disk (bpy.data.filepath set); Object Mode; at least one MESH with a source image and not exclude_from_atlas
- **Steps:** Save .blend > Object Mode > select/have sprite meshes with source images > click 'Pack Atlas'.
- **Expect:** Writes <stem>.atlas.png + <stem>.atlas.json next to the .blend; INFO report 'packed N sprite(s) into WxH px atlas -> file.png'; UVs and materials unchanged. Apply button then appears.
- **Status:** pending

#### [ ] BL-ATLAS-13 · Pack Atlas - disabled in Edit Mode / unsaved (poll)
- **Intent:** Pack requires Object Mode (Edit Mode hides UV data behind BMesh) and a saved blend.
- **Code:** apps/blender/operators/atlas_pack/pack.py:48-51
- **Pre:** Unsaved file OR Edit Mode
- **Steps:** On a never-saved file, or in Edit Mode, hover/observe the 'Pack Atlas' button.
- **Expect:** Button greyed out (poll returns False when bpy.data.filepath empty or context.mode != 'OBJECT').
- **Status:** pending

#### [ ] BL-ATLAS-14 · Pack Atlas - no eligible sprites path
- **Intent:** Pack walks sprites with a texture; warns when none found.
- **Code:** apps/blender/operators/atlas_pack/pack.py:68-72
- **Pre:** Saved file, Object Mode, but no MESH has a source image (or all are exclude_from_atlas)
- **Steps:** Remove/ exclude all textured meshes > click 'Pack Atlas'.
- **Expect:** WARN report 'no sprite meshes with source images found'; operation CANCELLED; no PNG/JSON written.
- **Status:** pending

#### [ ] BL-ATLAS-15 · Pack Atlas - pack-failed (overflow) path
- **Intent:** Pack fails when sprites cannot fit the max-size atlas.
- **Code:** apps/blender/operators/atlas_pack/pack.py:82-88
- **Pre:** Saved, Object Mode; total sprite area exceeds pack_max_size^2
- **Steps:** Set 'Pack max size' very low (e.g. 64) with large sprites > click 'Pack Atlas'.
- **Expect:** ERROR report 'pack failed - N sprite(s) do not fit in NxN px atlas.'; CANCELLED; nothing written.
- **Status:** pending

#### [ ] BL-ATLAS-17 · Apply Packed Atlas button
- **Intent:** Snapshots pre-apply state, then rewrites every sprite's UVs and material to address the packed atlas.
- **Code:** apps/blender/panels/atlas.py:60 -> operators/atlas_pack/apply.py:31
- **Pre:** Saved blend; <blend>.atlas.json exists (Pack Atlas ran); Object Mode
- **Steps:** After Pack Atlas, click 'Apply Packed Atlas' (FILE_REFRESH icon).
- **Expect:** Per matching mesh: pre_pack CP + '<uv>.pre_pack' UV layer created, UVs remapped into the packed slot, material relinked to 'Proscenio.PackedAtlas' (or image swapped if material_isolated). INFO 'applied packed atlas to N sprite(s)...'. Unpack button now appears.
- **Status:** pending

#### [ ] BL-ATLAS-18 · Apply Packed Atlas - disabled in Edit Mode / no manifest (poll)
- **Intent:** Apply requires Object Mode and an existing manifest.
- **Code:** apps/blender/operators/atlas_pack/apply.py:44-52
- **Pre:** Edit Mode, OR manifest missing, OR unsaved
- **Steps:** Delete the .atlas.json or enter Edit Mode > observe the Apply button.
- **Expect:** Button absent (panel hides it when manifest missing) or greyed (poll False in Edit Mode / unsaved).
- **Status:** pending

#### [ ] BL-ATLAS-19 · Apply Packed Atlas - manifest-not-found runtime path
- **Intent:** Apply reads <blend>.atlas.json; errors if absent.
- **Code:** apps/blender/operators/atlas_pack/apply.py:59-62
- **Pre:** Manifest existed at poll time but deleted before execute (race)
- **Steps:** Click Apply after externally deleting the .atlas.json between draw and click.
- **Expect:** ERROR report 'manifest not found - <stem>.atlas.json'; CANCELLED.
- **Status:** pending

#### [ ] BL-ATLAS-20 · Apply Packed Atlas - shared 'Proscenio.PackedAtlas' material creation
- **Intent:** Links each non-isolated sprite to the shared 'Proscenio.PackedAtlas' material.
- **Code:** apps/blender/operators/atlas_pack/apply.py:70,188-204,247-250
- **Pre:** Apply run; at least one mesh with material_isolated == False
- **Steps:** Apply > inspect the material on a non-isolated sprite + the Material datablocks.
- **Expect:** A material named 'Proscenio.PackedAtlas' exists (rebuilt: nodes cleared, Principled+TexImage(atlas)+Output linked), and non-isolated sprites' slot 0 points to it.
- **Status:** pending

#### [ ] BL-ATLAS-21 · Apply Packed Atlas - isolated-material path
- **Intent:** Set 'Isolated material' on a sprite to keep its own shader while drawing from the packed atlas.
- **Code:** apps/blender/operators/atlas_pack/apply.py:243-245 -> _paths.py:61 swap_image_in_materials
- **Pre:** A sprite mesh has material_isolated == True; Apply prerequisites met
- **Steps:** Enable 'Isolated material' on a sprite (Object panel) > Pack > Apply.
- **Expect:** That sprite keeps its own material; every TEX_IMAGE node's image is swapped to the packed atlas image instead of relinking to the shared material.
- **Status:** pending

#### [ ] BL-ATLAS-22 · Apply Packed Atlas - sprite region rewrite (element_type=='sprite')
- **Intent:** A packed Sprite Frame still slices correctly; region addresses the packed slot.
- **Code:** apps/blender/operators/atlas_pack/apply.py:168-186
- **Pre:** Object with proscenio.element_type == 'sprite' in the manifest; Apply run
- **Steps:** Apply with a sprite-type object > inspect its proscenio.region_mode / region_x/y/w/h.
- **Expect:** region_mode set to 'manual'; region_x/y/w/h set to slot.x/y/w/h divided by atlas_w/atlas_h (normalized slot rectangle).
- **Status:** pending

#### [ ] BL-ATLAS-23 · Apply Packed Atlas - re-Apply / stale-snapshot drift guard
- **Intent:** Re-applying restores original source-image UVs from the pre_pack layer first to avoid cumulative slot shrink.
- **Code:** apps/blender/operators/atlas_pack/apply.py:79-81,97-155
- **Pre:** Sprite already has a pre_pack snapshot from a prior Apply
- **Steps:** Apply > Apply again (re-pack) > if the pre_pack UV layer was renamed/length-mismatched, observe report.
- **Expect:** Healthy snapshot: active UVs restored from pre_pack then re-remapped (no drift). Broken snapshot: WARN 'pre-pack UV snapshot missing or out of sync...skipping Apply'; sprite skipped; summary shows '; skipped N (stale pre-pack snapshot)'.
- **Status:** pending

#### [ ] BL-ATLAS-24 · Apply Packed Atlas - no-UV-layer skip
- **Intent:** Sprites without UV data are skipped during rewrite.
- **Code:** apps/blender/operators/atlas_pack/apply.py:82-84,206-216
- **Pre:** A mesh in the manifest has no active UV layer (element_type=='mesh')
- **Steps:** Apply with a UV-less non-sprite mesh present in the manifest.
- **Expect:** That mesh skipped; report suffix '; skipped N (no UV layer)'. (Note: for element_type=='sprite' it is NOT skipped - see finding.)
- **Status:** pending

#### [ ] BL-ATLAS-25 · Apply Packed Atlas - Ctrl+Z undo
- **Intent:** Apply is undoable; Ctrl+Z reverts (per operator description); doc says Ctrl+Z does NOT revert Unpack snapshot semantics.
- **Code:** apps/blender/operators/atlas_pack/apply.py:42
- **Pre:** Apply just run
- **Steps:** Apply > press Ctrl+Z.
- **Expect:** REGISTER|UNDO pushes one undo step; Ctrl+Z reverts datablock changes (UVs, material assignment, region props). On-disk PNG/JSON remain. Confirm pre_pack CP/UV-layer state after undo (see suspected-bug finding).
- **Status:** pending

#### [ ] BL-ATLAS-26 · Unpack Atlas button
- **Intent:** Reverts a previous apply from the snapshot (survives save/reload; Ctrl+Z does not).
- **Code:** apps/blender/panels/atlas.py:66 -> operators/atlas_pack/unpack.py:36
- **Pre:** At least one mesh carries a pre_pack snapshot (Apply was run); Object Mode
- **Steps:** After Apply, click 'Unpack Atlas' (LOOP_BACK icon).
- **Expect:** Each snapshotted mesh: pre_pack UVs restored into the original layer, the '.pre_pack' layer removed, original material + image + region_mode restored, pre_pack CP deleted. INFO 'unpacked N sprite(s) - restored pre-Apply state'. Button disappears.
- **Status:** pending

#### [ ] BL-ATLAS-27 · Unpack Atlas - hidden when no snapshot
- **Intent:** Unpack only available after an Apply created a snapshot.
- **Code:** apps/blender/panels/atlas.py:65 + operators/atlas_pack/unpack.py:49-52
- **Pre:** No mesh has a pre_pack snapshot
- **Steps:** On a packed-but-not-applied (or freshly unpacked) file, expand Atlas subpanel.
- **Expect:** No 'Unpack Atlas' button drawn (scene_has_pre_pack_snapshot False); poll would also block it in Edit Mode.
- **Status:** pending

#### [ ] BL-ATLAS-28 · Unpack Atlas - material-missing partial restore
- **Intent:** Restores original material; if the original was deleted, restore UVs only.
- **Code:** apps/blender/operators/atlas_pack/unpack.py:107-124,68-72
- **Pre:** Apply ran; then the original material datablock deleted/renamed before Unpack
- **Steps:** Apply > delete the original material > Unpack.
- **Expect:** WARN per object 'original material ... not found (deleted?); restored UVs only'; summary 'unpacked N; M with materials missing (UVs only): names'. Rename case is rescued via the origin marker.
- **Status:** pending

#### [ ] BL-ATLAS-29 · Unpack Atlas - rename rescue via origin marker
- **Intent:** A rename between Apply and Unpack still restores via the stamped origin marker.
- **Code:** apps/blender/operators/atlas_pack/unpack.py:21-33,113-117
- **Pre:** Apply ran (stamps PROSCENIO_ATLAS_ORIGIN_MARKER); original material renamed
- **Steps:** Apply > rename the original material > Unpack.
- **Expect:** By-name lookup misses, marker scan finds the renamed material, slot 0 restored to it; counted as a successful (non-partial) restore.
- **Status:** pending

#### [ ] BL-ATLAS-30 · Unpack Atlas - region restore
- **Intent:** Restores original region_mode (and region x/y/w/h).
- **Code:** apps/blender/operators/atlas_pack/unpack.py:136-145
- **Pre:** Apply ran on a sprite-type object (region was changed to manual)
- **Steps:** Apply a sprite > Unpack > inspect proscenio.region_mode / region_x..h.
- **Expect:** region_mode and region_x/y/w/h restored to the pre-Apply snapshot values (suppresses TypeError/ValueError on assignment).
- **Status:** pending

#### [ ] BL-ATLAS-31 · Unpack Atlas - Ctrl+Z undo / survives reload
- **Intent:** The snapshot survives save/reload; Ctrl+Z does not revert the original Apply.
- **Code:** apps/blender/operators/atlas_pack/unpack.py:47
- **Pre:** Apply ran, file saved
- **Steps:** Apply > save > reopen .blend > Unpack works; separately, Unpack > Ctrl+Z.
- **Expect:** Snapshot (CP + .pre_pack layer) persists across save/reload so Unpack still functions after reopen. Unpack itself is REGISTER|UNDO so Ctrl+Z reverts the unpack operation.
- **Status:** pending

## Validation panel (export-blocking issues list)

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-VALID-01 | Status badge (header, godot-ready icon) | Hover shows the godot-ready band tooltip (from STATUS_BADGES); click opens the 'status_legend' help popup (480px) listing the status bands | UNDOCUMENTED | apps/blender/panels/validation.py:21 -> _helpers.py:83 (_draw_status_button) -> help_dispatch.py:17 (PROSCENIO_OT_status_info) | pending |
| BL-VALID-04 | 'proscenio scene props not registered' error label | Panel shows only the label 'proscenio scene props not registered' with an ERROR icon; no Validate button, no rows | UNDOCUMENTED (registration-guard fallback) | apps/blender/panels/validation.py:25-28 | pending |
| BL-VALID-05 | 'run Validate to see issues' info label | Below the Validate button shows label 'run Validate to see issues' with an INFO icon | UNDOCUMENTED (empty-state prompt before first Validate run) | apps/blender/panels/validation.py:33-35 | pending |
| BL-VALID-06 | 'no issues - ready to export' label | Label 'no issues - ready to export' with a CHECKMARK icon; no issue rows | UNDOCUMENTED (clean-scene success state; doc only says errors block / warnings inform) | apps/blender/panels/validation.py:38-40 | pending |
| BL-VALID-08 | Issue row (plain label, scene-wide) - 'message' | A non-clickable label appears with the message; error severity shows ERROR icon + red alert tint, warning shows INFO icon; clicking it does nothing | Errors block the export; warnings are informational (no object means a plain, non-clickable label). | apps/blender/panels/validation.py:43 -> _helpers.py:149-150 (draw_issue_row else branch) | pending |

#### [ ] BL-VALID-02 · Help '?' button (header)
- **Intent:** UNDOCUMENTED (the '?' itself is undocumented; it opens the Validation help topic which mirrors this doc page)
- **Code:** apps/blender/panels/validation.py:21 -> _helpers.py:84 (draw_subpanel_header) -> help_dispatch.py:50 (PROSCENIO_OT_help)
- **Pre:** Validation subpanel expanded
- **Steps:** Click the '?' icon at the right of the Validation header
- **Expect:** A 480px popup opens titled with the 'validation' help topic; shows summary + sections; ESC/click-away closes it
- **Status:** pending

#### [ ] BL-VALID-03 · Validate button
- **Intent:** Walks the scene and reports issues that would block an export (missing armature when sprites carry vertex groups, dead bone references, missing atlas files, sprite_frame meshes without hframes/vframes).
- **Code:** apps/blender/panels/validation.py:30 -> export_flow.py:121 (PROSCENIO_OT_validate_export.execute:132)
- **Pre:** scene.proscenio registered (else the panel short-circuits to an error label and never draws the button)
- **Steps:** Click 'Validate' with a populated scene
- **Expect:** validation_results is repopulated and validation_ran set True; info-bar reports 'N error(s), M warning(s)' (red) / 'M warning(s)' (yellow) / 'validation OK'; issue rows render below the separator; debug log echoes each issue
- **Status:** pending

#### [ ] BL-VALID-07 · Issue row (clickable, object-scoped) - '[obj] message'
- **Intent:** Click a row to select the offending object.
- **Code:** apps/blender/panels/validation.py:43 -> _helpers.py:142 (draw_issue_row) -> selection.py:18 (PROSCENIO_OT_select_issue_object.execute:31)
- **Pre:** validation_ran True; at least one issue with obj_name set (e.g. an element with vertex groups that don't resolve to bones, or a missing-atlas object)
- **Steps:** Run Validate to surface object-scoped issues > click a row showing '[Name] message'
- **Expect:** That object becomes the sole selection and active object (deselects all others first); error rows render with ERROR icon + red alert tint, warnings with INFO icon; if the object name no longer exists a 'object \'<name>\' not found' warning is reported and selection is unchanged
- **Status:** pending

## Pipeline panel: import Photoshop manifest + export/re-export .proscenio

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-PIPE-01 | Pipeline panel (parent grouper) - missing-props error label | Panel renders with Import + Export subpanels nested under it. With scene props registered, body is empty (no error). Only if scene.proscenio is unregistered does the row 'proscenio scene props not registered' (ERROR icon) appear. | Pipeline groups Import + Export; doc describes the panel as the import/export ends of the stage. | apps/blender/panels/pipeline.py:38-40 | pending |
| BL-PIPE-02 | Pipeline header status badge (feature_id 'pipeline') | Hover shows the GODOT_READY band tooltip (pipeline maps to GODOT_READY). Click opens the 'status_legend' help popup. Badge uses the custom Godot mark icon (falls back to built-in icon if preview load failed/headless). | UNDOCUMENTED (header status badge convention not in the pipeline doc). | apps/blender/panels/pipeline.py:35-36 -> apps/blender/panels/_helpers.py:46-69 | pending |
| BL-PIPE-03 | Pipeline header help button '?' (topic 'pipeline_overview') | A 480px-wide popup opens titled from the 'pipeline_overview' HelpTopic with summary + sections; an 'Open online docs' button (resolves to pipeline doc anchor) is present. | UNDOCUMENTED (the in-panel '?' help affordance is not described in the doc). | apps/blender/panels/pipeline.py:36 -> apps/blender/panels/_helpers.py:84-85 -> apps/blender/operators/help_dispatch.py:50-97 | pending |
| BL-PIPE-04 | Import header status badge (feature_id 'import') | Hover shows BLENDER_ONLY band tooltip (import maps to BLENDER_ONLY); badge uses the custom Blender mark icon. Click opens the status_legend popup. | UNDOCUMENTED (subpanel status badge not in doc). | apps/blender/panels/pipeline.py:54-55 -> apps/blender/panels/_helpers.py:46-69 | pending |
| BL-PIPE-05 | Import header help button '?' (topic 'import_photoshop') | Popup opens with the 'import_photoshop' HelpTopic content (title/summary/sections) and an Open online docs button to pipeline#import. | UNDOCUMENTED (in-panel help button not described). | apps/blender/panels/pipeline.py:55 -> apps/blender/panels/_helpers.py:84-85 -> apps/blender/operators/help_dispatch.py:50-97 | pending |
| BL-PIPE-07 | Import file dialog: Placement (enum: Landed / Centered) | Landed shifts every stamped mesh up so the figure's lowest point sits on world Z=0; Centered keeps the figure centred on the manifest canvas centre at world origin. Default is 'landed'. | UNDOCUMENTED (placement enum exists in the importer redo/dialog sidebar but the doc never mentions Landed vs Centered). | apps/blender/operators/import_photoshop.py:40-60 -> apps/blender/importers/photoshop/__init__.py:89-90 (_anchor_meshes_at_feet) | pending |
| BL-PIPE-08 | Import file dialog: Root Bone Name (text field) | The single bone created in the stub armature is named with the entered value (default 'root'); empty input falls back to 'root' (import_photoshop.py:81). | UNDOCUMENTED (the doc says everything parents to a 'stub root armature' but never exposes the bone-name override). | apps/blender/operators/import_photoshop.py:62-70 -> apps/blender/importers/photoshop/__init__.py:70-73 | pending |
| BL-PIPE-09 | Export header status badge (feature_id 'export') | Hover shows GODOT_READY band tooltip (export maps to GODOT_READY); badge uses the custom Godot mark icon. Click opens the status_legend popup. | UNDOCUMENTED (subpanel status badge not in doc). | apps/blender/panels/pipeline.py:80-81 -> apps/blender/panels/_helpers.py:46-69 | pending |
| BL-PIPE-10 | Export header help button '?' (topic 'export') | Popup opens with the 'export' HelpTopic content and an Open online docs button to pipeline#export. | UNDOCUMENTED (in-panel help button not described). | apps/blender/panels/pipeline.py:81 -> apps/blender/panels/_helpers.py:84-85 -> apps/blender/operators/help_dispatch.py:50-97 | pending |
| BL-PIPE-11 | Last export path (FILE_PATH field) | Field holds the sticky destination; once non-empty the 'Re-export' button appears below; value persists across save/reload of the .blend. Editing it manually changes where Re-export writes (re-export uses bpy.path.abspath of this value). | The path is sticky so Re-export skips the file dialog; saved with the .blend so the document carries its export target. | apps/blender/panels/pipeline.py:88 -> apps/blender/properties/scene_props.py:403-411 | pending |
| BL-PIPE-12 | Pixels per unit (number field, scene prop) | Scene-level pixels_per_unit updates (min 0.0001). Re-export uses this value as the conversion ratio. NOTE: the first 'Export (.proscenio)' run does NOT use this field (see finding) - it uses the operator's own ppu property defaulting to 100. Also auto-synced to the manifest PPU on import. | Sets the Blender-world-to-Godot-pixel ratio (default 100). | apps/blender/panels/pipeline.py:89 -> apps/blender/properties/scene_props.py:412-417 | pending |
| BL-PIPE-13 | Bundle textures (checkbox) | On write, every referenced texture is copied next to the .proscenio; success report gets a '; bundled N texture(s)' suffix (and 'K missing on disk' when applicable); console prints '[Proscenio] bundle -> copied .., skipped .., missing ..'. When off, no copying and no suffix. | UNDOCUMENTED (the pipeline doc never mentions a texture-bundling toggle). | apps/blender/panels/pipeline.py:90 -> apps/blender/properties/scene_props.py:418-426 -> apps/blender/operators/export_flow.py:97-118 | pending |
| BL-PIPE-15 | Export file dialog: Pixels per unit (operator FloatProperty) | Writer uses THIS operator value (default 100, min 0.0001), independent of the panel/scene Pixels-per-unit field. This is the only ppu the first Export honors. | Sets the Blender-world-to-Godot-pixel ratio (default 100) per the doc's Pixels-per-unit description. | apps/blender/operators/export_flow.py:158-163,167 | pending |

#### [ ] BL-PIPE-06 · Import Photoshop Manifest (button)
- **Intent:** Reads a manifest from the Photoshop plugin, stamps one mesh per layer (composing spritesheets for sprite_frame groups), parents everything to a stub root armature; re-importing reuses meshes so rotation/parenting/weights survive.
- **Code:** apps/blender/panels/pipeline.py:58-62 -> apps/blender/operators/import_photoshop.py:26-103 -> apps/blender/importers/photoshop/__init__.py:42-91
- **Pre:** A valid PSD manifest .json on disk (from the Photoshop plugin).
- **Steps:** Pipeline > Import > click 'Import Photoshop Manifest' > pick a manifest .json in the file dialog > Import.
- **Expect:** File dialog filters to *.json. On import, the info bar reports 'stamped N mesh(es) (armature: <name>)' plus 'skipped K' / 'composed M spritesheet(s)' when applicable; meshes appear parented to a stub armature; scene.proscenio.pixels_per_unit is synced to the manifest's PPU; operation is undoable (Ctrl+Z).
- **Status:** pending

#### [ ] BL-PIPE-14 · Export (.proscenio) (button)
- **Intent:** Runs the writer, validates against the schema, writes the JSON next to the .blend; the path is sticky.
- **Code:** apps/blender/panels/pipeline.py:93 -> apps/blender/operators/export_flow.py:147-178
- **Pre:** A scene with exportable content (armature + sprites).
- **Steps:** Pipeline > Export > click 'Export (.proscenio)' > choose destination in the file dialog > Export.
- **Expect:** File dialog filters to *.proscenio. Validation runs first; if any error-severity issues exist the export is blocked with 'export blocked by N validation error(s) - see Validation panel.' and nothing is written. On success: JSON written, info bar 'wrote <name>' (+bundle suffix), console '[Proscenio] exported -> <path>', and last_export_path is set to the chosen path (making Re-export appear).
- **Status:** pending

#### [ ] BL-PIPE-16 · Re-export (button)
- **Intent:** Re-export skips the file dialog (uses the sticky path).
- **Code:** apps/blender/panels/pipeline.py:94-95 -> apps/blender/operators/export_flow.py:181-206
- **Pre:** last_export_path is non-empty (a prior Export ran or the path was typed in).
- **Steps:** Pipeline > Export > click 'Re-export'.
- **Expect:** No file dialog. Validation gate runs; blocking errors abort with 're-export failed' path. On success the writer writes to abspath(last_export_path) using the SCENE pixels_per_unit, info bar 're-exported -> <name>' (+bundle suffix), console '[Proscenio] re-exported -> <path>'. Button is hidden when last_export_path is empty (and operator poll also returns False).
- **Status:** pending

## Helpers panel (viewport authoring aids outside export)

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-HELP-01 | Helpers subpanel foldout (header) | Subpanel starts collapsed (bl_options DEFAULT_CLOSED); clicking expands it to reveal the Preview Camera button. Header reads 'Helpers'. | Collapsible 'Helpers' subpanel hosting viewport authoring aids that never touch the .proscenio. | apps/blender/panels/helpers.py:16-35 | pending |
| BL-HELP-02 | Status badge icon (header, blender-only band) | Icon is the custom Blender-only mark (feature 'helpers' = BLENDER_ONLY); falls back to TOOL_SETTINGS built-in if the preview PNG failed to load. Hover shows the blender-only band tooltip ('Authoring shortcut. Lives entirely on the Blender side...'); click opens the Status badges legend popup. | UNDOCUMENTED (the doc page never mentions the status badge; the help_topics 'status_legend' topic explains it). | apps/blender/panels/_helpers.py:46-69 (drawn via draw_subpanel_header at helpers.py:28) | pending |

#### [ ] BL-HELP-03 · Status badge click -> Status legend popup (proscenio.status_info)
- **Intent:** UNDOCUMENTED in the doc page; surfaces the 'Status badges' legend (status_legend help topic).
- **Code:** apps/blender/operators/help_dispatch.py:42-44 (invoke calls bpy.ops.proscenio.help topic='status_legend')
- **Pre:** Helpers header status badge visible.
- **Steps:** Click the status badge icon on the Helpers header.
- **Expect:** A 480px-wide popup titled 'Status badges' opens listing the four bands (godot-ready / blender-only / planned / out-of-scope) and the per-feature legend, with an 'Open online docs' button (doc_url -> .../helpers? no, status_legend anchor '#status-badges').
- **Status:** pending

#### [ ] BL-HELP-04 · Help button '?' (proscenio.help, topic='helpers')
- **Intent:** UNDOCUMENTED in the doc page; opens the in-panel Helpers help popup. The 'helpers' help topic mirrors the doc text.
- **Code:** apps/blender/panels/_helpers.py:84-85 (op.topic='helpers'); operator at help_dispatch.py:50-98
- **Pre:** Helpers subpanel header rendered.
- **Steps:** Click the '?' (QUESTION) icon at the far right of the 'Helpers' header.
- **Expect:** A 480px popup opens titled 'Helpers' with summary 'Viewport authoring aids that are not part of the export pipeline.', a 'What it does' section, a 'Preview Camera' section, and an 'Open online docs' button linking to .../blender-addon/helpers.
- **Status:** pending

#### [ ] BL-HELP-05 · Preview Camera button (proscenio.create_ortho_camera)
- **Intent:** Drops an orthographic front camera framed the way the Godot importer expects, so the viewport matches the runtime framing.
- **Code:** apps/blender/panels/helpers.py:31-35 (button); operator at apps/blender/operators/armature/authoring_camera.py:16-53
- **Pre:** A Proscenio scene open. No specific active object/mode required. scene.proscenio.pixels_per_unit set (falls back to 100.0 if props missing).
- **Steps:** Expand Helpers > click 'Preview Camera' (OUTLINER_OB_CAMERA icon). Re-click to test the focus/update path.
- **Expect:** First click: creates object 'Proscenio.PreviewCam' at location (0,-10,0) rotated +90deg on X (front view), type=ORTHO, ortho_scale = max(res_x,res_y)/pixels_per_unit; sets it as scene.camera and the sole selection; INFO report "created 'Proscenio.PreviewCam' (ortho_scale=...)". Re-click: reuses the existing object, recomputes ortho_scale, reports "updated ...". Press Numpad 0 to look through it (native Blender, per the operator tooltip). REGISTER|UNDO so Ctrl+Z reverts creation.
- **Status:** pending

## Diagnostics + Help system + Addon Preferences + status badges

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| BL-DIAG-01 | Diagnostics panel (visibility / poll) | With Debug mode OFF the Diagnostics subpanel is absent; with Debug mode ON it appears (DEFAULT_CLOSED) at bl_order 13 below Help. | UNDOCUMENTED - the index sidebar list (panels 01-11) never mentions a Diagnostics panel; only the addon-prefs description says debug_mode 'Show the developer surface: the Diagnostics panel'. | apps/blender/panels/diagnostics.py:24-26 | pending |
| BL-DIAG-03 | Diagnostics header status badge (blender-only) | Custom Blender badge icon renders (or TOOL_SETTINGS built-in if preview load failed); tooltip reads the blender-only band text ('Authoring shortcut. Lives entirely on the Blender side - does NOT alter the .proscenio export'). | Status badge legend: blender-only = authoring shortcut that never reaches the export (index 'Status badges'). | apps/blender/panels/diagnostics.py:29 -> apps/blender/panels/_helpers.py:46-69; feature_status.py:120 | pending |
| BL-DIAG-06 | Help panel (visibility) | Help subpanel is always present (regardless of debug_mode), collapsed by default, sitting just above Diagnostics. | UNDOCUMENTED - the index sidebar list (panels 01-11) does not include a Help panel; the panel's own docstring calls it a 'Shortcut cheat-sheet - every Proscenio operator with its idname.' | apps/blender/panels/help.py:32-41 | pending |
| BL-DIAG-07 | Help panel body label 'Operators (use F3 to search):' | A QUESTION-icon label 'Operators (use F3 to search):' renders at the top of the body. | UNDOCUMENTED - read-only instructional label; doc never describes the Help cheat-sheet. | apps/blender/panels/help.py:48 | pending |
| BL-DIAG-08 | Help panel operator reference rows (18 label/idname pairs) | Exactly 18 rows render, each a two-label row (e.g. 'Validate' / 'proscenio.validate_export'); rows are plain read-only labels (NOT clickable operator buttons) - selecting/clicking does nothing. | UNDOCUMENTED - static two-column cheat-sheet mapping a human label to its operator idname for F3 search. | apps/blender/panels/help.py:49-52 (loop over _OPERATOR_REFERENCE, help.py:11-29) | pending |
| BL-DIAG-09 | Help header status badge (blender-only) | Blender badge icon renders; tooltip shows the blender-only band text. | Status badge legend: blender-only band per index 'Status badges'. | apps/blender/panels/help.py:44 -> _helpers.py:46-69; feature_status.py:119 | pending |
| BL-DIAG-13 | Help popup unknown-topic fallback | Popup shows a single ERROR-icon label "unknown help topic: 'nope'" and nothing else. | Defensive: an unresolved topic id surfaces an error label rather than crashing. | apps/blender/operators/help_dispatch.py:73-76 | pending |
| BL-DIAG-15 | Addon Preferences - 'Developer' box label | A boxed section with a TOOL_SETTINGS-icon 'Developer' label appears, containing the two prefs below. | UNDOCUMENTED grouping label; box header for the developer prefs. | apps/blender/addon_prefs.py:61-62 | pending |
| BL-DIAG-16 | Addon Preferences - 'Log level' dropdown (errors/info/debug) | Changing the enum immediately calls set_min_level: 'Errors only' suppresses report_info/report_warn output, 'Debug' surfaces '[Proscenio debug]'-tagged traces; default is 'Info'. Choice persists across restart and is re-applied at register via _sync_log_level_from_prefs. | UNDOCUMENTED in the doc page; prop description: controls how much operators report to the Info log (Errors only / Info default / Debug adds per-item traces). | apps/blender/addon_prefs.py:29-48 (update=_on_log_level_update -> report.set_min_level) | pending |
| BL-DIAG-17 | Addon Preferences - 'Debug mode' checkbox | ON reveals the Diagnostics subpanel (and the automesh Debug Pipeline subpanel elsewhere); OFF hides them. Has no update callback - effect appears on next panel redraw. | UNDOCUMENTED in the doc page; prop description: 'Show the developer surface: the Diagnostics panel and the automesh Debug Pipeline subpanel.' Off by default. | apps/blender/addon_prefs.py:50-58; consumed by debug_mode_enabled() at addon_prefs.py:67-80 and diagnostics.py:26 | pending |
| BL-DIAG-18 | Status legend popup (status_legend topic content) | Popup titled 'Status badges' lists all four bands with the same definitions as the index page; the popup is the only place godot-ready/planned/out-of-scope bands are described in-addon. | index 'Status badges': legend mapping godot-ready / blender-only / planned / out-of-scope to pipeline meaning. | apps/blender/core/help_topics.py:63-96; opened via help_dispatch.py:43 | pending |

#### [ ] BL-DIAG-02 · Run Smoke Test (PLAY icon button)
- **Intent:** UNDOCUMENTED in the doc page; operator's own bl_description: 'Print a sanity check to the system console' confirming the addon registers and dispatches.
- **Code:** apps/blender/panels/diagnostics.py:33 -> apps/blender/operators/help_dispatch.py:108-112
- **Pre:** Debug mode ON so Diagnostics panel is visible.
- **Steps:** Open Diagnostics subpanel > click 'Run Smoke Test'
- **Expect:** Info-area report 'Proscenio smoke test OK' (no 'Proscenio:' prefix) and system console prints '[Proscenio] Proscenio smoke test OK'; operator returns FINISHED.
- **Status:** pending

#### [ ] BL-DIAG-04 · Diagnostics header status badge (click)
- **Intent:** Per-feature status: 'Click the icon to re-open this legend' (status_legend help topic).
- **Code:** apps/blender/operators/help_dispatch.py:42-44 (PROSCENIO_OT_status_info.invoke)
- **Pre:** Debug mode ON.
- **Steps:** Open Diagnostics header > click the Blender-mark status icon
- **Expect:** invoke_popup opens the 'Status badges' legend popup (status_legend topic) listing the four bands; clicking does NOT toggle/edit anything else.
- **Status:** pending

#### [ ] BL-DIAG-05 · Diagnostics header '?' help button
- **Intent:** index line 26: each header carries a '?' that opens the matching help inline.
- **Code:** apps/blender/panels/diagnostics.py:29 -> _helpers.py:84-85 (topic='pipeline_overview')
- **Pre:** Debug mode ON.
- **Steps:** Open Diagnostics header > click the '?' icon
- **Expect:** A 480px help popup opens titled 'Proscenio pipeline overview' (NOT a Diagnostics-specific topic) - it shows the generic pipeline+status-badges content, not 'the matching help' the doc promises.
- **Status:** pending

#### [ ] BL-DIAG-10 · Help header status badge (click)
- **Intent:** Click the status icon re-opens the status legend (status_legend topic).
- **Code:** apps/blender/operators/help_dispatch.py:42-44
- **Pre:** None.
- **Steps:** Open Help header > click the status icon
- **Expect:** 'Status badges' legend popup opens.
- **Status:** pending

#### [ ] BL-DIAG-11 · Help header '?' help button
- **Intent:** index line 26: '?' opens the matching help inline.
- **Code:** apps/blender/panels/help.py:44 -> _helpers.py:84-85 (topic='pipeline_overview')
- **Pre:** None.
- **Steps:** Open Help header > click '?'
- **Expect:** Popup opens 'Proscenio pipeline overview' (generic), not a Help-panel-specific topic.
- **Status:** pending

#### [ ] BL-DIAG-12 · Help popup (PROSCENIO_OT_help) content rendering
- **Intent:** help_dispatch docstring: 'Pop up an in-panel help dialog for a given topic id' rendering title, summary, sections, see-also, online-docs button.
- **Code:** apps/blender/operators/help_dispatch.py:64-97
- **Pre:** Any '?' button clicked.
- **Steps:** Click any '?' > read popup > if a 'See also' http link or 'Open online docs' button present, click it
- **Expect:** 480px popup shows QUESTION-titled header, summary line, DOT-marked section headings + body lines; 'Open online docs' (HELP icon) opens the doc_url via wm.url_open; http see-also entries are clickable url buttons, non-http see-also entries render as indented plain labels.
- **Status:** pending

#### [ ] BL-DIAG-14 · Status-info tooltip dispatch (PROSCENIO_OT_status_info.description)
- **Intent:** Per-feature status: hovering the icon surfaces the band-specific tooltip.
- **Code:** apps/blender/operators/help_dispatch.py:30-40
- **Pre:** Any panel header with a status badge.
- **Steps:** Hover any status badge icon and read the tooltip; also observe a band whose value is invalid
- **Expect:** Tooltip text equals STATUS_BADGES[band].tooltip for the badge's band; an invalid band value falls back to the operator bl_label 'Proscenio: Feature Status'.
- **Status:** pending

## Findings

| ID | Type | Sev | Control | Detail | Code |
| --- | --- | --- | --- | --- | --- |
| F-01 | drift | high | Per-row favorite toggle / Favorites-only / SOLO icon | Doc says SOLO 'pins a row as a favorite' and object_props description says 'Pin this object to the TOP of the Proscenio outliner', but filter_items sorts purely by (category rank, name) at line 120 - favorites never reorder to the top. Favorite only affects the favorites-only filter, not list position. | apps/blender/panels/outliner.py:120; properties/object_props.py:253 |
| F-02 | undocumented | medium | Status badge button (header) | Header renders a Blender-only status badge (proscenio.status_info) whose click opens the status legend popup; doc never mentions the badge or its click-to-legend behavior. | apps/blender/panels/_helpers.py:83; operators/help_dispatch.py:42-44 |
| F-03 | undocumented | medium | Help '?' button (header) | Header renders a '?' help button opening the 'outliner' help popup; doc never mentions the in-panel help affordance. | apps/blender/panels/_helpers.py:84 |
| F-04 | undocumented | medium | Native 'Filter by Name' field | filter_items also honors Blender's native UIList self.filter_name (used when the Proscenio search bar is empty), an entirely separate search affordance the doc does not mention; dual-search precedence ('bar wins') is undocumented and surprising. | apps/blender/panels/outliner.py:96-99,117 |
| F-05 | undocumented | low | Sprite-mesh '@ <bone>' suffix label | Rank-2 sprite-mesh rows append ' @ <parent_bone>' when bone-parented; doc describes labels for slots and armatures but never this bone-attachment suffix. | apps/blender/panels/outliner.py:62-63 |
| F-06 | suspected-bug | low | Row click / active_outliner_index highlight | _sync_active_index writes the index by position in the UNFILTERED, UNSORTED bpy.data.objects collection, but template_list displays a filtered + category-reordered view (flt_neworder). The UIList active-row highlight can therefore land on a different visual row than the one the user clicked whenever the display order diverges from bpy.data.objects order. | apps/blender/operators/selection.py:58,153-167; panels/outliner.py:120-124 |
| F-07 | undocumented | low | 'Proscenio scene props not registered' fallback label | Panel draws an ERROR label and bails when scene.proscenio is missing; this failure state is not documented. | apps/blender/panels/outliner.py:143-146 |
| F-08 | drift | low | Outliner list ordering description | Doc says rows are 'slots ... their attachments indented under them; armatures render last', implying attachments stay visually grouped beneath their parent slot. Sorting is global by (rank, name): all rank-0 slots sort together first, then ALL rank-1 attachments together, so an attachment is not adjacent to its specific parent slot when multiple slots exist. | apps/blender/panels/outliner.py:120 |
| F-09 | dead | low | Weight-paint inline brush mirror (draw_weight_paint) | _draw_mesh.draw_weight_paint() is fully implemented (size/strength/weight/auto-normalize mirror) but never called; the element panel's PAINT_WEIGHT branch only draws a disabled element_type + 'locked' label, so the brush mirror is unreachable dead code. | apps/blender/panels/_draw_mesh.py:28-44 (never referenced); apps/blender/panels/element.py:56-61 |
| F-10 | drift | medium | Drive from Bone - Axis default / help text | Help doc states 'default ROT_Z = local 2D rotation', but both the PropertyGroup driver_source_axis and the operator source_axis default to ROT_Y; the panel default never matches the documented ROT_Z. | apps/blender/core/help_topics.py:295 vs object_props.py:202 / driver.py:118 |
| F-11 | drift | medium | Drive from Bone - Axis enum (order + descriptions) | Two divergent axis enum definitions: object_props DRIVER_SOURCE_AXIS_ITEMS lists ROT_Z first describing it as 'Pose bone local rotation around Z (typical 2D plane)', while operator _DRIVER_SOURCE_AXES lists ROT_Y first as 'front-ortho camera axis (visible 2D)'. The panel shows the PG order/descriptions; the redo-panel operator shows the other. Same control, inconsistent labels/order. | apps/blender/properties/object_props.py:59-66 vs apps/blender/operators/driver.py:24-31 |
| F-12 | suspected-bug | medium | Drive from Bone - Axis (ROT space) | Axis item descriptions claim 'Pose bone LOCAL rotation around Z/X/Y', but the operator forces target.transform_space = WORLD_SPACE for all ROT_* axes (comment: WORLD reads pose rotation 1:1). For non-axis-aligned bones the driven value differs from the 'local' rotation the label promises, so picking ROT_Z can read a different channel than the user expects. | apps/blender/operators/driver.py:230-236; object_props.py:59-62 |
| F-13 | undocumented | low | Isolated material toggle | material_isolated checkbox appears in the Active Mesh body but the element doc page never mentions it. | apps/blender/panels/_draw_mesh.py:24; object_props.py:157-167 |
| F-14 | undocumented | low | Exclude from atlas toggle | exclude_from_atlas checkbox appears in the Active Mesh body but the element doc page never mentions it. | apps/blender/panels/_draw_mesh.py:25; object_props.py:168-178 |
| F-15 | undocumented | low | Reproject UV button | Reproject UV lives in the Active Mesh body but the element doc never mentions it (only 'Drive from Bone' is described as an action). It also has a Smart-UV-Project mirror/rotate hazard worth documenting. | apps/blender/panels/_draw_mesh.py:23; operators/uv_authoring.py:22-80 |
| F-16 | undocumented | low | Setup Preview / Remove Preview buttons | Sprite preview-shader setup/remove buttons in the Active Sprite body are not documented on the element page. | apps/blender/panels/_draw_sprite.py:66-83 |
| F-17 | undocumented | low | Atlas/region/frame readout labels (sprite) and poly/vgroup label (mesh) | The numeric read-out labels (atlas size, region px, frame px grid; polygon/vertex-group counts) are undocumented. | apps/blender/panels/_draw_sprite.py:31-54; _draw_mesh.py:19-22 |
| F-18 | drift | low | Snap to UV bounds | Doc says 'Snap to UV bounds fills the manual fields from the current UV' without qualification, but the button is only drawn for element_type=='mesh'; sprite manual mode has no Snap button. | apps/blender/panels/_draw_region.py:28-29 |
| F-19 | undocumented | low | Drive from Bone - In/Out range, Advanced expression, live Value readout | The two-range linear map (In Min/Max, Out Min/Max), the Advanced expression toggle/field, and the live driven Value readout are present in the panel but the element doc only says 'wires a driver between a pose bone and a sprite property' with no mention of these controls. | apps/blender/panels/_draw_driver_shortcut.py:26-37 |
| F-20 | drift | low | Driver Target enum descriptions (frame range) | object_props DRIVER_TARGET_ITEMS frame description says 'driven 0..hframes*vframes-1' while the operator _DRIVER_TARGET_PROPERTIES says 'driven 0..hframes*vframes' (off-by-one inconsistency between the two enum copies). | apps/blender/properties/object_props.py:52 vs apps/blender/operators/driver.py:18 |
| F-21 | suspected-bug | low | Active Sprite / Active Mesh subpanels (bl_order collision) | PROSCENIO_PT_active_mesh and PROSCENIO_PT_active_sprite both declare bl_order = 0 under the same parent. They are mutually exclusive via poll so only one shows, but the duplicate order is fragile and relies solely on poll for disambiguation. | apps/blender/panels/element.py:76,100 |
| F-22 | undocumented | medium | Keyframe attachment button (KEYFRAME_HLT) | The per-attachment keyframe button (proscenio.keyframe_slot_attachment) is the only in-panel way to author the slot_attachment swap track, yet 03-slots.md never mentions a keyframe affordance — it only says the track 'flips visibility per key' abstractly. | apps/blender/panels/slots.py:152-157; operators/slot/attachment.py:107-152 |
| F-23 | undocumented | low | Per-slot mesh-child count badge | The number+OUTLINER_OB_MESH badge on each slot row (count of MESH children) is undocumented. | apps/blender/panels/slots.py:71-72 |
| F-24 | undocumented | low | Pose/Object-Mode tip box | The boxed two-line hint above Create Slot describing pose-bone vs mesh-selection anchoring is undocumented. | apps/blender/panels/slots.py:74-77 |
| F-25 | undocumented | low | Parent bone readout / 'no parent bone' warning | The Active Slot 'bone:' readout and the red 'no parent bone - attachments will not follow any bone' alert are undocumented; doc never describes the unparented failure case. | apps/blender/panels/slots.py:118-128 |
| F-26 | undocumented | low | Attachment kind label (mesh/sprite) | The per-attachment kind label + MESH_DATA/IMAGE_DATA icon is undocumented. | apps/blender/panels/slots.py:150-151 |
| F-27 | undocumented | low | Active-slot validation issue rows | The validation issue rows rendered under the attachment list (no-children, broken-default, child-bone-mismatch, transform-keys-on-child) are undocumented in 03-slots.md. | apps/blender/panels/slots.py:167-168 |
| F-28 | undocumented | low | Header status badges + '?' help buttons (both panels) | The slot_system / active_slot status icons and the QUESTION help buttons on both panel headers are undocumented in the slots doc (covered only by the separate help-surfaces spec). | apps/blender/panels/slots.py:51-52,101-102; _helpers.py:72-86 |
| F-29 | suspected-bug | medium | Slot row select operator | proscenio.select_slot resolves the row by name via bpy.data.objects.get(slot_name) (data-block global), but the list is built from context.scene.objects. With a same-named slot Empty linked into another scene, the click can select/activate the wrong (or scene-absent) object, or warn 'not found' even though the row is visible. | operators/slot/select.py:36-44; core/bpy_helpers/_shared/select.py:108 |
| F-30 | suspected-bug | low | Add Selected Mesh / SOLO star / Keyframe — slot re-flag risk | All slot detail operators gate on is_slot via the PropertyGroup flag is_slot (set in create.py only when hasattr(empty,'proscenio')). If the addon's proscenio PropertyGroup is unregistered (e.g. partial reload), create.py never sets is_slot, the panel poll fails, and a slot created earlier becomes unreachable in the UI — silent, no warning. | operators/slot/create.py:95-96; operators/slot/attachment.py:48-56 |
| F-31 | drift | low | Active Slot intent: 'adds the selected mesh as a new attachment' | Doc says the subpanel 'adds the selected mesh' (singular), but proscenio.add_slot_attachment re-parents ALL selected MESH objects (meshes list), and the poll only requires one — so a multi-select adds several at once, beyond the documented single-mesh behavior. | operators/slot/attachment.py:58-67 |
| F-32 | dead | low | sprite_frame preview operators filed under operators/slot | PROSCENIO_OT_setup/remove_sprite_frame_preview live in operators/slot/preview_shader.py (per __init__ docstring) but are drawn only from the Mesh/Element sprite panel (_draw_sprite.py:73,80), not from any Slots panel control — no slot-surface UI reaches them. | operators/slot/preview_shader.py:12-95; panels/_draw_sprite.py:66-83 |
| F-33 | undocumented | medium | Bake IK to Keyframes button | Panel draws a fourth Pose-mode operator the doc never lists; doc Pose Mode section names only Bake Current Pose, Toggle IK, Save Pose to Library. | apps/blender/panels/skeleton.py:182; doc 04-skeleton.md:11 |
| F-34 | drift | medium | Bake Current Pose button | Its own bl_description says it keys 'the first armature in the scene', but execute() keys context.active_object - the active armature, not necessarily the first. Doc says 'every bone at the playhead' (active is correct); the description string is the diverging artifact. | apps/blender/operators/pose_library.py:122-138 |
| F-35 | suspected-bug | medium | Bake Current Pose button | Inserts keyframes on BOTH rotation_quaternion AND rotation_euler for every bone regardless of bone.rotation_mode, producing redundant/garbage fcurves on the unused rotation channel (only one is the live rotation source). | apps/blender/operators/pose_library.py:143-145 |
| F-36 | drift | low | Toggle IK button (chain length) | Doc calls it 'a test IK constraint' with no chain length; bl_description hardcodes 'chain length 2'. The operator exposes a chain_length IntProperty (default 2) via F3/redo, undocumented and not surfaced in the panel. | apps/blender/operators/armature/authoring_ik.py:86-91 |
| F-37 | undocumented | low | Active Armature picker + Exports readout + presence warnings | Doc 'Armature' section describes only the bone list; the picker dropdown, 'Exports:' label, 'no Armature in scene', 'no rig picked' box and the per-armature 'Use existing' buttons (set_active_armature) are undocumented. | apps/blender/panels/skeleton.py:94-120 |
| F-38 | undocumented | low | Quick Armature chords X/Z, Ctrl, Ctrl+Z, Enter, Alt | 04-skeleton.md only mentions options (front-ortho lock, chain default, name prefix, grid snap) and defers the chord cheatsheet to a walkthrough link; axis lock, in-modal undo/redo, disconnected (Alt), confirm (Enter), and the overlay/cheatsheet surfaces are undocumented here. | apps/blender/operators/armature/quick_armature.py:233-264, _status_bar.py:40-47 |
| F-39 | drift | low | Quick Armature option: Lock to Front Orthographic | The panel exposes the PG default (scene.proscenio.quick_armature.lock_to_front_ortho) but invoke() only reads default_chain/name_prefix/snap_increment from the PG - lock_to_front_ortho is NOT read from the PG at invoke; the operator's own BoolProperty default (True) governs each run, so toggling the panel option has no effect unless overridden via F3-redo. | apps/blender/operators/armature/quick_armature.py:200-221 |
| F-40 | dead | low | Preview Camera (authoring_camera.create_ortho_camera) | Listed for this surface but not drawn anywhere in skeleton.py; it is rendered only by the Helpers panel. Unreachable from the Skeleton surface. | apps/blender/panels/skeleton.py (absent); apps/blender/panels/helpers.py:32 |
| F-41 | dead | low | Set Bone Mode (skinning.set_bone_mode) | Listed for this surface but is an INTERNAL Skinning operator (poll requires active MESH) drawn by the Skinning panel's bind sub-box, not the Skeleton panel. Unreachable from this surface. | apps/blender/operators/skinning/set_bone_mode.py:31,47-50 |
| F-42 | suspected-bug | medium | Quick Armature modal (ClassVar modal state) | All modal/session state lives in ClassVars on PROSCENIO_OT_quick_armature (e.g. _session_records, _drag_head, _axis_lock). Two concurrent invocations (e.g. two 3D viewports) would share/clobber the same state; invoke() mitigates by sweeping stale handlers but cannot isolate concurrent sessions. | apps/blender/operators/armature/quick_armature.py:108-144,160-166 |
| F-43 | suspected-bug | low | Save Pose to Library button | _first_writable_asset_library() reads bpy.context.preferences (global context) rather than the passed context; harmless for prefs but inconsistent with the operator's context-passing convention and could surprise under non-default context overrides. | apps/blender/operators/pose_library.py:107 |
| F-44 | suspected-bug | low | Bake IK to Keyframes button | Mutates per-bone selection (selects only chain bones via _set_bone_select) to scope nla.bake but never restores the user's prior pose-bone selection after the bake, leaving the viewport selection altered. | apps/blender/operators/armature/authoring_ik.py:201-213 |
| F-45 | suspected-bug | medium | Density follows bones (automesh_density_under_bones) interaction with bone-density build params | In SIMPLE mode _resolve_bone_segments returns None (build skips bone density), but build_automesh is also passed bone_density_radius/factor gated only on `if bone_segments`; in DENSE-with-no-armature it reports uniform fallback yet density_under_bones stays ON - the panel can show Bone radius/factor active (Dense+density on) while no picker armature exists, so the user sets values that silently no-op. | apps/blender/operators/automesh/automesh.py:228-234,281-306 |
| F-46 | drift | low | Density follows bones doc scope | Doc says 'Dense only, off by default - packs more triangles near the picker's bones'; code requires BOTH density_under_bones ON and a picker armature with deform bones, else it silently falls back to uniform density (INFO only). The doc omits the picker/deform-bone precondition. | apps/blender/operators/automesh/automesh.py:281-306 |
| F-47 | undocumented | medium | Alpha threshold / Boundary margin (annulus) / Preserve base quad / Preserve weights on regen | Four Automesh-from-Alpha fields are user-reachable and have real pipeline effects (annulus topology, AA-edge culling, quad retention, weight reproject) but the doc page lists none of them under 'Key settings'. | apps/blender/panels/mesh_generation.py:157,158,165,168 |
| F-48 | undocumented | medium | Interactive Loops / Spacing / Cut margin fields | The Automesh Interactive subpanel exposes Loops, Spacing, Cut margin and a preserve_on_regen mirror; the doc only says 'Advance through the stages' and never mentions these parameters or that Loops/Spacing apply only to DENSE. | apps/blender/panels/mesh_generation.py:198-205 |
| F-49 | undocumented | medium | Interactive modal pen gesture vocabulary | Doc describes the modal as 'Advance through the stages to cut / extend the outline and place interior points', but the entire toggle-pen interaction (Shift/Ctrl tap, X/Z axis lock, wheel/0-9 subdivisions, Alt+click delete, Ctrl+Z undo, free-draw vs click-pen, snap/merge, warn-outside-silhouette) is undocumented. | apps/blender/operators/automesh/automesh_authoring.py:458-624 / _status_bar.py:28-40 |
| F-50 | undocumented | low | Subpanel/panel header status badges + '?' help buttons | Every Mesh Generation panel and subpanel renders a feature-status badge (blender-only) and a '?' help button; the doc page never mentions the header convention. (Panel module docstring even flags the badge+help as a 'later phase'.) | apps/blender/panels/mesh_generation.py:56,92,115,138 / _helpers.py:72 |
| F-51 | drift | low | Debug stage enum labels (1-6 + Final) vs doc 'Pick a stage' | Doc speaks of picking 'a stage of the trace' generically; the enum exposes 8 discrete entries (off, raw_contours, smoothed, resampled, interior_points, bridges, fill_no_interior, final) where 'final' specifically also clears prior debug companions - behavior not surfaced in the doc. | apps/blender/operators/automesh/automesh.py:150-168 |
| F-52 | drift | low | Trace resolution cost description | Doc says higher resolution 'costs more'; the property description and operator both state cost grows QUADRATICALLY - a materially stronger warning omitted from the doc. | apps/blender/properties/scene_props.py:86-88 |
| F-53 | suspected-bug | low | Interactive subpanel 'select a mesh first' label (mesh_generation.py:213) | The subpanel poll already requires _active_is_mesh_element, so obj is always a MESH when draw runs; the `if obj is None or obj.type != 'MESH'` fallback label is effectively dead/unreachable from the panel. | apps/blender/panels/mesh_generation.py:111-114,213-214 |
| F-54 | drift | low | Interior Mode SIMPLE/DENSE default vs panel default | The one-shot operator's own interior_mode EnumProperty defaults to SIMPLE, but invoke() always overwrites it from the scene prop (automesh_interior_mode); the operator default only matters for an F3 redo with no scene PG, a corner the doc never addresses. | apps/blender/operators/automesh/automesh.py:117,184 |
| F-55 | dead | medium | 'Show provenance overlay' checkbox (Snapshot subpanel) | Toggling show_provenance_overlay outside the Edit Weights modal has no visible effect: no draw handler is added/removed on toggle. The overlay handler is only registered inside edit_weights.invoke (which also force-sets the flag ON), and unregistered on modal exit. As a standalone panel toggle it is inert. | apps/blender/panels/weight_paint.py:338 ; operators/skinning/edit_weights.py:97-99 |
| F-56 | drift | low | 'Show provenance overlay' tooltip / scene prop description | Prop description says 'The GPU draw handler ships later; this surface provides the data + toggle', but the GPU POST_VIEW draw handler is already implemented (weight_overlay.register_handler) and used by the Edit Weights modal. Description is stale. | apps/blender/properties/scene_props.py:299-307 ; core/bpy_helpers/skinning/weight_overlay.py:35 |
| F-57 | undocumented | low | Viewport display box (Weight Opacity, Zero Weights, opacity caveat) | The entire 'Viewport display' box (weight_paint_mode_opacity slider, vertex_group_user Zero Weights dropdown, Blender-145603 caveat) under Edit Weights is not mentioned anywhere in the doc page. | apps/blender/panels/weight_paint.py:303-321 |
| F-58 | undocumented | low | Per-bone Clear (X) button | The per-row Clear (X) that drops a bone override back to the bind default is not described in the doc; the doc only mentions Soft/Hard and 'no override uses the mode default'. | apps/blender/panels/weight_paint.py:241 ; operators/skinning/set_bone_mode.py:56 |
| F-59 | drift | low | Sidecar IO subpanel (doc 'Sidecar IO' section) | Doc describes a separate 'Sidecar IO' panel/section; the code folded Export/Import into the Snapshot subpanel (labelled 'Export Snapshot'/'Import Snapshot') - there is no standalone Sidecar IO subpanel. Section structure has drifted. | apps/blender/panels/weight_paint.py:357-360 |
| F-60 | drift | low | Bind button label | Doc 'Bind' section implies generic Bind; UI label is 'Bind to Picker Armature'. Bind failure hint in bind_mesh references a 'Skinning panel > Bind mode dropdown' but the panel is now the Weight Paint panel - stale panel name in the error string. | apps/blender/operators/skinning/bind_mesh.py:149 |
| F-61 | suspected-bug | medium | Bind to Picker Armature (multi-mesh bind) | execute() iterates targets calling self._bind_single, but _bind_single calls len(mesh_obj.data.vertices) and apply_bind without verifying data is a real mesh datablock; more notably, when ALL targets fail (e.g. pre-flight errors) it reports per-mesh warnings then 'bound 0 mesh(es)' and returns CANCELLED, but successes>0 returns FINISHED even if some meshes silently failed - partial failures are only surfaced as WARN, easy to miss. | apps/blender/operators/skinning/bind_mesh.py:199-212 |
| F-62 | suspected-bug | low | Copy Weights to Selected (panel button) | The panel operator button at line 151 is drawn with only icon=DUPLICATE and no text=; the visible affordance is an unlabeled icon button, while the doc treats it as a named 'Weight Transfer' action. Easy to overlook; relies on tooltip only. | apps/blender/panels/weight_paint.py:151 |
| F-63 | suspected-bug | low | Copy Weights to Selected (always FINISHED) | execute() always returns {'FINISHED'} even when no target verts were covered (all_covered False only downgrades the report to WARNING). A fully-uncovered transfer still reports FINISHED, so undo/redo treats it as a successful change with no weights applied. | apps/blender/operators/skinning/copy_weights_to_selected.py:49-51 |
| F-64 | drift | low | Bind redo max_distance vs panel Mode coverage | Doc says Proximity/Envelope/Single-nearest/Empty are 'F3-redo fallbacks', but bind_init_mode is also a first-class panel dropdown (Mode), not only F3 redo. falloff_power and max_distance, however, are only reachable via F3/F9 redo (no panel field), so the panel cannot fully configure Proximity binds. | apps/blender/panels/weight_paint.py:174 ; operators/skinning/bind_mesh.py:80-94 |
| F-65 | undocumented | low | Subpanel/panel status badges and '?' help buttons (all 5 headers) | Every subpanel header carries a feature-status badge + help button (draw_subpanel_header); none are mentioned in the doc page. | apps/blender/panels/_helpers.py:72-85 |
| F-66 | suspected-bug | low | Snapshot counts pill ('reprojected') | Doc snapshot section describes paint/seed only; counts pill also reports a 'reprojected' bucket. The provenance set {user_paint, auto_seed, reprojected} is fixed in _sidecar_counts; any other provenance string in the JSON is silently dropped from the pill, so totals may under-report verts. | apps/blender/panels/weight_paint.py:376-381 |
| F-67 | undocumented | medium | Action name row button (set_active_action) | Doc states 'Proscenio does not author animation' and frames the panel as read-only, but each row is a click-to-assign operator that mutates armature.animation_data.action - an interactive write the doc never mentions. | apps/blender/panels/animation.py:29-35; apps/blender/operators/selection.py:96-132 |
| F-68 | undocumented | low | Status badge icon (header) | Header status badge and its click-to-open status-legend behavior are not described on the doc page. | apps/blender/panels/_helpers.py:46-69 |
| F-69 | undocumented | low | Help '?' button (header) | Header help button is not mentioned on the doc page (it surfaces the 'animation' help topic). | apps/blender/panels/_helpers.py:84-85 |
| F-70 | undocumented | low | Per-row frame-range label and count label | The '[start-end]' frame-range readout and 'N action(s) total' count are visible controls with no doc coverage. | apps/blender/panels/animation.py:36,68 |
| F-71 | suspected-bug | medium | Action row button - feedback on CANCELLED paths | report_warn is gated by _min_level >= info; if the user sets the addon log preference to 'errors', the no-armature / not-found / multi-armature warnings are fully suppressed, so a CANCELLED click gives zero user feedback and the panel appears unresponsive. | apps/blender/core/_shared/report.py:50-53; apps/blender/operators/selection.py:115,119,123 |
| F-72 | drift | low | Action row button - target armature selection | bl_description says it assigns to 'the first armature in the scene' and the comment claims it mirrors the writer's primary-armature heuristic, but it simply takes armatures[0] from context.scene.objects iteration order (not the Active Armature picker nor any name/sort rule), which may not match the writer's actual primary-armature choice. | apps/blender/operators/selection.py:117,127 |
| F-73 | suspected-bug | low | Action row button - UNDO scope | Operator is REGISTER/UNDO and assigns armature.animation_data.action, but _sync_active_index writes scene.proscenio.active_action_index as a side effect; on Ctrl+Z the armature action reverts while the highlighted UIList row index may not visibly revert in lockstep, leaving the highlight and assigned action briefly out of sync. | apps/blender/operators/selection.py:105,131; selection.py:153-167 |
| F-74 | drift | low | 'N action(s) total' count vs exportable actions | Doc says the panel summarizes 'every Action in the file' the writer emits, but the list/count include orphan and zero-user actions (raw bpy.data.actions) which the writer may skip, so the count can overstate what actually exports. | apps/blender/panels/animation.py:55,68 |
| F-75 | undocumented | low | Pack padding / Pack max size / Power-of-two atlas config fields | Doc 08-atlas.md never mentions the three packer config fields (pack_padding_px, pack_max_size, pack_pot) that drive Pack Atlas behaviour. | apps/blender/panels/atlas.py:54-56; properties/scene_props.py:447-467 |
| F-76 | undocumented | low | Atlas readout labels (no atlas / packed atlas / source image / unsaved) | The discovered-atlas readout (3 label branches) and its '(unsaved)' state are not described in the doc. | apps/blender/panels/atlas.py:33-38,99 |
| F-77 | undocumented | low | Pixels-per-unit readout label | A read-only 'pixels per unit: N' row is drawn on this surface but the doc page doesn't mention it (it documents the Export-owned editable field elsewhere). | apps/blender/panels/atlas.py:39-42 |
| F-78 | undocumented | low | 'run Pack Atlas first' gating hint | The disabled hint row shown in place of Apply until a manifest exists is undocumented. | apps/blender/panels/atlas.py:61-64 |
| F-79 | suspected-bug | medium | Apply Packed Atlas (sprite with no UV layer) | _apply_to_object returns True for element_type=='sprite' regardless of whether _rewrite_uvs succeeded; a sprite with no/empty active UV layer (rewrote==False) is still counted as rewritten, gets region props set, and material relinked - the 'skipped (no UV layer)' guard only fires for non-sprite meshes. | apps/blender/operators/atlas_pack/apply.py:165-171,206-216 |
| F-80 | suspected-bug | medium | Apply Packed Atlas (Ctrl+Z vs persistent snapshot) | Apply is REGISTER/UNDO and writes the pre_pack snapshot (CP + '.pre_pack' UV layer) plus the origin marker into datablocks during execute. After Ctrl+Z, Blender's undo may roll the snapshot CP/UV-layer back out of existence, leaving the on-disk state and the doc's claim that the snapshot 'survives Ctrl+Z does not' ambiguous - the persistent-snapshot contract (Unpack) and the undoable contract (Apply) interact unpredictably; verify whether Ctrl+Z after Apply leaves a dangling pre_pack layer or removes the snapshot Unpack relies on. | apps/blender/operators/atlas_pack/apply.py:42,97-127 |
| F-81 | suspected-bug | low | Apply Packed Atlas (atlas image cache lookup) | bpy.data.images.get(atlas_png.stem) looks up the image by '<blend>.atlas' but Blender names the loaded datablock '<blend>.atlas.png'; the get() never hits, so dedup relies entirely on load(check_existing=True). Harmless because check_existing dedupes by filepath, but the stem lookup is dead. | apps/blender/operators/atlas_pack/apply.py:66-68 |
| F-82 | drift | low | Unpack Atlas (Ctrl+Z semantics) | Doc says 'Unpack Atlas reverts a previous apply from the snapshot ... Ctrl+Z does not', implying Unpack/snapshot is outside undo, yet the Unpack operator declares bl_options REGISTER/UNDO so the unpack action itself IS undoable with Ctrl+Z. The doc's 'Ctrl+Z does not' refers to the apply-snapshot persistence, not the unpack operator - wording can mislead testers. | apps/blender/operators/atlas_pack/unpack.py:47; docs/02-blender-addon/08-atlas.md:7 |
| F-83 | undocumented | low | exclude_from_atlas behaviour | Pack silently drops meshes flagged exclude_from_atlas (keeps their own UVs/texture/material). Doc mentions 'Isolated material' but never the exclude-from-atlas opt-out that governs which sprites Pack walks. | apps/blender/operators/atlas_pack/pack.py:19-33 |
| F-84 | drift | low | Status badge band (Unpack) | Atlas feature and pack/apply are marked GODOT_READY but unpack_atlas is marked BLENDER_ONLY in feature_status; the single Atlas subpanel badge shows the 'atlas' (GODOT_READY) band, so the Blender-only nature of Unpack isn't surfaced on this surface. | apps/blender/core/_shared/feature_status.py:73,89; apps/blender/panels/atlas.py:28 |
| F-85 | drift | high | Validate button / issue list | Doc claims only 4 check types (missing armature, dead bone refs, missing atlas files, sprite_frame without hframes/vframes) but validate_export also emits: bone-orientation off-XZ-plane warnings, IK-bake-needed errors, non-flat mesh warnings, sprite-UV-not-full-sheet warnings, duplicate-slot-name errors, 'no parent bone / no matching vertex groups' warnings, 'vertex groups but none resolve to bones' errors, plus active-element and active-slot validators. The doc is badly out of date with the implemented checks. | apps/blender/core/validation/export.py:42-76 |
| F-86 | drift | medium | Validate button (doc check #1 wording) | Doc describes the missing-armature error as 'a missing armature WHEN SPRITES CARRY VERTEX GROUPS', but the code raises 'scene has no Armature' unconditionally whenever the scene has zero armatures, independent of any vertex groups (export.py:52-55). | apps/blender/core/validation/export.py:52-55 |
| F-87 | drift | medium | Validate button (doc check #4 wording) | Doc says the check flags 'sprite_frame meshes without hframes/vframes', but the implemented sprite-frame UV check (_validate_sprite_frame_uvs) only warns when an auto-region multi-frame sprite's UVs do not span the full 0-1 sheet; there is no check for missing/absent hframes/vframes (a 1x1 sprite is simply skipped, not flagged). | apps/blender/core/validation/export.py:302-343 |
| F-88 | drift | medium | Validate button (atlas-missing severity) | Doc lists 'atlas image files missing from disk' among issues that 'block an export', but the atlas-missing finding is emitted as severity 'warning', which does NOT block export (only severity 'error' gates _gate_on_validation). A missing atlas exports anyway. | apps/blender/core/validation/export.py:396-401 |
| F-89 | suspected-bug | medium | Issue row (clickable) -> Select Issue Object | PROSCENIO_OT_select_issue_object -> select_only() calls obj.select_set()/view_layer.objects.active while the user is in a non-OBJECT mode (e.g. Edit/Pose on a different object). select_set can raise RuntimeError 'Object can't be selected because it is not in View Layer' or be disallowed in restricted contexts; unlike restore_selection (which wraps these in contextlib.suppress), this path is unguarded and would surface a Python traceback in the info bar. | apps/blender/operators/selection.py:31-37 -> apps/blender/core/bpy_helpers/_shared/select.py:32-35 |
| F-90 | undocumented | low | Status badge (header) | The godot-ready status badge and its click-to-open-status-legend / hover-tooltip behavior on the Validation header are not mentioned anywhere in 09-validation.md. | apps/blender/panels/_helpers.py:46-69 |
| F-91 | undocumented | low | Help '?' button (header) | The '?' help button on the Validation header is undocumented in the page itself (the page is the help topic source but never describes the affordance). | apps/blender/panels/_helpers.py:84-85 |
| F-92 | undocumented | low | Empty-state / success / guard labels | The three non-issue labels ('proscenio scene props not registered', 'run Validate to see issues', 'no issues - ready to export') are user-visible states never described in the doc. | apps/blender/panels/validation.py:27,34,39 |
| F-93 | drift | low | Validation panel header | Doc says 'Errors block the export; warnings are informational' but the panel itself renders no error/warning count badge or summary header; the only error/warning tally is the transient info-bar report from the Validate operator. A user reopening the panel sees rows but no aggregate count. | apps/blender/panels/validation.py:42-43 |
| F-94 | suspected-bug | high | Pixels per unit (panel field) vs Export (.proscenio) | First Export ignores the panel/scene pixels_per_unit: PROSCENIO_OT_export_godot uses its own ExportHelper FloatProperty (default 100) at export_flow.py:167, not scene_props.pixels_per_unit edited in the panel. Editing the panel field has no effect on the initial Export (only Re-export at line 199 reads the scene value), contradicting the doc's claim that 'Pixels per unit sets the ratio'. | apps/blender/operators/export_flow.py:158-163,167; apps/blender/panels/pipeline.py:89 |
| F-95 | drift | low | Export (.proscenio) - 'next to the .blend' | Doc says export writes the JSON 'next to the .blend', but the operator writes to the user-chosen file-dialog path (self.filepath), which need not be beside the .blend; the dialog default is whatever ExportHelper seeds, not the .blend directory. | apps/blender/operators/export_flow.py:165-174 |
| F-96 | drift | low | Export (.proscenio) - 'validates against the schema' | Doc says export 'validates against the schema'; the gate actually runs validation.validate_export (scene walk: sprites vs armature, atlas files) and blocks on error-severity issues - it is not a JSON-schema validation of the output. Terminology drift. | apps/blender/operators/export_flow.py:58-70,88 |
| F-97 | undocumented | medium | Bundle textures (checkbox) | The bundle_textures scene toggle and its export-time texture copying are entirely absent from the pipeline doc. | apps/blender/panels/pipeline.py:90; apps/blender/operators/export_flow.py:97-118 |
| F-98 | undocumented | low | Import Placement enum (Landed / Centered) | The Placement enum (default 'landed', anchors feet at Z=0) is a user-facing import option not mentioned in the doc. | apps/blender/operators/import_photoshop.py:40-60 |
| F-99 | undocumented | low | Import Root Bone Name field | The root_bone_name override (default 'root') is a user-facing import option not mentioned in the doc. | apps/blender/operators/import_photoshop.py:62-70 |
| F-100 | undocumented | low | Subpanel header status badges + '?' help buttons | Every subpanel header (Pipeline/Import/Export) carries a status badge and a '?' help popup; the panel module docstring itself flags these as a later 'header-convention pass' and the pipeline doc never documents them. | apps/blender/panels/pipeline.py:35-36,54-55,80-81; apps/blender/panels/_helpers.py:72-85 |
| F-101 | drift | low | Re-import reuse claim | Doc states 're-importing the same manifest reuses existing meshes, so rotation, parenting, and weights survive'. The orchestrator import_manifest always calls build_root_armature to create a FRESH armature (importers/photoshop/__init__.py:70-73) on every run; mesh reuse depends on stamp_mesh/stamp_sprite internals (not in the listed files). Reviewer should verify the round-trip reuse actually holds, as the armature is unconditionally rebuilt. | apps/blender/importers/photoshop/__init__.py:68-91 |
| F-102 | suspected-bug | low | Pixels per unit sync on import overrides user edits silently | _sync_scene_pixels_per_unit unconditionally overwrites scene.proscenio.pixels_per_unit with the manifest value on every import (importers/photoshop/__init__.py:107), discarding any user-set panel value with no report/warning. Undocumented side-effect of the import button. | apps/blender/importers/photoshop/__init__.py:94-107 |
| F-103 | undocumented | low | Status badge icon (Helpers header) | The doc page 11-helpers.md never mentions the per-panel status badge or its hover-tooltip/click-to-legend behavior; only the help_topics legend explains it. | apps/blender/panels/_helpers.py:46-69; docs/02-blender-addon/11-helpers.md |
| F-104 | undocumented | low | Help '?' button (Helpers header) | The doc page does not mention the in-panel '?' help popup affordance present on every Proscenio subpanel header. | apps/blender/panels/_helpers.py:84-85; docs/02-blender-addon/11-helpers.md |
| F-105 | undocumented | medium | Preview Camera (re-run / focus behavior, naming, report) | Doc says only 'drops an orthographic front camera'; it omits that the camera is named 'Proscenio.PreviewCam', that re-running focuses/updates the existing camera (ortho_scale recomputed from pixels_per_unit and render resolution), that it becomes scene.camera + sole selection, and that ortho_scale derives from pixels_per_unit - none of which the user can learn from the doc. | apps/blender/operators/armature/authoring_camera.py:31-52 |
| F-106 | drift | low | Preview Camera (doc_url target vs section anchor) | Help topic 'helpers' doc_url resolves to '.../blender-addon/helpers' (a page-level link); the doc page is a 5-line stub with no anchors, so 'Open online docs' lands on the page top - acceptable but the doc provides almost none of the operator's documented detail (pixels_per_unit-derived ortho_scale, Numpad 0 hint live only in the operator tooltip/help_topics, not the doc). | apps/blender/core/help_topics.py:880; docs/02-blender-addon/11-helpers.md:1-5 |
| F-107 | suspected-bug | low | Preview Camera (degenerate ortho_scale when resolution or ppu is zero) | ortho_scale = max(resolution_x, resolution_y) / ppu with no guard: if pixels_per_unit is 0 this raises ZeroDivisionError and the operator aborts; pixels_per_unit FloatProperty has no documented min clamp shown here, so a user-entered 0 breaks the button. Resolution is normally >=1 so that side is safe. | apps/blender/operators/armature/authoring_camera.py:30-31 |
| F-108 | drift | medium | Diagnostics header '?' help button | Doc (index:26) promises the '?' opens 'the matching help' for the panel, but diagnostics.py:29 hard-codes help_topic='pipeline_overview'; there is no 'diagnostics' HELP_TOPICS entry, so the generic pipeline overview opens instead. | apps/blender/panels/diagnostics.py:29 |
| F-109 | drift | medium | Help header '?' help button | Same as Diagnostics: help.py:44 passes help_topic='pipeline_overview' with no 'help' topic in HELP_TOPICS, so the '?' opens the generic overview rather than help-panel-specific help. | apps/blender/panels/help.py:44 |
| F-110 | undocumented | medium | Diagnostics panel + Run Smoke Test | The doc index sidebar list (panels 01-11) never lists a Diagnostics panel and the smoke-test operator is undocumented on the reference page; only the addon-prefs prop description mentions Diagnostics exists. | apps/blender/panels/diagnostics.py:13-34 |
| F-111 | undocumented | medium | Help panel (operator cheat-sheet) | The Help subpanel and its 18-row operator/idname cheat-sheet are absent from the doc index sidebar list; only the in-code docstring describes them. | apps/blender/panels/help.py:32-52 |
| F-112 | undocumented | low | Addon Preferences (Log level + Debug mode) | The addon preferences surface (Developer box, Log level enum, Debug mode checkbox) is never mentioned on docs/02-blender-addon/index.md - only in-code prop descriptions document it. | apps/blender/addon_prefs.py:60-64 |
| F-113 | suspected-bug | low | Run Smoke Test report | Smoke test reports via raw self.report({'INFO'}, message) bypassing report_info, so it (a) ignores the Log level gate (still prints at 'Errors only') and (b) omits the standard 'Proscenio: ' prefix every other operator uses; minor inconsistency with the report-gate design. | apps/blender/operators/help_dispatch.py:110 |
| F-114 | dead | low | Help panel operator-reference rows | Each cheat-sheet row is rendered as two plain layout.label() calls (label + idname), not as a clickable operator button - so the 'cheat-sheet' is read-only; users must still type into F3 manually (the panel's stated purpose is satisfied but the rows are non-interactive no-ops). | apps/blender/panels/help.py:50-52 |
| F-115 | drift | low | Diagnostics panel ('future addon-health buttons') | The panel docstring/bl description advertises 'Smoke test + future addon-health buttons' but draw() renders only the single smoke-test button; the promised health buttons are not implemented (placeholder copy). | apps/blender/panels/diagnostics.py:31-33 |
| F-116 | suspected-bug | low | Status badge icon fallback (planned / out-of-scope bands) | For non-godot/non-blender bands _draw_status_button sets icon_id=0 and falls back to badge.icon (EXPERIMENTAL/CANCEL); harmless here, but note Diagnostics+Help are both BLENDER_ONLY so they always use the custom Blender preview - if previews failed to load (headless/missing png) the TOOL_SETTINGS built-in is used, making the godot-ready vs blender-only marks visually indistinguishable from the planned/out-of-scope fallbacks in that degraded state. | apps/blender/panels/_helpers.py:59-68 |
