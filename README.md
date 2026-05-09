# Proscenio

Blender → Godot 4 pipeline for 2D cutout animation. Native `Skeleton2D` + `Bone2D` + `Polygon2D` output. No runtime, no GDExtension, no custom engine build.

> **Status:** pre-alpha. Format unstable. Not for production use.

## Why

The 2D cutout pipeline for Godot has gaps:

- **Spine2D** — paid, opaque format, GDExtension dependency, third-party-of-third-party support story.
- **COA Tools / coa_tools2** — Blender side alive (Blender 4.x and 5.x), Godot side broken or abandoned.
- **Godot 2D Bridge** — proves `Polygon2D` + `Skeleton2D` export works, but no animations and stuck on Godot 4.0.

Proscenio fills the gap: rig and animate in Blender, import into Godot 4 as native scenes (`.tscn`). After import, Godot does not know the asset came from Blender.

## Components

| Folder | Purpose |
| --- | --- |
| [`photoshop-exporter/`](photoshop-exporter/) | JSX script: PSD layers → sprites + position JSON |
| [`blender-addon/`](blender-addon/) | Blender 4.2+ addon: sprite import, rigging, animation, `.proscenio` export |
| [`godot-plugin/`](godot-plugin/) | Godot 4.3+ `EditorImportPlugin`: `.proscenio` → `.tscn` |
| [`schemas/`](schemas/) | `proscenio.schema.json` — versioned format spec, single source of truth |
| [`examples/`](examples/) | End-to-end sample assets (binary files via Git LFS) |

## Quickstart

The MVP is in progress. Full quickstart will land with the first end-to-end sample. The iteration loop, once both sides ship:

### 1. Bring the art in

Pick whichever entry point matches your asset:

- **Photoshop authored** — open the source `.psd` and run the JSX exporter (see [`photoshop-exporter/`](photoshop-exporter/)). It writes a manifest JSON + per-layer PNGs. In Blender, click **Import Photoshop Manifest** (Active Sprite subpanel) and point at the manifest. Each layer lands as a quad sprite with the right pivot, atlas region, and naming convention pre-populated.
- **Hand authored in Blender** — model your meshes directly. The panel still applies; just skip the manifest import.

### 2. Rig and weight

In the Blender sidebar (`N → Proscenio`):

- Need a quick skeleton for a doodle? **Skeleton → Quick Armature** (5.1.d.3) — click-drag in the viewport to draw bones (Shift to chain). The result is a normal armature; rename and refine in Edit Mode as usual.
- Parent your meshes to the armature (`Ctrl+P → Armature Deform`). The writer reads vertex-group names and matches them to bone names — see [SPEC 003](specs/003-skinning-weights/STUDY.md) for the matching rules.
- Use **Skeleton → Bake Current Pose** + **Toggle IK** + **Save Pose to Library** as authoring shortcuts. None of them affect the export — they only help you iterate.

### 3. Set per-sprite knobs

- **Active Sprite** — pick `Polygon` for cutout meshes or `Sprite Frame` for spritesheets. Set `hframes / vframes / frame` for sprite_frame; the in-panel preview slicer (5.1.d.5) lets you preview the cell choice in the 3D viewport without exporting.
- **Texture region** — auto computes from UV bounds; manual lets you slice an atlas. Click **Snap to UV bounds** to populate from the current UV.
- Need to swap textures based on bone rotation? **Drive from Bone** (5.1.d.1) wires a Blender driver between a pose bone and a sprite property in one click. For HARD swaps (forearm front/back, sword/staff), use the slot system below instead.

### 4. Slot system (SPEC 004)

For attachments that toggle between N variants — sword/staff/empty hand, brow up/down, expression swap:

1. Select the meshes you want to wrap. **Skeleton → Create Slot** anchors a slot Empty under the active bone and parents the selected meshes as attachments.
2. In **Active Slot**, pick which attachment is the default at scene load (SOLO icon).
3. Animate `proscenio_slot_index` on the slot to flip attachments per keyframe — Godot expands this into per-attachment visibility tracks at import time. See [`examples/slot_cycle/`](examples/slot_cycle/) for the minimal fixture.

### 5. Find things in big rigs

Big rigs (the doll fixture has 64 bones + 22 sprite meshes) drown Blender's native outliner. Use the **Outliner** subpanel (5.1.d.4): substring filter, favorites toggle, sprite-centric flat list. Click a row to make that object active.

### 6. Validate, export, and wrap

- **Export → Validate** — checks every sprite against the armature, the atlas, and required fields. Errors block export.
- **Export → Export Proscenio** writes a `.proscenio` JSON + the atlas next to it. **Re-export** silently re-uses the sticky path on subsequent saves.
- Drop the `.proscenio` into your Godot project — the `EditorImportPlugin` regenerates a `.scn` automatically.
- **Wrap the imported scene** — instance the generated `.scn` in your own `.tscn` and attach scripts there. Scripts and extra nodes on the wrapper survive every re-export from Blender; the imported scene itself is regenerated each time. See [`examples/doll/`](examples/doll/) for the comprehensive showcase, plus [`examples/blink_eyes/`](examples/blink_eyes/) (sprite_frame isolation test) and [`examples/shared_atlas/`](examples/shared_atlas/) (sliced atlas isolation test) for feature-focused fixtures.

### 7. Iterate

Re-export from Blender whenever the rig or animation changes. Reimport in Godot is automatic.

For the full panel walkthrough, the in-panel `?` button next to every subpanel header opens a topic-specific help popup. The same content lives in [`.ai/skills/blender-addon-dev.md`](.ai/skills/blender-addon-dev.md) (Blender side) and [`.ai/skills/godot-plugin-dev.md`](.ai/skills/godot-plugin-dev.md) (Godot side).

## Documentation

- **Contributors and LLM agents:** start at [AGENTS.md](AGENTS.md) → [`.ai/skills/`](.ai/skills/)
- **Current plan:** [`specs/000-initial-plan/STUDY.md`](specs/000-initial-plan/STUDY.md) and [`specs/000-initial-plan/TODO.md`](specs/000-initial-plan/TODO.md)

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
