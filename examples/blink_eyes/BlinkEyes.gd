@tool
class_name BlinkEyes
extends Node2D

## Documentation-by-example wrapper for the imported [code]blink_eyes.scn[/code].
##
## Minimal isolation test for the [code]sprite_frame[/code] track type: one
## mesh, one 4-frame spritesheet, one [code]blink[/code] action that cycles
## the frame index. Use this fixture when debugging the writer →
## [code].proscenio[/code] → importer path for sprite_frame specifically.
##
## See [code].ai/skills/godot-plugin-dev.md[/code] for the full wrapper pattern.

@export var default_animation: StringName = "blink"
@export var autoplay: bool = true

@onready var _player: AnimationPlayer = _find_player()


func _ready() -> void:
	if not autoplay:
		return
	if _player == null:
		push_warning("BlinkEyes: no AnimationPlayer found in the imported scene")
		return
	if not _player.has_animation(default_animation):
		push_warning("BlinkEyes: animation '%s' not in library" % default_animation)
		return
	_player.play(default_animation)


func _find_player() -> AnimationPlayer:
	for child: Node in get_children():
		var found: AnimationPlayer = child.find_child("AnimationPlayer", true, false)
		if found != null:
			return found
	return null
