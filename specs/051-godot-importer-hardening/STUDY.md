# Spec 051: Godot importer hardening

The Godot import builders trust the document shape with no validation, so malformed, duplicate, or unresolved data silently corrupts the rig or aborts the whole import. This spec is one subsystem pass over `apps/godot/addons/proscenio/builders/`: add the missing guards, scope the lookups, and clear the animation-fidelity cleanups that live in the same files.

Scaffolded ahead of its STUDY. The scope below marks what will be done; this is objective robustness work with no open design decisions beyond the one schema-touching item noted under Deferred.

## Scope

- Length-guarded vector parsing for polygon and UV points, shared with the bone path's existing helper.
- Resolve skinned-mesh weights before binding, so an all-missing-bone mesh is not left skeleton-bound with zero weights.
- Warn (or fall back) when a slot default matches no attachment instead of hiding every attachment silently.
- Scope the animation-target node lookup so a track cannot bind to an unrelated same-named subtree.
- Guard against duplicate bone names overwriting the lookup dictionary (defense in depth).
- Honor or drop the per-key `interp` field that is parsed but never applied.
- Set the discrete update mode on the imported `sprite_frame` track instead of relying on NEAREST interpolation alone.
- Add the missing parent assertion to the slot-anchor regression test.

## Sources

Drains [`backlog-godot-importer.md`](../backlog-godot-importer.md) (the six "Import-builder hardening" items), the discrete-update-mode item from [`backlog-bugs-found.md`](../backlog-bugs-found.md) (sprite-frame polish), and the `slot-anchor-test-missing-parent-assertion` test gap from [`backlog-coderabbit-nitpicks.md`](../backlog-coderabbit-nitpicks.md).

## Deferred

The imported animation keeping Godot's default `step = 1/30` (the editor frame grid reads 30 vs the authored 24) needs `scene.render.fps` carried through the `.proscenio` schema, which the format does not store today. That is a schema field change crossing models and codegen and the bundled wheel, so it rides the next schema-touching spec rather than this Godot-only pass. The bezier-handle fidelity gap stays gated (see [`gated.md`](../gated.md), `bezier-curve-preservation`).
