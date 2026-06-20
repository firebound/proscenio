# CodeRabbit nitpick backlog (closed-PR sweep)

Drained on 2026-06-20: the closed-PR review sweep was routed across the focused specs of the backlog-drain wave (see [`_index.md`](_index.md)). This file is kept as a thin pointer so existing references resolve; recover the original entries from this file's git history.

Routed to:

- Blender correctness and robustness bugs (Constrained Delaunay holes, driver-shortcut boolean, atlas-apply error handling, sidecar float guard, sprites zip-strict, selection ReferenceError) -> spec 052 blender-operator-robustness.
- The slot-anchor parent-assertion test gap -> spec 051 godot-importer-hardening.
- The Photoshop cosmetic nitpicks (disabled ternary, spurious select key, stray JSX) -> spec 053 photoshop-data-integrity.
- The remaining test gaps, DRY extractions, redundant/cosmetic code, doc typos, the frozen-dataclass tuple fix, and the CI permissions block -> spec 054 code-review-cleanup.
- The bare `use_nodes` atlas reads -> spec 062 blender-6-compatibility.
- The non-recursive `sonar.exclusions` glob -> spec 063 sonarcloud-analysis-pipeline.
