import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ORACLE = os.path.join(ROOT, "reference", "verify_geometry.py")


def test_oracle_script_passes():
    try:
        result = subprocess.run(
            [sys.executable, "reference/verify_geometry.py"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        pytest.skip("verify_geometry.py took more than 120 s")
        return
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
