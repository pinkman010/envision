"""Project-local runtime path bridge."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
VENDOR_RUNTIME = PROJECT_ROOT / "vendor" / "python_runtime"
if VENDOR_RUNTIME.exists():
    sys.path.insert(0, str(VENDOR_RUNTIME))
