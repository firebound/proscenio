# Photoshop: the foundation

Photoshop is where the art lives. The UXP exporter turns your layered `.psd` into the two things Blender needs: a manifest (a JSON describing every layer) and one PNG per layer.

## Author the PSD: layer kinds and tags

Every visible layer becomes one object on the Blender side. What kind of object depends on **bracket tags** written into the layer name - tokens like `[tag]` or `[tag:value]`. Tags are stripped from the name before export, so `arm.R [mesh] [folder:body]` exports as `arm.R`.

You can type tags into layer names by hand, but the plugin's **Tags** panel is the easier path: it shows the document's layer tree with per-row tag controls, writes the brackets into the layer names for you, and flags warnings and skipped layers live as you go.

The tag decides the layer's kind:

| Kind | How you tag it | What it becomes |
| - | - | - |
| `polygon` | default for any art layer (or `[polygon]`) | a cutout sprite -> Godot `Polygon2D` |
| `mesh` | `[mesh]` on the layer | imports as a `polygon` sprite, just flagged as a deformable-mesh source (a hint for skinning) - not a separate type downstream |
| `sprite_frame` | `[spritesheet]` on the **group** | a spritesheet sprite (each child layer is one frame) -> Godot `Sprite2D` |

So downstream there are only two sprite types, `polygon` and `sprite_frame` - a `[mesh]` layer is just a `polygon` flagged for skinning (the flag rides along as metadata).

Other tags shape how a layer exports:

| Tag | Where | Function |
| - | - | - |
| `[ignore]` | layer or group | skipped entirely - no entry, no PNG (use it for refs and notes) |
| `[merge]` | group | flatten all children into a single PNG |
| `[folder:NAME]` | group | becomes a Blender `Collection` named `NAME` |
| `[origin]` / `[origin:X,Y]` | layer or group | set the pivot (implicit centroid, or explicit PSD pixel coords) |
| `[blend:multiply]` / `[blend:screen]` / `[blend:additive]` | layer | tags the intended blend mode (kept as metadata; not exported to Godot yet) |
| `[scale:N]` | layer or group | multiply the bounding-box size by `N` |

The full taxonomy (every tag, the walk rules for groups and hidden layers, z-order, the document anchor) lives in the [Photoshop workflow](../01-advanced/01-photoshop.md).

## Export the manifest and PNGs

1. *Open the source*: the layered `.psd` in Photoshop.

2. *Open the exporter*: `Plugins > Proscenio Exporter` (loaded via the UXP plugin in [`apps/photoshop/`](../../../apps/photoshop/)).

3. *Pick an output folder*: where the manifest and PNGs will land.

4. *Export*: click `Export manifest + PNGs`. → The plugin writes a v2 manifest JSON next to one PNG per layer.

<!-- screenshot: Proscenio Exporter panel in Photoshop with Export button highlighted -->
