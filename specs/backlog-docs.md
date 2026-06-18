# Documentation and help-text backlog

The doc/help-text coverage gaps from the QA Companion code-read audit (2026-06-15). The docs and in-panel help describe an older, smaller surface than ships: whole controls (status badges, `?` help buttons, atlas/region readouts, driver In/Out range, bundle-textures, import placement, the entire Photoshop Tags/Validate/Debug panels) are undocumented, and several doc sentences state the opposite of the code (the validation check list, "next to the .blend", "validates against the schema", the driver axis "local rotation", the weight-overlay "ships later"). The remedy is one editorial pass per doc home, not code - so this is collected as area work for a future documentation STUDY, not ~100 micro-issues.

The audit's real code issues were promoted out to [backlog-bugs-found.md](backlog-bugs-found.md), [backlog-godot-importer.md](backlog-godot-importer.md), and [backlog-photoshop.md](backlog-photoshop.md); the dead code to [backlog-code-quality.md](backlog-code-quality.md).

## Scope, by doc home (future doc STUDY)

Each is a reconcile pass: diff the live surface against the page, add the missing controls, fix the stale sentences. The granular per-control list (104 rows, ID / type / control / code anchor) is preserved in git history - recover with `git show 063a7cc:specs/backlog-docs.md` (or the prior `tools/qa-companion/findings.md`) - rather than carried here, since the doc STUDY will re-derive specifics by reading each module against its page anyway.

- **`docs/02-blender-addon/*` (~63 gaps).** Reconcile each panel page against its panel module. Highest-value drift to fix: `09-validation.md`'s check list (understates the implemented checks, mis-states severities), `10-pipeline.md`'s export claims ("next to the .blend", "validates against the schema"). Document the header status-badge + `?` convention once for all panels. Some sprint-queue items already carve specific pieces out of this (`tooltip-copy-revision`, `texture-region-hide-for-mesh`, `automesh-shared-params-surfacing` in [backlog.md](backlog.md)).
- **`docs/04-godot-plugin/index.md` (~10 gaps).** Document the `type:"mesh"` element, the per-element sprite/mesh fields, slot routing + default visibility, the three animation track types, and the import options/preset surface.
- **`docs/03-photoshop-plugin/index.md` (~15 gaps).** Document the Tags / Validate / Debug / Import / Migration sections and the pixels-per-unit / filename-template / forget-folder controls; fix the v1/v2 manifest comment drift.

## In-code help strings to fix

_Now in spec 036, PR 5 (the help-text + tooltip revision sweep) - listed here for the record until it ships._ Stale strings the audit flagged as doc-only (the code behaves correctly, the text lies): the driver-axis PropertyGroup labels (say "local rotation" though the operator forces world space; the duplicated axis enum behind them is unified in the same edit), the `show_provenance_overlay` prop description ("GPU draw handler ships later" - it shipped), and the bind error string ("Skinning panel > Bind mode" - the panel is now Weight Paint).

The broader per-doc-home reconcile above stays here as a future documentation pass; only these in-code strings were pulled into spec 036.
