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


def main() -> int:
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
