@tool
extends RefCounted

# Length-guarded reads of a packed 2D point.
#
# Decoded `.proscenio` points are `PackedFloat32Array`; a malformed source can
# hand a builder a point shorter than two components. Reading `arr[0]`/`arr[1]`
# off such an array raises an out-of-bounds error and aborts the whole import,
# so every Vector2-from-packed read funnels through here and falls back instead.


static func to_vec2(arr: PackedFloat32Array) -> Vector2:
	return to_vec2_or(arr, Vector2.ZERO)


static func to_vec2_or(arr: PackedFloat32Array, fallback: Vector2) -> Vector2:
	if arr.size() < 2:
		return fallback
	return Vector2(arr[0], arr[1])
