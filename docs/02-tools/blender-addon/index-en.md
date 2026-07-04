# Blender Addon

Per-panel reference for the Proscenio sidebar. Open it in Blender at **3D Viewport > Sidebar (`N`) > Proscenio**.

For the end-to-end workflow, start with the [Blender walkthrough](../../00-guides/01-basic/02-blender.md); this section documents each panel and subpanel on its own.

> [!NOTE]
> **Placeholder pages.** These reference pages are a first cut. Each panel and subpanel carries a brief, specific description that mirrors the in-addon `?` help; they expand over time.

## What it does

The addon is where the pipeline's heavy lifting happens:

- **Mesh authoring (automesh)** - trace a sprite's alpha into a deformable mesh, one-click or through an interactive multi-stage modal; weight-preserving regeneration reprojects paint when you re-densify.
- **Skeleton authoring (Quick Armature)** - draw bones in the viewport by dragging head to tail.
- **Weight bind and paint** - five bind modes (Bone Heat, Proximity, Envelope, Single Nearest, Empty), a 2D-tuned Edit Weights modal, copy-weights-between-sprites, and a weight sidecar that records provenance.
- **Slots** - sprite-swap groups animated by slot index.
- **Atlas** - pack, unpack, and apply a shared texture atlas.
- **Source-art ingestion** - import a Photoshop manifest into planes plus a root bone (re-import reuses the planes and the armature and preserves painted weights - intact on a same-placement layer, reprojected from the sidecar on a changed one).
- **Export to Godot** - validate the scene, write the `.proscenio`, and one-click re-export to the same path afterwards.

Each capability has its own panel below; the bind modes and the automesh-vs-reimport weight rules are detailed in [Weight Paint](06-weight-paint.md) and [Mesh Generation](05-mesh-generation.md).

## The sidebar

Every panel renders on any selection and warns (rather than hiding) when it needs a different one. Each header carries a status badge plus a `?` that opens the matching help inline (see [Header affordances](#header-affordances) below).

- [Outliner](01-outliner.md) - sprite-centric flat list of slots, meshes, and armatures.
- [Element](02-element.md) - per-element settings (Polygon2D vs Sprite2D, texture region, drive-from-bone).
- [Slots](03-slots.md) - the project slot list and per-slot attachment detail.
- [Skeleton](04-skeleton.md) - the armature picker, bone list, pose helpers, and Quick Armature.
- [Mesh Generation](05-mesh-generation.md) - trace a sprite alpha into a deformable mesh.
- [Weight Paint](06-weight-paint.md) - bind and refine bone weights (mesh elements only).
- [Animation](07-animation.md) - read-only summary of the actions the writer exports.
- [Atlas](08-atlas.md) - pack source images into a shared atlas.
- [Pipeline](10-pipeline.md) - import a Photoshop manifest, validate the scene, and export the `.proscenio`.
- [Helpers](11-helpers.md) - viewport authoring aids that sit outside the export.

## Header affordances

Every panel and subpanel header carries two controls on its right edge, and a sub-box inside a body (the sprite Material Preview block) repeats the same pair on its title row. On a narrow N-panel both are dropped so they do not overlap the title. The conventions below hold everywhere, so the per-panel pages do not repeat them.

The **`?` help button** opens that feature's help inline - a popup with a one-line summary, what it does, how to use it, where it fits the pipeline, and any caveats - plus an `Open online docs` button that links to the matching page in this section. A row whose own help differs from its subpanel (the Save Pose to Library button under Pose Mode) carries its own `?`.

The **status badge** shows where the feature lands in the pipeline. Hover it for the band tooltip; click it to open the legend below. The godot-ready band uses a Godot mark, blender-only uses a Blender mark, and the rest use a built-in icon.

## Status badges

The single legend for the four bands a status badge can show. Every panel header's badge resolves to one of these, and clicking any badge re-opens this legend.

- **godot-ready** - exports to `.proscenio` and ships in the Godot importer; edits to its fields reach the runtime scene.
- **blender-only** - an authoring shortcut that lives entirely on the Blender side and never reaches the export.
- **planned** - designed, with a UI placeholder, not yet implemented.
- **out-of-scope** - intentionally not exported (IK constraints, shape keys, anything Godot does not consume).
