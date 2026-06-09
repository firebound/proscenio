# Animation

A read-only summary of every Action in the file. The writer iterates them and emits one Godot `AnimationPlayer` entry per Action, mapping bone-transform and sprite-frame channels to tracks.

Proscenio does not author animation - use Blender's native tools (Action Editor, Dopesheet, drivers). NLA strips are not consumed yet, so bake to a single Action first. Slot indices and driven sprite properties animate on the same timeline.
