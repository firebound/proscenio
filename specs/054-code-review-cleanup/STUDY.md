# Spec 054: Code review cleanup

The cheap residue left after the CodeRabbit closed-PR sweep is routed into the themed specs: this spec collects what does not change product behavior. Test gaps that pass while validating nothing, duplicated bootstrap blocks, dead code, redundant expressions, doc typos, and two infra hardening lines. All independent, all low risk, all mechanical.

Scaffolded ahead of its STUDY. This is a sweep, not a design: the scope below is the checklist. It can land as several small commits rather than waiting on each other.

## Scope

- Test gaps: make the weak tests able to catch the regression they appear to cover, and add the missing branches.
- DRY: extract the duplicated fixture image-rewrite helper and the duplicated skinning test `sys.path` bootstrap.
- Dead code: remove the unreachable weight-paint brush mirror, the unreachable fallback label, and the dead atlas image-cache lookup.
- Redundant code: drop the redundant `list()` calls, the dead `bool()` wrapper, the double-negative boolean, the extra blank line in emitted TypeScript, and the untyped test ClassVar.
- Docs and comments: fix the stale docstring, the two stale run-path docstrings, the Python-version note, the README typo, and the missing help-topics sentence.
- Infra: add the CI `permissions` block, and codify the no-hard-wrap prose rule.
- Type health: make the frozen validator dataclass fields tuples so the immutability contract holds.

## Sources

Drains the test-gap, DRY, redundant/cosmetic, docs/comments, and infra sections of [`backlog-coderabbit-nitpicks.md`](../backlog-coderabbit-nitpicks.md) (minus the items routed to spec 052, 053, 062, 063), plus the dead-code entries, the `validator-mutable-list-on-frozen-dataclass` item, and the `docs-no-hard-wrap-rule` quick win from [`backlog-code-quality.md`](../backlog-code-quality.md).
