---
name: references
description: Prior-art repos and external docs to study before implementing a feature
---

# References

External resources grouped by tier. Read the relevant section before writing a feature, not after.

## Tier 1 - Engine internals (Godot)

Classes and concepts the importer uses every day.

### `EditorImportPlugin`

<https://docs.godotengine.org/en/stable/classes/class_editorimportplugin.html>

The class our plugin extends. Import lifecycle, options, where saved resources land under `.godot/imported/`.

### `PackedScene` and `ResourceSaver`

<https://docs.godotengine.org/en/stable/classes/class_packedscene.html>
<https://docs.godotengine.org/en/stable/classes/class_resourcesaver.html>

How scenes are constructed in memory and saved to disk.

### `AnimationLibrary` and `AnimationPlayer`

<https://docs.godotengine.org/en/stable/classes/class_animationlibrary.html>
<https://docs.godotengine.org/en/stable/classes/class_animationplayer.html>

Godot 4 separated animations from the player. Importer creates one default library `""` and adds animations to it.

### `Skeleton2D`, `Bone2D`, `Polygon2D`

<https://docs.godotengine.org/en/stable/classes/class_skeleton2d.html>
<https://docs.godotengine.org/en/stable/classes/class_bone2d.html>
<https://docs.godotengine.org/en/stable/classes/class_polygon2d.html>

The three nodes the importer assembles. `Polygon2D.skeleton` (NodePath) and `Polygon2D.set_bones()` are the skinning entry points.

### `Sprite2D`

<https://docs.godotengine.org/en/stable/classes/class_sprite2d.html>

The `sprite_frame` track type relies on `hframes` / `vframes` / `frame`.

### TSCN file format

<https://docs.godotengine.org/en/stable/contributing/development/file_formats/tscn.html>

We do not write `.tscn` text by hand - `PackedScene.pack()` handles it - but the format is useful for debugging diffs.

## Tier 2 - DCC authoring (Blender, Photoshop)

### Blender Extensions Platform

<https://docs.blender.org/manual/en/latest/extensions/getting_started.html>

The 4.2+ extension system. Our addon ships under it - see [`apps/blender/blender_manifest.toml`](../../apps/blender/blender_manifest.toml).

### `bpy` API reference

<https://docs.blender.org/api/current/>

Lookup for operators, properties, types. Stay on stable APIs - `coa_tools2` has been chasing `bpy` drift for years (issues #92, #93, #95, #107, #109, #110, #111).

### Photoshop UXP guide (Adobe)

<https://developer.adobe.com/photoshop/uxp/2022/guides/>

UXP plugin target. TypeScript + React stack; replaces ExtendScript / JSX.

### Photoshop UXP API reference

<https://developer.adobe.com/photoshop/uxp/2022/ps_reference/>

Photoshop DOM exposed to UXP plugins.

### Photoshop UXP storage (file system)

<https://developer.adobe.com/photoshop/uxp/2022/uxp-api/reference-js/Modules/uxp/Persistent%20File%20Storage/>

Sandboxed file system API. Replaces ExtendScript's direct `File` constructor.

## Tier 3 - Competitor and prior-art study

One line per entry. Read the source or docs when designing a feature that overlaps the tool's niche.

### Skeleton-based cutout (paradigm-direct)

- **Spine** (paid, industry standard). <https://esotericsoftware.com/> + <https://en.esotericsoftware.com/spine-in-depth>. Reference for skeletal 2D animation features (skins, FFD, IK, paths, runtime preview).
- **DragonBones** (open Spine alt, multi-runtime). <https://github.com/DragonBones>. Free Spine-clone with JSON format and a community editor.
- **COA Tools 2** (Aodaruma fork, GPL, alive). <https://github.com/Aodaruma/coa_tools2>. Direct prior art for the Blender side. PSD / Krita / GIMP exporters useful as porting targets; Godot importer broken - see issue [#28](https://github.com/Aodaruma/coa_tools2/issues/28).
- **COA Tools original** (ndee85, abandoned since 2019). <https://github.com/ndee85/coa_tools>. Source of the reimport-merge pattern that informed SPEC 001's wrapper-scene approach. Godot 2.x only.
- **Godot 2D Bridge** (Tor-Kai, stuck on Godot 4.0). <https://github.com/Tor-Kai/Godot-2d-Bridge-1.0.0>. Boundary-first vertex ordering and bone-weight mapping references; no animation pipeline.

### Engine-side plugins

- **Souperior 2D Skeleton Modifications** (Godot, MIT). <https://github.com/ZedManul/souperior-2d-skeleton-modifications>. IK + LookAt nodes that extend Godot's `Skeleton2D` modification system. Stack-on-top reference for runtime IK polish.
- **Puppet2D** (Unity, paid Asset Store). Skeletal rigging with control-point mesh deform inside Unity.
- **AnyPortrait** (Unity, paid Asset Store). <http://anyportrait.com/>. Closest Unity-side feature counterpart - PSD layered import, mesh deform with weights, IK, motion paths, bone physics, automesh from sprite.
- **Unity 2D Animation package** (Unity, free). <https://docs.unity3d.com/Packages/com.unity.2d.animation@latest/>. Sprite Skinning + IK Manager 2D + Sprite Library. Closest engine-native counterpart on Unity.

### Adjacent paradigms (different problem space)

- **Live2D Cubism** (paid, free tier). <https://www.live2d.com/>. Illustration-first, parameter-driven 2.5D mesh deformer. Different art form; reference for "preserve the drawn artwork" philosophy.
- **DUIK Angela** (free). <https://rxlaboratory.org/tools/duik/>. Auto-rig + controller paradigm for After Effects. Reference for templates / presets QoL.
- **RubberHose** (paid). <https://battleaxe.co/rubberhose>. Non-destructive mid-animation re-rig paradigm. Reference for the "technique decisions do not lock creative direction" philosophy.

## Tier 4 - explicitly avoided

### Spine Godot runtime

<https://github.com/EsotericSoftware/spine-runtimes/tree/4.2/spine-godot>

The anti-pattern Proscenio rejects: paid runtime, GDExtension dependency, "third-party-of-third-party" support, custom C++ engine module variant. Read once to understand why we chose differently. Do not adopt patterns from it.
