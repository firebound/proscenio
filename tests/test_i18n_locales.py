"""Unit tests for per-locale i18n table assembly (spec 072, Track A1).

Pure pytest, no Blender. Exercises the fold that turns per-locale
modules (each exporting ``LOCALE`` + ``ROWS``) into the
``{locale: {(msgctxt, msgid): msgstr}}`` mapping Blender's
``bpy.app.translations.register`` consumes. The real ``pgettext_iface``
round-trip against a live Blender locale is covered by the in-Blender
test (apps/blender/tests/operators/test_i18n_translation.py).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

from core.i18n_locales import (  # noqa: E402  - sys.path setup above
    LOCALE_MODULES,
    LOCALE_TABLES,
    fold,
)


def _locale_module(
    locale: str, rows: list[tuple[tuple[str, str], str]]
) -> SimpleNamespace:
    """Stand-in for a per-locale module: just ``LOCALE`` + ``ROWS``."""
    return SimpleNamespace(LOCALE=locale, ROWS=tuple(rows))


def test_fold_maps_ctxt_msgid_to_msgstr_under_its_locale() -> None:
    mod = _locale_module("pt_BR", [(("*", "Weight Paint"), "Pintura de peso")])
    assert fold([mod]) == {"pt_BR": {("*", "Weight Paint"): "Pintura de peso"}}


def test_fold_keeps_locales_separate() -> None:
    pt = _locale_module("pt_BR", [(("*", "Atlas"), "Atlas")])
    es = _locale_module("es", [(("*", "Atlas"), "Atlas ES")])
    table = fold([pt, es])
    assert table["pt_BR"][("*", "Atlas")] == "Atlas"
    assert table["es"][("*", "Atlas")] == "Atlas ES"


def test_fold_preserves_msgctxt_in_the_key() -> None:
    """Same text under different contexts stays distinct (default vs Operator)."""
    mod = _locale_module(
        "pt_BR",
        [
            (("*", "Mirror"), "Espelhar"),
            (("Operator", "Mirror"), "Espelhar (operador)"),
        ],
    )
    table = fold([mod])
    assert table["pt_BR"][("*", "Mirror")] == "Espelhar"
    assert table["pt_BR"][("Operator", "Mirror")] == "Espelhar (operador)"


def test_fold_of_empty_module_yields_no_locale_key() -> None:
    """Ships-empty behaviour: a locale with zero rows is not advertised."""
    assert fold([_locale_module("pt_BR", [])]) == {}


def test_pt_br_module_is_wired_into_the_package() -> None:
    """The pt_BR module is aggregated (append-only frame), even while ROWS grow."""
    assert any(m.LOCALE == "pt_BR" for m in LOCALE_MODULES)


def test_shipped_aggregate_is_exactly_the_fold_of_the_modules() -> None:
    """LOCALE_TABLES is the single source register() consumes - keep it honest."""
    assert LOCALE_TABLES == fold(LOCALE_MODULES)
