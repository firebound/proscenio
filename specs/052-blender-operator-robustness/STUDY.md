# Spec 052: Blender operator robustness

A sweep over `apps/blender` operators and the export path where each touched operator currently does the wrong thing silently, or aborts with a raw traceback, instead of guarding the failure and reporting it. Every item is a cited correctness or feedback fix; none changes a feature's intent. The unifying contract: an operator either produces a correct result or reports clearly, and never registers a no-op as success.

Scaffolded ahead of its STUDY. The scope below marks what will be done; all items are objective, so the design cost is low. The work splits cleanly into two PRs (export and atlas correctness, then operator feedback and guards).

## Scope

- Pixels-per-unit: the first export honors the panel field, and import does not silently overwrite it.
- Apply Packed Atlas does not count a no-UV sprite as rewritten.
- Bake Current Pose keys only the channel the bone's rotation mode uses.
- Quick Armature reads its lock-to-front-ortho option at invoke.
- Copy Weights to Selected reports a zero-coverage transfer as not-applied, not FINISHED.
- Bake IK to Keyframes restores the selection it mutates.
- A cancelled action-row click is surfaced, not suppressed at log level "errors".
- Constrained Delaunay holes are filtered before the output type is set.
- The driver shortcut button disables on a zero-bone armature.
- Atlas apply, sidecar parsing, and the sprites writer fail loud on malformed input instead of leaking a raw exception or truncating topology.
- The selection action guards against a freed armature reference.

## Sources

Drains the "code-read audit" cluster in [`backlog-bugs-found.md`](../backlog-bugs-found.md) (export/atlas, operator robustness, the two Photoshop-import side effects) and the Blender correctness and robustness bugs in [`backlog-coderabbit-nitpicks.md`](../backlog-coderabbit-nitpicks.md) (`cdt-output-type-unfiltered-holes`, `driver-shortcut-bool-on-collection`, `atlas-apply-manifest-no-error-handling`, `sidecar-from-json-unwrapped-float`, `sprites-zip-strict-false`, `selection-action-no-referenceerror-guard`).
