@tool
extends RefCounted

# Shared sanitization helper for Godot Node names.
#
# Godot 4's ``Node.name`` setter normalises ``.``, ``/``, ``:``, ``@`` into
# ``_`` on assignment, while JSON keeps the original string. Builders funnel
# names through ``sanitize`` before lookup so a JSON-shaped name
# (``upper_arm.L``) and the Godot-shaped node name (``upper_arm_L``) converge
# on the same key.


static func sanitize(name: String) -> String:
	return name.replace(".", "_").replace("/", "_").replace(":", "_").replace("@", "_")
