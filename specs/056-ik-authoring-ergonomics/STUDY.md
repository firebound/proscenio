# Spec 056: IK authoring ergonomics

The IK target wiring and bake gate shipped, but the authoring surface around them is thin: the operator name promises a behavior it does not have, nothing in the addon shows an IK chain exists, the constraint properties live only in Blender's native menus, the control bone leaks into the export, and none of the Rigify-style visual affordances (named bone collections, colors, custom shapes) are used. This spec makes IK chains legible and editable from inside Proscenio.

This spec is STUDY-first for the feature-shaped items; two calls are already locked from the manual session (pole bone as the default scaffolding, and `use_deform=False` as the non-export convention). The control-bone export leak is objective and can land first regardless of the design.

## Scope

- Rename "Toggle IK" to describe its create / remove behavior, or evolve it into a real influence toggle.
- Show that an IK chain exists: a Skeleton-panel marker on the constrained bone and the control bone, and an "IK chains" section listing active chains (tip, length, target).
- Expose the constraint properties (chain length, influence, pole target) in the panel, with influence keyframable as the seed of an IK/FK blend.
- Stop the `.IK` control bone leaking into the Godot export by filtering non-deform bones in the writer.
- Apply Rigify-style affordances: a "Proscenio Controls" bone collection with a theme color and a custom shape for control bones.

## Open questions (resolve before coding)

- Naming: "Add IK Chain" / "Remove IK Chain" conditional on the active bone's state, versus evolving to a real influence on/off toggle. Which is the lasting model?
- Property exposure depth: chain length and pole target are static; influence is animatable. How much of the constraint surface belongs in the panel before it just mirrors Blender's?
- Export filter rule: adopt `use_deform=False` means "not exported" as the general convention (cleanest, opens a future controls layer), or filter only the `.IK` suffix as a narrower fix.

## Sources

Drains [`backlog-ik-ergonomics.md`](../backlog-ik-ergonomics.md) (all five entries). The locked pole-bone-default and DOF-lock calls from the 2026-06-11 session are recorded inline there. Related gated capabilities (`ik-chain-helper`, `ik-round-trip`) stay in [`gated.md`](../gated.md) and are out of scope.
