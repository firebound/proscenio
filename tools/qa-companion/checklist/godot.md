# Godot plugin - manual-test checklist

Maintained by the QA Companion tool (tools/qa-companion): one block per item. `status` / `note` / `shots` are the recorded walk; `review` is your verdict on the test itself (keep / rephrase / drop / todo). Edit here or via the tool.

## Godot import/reimport: EditorImportPlugin, reimporter, plugin registration, wrapper-scene safety, import order

### GD-IMPORT-01 · Importer entry "Proscenio Character" in the Import dock
- status: pending
- review: keep
- observe: Import tab shows "Import As: Proscenio Character" as the importer with a "Default" preset; .proscenio recognized (not 'keep file').
- intent: A single EditorImportPlugin that turns a .proscenio file into a native Godot scene on every reimport.
- code: apps/godot/addons/proscenio/importer.gd:17-18

### GD-IMPORT-02 · Recognized extension (.proscenio)
- status: pending
- review: keep
- observe: Godot routes foo.proscenio through this importer; a foo.proscenio.scn artifact appears under .godot/imported (or the file imports without 'unrecognized' warning).
- intent: The plugin claims files with the proscenio extension so they import as characters.
- code: apps/godot/addons/proscenio/importer.gd:21-22

### GD-IMPORT-03 · Save extension / resource type (.scn -> PackedScene)
- status: pending
- review: keep
- observe: Imported resource is a PackedScene saved with .scn; instancing it yields plain Node2D/Skeleton2D/Bone2D/Polygon2D/Sprite2D/AnimationPlayer with no GDExtension dependency.
- intent: Regenerates a scene as plain Godot 4 nodes with no runtime dependency.
- code: apps/godot/addons/proscenio/importer.gd:25-31

### GD-IMPORT-04 · Preset dropdown ("Default")
- status: pending
- review: keep
- observe: Exactly one preset named "Default" is offered; selecting it changes nothing (no options follow).
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:41-46

### GD-IMPORT-05 · Import options list (empty)
- status: pending
- review: keep
- observe: No per-import options are shown (no checkboxes/fields); the options area is empty though _get_option_visibility returns true.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:49-54

### GD-IMPORT-09 · Owner assignment (scene packs cleanly)
- status: pending
- review: keep
- observe: All descendant nodes are visible/persisted (owner = root) and PackedScene.pack returns OK; no nodes are dropped on save.
- intent: Generated scene runs standalone as plain Godot nodes.
- code: apps/godot/addons/proscenio/importer.gd:91-96

### GD-IMPORT-10 · Overwrite-existing-scene notice (print_verbose)
- status: pending
- review: keep
- observe: Verbose log prints "Proscenio: regenerating <path>.scn (existing scene will be overwritten)"; the prior .scn is replaced wholesale.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:99-102

### GD-IMPORT-11 · format_version gate error
- status: pending
- review: keep
- observe: Import fails (ERR_INVALID_DATA); error log: "Proscenio: unsupported format_version N (need 1)"; no scene generated.
- intent: The importer checks the format_version before building.
- code: apps/godot/addons/proscenio/importer.gd:136-143

### GD-IMPORT-12 · Unopenable source-file error
- status: pending
- review: keep
- observe: push_error "Proscenio: cannot open '<path>' (error N)"; _import returns ERR_INVALID_DATA.
- intent: Reads the document; reports failures so import returns a single error code.
- code: apps/godot/addons/proscenio/importer.gd:109-114

### GD-IMPORT-13 · JSON parse-failure error
- status: pending
- review: keep
- observe: push_error "Proscenio: JSON parse failed at line L: <msg>"; import returns ERR_INVALID_DATA; no scene built.
- intent: Reads the document as typed Resource after parsing JSON.
- code: apps/godot/addons/proscenio/importer.gd:116-125

### GD-IMPORT-14 · Non-object root error
- status: pending
- review: keep
- observe: push_error "Proscenio: expected JSON object at document root"; import returns ERR_INVALID_DATA.
- intent: Expects a JSON object at the document root.
- code: apps/godot/addons/proscenio/importer.gd:127-129

### GD-IMPORT-15 · from_dict null-return error
- status: pending
- review: keep
- observe: push_error from element dispatch then "Proscenio: ProscenioDocument.from_dict returned null"; import returns ERR_INVALID_DATA.
- intent: Reads the document as a typed Resource (ProscenioDocument.from_dict).
- code: apps/godot/addons/proscenio/importer.gd:132-135

### GD-IMPORT-16 · Atlas resolution (document.atlas)
- status: pending
- review: keep
- observe: Texture loaded with CACHE_MODE_REPLACE and applied to elements lacking a per-sprite texture.
- intent: Builds the atlas (texture) used by sprites/meshes during import.
- code: apps/godot/addons/proscenio/importer.gd:147-167

### GD-IMPORT-17 · Atlas-not-found warning
- status: pending
- review: keep
- observe: push_warning "Proscenio: atlas not found at '<full>'"; import still succeeds; elements fall back to per-sprite/by-name textures or none.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:152-154

### GD-IMPORT-18 · Atlas wrong-type error
- status: pending
- review: keep
- observe: push_error "Proscenio: '<full>' loaded but not Texture2D - got <class>"; atlas treated as null; import continues.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:161-166

### GD-IMPORT-21 · Import priority (_get_priority = 1.0)
- status: pending
- review: keep
- observe: Priority 1.0; this importer is the sole/winning claimant for .proscenio.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:33-34

### GD-IMPORT-22 · Import order (_get_import_order = 0)
- status: pending
- review: keep
- observe: Importer runs at order 0; atlas textures it depends on must already be imported (no explicit ordering guarantee that textures precede order-0 proscenio import).
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/importer.gd:37-38

### GD-IMPORT-25 · Plugin metadata (plugin.cfg name/description/version)
- status: pending
- review: keep
- observe: Entry "Proscenio" by Space Wizard Studios, version 0.1.0, description mentioning Skeleton2D+Bone2D+Polygon2D+AnimationPlayer; script points to plugin.gd.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/plugin.cfg:1-7

### GD-IMPORT-06 · Reimport button (full scene regeneration)
- status: pending
- review: keep
- pre: A valid format_version=1 .proscenio in res://, plugin enabled.
- steps:
  1. Select the .proscenio in FileSystem > Import tab > click Reimport (or edit/save the .proscenio to trigger auto-reimport).
- observe: A new .scn is built: root Node2D named after document.name (else "Character"), with Skeleton2D, AnimationPlayer, and element nodes; ResourceSaver.save returns OK; the imported scene reflects the new data.
- intent: Regenerate the scene (Skeleton2D + Bone2D + Polygon2D/Sprite2D + AnimationPlayer) whenever a .proscenio enters or changes.
- code: apps/godot/addons/proscenio/importer.gd:57-103

### GD-IMPORT-07 · Build order: skeleton -> atlas -> slots -> mesh/sprite elements -> animation
- status: pending
- review: keep
- pre: A .proscenio containing skeleton, slots, mesh+sprite elements, and animations.
- steps:
  1. Import a document exercising all sections > open the generated scene tree.
- observe: Skeleton2D added first; slot Node2D anchors exist before element nodes so slotted elements parent under the slot Node2D; AnimationPlayer present last with tracks resolving to the built nodes.
- intent: Builds the node tree in order: skeleton, atlas, slots before sprites, sprites, animation.
- code: apps/godot/addons/proscenio/importer.gd:72-89

### GD-IMPORT-08 · Slot-vs-bone routing fallback (empty slot map)
- status: pending
- review: keep
- pre: A .proscenio with elements but no slots[] section.
- steps:
  1. Import a document with elements and no slots > inspect element parents in the generated scene.
- observe: Each non-skinned element parents under its named Bone2D (or skeleton root); skinned meshes stay under Skeleton2D; no slot Node2D anchors exist.
- intent: No slots leaves the map empty and routing falls back to bone-parenting.
- code: apps/godot/addons/proscenio/importer.gd:80-84

### GD-IMPORT-19 · Wrapper-scene safety (user wrapper survives reimport)
- status: pending
- review: keep
- pre: A wrapper scene instances the generated foo.proscenio.scn and adds a script + child gameplay nodes.
- steps:
  1. Create wrapper.tscn instancing the generated scene > add a script and extra nodes > edit/reimport the .proscenio.
- observe: wrapper.tscn is untouched; only the instanced generated subtree updates; user script and added nodes persist (relies on Godot scene-instance inheritance, not on reimporter.gd).
- intent: A user-authored wrapper scene that instances the generated one survives every reimport, so scripts and gameplay nodes are never clobbered.
- code: apps/godot/addons/proscenio/importer.gd:98-103

### GD-IMPORT-20 · Non-destructive reimporter (diff/merge)
- status: pending
- review: keep
- pre: An imported scene the user has hand-edited (added nodes/animations directly).
- steps:
  1. Edit the imported scene directly > reimport the .proscenio.
- observe: Per the doc, a diff/merge preserves user edits. In reality reimporter.gd is an unimplemented stub (RefCounted, no code); nothing diff-merges. Confirm no diff behavior occurs.
- intent: Diff the existing imported scene against new .proscenio data, preserving user-added nodes, scripts and custom animations while replacing source-driven content.
- code: apps/godot/addons/proscenio/reimporter.gd:1-10

### GD-IMPORT-23 · Plugin registration (_enter_tree add_import_plugin)
- status: pending
- review: keep
- pre: Plugin listed in project.godot [editor_plugins] enabled.
- steps:
  1. Open the project (or toggle the plugin on in Project Settings > Plugins).
- observe: On enter_tree the importer is constructed and add_import_plugin called; "Proscenio Character" becomes selectable as an importer.
- intent: The plugin registers a single EditorImportPlugin.
- code: apps/godot/addons/proscenio/plugin.gd:9-11

### GD-IMPORT-24 · Plugin teardown (_exit_tree remove_import_plugin)
- status: pending
- review: keep
- pre: Plugin currently enabled.
- steps:
  1. Disable the plugin in Project Settings > Plugins (or close the project).
- observe: remove_import_plugin called and _importer cleared; "Proscenio Character" importer no longer offered; no leak/errors.
- intent: UNDOCUMENTED
- code: apps/godot/addons/proscenio/plugin.gd:14-17

## Godot builders: skeleton, sprite, mesh, slot, animation -> node tree

### GD-BUILD-02 · Bone position field
- status: pending
- review: keep
- observe: Bone2D.position == (10,20). Missing/short array (<2) yields Vector2.ZERO.
- intent: UNDOCUMENTED (doc names Bone2D as a node type only, not the position field).
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:20

### GD-BUILD-03 · Bone rotation field
- status: pending
- review: keep
- observe: Bone2D.rotation == 1.57 rad.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:21

### GD-BUILD-04 · Bone scale field
- status: pending
- review: keep
- observe: Bone2D.scale == (2,2). Missing/short array defaults to (1,1).
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:22

### GD-BUILD-05 · Bone length field
- status: pending
- review: keep
- observe: Bone2D length set to authored value and autocalculate_length_and_angle disabled. length==0 leaves Godot autocalc on.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:23-27

### GD-BUILD-06 · Bone rest pose capture
- status: pending
- review: keep
- observe: Bone2D.get_rest() equals the authored transform (so animation value tracks replace it cleanly).
- intent: UNDOCUMENTED (doc says animations replace pose; rest-capture mechanism not documented).
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:29

### GD-BUILD-08 · Bone name (unsanitized dict key, sanitized node name)
- status: pending
- review: keep
- observe: Bone2D.name == 'upper_arm_L' (dot->underscore), but parent lookup keys on original 'upper_arm.L'.
- intent: UNDOCUMENTED (dotted-name normalization is an internal note, not user doc).
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:15-19,30

### GD-BUILD-11 · Slot missing-name guard
- status: pending
- review: keep
- observe: Warning 'slot entry missing name - skipping'; no Node2D created, attachments not mapped.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/slot_builder.gd:38-40

### GD-BUILD-12 · Slot bone resolution / missing bone fallback
- status: pending
- review: keep
- observe: Warning 'references missing bone ... anchoring at skeleton root'; Node2D parented to Skeleton2D.
- intent: Slot anchors under its Bone2D; doc does not describe the missing-bone fallback.
- code: apps/godot/addons/proscenio/builders/slot_builder.gd:45-61

### GD-BUILD-15 · Mesh polygons (multi-face) field
- status: pending
- review: keep
- observe: Polygon2D.polygons holds each face index array. Empty polygons => single ring renders whole shape.
- intent: UNDOCUMENTED (multi-face per-face arrays not in doc).
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:67-71

### GD-BUILD-16 · Mesh UV scaling to pixel space
- status: pending
- review: keep
- observe: UVs multiplied by texture size (pixel space). With no texture, raw [0,1] UVs are kept.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:77-85

### GD-BUILD-17 · Mesh modulate / z_index
- status: pending
- review: keep
- observe: Polygon2D.modulate set when modulate has >=4 entries (else default white); z_index applied.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:92-96

### GD-BUILD-21 · Sprite hframes / vframes / frame
- status: pending
- review: keep
- observe: Sprite2D.hframes==4, vframes==1, frame==2.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:43-45

### GD-BUILD-22 · Sprite centered toggle
- status: pending
- review: keep
- observe: Sprite2D.centered matches authored bool (default false).
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:46

### GD-BUILD-23 · Sprite offset
- status: pending
- review: keep
- observe: Sprite2D.offset == (5,5) when offset has >=2 entries.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:48-49

### GD-BUILD-24 · Sprite texture_region (region_enabled + filter clip)
- status: pending
- review: keep
- observe: region_enabled==true, region_filter_clip_enabled==true, region_rect == (0,0,32,32). Absent -> full texture.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:53-63

### GD-BUILD-25 · Sprite modulate / z_index
- status: pending
- review: keep
- observe: Sprite2D.modulate set when >=4 entries (else default white); z_index applied.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:67-74

### GD-BUILD-26 · Sprite flip_h / flip_v
- status: pending
- review: keep
- observe: Sprite2D.flip_h==true, flip_v==true (default false).
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:75-76

### GD-BUILD-30 · Animation length / loop_mode
- status: pending
- review: keep
- observe: Animation.length set; loop_mode == LOOP_LINEAR when loop true, else LOOP_NONE.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:28-30

### GD-BUILD-34 · Unknown track type handling
- status: pending
- review: keep
- observe: Warning 'unknown track type bogus'; no track added; rest of animation unaffected.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:85-86

### GD-BUILD-35 · Empty-keys track guard
- status: pending
- review: keep
- observe: Track silently skipped (early return), no track added.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:43-44

### GD-BUILD-36 · skeleton-has-no-parent guard for animation paths
- status: pending
- review: keep
- observe: push_error 'skeleton has no parent'; track resolution aborts for that track.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:46-49

### GD-BUILD-38 · Document name -> root node name
- status: pending
- review: keep
- observe: Root Node2D named after document.name, or 'Character' when name empty.
- intent: UNDOCUMENTED (root naming default).
- code: apps/godot/addons/proscenio/importer.gd:69-70

### GD-BUILD-01 · Skeleton2D root build (SkeletonBuilder.build)
- status: pending
- review: keep
- pre: A .proscenio file in the project; reimport triggered
- steps:
  1. Author a .proscenio with a skeleton block > reimport > open generated .scn
- observe: Root Node2D contains a child named 'Skeleton2D'. With no skeleton block the Skeleton2D still appears (empty).
- intent: Plugin regenerates a scene whose skeleton is built first in order; null skeleton still yields a Skeleton2D node.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:5-44

### GD-BUILD-07 · Bone parent resolution / tree nesting
- status: pending
- review: keep
- pre: Skeleton with >=2 bones, child references parent by exact JSON name
- steps:
  1. Author bone B with parent A > reimport > inspect tree
- observe: B is a child of A. Empty parent string roots B at Skeleton2D. Parent name not found also roots at Skeleton2D (silent fallback).
- intent: Skeleton built in order; bones nest into a tree by parent reference (Bone2D under Bone2D).
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:32-42

### GD-BUILD-09 · Atlas load (importer._load_atlas)
- status: pending
- review: keep
- pre: .proscenio with document.atlas path next to file
- steps:
  1. Set document.atlas to a sibling png > reimport
- observe: Atlas Texture2D loaded and passed to element builders. Empty atlas -> null; missing path -> warning + null; non-texture -> error + null.
- intent: Importer reads atlas before slots/sprites; atlas is the scene-wide fallback texture.
- code: apps/godot/addons/proscenio/importer.gd:75,147-167

### GD-BUILD-10 · Slot anchor build (SlotBuilder.build)
- status: pending
- review: keep
- pre: .proscenio with a slots[] entry having name + attachments[]
- steps:
  1. Author a slot with bone and attachments > reimport > inspect tree
- observe: A Node2D named after the (sanitized) slot appears under the named Bone2D; under Skeleton2D root if bone empty or bone missing (with warning).
- intent: Slots build BEFORE sprites; each slot becomes a Node2D under its Bone2D (or Skeleton2D when bone empty).
- code: apps/godot/addons/proscenio/builders/slot_builder.gd:22-66

### GD-BUILD-13 · Slot attachment map / default attachment visibility
- status: pending
- review: keep
- pre: Slot with multiple attachments[], a default set; elements named to match attachments
- steps:
  1. Author slot default='headA' with attachments [headA,headB]; add sprite/mesh elements headA,headB > reimport
- observe: headA and headB parent under the slot Node2D; headA visible==true, headB visible==false.
- intent: Default attachment starts visible, others hidden until slot_attachment track flips them.
- code: apps/godot/addons/proscenio/builders/slot_builder.gd:32-34,65; sprite_attach_util.gd:50-54

### GD-BUILD-14 · Mesh element build (MeshBuilder.attach_elements -> Polygon2D)
- status: pending
- review: keep
- pre: element with type 'mesh' (or omitted) and a polygon ring
- steps:
  1. Author a mesh element with polygon [[x,y],...] > reimport > inspect Polygon2D
- observe: A Polygon2D named after the element with .polygon set; sprite-type elements skipped by this builder.
- intent: Sprites built as Polygon2D for mesh-type elements; type absent defaults to mesh.
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:32-71; proscenio_element.gd:15-17

### GD-BUILD-18 · Mesh skinning (weights -> Polygon2D bones)
- status: pending
- review: keep
- pre: Mesh element with weights[] referencing existing bones
- steps:
  1. Author a mesh with weights for bone A > reimport > inspect Polygon2D bones
- observe: Polygon2D.skeleton path set; one bone weight array per resolved bone. Missing bone -> push_error and skipped (rig still imports).
- intent: UNDOCUMENTED (weights/skinning not described in doc).
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:8-29,98-113

### GD-BUILD-19 · Mesh parent routing (skinned stays under skeleton, rigid under bone)
- status: pending
- review: keep
- pre: Two mesh elements: one skinned, one rigid with bone
- steps:
  1. Author skinned mesh + rigid mesh with bone > reimport > inspect parents
- observe: Slot routing wins if name in slot_map; else rigid mesh parents to Bone2D, skinned mesh stays under Skeleton2D.
- intent: UNDOCUMENTED (routing rules not in doc).
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:101-110; sprite_attach_util.gd:38-60

### GD-BUILD-20 · Sprite element build (SpriteBuilder.attach_elements -> Sprite2D)
- status: pending
- review: keep
- pre: element with type 'sprite'
- steps:
  1. Author a sprite element > reimport > inspect node
- observe: A Sprite2D named after the element; mesh-type elements skipped by this builder.
- intent: Sprites built as Sprite2D for sprite-type elements.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:12-46; proscenio_element.gd:18-19

### GD-BUILD-27 · Sprite parent routing (slot/bone/skeleton)
- status: pending
- review: keep
- pre: Sprite element with bone set
- steps:
  1. Author sprite with bone=A (no slot) > reimport > inspect parent
- observe: Sprite parents under Bone2D 'A' (or Skeleton2D if bone missing); slot membership re-routes under slot Node2D with default visibility.
- intent: UNDOCUMENTED (routing rules not in doc).
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:78-87; sprite_attach_util.gd:38-60

### GD-BUILD-28 · Per-element texture resolution order (resolve_sprite_texture)
- status: pending
- review: keep
- pre: source_dir set; a .png next to .proscenio
- steps:
  1. Test 3 cases: element.texture path, <name>.png convention, neither (atlas fallback) > reimport
- observe: Order honored: explicit texture path first, then <name>.png, then scene atlas. None present -> null texture.
- intent: UNDOCUMENTED (per-sprite path / by-name / atlas fallback chain not in doc).
- code: apps/godot/addons/proscenio/builders/sprite_attach_util.gd:17-35

### GD-BUILD-29 · AnimationPlayer + library populate (AnimationBuilder.populate)
- status: pending
- review: keep
- pre: Skeleton present; document.animations may be null or list
- steps:
  1. Author animations[] (or none) > reimport > inspect AnimationPlayer
- observe: AnimationPlayer node exists with an unnamed AnimationLibrary; each animation added under its name. Null animations -> empty library still added.
- intent: Plugin builds an AnimationPlayer; animation built last in order.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:7-22; importer.gd:86-89

### GD-BUILD-31 · bone_transform track (position/rotation/scale value tracks)
- status: pending
- review: keep
- pre: Animation track type 'bone_transform' targeting an existing bone; keys carry position/rotation/scale
- steps:
  1. Author keys with position only > reimport > inspect Animation tracks
- observe: Only channels present in keys emit tracks (position present => position track, rotation absent => no rotation track). Rotation uses CUBIC_ANGLE; position/scale CUBIC. Missing bone -> push_error, track skipped.
- intent: UNDOCUMENTED (track types not in doc).
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:51-60,96-124

### GD-BUILD-32 · sprite_frame track
- status: pending
- review: keep
- pre: Animation track type 'sprite_frame' targeting a Sprite2D element name; keys carry frame
- steps:
  1. Author a sprite_frame track on a Sprite2D > reimport > inspect Animation
- observe: A value track on '<sprite>:frame' with NEAREST interpolation and integer frame keys. Target not Sprite2D -> push_error and no track.
- intent: UNDOCUMENTED.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:61-78,148-154

### GD-BUILD-33 · slot_attachment track (per-child visibility)
- status: pending
- review: keep
- pre: A slot Node2D with attachment children; track type 'slot_attachment' targeting the slot; keys carry attachment names
- steps:
  1. Author slot_attachment keys naming attachments per time > reimport > inspect tracks
- observe: One '<slot>/<child>:visible' value track per CanvasItem child, NEAREST interp; at each key time only the named attachment is true. Empty key.attachment is skipped. Missing slot -> push_error.
- intent: Slot_attachment track flips attachment visibility at runtime (default visible, others hidden).
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:79-84,127-145

### GD-BUILD-37 · format_version gate (importer._load_document)
- status: pending
- review: keep
- pre: .proscenio file
- steps:
  1. Set format_version != 1 (or malformed JSON / non-object root) > reimport
- observe: push_error with specific reason (parse fail line, non-object root, unsupported version) and import returns ERR_INVALID_DATA; no scene generated.
- intent: Importer checks format_version before building.
- code: apps/godot/addons/proscenio/importer.gd:106-144

### GD-BUILD-39 · Scene pack + owner assignment + overwrite
- status: pending
- review: keep
- pre: A previously imported .proscenio
- steps:
  1. Reimport an existing .proscenio > confirm .scn regenerates
- observe: All nodes owned by root (visible/savable), PackedScene saved to <save_path>.scn; verbose log on overwrite; wrapper scene instancing it is untouched.
- intent: Generated scene is plain Godot 4 nodes; reimport overwrites the existing .scn (wrapper-scene safety).
- code: apps/godot/addons/proscenio/importer.gd:91-103,170-174
