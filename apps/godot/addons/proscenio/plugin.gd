@tool
extends EditorPlugin

const ProscenioImporter := preload("res://addons/proscenio/importer.gd")

var _importer: EditorImportPlugin


func _enter_tree() -> void:
	_importer = ProscenioImporter.new()
	add_import_plugin(_importer)


func _exit_tree() -> void:
	if _importer:
		remove_import_plugin(_importer)
		_importer = null
