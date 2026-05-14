"""Sync canonical examples/ fixtures into the apps/godot/ dev project.

Each fixture under ``examples/<name>/`` exists with the writer's authoritative
output committed as ``<name>.expected.proscenio`` (golden + diff target). The
Godot importer + wrapper scenes expect a runtime-named ``<name>.proscenio``
sitting alongside its textures + wrapper script under ``res://<name>/`` inside
the dev project at ``apps/godot/``.

This script populates ``apps/godot/<name>/`` for each canonical fixture by
**linking** (symlink first, hardlink fallback) the consumable files from the
canonical source under ``examples/``. No duplication on disk: edits in
``examples/`` propagate live.

1. Link ``<name>.expected.proscenio`` -> ``<name>.proscenio`` (drops the
   ``.expected.`` suffix; goldens stay under examples/ for the test harness).
2. Link every PNG sitting in the fixture root or under its texture subdirs
   (``pillow_layers/``, ``render_layers/``, ``00_blender_base/render_layers/``)
   into the same dest directory so the Godot importer + Sprite2D / Polygon2D
   builders can find them via filename lookup.
3. Link ``examples/<name>/godot/<Name>.tscn`` + ``<Name>.gd`` (the wrapper
   scene pattern - SPEC 001 Option A) into ``apps/godot/<name>/godot/``.

Link strategy:
- Try ``os.symlink`` first (works on POSIX always; Windows needs Developer
  Mode or admin).
- Fallback to ``os.link`` (hardlink) on permission error - Windows NTFS
  honors hardlinks without elevation; cross-volume hardlinks fail, but
  examples/ + apps/godot/ live on the same volume here.
- If both fail, falls back to ``shutil.copy2`` and prints a warning. Edits
  in examples/ won't propagate live in this last-resort path.

Output is **gitignored**. Treat ``apps/godot/<name>/`` as derived; regenerate
when sources change.

Run from the repository root:

    python scripts/godot/sync_fixtures.py
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples"
GODOT_DEST_DIR = REPO_ROOT / "apps" / "godot" / "examples"

# Subdirs (relative to the fixture root) to scan for PNGs that may need to
# travel alongside the .proscenio so the Godot importer resolves textures.
_TEXTURE_SUBDIRS: tuple[str, ...] = (
    "",
    "pillow_layers",
    "render_layers",
    "00_blender_base/render_layers",
    "_spritesheets",
)

# Fixtures intentionally excluded from the Godot sync. ``doll`` is an
# authoring sandbox for the Photoshop roundtrip: materials carry flat
# Base Color only (no Image Texture node), polygon vertices live in
# world coordinates instead of being centred per-mesh, and the rest
# pose was never authored for direct Godot consumption. The proper
# Godot-target fixture is the future ``doll-from-photoshop`` derived
# .blend documented in specs/007-testing-fixtures/TODO.md.
_GODOT_SKIP: frozenset[str] = frozenset({"doll"})


def discover_fixtures() -> list[tuple[str, Path]]:
    """Return ``(short_name, fixture_root)`` for every fixture with a golden.

    Skips entries listed in ``_GODOT_SKIP`` so authoring-only fixtures
    (doll today) stay out of the Godot dev project.
    """
    out: list[tuple[str, Path]] = []
    for golden in sorted(EXAMPLES_DIR.rglob("*.expected.proscenio")):
        short = golden.name[: -len(".expected.proscenio")]
        if short in _GODOT_SKIP:
            continue
        out.append((short, golden.parent))
    return out


def _link_file(src: Path, dst: Path) -> None:
    """Link ``src`` -> ``dst`` (symlink -> hardlink -> copy fallback chain)."""
    if dst.exists() or dst.is_symlink():
        dst.unlink()
    try:
        os.symlink(src, dst)
        return
    except (OSError, NotImplementedError):
        pass
    try:
        os.link(src, dst)
        return
    except OSError:
        pass
    print(
        f"[sync_fixtures] WARNING: could not link {src} -> {dst}; "
        "falling back to plain copy. Edits in examples/ will NOT propagate live; "
        "re-run this script after each source change.",
        file=sys.stderr,
    )
    shutil.copy2(src, dst)


def _link_pngs(fixture_root: Path, dest: Path) -> int:
    """Link every PNG found in known texture subdirs into ``dest``."""
    seen: set[str] = set()
    linked = 0
    for sub in _TEXTURE_SUBDIRS:
        tex_dir = fixture_root / sub if sub else fixture_root
        if not tex_dir.is_dir():
            continue
        for png in sorted(tex_dir.glob("*.png")):
            if png.name in seen:
                continue
            seen.add(png.name)
            _link_file(png, dest / png.name)
            linked += 1
    return linked


def _link_wrappers(fixture_root: Path, dest: Path) -> int:
    """Link ``examples/<name>/godot/*.{tscn,gd}`` flat into ``dest/``.

    The wrapper TSCNs reference ``res://<name>/<Name>.gd`` (root, not
    ``res://<name>/godot/<Name>.gd``) - the convention is "drop
    examples/<name>/godot/<wrapper> directly into res://<name>/", so
    the sync flattens the godot/ subdir at the destination.
    """
    wrapper_src = fixture_root / "godot"
    if not wrapper_src.is_dir():
        return 0
    linked = 0
    for item in sorted(wrapper_src.iterdir()):
        if item.suffix in {".tscn", ".gd"}:
            _link_file(item, dest / item.name)
            linked += 1
    return linked


def sync_one(short_name: str, fixture_root: Path) -> dict[str, int]:
    """Mirror a single fixture into ``apps/godot/<short_name>/``."""
    dest = GODOT_DEST_DIR / short_name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)

    _link_file(
        fixture_root / f"{short_name}.expected.proscenio",
        dest / f"{short_name}.proscenio",
    )
    return {
        "proscenio": 1,
        "png": _link_pngs(fixture_root, dest),
        "wrapper": _link_wrappers(fixture_root, dest),
    }


def main() -> int:
    if not EXAMPLES_DIR.is_dir():
        print(f"FAIL: {EXAMPLES_DIR} does not exist", file=sys.stderr)
        return 1
    GODOT_DEST_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = discover_fixtures()
    if not fixtures:
        print("FAIL: no fixtures discovered", file=sys.stderr)
        return 1

    total = {"proscenio": 0, "png": 0, "wrapper": 0}
    print(f"Syncing {len(fixtures)} fixture(s) into {GODOT_DEST_DIR}:")
    for short_name, fixture_root in fixtures:
        counts = sync_one(short_name, fixture_root)
        for key, val in counts.items():
            total[key] += val
        print(
            f"  {short_name:<14} <- {fixture_root.relative_to(REPO_ROOT)} "
            f"[proscenio={counts['proscenio']}, png={counts['png']}, "
            f"wrapper={counts['wrapper']}]"
        )

    print(
        f"\nTotal: {total['proscenio']} .proscenio, {total['png']} PNG(s), "
        f"{total['wrapper']} wrapper file(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
