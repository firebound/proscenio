# Basic walkthrough

The full Photoshop → Blender → Godot loop in one linear pass, grouped by the tool you are in at each stage.

For depth on any single tool, see the per-tool guides: [Photoshop](../01-advanced/01-photoshop.md), [Blender](../01-advanced/02-blender.md), [Godot](../01-advanced/03-godot.md).

> [!NOTE]
> **MVP in progress.** The full quickstart will land with the first end-to-end sample. The loop below describes the flow once both sides ship; some buttons exist ahead of the sample art.

1. [Photoshop](01-photoshop.md): author the PSD with layer tags, then export the manifest and PNGs.
2. [Blender](02-blender.md): import the layers, build the skeleton, skin the meshes, set sprite types, refine, add slots, animate, pack the atlas, and export.
3. [Godot](03-godot.md): drop the `.proscenio` in and wrap the generated scene.
4. [Iterate](04-iterate.md): the re-export loop that keeps both sides in sync.
