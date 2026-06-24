# Iterating through the loop

This is a loop, not a one-shot. One edit ripples across all three tools, and today each hop is a deliberate re-export / re-import - there is no live link **yet**.

Say you repaint a layer's PNG in Photoshop. To see it in the running Godot scene:

1. *Re-export from Photoshop*: the manifest + PNGs.

2. *Re-import in Blender*: point at the manifest again. Idempotent for object-level work - your rig, parenting, slots, per-sprite settings, and painted weights carry over (a changed-placement layer rebuilds the quad but reprojects its weights from the sidecar; only Automesh density resets, so re-densify after). The one thing that breaks the carry-over is renaming a layer in the PSD: that orphans the old plane (weights and all) and stamps a blank one, unless you re-point its tag first. See [the re-import contract](02-advanced/01-photoshop.md#re-importing-after-psd-edits).

3. *Re-export from Blender*: `Re-export` reuses the sticky path, no dialog.

4. *Reimport in Godot*: automatic on editor focus. Godot regenerates the imported character from scratch - the baked scene is fully overwritten, so anything edited *inside* it is lost. That is exactly why your work lives in a separate **wrapper** scene that instances the character: the wrapper `.tscn` / `.gd` is untouched by the reimport. See [the Godot contract](02-advanced/03-godot.md#the-contract).

Four steps, none of which discard your downstream work - because it all sits in places the regeneration does not touch: your weights ride the sidecar in Blender, and your game code rides the wrapper in Godot. That is the property the whole pipeline is built around.

## What is not automated yet

Every hop above is manual on purpose - there is no hot reload across the tool boundaries yet. The biggest gap is a live Blender <-> Godot link; that and the other not-yet-built directions are laid out in [Deferred](../01-project/04-deferred.md).

## Help and feedback

- Hit a bug or want a feature? Open an issue: [Proscenio issues](https://github.com/firebound/proscenio/issues).
- Want to contribute? See [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
- Per-tool depth lives in the workflow guides: [Photoshop](02-advanced/01-photoshop.md), [Blender](02-advanced/02-blender.md), [Godot](02-advanced/03-godot.md).
