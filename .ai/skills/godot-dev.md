---
name: godot-dev
description: Develop, lint, and test the Godot editor plugin
---

# Godot plugin development

## Target versions

- **Minimum:** Godot 4.3 - `AnimationLibrary` is stable and `EditorImportPlugin` is mature.
- **Tested:** Godot 4.4+, latest 4.x.

## Project layout

```text
apps/godot/
├── project.godot          dev project - kept inline for easy testing
├── addons/proscenio/
│   ├── plugin.cfg
│   ├── plugin.gd          EditorPlugin entry - registers importer
│   ├── importer.gd        EditorImportPlugin
│   ├── reimporter.gd      reimport orchestration
│   └── builders/          one file per concern
│       ├── skeleton_builder.gd
│       ├── polygon_builder.gd
│       ├── sprite_frame_builder.gd
│       ├── slot_builder.gd
│       └── animation_builder.gd
└── tests/                 GUT
```

## How import works

1. User drops a `.proscenio` file in the project.
2. Godot calls the importer.
3. Importer parses the JSON and validates `format_version` against `SUPPORTED_FORMAT_VERSION`.
4. Builders construct nodes in memory:
   - `Node2D` root.
   - `Skeleton2D` with the `Bone2D` hierarchy.
   - `Node2D` slot anchors under their bone, with attachments parented under them.
   - `Polygon2D` for sprites of `type: "polygon"`.
   - `Sprite2D` for sprites of `type: "sprite_frame"`.
   - `AnimationPlayer` with a default `AnimationLibrary`.
5. The root is packed via `PackedScene` and saved with `ResourceSaver`.

## Choosing the rendering path

The `.proscenio` schema uses a `type` discriminator per sprite. Pick by use case:

| Use case | Pick | Why |
| --- | --- | --- |
| Cutout-style character with deformable mesh | `polygon` | `Polygon2D` carries vertices + UV; with a `weights` array the importer wires `Polygon2D.skeleton` and the mesh deforms with the rig |
| Frame-by-frame pixel art animation | `sprite_frame` | `Sprite2D` with `hframes` / `vframes` / `frame` is the native idiom |
| Particles, hit flashes, sparkles | `sprite_frame` | cheapest; no per-vertex geometry |
| Sprite that only translates / rotates, no deformation | either | `sprite_frame` is lighter when no skinning is planned |
| Static atlas region | `polygon` quad | explicit UV; no fake 1x1 frame grid |

Mixing both kinds inside the same character is supported - a cutout body with a spritesheet face is idiomatic.

## The "no GDExtension" rule

The plugin runs **only** at editor import time. Generated scenes use built-in nodes only. Operational test: open a generated `.tscn` in another Godot project that does not have Proscenio installed - it must work.

## Reimport behavior

Reimport always **overwrites** the previous output. The importer rebuilds the scene from scratch from the current `.proscenio`. The action is logged via `print_verbose` so it stays auditable.

## Customizing an imported scene

To attach scripts, extra nodes, or game logic without losing them on every reimport, **wrap the imported scene in your own `.tscn`**:

- Your wrapper instances the imported scene as a child.
- Scripts attach to the wrapper root, not to the imported scene's children.
- Extra nodes (collisions, particles, AI controllers) parent to the wrapper.

The imported scene's `AnimationPlayer` holds the DCC-authored library under the default (`""`) key. For Godot-authored animations, give the wrapper its **own** `AnimationPlayer` and a separate `AnimationLibrary` (e.g. `"user"`) - the imported library stays untouched on reimport.

### Bone rename caveat

Renaming a Blender bone invalidates wrapper `NodePath`s referencing the old name. Treat renames as cross-DCC operations: rename in Blender, then fix every wrapper that referenced the old name.

## Slots

A slot is a sprite-swap group: one named anchor with N alternate attachments, exactly one visible at a time. Use it for hard texture swaps where `sprite_frame` indices or a driver are the wrong primitive (forearm front/back, equipment swap, expression swap).

**Schema sketch** (see `format-spec.md` for the full shape):

```json
{
  "slots": [
    {
      "name": "brow.L.swap",
      "bone": "brow.L",
      "default": "brow.L",
      "attachments": ["brow.L", "brow.L.up"]
    }
  ]
}
```

`bone` is optional - omitted when the slot anchor sits directly under `Skeleton2D`.

**Generated scene shape**:

```text
Skeleton2D
└── Bone2D "brow.L"
    └── Node2D "brow.L.swap"        ← slot anchor (Node2D)
        ├── Polygon2D "brow.L"      visible=true   (default)
        └── Polygon2D "brow.L.up"   visible=false
```

**Animation expansion**: a `slot_attachment` track expands to N `:visible` tracks (one per attachment), with `INTERPOLATION_NEAREST` so swaps are hard cuts. At each key time, the named attachment gets `visible=true`, siblings get `visible=false`.

**Name sanitization**: Godot's `Node.name` setter replaces `.` / `/` / `:` / `@` with `_`. The slot builder applies the same transform on every map key + `find_child` lookup. Wrapper-side scripts addressing a slot via `$NodePath` must use the underscored form.

## Coding rules

- GDScript 2.0 with static typing everywhere (`var x: int = 0`, typed parameters and returns).
- One class per file. Filename matches the concept.
- Format: `gdformat addons/proscenio/`. Lint: `gdlint addons/proscenio/`.
- No `@tool` scripts in user-facing scenes - only inside the plugin.

## Testing

GUT-based tests in `apps/godot/tests/`. Run via Godot CLI:

```sh
godot --headless --path apps/godot -s addons/gut/gut_cmdln.gd
```

Fixtures: small `.proscenio` files in `tests/fixtures/`.
