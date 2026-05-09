# SPEC 005 — Research addendum

Status: **research notes**, not commitments. Purpose: survey the workflow features that other 2D rigging/animation tools ship so SPEC 005's panel can be planned with the long-term shape in mind, even when the first cut intentionally skips most of these.

The matrix at the bottom (["Proscenio relevance"](#proscenio-relevance-matrix)) maps every observed feature to one of:

- **first cut** — already fits the SPEC 005 TODO scope.
- **5.1** — natural follow-up to the panel; expand here once the foundation lands.
- **004** — belongs to the slot system spec.
- **future** — separate SPEC or backlog.
- **out of scope** — won't ship at all (paid runtime parity, GDExtension territory, etc.).

## Tools surveyed

| Tool | Niche | License |
| --- | --- | --- |
| Spine (Esoteric Software) | industry standard for game-engine 2D skeletal animation | paid |
| DragonBones Pro / LoongBones | open-source Spine alternative; Pro editor + JSON | free / GPL ecosystem |
| COA Tools 2 (Aodaruma) | direct prior art — Blender addon, the project Proscenio inherits the goal of | GPL |
| Blender native | armatures, weight paint, dopesheet, graph editor, NLA | GPL — already on the rails |
| Tiny 2D Rig Tools, Smart GP Controller, Mesh Deform System | Blender addons targeting Grease Pencil + lattice rigging | mixed |
| Spriter Pro | classic 2D modular skeletal animation | paid |
| Live2D Cubism | face/character deformer-driven animation, parameters + physics | paid (free tier limited) |
| DUIK Ángela / Joysticks 'n Sliders / RubberHose | After Effects character animation toolkits | free / paid |

What *each tool exposes well* matters more than "which tool is best" — Proscenio is not competing with paid tools on feature parity, it is filling the open-source Godot gap and lifting the best UX patterns where they fit.

## Workflow features by category

### A. Mode separation (Setup vs Animate)

**Spine** is built around two distinct modes — Setup mode for rig topology and rest pose, Animate mode for keyframing. Switching modes resets what the cursor does and which side panels show. This forces clean separation between "rigging" and "animating" mistakes.

Blender has a parallel concept (Object / Edit / Pose / Weight Paint). The Proscenio panel could *react to the active mode* — show different subpanels, surface contextual operators ("In Pose Mode → bake current pose as new animation key"). First-cut SPEC 005 already touches this implicitly via `poll()` checks on the active object.

**Proscenio relevance:** **first cut** (already implied), with **5.1** polish to add mode-aware subpanels.

### B. Onion skinning / ghost frames

**Spine** renders past + future frames as transparent overlays during animation playback. **DragonBones** has the same. Blender has onion skinning *only for Grease Pencil* — armature-driven 2D rigs do not show ghost frames natively.

For Proscenio's case (cutout meshes deformed by `Polygon2D.skeleton`), a Blender-side overlay that draws the rest pose + N keyframes around the playhead translucent would close a real gap. Implementation: a `bpy.types.SpaceView3D.draw_handler_add` callback that walks the action's keyframes and renders deformed meshes with reduced alpha. Non-trivial but bounded.

**Proscenio relevance:** **future** SPEC. Real value for animators, but custom drawing in viewport is a project on its own.

### C. Dopesheet + graph editor

**Spine**'s dopesheet shows per-property timelines. **Blender already ships** both. Nothing to add — Proscenio rides on Blender's animation editors directly.

**Proscenio relevance:** **out of scope** (Blender owns this).

### D. IK Pose tool

**Spine** has a "Pose tool" that lets you drag an end-effector and the IK solver poses the chain. **DragonBones** ships the same. **Spriter** has IK + IK anchoring. Blender has bone IK constraints but the *daily authoring shortcut* — drag-to-pose-on-canvas — is not the default workflow.

For Proscenio, IK is explicitly out of scope at format level (SPEC 000 — IK is added in Godot post-import via `Skeleton2DIK`). However, *Blender-side* IK during authoring is independent of what gets exported — the user can use Blender's IK constraints freely while authoring. The SPEC 005 panel could surface a "Toggle IK on selected bone chain" helper that scaffolds the constraint stack.

**Proscenio relevance:** **5.1** — small helper, big QoL. Keep it Blender-side; the constraint never leaves Blender.

### E. Mesh editing + FFD

**Spine** has Free-Form Deformation: move individual mesh vertices to deform the image, with each frame storing per-vertex offsets. **Live2D** does the entire animation as deformer-driven mesh edits. **DragonBones** ships mesh editing too.

Blender has full mesh edit mode + shape keys. Proscenio's writer reads the mesh's polygon vertices in winding order — *shape keys would bake into mesh deformation that is lost on export*. The current model assumes the mesh stays static in topology; deformation comes from `Polygon2D.skeleton` weights.

A future SPEC could add "shape key animation" (per-vertex offsets baked into a Godot-side track), but the Godot `Polygon2D` does not support shape keys natively — would need either runtime baking into mesh OR new node type. Heavy.

**Proscenio relevance:** **future** SPEC, low priority. Skinning weights (already shipped in SPEC 003) covers most cases.

### F. Atlas packer integrated into the editor

**Spine** ships its own texture packer. **DragonBones** packs to atlases on export. Currently Proscenio's contract is "atlas is pre-packed externally" — TexturePacker, Free Texture Packer, or a Pillow script.

A Blender-side panel button "Pack atlas from current sprite materials" would auto-discover the linked image textures and build a packed texture + per-sprite `texture_region` rectangles. Open-source packers (e.g. [PyTexturePacker](https://github.com/wo1fsea/PyTexturePacker)) make this feasible without re-implementing packing.

**Proscenio relevance:** **5.1** — large win for new users, but not blocking. First-cut SPEC 005 keeps atlases external.

### G. Skin system (Spine "Skins")

**Spine** has skins: a named set of attachment overrides. Same skeleton, different visual. Used for character variants (color palette, gender, equipment). A skin is conceptually a parallel to slots-with-defaults.

Proscenio's schema does not model skins — it models slots (single-attachment-at-a-time). Skins are a strict superset. **Future** SPEC if a real use case appears.

**Proscenio relevance:** **future**. Slot system (SPEC 004) is the closest equivalent and lands first.

### H. Constraints (transform, path)

**Spine** has transform constraints (a bone copies another's transform with offsets) and path constraints (bone follows a Bezier path). Blender has all of these as native bone constraints — the *export* side is the question. Today Proscenio writes only `bone_transform` per-key animation; constraints are not transmitted.

A future format extension could ship a `constraints` array on bones and the Godot importer would translate to `RemoteTransform2D` or scripted equivalents. Complexity is moderate.

**Proscenio relevance:** **future** SPEC, separate; coordinates with potential `format_version=2` discussion.

### I. Bone hierarchy editor (re-parent without breaking animation)

**Spriter** lets you change a bone's parent mid-animation. Blender's armature edit mode handles re-parenting but animations referencing the renamed/re-parented bone may break.

This is a Blender problem more than a Proscenio one. The Proscenio panel could *warn* when a bone with active animation tracks is about to be renamed/re-parented (write detection logic), but solving the underlying issue is upstream.

**Proscenio relevance:** **future** — defensive helper.

### J. Sticky / quick export

**DragonBones** and **Spine** both have one-click re-export to last-used path. Proscenio SPEC 005 D5 already addresses this.

**Proscenio relevance:** **first cut** ✓ (already in TODO).

### K. Live preview / runtime sync

**Spine** has a runtime preview pane that shows the rig as the game engine will render it. **Live2D** has parameter sliders that drive the live deformer state.

Proscenio's runtime preview is "export → reimport in Godot → see result". A live link (Blender ↔ Godot socket) would close this loop dramatically — the user paints weights in Blender and the Godot editor's preview viewport updates instantly.

This belongs to a deep-integration SPEC (likely needing the GDExtension escape hatch tracked in `specs/backlog.md`, or at minimum a TCP socket protocol on both sides).

**Proscenio relevance:** **future** SPEC, **may force GDExtension reconsideration** — already documented as one of the four triggers in the backlog "Architecture revisits" section.

### L. Lip sync, audio import

**Spriter** has built-in Papagayo lipsync support. **DragonBones** also imports audio.

Proscenio is a static-asset pipeline — no audio in the schema. Animation events / method tracks (already in backlog) cover sound *cues* (when to play) but not authoring lip sync.

**Proscenio relevance:** **out of scope**.

### M. Pose library

**Blender** has a pose library system (Asset Browser → poses). The Proscenio panel could surface a "Save current pose as asset" button → saves the current armature pose to the Asset Browser, retrievable later in any project. Blender already does the heavy lifting.

**Proscenio relevance:** **5.1** polish. Tiny shim, real value.

### N. Mesh symmetry / copy-paste mesh

**Live2D** specifically has mesh copy/paste with horizontal/vertical mirroring — useful for symmetric character parts. Blender has mirror modifiers and symmetry edit but the *manual mesh-mirroring shortcut* is more ceremonious.

For Proscenio, the writer reads the mesh's polygon as-is. If the user has a left arm mesh and wants to derive a right arm mesh, Blender's tools do this — no addon assistance needed. A panel button "Mirror selected sprite around X" might save clicks but is not a unique value-add.

**Proscenio relevance:** **future**, low priority.

### O. Deformers (warp, rotation) — Live2D model

**Live2D**'s entire paradigm is layered deformers parented to bones. A "warp deformer" is a free-form lattice; a "rotation deformer" is a rotation handle that snaps to angle values. Combined with parameter sliders, it is a different mental model from skinned-mesh-on-bones.

This is fundamentally incompatible with Proscenio's `Polygon2D.skeleton` approach. Useful as inspiration only.

**Proscenio relevance:** **out of scope**.

### P. Physics for hair / cloth

**Live2D** has built-in 2D physics simulators on parameters. **Spine** has bone physics (jiggle bones).

Godot has `PhysicsBody2D` + `Joint2D` already; the Proscenio importer could be extended with a `physics` field per bone that wires up simulation post-import. Future format extension.

**Proscenio relevance:** **future**.

### Q. Joysticks / sliders pattern (DUIK)

**Joysticks 'n Sliders** lets you create a 2D "joystick" widget that interpolates between four corner poses (UP/DOWN/LEFT/RIGHT). Beautiful for facial animation (smile/frown/serious/surprised → mix) and head turns (front/3-4/profile/back).

Implementation: a custom panel widget + N corner poses stored as keyframes + interpolation that picks a blend ratio from the joystick position. Godot's `AnimationTree` with a `BlendSpace2D` gives you this at runtime; the Blender side could expose authoring helpers.

**Proscenio relevance:** **future** SPEC — high value, but big design surface.

### R. Auto-rig from layered PSD

**DUIK** auto-rigs limb chains from layered PSDs. **COA Tools** auto-creates a basic skeleton from a layered Photoshop import.

Proscenio already has the Photoshop exporter shipping per-layer PNGs + position JSON. A future Blender-side importer could read that JSON and stamp planes + an initial armature ready for the user to refine.

**Proscenio relevance:** **future** SPEC — natural extension of the Photoshop side. Tracks the broader "Photoshop → Blender importer" backlog item.

### S. Hotkey discoverability (Spine cheat sheet)

**Spine** ships a printed/PDF cheat sheet with all its hotkeys. Blender does too via the F3 search and the Preferences → Keymap panel. The SPEC 005 panel could include a "Shortcuts" section showing the addon's own operators with their bindings (and a "Customize…" button that opens the keymap editor pre-filtered).

**Proscenio relevance:** **5.1** polish — discovery aid for new users.

### T. Export validation (Spine "Issues" pane)

**Spine** has a dedicated Issues pane that lists everything wrong with the project (missing images, atlas overflow, etc.). This is exactly the lazy-validation surface SPEC 005 D6 already chose. Spine's pattern — persistent, click-target rows — is the model.

**Proscenio relevance:** **first cut** ✓ (already in TODO under "Validate operator").

## COA Tools detailed inventory

The first survey pass treated COA Tools 1/2 as a single "panel inspiration" reference. A deeper read of [`Blender/coa_tools/ui.py`](https://github.com/ndee85/coa_tools/blob/master/Blender/coa_tools/ui.py) and the [COA Tools 2 issue tracker](https://github.com/Aodaruma/coa_tools2/issues) reveals features that deserve their own classification — especially the slot-system, mesh-tessellation and animation-events territory.

### Panels and operators worth name-checking

COA Tools 1 ships four panels under a `COA Tools` sidebar tab — Info (deprecation/shading warnings), Object Properties (custom outliner), Cutout Tools (mesh/armature editing), Cutout Animations (animation collection management). Operators of interest:

- **Mesh tessellation from drawn edges** — `coa_tools.generate_mesh_from_edges_and_verts`. User draws an outline, the operator fills it with a triangulated mesh and auto-UVs against the source texture. Similar to Spine's mesh outline tool. The COA 2 backlog ([issue #6](https://github.com/Aodaruma/coa_tools2/issues/6)) wants a stronger version: auto-generate mesh from the image's alpha channel.
- **Reproject sprite texture** — `coa_tools.reproject_sprite_texture`. Re-UV-unwraps a mesh against its texture after edits. Useful when the user adjusts vertices and the UV mapping drifts.
- **Quick armature** — `coa_tools.quick_armature` + `coa_tools.draw_bone_shape`. Click-drag bone drawing tool for rapid skeleton creation without entering Edit Mode by hand.
- **IK suite** — `coa_tools.set_ik`, `coa_tools.set_stretch_bone`, `coa_tools.create_stretch_ik`, `coa_tools.remove_ik`. Single-click IK chain authoring. Authoring-time only — Proscenio still does not export IK constraints (per SPEC 000).
- **Mesh editing helpers** — `coa_tools.pick_edge_length`, `mesh.knife_tool` wired into the panel, surface snap toggle, snap distance, stroke distance.
- **Edit-mode toggles per object** — `obj.coa_tools.edit_mesh`, `edit_armature`, `edit_weights`, `edit_shapekey`. Stored as boolean properties on the object, the panel decides which subsection to show. This is COA Tools' answer to the Spine "Setup vs Animate" mode separation, applied per-object instead of globally.
- **Spriteobject outliner** — `COATOOLS_UL_Outliner` lists sprite_objects + armatures + bones in a custom hierarchical browser with search/filter and favorites. Replaces / supplements Blender's native outliner for the sprite-centric hierarchy.
- **Animation collections** — `COATOOLS_UL_AnimationCollections` plus `coa_tools.add_animation_collection` / `remove` / `duplicate`. Multiple named animations stored on the sprite_object, each with its own end-frame and Action binding. This is essentially `AnimationLibrary` authored in Blender.
- **Timeline events** — `COATOOLS_UL_EventCollection`, `coa_tools.add_timeline_event`, `coa_tools.add_event`. Per-animation event list with frame, type, value, animation reference, target identifier, and integer/float/string parameter slots. Direct parallel to the "Animation events / method tracks" backlog item.
- **Slot system** — `coa_tools.create_slot_object`, `coa_tools.extract_slots`, plus `obj.coa_tools.slot_index` (keyframable). Sprites are merged into a slot_object; animation drives a `slot_index` integer that picks which sub-mesh shows. Direct prior art for [SPEC 004](../004-slot-system/STUDY.md).
- **Per-sprite z-value, alpha, modulate_color** — keyframable transparency, color tint, and depth ordering per sprite. Animatable. Currently not in Proscenio's schema; would extend `Sprite` shape if/when added.
- **Camera + render helpers** — `coa_tools.create_ortho_cam` plus inline render-resolution fields. One-click ortho preview camera matching the project's `pixels_per_unit`.
- **Batch render animations** — `coa_tools.batch_render`. Renders every animation in the sprite_object's `anim_collections` to PNG sequences with one click. Pairs with the camera helper.
- **NLA mode toggle** — `scene.coa_tools.nla_mode` switches the timeline between Action editor and NLA strip workflows.
- **Sprite import from JSON** — `coa_tools.import_sprites` (bulk + single, with JSON metadata import). The pairing with the Photoshop exporter — read the JSX-generated JSON, stamp planes + initial layer order in Blender.
- **Driver constraint shortcut** — `object.create_driver_constraint`. Surfaces driver creation from the panel for facial-rig style "this slider drives that bone" setups.
- **Weight paint controls inline** — brush size / strength / weight / auto-normalize directly in the panel during weight editing.

### COA Tools 2 open roadmap (issues with `enhancement` label)

These are *requested but not yet shipped* in COA Tools 2 — gaps the maintainer is still working on:

- [#28](https://github.com/Aodaruma/coa_tools2/issues/28) — JSON export. **In progress.** COA Tools 2 still lacks the export-to-JSON path that COA Tools 1 had. Confirms Proscenio's premise that the Godot interop side is the project's missing leg.
- [#82](https://github.com/Aodaruma/coa_tools2/issues/82) — Import DragonBones data into Blender. Cross-format interop.
- [#73](https://github.com/Aodaruma/coa_tools2/issues/73) — Non-destructive weight transfer between layers with identical mesh topology using modifiers.
- [#69](https://github.com/Aodaruma/coa_tools2/issues/69) — Outliner enhancements: layer group display, name abbreviation.
- [#66](https://github.com/Aodaruma/coa_tools2/issues/66) — `StateData` property for smooth transition animation between sprites (between slot attachments). Related to slot system but with crossfade.
- [#48](https://github.com/Aodaruma/coa_tools2/issues/48) — Mask sprite object (alpha mask via sprite).
- [#47](https://github.com/Aodaruma/coa_tools2/issues/47) — Sliders for shapekeys + advanced 2D rigging features. The Joysticks-n-Sliders pattern in Blender.
- [#18](https://github.com/Aodaruma/coa_tools2/issues/18) — Copy/link mesh, weight, shapekey from one sprite to another. Symmetric character authoring.
- [#11](https://github.com/Aodaruma/coa_tools2/issues/11) — Sprite composite/blend modes.
- [#6](https://github.com/Aodaruma/coa_tools2/issues/6) — Auto-generate mesh from image alpha channel.

### Updated relevance for COA-specific items

These rows extend the matrix at the bottom of this document — they are not duplicates but the COA-specific findings the wider survey did not surface.

| Feature | When |
| --- | --- |
| Animation collections (multiple named animations per sprite_object) | Already implicit — Blender `Action` per `bpy.data.actions`; writer iterates them. Panel could surface a list view that shows them with end-frame + rename. **5.1** polish. |
| Timeline events / cue keyframes | **future** SPEC, paired with animation events / method tracks (already in `specs/backlog.md`). |
| Per-sprite alpha / z-value / modulate_color, animatable | **future** SPEC + format extension. Adds three optional fields to `Sprite`, three optional track types. Real value for fade-ins, stack-order shuffles, color flashing. |
| Slot crossfade (`StateData`-style smooth transition between slot attachments) | **future** within / after SPEC 004. Slot system in COA hard-cuts; smoother transitions are a follow-up. |
| Mask sprite object (alpha mask via sprite) | **future** SPEC, low priority. Godot has `CanvasItem.material` with mask shaders; format extension would hook this. |
| Sprite composite / blend modes | **future** SPEC + format extension. Maps to Godot's `CanvasItemMaterial.blend_mode`. Trivial schema field, larger writer/importer wiring. |
| Mesh tessellation from drawn outline (auto-fill triangles) | **future** SPEC — significant tooling, classic "draw shape, get mesh" feature. |
| Auto-generate mesh from image alpha | **future** SPEC — pairs with the previous; uses image alpha as the source outline. |
| Reproject sprite texture (re-UV after vertex edits) | **5.1** if cheap, otherwise **future**. Blender has UV unwrap operators; the addon would just chain them. |
| Quick armature (click-drag bone drawing) | **5.1** — small operator, big speed win for new rigs. |
| IK suite shortcuts (Set IK / Stretch IK / Remove IK) | **5.1** — operators that scaffold Blender's native bone constraints. Stays Blender-side, never exported. |
| Edit-mode toggles per object (boolean flags drive panel UI state) | **first cut** — already implicit in SPEC 005 D2 (PropertyGroup wraps Custom Properties). Documented as the COA-1 pattern. |
| Spriteobject outliner (custom hierarchical browser with search/filter/favorites) | **5.1** — Blender's native outliner is fine for first cut; custom outliner is polish for big rigs. |
| Sprite import from JSON (Photoshop exporter integration) | **future** SPEC — pairs with the existing apps/photoshop work. Already in the long-term backlog seeds. |
| Bulk batch render of animations | **future** SPEC — useful for art-team turnaround. Low priority for engine-targeted assets. |
| NLA mode toggle (Action vs NLA strip authoring) | **future** — Blender exposes both natively; toggle would be a minor convenience. |
| Driver constraint shortcut | **5.1** — single button that wraps `object.create_driver_constraint` with sensible defaults. |
| Camera + render resolution helpers (one-click ortho cam matching `pixels_per_unit`) | **5.1** — already in [`specs/backlog.md`](../backlog.md) as "Camera orthographic preview helper". |
| Inline weight paint brush controls | **5.1** — Blender already exposes them in tool settings; a panel mirror is convenience. |
| Non-destructive weight transfer between layers with identical mesh topology | **future** SPEC, low priority — power-user feature for character variants sharing skeleton + mesh shape. |
| Import DragonBones data into Blender | **future** — interop helper, low priority for Proscenio's primary path. |

## Cross-cutting UX patterns

Three patterns appear across most tools:

1. **Inspector-style panels** that change content based on the active selection (Spine sidebar, Spriter properties, DragonBones).
2. **Hover-revealed micro-tooltips** explaining each property, often with a link to docs.
3. **Right-click context menus** on tree items / timeline rows with quick operators.

Blender's Properties Editor + N-key sidebar already provide #1 and #3 natively; SPEC 005's panel rides on this. Tooltips (#2) come for free with Blender's `bl_description` on properties — a low-cost discipline.

## Mockup notes for SPEC 005 panel evolution

Sketch of the layout *post-005-shipping*, with 5.1 enrichments dotted in:

```text
N-key sidebar
└── Proscenio tab
    ├── Active sprite               [first cut]
    │   ├── Sprite type dropdown
    │   ├── [if sprite_frame] hframes / vframes / frame / centered
    │   ├── Vertex-group summary    [first cut, read-only]
    │   ├── Atlas region helper     [5.1]
    │   └── Mirror-X helper         [future, low-priority]
    │
    ├── Skeleton                    [first cut: read-only summary]
    │   ├── Bone count + naming sanity
    │   ├── Pose library buttons    [5.1]
    │   ├── IK chain helper         [5.1]
    │   └── Onion-skin viewport overlay  [future SPEC]
    │
    ├── Slots                       [SPEC 004]
    │
    ├── Skins                       [future SPEC, post-004]
    │
    ├── Animation                   [first cut: ride on Blender's editors]
    │   ├── Active action info
    │   ├── Bake current pose       [5.1]
    │   └── Joystick/slider authoring  [future SPEC]
    │
    ├── Atlas                       [first cut: read-only filename]
    │   └── Pack from materials     [5.1]
    │
    ├── Validation                  [first cut]
    │   ├── Inline status icons     [first cut]
    │   ├── Issues list             [first cut, SPEC 005 D6]
    │   └── Click-to-select         [5.1]
    │
    ├── Export                      [first cut]
    │   ├── Sticky path
    │   ├── Pixels-per-unit
    │   ├── [Validate] button
    │   ├── [Export] button
    │   └── [Re-export] silent      [first cut]
    │
    ├── Live link                   [future, may force GDExtension reconsideration]
    │
    └── Help                        [5.1: shortcut cheat sheet]
```

## Long-term backlog seeds

These came up during the survey and should be carried into [`specs/backlog.md`](../backlog.md) when SPEC 005 closes (separate from the SPEC 005.1 list inside [TODO.md](TODO.md)):

- **Joystick / slider authoring** — multi-pose blend widget; pairs well with Godot's `AnimationTree.BlendSpace2D`.
- **Onion-skin overlay** — viewport draw handler showing rest pose + N keyframes around playhead.
- **Live link Blender ↔ Godot** — TCP / WebSocket protocol with optional GDExtension. Already a trigger in "Architecture revisits".
- **Photoshop → Blender importer** — read the JSX exporter's JSON, stamp planes + skeleton in Blender. Pairs with the existing apps/photoshop work.
- **Bone physics** — `format_version=2` extension; importer wires `Joint2D` chains.
- **Pose library shim** — Blender Asset Browser integration.
- **IK chain helper** — Blender-side scaffolding (constraint stack), still no IK in `.proscenio` per SPEC 000.
- **Path constraint export** — `format_version=2` extension; importer wires path-following.

## Proscenio relevance matrix

| Feature | Source | When |
| --- | --- | --- |
| Sticky export path | Spine, DragonBones | first cut |
| Issues pane / lazy validation | Spine | first cut |
| Active-object subpanel | universal | first cut |
| Vertex-group summary | Live2D, COA Tools 2 | first cut |
| Mode-aware subpanels (Pose/Object) | Spine | 5.1 |
| Atlas packer integration | Spine, DragonBones | 5.1 |
| Pose library shim | Blender native | 5.1 |
| IK chain helper (Blender-side) | Spriter, Spine, DragonBones | 5.1 |
| Atlas region helper | Spine | 5.1 |
| Bake-current-pose-as-key | Blender native | 5.1 |
| Shortcut cheat-sheet panel | Spine | 5.1 |
| Slot list editing | Spine | SPEC 004 |
| Skin system | Spine | future SPEC |
| Bone constraints export | Spine | future SPEC + format v2 |
| Path constraints export | Spine | future SPEC + format v2 |
| Bone physics | Spine, Live2D | future SPEC + format v2 |
| Onion-skin viewport overlay | Spine, DragonBones | future SPEC |
| Joystick / sliders authoring | DUIK | future SPEC |
| Photoshop → Blender importer | DUIK, COA Tools | future SPEC (paired with apps/photoshop) |
| Live link Blender ↔ Godot | (none — novel) | future SPEC, may force GDExtension reconsideration |
| Mesh shape-key animation | Spine FFD, Live2D | future SPEC, low priority |
| Mesh mirror helper | Live2D | future, low priority |
| Lip sync | Spriter | out of scope |
| Live2D-style deformer model | Live2D | out of scope |
| Audio import | Spriter | out of scope |
| Free-form deformer per-frame baking | Spine, Live2D | out of scope |

Sources:

- [Spine — In Depth Features](https://esotericsoftware.com/spine-in-depth)
- [Spine — Dopesheet view](http://esotericsoftware.com/spine-dopesheet)
- [Spine — Keys (animation editor)](http://en.esotericsoftware.com/spine-keys)
- [Spine — Cheat Sheet](http://en.esotericsoftware.com/spine-cheat-sheet)
- [DragonBones — Animation Solution](https://dragonbones.github.io/en/animation.html)
- [DragonBones — Features](http://dragonbones.effecthub.com/features.html)
- [Aodaruma — COA Tools 2 (GitHub)](https://github.com/Aodaruma/coa_tools2)
- [Live2D Cubism — Editor Manual](https://docs.live2d.com/en/cubism-editor-manual/)
- [Live2D Cubism — Mesh Edit Manual](https://docs.live2d.com/en/cubism-editor-manual/mesh-edit-manual/)
- [Live2D Cubism — About Deformers](https://docs.live2d.com/en/cubism-editor-manual/deformer/)
- [Spriter Pro — Manual (BrashMonkey)](http://www.brashmonkey.com/spriter_manual/getting%20started.htm)
- [Spriter Pro — Bones (BrashMonkey)](https://brashmonkey.com/spriter_manual/creating%20and%20assigning%20bones.htm)
<!-- cspell:disable-next-line -->
- [DUIK Ángela (RxLaboratorio)](https://rxlaboratorio.org/rx-tool/duik/)
- [Blender — Animation & Rigging](https://www.blender.org/features/animation/)
- [Tiny 2D Rig Tools (NickTiny, GitHub)](https://github.com/NickTiny/Tiny-2D-Rig-Tools)
- [School of Motion — Joysticks 'n Sliders vs DUIK Bassel](https://www.schoolofmotion.com/blog/after-effects-tool-review-joysticks-n-sliders-vs-duik-bassel)
- [School of Motion — DUIK vs RubberHose](https://www.schoolofmotion.com/blog/duik-vs-rubberhose)
