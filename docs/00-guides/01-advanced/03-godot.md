# Godot

The deep guide to the Godot side: how to add scripts, effects, colliders, audio, and gameplay to a Proscenio character without losing that work on the next reimport. For the quick version, see the [basic walkthrough](../00-basic/03-godot.md).

## The contract

Re-export from Blender **regenerates the imported character from scratch** - anything edited inside it is lost. So you never edit it directly: you keep all your work in a separate scene of your own, the **wrapper**, which instances the character. (Why regenerate instead of merge? See [Why not just merge?](#why-not-just-merge).)

## How the `.proscenio` becomes a scene

The `.proscenio` is not a scene file you open and edit - it is an **import source**, the same way a `.png` is. You drop it in your Godot project (with the PNGs it names beside it, since the `.proscenio` is JSON that refers to its textures by filename), and Godot's [import system](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/import_process.html) runs the Proscenio [`EditorImportPlugin`](https://docs.godotengine.org/en/stable/classes/class_editorimportplugin.html). That plugin **bakes a [`PackedScene`](https://docs.godotengine.org/en/stable/classes/class_packedscene.html)** - the assembled skeleton, sprites, and animations - into Godot's hidden import cache (`.godot/imported/`), not as a sibling file. The baked scene is regenerated on every reimport, which is exactly why it is not yours to edit.

In the FileSystem dock the `.proscenio` still shows up as a single scene you can instance - just like an imported `.glb`. You build your game by [instancing](https://docs.godotengine.org/en/stable/getting_started/step_by_step/instancing.html) it inside a scene of your own: the wrapper.

## The wrapper

The wrapper is a plain `.tscn` you own and version-control. Its root is your node with your script; the imported character is instanced as a child. Everything you add - scripts, AI, effects, colliders - lives on the wrapper, never inside the instanced character. (The on-disk folder layout is in the [basic walkthrough](../00-basic/03-godot.md#wrap-the-generated-scene).)

A reimport regenerates the baked scene; your `.tscn` and `.gd` are untouched. This is the same instance-an-imported-asset pattern you already use for a `.glb` model: edit around it, never inside it. (The recipes below use a made-up `hero` character - swap in your own names; the node paths are illustrative.)

## Wrapper pattern vs Editable Children

Godot gives you two ways to customize an instanced sub-scene: the wrapper, or Godot's built-in [Editable Children](https://docs.godotengine.org/en/stable/getting_started/step_by_step/instancing.html) (which exposes an instance's internal nodes for in-place overrides). Here is how they compare:

| Concern | Wrapper pattern | Editable Children |
| - | - | - |
| A bone renamed in Blender | partial - wrapper [NodePaths](https://docs.godotengine.org/en/stable/classes/class_nodepath.html) break, but a grep and edit fixes them | no - the override is silently orphaned |
| A sprite added or removed in the `.proscenio` | fine - the wrapper is unaffected | no - the override may land on the wrong node or vanish |
| The exporter's output shape evolving | fine - the wrapper's code paths still resolve | no - override paths point at a layer that no longer exists |
| Seeing your customizations | clear - everything is in the wrapper `.tscn` and `.gd`, version-controlled side files | hidden - overrides live inside the `.tscn` as a diff against the sub-scene |
| Conflict with a regenerated default | deterministic - the wrapper applies in `_ready`, last write wins | undefined - the order between sub-scene default and outer diff is opaque |
| Reimport behaviour | clean - the scene regenerates and the wrapper does not flinch | reconcile-or-drop - Godot re-applies overrides and silently drops the ones that no longer fit |
| Plugin uninstalled | safe - the wrapper is a plain `.tscn` | the output still works, but the authoring path becomes read-modify-write |
| Best for | most game-dev work on top of an imported character | a last-resort tweak on a sub-scene that never changes |
| Worst for | per-bone scripts and per-sprite overrides (use composition and a `_ready` loop) | anything that re-exports often or expects the schema to grow |

The wrapper pattern is the default. Editable Children works in narrow, stable cases, but it does not survive the iteration loop the rest of the pipeline is built for.

## Recipes

### AI, behaviour, and state machines

Put the script on the wrapper root (`Hero.gd`) and reach into the imported scene with [`@onready`](https://docs.godotengine.org/en/stable/tutorials/scripting/gdscript/gdscript_basics.html#onready-annotation) references:

```gdscript
extends Node2D
@onready var skeleton: Skeleton2D = $hero/Skeleton2D
@onready var anim: AnimationPlayer = $hero/AnimationPlayer
# ... game logic, signals, state machine, input handling
```

This survives reimport completely. It only breaks if a bone or sprite you reference is renamed in Blender - and that fails loudly at runtime.

### Effects that follow a bone

Add the effect under the wrapper and slave its transform to a bone with a [`RemoteTransform2D`](https://docs.godotengine.org/en/stable/classes/class_remotetransform2d.html):

```text
Hero.tscn
├── hero (instance)
├── HandTrail (GPUParticles2D)
└── HandFollower (RemoteTransform2D)
    remote_path = ../hero/Skeleton2D/torso/arm/hand
```

The `RemoteTransform2D` copies the bone's transform onto the effect every frame. It is wrapper-owned, so it is reimport-safe.

### Colliders and hitboxes on a bone

Same idea as effects: add an [`Area2D`](https://docs.godotengine.org/en/stable/classes/class_area2d.html) (or a [`CharacterBody2D`](https://docs.godotengine.org/en/stable/classes/class_characterbody2d.html) for a solid hitbox) under the wrapper, plus a `RemoteTransform2D` slaved to the bone. Keep the signal handling and the layer / mask setup in `Hero.gd`.

### A material or shader override on a sprite

Apply it at runtime in `_ready` - do not use Editable Children for this:

```gdscript
func _ready() -> void:
    var head_sprite := $hero/Skeleton2D/torso/head/head_sprite as Polygon2D
    head_sprite.material = preload("res://shaders/glow.tres")
    head_sprite.modulate = Color.RED
```

It is reimport-safe because the override is code, not a stored structural diff.

### Animation events (sound cues, gameplay hooks at a frame)

The friction case. Until the schema grows an `event` track type, the workaround is a second [`AnimationPlayer`](https://docs.godotengine.org/en/stable/classes/class_animationplayer.html) on the wrapper, holding mirror animations whose tracks call methods on `Hero.gd`, played in sync with the imported one:

```text
Hero.tscn
├── hero (instance)              imported AnimationPlayer plays the visuals
└── EventPlayer (AnimationPlayer) wrapper-owned, plays method tracks
```

```gdscript
func play_idle() -> void:
    $hero/AnimationPlayer.play("idle")
    $EventPlayer.play("idle_events")  # mirror: method tracks for sound cues
```

The mirror matches the imported animation's length and timing but carries only [Call Method tracks](https://docs.godotengine.org/en/stable/tutorials/animation/animation_track_types.html#call-method-track). You author it once and keep it in sync by hand - which gets verbose past a handful of events.

### Bulk per-sprite overrides

Drive them from a config dictionary on the wrapper, in a `_ready` loop:

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

Verbose but stable; it only breaks if a sprite is renamed in Blender.

### Your own animations alongside the imported ones

The imported `AnimationPlayer` holds the Blender-authored animations in an [animation library](https://docs.godotengine.org/en/stable/tutorials/animation/introduction.html) under the default (`""`) key. To add your own:

1. Add a separate `AnimationPlayer` to the wrapper (say `UserAnimations`).
2. Author your animations into a named library on it (say `"user"`).
3. Trigger from `Hero.gd`: `imported_player.play("idle")` or `user_player.play("user/death_special")`.

The imported library is regenerated on every reimport; your library is wrapper-owned and the import side never touches it.

## Edge cases and known costs

- **A bone renamed in Blender** breaks any wrapper `NodePath` that used the old name. Treat renames as a cross-tool operation: rename in Blender, then grep the wrapper for the old name.
- **A sprite added or removed in the `.proscenio`**: a removed sprite breaks any wrapper code addressing it (loud at runtime); an added sprite is visible but inert until you choose to address it.
- **Lots of animation events** get painful past roughly ten per animation with the mirror-`AnimationPlayer` workaround. That is the signal to promote the `event` track type from idea to spec.
- **No live link between Blender and Godot today.** Each Blender re-export means a Godot reimport. It is parked as a long-term idea; closing it likely reopens the no-GDExtension rule.

## Why not just merge?

Full overwrite plus a wrapper was chosen over merging Blender's output into your edits. A marker-based merge was rejected: the schema has no stable IDs, so a bone rename would silently lose your attached scripts. A hybrid (overwrite by default, opt-in merge) is deferred until wrapper composition proves genuinely insufficient. The current approach needs zero merge code, stays safe when the plugin is uninstalled, and is idiomatic Godot.

Most pain points - effects, AI, materials, colliders - have a wrapper recipe above. The two that still bite, animation events and a live link, are better solved by dedicated specs than by merge logic.
