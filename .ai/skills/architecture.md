---
name: architecture
description: Repo layout, component boundaries, dependency direction, extension points
---

# Proscenio architecture

## Three components, two contracts

```text
Photoshop ──UXP plugin──▶ layer PNGs + manifest JSON (psd_manifest.schema.json v1)
                                  │
                                  ▼
                               Blender (addon: rig, mesh, animate)
                                  │
                                  ▼ exporter
                            .proscenio (JSON, proscenio.schema.json v1)
                                  │
                                  ▼ EditorImportPlugin
                               Godot .scn (Skeleton2D + Bone2D + Polygon2D + AnimationPlayer)
```

## Strict dependency direction

- **Photoshop exporter** (UXP plugin, TypeScript + React) knows nothing of Blender or Godot. Output conforms to `psd_manifest.schema.json` v1.
- **Blender addon** knows the Photoshop manifest format and the `.proscenio` output format. Knows nothing of Godot internals.
- **Godot plugin** knows only the `.proscenio` schema. Does not parse `.blend`. Does not depend on Python.
- **Two schemas, two contracts**:
  - [`schemas/psd_manifest.schema.json`](../../schemas/psd_manifest.schema.json) — Photoshop ↔ Blender bridge.
  - [`schemas/proscenio.schema.json`](../../schemas/proscenio.schema.json) — Blender ↔ Godot bridge.

## What goes where

| Concern | Component |
| --- | --- |
| Layer slicing, alpha trim, manifest JSON | photoshop-exporter (UXP plugin) |
| Manifest validation against `psd_manifest.schema.json` | photoshop-exporter + blender-addon (consumer) |
| Bone hierarchy, weights, keyframes | blender-addon |
| Mesh tessellation, UV, slot system, atlas packing | blender-addon |
| `.proscenio` file production | blender-addon (`exporters/godot/writer/` package) |
| `.scn` generation | godot-plugin |
| Reimport overwrite + wrapper-scene pattern | godot-plugin |

## Extension points

- New DCC input format (Krita, GIMP, Aseprite) → emit conforming `psd_manifest.schema.json` from that DCC; reuse the existing [`blender-addon/importers/photoshop/`](../../blender-addon/importers/) consumer (manifest is DCC-agnostic by design).
- New output target (Unity, Defold, raw Spine emitter) → new module under [`blender-addon/exporters/`](../../blender-addon/exporters/).
- New animation track type → bump `format_version` in `proscenio.schema.json`, update schema, update Blender writer, update Godot animation builder.

## Hard rules

- Generated `.tscn` must run in stock Godot **without** the Proscenio plugin installed. The plugin is import-time only.
- No GDExtension. No native libraries. No runtime dependencies in user games.
- Blender addon is GPL-3.0 (Blender constraint). Repo is GPL-3.0 throughout for simplicity.
- Format change requires `format_version` bump and a migration path.

## Why no GDExtension

Spine ships a GDExtension because their `.skel` is a binary format, interpreted by their proprietary code at runtime, frame by frame, while the game runs. Native code is required to do that with acceptable performance.

Proscenio does the conversion **once, at editor import time**. The output is a `.tscn` made of built-in nodes — `Skeleton2D`, `Bone2D`, `Polygon2D`, `Sprite2D`, `AnimationPlayer`, `AnimationLibrary` — all already C++ in Godot core. At runtime the game uses Godot's own animation system. There is nothing for our plugin to do.

| Dimension | Spine GDExtension | Proscenio EditorImportPlugin |
| --- | --- | --- |
| Runtime cost | non-zero, native call per frame | zero — built-in nodes |
| Per-platform compilation | yes | no |
| Update cadence vs Godot | breaks on engine API drift | only `Skeleton2D` API matters |
| End-user install | runtime + plugin | nothing — scene is portable |
| Maintenance | high | low |

The only case where GDExtension would be worth the cost is a custom node type with proprietary tools (e.g. `ProscenioCharacter`). That is explicitly out of scope. Pure GDScript stays.

The hard rule above ("must run in stock Godot without the Proscenio plugin installed") is the operational test for this design. If a generated `.tscn` ever depends on plugin code, the design has slipped — fix it before merging.

For deeper reasoning and the prior-art investigation, see [`specs/000-initial-plan/STUDY.md`](../../specs/000-initial-plan/STUDY.md).
