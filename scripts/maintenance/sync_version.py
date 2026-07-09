#!/usr/bin/env python3
"""Single source of truth for the product version.

The root ``VERSION`` file is canonical. The three shipped app bundles each
declare their own version field, and they used to drift by hand (a release once
went out with the Blender manifest a full minor behind the tag). This script
propagates ``VERSION`` into every declaration, and ``--check`` fails CI when any
of them has drifted.

Channel suffix handling: ``VERSION`` may carry a channel marker on the beta
channel (``0.9.1-beta``, ``1.0.0-rc1``). The Blender extension manifest and the
UXP manifest only accept a numeric ``MAJOR.MINOR.PATCH``, so the manifest fields
carry the *core* (suffix stripped); the channel marker lives on ``VERSION`` and
the git tag only. For a final release (``1.0.0``) core and VERSION coincide.

Not synced (independent lifecycles, deliberately left alone):
  - ``pyproject.toml`` (root) - the uv *workspace root*, never published.
  - ``packages/*/pyproject.toml`` - internal libraries versioned on their own.

Usage:
  python scripts/maintenance/sync_version.py          # write VERSION into all manifests
  python scripts/maintenance/sync_version.py --check   # verify sync, exit 1 on drift
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VERSION_FILE = REPO_ROOT / "VERSION"


@dataclass(frozen=True)
class Target:
    """A version declaration to keep in lockstep with ``VERSION``.

    ``pattern`` must capture the version string in group ``ver`` and keep the
    surrounding syntax in groups ``pre``/``post`` so a rewrite is byte-exact
    apart from the version itself.
    """

    path: Path
    pattern: re.Pattern[str]
    label: str


# Anchored so `version = "..."` matches but `schema_version` / `blender_version_min`
# / `manifestVersion` do not.
_TOML_CFG = re.compile(r'(?P<pre>^version\s*=\s*")(?P<ver>[^"]*)(?P<post>")', re.MULTILINE)
_JSON = re.compile(r'(?P<pre>"version"\s*:\s*")(?P<ver>[^"]*)(?P<post>")')

TARGETS: tuple[Target, ...] = (
    Target(REPO_ROOT / "apps/blender/blender_manifest.toml", _TOML_CFG, "Blender extension manifest"),
    Target(REPO_ROOT / "apps/godot/addons/proscenio/plugin.cfg", _TOML_CFG, "Godot plugin.cfg"),
    Target(REPO_ROOT / "apps/photoshop/plugin/manifest.json", _JSON, "Photoshop UXP manifest"),
    Target(REPO_ROOT / "apps/photoshop/package.json", _JSON, "Photoshop package.json"),
)


def read_version() -> str:
    raw = VERSION_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        sys.exit("VERSION file is empty")
    return raw


def numeric_core(version: str) -> str:
    """`1.0.0-rc1` -> `1.0.0`. Manifest fields take the core only."""
    core = version.split("-", 1)[0]
    if not re.fullmatch(r"\d+\.\d+\.\d+", core):
        sys.exit(f"VERSION core {core!r} is not MAJOR.MINOR.PATCH")
    return core


def current_field(target: Target) -> str:
    text = target.path.read_text(encoding="utf-8")
    match = target.pattern.search(text)
    if match is None:
        sys.exit(f"no version field found in {target.path}")
    return match.group("ver")


def rewrite(target: Target, core: str) -> bool:
    """Write ``core`` into ``target``. Return True if the file changed."""
    text = target.path.read_text(encoding="utf-8")
    new_text, n = target.pattern.subn(
        lambda m: f"{m.group('pre')}{core}{m.group('post')}", text, count=1
    )
    if n != 1:
        sys.exit(f"no version field found in {target.path}")
    if new_text == text:
        return False
    # write_text on Windows would translate LF to CRLF and corrupt these files;
    # write bytes to preserve the on-disk line endings exactly.
    target.path.write_bytes(new_text.encode("utf-8"))
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify sync without writing; exit 1 on drift")
    args = parser.parse_args()

    version = read_version()
    core = numeric_core(version)

    if args.check:
        drift = [(t.label, cur, core) for t in TARGETS if (cur := current_field(t)) != core]
        if drift:
            print(f"Version drift from VERSION ({version}, core {core}):", file=sys.stderr)
            for label, cur, want in drift:
                print(f"  {label}: {cur} != {want}", file=sys.stderr)
            print("Run: python scripts/maintenance/sync_version.py", file=sys.stderr)
            return 1
        print(f"All {len(TARGETS)} version declarations match VERSION core {core}.")
        return 0

    changed = [t.label for t in TARGETS if rewrite(t, core)]
    if changed:
        print(f"Synced to {core}: {', '.join(changed)}")
    else:
        print(f"Already at {core}; nothing to do.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
