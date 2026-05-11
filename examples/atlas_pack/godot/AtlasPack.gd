@tool
class_name AtlasPack
extends Node2D

## Documentation-by-example wrapper for the imported [code]atlas_pack.scn[/code].
##
## Workbench for the atlas packer (SPEC 005.1.c). Nine flat-colored
## quads each with its own texture; running Pack Atlas + Apply in
## Blender rewrites them to share a single packed atlas. The wrapper
## lets you attach scripts / collisions / extra nodes here without
## losing them on reimport.
##
## See [code].ai/skills/godot-dev.md[/code] for the full wrapper pattern.


func _ready() -> void:
	pass
