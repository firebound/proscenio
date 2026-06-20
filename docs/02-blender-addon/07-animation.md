# Animation

A read-only summary of every Action in the file. The writer iterates them and emits one Godot `AnimationLibrary` entry per Action, mapping bone-transform and sprite-frame channels to `AnimationPlayer` tracks. The list shows each Action with its frame range; clicking a row assigns it to the rig picked in the [Skeleton](04-skeleton.md) panel (named in the target read-out at the top) so the timeline plays it, and a count of all Actions sits below.

All Actions land in the imported scene's `AnimationPlayer` under the default (empty-name) library, so a Wrapper scene can host a second `AnimationPlayer` for game-side animations without colliding.

Proscenio does not author animation - use Blender's native tools (Action Editor, Dopesheet, drivers). NLA strips are not consumed yet, so bake to a single Action first. Slot indices and driven sprite properties animate on the same timeline.
