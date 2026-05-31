"""Headless automesh validator (the weight-paint-automesh first cut).

Domain package backing ``scripts/validate_automesh.py``. The entry
point is a thin shim that imports :func:`cli.main` and calls it -
all the actual logic lives here:

- ``addon_loader``: mount apps/blender as the ``proscenio`` package
  and run register() against the headless Blender session.
- ``invariants``: ``SpriteInvariants`` dataclass + the per-sprite
  ``SPRITE_BOUNDS`` table + the ``check_invariants`` enforcement.
- ``coverage``: per-pixel coverage + hole-bleed measurement +
  RGBA debug-PNG emission. The CPU-hot path of the validator.
- ``measurement``: bmesh metrics + per-sprite operator invocation.
- ``report``: console + JSON output formatting.
- ``cli``: argparse + main() orchestrator.
"""
