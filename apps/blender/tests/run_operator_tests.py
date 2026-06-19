"""Headless operator pytest entry.

Invoke from the repository root:

    blender --background --python apps/blender/tests/run_operator_tests.py

Runs pytest on apps/blender/tests/operators/ INSIDE Blender so
``bpy.ops.proscenio.*`` operators register + execute end-to-end.
Exits non-zero on any test failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OPERATOR_TESTS_DIR = REPO_ROOT / "apps" / "blender" / "tests" / "operators"
MODELS_SRC = REPO_ROOT / "packages" / "models" / "src"


def prefer_source_models() -> None:
    """Make the in-repo ``proscenio_models`` win over the installed extension copy.

    The auto-enabled installed extension bundles a version-keyed
    ``proscenio_models`` (``0.1.0``); a pre-launch field change keeps that
    version, so Blender never re-unpacks the wheel and the stale copy lingers
    (already imported at enable). Prepend the repo source and drop the cached
    modules so the operators import the current models, matching CI's fresh
    install - without it, producer tests needing a new field would self-skip.
    """
    sys.path.insert(0, str(MODELS_SRC))
    for name in [
        m for m in sys.modules if m == "proscenio_models" or m.startswith("proscenio_models.")
    ]:
        del sys.modules[name]


def main() -> int:
    prefer_source_models()
    try:
        import pytest
    except ImportError:
        print(
            "FAIL: pytest not installed in Blender's bundled Python. "
            "Install via: blender --background --python-expr "
            '"import ensurepip; ensurepip.bootstrap(); import subprocess, sys; '
            "subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest'])\"",
            file=sys.stderr,
        )
        return 1
    # Forward any args passed after Blender's "--" separator to pytest
    # (e.g. `blender ... -- -k automesh` filters the run).
    extra = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return int(pytest.main([str(OPERATOR_TESTS_DIR), "-v", "-x", *extra]))


if __name__ == "__main__":
    sys.exit(main())
