@tool
extends SceneTree

# Headless coverage for Sprite2D region handling in sprite_builder.gd.
#
# Split out of test_importer.gd to keep that file under the line cap. Two
# behaviors that the effect-fixture smoke test cannot reach:
#   1. with a texture, the normalized [0,1] texture_region scales into the
#      texture-pixel region_rect (a confirming test of the load-bearing path);
#   2. without a texture, the region is left disabled so the sprite ships as a
#      plain Sprite2D instead of an enabled empty region that draws nothing.
#
# Run from the apps/godot project root:
#
#     godot --headless --script res://tests/test_sprite_region.gd

const SpriteBuilder := preload("res://addons/proscenio/builders/sprite_builder.gd")
const ProscenioDocumentRes := preload(
	"res://addons/proscenio/schema_bindings/proscenio_document.gd"
)

# A known, non-square size so a wrong axis or a swapped width/height shows up.
const TEX_W := 64
const TEX_H := 32

var _failures: Array[String] = []
var _passes: int = 0  # gdlint: ignore=unused-private-class-variable


func _initialize() -> void:
	_run_with_texture_check()
	_run_without_texture_check()
	_finish()


# A sprite element carrying a normalized sub-rect, routed through from_dict so
# the builder receives the same typed Array[ProscenioElement] the importer does.
func _sprite_document() -> ProscenioDocumentRes:
	return (
		ProscenioDocumentRes
		. from_dict(
			{
				"name": "region_probe",
				"elements":
				[
					{
						"type": "sprite",
						"name": "glint",
						"hframes": 1,
						"vframes": 1,
						# x=0.25, y=0.5, w=0.5, h=0.5 of the texture.
						"texture_region": [0.25, 0.5, 0.5, 0.5],
					}
				],
			}
		)
	)


func _known_texture() -> Texture2D:
	var image := Image.create(TEX_W, TEX_H, false, Image.FORMAT_RGBA8)
	return ImageTexture.create_from_image(image)


func _build_sprite(atlas: Texture2D) -> Sprite2D:
	var document := _sprite_document()
	var skeleton := Skeleton2D.new()
	SpriteBuilder.attach_elements(skeleton, document.elements, atlas, {})
	for child: Node in skeleton.get_children():
		if child is Sprite2D:
			return child as Sprite2D
	return null


func _run_with_texture_check() -> void:
	var sprite := _build_sprite(_known_texture())
	if sprite == null:
		_fail("with-texture: no Sprite2D was attached")
		return
	_assert_true(sprite.region_enabled, "with-texture: region enabled")
	_assert_true(sprite.region_filter_clip_enabled, "with-texture: region clip enabled")
	# Normalized [0.25, 0.5, 0.5, 0.5] * (64, 32) = (16, 16, 32, 16).
	_assert_eq(
		sprite.region_rect,
		Rect2(0.25 * TEX_W, 0.5 * TEX_H, 0.5 * TEX_W, 0.5 * TEX_H),
		"with-texture: region_rect scaled to texture pixels",
	)


func _run_without_texture_check() -> void:
	var sprite := _build_sprite(null)
	if sprite == null:
		_fail("without-texture: no Sprite2D was attached")
		return
	# No texture resolves, so the pixel rect cannot be computed; the region must
	# stay disabled rather than ship enabled with a zero-area rect (invisible).
	_assert_eq(sprite.region_enabled, false, "without-texture: region disabled")
	_assert_eq(sprite.region_filter_clip_enabled, false, "without-texture: region clip disabled")


func _assert_eq(actual: Variant, expected: Variant, label: String) -> void:
	if actual == expected:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail("%s - expected %s, got %s" % [label, expected, actual])


func _assert_true(condition: bool, label: String) -> void:
	if condition:
		_passes += 1
		print("  ok  %s" % label)
	else:
		_fail(label)


func _fail(msg: String) -> void:
	_failures.append(msg)
	push_error("FAIL: %s" % msg)


func _finish() -> void:
	if _failures.is_empty():
		print("test_sprite_region: all %d checks passed" % _passes)
		quit(0)
	else:
		for failure: String in _failures:
			printerr("  - %s" % failure)
		printerr("test_sprite_region: %d failure(s)" % _failures.size())
		quit(1)
