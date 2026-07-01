from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_RUNTIME = PROJECT_ROOT / "vendor" / "python_runtime"
if VENDOR_RUNTIME.exists():
    sys.path.insert(0, str(VENDOR_RUNTIME))

from src.config.settings import settings


def main() -> int:
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
