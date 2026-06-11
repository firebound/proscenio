# Iterating through the loop

This is a loop, not a one-shot. One edit ripples across all three tools, and today each hop is a deliberate re-export / re-import - there is no live link **yet**.

Say you repaint a layer's PNG in Photoshop. To see it in the running Godot scene:

1. *Re-export from Photoshop*: the manifest + PNGs.

2. *Re-import in Blender*: point at the manifest again. Idempotent for object-level work - your rig, parenting, slots, and per-sprite settings carry over - but the mesh is rebuilt from the new art, so painted weights and Automesh density do not survive ([the order that saves your skinning](01-advanced/01-photoshop.md#re-importing-after-psd-edits)).

3. *Re-export from Blender*: `Re-export` reuses the sticky path, no dialog.

4. *Reimport in Godot*: automatic on editor focus, and your wrapper scene is untouched.

Four steps, none of which discard your downstream work on the Godot side - that is the property the whole pipeline is built around.

## What is not automated yet

Every hop above is manual on purpose - there is no hot reload across the tool boundaries yet. The biggest gap is a live Blender <-> Godot link; that and the other not-yet-built directions are laid out in [Deferred](../01-project/04-deferred.md).

## Help and feedback

- Hit a bug or want a feature? Open an issue: [Proscenio issues](https://github.com/firebound/proscenio/issues).
- Want to contribute? See [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
- Per-tool depth lives in the workflow guides: [Photoshop](01-advanced/01-photoshop.md), [Blender](01-advanced/02-blender.md), [Godot](01-advanced/03-godot.md).
