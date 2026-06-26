"""Inspect Stage C2 GRI locator refinement results."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.paths import P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH, P0_GRI_REQUIREMENT_PACK_PATH
from src.models import GRIRequirementPack


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    pack = GRIRequirementPack.model_validate(_load_json(P0_GRI_REQUIREMENT_PACK_PATH))
    audit = _load_json(P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH)
    review_items = audit.get("locator_review_required", [])
    result = {
        "requirements": len(pack.requirements),
        "locator_counts": audit.get("locator_counts", {}),
        "locator_review_required_count": len(review_items),
        "locator_review_required_sample": review_items[:20],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
