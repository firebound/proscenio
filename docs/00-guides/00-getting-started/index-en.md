# Getting started

Proscenio is a Photoshop -> Blender -> Godot pipeline for 2D cutout animation: you paint the art in Photoshop, rig and animate it in Blender, and ship a native scene to Godot. This page covers what you need installed, where each plugin lives, and the shape of the loop, then hands off to the basic walkthrough for the step-by-step.

## Prerequisites

You author in all three tools, so you need all three installed:

- **Photoshop 2024+** - where the art lives and the layered `.psd` is authored.
- **Blender 4.2+** - the hub of the pipeline: import, rig, skin, animate, and export.
- **Godot 4.6+** - the runtime target the `.proscenio` imports into as a native scene.

## Where to get each plugin

The quickest path is the prebuilt bundles attached to every [GitHub release](https://github.com/firebound/proscenio/releases): each tag ships a ready-to-install archive per tool.

- **Photoshop plugin** - `proscenio-photoshop-<version>.ccx`. Double-click it and Photoshop's UXP installer takes over (it prompts to allow an untrusted developer, since the plugin is unsigned). A `proscenio-photoshop-<version>.zip` with the same contents is attached too if you prefer to load it manually.
- **Blender addon** - `proscenio-blender-<version>.zip`. Install it from `Edit > Preferences > Add-ons > Install from Disk`, then enable it.
- **Godot plugin** - `proscenio-godot-<version>.zip`. Unzip its `addons/proscenio` into your project's `addons/` folder and enable it under `Project > Project Settings > Plugins`.

Once installed, each plugin lives where you author:

- **Photoshop plugin** - the [UXP](https://developer.adobe.com/photoshop/uxp/) exporter. It loads inside Photoshop and adds the **Proscenio** panels under `Plugins > Proscenio ...`.
- **Blender addon** - the Python addon. Once enabled it adds the **Proscenio** tab to the 3D Viewport sidebar (open it with <kbd>N</kbd>).
- **Godot plugin** - the GDScript editor plugin. It registers an importer that turns any `.proscenio` file into a scene on import.

Prefer to build from source? Each plugin's source lives in the repository under [`apps/photoshop/`](../../../apps/photoshop/), [`apps/blender/`](../../../apps/blender/), and [`apps/godot/`](../../../apps/godot/).

## The shape of the loop

One character moves through the three tools in order, each handing the next a single file:

1. **Photoshop** - tag the layers and export a manifest plus one PNG per layer.
2. **Blender** - import the manifest, build the skeleton, skin the meshes, set element types, add slots, animate, optionally pack an atlas, and export the `.proscenio`.
3. **Godot** - drop the `.proscenio` in and wrap the generated scene with your own gameplay.

Each step is idempotent, so editing any stage and pushing the change through again keeps every side in sync without discarding your downstream work. That repeat pass is [the iteration loop](../03-iterate.md).

## Next steps

- Follow the [basic walkthrough](../01-basic/index.md) for the full loop, one page per tool.
- Once you are past your first character, the [advanced workflows](../02-advanced/index.md) go deeper on each tool's panels, contracts, and gotchas.
- For the per-app reference, see the [Tools hub](../../02-tools/index.md).
