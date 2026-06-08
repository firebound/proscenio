# Current UI inventory (Blender addon sidebar)

Faithful catalogue of what the `Proscenio` N-panel tab renders today, in registration order. Code-grounded (read from `apps/blender/panels/`), no redesign. This is the baseline the IA redesign builds on.

Badge column: `godot` = GODOT_READY (exports to `.proscenio`), `blender` = BLENDER_ONLY (authoring), `-` = no status badge drawn today. `?` = has a help button. "When" = the panel `poll()` condition. "Open" = expanded by default (no `DEFAULT_CLOSED`).

## Root

- **`PROSCENIO_PT_main`** - the tab anchor. Draws only `Pipeline v0.1.0` + a root `?` (topic `pipeline_overview`). Every panel below is a child via `bl_parent_id="PROSCENIO_PT_main"`, which is why they all visually indent under the version line.

## Panels (registration order)

### 1. Active Element - `godot` `?` - when: active object is MESH, modes object/edit-mesh/paint-weight/paint-vertex

- `Element type` selector (Mesh / Sprite) - `godot`
- if Sprite: **Sprite frame** box - `blender` `?` (feature `sprite_frame_preview`): hframes / vframes / frame / centered + readout (atlas / region / frame grid) + [Setup Preview] [Remove Preview]
- if Mesh: **Mesh** box - `-`: "N polygon(s), M vertex group(s)" + [Reproject UV] (`blender`) + [ ] Isolated material
- if Weight Paint mode: **Weight paint** box - `-`: brush size / strength / weight / auto-normalize (mirror of native brush)
- **Texture region** box - `-`: region_mode auto/manual + region_x/y/w/h + [Snap to UV bounds] (`blender`, mesh only)
- **Drive from bone** box - `blender` `?`: Target / Armature / Bone / Axis / Expression + [Drive from Bone]
- inline validation issues

### 2. Active Slot - `godot` `?` - when: active object is EMPTY with `is_slot`

- "Slot '<name>'" + "bone: <parent_bone / unparented>"
- Attachments (N): list with default-star toggle + name + kind icon
- [Add Selected Mesh]
- inline validation issues

### 3. Skeleton - `godot` `?` - when: modes object/pose/edit-armature

- active-armature picker (always)
- bone UIList (click selects bone) + "Armature 'X' - N bone(s)" - `godot`
- if Pose mode: [Bake Current Pose] [Toggle IK] [Save Pose to Library] - all `blender`
- [Quick Armature] (`blender`) + **Quick Armature defaults** box (lock front ortho / default_chain / name_prefix / snap_increment)
- **[Create Slot]** (`godot`) - slot creation lives here, not in Active Slot

### 4. Skinning - `blender` (fallback) `?` - when: active object is MESH

- Note: badge falls back to blender-only because `skinning` is absent from `feature_status`; yet Bind produces weights that DO export.
- Picker readout ("Picker: <arm>" / "(none - set in Skeleton)")
- **Automesh from sprite** box - `-`: ~10 props + [Automesh from Sprite]
- **Automesh authoring** box - `-`: loops / spacing / cut_margin + [Automesh (modal)]
- **Bind to picker** box - `godot`: Mode + [Bind to Picker Armature] + per-bone Soft/Hard overrides
- **Edit Weights** box - `-`: active group + [Edit Weights] + brush curve presets
- **Weight transfer** box - `-`: [Copy Weights to Selected]
- **Snapshot** box - `-`: preserve_on_regen / provenance overlay / counts pill + [Reset to Last Saved Weights]
- **Sidecar IO** box - `-`: [Export] [Import]
- **Debug pipeline** box - `-`: stage enum + [Clear Debug Companions]

### 5. Outliner - `blender` `?` - when: always

- search (outliner_filter) + favorites toggle
- UIList: slots / attachments / sprites / armatures (category icons) + per-row favorite star

### 6. Animation - `godot` `?` - when: always

- actions UIList (name + frame range, click sets active action) + "N action(s) total"

### 7. Atlas - `godot` `?` - when: always

- discovered atlas-name readout
- **Atlas packer** box: padding / max_size / pot + [Pack Atlas] [Apply Packed Atlas] [Unpack Atlas (`blender`)]

### 8. Validation - `godot` `?` - when: always - **Open**

- "run Validate to see issues" / clickable issue list / "no issues - ready to export"
- Note: no Validate button here - the button lives in Export.

### 9. Export - `godot` `?` - when: always - **Open**

- last_export_path + pixels_per_unit
- [Preview Camera] (create_ortho_camera, `blender`)
- **[Validate]** (`godot`) - validate button lives here + [Export (.proscenio)] + [Re-export]
- **[Import Photoshop Manifest]** (`blender`) - PS import lives here

### 10. Help - `-` (no badge, no `?`) - when: always

- table of 17 operators (label + idname), "use F3 to search"

### 11. Diagnostics - `-` (no badge, no `?`) - when: always

- [Run Smoke Test]

## Cross-tool placement notes (design-relevant)

Where an operator lives today vs where a user might look for it:

- **Create Slot** - in Skeleton (not Active Slot).
- **Validate** button - in Export (not Validation).
- **Preview Camera** + **Import Photoshop Manifest** - in Export.
- **Weight paint** brush controls - inline in Active Element (mesh body, paint-weight mode), separate from the Skinning panel.
- **Quick Armature**, **Toggle IK**, **Bake Pose**, **Save Pose** - all in Skeleton.

## Badge / affordance gaps (faithful, not yet judged)

- `skinning` not in `feature_status` -> header badge falls back to blender-only despite Bind exporting weights.
- No badge/`?` on: Texture region box, every Skinning sub-box, Help panel header, Diagnostics panel header.
- Help panel is a flat operator/idname table, not the popup-style help the `?` buttons open.
