@tool
class_name SlotCycle
extends Node2D

## Documentation-by-example wrapper for the imported [code]slot_cycle.scn[/code].
##
## Minimal slot-system isolation test (SPEC 004 Wave 4.3): one slot, three
## attachment polygons, the [code]cycle[/code] action keyframing
## visibility per attachment. Runtime view: each frame of the action
## one [code]Polygon2D[/code] becomes [code]visible=true[/code], the
## others go [code]visible=false[/code]; the slot Node2D parent stays
## fixed under the skeleton.
##
## Use this fixture when debugging the slot_attachment track expansion
## ([code]animation_builder.gd[/code]) or the slot routing in the
## sprite builders ([code]polygon_builder.gd[/code] /
## [code]sprite_frame_builder.gd[/code]).

@export var default_animation: StringName = "cycle"
@export var autoplay: bool = true

@onready var _player: AnimationPlayer = _find_player()


func _ready() -> void:
	if not autoplay:
		return
	if _player == null:
		push_warning("SlotCycle: no AnimationPlayer found in the imported scene")
		return
	if not _player.has_animation(default_animation):
		push_warning("SlotCycle: animation '%s' not in library" % default_animation)
		return
	_player.play(default_animation)


func _find_player() -> AnimationPlayer:
	for child: Node in get_children():
		var found: AnimationPlayer = child.find_child("AnimationPlayer", true, false)
		if found != null:
			return found
	return null
