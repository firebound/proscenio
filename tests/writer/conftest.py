"""Shared scaffolding for pure-pytest tests of the Blender->Godot writer.

The writer modules (``exporters/godot/writer/*``) and their shared
helpers (``core/bpy_helpers/_shared/_bpy_compat``, ``writer/skeleton``)
do a top-level ``import bpy`` / ``from mathutils import Vector`` because
they use those native modules at runtime. fake-bpy-module ships type
stubs only (no runtime module), so importing the writer chain under
plain pytest fails with ``ModuleNotFoundError``.

These tests exercise the *pure* projection logic (transform math plus
typed-model construction), never the bpy-bound code paths. We install
lightweight stand-ins for ``bpy`` and ``mathutils`` in ``sys.modules``
so the import chain resolves; the stubs carry just enough surface for
the pure functions (isinstance bases for the ``expect_*`` narrowing
helpers, a pass-through ``bpy.path.abspath``, and a minimal ``Vector``).
Any bpy-bound call (``bpy.data`` access, real fcurve evaluation) is
patched per test instead.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

_BLENDER_ROOT = Path(__file__).resolve().parents[2] / "apps" / "blender"


def _install_addon_root_package() -> None:
    """Expose apps/blender as the synthetic ``blender`` package.

    The writer modules reach sibling subpackages with deep relative
    imports (``from ....core...``), which assume the addon directory is
    itself a package above ``exporters``. The pure-test convention puts
    subpackages on sys.path as top-level names, which cannot satisfy
    that four-level hop. Registering a synthetic ``blender`` package
    whose ``__path__`` points at apps/blender lets
    ``blender.exporters.godot.writer.animations`` import and resolves
    its ``....core`` to ``blender.core`` - without executing the addon's
    own ``__init__`` (which registers operators / panels and needs a
    live Blender).
    """
    if "blender" in sys.modules:
        return
    pkg = types.ModuleType("blender")
    pkg.__path__ = [str(_BLENDER_ROOT)]  # type: ignore[attr-defined]
    sys.modules["blender"] = pkg


class _AutoTypes(types.ModuleType):
    """``bpy.types`` substitute that creates a class for any name.

    Every attribute access returns (and caches) a fresh empty class, so
    both the ``isinstance`` narrowing helpers (``expect_mesh`` /
    ``expect_armature``) and the ``cast(Iterator[bpy.types.X], ...)`` shims
    resolve for whatever type name the writer references at call time.
    Caching keeps class identity stable so repeated isinstance checks agree.
    """

    def __getattr__(self, name: str) -> type:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        cls = type(name, (), {})
        setattr(self, name, cls)
        return cls


def _install_bpy_stub() -> None:
    """Register a minimal ``bpy`` module so the writer chain imports.

    Installed unconditionally (overwriting any earlier stand-in, e.g. the
    ``MagicMock`` another suite installs): the writer modules capture
    whatever ``sys.modules['bpy']`` holds when they import, which is right
    after this conftest runs. Suites collected earlier already captured
    their own ``bpy`` by reference, so the overwrite does not reach them.
    """
    bpy = types.ModuleType("bpy")

    types_mod = _AutoTypes("bpy.types")
    bpy.types = types_mod  # type: ignore[attr-defined]

    path_mod = types.ModuleType("bpy.path")
    path_mod.abspath = lambda p: p  # type: ignore[attr-defined]
    bpy.path = path_mod  # type: ignore[attr-defined]

    # Empty data collections: the bpy-bound iterators are patched per
    # test, so this is only a safety net for stray attribute access.
    bpy.data = types.SimpleNamespace(actions=[], objects=[], materials=[])  # type: ignore[attr-defined]

    sys.modules["bpy"] = bpy
    sys.modules["bpy.types"] = types_mod
    sys.modules["bpy.path"] = path_mod


def _install_mathutils_stub() -> None:
    """Register a minimal ``mathutils`` with a 3-component ``Vector``.

    Installed unconditionally for the same reason as the bpy stub: it must
    win over any earlier ``MagicMock`` so the writer captures a real
    ``Vector`` at import time.
    """
    mathutils = types.ModuleType("mathutils")

    class Vector:
        """Stand-in storing up to three components, exposing x/y/z."""

        def __init__(self, components: object = (0.0, 0.0, 0.0)) -> None:
            c = list(components)  # type: ignore[call-overload]
            self.x = float(c[0]) if len(c) > 0 else 0.0
            self.y = float(c[1]) if len(c) > 1 else 0.0
            self.z = float(c[2]) if len(c) > 2 else 0.0

        def __getitem__(self, index: int) -> float:
            return (self.x, self.y, self.z)[index]

        def __sub__(self, other: "Vector") -> "Vector":
            return Vector((self.x - other.x, self.y - other.y, self.z - other.z))

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, Vector):
                return NotImplemented
            return (self.x, self.y, self.z) == (other.x, other.y, other.z)

    mathutils.Vector = Vector  # type: ignore[attr-defined]
    sys.modules["mathutils"] = mathutils


_install_bpy_stub()
_install_mathutils_stub()
_install_addon_root_package()
