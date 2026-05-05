@tool
class_name Dummy
extends Node2D

## Documentation-by-example wrapper for the imported [code]dummy.scn[/code].
##
## The Proscenio importer regenerates [code]dummy.scn[/code] from
## [code]dummy.proscenio[/code] on every reimport (SPEC 001 Option A).
## Scripts and extra nodes attached directly to the generated scene are
## clobbered. Wrap the imported scene in a separate [code].tscn[/code] —
## like this one — and customize there. The wrapper is yours; reimport
## never touches it.
##
## See [code].ai/skills/godot-plugin-dev.md[/code] for the full pattern.

## Animation library name to play on [code]_ready()[/code]. The Proscenio
## importer puts DCC-authored animations under the default ("") library;
## leave this empty unless you add a second library on the wrapper itself.
@export var default_animation: StringName = "idle"

## Whether the default animation auto-plays on ready. Disable when the
## game flow drives playback (e.g. state machines, AnimationTree).
@export var autoplay: bool = true

@onready var _player: AnimationPlayer = _find_player()


func _ready() -> void:
	if not autoplay:
		return
	if _player == null:
		push_warning("Dummy: no AnimationPlayer found in the imported scene")
		return
	if not _player.has_animation(default_animation):
		push_warning("Dummy: animation '%s' not in library" % default_animation)
		return
	_player.play(default_animation)


func _find_player() -> AnimationPlayer:
	# Walk the instanced child looking for the AnimationPlayer the Proscenio
	# importer ships under the character root. Surface a helpful error if
	# the wrapper has been re-parented in unexpected ways.
	for child: Node in get_children():
		var found: AnimationPlayer = child.find_child("AnimationPlayer", true, false)
		if found != null:
			return found
	return null
