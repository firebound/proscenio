@tool
class_name SlotMultiAnim
extends Node2D

## Documentation-by-example wrapper for the imported [code]slot_multi_anim.scn[/code].
##
## Per-animation slot swap isolation test (spec 079 core): one slot Empty
## carries a DIFFERENT attachment-visibility timeline per animation -
## [code]idle[/code] shows no weapon ("(none)"), [code]attack[/code] shows the
## club while the arm swings. Useful for reproducing per-animation slot
## regressions in isolation.
##
## See [code].ai/skills/godot-dev.md[/code] for the full wrapper pattern.

@onready var animation_player: AnimationPlayer = $SlotMultiAnimCharacter/AnimationPlayer


func _ready() -> void:
	if Engine.is_editor_hint():
		return
	animation_player.play("attack")
