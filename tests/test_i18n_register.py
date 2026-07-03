"""i18n.register wires the per-locale package table into Blender (spec 072 A1).

Pure pytest: ``bpy`` is mocked (external I/O) so we can assert the thin
assembler hands Blender exactly the folded ``LOCALE_TABLES`` from
``core.i18n_locales`` under the addon key, without launching Blender.
The real ``pgettext_iface`` translation round-trip is the in-Blender test
(apps/blender/tests/operators/test_i18n_translation.py).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps/blender"))

# i18n imports bpy at module top; install a mock before importing it so the
# module loads outside Blender (repo-root pytest has no bpy shim).
sys.modules.setdefault("bpy", MagicMock())

from core.bpy_helpers import i18n  # noqa: E402  - after the bpy mock above
from core.i18n_locales import LOCALE_TABLES  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_bpy_mock() -> None:
    """Each test sees a clean translations mock (sys.modules['bpy'] is shared)."""
    i18n.bpy.app.translations.register.reset_mock()
    i18n.bpy.app.translations.unregister.reset_mock()


def test_register_hands_blender_the_package_locale_tables() -> None:
    """register sources the package aggregate itself, not a recomputed table."""
    i18n.register()
    call = i18n.bpy.app.translations.register.call_args
    assert call.args[0] == i18n.__name__
    assert call.args[1] is LOCALE_TABLES


def test_unregister_drops_the_addon_key() -> None:
    i18n.unregister()
    i18n.bpy.app.translations.unregister.assert_called_once_with(i18n.__name__)
