"""CLI argument parsing + main orchestrator.

Wired by the ``scripts/validate_automesh.py`` entry shim. ``main()``
is the only external surface; everything else stays private to the
package.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .addon_loader import load_and_register_addon
from .invariants import SPRITE_BOUNDS
from .measurement import load_fixture, run_validation
from .report import print_report, write_json_report


def parse_args() -> argparse.Namespace:
    """Parse args appearing after ``--`` in the Blender invocation."""
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Headless automesh validation")
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional JSON report output path",
    )
    parser.add_argument(
        "--margin-pixels",
        type=int,
        default=0,
        help="margin_pixels operator option (default 0 = no annulus)",
    )
    parser.add_argument(
        "--alpha-threshold",
        type=int,
        default=1,
        help="alpha_threshold operator option (default 1 = include AA edges)",
    )
    parser.add_argument(
        "--ci-only",
        action="store_true",
        help=(
            "Skip sprites flagged ci_safe=False in SPRITE_BOUNDS. The "
            "per-pixel coverage check is O(source_pixels * triangles) "
            "in pure Python; larger fixtures (>= ~256x256 source) push "
            "the runtime past practical CI budget."
        ),
    )
    return parser.parse_args(argv)


def _filter_sprites_for_ci(sprites: list[str], ci_only: bool) -> list[str]:
    """Drop sprites flagged ``ci_safe=False`` when ``--ci-only`` is set."""
    if not ci_only:
        return sprites
    skipped = [n for n in sprites if not SPRITE_BOUNDS[n].ci_safe]
    kept = [n for n in sprites if SPRITE_BOUNDS[n].ci_safe]
    if skipped:
        print(
            f"[validate] --ci-only: skipping {len(skipped)} non-CI-safe sprite(s): "
            f"{', '.join(skipped)}",
            flush=True,
        )
    return kept


def main() -> None:
    args = parse_args()
    load_and_register_addon()
    load_fixture()
    sprites = _filter_sprites_for_ci(list(SPRITE_BOUNDS.keys()), args.ci_only)
    report = run_validation(sprites, args)
    total_failures = print_report(report)
    write_json_report(report, args.report)
    sys.exit(0 if total_failures == 0 else 1)
