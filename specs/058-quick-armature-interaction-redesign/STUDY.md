# Spec 058: Quick Armature interaction redesign

The Quick Armature modal binds Shift, Alt, Ctrl, X, and Z, conflating chain modifiers with standalone tools (undo, axis lock), and the modifier taps are unintuitive. Viewport pick-parent (hit-testing a bone tip to reparent mid-sketch) has confirmed demand but no home in the saturated scheme. This spec redesigns the interaction vocabulary first, then fits pick-parent into the new scheme.

This spec is STUDY-first and returned from spec 050 for exactly this reason: the redesign needs design time before any code. The locked Quick Armature UX promises (GPU preview line plus real bone on click, tail tracks mouse, prefix from preference plus F3, Front-Ortho auto-snap restoring the prior view on exit) must survive the redesign.

## Scope

- Replace the saturated modifier-tap chord scheme with a vocabulary that separates chain modifiers from standalone tools.
- Add viewport pick-parent (hit-test a bone tip to reparent mid-sketch) as a first-class part of the new scheme. This absorbs the former `qa-pick-parent-viewport` item.
- Keep every locked Quick Armature UX promise intact.

## Open questions (resolve before coding)

- The replacement vocabulary: a mode-layer scheme (a key switches modal mode, the status bar shows that mode's chords, pick-parent is its own mode) versus overloading a modifier (Alt+click direct parent-pick) versus a standalone reparent operator outside the modal. The mode-layer scheme was the leaning recommendation when this returned from spec 050, but the call is open.
- Where pick-parent sits in the chosen scheme, and how it resolves the hit-test (nearest bone tip, fallback behavior).

## Sources

Drains the `qa-quickarm-interaction-revision` item in [`backlog.md`](../backlog.md) (which absorbed `qa-pick-parent-viewport`). The locked modal-UX calls are in [`decisions.md`](../decisions.md) under Quick Armature UX. Convenience extensions (`qa-chain-naming-suffixes`, `qa-mirror-suffix`) stay in [`gated.md`](../gated.md).
