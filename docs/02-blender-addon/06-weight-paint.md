# Weight Paint

Bind a cutout mesh to the rig and refine its bone weights. The panel is mesh-only - it warns when the active element is a sprite. Bind plus the resulting weights export to the Polygon2D; the edit / snapshot / transfer tools are blender-side.

## Bind

Builds the vertex weights that let the rig deform the mesh. **Mode** picks the algorithm: Bone Heat is the Blender-native default; Proximity / Envelope / Single-nearest / Empty are F3-redo fallbacks.

**Per-bone Soft / Hard** overrides a single bone's falloff. Soft shares weight smoothly with neighbours (cloth, hair); Hard gives a crisp single-nearest boundary (finger joints). A bone with no override uses the mode's default family.

## Edit Weights

Enters a modal weight-paint session on the active group with a provenance overlay (auto-seed vs hand-painted verts). The brush-curve presets (Hard Edge / Soft Falloff / Crease / Smooth Blend) shape the brush for common 2D tasks. Bind first - the button is disabled until then.

## Snapshot

The weight snapshot stores, per vertex, a UV anchor plus its weights and provenance. *Preserve weights on regen* snapshots the weights by UV before an automesh re-run and reprojects them onto the new mesh (off = the regen wipes paint); *Reset to Last Saved Weights* reverts the live weights to that snapshot.

## Sidecar IO

Exports the weight snapshot to a JSON file, or imports one back - useful for version-controlling weights in git or moving them between files. Import loads the snapshot; run *Reset to Last Saved Weights* to push it onto the live mesh (the topology must match).

## Weight Transfer

Copies weights from the active mesh to every other selected mesh by nearest world-space vertex - an imprint for layered or split cutouts that overlap a rigged base. Target verts beyond the Max Distance (F3 redo) get no weights.
