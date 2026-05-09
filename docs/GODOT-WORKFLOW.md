# Godot workflow: customizing an imported character

How to add scripts, effects, colliders, audio, and gameplay logic to a Proscenio character on the Godot side without losing work on the next reimport.

## The contract

When Blender re-exports a `.proscenio`, the Proscenio importer **fully overwrites** the generated `.scn`. Any direct edit to that `.scn` is lost. This is by design ([SPEC 001 Option A](../specs/001-reimport-merge/STUDY.md)) and underwrites the "Non-destructive integration" pillar via *physical separation* rather than merge logic.

The user-facing rule: **never edit `<name>.scn` directly. Work only on your own `<Name>.tscn` wrapper.**

## Layout

```text
res://characters/doll/
├── doll.proscenio        source, Blender owns
├── doll.scn              generated, Proscenio overwrites every reimport
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
| Survives exporter shape evolution (e.g. SPEC 004 added Node2D anchor between Bone2D and Polygon2D) | yes - wrapper code paths still resolve | no - override paths point to a layer that no longer exists |
| Visibility / inspectability of customizations | high - everything is in `Doll.tscn` + `Doll.gd`, version-controlled side files | low - overrides hide inside the wrapper `.tscn` as a diff against the sub-scene; no UI surfaces "show all overrides" |
| Property override conflict with regenerated default (e.g. material) | resolved deterministically: wrapper applies in `_ready`, last-write-wins | undefined: order between sub-scene default and outer diff is opaque |
| Reload semantics | clean - reimport regenerates `doll.scn`, wrapper does not flinch | reconcile-or-drop - Godot tries to re-apply overrides; on mismatch, drops silently |
| Plugin-uninstall safety | trivially preserved - wrapper is a normal `.tscn` | preserved at output but the production path becomes read-modify-write (more failure modes) |
| Best at | 95% of game-dev customization on top of an imported character | last-resort tweak on a stable sub-scene that does not evolve |
| Worst at | per-bone scripts and per-sprite property overrides (mitigated by composition + `_ready` loops) | anything in a project that re-exports often or expects schema evolution |

**Verdict for Proscenio**: wrapper pattern is the documented default. Editable Children works in narrow, stable cases but does not survive the iteration loop the rest of the pipeline is optimized for. If you reach for it, you are fighting the contract.

## Recipes by use case

Each recipe describes the pattern; concrete code lives in [`examples/doll/godot/`](../examples/doll/godot/) where applicable.

### 1. AI / behavior / state machine on the character

Script lives on the root of `Doll.tscn` (`Doll.gd`). Operates from the outside via `@onready` references into the imported scene.

```text
extends Node2D
@onready var skeleton := $doll/Skeleton2D
@onready var anim   := $doll/AnimationPlayer
# ... game logic, signals, state machine, input handling
```

Survives reimport completely. Reads internals via NodePath; only breaks if a referenced bone/sprite gets renamed in Blender (and even then, error is loud at runtime).

### 2. Particles / effects following a bone

Add the effect under the wrapper, slave its transform to a bone via `RemoteTransform2D`:

```text
Doll.tscn
├── doll (instance)
├── HandTrail (GPUParticles2D)
└── HandFollower (RemoteTransform2D)
    remote_path = ../doll/Skeleton2D/torso/arm/hand
```

The `RemoteTransform2D` copies the bone's transform every frame onto the effect. Wrapper-owned, reimport-safe. Cost: one NodePath that breaks if the bone is renamed.

### 3. Colliders / hitboxes anchored to a bone

Same pattern as effects. Add `Area2D` (or `KinematicBody2D` for solid hitboxes) under the wrapper, plus a `RemoteTransform2D` slaved to the relevant bone.

```text
Doll.tscn
├── doll (instance)
└── Hitbox (Area2D)
    ├── CollisionShape2D
    └── BoneAnchor (RemoteTransform2D, remote_path = ../doll/Skeleton2D/torso)
```

Signal handling, layer/mask configuration, hit reaction logic all live on `Doll.gd`.

### 4. Material / shader override on an imported sprite

Apply at runtime in `_ready`. Do not use Editable Children for this - the override would conflict with whatever the importer regenerates and the conflict resolution is opaque.

```text
func _ready() -> void:
    var head_sprite := $doll/Skeleton2D/torso/head/head_sprite as Polygon2D
    head_sprite.material = preload("res://shaders/glow.tres")
    head_sprite.modulate = Color.RED
```

Runs on every scene instance, after the imported scene loads. Reimport-safe because the override is applied by code, not stored as a structural diff.

### 5. Animation events (sound cues, gameplay hooks at specific frames)

The friction case. Today's workaround uses a **second `AnimationPlayer` on the wrapper** with mirror animations whose tracks call methods on `Doll.gd`. Synchronize with the imported AnimationPlayer:

```text
Doll.tscn
├── doll (instance)              imported AnimationPlayer plays the visuals
└── EventPlayer (AnimationPlayer) wrapper-owned, plays method tracks

# Doll.gd
func play_idle() -> void:
    $doll/AnimationPlayer.play("idle")
    $EventPlayer.play("idle_events")  # mirror: method tracks for sound cues
```

The mirror has the same length and timing as the imported animation but only contains `:method_call` tracks. Hand-authored once, kept in sync manually. Verbose for many events.

The proper solution is a deferred SPEC: **animation events / method tracks** in the schema. Once shipped, the writer emits `event` tracks alongside `bone_transform`, the importer wires `AnimationPlayer` method tracks pointing at functions on the wrapper script, and the mirror disappears entirely. Tracked in [`docs/DEFERRED.md`](DEFERRED.md). Until then, the mirror pattern is the supported workaround.

### 6. Per-sprite property override in bulk (modulate, z-index, visibility default)

Loop in `_ready` from a config dictionary on the wrapper:

```text
@export var sprite_overrides := {
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

Verbose but stable. Survives reimport. Only breaks if a sprite name changes in Blender (and the missing-find is loud).

### 7. Custom Godot-authored animations alongside the imported library

The imported `AnimationPlayer` holds the default (`""`) `AnimationLibrary` populated from `.proscenio`. To add Godot-authored animations:

1. Add a separate `AnimationPlayer` to the wrapper (e.g. `UserAnimations`).
2. Author animations into a library on it (e.g. named `"user"`).
3. Trigger from `Doll.gd`: `imported_player.play("idle")` or `user_player.play("user/death_special")`.

Imported library is regenerated on every reimport; user library is wrapper-owned and untouchable from the import side. Boundary stays clean.

## Edge cases and known costs

- **Bone rename in Blender**: invalidates wrapper `NodePath`s referencing the old name. Treat rename as a cross-DCC operation - rename in Blender + grep the wrapper for the old name. Same workflow as renaming a node in any engine.
- **Sprite added/removed in `.proscenio`**: removed sprites kill any wrapper code addressing them; loud at runtime. Added sprites are visible but inert until the wrapper opts to address them.
- **Mass animation events**: the mirror-AnimationPlayer pattern scales painfully past ~10 events per animation. The animation-events deferred SPEC is the solution; if friction hits hard, that SPEC's priority gets re-evaluated.
- **Live iteration speed**: each Blender re-export forces a Godot reimport. There is no live link today. Tracked as a deferred item; closing it likely reopens the GDExtension question (see [`docs/DECISIONS.md`](DECISIONS.md)).

## Why not just merge?

Reasonable question. [SPEC 001 STUDY](../specs/001-reimport-merge/STUDY.md) considered three options and chose A:

- **Option A (full overwrite + wrapper, current)**: zero merge code, plugin-uninstall trivially safe, idiomatic Godot (instance/inherit pattern).
- **Option B (marker-based merge)**: rejected because schema v1 has no stable IDs - bone renames silently lose user-attached scripts. Plus duplicates code paths and grows the bug surface.
- **Option C (hybrid: A default + B opt-in)**: deferred. Reopens if concrete pain emerges that wrapper composition genuinely cannot serve.

Most pain points users hit (events, effects, AI, materials, colliders) have wrapper-pattern recipes documented above. The remaining real friction (animation events, live link) is better solved by **dedicated SPECs** than by merge logic. See [`docs/DEFERRED.md`](DEFERRED.md) and [`docs/DECISIONS.md`](DECISIONS.md).

## See also

- [SPEC 001 — Reimport without losing user work](../specs/001-reimport-merge/STUDY.md): full design rationale and option matrix.
- [`.ai/skills/godot-plugin-dev.md`](../.ai/skills/godot-plugin-dev.md): plugin internals (importer, builders, slot system).
- [`docs/DECISIONS.md`](DECISIONS.md): cross-cutting architectural decisions.
- [`docs/DEFERRED.md`](DEFERRED.md): future SPECs that will reduce wrapper-pattern friction.
- [`examples/doll/godot/`](../examples/doll/godot/): worked example wrapper (`Doll.tscn` + `Doll.gd`).
