# Godot workflow

How to add scripts, effects, colliders, audio, and gameplay logic to a Proscenio character on the Godot side without losing work on the next reimport.

## The contract

When Blender re-exports a `.proscenio`, the Proscenio importer **fully overwrites** the generated `.scn`. Any direct edit to that `.scn` is lost. This is by design and underwrites the non-destructive iteration story via *physical separation* rather than merge logic.

Rule of thumb: never edit `<name>.scn` directly. Work only on your own `<Name>.tscn` wrapper.

## Project layout

```text
res://characters/doll/
├── doll.proscenio        source, Blender owns
├── doll.scn              generated, the Proscenio importer overwrites on every reimport
├── Doll.tscn             user owned, instances doll.scn
└── Doll.gd               script on the wrapper root
```

`Doll.tscn` instances `doll.scn`. Scripts, extras, effects, colliders, AI all live on the wrapper. Reimport touches only `doll.scn`; `Doll.tscn` and `Doll.gd` stay intact.

## Wrapper pattern vs Editable Children

Godot offers two ways to customize an instanced sub-scene. Side-by-side trade-offs:

| Concern | Wrapper pattern | Editable Children |
| --- | --- | --- |
| Survives bone rename in Blender | partial - wrapper NodePaths break, fixable with a grep + edit | no - override gets orphaned silently |
| Survives sprite added / removed in `.proscenio` | yes - wrapper is unaffected | no - override may apply to wrong node or vanish |
| Survives exporter shape evolution | yes - wrapper code paths still resolve | no - override paths point to a layer that no longer exists |
| Visibility / inspectability of customizations | high - everything is in `Doll.tscn` + `Doll.gd`, version-controlled side files | low - overrides hide inside the wrapper `.tscn` as a diff against the sub-scene |
| Property override conflict with regenerated default | resolved deterministically: wrapper applies in `_ready`, last-write-wins | undefined: order between sub-scene default and outer diff is opaque |
| Reload semantics | clean - reimport regenerates the `.scn`, wrapper does not flinch | reconcile-or-drop - Godot tries to re-apply overrides; on mismatch, drops silently |
| Plugin-uninstall safety | trivially preserved - wrapper is a normal `.tscn` | preserved at output but the production path becomes read-modify-write |
| Best at | 95% of game-dev customization on top of an imported character | last-resort tweak on a stable sub-scene that does not evolve |
| Worst at | per-bone scripts and per-sprite property overrides (mitigated by composition + `_ready` loops) | anything in a project that re-exports often or expects schema evolution |

Wrapper pattern is the documented default. Editable Children works in narrow, stable cases but does not survive the iteration loop the rest of the pipeline is optimized for.

## Recipes

### 1. AI / behavior / state machine on the character

Script lives on the root of `Doll.tscn` (`Doll.gd`). Operates from the outside via `@onready` references into the imported scene.

```gdscript
extends Node2D
@onready var skeleton: Skeleton2D = $doll/Skeleton2D
@onready var anim: AnimationPlayer = $doll/AnimationPlayer
# ... game logic, signals, state machine, input handling
```

Survives reimport completely. Reads internals via NodePath; only breaks if a referenced bone or sprite is renamed in Blender (and the failure is loud at runtime).

### 2. Particles or effects following a bone

Add the effect under the wrapper; slave its transform to a bone via `RemoteTransform2D`:

```text
Doll.tscn
├── doll (instance)
├── HandTrail (GPUParticles2D)
└── HandFollower (RemoteTransform2D)
    remote_path = ../doll/Skeleton2D/torso/arm/hand
```

The `RemoteTransform2D` copies the bone's transform every frame onto the effect. Wrapper-owned, reimport-safe.

### 3. Colliders / hitboxes anchored to a bone

Same pattern as effects. Add `Area2D` (or `CharacterBody2D` for solid hitboxes) under the wrapper, plus a `RemoteTransform2D` slaved to the relevant bone. Signal handling and layer / mask configuration live on `Doll.gd`.

### 4. Material / shader override on an imported sprite

Apply at runtime in `_ready`. Do not use Editable Children for this.

```gdscript
func _ready() -> void:
    var head_sprite := $doll/Skeleton2D/torso/head/head_sprite as Polygon2D
    head_sprite.material = preload("res://shaders/glow.tres")
    head_sprite.modulate = Color.RED
```

Reimport-safe because the override is applied by code, not stored as a structural diff.

### 5. Animation events (sound cues, gameplay hooks at specific frames)

The friction case. Today's workaround uses a **second `AnimationPlayer` on the wrapper** with mirror animations whose tracks call methods on `Doll.gd`. Synchronize with the imported `AnimationPlayer`:

```text
Doll.tscn
├── doll (instance)              imported AnimationPlayer plays the visuals
└── EventPlayer (AnimationPlayer) wrapper-owned, plays method tracks
```

```gdscript
func play_idle() -> void:
    $doll/AnimationPlayer.play("idle")
    $EventPlayer.play("idle_events")  # mirror: method tracks for sound cues
```

The mirror has the same length and timing as the imported animation but only contains `:method_call` tracks. Hand-authored once, kept in sync manually. Verbose for many events. A dedicated `event` track type in the schema would replace this pattern; until then, the mirror is the supported workaround.

### 6. Per-sprite property override in bulk

Loop in `_ready` from a config dictionary on the wrapper:

```gdscript
@export var sprite_overrides: Dictionary = {
    "head_sprite": {"modulate": Color.RED},
    "torso_sprite": {"z_index": 5},
}

func _ready() -> void:
    for sprite_name in sprite_overrides:
        var node := find_child(sprite_name, true, false)
        if node:
            for prop in sprite_overrides[sprite_name]:
                node.set(prop, sprite_overrides[sprite_name][prop])
```

Verbose but stable. Only breaks if a sprite name changes in Blender.

### 7. Custom Godot-authored animations alongside the imported library

The imported `AnimationPlayer` holds the DCC-authored library under the default (`""`) key. To add Godot-authored animations:

1. Add a separate `AnimationPlayer` to the wrapper (e.g. `UserAnimations`).
2. Author animations into a library on it (e.g. named `"user"`).
3. Trigger from `Doll.gd`: `imported_player.play("idle")` or `user_player.play("user/death_special")`.

Imported library is regenerated on every reimport; user library is wrapper-owned and untouchable from the import side.

## Edge cases and known costs

- **Bone rename in Blender** invalidates wrapper `NodePath`s referencing the old name. Treat renames as cross-DCC operations - rename in Blender, then grep the wrapper for the old name.
- **Sprite added or removed in `.proscenio`**: removed sprites kill any wrapper code addressing them (loud at runtime). Added sprites are visible but inert until the wrapper opts to address them.
- **Mass animation events** scale painfully past roughly 10 events per animation with the mirror-`AnimationPlayer` pattern. If real friction hits, that is the cue to promote the dedicated `event` track type from idea to SPEC.
- **No live link Blender ↔ Godot today**. Each Blender re-export forces a Godot reimport. Tracked as a long-term idea; closing it likely reopens the GDExtension question.

## Why not just merge?

Three options were considered when the wrapper pattern was locked:

- **Full overwrite + wrapper (current)**: zero merge code, plugin-uninstall trivially safe, idiomatic Godot (instance / inherit pattern).
- **Marker-based merge**: rejected because the schema has no stable IDs - bone renames would silently lose user-attached scripts. Plus it duplicates code paths and grows the bug surface.
- **Hybrid (full overwrite default + marker merge opt-in)**: deferred. Reopens if concrete pain emerges that wrapper composition genuinely cannot serve.

Most pain points (events, effects, AI, materials, colliders) have wrapper-pattern recipes documented above. The remaining real friction (animation events, live link) is better solved by dedicated SPECs than by merge logic.
