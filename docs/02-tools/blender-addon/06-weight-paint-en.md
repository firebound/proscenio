# Weight Paint

Bind a cutout mesh to the rig and refine its bone weights. The panel is mesh-only - it warns when the active element is a sprite. It shows the target rig (picked in the [Skeleton](04-skeleton.md) panel) that the subpanels act on. Bind plus the resulting weights export to the Polygon2D; the edit, snapshot, and transfer tools are blender-side.

## Bind

Builds the vertex weights that let the rig deform the mesh. **Mode** picks the algorithm: Bone Heat is the Blender-native default; Proximity / Envelope / Single-nearest / Empty are the alternatives (Proximity adds `Max Distance` and `Falloff Power` fields). The `Bind to Target Armature` button is disabled until a rig is picked.

**Per-bone Soft / Hard** overrides a single bone's falloff: Soft shares weight smoothly with neighbours (cloth, hair), Hard gives a crisp single-nearest boundary (finger joints), and the X clears an override back to the mode default. The overrides apply only to the planar modes - under Bone Heat the box shows a hint, because Bone Heat ignores them. The list scrolls so a many-bone rig does not push the Bind button off-screen.

## Edit Weights

Enters a modal weight-paint session on the active group with a provenance overlay (auto-seed vs hand-painted verts). The button is disabled until you bind (it needs a populated snapshot); once you are painting it turns into `Exit Painting Mode`. The brush-curve presets (Hard Edge / Soft Falloff / Crease / Smooth Blend) shape the brush for common 2D tasks. A **Viewport display** box surfaces Blender's own Weight Opacity and Zero Weights levers so the texture shows through the gradient while painting. `Clear Empty Vertex Groups` drops groups left empty by re-binds or edits.

## Snapshot

The weight snapshot stores, per vertex, a UV anchor plus its weights and provenance (auto-seed / hand-paint / reprojected); it is the safety net that survives a mesh rebuild. `Preserve weights on regen` snapshots the weights by UV before an automesh re-run and reprojects them onto the new mesh (off = the regen wipes paint). A pill reports the paint / seed / reprojected counts, and `Reset to Last Saved Weights` reverts the live weights to the snapshot.

Below that, named save points: `Save Snapshot` adds a manual save point (unbounded), and the Edit Weights modal adds a few rolling auto-snapshots per session; each row restores its snapshot. `Export Snapshot` and `Import Snapshot` write the snapshot to a JSON file or load one back - useful for version-controlling weights or moving them between files. Import pushes the weights onto the live mesh when the topology matches; otherwise it stores the snapshot only (re-run Automesh with Preserve weights on regen to reproject).

## Weight Transfer

Copies weights from the active mesh to every other selected mesh by nearest world-space vertex - an imprint for layered or split cutouts that overlap a rigged base. Target verts beyond the `Max Distance` (the panel field, also exposed in the F9 redo) get no weights.
