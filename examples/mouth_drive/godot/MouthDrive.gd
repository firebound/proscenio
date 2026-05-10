@tool
class_name MouthDrive
extends Node2D

## Documentation-by-example wrapper for the imported [code]mouth_drive.scn[/code].
##
## Minimal isolation test for [b]Drive from Bone[/b]: one sprite_frame mouth
## mesh + one bone ([code]mouth_drive[/code]) on the [code]mouth_rig[/code]
## armature. The fixture ships without a driver wired -- the user adds one
## via the Blender panel operator and the round-trip should preserve the
## driver as a bone_transform track on the AnimationPlayer.
##
## Useful for reproducing driver / bone-track regressions in isolation,
## without the noise of a full doll rig.
##
## See [code].ai/skills/godot-dev.md[/code] for the full wrapper pattern.


func _ready() -> void:
	pass
