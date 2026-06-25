r"""
验证 P0 Analysis Contract 是否可读取、可校验、可序列化。

运行：
    C:\ProgramData\miniconda3\envs\envision\python.exe scripts\validate_p0_contract.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models import AnalysisMode, AnalysisRun  # noqa: E402
from src.utils.manifest_utils import (  # noqa: E402
    build_empty_p0_analysis_run,
    load_p0_disclosure_items,
    load_p0_source_documents,
    validate_p0_manifest_contract,
)


def main() -> int:
    validation = validate_p0_manifest_contract()
    current_gap_items = load_p0_disclosure_items(AnalysisMode.CURRENT_GAP)
    source_documents = load_p0_source_documents()
    analysis_run = build_empty_p0_analysis_run()

    run_payload = analysis_run.model_dump(mode="json")
    AnalysisRun.model_validate(run_payload)

    errors = list(validation["errors"])
    analysis_run_id_startswith_expected_prefix = analysis_run.run_id.startswith("analysis_run_")
    if not analysis_run_id_startswith_expected_prefix:
        errors.append("AnalysisRun.run_id does not start with analysis_run_")
    if len(source_documents) != 2:
        errors.append(f"source_documents expected 2, got {len(source_documents)}")

    status = "ok" if validation["status"] == "ok" and not errors else "failed"

    result = {
        "status": status,
        "manifest_version": validation["manifest_version"],
        "total_disclosures": validation["total_disclosures"],
        "counts": validation["counts"],
        "current_gap": validation["current_gap"],
        "readiness_2026": validation["readiness_2026"],
        "watchlist_2027": validation["watchlist_2027"],
        "current_gap_items_loaded": len(current_gap_items),
        "source_documents_loaded": len(source_documents),
        "source_documents_match_manifest": validation["source_documents_match_manifest"],
        "manifest_item_ids_unique": validation["manifest_item_ids_unique"],
        "current_gap_canonical_ids_unique": validation["current_gap_canonical_ids_unique"],
        "has_405_2_typo": validation["has_405_2_typo"],
        "has_414_2_typo": validation["has_414_2_typo"],
        "has_3_3_scope_marker": validation["has_3_3_scope_marker"],
        "analysis_run_serializable": True,
        "analysis_run_id_startswith_expected_prefix": analysis_run_id_startswith_expected_prefix,
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())