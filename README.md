# Proscenio

> [!WARNING]
> Proof of Concept / WIP. Format unstable. Not for production use.

Photoshop → Blender → Godot 4 pipeline for 2D cutout animation. Native scenes, no runtime.

## What Proscenio is

Proscenio is an open-source pipeline tool that lets artists rig and animate 2D cutout characters in Blender, then ship them into Godot 4 as native scenes. The Godot output is a regular `Skeleton2D` + `Bone2D` + `Polygon2D` + `AnimationPlayer` tree - no GDExtension, no custom runtime, no plugin required to play the scene at runtime.

The bridge between Blender and Godot is a single versioned JSON contract (`.proscenio`). The Photoshop side feeds Blender via a parallel manifest contract. Each component owns one job; the schema is the only thing they share.

Blender is the chosen DCC (Digital Content Creation tool, the software where art and animation are authored) on purpose: open source like the rest of the Firebound stack, free of license cost, and equipped with a mature animation toolset (dopesheet, NLA, drivers, weight paint, vertex groups, shape keys). The artist authors in software they likely already know; no proprietary DCC license enters the dependency chain.

## Who it's for

Artists and game devs who want a practical, friction-free 2D cutout workflow on Godot 4, where each tool plays to its strength:

- **Photoshop** for raster art - paint, layer, organize.
- **Blender** for everything animation - rig, weight, keyframe, NLA, drivers.
- **Godot** as the final game engine - native scenes, no proprietary runtime.

What Proscenio gives you:

- The three tools wired end-to-end, no manual hand-off between them. PSD layers carry their pivot, naming, and atlas region into Blender; Blender's rig and animations carry into Godot as native `Skeleton2D` + `Polygon2D` + `AnimationPlayer`.
- An open-source alternative to Spine and to abandoned Godot importers for COA Tools.
- Output that survives plugin uninstall - generated scenes are plain Godot 4 nodes you can ship without Proscenio installed.

## Pillars

| Pillar | Promise | How it delivers |
| --- | --- | --- |
| **Non-destructive integration** | Source files and engine work survive every reimport. | `.psd` and `.blend` are read-only sources; Godot reimport clobbers only the generated `.scn`; user-authored `.tscn` wrappers, scripts, and extras stay intact. |
| **Engine-native output** | Shipped game runs without Proscenio installed. | `.scn` uses Godot core nodes only. No GDExtension, no custom runtime. |
| **Each tool to its strength** | No proprietary editor in the chain. | Open-source pipeline (Blender, Godot, schemas, addons); no Spine-style DCC license. |
| **Direct manipulation in the DCC** | No proprietary modes layered on top of Blender. | Shortcuts (Quick Armature, Drive from Bone, Create Slot) sit on top of native operators - never replace them. |
| **Predictable contract** | What leaves Blender is what arrives in Godot, byte-checked. | Versioned JSON contract validated at 6 gates (IDE, pre-commit, CI Python lint, CI Photoshop lint, CI Blender, CI Godot). Strong typing across the pipeline: Python on the Blender side, TypeScript on the Photoshop UXP plugin, GDScript on the Godot importer. Format bumps require explicit migrators. |

## Components

| Component | Tech | Role |
| --- | --- | --- |
| Photoshop side ([`apps/photoshop/`](apps/photoshop/)) | UXP plugin, TypeScript + React | PSD → manifest JSON + per-layer PNGs. Optional manifest mirror back to PSD. Photoshop CC 2021+. |
| Blender side ([`apps/blender/`](apps/blender/)) | Python 3.11, mypy `--strict` | Manifest import, sprite/armature authoring panel, validation, `.proscenio` writer. |
| Godot side ([`apps/godot/`](apps/godot/)) | GDScript 2.0 typed | `EditorImportPlugin` reading `.proscenio` and regenerating `.scn` on every reimport. |
| Schema ([`schemas/`](schemas/)) | JSON Schema 2020-12 | Source of truth. `proscenio.schema.json` (Blender↔Godot) and `psd_manifest.schema.json` (Photoshop↔Blender). |

## In scope

### Photoshop side

- Recursive layer walk → per-layer PNG export.
- PSD layer hierarchy → manifest JSON with `kind` discriminator (`polygon` | `sprite_frame`).
- Sprite-frame group detection: numeric children inside a layer group (primary) + `<name>_<index>` flat-naming fallback.
- Manifest mirror back to PSD (round-trip).
- Schema-versioned manifest (`MANIFEST_FORMAT_VERSION` lockstep with `psd_manifest.schema.json`).

### Blender side

Heavy lift lives here. Features grouped by workflow theme.

#### Source-art ingestion

- **Import Photoshop Manifest** operator: manifest JSON becomes planes + stub armature + naming convention pre-populated, ready to rig.
- PropertyGroup-canonical metadata layered on the imported objects, with Custom-Property fallback for legacy reads.

#### Rigging

- **Quick Armature**: click-drag bone drawing in the viewport, Shift-chain modal handler. Output is a normal Blender armature; refine in Edit Mode as usual.
- **Toggle IK** shortcut: scaffolds Blender's native IK constraint without leaving the panel.
- **Bake Current Pose** + **Save Pose to Library**: authoring shortcuts that ride on Blender's pose-library asset system.
- **Drive-from-Bone**: one-click Blender driver wiring from a pose bone to a sprite property (frame index, region, custom prop). For gradual mappings; hard swaps go through the slot system instead.

#### Mesh authoring

- Native Blender mesh edit on plane primitives. No proprietary mode; use the tools the artist already knows (Knife, Loop Cut, vertex sliding, snapping).
- Vertex-group naming matches Blender bones to schema bones at write time.
- Procedural mesh from contour (drawn outline or image alpha) is on the deferred roadmap.

#### Weight painting

- Native Blender weight paint, vertex groups named after target bones. Writer reads vertex-group weights into the `weights[]` array on each `Sprite`.
- Per-vertex weights survive into Godot as real `Polygon2D.skeleton` deformation, not rigid attachment.
- Symmetric weight transfer between sprites with matching topology is a deferred convenience.

#### Texturing and atlas

- **Atlas packer**: pipeline-specific atlas layout that emits a single `atlas` per character with row-packed regions.
- **Sliced atlas** + **Unpack**: split a packed atlas back into its source images for re-edit, then repack.
- **Texture region authoring**: auto-compute the atlas region from UV bounds, or slice manually for spritesheet variants.
- **Snap to UV bounds** operator: populate the region from the current UV in one click.
- **Material-Preview shader**: drives sliced UV from `frame` index so the artist previews the spritesheet cell choice in the 3D viewport without exporting.

#### Sprite metadata

- **Active Sprite** subpanel: sprite type dropdown (`polygon` for cutout meshes, `sprite_frame` for spritesheets).
- Spritesheet metadata: `hframes` / `vframes` / `frame` / `centered`, animatable.
- Per-sprite `proscenio.is_slot` flag and `proscenio_slot_index` (keyframable).

#### Slot system (SPEC 004)

- **Create Slot** operator: anchors an Empty under the active bone and parents the selected meshes as attachments.
- **Active Slot** subpanel: pick the default attachment at scene load (SOLO icon), reorder attachments, animate `proscenio_slot_index` to flip per keyframe.
- Kind-agnostic: polygon meshes and sprite_frame attachments compose freely inside the same slot.

#### Organization

- **Custom Outliner** subpanel (5.1.d.4): sprite-centric flat list with substring filter and favorites toggle. Replaces Blender's native outliner only for the Proscenio hierarchy; the native outliner remains untouched.

#### Validation

- **Validate** operator: schema validation against `proscenio.schema.json` plus cross-references (sprite vs armature, atlas, required fields). Errors block export.
- Inline status badges per subpanel: cheap O(1) checks per redraw, surfaced as icons next to subpanel headers.
- Per-subpanel issue list: clickable rows that select the offending object.

#### Export

- **Export Proscenio** operator: writes `.proscenio` JSON + atlas next to the source `.blend`.
- Sticky export path: re-export silently reuses the last path on subsequent saves.
- Per-project `pixels_per_unit` knob.
- In-panel `?` help popup per subpanel: same content as the dev skill docs, surfaced where the user works.

### Godot side

- `EditorImportPlugin` consuming `.proscenio` files at editor time.
- Builders: `Skeleton2D` + `Bone2D` from bones; `Polygon2D` / `Sprite2D` from sprites; `AnimationPlayer` from actions.
- Coordinate conversion: Blender XZ → Godot XY (Y-flip, CCW→CW), rest+delta absolute values on tracks.
- Atlas mapping: pixel-space (`Polygon2D.uv` = `uv * atlas.get_size()`).
- Animation interpolation: `INTERPOLATION_CUBIC_ANGLE` on rotation, `INTERPOLATION_CUBIC` on position/scale, `INTERPOLATION_NEAREST` on `sprite_frame` and `slot_attachment` tracks.
- Skinning: `Polygon2D.skeleton` wiring + per-vertex weights for real mesh deformation.
- Slot expansion: `Node2D` parent + `visible`-toggled children; `slot_attachment` track expanded into per-attachment visibility tracks.
- Wrapper-scene pattern: every reimport clobbers the `.scn`; user-authored `.tscn` instances it and survives intact.

### Schema / contract

- `proscenio.schema.json` v1: `Bone`, `Sprite`, `Animation`, `bone_transform` track, `sprite_frame` track, `slot_attachment` track, `weights[]`, `slots[]`.
- `psd_manifest.schema.json` v1: `kind` discriminator, `pixels_per_unit`, `z_order`, `frames[]`.
- Validated at writer output, importer input, and CI fixtures.

## Out of scope

Hard non-goals. Paradigm-locked decisions that won't reopen without a fundamental shift.

| Non-goal | Reason | Escape hatch |
| --- | --- | --- |
| Multi-engine runtime (Spine, DragonBones model) | Godot-only by design. | None. Multi-target export needs a runtime layer Proscenio explicitly avoids. |
| Custom runtime / GDExtension / C# component | Generated `.scn` must run on plain Godot 4 with no plugin installed. | Triggers logged in [`specs/backlog.md`](specs/backlog.md) "Architecture revisits": deep Firebound integration, perf ceiling, live link. |
| Live2D parameter-driven deformer rigs | Skeleton-based cutout, not parameter-blended 2.5D mesh deformation. | None. Different art form. |
| Grease Pencil rigging | Mesh cutout target only. GP has its own native Blender rigging. | None. |
| After-Effects motion design (DUIK, RubberHose) | Game runtime targets, not broadcast/motion-graphics. | None. |
| Proprietary DCC dependency | Authoring stays in Blender, an open-source tool the artist already knows. | None. Open-source DCC is a project value. |

## Deferred

In scope conceptually, not yet shipped. Includes mesh-from-contour, skin coordination, Bezier preservation, animation events, bone physics, multi-atlas, Krita/GIMP exporters, live link, mid-edit re-rig, weight transfer, mask/blend modes, mesh subdivision presets, auto-rig templates. Full list with rationale in [`docs/DEFERRED.md`](docs/DEFERRED.md). Finer-grained backlog items (single operators, CI matrix, repo polish) live in [`specs/backlog.md`](specs/backlog.md).

## Comparison

Full feature matrix vs Spine, COA Tools 2, Live2D, DragonBones, Godot native, Unity 2D Animation, plus per-tool positioning summary and the cross-tool QoL paradigms Proscenio adopts / partially adopts / rejects: see [`docs/COMPARISON.md`](docs/COMPARISON.md).

In one sentence: Proscenio trades Spine's multi-runtime, polished preview, and runtime constraints for being free, open, plugin-uninstall safe, and emitting native Godot scenes; trades CT2's authoring acceleration (automesh, multi-DCC) for schema rigor and a working Godot importer; trades Live2D's illustration-first paradigm for skeleton-based cutout fit for game runtime.

## Documentation

- [`AGENTS.md`](AGENTS.md) - entry point for contributors and LLM agents.
- [`.ai/skills/`](.ai/skills/README.md) - task-specific skill bundles.
- [`STATUS.md`](STATUS.md) - live state: current branch, recent waves, fixtures, open work.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) - setup, PR rules, end-to-end usage walkthrough.
- [`docs/DECISIONS.md`](docs/DECISIONS.md) - locked architectural and per-SPEC decisions.
- [`docs/COMPARISON.md`](docs/COMPARISON.md) - feature matrix and positioning vs alternatives.
- [`docs/DEFERRED.md`](docs/DEFERRED.md) - SPEC-level deferred features and rationale.
- [`docs/GODOT-WORKFLOW.md`](docs/GODOT-WORKFLOW.md) - customizing imported characters Godot-side without losing work on reimport.
- [`specs/`](specs/) - per-feature design documents.
- [`specs/backlog.md`](specs/backlog.md) - finer-grained backlog (operators, CI, repo polish).
- [`schemas/`](schemas/) - `.proscenio` and PSD manifest schemas.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
