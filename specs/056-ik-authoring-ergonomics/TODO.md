# Spec 056: IK authoring ergonomics - TODO

The export-leak fix is objective and lands first. The rest finalizes once the naming and property-depth calls are made.

## PR 1 - stop the control bone leaking to export (objective, no decision)

- [ ] Filter non-deform bones in `build_skeleton` so the `.IK` control bone is not emitted as a `Bone2D`. `skeleton.py:92` iterates `iter_bones` without filtering `use_deform=False`. Apply the rule to both the skeleton and the animation writers.
- [ ] Headless test: a rig with an IK control bone exports only the deform bones; the control bone is absent from the skeleton and the tracks.

## PR 2 - make IK chains legible (pending naming call)

- [ ] Rename the Toggle IK operator per the locked naming call (create / remove, or real influence toggle).
- [ ] Add a Skeleton-panel marker on a bone carrying a `Proscenio IK` constraint and on its control bone.
- [ ] Add an "IK chains" section listing active chains with tip, chain length, and target.

## PR 3 - expose constraint properties (pending depth call)

- [ ] When a constrained bone or its control bone is active, expose chain length, influence, and pole target in the panel.
- [ ] Make influence keyframable from the panel (the seed of an IK/FK blend).

## PR 4 - Rigify-style affordances

- [ ] Create control bones in a "Proscenio Controls" bone collection with a theme color.
- [ ] Assign a custom shape to control bones so they read as controls, not deform bones.
