# Validation

`Validate` runs the full pre-export pass and lists what it finds; the same pass runs automatically before every export, and any `error` row blocks it. Sits between Import and Export in the Pipeline panel so the run order reads top to bottom. Until you click `Validate` the panel shows `run Validate to see issues`; a clean scene shows `no issues - ready to export`.

This is structural and semantic validation of the live scene - it never runs JSON Schema validation. The schema is checked in CI and the test runner, not in the Blender session (see [Pipeline](10-pipeline.md#export) for what export does instead).

Each finding renders as one row with an `error` or `info` icon. A row that names an offending object is a button - click it to select that object in the viewport; findings with no object (the no-armature error) render as a plain label.

## Errors block the export

- The scene has no Armature (export requires one; this is reported alone, before any other check).
- An element carries vertex groups but none resolve to armature bones - the writer would raise at export.
- A sprite element has `hframes` or `vframes` below 1.
- An element has an unknown element type (neither `mesh` nor `sprite`).
- An IK chain is driven by an animated target but its chain bones carry no keyframes - run `Bake IK to Keyframes` first (the exporter reads raw fcurves and would write flat bones).
- Two slots share a name.
- A slot has no mesh children.
- A slot's default attachment names a mesh that is not a child of the slot.

## Warnings inform but still export

- An element has no parent bone and no vertex groups matching armature bones - the writer falls back to an empty bone field.
- A bone's rest direction tilts out of the world XZ plane - the exporter projects bone angles onto XZ and would misread it.
- A bone drives a sprite's rotation but is not in XYZ Euler mode - the driver reads XYZ, so the animation will not track. Run `Active to Euler` in the [Skeleton](04-skeleton.md#active-armature) panel.
- A mesh element is not flat (it has thickness on every axis), so the flatten-to-plane step would lose geometry.
- A sprite-frame element's quad UVs do not span the full 0-1 sheet, so the `hframes` / `vframes` grid would be garbled in Godot.
- An atlas image referenced by a material is missing on disk - Godot will warn at import. This is a warning, not a blocker.
- A sprite element's mesh is no longer a single quad (a mesh tool likely ran on it).
- A mesh element has no polygons.
- A slot attachment follows a different bone than its slot.
- A slot child carries bone-transform keyframes - a slot animates visibility only.

The Element and Active Slot subpanels surface a cheap subset of these checks inline on every redraw (the active object, the active slot), so most problems show before you click `Validate`.
