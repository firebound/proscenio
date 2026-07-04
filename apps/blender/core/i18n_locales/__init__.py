"""Per-locale i18n tables for the Blender addon (spec 072, Track A).

Each language is one module in this package exporting ``LOCALE`` (the
Blender locale code, e.g. ``pt_BR``) and ``ROWS`` - a tuple of
``((msgctxt, msgid), msgstr)`` where ``msgid`` is the canonical English
source string. English is never a module here; it is the msgid itself.

``fold`` collapses the modules into ``{locale: {(msgctxt, msgid): msgstr}}``,
the exact mapping ``bpy.app.translations.register`` consumes, and
``LOCALE_TABLES`` is that mapping for the shipped locales. Adding a
language is append-only: drop a new module in this package and list it in
``LOCALE_MODULES``.

This package is bpy-free (pure data + a fold), so it sits at the
``core/`` top level per the core-package contract and is unit-testable
without Blender. The bpy-bound assembler that registers the table lives
in ``core/bpy_helpers/i18n.py``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from . import pt_br
from ._types import LocaleRow


class LocaleModule(Protocol):
    """Structural shape every per-locale module satisfies."""

    LOCALE: str
    ROWS: tuple[LocaleRow, ...]


def fold(modules: Iterable[LocaleModule]) -> dict[str, dict[tuple[str, str], str]]:
    """Collapse per-locale modules into ``{locale: {(msgctxt, msgid): msgstr}}``.

    A locale contributing no rows is omitted from the result, so the
    mechanism ships as an empty table until a locale is populated -
    matching the pre-split ``TRANSLATIONS = ()`` behaviour.
    """
    out: dict[str, dict[tuple[str, str], str]] = {}
    for module in modules:
        for (msgctxt, msgid), msgstr in module.ROWS:
            out.setdefault(module.LOCALE, {})[(msgctxt, msgid)] = msgstr
    return out


#: Every locale module the addon ships. Append a module to add a language.
LOCALE_MODULES: tuple[LocaleModule, ...] = (pt_br,)

#: The mapping ``i18n.register`` hands to ``bpy.app.translations.register``.
LOCALE_TABLES: dict[str, dict[tuple[str, str], str]] = fold(LOCALE_MODULES)
