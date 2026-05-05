@tool
extends RefCounted


static func attach_sprites(skeleton: Skeleton2D, sprites_data: Array, atlas: Texture2D) -> void:
	for sprite_data in sprites_data:
		# Discriminator dispatch: this builder only handles polygon sprites.
		# Default to "polygon" when `type` is absent (v1 backwards-compat).
		var sprite_type: String = sprite_data.get("type", "polygon")
		if sprite_type != "polygon":
			continue

		var poly := Polygon2D.new()
		poly.name = sprite_data.get("name", "sprite")

		var polygon_pts: Array = sprite_data.get("polygon", [])
		var pts := PackedVector2Array()
		for p in polygon_pts:
			pts.append(Vector2(p[0], p[1]))
		poly.polygon = pts

		var uv_pts: Array = sprite_data.get("uv", [])
		var uvs := PackedVector2Array()
		# .proscenio stores UVs normalized [0, 1] — engine-agnostic. Godot's
		# Polygon2D expects UVs in texture pixel space, so multiply by atlas
		# size at import time. Sprites without an atlas keep raw UVs.
		var uv_scale := Vector2.ONE
		if atlas != null:
			uv_scale = atlas.get_size()
		for u in uv_pts:
			uvs.append(Vector2(u[0] * uv_scale.x, u[1] * uv_scale.y))
		poly.uv = uvs

		if atlas != null:
			poly.texture = atlas

		if sprite_data.has("weights"):
			push_warning(
				(
					(
						"Proscenio: sprite '%s' has weights — full skinning lands in Phase 2 "
						+ "(SPEC 003); attaching rigidly to bone for now."
					)
					% poly.name
				)
			)

		var bone_name: String = sprite_data.get("bone", "")
		var parent: Node = skeleton
		if bone_name != "":
			var found := skeleton.find_child(bone_name, true, false)
			if found != null:
				parent = found
		parent.add_child(poly)
