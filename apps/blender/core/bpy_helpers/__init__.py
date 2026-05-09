"""bpy-bound helpers (SPEC 009 wave 9.6).

Submodules in this subpackage import ``bpy`` at module top. Code that
runs in pytest contexts (no Blender) must NOT import from here. The
rest of ``core/`` is bpy-free.

Modules:

- ``atlas_collect.py``      ``SourceImage`` + walk meshes for textured materials
- ``atlas_compose.py``      assemble packed ``bpy.types.Image`` + write manifest JSON
- ``atlas_manifest.py``     ``Placement`` + read manifest JSON
- ``psd_spritesheet.py``    Photoshop-driven spritesheet composition
- ``sprite_frame_shader.py`` Material slicer node group setup / removal
- ``select.py``             ``select_only(context, obj)`` helper
- ``viewport_math.py``      mouse-event projection onto z=0 plane

This ``__init__.py`` deliberately does NOT eager-import the submodules.
Tests that touch one submodule (after mocking bpy) should import
``from core.bpy_helpers.sprite_frame_shader import ...`` directly so
the other bpy-bound modules do not load and fail on a missing bpy.
"""
