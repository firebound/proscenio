# Spec 060: Documentation coverage pass - TODO

Three editorial passes, one per doc home, landing directly on main. Each pass diffs the live surface against the page, adds the missing controls, and fixes the stale sentences.

## Pass 1 - Blender addon pages

- [ ] Reconcile each `docs/02-blender-addon/*` panel page against its panel module: add the undocumented controls (status badges, `?` help buttons, atlas and region readouts, driver In/Out range, bundle-textures, import placement).
- [ ] Fix `09-validation.md`: correct the check list it understates and the severities it mis-states.
- [ ] Fix `10-pipeline.md`: correct the "next to the .blend" and "validates against the schema" export claims.
- [ ] Document the header status-badge and `?` help convention once for all panels.
- [ ] Fix the remaining lying sentences flagged by the audit (driver axis "local rotation", weight-overlay "ships later").

## Pass 2 - Godot plugin index

- [ ] Document the `type:"mesh"` element and the per-element sprite and mesh fields.
- [ ] Document slot routing and default visibility.
- [ ] Document the three animation track types.
- [ ] Document the import options and preset surface.

## Pass 3 - Photoshop plugin index

- [ ] Document the Tags / Validate / Debug / Import / Migration sections.
- [ ] Document the pixels-per-unit, filename-template, and forget-folder controls.
- [ ] Fix the v1/v2 manifest comment drift.
