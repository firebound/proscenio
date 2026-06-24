# Godot Plugin

A GDScript editor plugin: a single [`EditorImportPlugin`](https://docs.godotengine.org/en/stable/classes/class_editorimportplugin.html) plus a handful of builders that turn a `.proscenio` file into a native Godot scene on every reimport.

## What it does

- **Reimport to a native scene.** The plugin regenerates a scene (Skeleton2D + Bone2D + Polygon2D / Sprite2D + AnimationPlayer) whenever a `.proscenio` file enters or changes in the project. Reimport overwrites the generated scene wholesale - it rebuilds the tree from scratch and there is no diff or merge against the previous output, because the `.proscenio` is the source and the scene is a generated artifact the engine owns. The generated scene runs with the plugin uninstalled: it is plain Godot 4 nodes, no GDExtension and no runtime dependency.
- **Wrapper-scene safety.** Because reimport overwrites, edits never live inside the generated scene; the supported way to keep them is to wrap the generated scene in your own `.tscn` that instances it. The wrapper holds your scripts, extra nodes, and its own `AnimationPlayer`, so it survives every reimport untouched.
- **Typed read.** The importer reads the document as a typed Resource (`ProscenioDocument.from_dict`), checks the `format_version`, and builds the node tree in order: skeleton, atlas, slots before sprites, sprites, animation.

## How it is built

Small and focused: one import plugin and five builders, each handling only the node types it recognizes by reading the `type` field on each element. No inheritance or polymorphism, just functions called in sequence. The typed read layer is generated from the schema.

## The importer surface

The plugin registers a single `EditorImportPlugin` whose identity is fixed in code, not configurable per file:

- It claims the `.proscenio` extension, presents in the editor's **Import** dock as `Proscenio Character`, and bakes each source to a `.scn` `PackedScene`.
- It declares one preset, `Default`, and exposes no per-import options - the options list is empty, so the **Import** dock shows the preset with nothing to tune. A reimport is driven entirely by the `.proscenio` contents, never by import-dock settings.
- It runs at import order `100`, the engine's own scene-import order, so it bakes after the default-order resources. That ordering is load-bearing: the bake resolves the atlas and per-element PNGs through `ResourceLoader` against the sibling files, and at the default order a `.proscenio` could bake before its textures import and ship a scene with blank textures.

## Elements: mesh and sprite

Each entry in the document's `elements` array carries a `type` that selects the node a builder emits. An entry with no `type` is read as a mesh - the default lives in the typed read layer, so an untyped element is never dropped.

A `type: "mesh"` element becomes a `Polygon2D`. The builder reads:

- `polygon` - the outline ring, as `[x, y]` pairs.
- `polygons` - optional per-face vertex-index arrays for multi-face meshes (automesh triangulation, multi-island cutouts); each face renders through `Polygon2D.polygons`. Absent or empty means the single `polygon` ring is the whole shape.
- `uv` - normalized `[0, 1]` coordinates, scaled to texture pixels at build time; a mesh with no texture keeps the raw values.
- `weights` - per-bone vertex weights that skin the mesh (see Slot routing for how a skinned mesh is parented).
- `texture`, `texture_region`, `modulate`, `z_index` - the shared appearance fields below.

A `type: "sprite"` element becomes a `Sprite2D`. The builder reads:

- `hframes`, `vframes`, `frame` - the spritesheet grid and the displayed cell.
- `centered`, `offset` - the Sprite2D pivot and pixel offset.
- `texture_region` - an optional atlas sub-rect, normalized `[0, 1]` like mesh UVs and converted to pixels once the texture size is known. The region is enabled only when a texture is present and the pixel rect can be set in the same pass; a texture-less sprite ships with the region disabled (an enabled zero-area rect would draw nothing). When the region is enabled the builder also clips the texture filter to the region edge so neighbouring atlas frames do not bleed in at the seam.
- `flip_h`, `flip_v` - the Sprite2D-only horizontal and vertical flips.
- `texture`, `modulate`, `z_index` - the shared appearance fields below.

`modulate` (an RGBA tint) and `z_index` (draw order) apply to both kinds; an absent `modulate` keeps Godot's default white. Both kinds resolve their texture the same way, in order: the element's own `texture` filename loaded next to the `.proscenio`; failing that, `<element name>.png` next to the `.proscenio` (filename by convention); failing that, the document-wide `atlas`.

A multi-frame `sprite` is the case behind the preview note below.

## Slot routing and default visibility

Slots let several elements share one anchor and swap at runtime. The slot builder runs before the element builders so the elements can route under a slot:

- Each entry in the document's `slots` array becomes a `Node2D` named after the slot. It parents under the matching `Bone2D` when the slot names a `bone`, or under the `Skeleton2D` root when `bone` is empty or the named bone is missing (a missing bone logs a warning and anchors at the root).
- Every name in the slot's `attachments` array is mapped to that slot. An element whose name is in some slot's attachments re-parents under the slot `Node2D` instead of bone-parenting.
- The slot's `default` names the attachment shown at rest: that one element starts visible, every other attachment in the slot starts hidden, and a `slot_attachment` animation track flips them at runtime.

An element that is in no slot falls back to parenting under its `bone`'s `Bone2D` (or the skeleton root when the bone is absent), and stays visible. A skinned mesh (one carrying `weights`) is the exception to all of the above: it must be a sibling of the `Skeleton2D`, so it parents under the skeleton's parent (the rig root) and is never routed into a slot or under a bone; if the `Skeleton2D` has no parent the builder skips that mesh and logs an error rather than ship a collapsed shape.

## Animation tracks

Animations become one `AnimationLibrary` on the `AnimationPlayer`, with each document animation contributing its `length` and `loop` flag. The builder emits three track types, selected by each track's `type`; an unrecognized type logs a warning and is skipped:

- `bone_transform` - targets a `Bone2D` and emits up to three value tracks, `position`, `rotation`, and `scale`. Only the channels actually present in the keys are emitted, so a position-only animation registers no phantom rotation channel that would reset the pose. Rotation interpolates with the angle-aware cubic mode so it wraps correctly at +/-pi; position and scale use plain cubic.
- `sprite_frame` - targets a `Sprite2D` (and only a sprite element; a non-sprite target logs an error) and keys its `frame`. Frame indices are discrete, so the track uses nearest interpolation with no blending.
- `slot_attachment` - targets a slot `Node2D` and emits one visibility track per attachment child. At each key the attachment named in the key is the only visible one; swaps are hard cuts (nearest interpolation), not blends.

Tracks resolve their targets by leaf name through `find_child`, which is why node names are kept verbatim (see Node names).

## Node names

Builders set each node's name to its element name verbatim. When two siblings collide, Godot's `add_child` auto-appends a numeric suffix (`_001`, `_002`, ...) - that suffix is Godot's, not something the plugin writes. The importer never disambiguates by *prefixing* a kind (no `sprite_foo` / `mesh_foo`), because animation tracks resolve their targets by leaf name through `find_child(target, ...)`: a prefix would change the name a track looks for and break the lookup, while a numeric suffix only ever lands on a name that was already ambiguous.

## Sprite preview differs from Blender

A multi-frame `sprite` element renders in Godot as a `Sprite2D` showing one frame at its native pixel size (`region_px / hframes`), while Blender shows the whole authored quad. This is inherent to the model, not an import bug: pixel-exact Blender and Godot previews are not achievable for multi-frame sprites by design, the invariant is geometry and bounds rather than pixels. The authoring rule that keeps the bounds matching, `quad_units = frame_px / pixels_per_unit`, lives with the fixtures (`packages/fixtures/README.md`, "Sprite quads (multi-frame)").

See [Architecture](../../01-project/01-architecture.md) for how the plugin fits the pipeline, and the Schema reference for the `.proscenio` format it reads: the [document](../../content/proscenio/document.mdx) shape, the [elements](../../content/proscenio/elements.mdx) and [slots](../../content/proscenio/slots.mdx) field contracts, and the [animation](../../content/proscenio/animation.mdx) tracks and keys.
