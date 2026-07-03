"""Reverse-coverage drift guard for the pt-BR i18n table (spec 072, Track A2).

Holds the shipped pt-BR rows and the live-extracted source catalog to each
other in both directions, so the table cannot silently drift from the code:

  - a pt-BR row whose msgid no longer exists in source (stale) fails
    ``test_no_orphan_translations``;
  - a translatable source string with no pt-BR row (new / untranslated)
    fails ``test_full_catalog_coverage``.

The catalog is (re)extracted from ``apps/blender`` on every run, so adding a
new operator label or property without translating it breaks the build.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "blender"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "blender"))

from core.i18n_locales.pt_br import ROWS  # noqa: E402  - sys.path setup above
from extract_i18n import extract_catalog  # noqa: E402

_ADDON = REPO_ROOT / "apps" / "blender"
_CATALOG: set[tuple[str, str]] = set(extract_catalog(_ADDON))
_TRANSLATED: set[tuple[str, str]] = {key for key, _ in ROWS}


def test_no_orphan_translations() -> None:
    """Every pt-BR row maps a msgid that still exists in the source catalog."""
    orphans = sorted(_TRANSLATED - _CATALOG)
    assert not orphans, f"stale pt-BR rows (msgid gone from source): {orphans}"


def test_full_catalog_coverage() -> None:
    """Every translatable source msgid has a pt-BR row (100%, spec 072 completeness)."""
    missing = sorted(_CATALOG - _TRANSLATED)
    assert not missing, f"{len(missing)} untranslated msgids; first: {missing[:8]}"
