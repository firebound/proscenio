# Godot: wrap and play

Godot imports the `.proscenio` into a native scene; your job is to wrap that scene so your own work survives re-exports.

## Import the .proscenio

A `.proscenio` is just JSON - it names its textures by filename (the atlas, any per-sprite PNGs, the composed spritesheets), so it does not travel alone.

_Import_: copy the `.proscenio` **and the PNGs it names** into one folder in your Godot project. They must sit side by side, no subfolders - the importer resolves every texture by filename relative to the `.proscenio`.

Godot then imports it as a scene, baked into the import cache (you never see or edit it as a file). The result is plain Godot nodes that run even with the plugin uninstalled.

Instancing it gives you:

```text
<root> (Node2D)
├── Skeleton2D
│   ├── Bone2D ...        the rig
│   ├── Polygon2D ...     cutout sprites (skinned ones deform via bone weights)
│   ├── Sprite2D ...      sprite_frame sprites (hframes/vframes grid)
│   └── Node2D ...        slots (visibility-toggled attachment children)
└── AnimationPlayer       one library: bone_transform, sprite_frame, slot tracks
```

Skinned `Polygon2D` sprites carry `Polygon2D.skeleton` + per-bone weight arrays, so they deform with the rig; rigid ones are parented to their `Bone2D`. `Sprite2D` sprites slice their `region_rect` by `hframes` / `vframes`. Slots hold their attachments and a track flips which one is visible.

## Wrap the generated scene

Reimport **fully regenerates** the imported scene, so anything changed inside it is lost. Keep all your work in a wrapper scene that instances the `.proscenio`:

```text
res://characters/<character>/
├── <character>.proscenio   from Blender; you instance this
├── <character>.atlas.png   plus every PNG the .proscenio names, same folder
├── <character>.tscn        yours - instances <character>.proscenio
└── <character>.gd          your script, on the wrapper root
```

1. _Instance the character_: in your own `<character>.tscn`, instance `<character>.proscenio` (Godot treats the imported `.proscenio` as a `PackedScene`).

2. _Build on the wrapper_: scripts, effects, colliders, and gameplay all live on the wrapper, never inside the imported scene. Reach into the imported nodes from the wrapper - for example, play an imported animation:

```gdscript
@onready var anim: AnimationPlayer = $Character/AnimationPlayer

func _ready() -> void:
    anim.play("idle")
```

Effects and colliders follow a bone with a `RemoteTransform2D`; per-sprite material or visibility overrides go in `_ready`. The [Godot workflow](../01-advanced/03-godot.md) has the full recipe set (AI, effects, colliders, shader overrides, animation events, custom animations) and the wrapper-vs-editable-children trade-offs.

> [!WARNING]
> **Never edit the imported scene directly.** It is regenerated on every re-export from Blender, so changes inside it are lost. Always build on the wrapper.

Reference fixtures: [`examples/authored/doll/`](../../../examples/authored/doll/) is the comprehensive showcase; [`examples/generated/blink_eyes/`](../../../examples/generated/blink_eyes/) isolates the `sprite_frame` path, and [`examples/generated/shared_atlas/`](../../../examples/generated/shared_atlas/) isolates the sliced-atlas path. See the [Godot workflow](../01-advanced/03-godot.md) for importer behaviour in detail.
