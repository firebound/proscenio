"""Addon-wide i18n registration (the thin bpy-bound assembler).

Wires Blender's ``bpy.app.translations`` so the whole addon becomes
translatable without touching call sites: Blender auto-translates a
registered ``(msgctxt, msgid)`` whenever "Translate Interface" is on and
a locale entry exists. The English strings stay inline as the msgid (the
canonical source, per the idiomatic Blender model).

The per-locale tables live in the bpy-free ``core.i18n_locales`` package
(one module per language). This module stays thin: it imports the folded
``LOCALE_TABLES`` mapping and hands it to Blender at register time.
Adding a language = add a module in ``core.i18n_locales`` (spec 072).

For strings assembled at draw time (f-strings, computed labels), look
them up through ``iface`` so they translate too; static ``bl_label`` /
``bl_description`` / property / ``layout`` strings are auto-translated by
Blender from the registered table and need no change.
"""

from __future__ import annotations

import bpy

from ..i18n_locales import LOCALE_TABLES


def iface(msgid: str, msgctxt: str | None = None) -> str:
    """Translate an interface string for the active locale.

    Use for strings assembled at draw time; static UI strings are
    auto-translated by Blender from the registered table without a call.
    """
    return str(bpy.app.translations.pgettext_iface(msgid, msgctxt))


def register() -> None:
    """Register the addon's per-locale translation tables under the addon key."""
    bpy.app.translations.register(__name__, LOCALE_TABLES)


def unregister() -> None:
    """Drop the addon's translation table."""
    bpy.app.translations.unregister(__name__)
