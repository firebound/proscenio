# Godot manual-test checklist

Standing manual-test surface for the Godot plugin: import/reimport, the builders, and wrapper-scene safety, each audited against its documented intent.

## Surface tokens

| Token | Panel / section |
| --- | --- |
| IMPORT | Godot import/reimport: EditorImportPlugin, reimporter, plugin registration, wrapper-scene safety, import order |
| BUILD | Godot builders: skeleton, sprite, mesh, slot, animation -> node tree |

## Godot import/reimport: EditorImportPlugin, reimporter, plugin registration, wrapper-scene safety, import order

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| GD-IMPORT-01 | Importer entry "Proscenio Character" in the Import dock | Import tab shows "Import As: Proscenio Character" as the importer with a "Default" preset; .proscenio recognized (not 'keep file'). | A single EditorImportPlugin that turns a .proscenio file into a native Godot scene on every reimport. | apps/godot/addons/proscenio/importer.gd:17-18 | pending |
| GD-IMPORT-02 | Recognized extension (.proscenio) | Godot routes foo.proscenio through this importer; a foo.proscenio.scn artifact appears under .godot/imported (or the file imports without 'unrecognized' warning). | The plugin claims files with the proscenio extension so they import as characters. | apps/godot/addons/proscenio/importer.gd:21-22 | pending |
| GD-IMPORT-03 | Save extension / resource type (.scn -> PackedScene) | Imported resource is a PackedScene saved with .scn; instancing it yields plain Node2D/Skeleton2D/Bone2D/Polygon2D/Sprite2D/AnimationPlayer with no GDExtension dependency. | Regenerates a scene as plain Godot 4 nodes with no runtime dependency. | apps/godot/addons/proscenio/importer.gd:25-31 | pending |
| GD-IMPORT-04 | Preset dropdown ("Default") | Exactly one preset named "Default" is offered; selecting it changes nothing (no options follow). | UNDOCUMENTED | apps/godot/addons/proscenio/importer.gd:41-46 | pending |
| GD-IMPORT-05 | Import options list (empty) | No per-import options are shown (no checkboxes/fields); the options area is empty though _get_option_visibility returns true. | UNDOCUMENTED | apps/godot/addons/proscenio/importer.gd:49-54 | pending |
| GD-IMPORT-09 | Owner assignment (scene packs cleanly) | All descendant nodes are visible/persisted (owner = root) and PackedScene.pack returns OK; no nodes are dropped on save. | Generated scene runs standalone as plain Godot nodes. | apps/godot/addons/proscenio/importer.gd:91-96 | pending |
| GD-IMPORT-10 | Overwrite-existing-scene notice (print_verbose) | Verbose log prints "Proscenio: regenerating <path>.scn (existing scene will be overwritten)"; the prior .scn is replaced wholesale. | UNDOCUMENTED | apps/godot/addons/proscenio/importer.gd:99-102 | pending |
| GD-IMPORT-11 | format_version gate error | Import fails (ERR_INVALID_DATA); error log: "Proscenio: unsupported format_version N (need 1)"; no scene generated. | The importer checks the format_version before building. | apps/godot/addons/proscenio/importer.gd:136-143 | pending |
| GD-IMPORT-12 | Unopenable source-file error | push_error "Proscenio: cannot open '<path>' (error N)"; _import returns ERR_INVALID_DATA. | Reads the document; reports failures so import returns a single error code. | apps/godot/addons/proscenio/importer.gd:109-114 | pending |
| GD-IMPORT-13 | JSON parse-failure error | push_error "Proscenio: JSON parse failed at line L: <msg>"; import returns ERR_INVALID_DATA; no scene built. | Reads the document as typed Resource after parsing JSON. | apps/godot/addons/proscenio/importer.gd:116-125 | pending |
| GD-IMPORT-14 | Non-object root error | push_error "Proscenio: expected JSON object at document root"; import returns ERR_INVALID_DATA. | Expects a JSON object at the document root. | apps/godot/addons/proscenio/importer.gd:127-129 | pending |
| GD-IMPORT-15 | from_dict null-return error | push_error from element dispatch then "Proscenio: ProscenioDocument.from_dict returned null"; import returns ERR_INVALID_DATA. | Reads the document as a typed Resource (ProscenioDocument.from_dict). | apps/godot/addons/proscenio/importer.gd:132-135 | pending |
| GD-IMPORT-16 | Atlas resolution (document.atlas) | Texture loaded with CACHE_MODE_REPLACE and applied to elements lacking a per-sprite texture. | Builds the atlas (texture) used by sprites/meshes during import. | apps/godot/addons/proscenio/importer.gd:147-167 | pending |
| GD-IMPORT-17 | Atlas-not-found warning | push_warning "Proscenio: atlas not found at '<full>'"; import still succeeds; elements fall back to per-sprite/by-name textures or none. | UNDOCUMENTED | apps/godot/addons/proscenio/importer.gd:152-154 | pending |
| GD-IMPORT-18 | Atlas wrong-type error | push_error "Proscenio: '<full>' loaded but not Texture2D - got <class>"; atlas treated as null; import continues. | UNDOCUMENTED | apps/godot/addons/proscenio/importer.gd:161-166 | pending |
| GD-IMPORT-21 | Import priority (_get_priority = 1.0) | Priority 1.0; this importer is the sole/winning claimant for .proscenio. | UNDOCUMENTED | apps/godot/addons/proscenio/importer.gd:33-34 | pending |
| GD-IMPORT-22 | Import order (_get_import_order = 0) | Importer runs at order 0; atlas textures it depends on must already be imported (no explicit ordering guarantee that textures precede order-0 proscenio import). | UNDOCUMENTED | apps/godot/addons/proscenio/importer.gd:37-38 | pending |
| GD-IMPORT-25 | Plugin metadata (plugin.cfg name/description/version) | Entry "Proscenio" by Space Wizard Studios, version 0.1.0, description mentioning Skeleton2D+Bone2D+Polygon2D+AnimationPlayer; script points to plugin.gd. | UNDOCUMENTED | apps/godot/addons/proscenio/plugin.cfg:1-7 | pending |

#### [ ] GD-IMPORT-06 · Reimport button (full scene regeneration)
- **Intent:** Regenerate the scene (Skeleton2D + Bone2D + Polygon2D/Sprite2D + AnimationPlayer) whenever a .proscenio enters or changes.
- **Code:** apps/godot/addons/proscenio/importer.gd:57-103
- **Pre:** A valid format_version=1 .proscenio in res://, plugin enabled.
- **Steps:** Select the .proscenio in FileSystem > Import tab > click Reimport (or edit/save the .proscenio to trigger auto-reimport).
- **Expect:** A new .scn is built: root Node2D named after document.name (else "Character"), with Skeleton2D, AnimationPlayer, and element nodes; ResourceSaver.save returns OK; the imported scene reflects the new data.
- **Status:** pending

#### [ ] GD-IMPORT-07 · Build order: skeleton -> atlas -> slots -> mesh/sprite elements -> animation
- **Intent:** Builds the node tree in order: skeleton, atlas, slots before sprites, sprites, animation.
- **Code:** apps/godot/addons/proscenio/importer.gd:72-89
- **Pre:** A .proscenio containing skeleton, slots, mesh+sprite elements, and animations.
- **Steps:** Import a document exercising all sections > open the generated scene tree.
- **Expect:** Skeleton2D added first; slot Node2D anchors exist before element nodes so slotted elements parent under the slot Node2D; AnimationPlayer present last with tracks resolving to the built nodes.
- **Status:** pending

#### [ ] GD-IMPORT-08 · Slot-vs-bone routing fallback (empty slot map)
- **Intent:** No slots leaves the map empty and routing falls back to bone-parenting.
- **Code:** apps/godot/addons/proscenio/importer.gd:80-84
- **Pre:** A .proscenio with elements but no slots[] section.
- **Steps:** Import a document with elements and no slots > inspect element parents in the generated scene.
- **Expect:** Each non-skinned element parents under its named Bone2D (or skeleton root); skinned meshes stay under Skeleton2D; no slot Node2D anchors exist.
- **Status:** pending

#### [ ] GD-IMPORT-19 · Wrapper-scene safety (user wrapper survives reimport)
- **Intent:** A user-authored wrapper scene that instances the generated one survives every reimport, so scripts and gameplay nodes are never clobbered.
- **Code:** apps/godot/addons/proscenio/importer.gd:98-103
- **Pre:** A wrapper scene instances the generated foo.proscenio.scn and adds a script + child gameplay nodes.
- **Steps:** Create wrapper.tscn instancing the generated scene > add a script and extra nodes > edit/reimport the .proscenio.
- **Expect:** wrapper.tscn is untouched; only the instanced generated subtree updates; user script and added nodes persist (relies on Godot scene-instance inheritance, not on reimporter.gd).
- **Status:** pending

#### [ ] GD-IMPORT-20 · Non-destructive reimporter (diff/merge)
- **Intent:** Diff the existing imported scene against new .proscenio data, preserving user-added nodes, scripts and custom animations while replacing source-driven content.
- **Code:** apps/godot/addons/proscenio/reimporter.gd:1-10
- **Pre:** An imported scene the user has hand-edited (added nodes/animations directly).
- **Steps:** Edit the imported scene directly > reimport the .proscenio.
- **Expect:** Per the doc, a diff/merge preserves user edits. In reality reimporter.gd is an unimplemented stub (RefCounted, no code); nothing diff-merges. Confirm no diff behavior occurs.
- **Status:** pending

#### [ ] GD-IMPORT-23 · Plugin registration (_enter_tree add_import_plugin)
- **Intent:** The plugin registers a single EditorImportPlugin.
- **Code:** apps/godot/addons/proscenio/plugin.gd:9-11
- **Pre:** Plugin listed in project.godot [editor_plugins] enabled.
- **Steps:** Open the project (or toggle the plugin on in Project Settings > Plugins).
- **Expect:** On enter_tree the importer is constructed and add_import_plugin called; "Proscenio Character" becomes selectable as an importer.
- **Status:** pending

#### [ ] GD-IMPORT-24 · Plugin teardown (_exit_tree remove_import_plugin)
- **Intent:** UNDOCUMENTED
- **Code:** apps/godot/addons/proscenio/plugin.gd:14-17
- **Pre:** Plugin currently enabled.
- **Steps:** Disable the plugin in Project Settings > Plugins (or close the project).
- **Expect:** remove_import_plugin called and _importer cleared; "Proscenio Character" importer no longer offered; no leak/errors.
- **Status:** pending

## Godot builders: skeleton, sprite, mesh, slot, animation -> node tree

| ID | Control | Expect | Intent | Code | Status |
| --- | --- | --- | --- | --- | --- |
| GD-BUILD-02 | Bone position field | Bone2D.position == (10,20). Missing/short array (<2) yields Vector2.ZERO. | UNDOCUMENTED (doc names Bone2D as a node type only, not the position field). | apps/godot/addons/proscenio/builders/skeleton_builder.gd:20 | pending |
| GD-BUILD-03 | Bone rotation field | Bone2D.rotation == 1.57 rad. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/skeleton_builder.gd:21 | pending |
| GD-BUILD-04 | Bone scale field | Bone2D.scale == (2,2). Missing/short array defaults to (1,1). | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/skeleton_builder.gd:22 | pending |
| GD-BUILD-05 | Bone length field | Bone2D length set to authored value and autocalculate_length_and_angle disabled. length==0 leaves Godot autocalc on. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/skeleton_builder.gd:23-27 | pending |
| GD-BUILD-06 | Bone rest pose capture | Bone2D.get_rest() equals the authored transform (so animation value tracks replace it cleanly). | UNDOCUMENTED (doc says animations replace pose; rest-capture mechanism not documented). | apps/godot/addons/proscenio/builders/skeleton_builder.gd:29 | pending |
| GD-BUILD-08 | Bone name (unsanitized dict key, sanitized node name) | Bone2D.name == 'upper_arm_L' (dot->underscore), but parent lookup keys on original 'upper_arm.L'. | UNDOCUMENTED (dotted-name normalization is an internal note, not user doc). | apps/godot/addons/proscenio/builders/skeleton_builder.gd:15-19,30 | pending |
| GD-BUILD-11 | Slot missing-name guard | Warning 'slot entry missing name - skipping'; no Node2D created, attachments not mapped. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/slot_builder.gd:38-40 | pending |
| GD-BUILD-12 | Slot bone resolution / missing bone fallback | Warning 'references missing bone ... anchoring at skeleton root'; Node2D parented to Skeleton2D. | Slot anchors under its Bone2D; doc does not describe the missing-bone fallback. | apps/godot/addons/proscenio/builders/slot_builder.gd:45-61 | pending |
| GD-BUILD-15 | Mesh polygons (multi-face) field | Polygon2D.polygons holds each face index array. Empty polygons => single ring renders whole shape. | UNDOCUMENTED (multi-face per-face arrays not in doc). | apps/godot/addons/proscenio/builders/mesh_builder.gd:67-71 | pending |
| GD-BUILD-16 | Mesh UV scaling to pixel space | UVs multiplied by texture size (pixel space). With no texture, raw [0,1] UVs are kept. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/mesh_builder.gd:77-85 | pending |
| GD-BUILD-17 | Mesh modulate / z_index | Polygon2D.modulate set when modulate has >=4 entries (else default white); z_index applied. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/mesh_builder.gd:92-96 | pending |
| GD-BUILD-21 | Sprite hframes / vframes / frame | Sprite2D.hframes==4, vframes==1, frame==2. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/sprite_builder.gd:43-45 | pending |
| GD-BUILD-22 | Sprite centered toggle | Sprite2D.centered matches authored bool (default false). | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/sprite_builder.gd:46 | pending |
| GD-BUILD-23 | Sprite offset | Sprite2D.offset == (5,5) when offset has >=2 entries. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/sprite_builder.gd:48-49 | pending |
| GD-BUILD-24 | Sprite texture_region (region_enabled + filter clip) | region_enabled==true, region_filter_clip_enabled==true, region_rect == (0,0,32,32). Absent -> full texture. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/sprite_builder.gd:53-63 | pending |
| GD-BUILD-25 | Sprite modulate / z_index | Sprite2D.modulate set when >=4 entries (else default white); z_index applied. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/sprite_builder.gd:67-74 | pending |
| GD-BUILD-26 | Sprite flip_h / flip_v | Sprite2D.flip_h==true, flip_v==true (default false). | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/sprite_builder.gd:75-76 | pending |
| GD-BUILD-30 | Animation length / loop_mode | Animation.length set; loop_mode == LOOP_LINEAR when loop true, else LOOP_NONE. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/animation_builder.gd:28-30 | pending |
| GD-BUILD-34 | Unknown track type handling | Warning 'unknown track type bogus'; no track added; rest of animation unaffected. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/animation_builder.gd:85-86 | pending |
| GD-BUILD-35 | Empty-keys track guard | Track silently skipped (early return), no track added. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/animation_builder.gd:43-44 | pending |
| GD-BUILD-36 | skeleton-has-no-parent guard for animation paths | push_error 'skeleton has no parent'; track resolution aborts for that track. | UNDOCUMENTED. | apps/godot/addons/proscenio/builders/animation_builder.gd:46-49 | pending |
| GD-BUILD-38 | Document name -> root node name | Root Node2D named after document.name, or 'Character' when name empty. | UNDOCUMENTED (root naming default). | apps/godot/addons/proscenio/importer.gd:69-70 | pending |

#### [ ] GD-BUILD-01 · Skeleton2D root build (SkeletonBuilder.build)
- **Intent:** Plugin regenerates a scene whose skeleton is built first in order; null skeleton still yields a Skeleton2D node.
- **Code:** apps/godot/addons/proscenio/builders/skeleton_builder.gd:5-44
- **Pre:** A .proscenio file in the project; reimport triggered
- **Steps:** Author a .proscenio with a skeleton block > reimport > open generated .scn
- **Expect:** Root Node2D contains a child named 'Skeleton2D'. With no skeleton block the Skeleton2D still appears (empty).
- **Status:** pending

#### [ ] GD-BUILD-07 · Bone parent resolution / tree nesting
- **Intent:** Skeleton built in order; bones nest into a tree by parent reference (Bone2D under Bone2D).
- **Code:** apps/godot/addons/proscenio/builders/skeleton_builder.gd:32-42
- **Pre:** Skeleton with >=2 bones, child references parent by exact JSON name
- **Steps:** Author bone B with parent A > reimport > inspect tree
- **Expect:** B is a child of A. Empty parent string roots B at Skeleton2D. Parent name not found also roots at Skeleton2D (silent fallback).
- **Status:** pending

#### [ ] GD-BUILD-09 · Atlas load (importer._load_atlas)
- **Intent:** Importer reads atlas before slots/sprites; atlas is the scene-wide fallback texture.
- **Code:** apps/godot/addons/proscenio/importer.gd:75,147-167
- **Pre:** .proscenio with document.atlas path next to file
- **Steps:** Set document.atlas to a sibling png > reimport
- **Expect:** Atlas Texture2D loaded and passed to element builders. Empty atlas -> null; missing path -> warning + null; non-texture -> error + null.
- **Status:** pending

#### [ ] GD-BUILD-10 · Slot anchor build (SlotBuilder.build)
- **Intent:** Slots build BEFORE sprites; each slot becomes a Node2D under its Bone2D (or Skeleton2D when bone empty).
- **Code:** apps/godot/addons/proscenio/builders/slot_builder.gd:22-66
- **Pre:** .proscenio with a slots[] entry having name + attachments[]
- **Steps:** Author a slot with bone and attachments > reimport > inspect tree
- **Expect:** A Node2D named after the (sanitized) slot appears under the named Bone2D; under Skeleton2D root if bone empty or bone missing (with warning).
- **Status:** pending

#### [ ] GD-BUILD-13 · Slot attachment map / default attachment visibility
- **Intent:** Default attachment starts visible, others hidden until slot_attachment track flips them.
- **Code:** apps/godot/addons/proscenio/builders/slot_builder.gd:32-34,65; sprite_attach_util.gd:50-54
- **Pre:** Slot with multiple attachments[], a default set; elements named to match attachments
- **Steps:** Author slot default='headA' with attachments [headA,headB]; add sprite/mesh elements headA,headB > reimport
- **Expect:** headA and headB parent under the slot Node2D; headA visible==true, headB visible==false.
- **Status:** pending

#### [ ] GD-BUILD-14 · Mesh element build (MeshBuilder.attach_elements -> Polygon2D)
- **Intent:** Sprites built as Polygon2D for mesh-type elements; type absent defaults to mesh.
- **Code:** apps/godot/addons/proscenio/builders/mesh_builder.gd:32-71; proscenio_element.gd:15-17
- **Pre:** element with type 'mesh' (or omitted) and a polygon ring
- **Steps:** Author a mesh element with polygon [[x,y],...] > reimport > inspect Polygon2D
- **Expect:** A Polygon2D named after the element with .polygon set; sprite-type elements skipped by this builder.
- **Status:** pending

#### [ ] GD-BUILD-18 · Mesh skinning (weights -> Polygon2D bones)
- **Intent:** UNDOCUMENTED (weights/skinning not described in doc).
- **Code:** apps/godot/addons/proscenio/builders/mesh_builder.gd:8-29,98-113
- **Pre:** Mesh element with weights[] referencing existing bones
- **Steps:** Author a mesh with weights for bone A > reimport > inspect Polygon2D bones
- **Expect:** Polygon2D.skeleton path set; one bone weight array per resolved bone. Missing bone -> push_error and skipped (rig still imports).
- **Status:** pending

#### [ ] GD-BUILD-19 · Mesh parent routing (skinned stays under skeleton, rigid under bone)
- **Intent:** UNDOCUMENTED (routing rules not in doc).
- **Code:** apps/godot/addons/proscenio/builders/mesh_builder.gd:101-110; sprite_attach_util.gd:38-60
- **Pre:** Two mesh elements: one skinned, one rigid with bone
- **Steps:** Author skinned mesh + rigid mesh with bone > reimport > inspect parents
- **Expect:** Slot routing wins if name in slot_map; else rigid mesh parents to Bone2D, skinned mesh stays under Skeleton2D.
- **Status:** pending

#### [ ] GD-BUILD-20 · Sprite element build (SpriteBuilder.attach_elements -> Sprite2D)
- **Intent:** Sprites built as Sprite2D for sprite-type elements.
- **Code:** apps/godot/addons/proscenio/builders/sprite_builder.gd:12-46; proscenio_element.gd:18-19
- **Pre:** element with type 'sprite'
- **Steps:** Author a sprite element > reimport > inspect node
- **Expect:** A Sprite2D named after the element; mesh-type elements skipped by this builder.
- **Status:** pending

#### [ ] GD-BUILD-27 · Sprite parent routing (slot/bone/skeleton)
- **Intent:** UNDOCUMENTED (routing rules not in doc).
- **Code:** apps/godot/addons/proscenio/builders/sprite_builder.gd:78-87; sprite_attach_util.gd:38-60
- **Pre:** Sprite element with bone set
- **Steps:** Author sprite with bone=A (no slot) > reimport > inspect parent
- **Expect:** Sprite parents under Bone2D 'A' (or Skeleton2D if bone missing); slot membership re-routes under slot Node2D with default visibility.
- **Status:** pending

#### [ ] GD-BUILD-28 · Per-element texture resolution order (resolve_sprite_texture)
- **Intent:** UNDOCUMENTED (per-sprite path / by-name / atlas fallback chain not in doc).
- **Code:** apps/godot/addons/proscenio/builders/sprite_attach_util.gd:17-35
- **Pre:** source_dir set; a .png next to .proscenio
- **Steps:** Test 3 cases: element.texture path, <name>.png convention, neither (atlas fallback) > reimport
- **Expect:** Order honored: explicit texture path first, then <name>.png, then scene atlas. None present -> null texture.
- **Status:** pending

#### [ ] GD-BUILD-29 · AnimationPlayer + library populate (AnimationBuilder.populate)
- **Intent:** Plugin builds an AnimationPlayer; animation built last in order.
- **Code:** apps/godot/addons/proscenio/builders/animation_builder.gd:7-22; importer.gd:86-89
- **Pre:** Skeleton present; document.animations may be null or list
- **Steps:** Author animations[] (or none) > reimport > inspect AnimationPlayer
- **Expect:** AnimationPlayer node exists with an unnamed AnimationLibrary; each animation added under its name. Null animations -> empty library still added.
- **Status:** pending

#### [ ] GD-BUILD-31 · bone_transform track (position/rotation/scale value tracks)
- **Intent:** UNDOCUMENTED (track types not in doc).
- **Code:** apps/godot/addons/proscenio/builders/animation_builder.gd:51-60,96-124
- **Pre:** Animation track type 'bone_transform' targeting an existing bone; keys carry position/rotation/scale
- **Steps:** Author keys with position only > reimport > inspect Animation tracks
- **Expect:** Only channels present in keys emit tracks (position present => position track, rotation absent => no rotation track). Rotation uses CUBIC_ANGLE; position/scale CUBIC. Missing bone -> push_error, track skipped.
- **Status:** pending

#### [ ] GD-BUILD-32 · sprite_frame track
- **Intent:** UNDOCUMENTED.
- **Code:** apps/godot/addons/proscenio/builders/animation_builder.gd:61-78,148-154
- **Pre:** Animation track type 'sprite_frame' targeting a Sprite2D element name; keys carry frame
- **Steps:** Author a sprite_frame track on a Sprite2D > reimport > inspect Animation
- **Expect:** A value track on '<sprite>:frame' with NEAREST interpolation and integer frame keys. Target not Sprite2D -> push_error and no track.
- **Status:** pending

#### [ ] GD-BUILD-33 · slot_attachment track (per-child visibility)
- **Intent:** Slot_attachment track flips attachment visibility at runtime (default visible, others hidden).
- **Code:** apps/godot/addons/proscenio/builders/animation_builder.gd:79-84,127-145
- **Pre:** A slot Node2D with attachment children; track type 'slot_attachment' targeting the slot; keys carry attachment names
- **Steps:** Author slot_attachment keys naming attachments per time > reimport > inspect tracks
- **Expect:** One '<slot>/<child>:visible' value track per CanvasItem child, NEAREST interp; at each key time only the named attachment is true. Empty key.attachment is skipped. Missing slot -> push_error.
- **Status:** pending

#### [ ] GD-BUILD-37 · format_version gate (importer._load_document)
- **Intent:** Importer checks format_version before building.
- **Code:** apps/godot/addons/proscenio/importer.gd:106-144
- **Pre:** .proscenio file
- **Steps:** Set format_version != 1 (or malformed JSON / non-object root) > reimport
- **Expect:** push_error with specific reason (parse fail line, non-object root, unsupported version) and import returns ERR_INVALID_DATA; no scene generated.
- **Status:** pending

#### [ ] GD-BUILD-39 · Scene pack + owner assignment + overwrite
- **Intent:** Generated scene is plain Godot 4 nodes; reimport overwrites the existing .scn (wrapper-scene safety).
- **Code:** apps/godot/addons/proscenio/importer.gd:91-103,170-174
- **Pre:** A previously imported .proscenio
- **Steps:** Reimport an existing .proscenio > confirm .scn regenerates
- **Expect:** All nodes owned by root (visible/savable), PackedScene saved to <save_path>.scn; verbose log on overwrite; wrapper scene instancing it is untouched.
- **Status:** pending

## Findings

| F-NN | Type | Sev | Control | Detail | Code |
| --- | --- | --- | --- | --- | --- |
| F-01 | unimplemented | high | Non-destructive reimporter (diff/merge) | Doc 'Typed read'/non-destructive reimport and reimporter.gd's own header promise a diff/merge preserving user edits to the imported scene, but reimporter.gd is an empty RefCounted stub with zero code; no diff is ever performed. | apps/godot/addons/proscenio/reimporter.gd:1-10 |
| F-02 | drift | medium | Wrapper-scene safety | Doc credits 'wrapper-scene safety' as a plugin feature, but it is purely a side effect of Godot scene instancing: _import overwrites the generated .scn wholesale every reimport (lines 99-103). Direct edits to the generated scene ARE clobbered; only edits in a separate wrapper survive. No plugin code enforces or tests this. | apps/godot/addons/proscenio/importer.gd:98-103 |
| F-03 | suspected-bug | medium | Import order (_get_import_order = 0) | Importer runs at order 0 (earliest) yet _load_atlas/resolve_sprite_texture depend on already-imported Texture2D resources via ResourceLoader.exists/load. On a first full-project import there is no guarantee the atlas/png imports complete before the order-0 proscenio import, so atlas may resolve null on initial import and only succeed after a second reimport. | apps/godot/addons/proscenio/importer.gd:37-38 |
| F-04 | undocumented | low | Preset dropdown / import options | The 'Default' preset and the empty import-options/option-visibility surface are user-reachable in the Import dock but never mentioned in the doc. | apps/godot/addons/proscenio/importer.gd:41-54 |
| F-05 | undocumented | low | Atlas warning/error paths | Atlas-not-found warning, wrong-type error, and ResourceLoader-null error are user-observable diagnostics with no documentation of atlas resolution behavior. | apps/godot/addons/proscenio/importer.gd:147-167 |
| F-06 | undocumented | low | Plugin metadata / registration / teardown / priority | plugin.cfg metadata, _enter_tree/_exit_tree registration, _get_priority, and _get_import_order are all reachable behaviors absent from the doc index. | apps/godot/addons/proscenio/plugin.gd:9-17 |
| F-07 | suspected-bug | low | Build order: slots before sprites | Doc claims order 'slots before sprites' matters, but importer comment (lines 81-82) says order between MeshBuilder and SpriteBuilder does not matter; the only real ordering constraint is SlotBuilder before both. Doc overstates the ordering contract, mild drift between stated intent and code comments. | apps/godot/addons/proscenio/importer.gd:80-84 |
| F-08 | suspected-bug | high | Mesh polygon point parsing | poly.polygon reads p[0]/p[1] with no length guard; a polygon point with <2 floats triggers an out-of-bounds index error that aborts the whole import. | apps/godot/addons/proscenio/builders/mesh_builder.gd:60-61 |
| F-09 | suspected-bug | high | Mesh UV parsing | UV reads u[0]/u[1] without guarding array length, unlike the size>=2 guards used for sprite offset; a malformed uv entry crashes the import. | apps/godot/addons/proscenio/builders/mesh_builder.gd:83-84 |
| F-10 | dead | low | Key interp field | ProscenioKey.interp is parsed but never read by the animation builder; interpolation is hardcoded per property (CUBIC/CUBIC_ANGLE/NEAREST), so a per-key interp authored in the document is silently ignored. | apps/godot/addons/proscenio/builders/animation_builder.gd:113-119 |
| F-11 | suspected-bug | medium | sprite_frame / slot_attachment target lookup | Targets are resolved via character_root.find_child(target, true, false) across the entire tree, so an animation can bind to a same-named node in an unrelated subtree (e.g. a bone or slot child) rather than the intended element. | apps/godot/addons/proscenio/builders/animation_builder.gd:62,80 |
| F-12 | suspected-bug | medium | Duplicate bone names | bones[json_name] is keyed by raw name with no collision check; two bones sharing a name overwrite the dict entry, so the first bone's parent linkage is lost and its node may be orphaned/added to root. | apps/godot/addons/proscenio/builders/skeleton_builder.gd:30,32-42 |
| F-13 | suspected-bug | medium | Mesh skeleton path set when no bones resolve | _apply_skinning sets poly.skeleton and clears bones before validating any weight resolves; if every weight references a missing bone the Polygon2D is left with a skeleton path but zero bone weights, yielding an undeformed mesh bound to the skeleton. | apps/godot/addons/proscenio/builders/mesh_builder.gd:15-27 |
| F-14 | suspected-bug | medium | Slot default visibility when default empty/mismatched | visible = (sanitized_name == slot_info.default); if a slot omits 'default' (empty string) or its default never matches an attachment name, every attachment in the slot imports hidden with no warning. | apps/godot/addons/proscenio/builders/sprite_attach_util.gd:53; slot_builder.gd:65 |
| F-15 | drift | medium | Doc node-tree order vs code order | Doc states build order 'skeleton, atlas, slots before sprites, sprites, animation'; code calls MeshBuilder.attach_elements before SpriteBuilder, and meshes (Polygon2D) are a primary element type the doc's order phrase omits (it lists only sprites). | apps/godot/addons/proscenio/importer.gd:83-84 |
| F-16 | undocumented | low | Mesh (Polygon2D) element type | The doc mentions Polygon2D as a node but never documents the type:'mesh' element, multi-face polygons, UV scaling, or weight skinning behaviors that drive it. | apps/godot/addons/proscenio/builders/mesh_builder.gd:49-113 |
| F-17 | undocumented | low | All per-element sprite/mesh fields | Sprite fields (hframes, vframes, frame, centered, offset, texture_region, modulate, z_index, flip_h, flip_v) and mesh fields are entirely absent from the doc page, which only describes the high-level reimport flow. | apps/godot/addons/proscenio/builders/sprite_builder.gd:43-76 |
| F-18 | undocumented | low | Slot routing and attachment behavior | Slot anchor Node2D creation, bone/skeleton-root fallback, attachment mapping, and default-visibility routing are not described anywhere in the doc page. | apps/godot/addons/proscenio/builders/slot_builder.gd:22-66; sprite_attach_util.gd:38-60 |
| F-19 | undocumented | low | Animation track types | The three track types (bone_transform, sprite_frame, slot_attachment) and their interpolation/channel rules are not documented; only slot_attachment behavior is implied indirectly via 'flips them at runtime'. | apps/godot/addons/proscenio/builders/animation_builder.gd:51-86 |
| F-20 | suspected-bug | low | Bone parent resolution vs sanitized names | Parent resolution keys on raw JSON name (skeleton_builder) while slot/weight/animation lookups use sanitized names; a parent reference using a sanitized form (e.g. 'upper_arm_L' when the bone is 'upper_arm.L') silently fails and roots the child at the skeleton. | apps/godot/addons/proscenio/builders/skeleton_builder.gd:33-42 |
