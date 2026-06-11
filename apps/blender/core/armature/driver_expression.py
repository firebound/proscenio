"""Bone-channel -> property driver expression builder (bpy-free).

The Drive-from-Bone shortcut exposes two ranges - an input bone-channel
range and an output target-value range - instead of a raw expression. This
turns those four numbers into a clamped linear-map driver expression over
``var`` (the bone channel). Clamping holds out-of-range input at the nearest
output end rather than letting it run away, and a zero-width input range
collapses to a constant so the expression never divides by zero.

Replaces the old ``var`` default, which mapped radians (about -pi..pi)
straight onto a 0..N frame range: negative rotation clamped to 0 and the
flagship driver looked broken on first contact.
"""

from __future__ import annotations


def _fmt(value: float) -> str:
    """Round-trippable float literal for embedding in the expression string."""
    return repr(float(value))


def build_driver_expression(
    in_min: float,
    in_max: float,
    out_min: float,
    out_max: float,
) -> str:
    """Clamped linear map from ``[in_min, in_max]`` onto ``[out_min, out_max]``.

    Returns a Blender driver expression over ``var``. Values outside the input
    range hold at the nearest output end (the output band is sorted so an
    inverted ``out_min > out_max`` clamps correctly). A degenerate input range
    (``in_min == in_max``) returns the constant ``out_min`` - no division by
    zero.
    """
    if in_max == in_min:
        return _fmt(out_min)
    low = _fmt(min(out_min, out_max))
    high = _fmt(max(out_min, out_max))
    mapped = (
        f"{_fmt(out_min)} + (var - {_fmt(in_min)}) "
        f"* ({_fmt(out_max)} - {_fmt(out_min)}) / ({_fmt(in_max)} - {_fmt(in_min)})"
    )
    return f"min(max({mapped}, {low}), {high})"
