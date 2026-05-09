@tool
class_name SimplePSD
extends Node2D

## Documentation-by-example wrapper for the imported [code]simple_psd.scn[/code].
##
## Smallest end-to-end Photoshop-importer fixture (SPEC 006 Wave 6.5): one
## [code]polygon[/code] layer + one [code]sprite_frame[/code] group of 4
## frames built from a v1 manifest. Use this fixture when debugging the
## Photoshop manifest -> Blender importer -> writer -> Godot importer
## path without the noise of a full character rig.
##
## See [code].ai/skills/godot-dev.md[/code] for the full wrapper pattern.

@export var default_animation: StringName = ""
@export var autoplay: bool = false

@onready var _player: AnimationPlayer = _find_player()


func _ready() -> void:
	if not autoplay or default_animation == &"":
		return
	if _player == null:
		push_warning("SimplePSD: no AnimationPlayer found in the imported scene")
		return
	if not _player.has_animation(default_animation):
		push_warning("SimplePSD: animation '%s' not in library" % default_animation)
		return
	_player.play(default_animation)


func _find_player() -> AnimationPlayer:
	for child: Node in get_children():
		var found: AnimationPlayer = child.find_child("AnimationPlayer", true, false)
		if found != null:
			return found
	return null
