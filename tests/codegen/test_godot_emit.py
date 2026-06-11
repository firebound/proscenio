"""Smoke tests for the GDScript Resource emitter.

These cover the Python-side contract: every pydantic model produces a
file, the emit is deterministic across runs, and the header banner
survives. The GDScript itself is rebuilt and verified by the Godot
lint job in CI.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from proscenio_codegen.godot_emit import (
    GODOT_BINDINGS_DIR,
    _emit_helpers,
    _resolve_type,
    emit_godot_resources,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_godot_emitter_writes_one_file_per_model(tmp_path: Path) -> None:
    """Emit lands at least the model-derived files plus the dispatchers."""
    written = emit_godot_resources(tmp_path)
    names = {p.name for p in written}

    # Every class_name carries the `Proscenio` prefix to avoid colliding
    # with Godot built-ins (`Animation`, `Skeleton`, ...); filenames follow.
    expected_models = {
        "proscenio_bone.gd",
        "proscenio_skeleton.gd",
        "proscenio_weight.gd",
        "proscenio_mesh_element.gd",
        "proscenio_sprite_element.gd",
        "proscenio_slot.gd",
        "proscenio_key.gd",
        "proscenio_track.gd",
        "proscenio_animation.gd",
        "proscenio_document.gd",
        "proscenio_mesh_layer.gd",
        "proscenio_sprite_layer.gd",
        "proscenio_frame_entry.gd",
        "proscenio_psd_manifest.gd",
    }
    expected_dispatchers = {"proscenio_element.gd", "proscenio_layer.gd"}
    expected_helpers = {"proscenio_parse_helpers.gd"}

    missing = (expected_models | expected_dispatchers | expected_helpers) - names
    assert not missing, f"emitter did not produce: {missing}"


def test_emit_is_deterministic(tmp_path: Path) -> None:
    """Two consecutive emits must produce byte-identical files.

    Runs without the gdformat whitespace post-pass, so it exercises the
    Python emit path's own determinism (catches dict/set ordering bugs in
    the dispatcher case-list, for example).
    """
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    written_a = {
        p.name: p.read_text(encoding="utf-8") for p in emit_godot_resources(dir_a)
    }
    written_b = {
        p.name: p.read_text(encoding="utf-8") for p in emit_godot_resources(dir_b)
    }
    assert written_a == written_b


def test_committed_artifacts_match_emit() -> None:
    """The checked-in .gd files reproduce from the current pydantic models.

    Catches a contributor who edited a generated file by hand instead of
    the source models, by diffing the committed files against a fresh emit.
    """
    if not GODOT_BINDINGS_DIR.is_dir():
        pytest.skip("schema_bindings/ not committed yet")
    if shutil.which("gdformat") is None and shutil.which("gdformat.exe") is None:
        pytest.skip("gdformat not on PATH; lint-gdscript CI job is the staleness gate")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp_str:
        fresh = Path(tmp_str)
        emit_godot_resources(fresh)
        for committed in GODOT_BINDINGS_DIR.glob("*.gd"):
            fresh_file = fresh / committed.name
            assert fresh_file.is_file(), f"emitter no longer produces {committed.name}"
            assert fresh_file.read_text(encoding="utf-8") == committed.read_text(
                encoding="utf-8"
            ), (
                f"{committed.name} differs from the pydantic-derived emit. "
                "Run `python -m proscenio_codegen godot`."
            )


def test_resolve_list_of_int_lists_maps_to_packed_int_array() -> None:
    resolved = _resolve_type(list[list[int]])
    assert resolved.gd_type == "Array[PackedInt32Array]"
    assert "_parse_int_array" in resolved.parse_expr_template


def test_int_array_parse_helper_is_emitted() -> None:
    assert "_parse_int_array" in _emit_helpers()


def test_each_file_carries_auto_generated_banner(tmp_path: Path) -> None:
    written = emit_godot_resources(tmp_path)
    for path in written:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert "AUTO-GENERATED" in first_line
