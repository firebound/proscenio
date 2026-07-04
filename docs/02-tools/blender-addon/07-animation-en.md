# Animation

A read-only summary of every Action in the file - the Actions the writer emits as Godot `AnimationPlayer` tracks at export. Proscenio does not author animation; you key poses with Blender's native tools (Action Editor, Dopesheet, drivers) and this panel is the window onto what export will carry. It sits seventh in the sidebar and is collapsed by default.

The panel opens with the export target read-out (`Exports: <name>`), the same line the [Mesh Generation](05-mesh-generation.md) and [Weight Paint](06-weight-paint.md) panels show, because clicking a row assigns the Action to that armature. Below it sits the Action list, then a total count. With no Actions in the file the list is replaced by `no actions to export`.

**The action list.** Each row names one Action behind an `ACTION` icon and shows its frame range as `[start-end]`. The list is single-select: clicking a row assigns that Action to the rig picked in the [Skeleton](04-skeleton.md) panel, so the timeline scrubs and plays it. The Skeleton picker is the single source of truth here - if no armature is picked, the click reports that and assigns nothing rather than guessing a rig. Source order is kept, and a count of all Actions sits below the list.

**What export emits.** At export the writer iterates every Action and emits one animation entry per Action. Three kinds of channel merge into that one entry, keyed by the Action name:

- **Bone transforms** - position, rotation, and scale fcurves on the rig's deform bones become `bone_transform` tracks. A channel with no motion off the rest pose is dropped so the Bone2D rest survives import; a control bone's fcurves (an IK or pole target) are filtered out and never reach the document.
- **Slot indices** - keyframes on a slot's index become a `slot_attachment` track on the slot, with constant interpolation so the swap is a hard cut.
- **Driven sprite frames** - a sprite `frame` driven from a pose bone (the [Drive from Bone](02-element.md#drive-from-bone) shortcut) is baked by stepping the Action and reading the posed bone, emitting a `sprite_frame` track with constant-interpolation keys at each change.

Because all three are keyed by Action name, slot indices and driven sprite properties animate on the same timeline as the bones.

**Where the animations land in Godot.** Every Action lands in the imported scene's `AnimationPlayer` under the default (empty-name) library, so a Wrapper scene can host a second `AnimationPlayer` for game-side animations without a name collision.

**Caveats.** NLA strips are not consumed yet, so bake an NLA stack down to a single Action before relying on it at export. The panel reads Actions straight from the file, so an Action with no keyed deform-bone, slot, or driven-frame channel contributes no tracks even though it still appears in the list.
