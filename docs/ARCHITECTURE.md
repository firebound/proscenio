# Architecture - systems by plugin

A technical map of the project, derived from the code itself (registrations, imports, call graphs, function signatures) rather than from docstrings or comments. It groups the work into the concrete systems each plugin runs, the data each one moves, and where the complexity and risk actually sit.

## The spine: the cross-app pipeline

The three plugins form one conveyor belt. A character is drawn in Photoshop, rigged and animated in Blender, and turned into a playable scene in Godot:

```text
PSD ──[Photoshop]──> manifest.json + PNGs ──[Blender import]──> Blender scene
                                                                     │
                                       authoring: mesh, weights, rig, slots, atlas
                                                                     │
       .scn <──[Godot import]── .proscenio + atlas <──[Blender export]
```

What ties it together is a **single data model as the source of truth**: the schemas written as pydantic models (`packages/models/`), and a codegen step that generates the JSON Schema, the TypeScript types, and the Godot Resources from them. In practice, Blender **writes** the `.proscenio` file by building a typed pydantic object (`ProscenioDocument(...).model_dump_json()`), and Godot **reads** the same file as a typed Resource (`ProscenioDocument.from_dict(...)`). Both ends speak the same format with nobody hand-maintaining a loose dictionary.

## Photoshop - UXP plugin (React + TypeScript)

Turns a layered PSD into a manifest plus PNGs that Blender can import. The code is layered cleanly: an adapter isolates the Adobe API, the domain holds the pure (testable) logic, and the `io/` layer concentrates the side effects (reading and writing files, calling the Photoshop API) so the domain stays platform-free.

| System | What it does | Key files |
| --- | --- | --- |
| **Document adapter** | Converts the Photoshop API's document and layers into its own `Layer` model. Acts as a boundary so the rest of the code never touches the Adobe API directly. | `adapters/photoshop-layer.ts` |
| **Tag system** | Reads and writes bracket markers in the layer name (`[ignore]`, `[merge]`, `[spritesheet]`, `[folder]`, `[scale]`, `[origin]`, and more). This is how the artist drives the export without leaving Photoshop. | `domain/tag-parser`, `tag-writer`, `tag-tree`; `io/layer-rename` |
| **Planner** | The heart of the export: walks the layer tree and produces the manifest (each layer becomes a `polygon`, `mesh`, or `sprite_frame` entry), the list of PNGs to write, the warnings, and what was skipped. Resolves draw order (z-order), `[merge]` groups, automatic spritesheet detection, pivot, and scale. | `domain/planner.ts`, `domain/manifest.ts` |
| **Manifest validation and I/O** | Validates the manifest with ajv (a runtime JSON Schema validator) **before** anything is written to disk, so an invalid manifest never reaches Blender. Plus the JSON reader and writer. | `io/manifest-validator` (ajv), `manifest-reader`, `manifest-writer` |
| **PNG export** | Renders each layer region to a PNG, reading the bounding box from the Photoshop selection. | `io/png-writer`, `png-placer`, `ps-selection`, `ps-selection-bounds` |
| **Orchestration (export / import)** | Wires it all together. Export: adapt the document, build the plan, validate, then write PNGs + manifest inside one Photoshop modal (`executeAsModal`); the manifest is saved only if **every** PNG succeeded, so it never points at missing files. Import runs the reverse: from a manifest plus PNGs it **rebuilds a fresh PSD**. | `controllers/export-flow`, `import-flow` |
| **UI and cross-cutting** | The panels (Exporter, Tags, Validate, Debug) with their sections and reactive hooks, plus supporting parts: XMP metadata (so pixels-per-unit survives the round trip), a persistent output folder, and migration of old manifests (v1 to v2). | `panels/**`, `hooks/**`, `io/xmp`, `folder-storage`, `*/legacy-migration` |

## Blender - Python addon

The addon registers three groups: `properties`, `operators`, and `panels`.

**Before the systems, the data store.** Each object carries a `ProscenioObjectProps` (reached as `Object.proscenio`) and the scene carries a `ProscenioSceneProps`. These are *PropertyGroups* - Blender's typed structure for storing data on objects. Each field is also mirrored to a raw *Custom Property* (a loose key/value on the object), because the Custom Property is more resilient: it survives the addon being disabled and is a stable target for animation drivers. The mirroring is done by `hydrate` / `cp_keys` / `pg_cp_fallback`.

| System | What it does | Operators / core |
| --- | --- | --- |
| **Automesh** | Builds the sprite's mesh from the image alpha: it detects the silhouette, then triangulates the interior with CDT (constrained Delaunay triangulation - a triangle mesh that respects the outline). It has an interactive authoring mode (a modal) with a GPU overlay where the artist edits the contour, adds points, and cuts. The geometry logic is **pure** (`core/automesh`, no Blender) and kept separate from the bridge that touches bmesh (`core/bpy_helpers/automesh`), which is why it can be tested outside Blender. | `automesh`, `automesh_authoring`, `bind_mesh` |
| **Skinning (weight paint)** | Binds the mesh vertices to the bones. It does the initial bind by in-plane proximity, has a weight-paint modal with a 2D-appropriate preset, and keeps a **sidecar** - a parallel JSON that records each weight's provenance (hand-painted, reprojected, auto-generated) and survives a mesh regeneration. Includes copying weights between sprites and snapshot/restore. | `edit_weights`, `brush_preset`, `copy_weights_to_selected`, `restore_weight_snapshot`, `sidecar_io`; `core/skinning` |
| **Quick Armature** | A modal for drawing the bone chain by extruding in the viewport, locked to the XZ plane in front-orthographic view. The chain math is pure and tested separately. | `quick_armature`; `core/quick_armature_math` |
| **Slot system** | Sprite-swap groups (for example, swapping a closed hand for an open one). Creates the slot, attaches the attachments, and has a preview shader. | `slot/create`, `slot/attachment`, `slot/preview_shader`; `core/slot_emit` |
| **Atlas packing** | Packs, unpacks, and applies UV regions into a single texture atlas. | `atlas_pack/*`; `core/atlas_packer` |
| **PSD import** | Consumes the Photoshop manifest plus PNGs and builds the planes (Polygon2D quads) and, optionally, the armature. | `import_photoshop`; `importers/photoshop/{planes,armature}`; `core/psd_manifest` |
| **Godot export** | Discovers the armature, sprites, and atlas in the scene (`scene_discovery`), calls one builder per aspect (`build_skeleton`, `build_sprite`, `build_slots`, `build_animations`, `build_slot_animations`), and assembles a `ProscenioDocument` that becomes the `.proscenio` file. | `export_flow`; `exporters/godot/writer/*` |
| **Animation authoring** | Rigging and animation shortcuts: "drive from bone" (a driver linking a sprite's frame to a bone), per-bone IK/FK toggle, a pose library (on top of Blender's native system), an orthographic preview camera, and an IK helper. | `driver`, `set_bone_mode`, `pose_library`, `authoring_camera`, `authoring_ik` |
| **Support** | UV authoring (bounds), the armature picker, selection helpers, validation, help dispatch, and utilities (error reporting, mirroring, viewport state). | `uv_authoring`, `skeleton_target`, `selection`, `help_dispatch`; `core/validation`, `core/{report,mirror,viewport_state,...}` |

## Godot - editor plugin (GDScript)

Small and focused: a single import plugin plus five builders.

| Component | What it does |
| --- | --- |
| **Import plugin** (`importer.gd`) | An `EditorImportPlugin` - Godot runs it whenever a `.proscenio` enters the project. It reads the JSON as a typed Resource (`ProscenioDocument.from_dict`), checks the `format_version`, builds the node tree, and saves it as a `.scn` scene. Order matters: skeleton, then atlas, then **slots before sprites** (so sprites can be parented under the slot node), then sprites, then animation. |
| **The five builders** | Each one builds a slice of the scene, and **each only handles what it recognizes**: it reads the `type` field on each sprite in the JSON, processes the ones that are its own, and ignores the rest - there is no inheritance or polymorphism, just functions called in sequence. They are: `SkeletonBuilder` (Skeleton2D + Bone2D), `SlotBuilder` (the slot nodes), `PolygonBuilder` (Polygon2D with weights, for `polygon`/`mesh` sprites), `SpriteFrameBuilder` (Sprite2D with a frame grid), and `AnimationBuilder` (fills the AnimationPlayer with the tracks: `bone_transform`, `sprite_frame`, `slot_attachment`, `visibility`). |
| **Reimporter + node_name_util** | Re-import by overwrite (with the wrapper-scene pattern) and collision-safe naming. |
| **Plugin + schema_bindings** | `plugin.gd` registers the import plugin with the editor; `schema_bindings/` is the typed read layer generated from the schema. |

## Quality and structure (read from the code)

### Strengths

- **A single data model links all three apps.** It is not a loose dictionary at the ends: Godot reads typed and Blender writes typed, both from the same schema. Changing a field is a change in one place.
- **In Blender, the pure geometry is separated from the Blender-bound code.** In automesh and skinning, the math lives in modules with no `bpy`, and a thin bridge talks to Blender. That is what lets the ~500 tests run without opening Blender.
- **In Photoshop, the layers are clean.** The adapter isolates the Adobe API; the domain (planner, tags) is pure logic and runs under vitest; `io/` is where the side effects live; the controllers only orchestrate. Validation (ajv) runs before touching the disk.

### Watch points

These are not bugs - they are where the complexity and risk live.

- **Blender is the heavy app** (78 modules in `core/`, 30 operators). The two riskiest systems are the **automesh authoring modal** (multi-stage, a lot of state and an overlay) and the **skinning** sidecar/provenance work: plenty of mutable state and only headless smoke coverage, because they depend on Blender. That is where regressions tend to hide.
- **The dual storage (PropertyGroup mirrored to a Custom Property)** is resilient, but it is the addon's subtlest coupling - sync, undo, and the hydrate timing. It is already in the backlog to be split by intent before 1.0.
- **The Photoshop round trip is asymmetric.** The plugin imports (rebuilds a PSD) and exports, but details like the "waist -1px" drift and the pixels-per-unit that does not come back identical (both in the backlog) show the PSD-to-PSD cycle is not lossless. That is acceptable because the real consumer is Blender, not Photoshop.
- **The Godot importer is single-version** (`SUPPORTED_FORMAT_VERSION = 1`, no migrator). Rigid by design until a v2 exists.
