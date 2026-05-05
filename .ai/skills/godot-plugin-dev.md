---
name: godot-plugin-dev
description: Develop, lint, and test the Godot editor plugin
---

# Godot plugin development

## Target versions

- **Minimum:** Godot 4.3 — `AnimationLibrary` is stable and `EditorImportPlugin` is mature.
- **Tested:** Godot 4.4, latest 4.x.

## Project layout

```text
godot-plugin/
├── project.godot           # dev project — kept inline for easy testing
├── addons/proscenio/
│   ├── plugin.cfg
│   ├── plugin.gd           # EditorPlugin entry — registers importer
│   ├── importer.gd         # EditorImportPlugin
│   ├── reimporter.gd       # diff/merge logic for non-destructive reimport
│   └── builders/
│       ├── skeleton_builder.gd
│       ├── polygon_builder.gd        # type: "polygon" sprites — Polygon2D
│       ├── sprite_frame_builder.gd   # type: "sprite_frame" sprites — Sprite2D
│       └── animation_builder.gd
└── tests/                  # GUT
```

## How import works

1. User drops a `.proscenio` file in the project.
2. Godot calls `importer.gd._import()`.
3. Importer parses the JSON and validates `format_version`.
4. Builders construct nodes in memory:
   - `Node2D` (root)
     - `Skeleton2D` → `Bone2D` (recursive) → sprites attached to bones
       - `Polygon2D` for sprites of `type: "polygon"` (default, cutout)
       - `Sprite2D` for sprites of `type: "sprite_frame"` (spritesheet)
     - `AnimationPlayer` with one default `AnimationLibrary`
5. Wrap root in `PackedScene`, save via `ResourceSaver` to `.godot/imported/<hash>.scn`.

## Choosing the rendering path

The `.proscenio` schema uses a `type` discriminator per sprite (see [SPEC 002](../../specs/002-spritesheet-sprite2d/STUDY.md) and [`format-spec.md`](format-spec.md#sprite-kinds-type-discriminator)). Pick by use case:

| Use case | Pick | Why |
| --- | --- | --- |
| Cutout-style character with deformable mesh (Spine / COA Tools target audience) | `polygon` | `Polygon2D` carries vertices + UV; with a `weights` array, the importer wires `Polygon2D.skeleton` + `add_bone()` and the mesh deforms with the rig (SPEC 003 — shipped) |
| Frame-by-frame pixel art animation | `sprite_frame` | `Sprite2D` with `hframes`/`vframes`/`frame` is the native idiom |
| Particles, hit flashes, sparkles, simple effects | `sprite_frame` | cheapest, no per-vertex geometry |
| Simple sprite that only translates/rotates with no deformation | either | `sprite_frame` is lighter when no skinning is on the horizon |
| Static atlas region (one frame, no animation) | `polygon` quad | UV is explicit; no need to invent a 1×1 frame grid |

Mixing both kinds inside the same character is supported and idiomatic — a cutout body with a spritesheet face is a common pattern.

## The "no GDExtension" rule

This plugin runs **only** at editor import time. Generated scenes use built-in nodes only. To verify: open a generated `.tscn` in another Godot project that does not have Proscenio installed — it must work.

## Reimport behavior

Reimport **always overwrites** the previous output. The importer rebuilds the
scene from scratch from the current `.proscenio`. This is the resolution of
[SPEC 001](../../specs/001-reimport-merge/STUDY.md) — Option A. Marker-based
merge (Option B) is deferred unless concrete demand emerges.

The importer logs a single `print_verbose` line when overwriting an existing
output, so the action is auditable when the user enables verbose mode.

## Customizing an imported scene

To attach scripts, extra nodes, or game logic without losing them on every
reimport, **wrap the imported scene in your own `.tscn`**:

```text
res://characters/dummy/
├── dummy.proscenio                    # source — DCC-authored
├── Dummy.tscn                         # wrapper — yours, never touched
└── Dummy.gd                           # script attached to the wrapper root
```

`Dummy.tscn` instances `dummy.proscenio` (Godot transparently uses the
generated `.scn`). Scripts attach to the wrapper root, not to the imported
scene's children. Extra nodes (collisions, particles, AI controllers)
parent to the wrapper.

See [`examples/dummy/Dummy.tscn`](../../examples/dummy/Dummy.tscn) and
[`examples/dummy/Dummy.gd`](../../examples/dummy/Dummy.gd) for the worked
documentation-by-example.

### Bone rename caveat

A Blender bone rename invalidates wrapper-scene `NodePath`s referencing the
old name. `$DummyCharacter/Skeleton2D/torso` breaks if `torso` becomes
`upper_body`. Plan renames as cross-DCC operations: rename in Blender, then
fix every wrapper that referenced the old name.

### Adding Godot-authored animations

The imported scene's `AnimationPlayer` holds the default (`""`)
`AnimationLibrary` populated from the `.proscenio`. To add animations
authored in Godot:

1. Give the wrapper its **own** `AnimationPlayer`, separate from the imported one.
2. Create a second `AnimationLibrary`, e.g. `"user"`.
3. Both libraries can play under the wrapper's logic — call
   `AnimationPlayer.play("user/my_attack")` for the user-authored library
   or `imported_player.play("idle")` for the DCC-authored one.

This keeps the boundary clean: DCC-authored animations are owned by the
exporter, user-authored ones never collide with reimport.

## Coding rules

- GDScript 2.0 syntax. Use static typing wherever possible (`var x: int = 0`).
- One class per file. Filename matches the class concept.
- Format: `gdformat addons/proscenio/`. Lint: `gdlint addons/proscenio/`.
- No `@tool` scripts in user-facing scenes — only inside the plugin.

## Testing

GUT-based tests in `godot-plugin/tests/`. Run via Godot CLI:

```sh
godot --headless --path godot-plugin -s addons/gut/gut_cmdln.gd
```

Fixtures: small `.proscenio` files in `tests/fixtures/`.
