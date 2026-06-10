---
title: Godot Plugin
---

# Godot Plugin

A GDScript editor plugin: a single [`EditorImportPlugin`](https://docs.godotengine.org/en/stable/classes/class_editorimportplugin.html) plus a handful of builders that turn a `.proscenio` file into a native Godot scene on every reimport.

## What it does

- **Reimport to a native scene.** The plugin regenerates a scene (Skeleton2D + Bone2D + Polygon2D / Sprite2D + AnimationPlayer) whenever a `.proscenio` file enters or changes in the project. The generated scene runs with the plugin uninstalled: it is plain Godot 4 nodes, no GDExtension and no runtime dependency.
- **Wrapper-scene safety.** A user-authored wrapper scene that instances the generated one survives every reimport, so scripts and gameplay nodes are never clobbered.
- **Typed read.** The importer reads the document as a typed Resource (`ProscenioDocument.from_dict`), checks the `format_version`, and builds the node tree in order: skeleton, atlas, slots before sprites, sprites, animation.

## How it is built

Small and focused: one import plugin and five builders, each handling only the node types it recognizes by reading the `type` field on each element. No inheritance or polymorphism, just functions called in sequence. The typed read layer is generated from the schema.

See [Architecture](../01-project/01-architecture.md) for how the plugin fits the pipeline, and the [Schema reference](../content/proscenio/document.mdx) for the `.proscenio` format it reads.
