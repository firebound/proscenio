"""Pure-pytest unit tests for the sprite-frame wrap helper.

The conftest bpy/mathutils stand-ins let the writer module import so the
pure frame-index math runs without Blender.
"""

from __future__ import annotations

from types import SimpleNamespace

from blender.exporters.godot.writer import sprite_frame_animations as sfa


class _Sprite:
    """Minimal CP carrier: dict-style ``.get`` + a ``name``. Empty CPs read as
    a 1x1 grid (``max_frame`` 0), the unset-grid case under test."""

    def __init__(self, name: str, cps: dict[str, object] | None = None) -> None:
        self.name = name
        self._cps = cps or {}

    def get(self, key: str, default: object = None) -> object:
        return self._cps.get(key, default)


def _frame_action(values: list[int]) -> SimpleNamespace:
    kps = [SimpleNamespace(co=(float(i + 1), float(v))) for i, v in enumerate(values)]
    fcurve = SimpleNamespace(data_path='["proscenio_frame"]', keyframe_points=kps)
    return SimpleNamespace(fcurves=[fcurve], layers=[])


def test_wrap_in_range_is_unchanged() -> None:
    assert sfa._wrap_frame(2, 3) == 2
    assert sfa._wrap_frame(0, 3) == 0
    assert sfa._wrap_frame(3, 3) == 3


def test_wrap_positive_overflow_wraps_like_blender() -> None:
    # hframes*vframes = 4 (max_frame 3): Blender's MODULO shows 4 -> 0, 5 -> 1.
    assert sfa._wrap_frame(4, 3) == 0
    assert sfa._wrap_frame(5, 3) == 1
    assert sfa._wrap_frame(8, 3) == 0


def test_wrap_negative_is_non_negative() -> None:
    # Python modulo keeps the result in [0, max_frame]; -1 lands on the last cell.
    assert sfa._wrap_frame(-1, 3) == 3
    assert sfa._wrap_frame(-4, 3) == 0


def test_wrap_single_cell_grid_is_always_zero() -> None:
    # max_frame 0 -> one cell; every index collapses to 0 (no div-by-zero).
    assert sfa._wrap_frame(7, 0) == 0
    assert sfa._wrap_frame(-3, 0) == 0


def test_direct_frame_unset_grid_warns_and_collapses(capsys) -> None:
    # Distinct frame keys on a sprite with no grid (1x1) all wrap to cell 0 and
    # collapse to a single key - the animation is lost. That must warn, not go
    # silent (the fix is to set hframes/vframes).
    sprite = _Sprite("eyes")
    action = _frame_action([0, 1, 2, 0])
    track = sfa._direct_frame_track(sprite, action, fps=24)
    out = capsys.readouterr().out
    assert "eyes" in out and "grid is" in out
    assert track is not None
    assert [k.frame for k in track.keys] == [0]  # the collapsed single cell


def test_eval_frame_resolves_math_and_vars() -> None:
    assert sfa._eval_frame("floor(x)", {"x": 2.7}) == 2
    assert sfa._eval_frame("v * 2", {"v": 3.0}) == 6


def test_eval_frame_name_error_returns_none() -> None:
    # An undefined name (no such driver variable) fails closed, not raising.
    assert sfa._eval_frame("undefined_name", {}) is None


def test_eval_frame_disallowed_builtin_returns_none() -> None:
    # __builtins__ is stripped, so neither a dangerous nor a benign builtin
    # resolves - both degrade to None (this is a build-time tool, not an RCE gate,
    # but the sandbox must still hold).
    assert sfa._eval_frame("__import__('os')", {}) is None
    assert sfa._eval_frame("abs(-3)", {}) is None


def test_eval_frame_non_numeric_returns_none() -> None:
    # A non-numeric result must not raise out of the writer: int() lives inside
    # the guard, so a string / None result degrades to None like any failure.
    assert sfa._eval_frame("'a string'", {}) is None


def test_direct_frame_set_grid_does_not_warn(capsys) -> None:
    # With a real grid the frames do not collapse, so no warning fires.
    sprite = _Sprite("eyes", {"proscenio_hframes": 2, "proscenio_vframes": 2})
    action = _frame_action([0, 1, 2, 3])
    track = sfa._direct_frame_track(sprite, action, fps=24)
    assert capsys.readouterr().out == ""
    assert track is not None
    assert [k.frame for k in track.keys] == [0, 1, 2, 3]
