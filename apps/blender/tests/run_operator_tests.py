"""Headless operator pytest entry (SPEC 013.2 bind, Q7).

Invoke from the repository root:

    blender --background --python apps/blender/tests/run_operator_tests.py

Runs pytest on apps/blender/tests/operators/ INSIDE Blender so
``bpy.ops.proscenio.*`` operators register + execute end-to-end.
Exits non-zero on any test failure. This is the NEW test layer
SPEC 013.2 bind introduces; paint / sidecar / modal waves reuse
the same pattern.
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
            "\"import ensurepip; ensurepip.bootstrap(); import subprocess, sys; "
            "subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest'])\"",
            file=sys.stderr,
        )
        return 1
    return int(pytest.main([str(OPERATOR_TESTS_DIR), "-v", "-x"]))


if __name__ == "__main__":
    sys.exit(main())
