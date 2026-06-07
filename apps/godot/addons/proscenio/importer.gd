@tool
extends EditorImportPlugin

const SkeletonBuilder := preload("res://addons/proscenio/builders/skeleton_builder.gd")
const SlotBuilder := preload("res://addons/proscenio/builders/slot_builder.gd")
const MeshBuilder := preload("res://addons/proscenio/builders/mesh_builder.gd")
const SpriteBuilder := preload("res://addons/proscenio/builders/sprite_builder.gd")
const AnimationBuilder := preload("res://addons/proscenio/builders/animation_builder.gd")

const SUPPORTED_FORMAT_VERSION := 1


func _get_importer_name() -> String:
	return "proscenio.character"


func _get_visible_name() -> String:
	return "Proscenio Character"


func _get_recognized_extensions() -> PackedStringArray:
	return PackedStringArray(["proscenio"])


func _get_save_extension() -> String:
	return "scn"


func _get_resource_type() -> String:
	return "PackedScene"


func _get_priority() -> float:
	return 1.0


func _get_import_order() -> int:
	return 0


func _get_preset_count() -> int:
	return 1


func _get_preset_name(_preset_index: int) -> String:
	return "Default"


func _get_import_options(_path: String, _preset_index: int) -> Array[Dictionary]:
	return []


func _get_option_visibility(_path: String, _option_name: StringName, _options: Dictionary) -> bool:
	return true


func _import(
	source_file: String,
	save_path: String,
	_options: Dictionary,
	_platform_variants: Array[String],
	_gen_files: Array[String]
) -> Error:
	var document := _load_document(source_file)
	if document == null:
		# `_load_document` already pushed the diagnostic; surface a
		# consistent error code here so the editor reimport flow stays
		# deterministic.
		return ERR_INVALID_DATA

	var root := Node2D.new()
	root.name = document.name if document.name != "" else "Character"

	var skeleton := SkeletonBuilder.build(document.skeleton)
	root.add_child(skeleton)

	var atlas := _load_atlas(source_file, document.atlas)
	var source_dir := source_file.get_base_dir()
	# Slots build BEFORE sprites so the sprite builders can route attachment
	# children under the slot Node2D parent. Empty slots
	# leaves the map empty and sprite routing falls back to bone-parented.
	var slot_map := SlotBuilder.build(skeleton, document.slots)
	# Each builder discriminator-filters its own element kind; calling both is
	# cheap and keeps the dispatch table flat. Order does not matter.
	MeshBuilder.attach_elements(skeleton, document.elements, atlas, slot_map, source_dir)
	SpriteBuilder.attach_elements(skeleton, document.elements, atlas, slot_map, source_dir)

	var animation_player := AnimationPlayer.new()
	animation_player.name = "AnimationPlayer"
	root.add_child(animation_player)
	AnimationBuilder.populate(animation_player, skeleton, document.animations)

	_set_owner_recursive(root, root)

	var packed := PackedScene.new()
	var pack_err := packed.pack(root)
	if pack_err != OK:
		return pack_err

	var output_path := "%s.scn" % save_path
	if ResourceLoader.exists(output_path):
		print_verbose(
			"Proscenio: regenerating %s (existing scene will be overwritten)" % output_path
		)
	return ResourceSaver.save(packed, output_path)


static func _load_document(source_file: String) -> ProscenioDocument:
	# Open the .proscenio file, parse JSON, and validate the document root
	# against the typed model. Pushes its own error on every failure path
	# and returns null so the caller surfaces a single error code.
	var file := FileAccess.open(source_file, FileAccess.READ)
	if file == null:
		push_error(
			"Proscenio: cannot open '%s' (error %d)" % [source_file, FileAccess.get_open_error()]
		)
		return null

	var json := JSON.new()
	var parse_err := json.parse(file.get_as_text())
	if parse_err != OK:
		push_error(
			(
				"Proscenio: JSON parse failed at line %d: %s"
				% [json.get_error_line(), json.get_error_message()]
			)
		)
		return null

	if typeof(json.data) != TYPE_DICTIONARY:
		push_error("Proscenio: expected JSON object at document root")
		return null

	var raw: Dictionary = json.data
	# Parse through the schema-derived Resource. Future schema additions land
	# in the pydantic source (packages/models/) + a codegen re-run; the
	# importer reads typed fields off the resulting Resource graph.
	var document := ProscenioDocument.from_dict(raw)
	if document == null:
		push_error("Proscenio: ProscenioDocument.from_dict returned null")
		return null
	if document.format_version != SUPPORTED_FORMAT_VERSION:
		push_error(
			(
				"Proscenio: unsupported format_version %d (need %d)"
				% [document.format_version, SUPPORTED_FORMAT_VERSION]
			)
		)
		return null
	return document


static func _load_atlas(source_file: String, atlas_path: String) -> Texture2D:
	if atlas_path == "":
		return null
	var source_dir := source_file.get_base_dir()
	var full := source_dir.path_join(atlas_path)
	if not ResourceLoader.exists(full):
		push_warning("Proscenio: atlas not found at '%s'" % full)
		return null
	var resource: Resource = ResourceLoader.load(
		full, "Texture2D", ResourceLoader.CACHE_MODE_REPLACE
	)
	if resource == null:
		push_error("Proscenio: ResourceLoader.load() returned null for '%s'" % full)
		return null
	var tex := resource as Texture2D
	if tex == null:
		push_error(
			"Proscenio: '%s' loaded but not Texture2D - got %s" % [full, resource.get_class()]
		)
		return null
	return tex


static func _set_owner_recursive(node: Node, owner: Node) -> void:
	for child in node.get_children():
		if child != owner:
			child.owner = owner
		_set_owner_recursive(child, owner)
