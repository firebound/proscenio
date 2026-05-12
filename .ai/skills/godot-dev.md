---
name: godot-dev
description: Develop, lint, and test the Godot editor plugin
---

# Godot plugin development

## Target versions

- **Minimum:** Godot 4.3 - `AnimationLibrary` is stable and `EditorImportPlugin` is mature.
- **Tested:** Godot 4.4, latest 4.x.

## Project layout

```text
apps/godot/
├── project.godot           # dev project - kept inline for easy testing
├── addons/proscenio/
│   ├── plugin.cfg
│   ├── plugin.gd           # EditorPlugin entry - registers importer
│   ├── importer.gd         # EditorImportPlugin
│   ├── reimporter.gd       # reimport orchestration (Option A full overwrite)
│   └── builders/
│       ├── skeleton_builder.gd
│       ├── polygon_builder.gd        # type: "polygon" sprites - Polygon2D
│       ├── sprite_frame_builder.gd   # type: "sprite_frame" sprites - Sprite2D
│       ├── slot_builder.gd           # SPEC 004 - Node2D anchors + visible toggling
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
| Cutout-style character with deformable mesh (Spine / COA Tools target audience) | `polygon` | `Polygon2D` carries vertices + UV; with a `weights` array, the importer wires `Polygon2D.skeleton` + `add_bone()` and the mesh deforms with the rig (SPEC 003 - shipped) |
| Frame-by-frame pixel art animation | `sprite_frame` | `Sprite2D` with `hframes`/`vframes`/`frame` is the native idiom |
| Particles, hit flashes, sparkles, simple effects | `sprite_frame` | cheapest, no per-vertex geometry |
| Simple sprite that only translates/rotates with no deformation | either | `sprite_frame` is lighter when no skinning is on the horizon |
| Static atlas region (one frame, no animation) | `polygon` quad | UV is explicit; no need to invent a 1×1 frame grid |

Mixing both kinds inside the same character is supported and idiomatic - a cutout body with a spritesheet face is a common pattern.

## The "no GDExtension" rule

This plugin runs **only** at editor import time. Generated scenes use built-in nodes only. To verify: open a generated `.tscn` in another Godot project that does not have Proscenio installed - it must work.

## Reimport behavior

Reimport **always overwrites** the previous output. The importer rebuilds the
scene from scratch from the current `.proscenio`. This is the resolution of
[SPEC 001](../../specs/001-reimport-merge/STUDY.md) - Option A. Marker-based
merge (Option B) is deferred unless concrete demand emerges.

The importer logs a single `print_verbose` line when overwriting an existing
output, so the action is auditable when the user enables verbose mode.

## Customizing an imported scene

To attach scripts, extra nodes, or game logic without losing them on every
reimport, **wrap the imported scene in your own `.tscn`**:

```text
res://characters/dummy/
├── dummy.proscenio                    # source - DCC-authored
├── Dummy.tscn                         # wrapper - yours, never touched
└── Dummy.gd                           # script attached to the wrapper root
```

`Dummy.tscn` instances `dummy.proscenio` (Godot transparently uses the
generated `.scn`). Scripts attach to the wrapper root, not to the imported
scene's children. Extra nodes (collisions, particles, AI controllers)
parent to the wrapper.

See [`examples/authored/doll/godot/Doll.tscn`](../../examples/authored/doll/godot/Doll.tscn) and
[`examples/authored/doll/godot/Doll.gd`](../../examples/authored/doll/godot/Doll.gd) for the worked
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
3. Both libraries can play under the wrapper's logic - call
   `AnimationPlayer.play("user/my_attack")` for the user-authored library
   or `imported_player.play("idle")` for the DCC-authored one.

This keeps the boundary clean: DCC-authored animations are owned by the
exporter, user-authored ones never collide with reimport.

## Slots (SPEC 004)

A slot is a sprite-swap group: one named anchor with N alternate attachments, one of which is visible at a time. Use it for hard texture swaps where a `sprite_frame` index or a driver shortcut is the wrong primitive (forearm front/back rotation, equipment swap, expression swap).

**Schema shape**:

`bone` is **optional** - the writer emits it only when the slot Empty is bone-parented (`parent_type == "BONE"`); object-parented slot Empties (like the doll fixture's brow swaps, which use `parent_type == "OBJECT"` to avoid the bone Y-axis rotating its attachments) omit `bone` and the importer anchors the slot directly under `Skeleton2D`. The example below shows the bone-parented variant; see `examples/authored/doll/doll.expected.proscenio` for the object-parented golden.

```json
{
  "slots": [
    {
      "name": "brow.L.swap",
      "bone": "brow.L",
      "default": "brow.L",
      "attachments": ["brow.L", "brow.L.up"]
    }
  ],
  "animations": [{
    "name": "brow_raise",
    "tracks": [{
      "type": "slot_attachment",
      "target": "brow.L.swap",
      "keys": [
        { "time": 0.0, "interp": "constant", "attachment": "brow.L" },
        { "time": 0.5, "interp": "constant", "attachment": "brow.L.up" },
        { "time": 1.0, "interp": "constant", "attachment": "brow.L" }
      ]
    }]
  }]
}
```

**Generated scene shape**:

```text
Skeleton2D
└── Bone2D "brow.L"
    └── Node2D "brow.L.swap"        ← slot anchor (one per slots[] entry)
        ├── Polygon2D "brow.L"      visible=true   (default)
        └── Polygon2D "brow.L.up"   visible=false

AnimationPlayer
└── Animation "brow_raise"
    ├── Track "Skeleton2D/.../brow.L.swap/brow.L:visible"     NEAREST
    └── Track "Skeleton2D/.../brow.L.swap/brow.L.up:visible"  NEAREST
```

**Builder dispatch** (`addons/proscenio/builders/slot_builder.gd`):

- Reads `slots[]` BEFORE the sprite builders run.
- Builds one `Node2D` per slot under the matching `Bone2D` (or `Skeleton2D` root when `bone` is empty).
- Returns a `{sanitized_attachment_name: SlotInfo}` map. Sprite builders consult the map and route attachments under the slot Node2D + set `visible = (name == default)`.

**Animation expansion** (`addons/proscenio/builders/animation_builder.gd`):

- `slot_attachment` track expands to N `:visible` tracks (one per attachment child of the slot Node2D).
- At each key time, the named attachment gets `visible=true`, siblings get `visible=false`.
- `INTERPOLATION_NEAREST` - attachment swaps are hard cuts (no in-between).

**Name sanitization caveat**:

Godot's `Node.name` setter strips `.` / `/` / `:` / `@` and replaces them with `_`. The Blender side typically authors names like `brow.L.swap` with dots intact. `SlotBuilder.sanitize` applies the same transform on every map key + `find_child` lookup, so writer + importer converge on the Godot-shaped name. Wrapper-side scripts addressing the slot via `$NodePath` must use the underscored form.

**Customizing slot behavior in the wrapper**:

Slots are pure-data Node2Ds - wrappers can drive them via:

```gdscript
var slot := $Skeleton2D/.../brow_L_swap  # note sanitized "_"
for child in slot.get_children():
    child.visible = (child.name == "brow_L_up")
```

User-authored animations on the wrapper's own AnimationPlayer can hook the same `:visible` track shape; the imported AnimationLibrary stays untouched on reimport.

**See also**: `examples/generated/slot_cycle/` (isolated minimal slot fixture), `examples/authored/doll/` brow swap (slot on a comprehensive rig).

## Coding rules

- GDScript 2.0 syntax. Use static typing wherever possible (`var x: int = 0`).
- One class per file. Filename matches the class concept.
- Format: `gdformat addons/proscenio/`. Lint: `gdlint addons/proscenio/`.
- No `@tool` scripts in user-facing scenes - only inside the plugin.

## Testing

GUT-based tests in `apps/godot/tests/`. Run via Godot CLI:

```sh
godot --headless --path apps/godot -s addons/gut/gut_cmdln.gd
```

Fixtures: small `.proscenio` files in `tests/fixtures/`.
