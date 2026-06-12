@tool
class_name MixedFeature
extends Node2D

## Documentation-by-example wrapper for the imported [code]mixed_feature.scn[/code].
##
## The feature-stack fixture - the one document that exercises every
## Blender-to-Godot feature at once: a skinned [code]body[/code] polygon,
## a sprite_frame [code]mouth[/code] driven from the [code]jaw[/code] bone,
## a slot ([code]face.slot[/code]) holding one mesh and one sprite
## attachment, all packed into a single [code]atlas.png[/code], plus the
## [code]mixed_anim[/code] action keying the jaw (which the driver projects
## onto the mouth frame).
##
## Use this fixture when a change could touch more than one builder at once
## ([code]mesh_builder.gd[/code] / [code]sprite_builder.gd[/code] /
## [code]slot_builder.gd[/code] / [code]animation_builder.gd[/code]); the
## single-feature fixtures cannot catch interactions between them.

@export var default_animation: StringName = "mixed_anim"
@export var autoplay: bool = true

@onready var _player: AnimationPlayer = _find_player()


func _ready() -> void:
	if not autoplay:
		return
	if _player == null:
		push_warning("MixedFeature: no AnimationPlayer found in the imported scene")
		return
	if not _player.has_animation(default_animation):
		push_warning("MixedFeature: animation '%s' not in library" % default_animation)
		return
	_player.play(default_animation)


func _find_player() -> AnimationPlayer:
	for child: Node in get_children():
		var found: AnimationPlayer = child.find_child("AnimationPlayer", true, false)
		if found != null:
			return found
	return null
