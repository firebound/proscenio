@tool
class_name SharedAtlas
extends Node2D

## Documentation-by-example wrapper for the imported [code]shared_atlas.scn[/code].
##
## Three polygon quads share a single atlas PNG, each with its own UV
## bounds. Isolation test for the sliced atlas packer introduced in
## SPEC 005.1.c.2.1. No animation — verifies the polygon + sliced-UV
## path on its own.
##
## See [code].ai/skills/godot-plugin-dev.md[/code] for the full wrapper pattern.
