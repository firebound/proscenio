@tool
extends RefCounted

# Shared sanitization helper for Godot Node names (SPEC 001 ergonomics).
#
# Godot 4's ``Node.name`` setter normalises a handful of reserved
# characters (``.``, ``/``, ``:``, ``@``) into ``_`` automatically -- a
# bone authored as ``spine.001`` in Blender becomes ``spine_001`` once
# attached to a Skeleton2D. JSON keeps the original string, so any
# downstream lookup that hands a JSON-shaped name to ``find_child`` or
# a dict whose keys are ``Node.name`` values misses every dotted entry.
#
# All builders -- skeleton, polygon, sprite_frame, slot -- funnel
# names through ``sanitize`` before lookup so the JSON-shaped string
# (``upper_arm.L``) and the Godot-shaped node name (``upper_arm_L``)
# converge on the same key.


static func sanitize(name: String) -> String:
	return name.replace(".", "_").replace("/", "_").replace(":", "_").replace("@", "_")
