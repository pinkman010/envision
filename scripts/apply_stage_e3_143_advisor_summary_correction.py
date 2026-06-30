"""Correct computed summary counts for the Stage E3 143-item final Advisor output."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _write_json  # noqa: E402
from scripts.run_stage_e3_143_unified_final_advisor import validate_final_advisor_result  # noqa: E402

DEFAULT_RUN_DIR = (
    PROJECT_ROOT
    / "data"
    / "runs"
    / "stage_e_final_advisor"
    / "20260630T114005Z_e3_143_unified_final_advisor"
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _accepted_assessment_ids(run_summary: dict[str, Any]) -> set[str]:
    accepted_set_path = Path(str(run_summary["accepted_assessment_set"]))
    accepted_set = _load_json(accepted_set_path)
    return {
        str(item.get("manifest_item_id", ""))
        for item in accepted_set.get("assessments", [])
        if isinstance(item, dict)
    }


def correct_final_advisor_summary(run_dir: Path = DEFAULT_RUN_DIR) -> dict[str, Any]:
    advisor_path = run_dir / "final_advisor_result.json"
    run_summary_path = run_dir / "run_summary.json"
    if not advisor_path.exists():
        raise FileNotFoundError(f"Final advisor result not found: {advisor_path}")
    if not run_summary_path.exists():
        raise FileNotFoundError(f"run_summary.json not found: {run_summary_path}")

    run_summary = _load_json(run_summary_path)
    assessment_ids = _accepted_assessment_ids(run_summary)
    raw_advisor = _load_json(advisor_path)
    recommendations = [
        item for item in raw_advisor.get("p0_recommendations", []) if isinstance(item, dict)
    ]

    corrected = copy.deepcopy(raw_advisor)
    corrected_summary = corrected.setdefault("summary", {})
    corrected_summary["total_recommendations"] = len(recommendations)
    corrected_summary["manual_review_recommendations"] = sum(
        1 for item in recommendations if item.get("recommendation_type") == "manual_review"
    )
    corrected_summary["high_priority_count"] = sum(
        1 for item in recommendations if item.get("priority") == "high"
    )
    corrected["correction_metadata"] = {
        "corrected_at": datetime.now(timezone.utc).isoformat(),
        "correction_type": "advisor_summary_count_recalculation",
        "source_file": str(advisor_path),
        "changed_fields": [
            "summary.total_recommendations",
            "summary.manual_review_recommendations",
            "summary.high_priority_count",
        ],
    }

    corrected_path = run_dir / "final_advisor_result_corrected.json"
    validation_path = run_dir / "advisor_validation_result_corrected.json"
    _write_json(corrected_path, corrected)
    validation = validate_final_advisor_result(corrected, assessment_ids)
    _write_json(validation_path, validation)

    run_summary["raw_final_advisor_result_status"] = "superseded_by_summary_count_correction"
    run_summary["effective_final_advisor_result"] = str(corrected_path)
    run_summary["final_advisor_result_corrected"] = str(corrected_path)
    run_summary["advisor_validation_result_corrected"] = str(validation_path)
    run_summary["advisor_validation_status_after_correction"] = validation["status"]
    run_summary["advisor_validation_warnings_after_correction"] = validation.get("warnings", [])
    run_summary["advisor_validation_errors_after_correction"] = validation.get("errors", [])
    run_summary["recommendation_count_after_correction"] = validation["recommendation_count"]
    run_summary["warnings"] = validation.get("warnings", [])
    run_summary["errors"] = validation.get("errors", [])
    if validation["status"] == "ok":
        run_summary["status"] = "completed"
    _write_json(run_summary_path, run_summary)

    result = {
        "status": validation["status"],
        "run_dir": str(run_dir),
        "final_advisor_result_corrected": str(corrected_path),
        "advisor_validation_result_corrected": str(validation_path),
        "recommendation_count": validation["recommendation_count"],
        "validation_error_count": len(validation.get("errors", [])),
        "validation_warning_count": len(validation.get("warnings", [])),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Correct Stage E3 143-item final Advisor summary counts.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args(argv)
    result = correct_final_advisor_summary(args.run_dir)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
