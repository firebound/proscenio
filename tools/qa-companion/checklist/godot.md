# Godot plugin - manual-test checklist

Maintained by the QA Companion tool (tools/qa-companion): one block per item. Each block answers three questions in plain language a tester can follow without reading the code: what passing it proves (`intent`), what to do (`steps`), and what you see (`observe`). `status` / `note` / `shots` are the recorded walk; `review` is your verdict on the test itself (keep / rephrase / drop / todo). Edit here or via the tool.

Most Godot node-tree behavior is asserted inside the roundtrip flows' import-and-inspect steps (flows.md), not here. This file keeps only the conditional / error-path tests that no flow exercises (import error gates, atlas and parent-routing fallbacks, animation guard edges) plus a per-builder output inventory describing what each builder produces in the generated scene. The inventories are what a flow's inspect step checks against; the standalone tests below are the behaviors no flow covers.

## Import: error gates + routing + reimport

### GD-IMPORT-GATE-01 · Bad input files are rejected before any scene is built
- status: pending
- review: keep
- pre: A .proscenio file sitting in res:// with the plugin enabled. Keep a previously generated .scn next to it so you can confirm it is not touched.
- steps:
  1. Point the importer at a file it cannot open (e.g. a path with the wrong permissions) and reimport.
  2. Truncate the file mid-object so the JSON is incomplete and reimport.
  3. Change the file so its top level is a JSON list instead of an object and reimport.
  4. Author a body the importer cannot turn into a document and reimport.
  5. Set the file's format version to 2 and reimport.
- observe: Every case stops the import with one clear message in the Output panel and produces no new scene. (1) cannot open the file at that path; (2) JSON parse failed, naming the line; (3) the document root must be a JSON object; (4) an element error followed by a "document could not be read" message; (5) unsupported format version 2, needs version 1. In each case the previously generated .scn is left exactly as it was - nothing regenerates on failure.
- intent: The importer checks the document (can it open, is it valid JSON, is the root an object, does it parse into a document, is the format version supported) before building anything, and reports a distinct error for each failure.
- code: apps/godot/addons/proscenio/importer.gd:106-144
- note: absorbs GD-IMPORT-11/12/13/14/15 and GD-BUILD-37 (duplicate gate). Maps gap G1.

### GD-IMPORT-GATE-02 · Plugin registers on enable and removes itself on disable
- status: pending
- review: keep
- pre: The plugin listed under [editor_plugins] in project.godot.
- steps:
  1. Enable the plugin (or open the project) and check the import dock.
  2. Disable the plugin and check the import dock again.
- observe: After enabling, "Proscenio Character" appears as a selectable importer for .proscenio files. After disabling, that importer is no longer offered, and the Output panel shows no errors or leftover errors from teardown.
- intent: The plugin adds exactly one importer when enabled and cleanly removes it when disabled.
- code: apps/godot/addons/proscenio/plugin.gd:9-17
- note: absorbs GD-IMPORT-01 (entry visible), GD-IMPORT-23 (register), GD-IMPORT-24 (teardown).

### GD-IMPORT-ATLAS-01 · A broken scene atlas degrades instead of aborting the import
- status: pending
- review: keep
- pre: A .proscenio whose sprites carry no per-sprite texture, plus a sibling atlas .png the document points at.
- steps:
  1. Delete the atlas .png the document references and reimport.
  2. Point the document's atlas at something that is not an image (e.g. a .tres) and reimport.
  3. Set the document's atlas field to an empty string and reimport.
- observe: In all three cases the import still finishes and a scene is produced. (1) a warning that the atlas was not found, and elements fall back to their own texture or a same-named .png or nothing; (2) a warning that the file loaded but is not an image, and the import continues with no atlas; (3) no atlas and no warning. The happy path (a valid atlas loaded once and applied to texture-less elements) is checked in FLOW-ATLAS-02.
- intent: The scene-wide atlas is an optional fallback texture - if it is missing or the wrong type, the import warns and continues with no atlas rather than failing.
- code: apps/godot/addons/proscenio/importer.gd:147-167
- note: absorbs GD-IMPORT-16/17/18 and GD-BUILD-09 (load wrapper). Maps gap G2.

### GD-IMPORT-ANIM-GUARDS-01 · Malformed animation tracks are skipped, the rest of the animation survives
- status: pending
- review: keep
- pre: A document with one valid animation track plus several deliberately broken tracks alongside it.
- steps:
  1. Add a track with an unknown type and reimport.
  2. Add a track whose keyframe list is empty and reimport.
  3. Make the skeleton have no parent node, add any bone-targeting track, and reimport.
  4. Author a bone-transform track with position keys only (no rotation or scale) and reimport.
  5. Author a bone-transform track aimed at a bone that does not exist and reimport.
  6. Author a sprite-frame track whose target is not a Sprite2D and reimport.
- observe: Each broken track is dropped and the valid track still imports. The Output panel shows: (1) a warning about the unknown track type, no track added; (2) the empty track is silently skipped; (3) an error that the skeleton has no parent, that track is abandoned; (4) only the channel that has keys gets a track - a position track appears, no rotation or scale track; (5) an error and the track is skipped; (6) an error and no track. The remaining good tracks are always present and intact in the generated AnimationPlayer.
- intent: The animation builder skips any malformed or unresolvable track (warning or error) without throwing away the rest of the animation.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:43-49,51-60,85-86,96-124,148-154
- note: absorbs GD-BUILD-31 (per-channel + missing bone), GD-BUILD-32 (target-not-Sprite2D), GD-BUILD-34/35/36. Maps gap G5.

### GD-IMPORT-ROUTE-01 · Build order: skeleton, atlas, slots, elements, animation
- status: pending
- review: keep
- pre: A .proscenio containing a skeleton, slots, both mesh and sprite elements, and animations.
- steps:
  1. Import a document that exercises every section and open the generated scene tree.
- observe: In the scene tree the Skeleton2D is added first; the slot anchor nodes exist before the element nodes, so elements that belong to a slot sit under their slot anchor; the AnimationPlayer comes last and its tracks point at nodes that already exist.
- intent: The scene is built in a fixed order - skeleton, atlas, slots, mesh/sprite elements, animation - so each stage can find the nodes the previous stage created.
- code: apps/godot/addons/proscenio/importer.gd:72-89
- note: absorbs GD-IMPORT-07.

### GD-IMPORT-ROUTE-02 · With no slots, elements parent onto bones instead
- status: pending
- review: keep
- pre: A .proscenio with elements but no slots section.
- steps:
  1. Import a document that has elements and no slots, then inspect each element's parent in the scene tree.
- observe: There are no slot anchor nodes. Each non-skinned element sits under its named Bone2D (or directly under the Skeleton2D when it names no bone or an unknown bone). Skinned meshes sit under the Skeleton2D. No errors.
- intent: When the document has no slots, elements fall back to parenting onto bones without error.
- code: apps/godot/addons/proscenio/importer.gd:80-84
- note: absorbs GD-IMPORT-08. Contributes to gap G4 (empty-input defaults).

### GD-IMPORT-ROUTE-03 · Bones nest by parent name, unknown parents fall back to the root
- status: pending
- review: keep
- pre: A skeleton with at least two bones where a child names its parent exactly.
- steps:
  1. Author bone B with parent A, reimport, and inspect the tree.
  2. Set B's parent to an empty string, reimport, and inspect.
  3. Set B's parent to a name no bone has, reimport, and inspect.
- observe: (1) Bone2D B is a child of Bone2D A; (2) with an empty parent, B sits directly under the Skeleton2D; (3) with an unknown parent name, B also sits directly under the Skeleton2D, and no warning appears (silent fallback).
- intent: Bones form a tree from their parent names; an empty or unrecognized parent quietly roots the bone at the Skeleton2D.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:32-42
- note: absorbs GD-BUILD-07. Maps gap G3.

### GD-IMPORT-ROUTE-04 · Dotted bone names are renamed but still resolve as parents
- status: pending
- review: keep
- pre: A bone named with a dot, e.g. "upper_arm.L", with a child whose parent is that dotted name.
- steps:
  1. Author bone "upper_arm.L" with a child whose parent is "upper_arm.L", reimport, and inspect the tree.
- observe: The Bone2D is renamed to "upper_arm_L" (the dot becomes an underscore), yet the child still nests correctly under it because the parent lookup uses the original dotted name. A child that named the renamed "upper_arm_L" instead would not find its parent.
- intent: Node names get sanitized for the editor while parent lookups still match the original dotted name - a real edge a tester should know about.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:15-19,30
- note: absorbs GD-BUILD-08. Maps gap G3.

### GD-IMPORT-ROUTE-05 · Mesh parenting: slot, then bone vs skeleton; missing skin bone is non-fatal
- status: pending
- review: keep
- pre: Two mesh elements (one skinned, one rigid with a bone), plus a skinned mesh whose weights reference a bone that does not exist.
- steps:
  1. Author a skinned mesh and a rigid-with-bone mesh, reimport, and inspect their parents.
  2. Author a skinned mesh weighted to a non-existent bone and reimport.
- observe: If the element's name matches a slot, it goes under that slot anchor. Otherwise a rigid mesh sits under its Bone2D and a skinned mesh sits under the Skeleton2D. The mesh weighted to a missing bone produces an error in the Output panel and that bone's weights are dropped, but the rest of the mesh and the rig still import. A mesh whose weights all reference a missing bone, or a name that resolves to a non-Bone2D node (a slot anchor sharing the name), is left unbound - no skeleton reference - rather than bound with zero weights, which would collapse it to a point.
- intent: Mesh elements route by slot first, then by skin (skeleton root) versus rigid (bone); a missing skin bone is skipped rather than failing the import.
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:8-29,98-113; sprite_attach_util.gd:38-60
- note: absorbs GD-BUILD-18 (missing-bone clause) and GD-BUILD-19. Maps gap G3. The all-missing-unbound and non-Bone2D-target guards are asserted in apps/godot/tests/test_builder_guards.gd (all_missing, non_bone_weight).

### GD-IMPORT-ROUTE-06 · Sprite parenting: slot, then bone, then skeleton
- status: pending
- review: keep
- pre: A sprite element with a bone set, and a second sprite that belongs to a slot.
- steps:
  1. Author a sprite with bone A and no slot, reimport, and inspect its parent.
  2. Author a sprite that is a slot attachment, reimport, and inspect its parent and visibility.
- observe: The bone-only sprite sits under Bone2D A (or under the Skeleton2D when it names no bone). The slot sprite sits under the slot anchor instead, with its visibility set by whether it is the slot's default attachment.
- intent: Sprites route by slot membership first, then by bone, then to the skeleton root.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:78-87; sprite_attach_util.gd:38-60
- note: absorbs GD-BUILD-27. Maps gap G3.

### GD-IMPORT-ROUTE-07 · Each element resolves its texture down a fixed fallback chain
- status: pending
- review: keep
- pre: A source folder set, a .png sibling to the .proscenio, and a scene atlas available.
- steps:
  1. Give an element an explicit texture path, reimport, and confirm that texture is used.
  2. Remove the explicit path, provide a same-named .png next to the file, reimport, and confirm the by-name texture is used.
  3. Remove both, keep the scene atlas, reimport, and confirm the atlas is used.
  4. Remove all three, reimport, and confirm the element has no texture.
- observe: The element always uses the first source available in this order: its explicit texture path, then a same-named .png, then the scene atlas, then nothing. The atlas-fallback case is also checked in FLOW-ATLAS-02.
- intent: Every element finds its texture through a fixed fallback chain that ends in no texture.
- code: apps/godot/addons/proscenio/builders/sprite_attach_util.gd:17-35
- note: absorbs GD-BUILD-28.

### GD-IMPORT-PRIORITY-01 · Importer claims .proscenio and tolerates not-yet-imported textures
- status: pending
- review: keep
- steps:
  1. In a fresh project where a referenced texture has not been imported yet, import a .proscenio that depends on it and check the result.
- observe: The .proscenio importer is the one that handles the file (nothing else competes for it). Because the proscenio import runs early, a texture it needs may not be imported yet - confirm the import still resolves the texture, or degrades to no atlas as in GD-IMPORT-ATLAS-01, rather than hard-failing.
- intent: The importer is the sole claimant for .proscenio and runs early; there is no explicit guarantee that dependent textures import first, so confirm the import copes either way.
- code: apps/godot/addons/proscenio/importer.gd:33-38
- note: absorbs GD-IMPORT-21/22.

### GD-IMPORT-REIMPORT-01 · A wrapper scene that instances the generated scene survives reimport
- status: pending
- review: keep
- pre: A wrapper scene that instances the generated foo.proscenio.scn and adds its own script plus extra gameplay nodes.
- steps:
  1. Create wrapper.tscn instancing the generated scene, add a script and extra nodes, then edit and reimport the .proscenio.
- observe: wrapper.tscn is untouched; only the instanced generated part updates, and the user's script and added nodes stay in place. This works through Godot's normal scene-instance inheritance, not through any plugin code.
- intent: A wrapper that instances the generated scene survives every reimport, so user scripts and gameplay nodes are never clobbered.
- code: apps/godot/addons/proscenio/importer.gd:98-103,170-174
- note: absorbs GD-IMPORT-19 and the GD-BUILD-39 wrapper clause; asserted alongside FLOW-REIMPORT-01.

### GD-IMPORT-REIMPORT-02 · Reimport fully regenerates the scene; direct edits are lost
- status: pending
- review: keep
- pre: A generated scene the user has hand-edited directly (added nodes or animations inside the generated .scn itself).
- steps:
  1. Edit the imported scene directly, then reimport the .proscenio.
- observe: The scene is fully regenerated and the direct edits are discarded - there is no merge step. Confirm nothing is preserved. The dead diff/merge stub was removed (spec 055) and the docs now state the overwrite contract plainly, so there is no longer a documentation claim to contradict. The supported way to keep user work is the wrapper approach in GD-IMPORT-REIMPORT-01.
- intent: Confirm reimport is a full regeneration - the plugin promises no non-destructive diff/merge.
- code: apps/godot/addons/proscenio/importer.gd:98-109
- note: absorbs GD-IMPORT-20; asserted alongside FLOW-REIMPORT-01.

## Builders: per-builder output inventory

### GD-SKEL-INV · Skeleton output inventory
- status: pending
- review: keep
- observe: A root Node2D named after the document (or "Character" if unnamed). Under it a Skeleton2D, present even when the skeleton section is empty. One Bone2D per bone carrying its authored transform: position (zero when the array is missing or too short), rotation in radians, scale (1,1 when missing or too short), and length (the authored value, with Godot's auto-length turned off; a length of 0 leaves auto-length on). Each bone's rest pose equals its authored transform, so animation tracks replace it cleanly.
- intent: The skeleton builder produces the root Node2D, the Skeleton2D, and the Bone2D tree with each bone's transform fields filled in.
- code: apps/godot/addons/proscenio/builders/skeleton_builder.gd:5-44; importer.gd:69-70
- note: absorbs GD-BUILD-01/02/03/04/05/06/38; behavior asserted in FLOW-DOLL-03 inspect step (empty-skeleton default contributes to gap G4).

### GD-SLOT-INV · Slot output inventory
- status: pending
- review: keep
- observe: One Node2D anchor per slot, named after the slot and parented under the slot's Bone2D. The slot's attachments sit under that anchor: the default attachment is visible, all the others are hidden. If the slot's default names no attachment that exists, the builder warns and falls back to showing the first attachment instead of hiding every one. A slot with no name is skipped with a warning and produces no anchor (its attachments are left unmapped). A slot whose bone is missing or empty gets a warning and its anchor is parented under the Skeleton2D root instead.
- intent: The slot builder produces one anchor Node2D per slot, shows only the default attachment, and guards against missing names and bones.
- code: apps/godot/addons/proscenio/builders/slot_builder.gd:22-66; sprite_attach_util.gd:50-54
- note: absorbs GD-BUILD-10/11/12/13; behavior asserted in FLOW-SLOTSWAP-02 and FLOW-SLOTCYCLE-01 inspect steps. The default-matches-nothing fallback is asserted in apps/godot/tests/test_builder_guards.gd (slot_default_miss).

### GD-MESH-INV · Mesh (Polygon2D) output inventory
- status: pending
- review: keep
- observe: One Polygon2D per mesh element (elements typed "mesh" or untyped; sprite-type elements are skipped), named after the element with its polygon shape set. Multi-face meshes carry per-face index lists; a mesh with none renders as a single ring covering the whole shape. UVs are scaled into pixels by the texture size (kept raw in 0..1 range when there is no texture). The element's color tint is applied when the document gives a full color (otherwise white), and its draw order is applied. Skinned meshes carry a skeleton reference and one weight list per resolved bone.
- intent: The mesh builder produces a Polygon2D per mesh element with its geometry, UV scaling, tint and draw order, and skin weights.
- code: apps/godot/addons/proscenio/builders/mesh_builder.gd:32-113; proscenio_element.gd:15-17
- note: absorbs GD-BUILD-14/15/16/17 and the GD-BUILD-18 skin-path clause; behavior asserted in FLOW-PSD-02 and FLOW-DOLL-03 inspect steps.

### GD-SPRITE-INV · Sprite (Sprite2D) output inventory
- status: pending
- review: keep
- observe: One Sprite2D per sprite element (mesh-type elements are skipped), named after the element. The frame grid columns/rows and the current frame come from the authored values. Centering matches the authored setting (off by default); the offset comes from the authored value when given. The texture region is enabled with edge clipping on and uses the authored rectangle (or the whole texture when none is given). The color tint is applied when the document gives a full color (otherwise white), the draw order is applied, and horizontal/vertical flip come from the authored settings (off by default).
- intent: The sprite builder produces a Sprite2D per sprite element with its frame, region, tint, draw order, and flip fields.
- code: apps/godot/addons/proscenio/builders/sprite_builder.gd:12-87; proscenio_element.gd:18-19
- note: absorbs GD-BUILD-20/21/22/23/24/25/26; behavior asserted in FLOW-PSD-02 inspect step.

### GD-ANIM-INV · AnimationPlayer output inventory
- status: pending
- review: keep
- observe: One AnimationPlayer holding an animation library, with each animation added under its name (an empty animation still adds an empty entry). Per animation: the length is set and looping is on or off per the authored loop flag. The track types produced, only for channels that have keys: bone-transform tracks (position and scale interpolated smoothly, rotation interpolated as an angle); a sprite-frame track on the sprite's frame property stepping between integer frames; and slot-attachment visibility tracks, one per attachment, that turn on only the named attachment at each key time.
- intent: The animation builder produces the AnimationPlayer, its library, each animation's length and loop, and the per-channel transform, frame, and visibility tracks.
- code: apps/godot/addons/proscenio/builders/animation_builder.gd:7-145
- note: absorbs GD-BUILD-29/30 and the GD-BUILD-31/32/33 happy-path track-shape clauses (guard edges live in GD-IMPORT-ANIM-GUARDS-01); behavior asserted in FLOW-DOLL-03, FLOW-PSD-02, FLOW-SLOTSWAP-02 / FLOW-SLOTCYCLE-01 inspect steps. Empty/null-animation default contributes to gap G4.
