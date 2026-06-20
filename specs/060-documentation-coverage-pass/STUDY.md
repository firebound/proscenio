# Spec 060: Documentation coverage pass

The docs and in-panel help describe an older, smaller surface than ships. Whole controls (status badges, the `?` help buttons, atlas and region readouts, driver In/Out range, bundle-textures, import placement, the entire Photoshop Tags / Validate / Debug panels) are undocumented, and several doc sentences state the opposite of the code. The remedy is one editorial pass per doc home: diff the live surface against the page, add the missing controls, fix the stale sentences.

Scaffolded ahead of its STUDY. This is editorial work, not code; per the repository convention documentation lands directly on main rather than through a branch and PR, but it is organized as a spec here so the scope is tracked like the rest of the wave. The detailed per-control list is re-derived by reading each module against its page, so it is not re-pasted here.

## Scope

- `docs/02-blender-addon/*` (about 63 gaps): reconcile each panel page against its panel module. Highest-value drift: the `09-validation.md` check list (understates the implemented checks, mis-states severities) and `10-pipeline.md`'s export claims ("next to the .blend", "validates against the schema"). Document the header status-badge and `?` convention once for all panels.
- `docs/04-godot-plugin/index.md` (about 10 gaps): document the `type:"mesh"` element, the per-element sprite and mesh fields, slot routing and default visibility, the three animation track types, and the import options and preset surface.
- `docs/03-photoshop-plugin/index.md` (about 15 gaps): document the Tags / Validate / Debug / Import / Migration sections and the pixels-per-unit / filename-template / forget-folder controls; fix the v1/v2 manifest comment drift.

## Sources

Drains [`backlog-docs.md`](../backlog-docs.md) (all three doc homes). The granular 104-row list is recoverable from git history (`git show 063a7cc:specs/backlog-docs.md`). The same audit's code issues already left for specs 051 to 054.
