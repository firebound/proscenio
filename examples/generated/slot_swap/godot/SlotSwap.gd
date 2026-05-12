@tool
class_name SlotSwap
extends Node2D

## Documentation-by-example wrapper for the imported [code]slot_swap.scn[/code].
##
## Minimal isolation test for the slot system + bone animation combined:
## a pseudo-arm swings while its weapon attachment swaps from axe to
## sword at the apex of the swing. Useful for reproducing slot-related
## regressions in isolation, without the noise of a full doll rig.
##
## See [code].ai/skills/godot-dev.md[/code] for the full wrapper pattern.


func _ready() -> void:
	pass
