# Proscenio

> [!WARNING]
> Proof of concept / work in progress. The format is still unstable - not for production use.

**A Photoshop -> Blender -> Godot 4 pipeline for 2D cutout animation.** Rig and animate in Blender, then ship to Godot as native scenes with no runtime of their own.

## What it is

Proscenio is an open-source pipeline that lets artists rig and animate 2D cutout characters in Blender, then bring them into Godot 4 as plain scenes. The Godot output is an ordinary `Skeleton2D` + `Bone2D` + `Polygon2D` + `AnimationPlayer` tree - no GDExtension, no custom runtime, and nothing to install for the scene to play.

Each tool does the one thing it is best at, and a single versioned JSON file (`.proscenio`) is the only contract between Blender and Godot. Photoshop feeds Blender through a parallel manifest. Blender is the authoring tool on purpose: open source like the rest of the stack, free of license cost, and already equipped with a mature animation toolset (dopesheet, NLA, drivers, weight paint).

```text
Photoshop ──> manifest + PNGs ──> Blender ──> .proscenio + atlas ──> Godot (.scn)
 raster art        rig · weight · keyframe · animate          native scene, no runtime
```

## Who it's for

Artists and game devs who want a practical 2D cutout workflow on Godot 4, with each tool playing to its strength:

- **Photoshop** for raster art - paint, layer, organize.
- **Blender** for everything animation - rig, weight, keyframe, NLA, drivers.
- **Godot** as the final engine - native scenes, no proprietary runtime.

It is an open, free alternative to Spine and to the abandoned Godot importers for COA Tools, and the scenes it emits survive uninstalling the plugin.

## The promises

| Pillar | What it means |
| --- | --- |
| **Non-destructive** | `.psd` and `.blend` stay read-only sources; a Godot reimport overwrites only the generated `.scn`. Your wrapper scenes, scripts, and extras stay intact. |
| **Engine-native output** | The `.scn` uses Godot core nodes only. The shipped game runs with Proscenio uninstalled. |
| **Each tool to its strength** | An open-source chain (Blender, Godot, schemas) with no Spine-style editor license. Shortcuts sit on top of Blender's native operators - never replacing them. |
| **A predictable contract** | One versioned, typed JSON schema. What leaves Blender is what arrives in Godot, validated from the IDE through CI. Format bumps require explicit migrators. |

## Components

| Part | Tech | Role |
| --- | --- | --- |
| [`apps/photoshop/`](apps/photoshop/) | UXP plugin, TypeScript + React | PSD -> manifest JSON + per-layer PNGs. Optional mirror back to PSD. |
| [`apps/blender/`](apps/blender/) | Python addon (mypy strict) | Manifest import, the authoring panel (mesh, rig, weights, slots), validation, and the `.proscenio` writer. |
| [`apps/godot/`](apps/godot/) | GDScript (typed) | An `EditorImportPlugin` that reads `.proscenio` and regenerates the `.scn` on every reimport. |
| [`packages/models/`](packages/models/) | Pydantic v2 + generated JSON Schema | The source of truth. The JSON Schema, TypeScript, and GDScript bindings are all generated from these models. |

## What you can do with it

The full, code-verified feature list lives in [`FEATURES.md`](FEATURES.md), and the systems behind them in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). In short:

- **Photoshop** - tag layers from their name to drive the export; get one PNG per layer plus a validated manifest.
- **Blender** - build a deformable mesh from the sprite alpha (automesh), draw a skeleton (Quick Armature), bind and paint weights, swap sprites through slots, pack an atlas, and animate - all on top of native Blender tools.
- **Godot** - a one-step import that rebuilds the character as a native scene on every reimport.

## Out of scope

Paradigm-locked non-goals that will not reopen without a fundamental shift:

| Non-goal | Why |
| --- | --- |
| Multi-engine runtime (Spine / DragonBones model) | Godot-only by design; multi-target export needs a runtime layer Proscenio avoids. |
| Custom runtime / GDExtension / C# | The generated `.scn` must run on plain Godot 4 with nothing installed. |
| Live2D parameter-driven deformers | Skeleton-based cutout, not parameter-blended mesh deformation. |
| Proprietary DCC dependency | Authoring stays in Blender, an open tool artists already know. |

The conditions that could reopen the runtime question are logged under "Architecture revisits" in [`specs/backlog.md`](specs/backlog.md).

## More

- [`FEATURES.md`](FEATURES.md) - the full feature list, by plugin.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - the systems and how the data flows.
- [`docs/COMPARISON.md`](docs/COMPARISON.md) - feature matrix vs Spine, COA Tools 2, Live2D, and others.
- [`docs/DEFERRED.md`](docs/DEFERRED.md) - features planned but not shipped yet.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) - setup, the end-to-end walkthrough, and PR rules.
- [`AGENTS.md`](AGENTS.md) and [`.ai/`](.ai/skills/README.md) - guidance for contributors and AI agents.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
