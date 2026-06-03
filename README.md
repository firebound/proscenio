# Proscenio

**A Photoshop -> Blender -> Godot pipeline for 2D cutout animation.**

> [!WARNING]
> Proof of concept / work in progress. The format is still unstable - not for production use.

## What it is

Proscenio is an open-source pipeline for 2D cutout animation, built for artists. You paint in Photoshop, rig and animate in Blender, and ship to Godot - every step on open, free tooling.

The pipeline runs one direction:

1. Photoshop slices your layered artwork into one PNG per layer.
2. Blender imports that, where you build the mesh, rig the skeleton, paint weights, and animate with Blender's toolset (dopesheet, NLA, drivers).
3. Godot reads the single versioned file Blender exports and rebuilds the character as a native scene - an ordinary `Skeleton2D` + `Bone2D` + `Polygon2D` + `AnimationPlayer` tree that runs with nothing else installed.

```text
Photoshop -> manifest + PNGs -> Blender -> .proscenio + atlas / spritesheets -> Godot (.scn)
```

> [!NOTE]
> This project has used AI-assisted heavily through the actual Proof of Concept development, all code and documentation is human reviewed but may contain AI artifacts as I'm a single developer and the project is in early stages.

## Who it's for

Artists and game devs who want a practical 2D cutout workflow on Godot 4, with each tool playing to its strength:

- **Photoshop 2024+** for rasterized art - paint, layer, organize.
- **Blender 4.2+** for everything animation - rig, weight, keyframe.
- **Godot 4.6+** as the final engine - native scenes, no proprietary runtime.

It is an open, no lock-in, free alternative to Spine and other 2D animation workflows - no custom runtime and no standalone editor, just open tools tied together by one versioned JSON format.

If you want a practical, artist-friendly pipeline that leverages open tools and outputs native Godot scenes, Proscenio is for you.

## The promises

| Pillar                        | What it means                                                                                                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Non-destructive**           | `.psd` and `.blend` stay read-only sources; a Godot reimport overwrites only the generated `.scn`. Your wrapper scenes, scripts, and extras stay intact.      |
| **Engine-native output**      | The `.scn` uses Godot core nodes only. The shipped game runs with Proscenio uninstalled.                                                                      |
| **Each tool to its strength** | An open-source chain (Blender, Godot, schemas) with no Spine-style editor license. Shortcuts sit on top of Blender's native operators - never replacing them. |
| **A predictable contract**    | One versioned, typed JSON schema. What leaves Blender is what arrives in Godot, validated from the IDE through CI. Format bumps require explicit migrators.   |

## Components

| Part                                   | Tech                                | Role                                                                                                         |
| -------------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| [`apps/photoshop/`](apps/photoshop/)   | UXP plugin, TypeScript + React      | PSD -> manifest JSON + per-layer PNGs.                                                                       |
| [`apps/blender/`](apps/blender/)       | Python addon (mypy strict)          | Manifest import, the authoring panel (mesh, rig, weights, slots), validation, and the `.proscenio` writer.   |
| [`apps/godot/`](apps/godot/)           | GDScript (typed)                    | An `EditorImportPlugin` that reads `.proscenio` and regenerates the `.scn` on every reimport.                |
| [`packages/models/`](packages/models/) | Pydantic v2 + generated JSON Schema | The source of truth. The JSON Schema, TypeScript, and GDScript bindings are all generated from these models. |

## What you can do with it

The full, code-verified feature list lives in [`docs/FEATURES.md`](docs/FEATURES.md), and the systems behind them in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). In short:

- **Photoshop** - tag layers from their name to drive the export; get one PNG per layer plus a validated manifest.
- **Blender** - build a deformable mesh from the sprite alpha (automesh), draw a skeleton (Quick Armature), bind and paint weights, swap sprites through slots, pack an atlas, and animate - all on top of native Blender tools.
- **Godot** - a one-step import that rebuilds the character as a native scene on every reimport.

## Out of scope

Paradigm-locked non-goals that will not reopen without a fundamental shift:

| Non-goal                                         | Why                                                                               |
| ------------------------------------------------ | --------------------------------------------------------------------------------- |
| Multi-engine runtime (Spine / DragonBones model) | Godot-only by design; multi-target export needs a runtime layer Proscenio avoids. |
| Custom runtime / GDExtension / C#                | The generated `.scn` must run on plain Godot 4 with nothing installed.            |
| Live2D parameter-driven deformers                | Skeleton-based cutout, not parameter-blended mesh deformation.                    |
| Proprietary DCC dependency                       | Authoring stays in Blender, an open tool artists already know.                    |

## More

You can find the contribution guidelines, the end-to-end walkthrough, and PR rules in [`CONTRIBUTING.md`](CONTRIBUTING.md), and check [`AGENTS.md`](AGENTS.md) or [`.ai/`](.ai/skills/README.md) for guidance on the project structure and best practices.

For the full feature list, see:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - the systems and how the data flows.
- [`docs/COMPARISON.md`](docs/COMPARISON.md) - feature matrix vs Spine, COA Tools 2, Live2D, and others.
- [`docs/DEFERRED.md`](docs/DEFERRED.md) - features planned but not shipped yet.
- [`docs/FEATURES.md`](docs/FEATURES.md) - the full feature list, by plugin.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
