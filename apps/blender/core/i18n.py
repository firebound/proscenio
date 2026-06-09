"""Addon-wide i18n registration (build the isolation; translations later).

Wires Blender's ``bpy.app.translations`` so the whole addon becomes
translatable without touching call sites: Blender auto-translates a
registered ``(msgctxt, msgid)`` whenever "Translate Interface" is on and
a locale entry exists. The English strings stay inline as the msgid (the
canonical source, per the idiomatic Blender model); this module is the
single home the per-locale tables grow into.

Adding a language = append rows to ``TRANSLATIONS`` (one
``(msgctxt, msgid) -> ((locale, msgstr), ...)`` per string). The actual
per-locale tables are deferred - this lands the mechanism + format only.

For strings assembled at draw time (f-strings, computed labels), look
them up through ``iface`` so they translate too; static ``bl_label`` /
``bl_description`` / property / ``layout`` strings are auto-translated by
Blender from the registered table and need no change.
"""

from __future__ import annotations

import bpy

# One catalog row: the (context, English msgid) and its per-locale strings.
# msgctxt is usually "*" (the default interface context) or "Operator".
TranslationRow = tuple[tuple[str, str], tuple[tuple[str, str], ...]]

# The canonical per-locale table. Empty for now: the mechanism ships, the
# English strings stay inline as msgids, and locales are appended here later.
# Example row (commented - the format, not a shipped translation):
#   (("*", "Weight Paint"), (("pt_BR", "the translated label"),)),
TRANSLATIONS: tuple[TranslationRow, ...] = ()


def _as_translations_dict(
    rows: tuple[TranslationRow, ...],
) -> dict[str, dict[tuple[str, str], str]]:
    """Fold the catalog rows into the ``{locale: {(ctxt, msgid): msgstr}}`` shape."""
    out: dict[str, dict[tuple[str, str], str]] = {}
    for (msgctxt, msgid), locales in rows:
        for locale, msgstr in locales:
            out.setdefault(locale, {})[(msgctxt, msgid)] = msgstr
    return out


def iface(msgid: str, msgctxt: str | None = None) -> str:
    """Translate an interface string for the active locale.

    Use for strings assembled at draw time; static UI strings are
    auto-translated by Blender from the registered table without a call.
    """
    return str(bpy.app.translations.pgettext_iface(msgid, msgctxt))


def register() -> None:
    """Register the (currently empty) translation table under the addon key."""
    bpy.app.translations.register(__name__, _as_translations_dict(TRANSLATIONS))


def unregister() -> None:
    """Drop the addon's translation table."""
    bpy.app.translations.unregister(__name__)
