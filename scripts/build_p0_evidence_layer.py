"""Build Stage C P0 GRI requirement and report evidence manifests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.utils.evidence_layer_utils import build_and_write_p0_evidence_layer


def main() -> int:
    try:
        summary = build_and_write_p0_evidence_layer()
    except Exception as exc:  # pragma: no cover - command-line guard
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
