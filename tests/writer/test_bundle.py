"""Pure-pytest tests for the texture-bundle collision detection.

The bpy substitute in ``conftest`` lets the module import; ``image_filename`` /
``image_abspath`` are duck-typed over ``image.name`` / ``image.filepath`` and
the stub's pass-through ``bpy.path.abspath``, so a plain ``SimpleNamespace``
image drives the real collision logic. The copy-to-disk half of
``bundle_textures`` is bpy + filesystem integration and covered in-Blender.
"""

from __future__ import annotations

from types import SimpleNamespace

from blender.exporters.godot.writer import bundle


def _img(name: str, filepath: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, filepath=filepath)


def _register(*images: SimpleNamespace) -> list[str]:
    by_name: dict[str, object] = {}
    source_by_name: dict[str, object] = {}
    collisions: list[str] = []
    for image in images:
        bundle._register_image(image, by_name, source_by_name, collisions)
    return collisions


def test_register_image_dedupes_the_same_source() -> None:
    a = _img("torso", "/images/torso.png")
    assert _register(a, a) == []  # same source twice -> not a collision


def test_register_image_flags_two_distinct_sources() -> None:
    a = _img("torso_a", "/a/torso.png")
    b = _img("torso_b", "/b/torso.png")  # different folder, same basename
    assert _register(a, b) == ["torso.png"]


def test_register_image_flags_a_pathless_collision() -> None:
    # An unsaved image (no filepath) whose synthesised name collides with a saved
    # one is still a collision - the CodeRabbit fix: do not require a path.
    saved = _img("logo_src", "/a/logo.png")  # -> logo.png
    pathless = _img("logo", "")  # synth -> logo.png, abspath None
    assert _register(saved, pathless) == ["logo.png"]


def test_register_image_records_each_name_once() -> None:
    a = _img("torso_a", "/a/torso.png")
    b = _img("torso_b", "/b/torso.png")
    c = _img("torso_c", "/c/torso.png")
    assert _register(a, b, c) == ["torso.png"]  # recorded once, not per extra
