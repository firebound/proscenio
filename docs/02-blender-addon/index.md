# Blender addon reference

Per-panel reference for the Proscenio sidebar. Open it in Blender at **3D Viewport > Sidebar (`N`) > Proscenio**.

For the end-to-end workflow, start with the [Blender walkthrough](../00-guides/00-basic/02-blender.md); this section documents each panel and subpanel on its own.

:::note Placeholder pages
These reference pages are a first cut. Each panel and subpanel carries a brief, specific description that mirrors the in-addon `?` help; they expand over time.
:::

## The sidebar

Every panel renders on any selection and warns (rather than hiding) when it needs a different one. Each header carries a status badge plus a `?` that opens the matching help inline.

- [Outliner](01-outliner.md) - sprite-centric flat list of slots, meshes, and armatures.
- [Element](02-element.md) - per-element settings (Polygon2D vs Sprite2D, texture region, drive-from-bone).
- [Slots](03-slots.md) - the project slot list and per-slot attachment detail.
- [Skeleton](04-skeleton.md) - the armature picker, bone list, pose helpers, and Quick Armature.
- [Mesh Generation](05-mesh-generation.md) - trace a sprite alpha into a deformable mesh.
- [Weight Paint](06-weight-paint.md) - bind and refine bone weights (mesh elements only).
- [Animation](07-animation.md) - read-only summary of the actions the writer exports.
- [Atlas](08-atlas.md) - pack source images into a shared atlas.
- [Validation](09-validation.md) - issues that would block an export.
- [Pipeline](10-pipeline.md) - import a Photoshop manifest and export the `.proscenio`.
- [Helpers](11-helpers.md) - viewport authoring aids that sit outside the export.

## Status badges

Each header shows where the feature lands in the pipeline:

- **godot-ready** - exports to `.proscenio` and ships in the Godot importer.
- **blender-only** - an authoring shortcut that never reaches the export.
- **planned** - designed, with a UI placeholder, not yet implemented.
- **out-of-scope** - intentionally not exported.
