"""In-Blender round-trip for the folded i18n table (spec 072, Track A1).

Rides the operator runner because it needs a live Blender translation
subsystem (``bpy.app.translations``), not because it drives an operator.
Proves ``core.i18n_locales.fold`` produces a mapping Blender registers and
``pgettext_iface`` resolves under ``pt_BR``, and that an unregistered
msgid falls back to its canonical English source.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import bpy
import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "apps" / "blender"))

from core.i18n_locales import fold  # noqa: E402  - sys.path setup above

_TEST_KEY = "_proscenio_i18n_roundtrip_test"
_CTXT = "*"
# A Proscenio-namespaced msgid Blender has no native translation for. Blender
# ships its own pt_BR table, so a bare Blender-native msgid (e.g. "Weight Paint"
# -> "Pintura de influência") resolves to Blender's string, not an addon
# registration under the default "*" context - addon strings that must override
# a Blender-native term need a distinct msgctxt. Here we assert our own round-trip
# on a string Blender does not own, and prove an accented msgstr survives.
_MSGID = "Proscenio Weight Transfer"
_MSGSTR = "Transferência de peso"


@pytest.fixture
def pt_br_interface() -> Iterator[None]:
    """Force the interface to translate under pt_BR, restoring prefs after."""
    view = bpy.context.preferences.view
    prev_lang = view.language
    prev_toggle = view.use_translate_interface
    view.use_translate_interface = True
    view.language = "pt_BR"
    try:
        yield
    finally:
        view.language = prev_lang
        view.use_translate_interface = prev_toggle


def test_folded_table_translates_under_pt_br(pt_br_interface: None) -> None:
    """A seeded row folded by core.i18n_locales.fold round-trips through Blender."""
    module = SimpleNamespace(LOCALE="pt_BR", ROWS=(((_CTXT, _MSGID), _MSGSTR),))
    bpy.app.translations.register(_TEST_KEY, fold([module]))
    try:
        assert bpy.app.translations.pgettext_iface(_MSGID, _CTXT) == _MSGSTR
    finally:
        bpy.app.translations.unregister(_TEST_KEY)


def test_unregistered_msgid_falls_back_to_english(pt_br_interface: None) -> None:
    """Any msgid with no row shows its English source - partial locales are safe."""
    untranslated = "A String With No Proscenio Translation"
    assert bpy.app.translations.pgettext_iface(untranslated) == untranslated
