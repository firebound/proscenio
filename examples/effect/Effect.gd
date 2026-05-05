@tool
class_name Effect
extends Node2D

## Wrapper for the imported [code]effect.scn[/code] (a sprite_frame fixture).
##
## Same SPEC 001 wrapper-scene pattern as [code]Dummy.gd[/code]: scripts and
## extra nodes live on this wrapper and survive every reimport. The
## difference is the imported scene contains a [Sprite2D] (frame-indexed
## spritesheet) instead of a [Polygon2D] (vertex mesh).

## Animation to play on [code]_ready()[/code]. The Proscenio importer puts the
## DCC-authored animations under the default ("") library.
@export var default_animation: StringName = "play"

## Whether to auto-play on ready. Disable when the game flow drives playback.
@export var autoplay: bool = true

@onready var _player: AnimationPlayer = _find_player()


func _ready() -> void:
	if not autoplay:
		return
	if _player == null:
		push_warning("Effect: no AnimationPlayer found in the imported scene")
		return
	if not _player.has_animation(default_animation):
		push_warning("Effect: animation '%s' not in library" % default_animation)
		return
	_player.play(default_animation)


func _find_player() -> AnimationPlayer:
	for child: Node in get_children():
		var found: AnimationPlayer = child.find_child("AnimationPlayer", true, false)
		if found != null:
			return found
	return null
