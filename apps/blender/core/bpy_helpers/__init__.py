"""bpy-bound helpers.

Submodules in this subpackage import ``bpy`` at module top. Code that
runs in pytest contexts (no Blender) must NOT import from here. The
rest of ``core/`` is bpy-free.

Subpackages:

- ``_shared/``      cross-cutting bpy-bound infra (viewport_math, modal_overlay,
                    select, _bpy_compat)
- ``atlas/``        atlas collect / compose / manifest helpers
- ``psd/``          the spritesheet composer
- ``sprite_frame/`` the preview shader-node-group builder
- ``automesh/`` / ``skinning/``  per-feature bpy-bound domain packages

This ``__init__.py`` deliberately does NOT eager-import the submodules.
Tests that touch one submodule (after mocking bpy) should import
``from core.bpy_helpers.sprite_frame.sprite_frame_shader import ...`` directly so
the other bpy-bound modules do not load and fail on a missing bpy.
"""
