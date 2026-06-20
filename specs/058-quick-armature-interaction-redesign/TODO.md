# Spec 058: Quick Armature interaction redesign - TODO

Pending the interaction-vocabulary call in the STUDY. This is the heaviest design of the open features; the rows finalize once the scheme is locked.

## After the vocabulary is locked

- [ ] Implement the chosen interaction scheme in the Quick Armature modal, freeing the conflated modifier taps. `operators/armature/quick_armature.py`, `core/armature/quick_armature_math.py`.
- [ ] Update the rendered chord cheatsheet to the new scheme. `operators/armature/_status_bar.py`.
- [ ] Add viewport pick-parent: hit-test a bone tip to reparent mid-sketch, with a defined fallback when no tip is hit.
- [ ] Verify the locked promises still hold: GPU preview line plus real bone on click, tail tracks mouse, prefix from preference plus F3, Front-Ortho auto-snap restoring the prior view on exit.
- [ ] Headless coverage for the new mode transitions and the pick-parent resolution, extending the existing Quick Armature modal test.
