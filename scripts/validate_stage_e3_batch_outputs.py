"""Validate Stage E3 batch output artifacts without calling external services."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.models.analysis_contract import AnalysisRun  # noqa: E402

REQUIRED_FILES = {
    "retrieval_result.json",
    "analyst_result.json",
    "advisor_result.json",
    "analysis_run.json",
    "manual_review_input.json",
    "manual_review_result_template.json",
    "smoke_review_template.json",
    "batch_scope_manifest.json",
    "run_summary.json",
}
POSITIVE_VERDICTS = {"disclosed", "partially_disclosed"}
NON_INDEX_EVIDENCE_KINDS = {
    "substantive_report_evidence",
    "omission_or_not_applicable_explanation",
    "external_reference_evidence",
}
BODY_EVIDENCE_KINDS = {"substantive_report_evidence", "external_reference_evidence"}
FORBIDDEN_ADVISOR_PHRASES = [
    "企业未建立",
    "企业没有建立",
    "企业没有",
    "企业缺乏内部管理",
    "内部不存在",
]
ALLOWED_SMOKE_GATE_STATUSES = {
    "blocked_before_batch_02",
    "blocked_before_batch_05_required_field_corrections",
    "blocked_before_e3_current_scope_acceptance_required_field_corrections",
    "passed_after_corrections",
    "passed_before_batch_03",
    "passed_before_batch_04_with_minor_requirement_granularity_issue",
}
ALLOWED_E3_RUN_MODES = {
    "stage_e3_batch",
    "stage_e3_batch_split_merged",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _selected_ids(run_dir: Path) -> list[str]:
    payload = _load_json(run_dir / "batch_scope_manifest.json")
    return [str(item) for item in _as_list(payload.get("selected_manifest_item_ids"))]


def _assessment_label(assessment: dict[str, Any], index: int) -> str:
    return str(assessment.get("manifest_item_id") or assessment.get("assessment_id") or f"assessment[{index}]")


def _has_non_index_evidence(assessment: dict[str, Any]) -> bool:
    return any(
        isinstance(evidence, dict) and str(evidence.get("evidence_kind", "")) in NON_INDEX_EVIDENCE_KINDS
        for evidence in _as_list(assessment.get("evidence"))
    )


def _is_body_evidence(evidence: dict[str, Any]) -> bool:
    return str(evidence.get("evidence_kind", "")) in BODY_EVIDENCE_KINDS


def _validate_body_evidence_fields(label: str, evidence: dict[str, Any], errors: list[str]) -> None:
    for field in ("source_page", "report_page_label", "source_text", "evidence_kind", "chunk_id"):
        value = evidence.get(field)
        if value is None or value == "":
            errors.append(f"{label}: body evidence missing {field}")

    source_text = str(evidence.get("source_text", ""))
    if "..." in source_text or "…" in source_text:
        errors.append(f"{label}: body evidence source_text must be verbatim, not ellipsis summary")

    source_page = evidence.get("source_page")
    report_label = str(evidence.get("report_page_label", "")).strip()
    if isinstance(source_page, int) and report_label.isdigit():
        expected_source_page = int(report_label) + 1
        if source_page != expected_source_page:
            errors.append(
                f"{label}: page offset mismatch for {evidence.get('evidence_id', '<evidence>')}: "
                f"source_page={source_page}, report_page_label={report_label}"
            )


def _advisor_text(advisor_result: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("overall_recommendation", "generated_content"):
        value = advisor_result.get(key)
        if value:
            parts.append(str(value))
    for item in _as_list(advisor_result.get("p0_recommendations")):
        if isinstance(item, dict):
            parts.append(json.dumps(item, ensure_ascii=False))
        else:
            parts.append(str(item))
    return "\n".join(parts)


def _artifact_path(run_dir: Path, corrected_name: str, raw_name: str) -> tuple[Path, bool]:
    corrected_path = run_dir / corrected_name
    if corrected_path.exists():
        return corrected_path, True
    return run_dir / raw_name, False


def _validate_smoke_review_result(run_dir: Path, errors: list[str], expected_item_count: int) -> bool:
    smoke_result_path = run_dir / "smoke_review_result.json"
    if not smoke_result_path.exists():
        errors.append("smoke_review_result.json is required after smoke review")
        return False
    payload = _load_json(smoke_result_path)
    if payload.get("review_status") != "completed":
        errors.append("smoke_review_result.review_status must be completed")
    if payload.get("gate_status") not in ALLOWED_SMOKE_GATE_STATUSES:
        errors.append(
            "smoke_review_result.gate_status must be one of "
            f"{sorted(ALLOWED_SMOKE_GATE_STATUSES)}"
        )
    items = _as_list(payload.get("items"))
    if len(items) != expected_item_count:
        errors.append(f"smoke_review_result.items must contain {expected_item_count} smoke review items")
    for item in items:
        if not isinstance(item, dict):
            errors.append("smoke_review_result.items entries must be objects")
            continue
        for field in ("manifest_item_id", "model_verdict", "human_verdict", "issue_types"):
            if field not in item:
                errors.append(f"smoke_review_result item missing {field}")
    return True


def validate_run_dir(run_dir: Path, require_smoke_review_result: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    missing_files = sorted(filename for filename in REQUIRED_FILES if not (run_dir / filename).exists())
    if missing_files:
        return {
            "status": "failed",
            "mode": "stage_e3_batch_run_dir",
            "run_dir": str(run_dir),
            "errors": [f"missing required output files: {missing_files}"],
            "warnings": warnings,
        }

    run_summary = _load_json(run_dir / "run_summary.json")
    analysis_path, corrected_analysis_used = _artifact_path(run_dir, "analysis_run_corrected.json", "analysis_run.json")
    analyst_path, corrected_analyst_used = _artifact_path(run_dir, "analyst_result_corrected.json", "analyst_result.json")
    advisor_path, corrected_advisor_used = _artifact_path(run_dir, "advisor_result_corrected.json", "advisor_result.json")
    analysis_run_payload = _load_json(analysis_path)
    analyst_result = _load_json(analyst_path)
    advisor_result = _load_json(advisor_path)
    retrieval_result = _load_json(run_dir / "retrieval_result.json")
    selected_ids = _selected_ids(run_dir)

    if run_summary.get("status") != "ok":
        errors.append("run_summary.status must be ok")
    if run_summary.get("run_mode") not in ALLOWED_E3_RUN_MODES:
        errors.append(f"run_summary.run_mode must be one of {sorted(ALLOWED_E3_RUN_MODES)}")
    if retrieval_result.get("retrieval_summary", {}).get("run_mode") not in ALLOWED_E3_RUN_MODES:
        errors.append(
            "retrieval_result.retrieval_summary.run_mode must be one of "
            f"{sorted(ALLOWED_E3_RUN_MODES)}"
        )

    try:
        analysis_run = AnalysisRun.model_validate(analysis_run_payload)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"analysis_run schema validation failed: {type(exc).__name__}: {exc}")
        analysis_run = None

    assessments = [item for item in _as_list(analyst_result.get("disclosure_assessments")) if isinstance(item, dict)]
    if not assessments:
        errors.append("analyst_result.disclosure_assessments must be non-empty")
    if len(assessments) != len(selected_ids):
        errors.append(f"assessment count {len(assessments)} does not match selected id count {len(selected_ids)}")
    if run_summary.get("assessment_count") != len(assessments):
        errors.append("run_summary.assessment_count does not match analyst_result")
    if analysis_run is not None and len(analysis_run.assessments) != len(assessments):
        errors.append("analysis_run.assessments count does not match analyst_result")

    assessment_ids = {str(item.get("manifest_item_id", "")) for item in assessments}
    selected_id_set = set(selected_ids)
    if assessment_ids != selected_id_set:
        errors.append(
            "assessment manifest_item_ids do not match selected scope: "
            f"missing={sorted(selected_id_set - assessment_ids)}, unexpected={sorted(assessment_ids - selected_id_set)}"
        )

    for index, assessment in enumerate(assessments):
        label = _assessment_label(assessment, index)
        verdict = str(assessment.get("verdict", ""))
        if assessment.get("assessment_mode") != "current_gap":
            errors.append(f"{label}: assessment_mode must be current_gap")
        if label == "current_gap:GRI3:3-3_generic":
            errors.append(f"{label}: 3-3_generic must not enter ordinary E3 batch scoring")

        if verdict in POSITIVE_VERDICTS and not _has_non_index_evidence(assessment):
            errors.append(f"{label}: {verdict} cannot be supported by index_evidence alone")
        if verdict == "partially_disclosed" and not (
            _as_list(assessment.get("missing_requirements")) or _as_list(assessment.get("partial_requirements"))
        ):
            errors.append(f"{label}: partially_disclosed requires missing_requirements or partial_requirements")
        if verdict == "manual_review" and not _as_list(assessment.get("manual_review_reason_codes")):
            errors.append(f"{label}: manual_review requires manual_review_reason_codes")

        for evidence in _as_list(assessment.get("evidence")):
            if not isinstance(evidence, dict) or not _is_body_evidence(evidence):
                continue
            _validate_body_evidence_fields(label, evidence, errors)

    advisor_text = _advisor_text(advisor_result)
    for phrase in FORBIDDEN_ADVISOR_PHRASES:
        if phrase in advisor_text:
            errors.append(f"advisor_result contains forbidden internal absence inference phrase: {phrase}")

    smoke_items = _as_list(_load_json(run_dir / "smoke_review_template.json").get("items"))
    if not smoke_items:
        errors.append("smoke_review_template.items must be non-empty")
    if len(smoke_items) > 5:
        errors.append("smoke_review_template.items must not exceed 5 for E3 batch smoke review")
    if require_smoke_review_result:
        _validate_smoke_review_result(run_dir, errors, expected_item_count=len(smoke_items))

    return {
        "status": "ok" if not errors else "failed",
        "mode": "stage_e3_batch_run_dir",
        "run_dir": str(run_dir),
        "batch_id": run_summary.get("batch_id"),
        "assessment_count": len(assessments),
        "selected_count": len(selected_ids),
        "corrected_artifacts_used": corrected_analysis_used or corrected_analyst_used or corrected_advisor_used,
        "analysis_source_file": str(analysis_path),
        "analyst_source_file": str(analyst_path),
        "advisor_source_file": str(advisor_path),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Stage E3 batch output artifacts.")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--require-smoke-review-result", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = validate_run_dir(args.run_dir, require_smoke_review_result=args.require_smoke_review_result)
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "failed",
            "mode": "stage_e3_batch_run_dir",
            "run_dir": str(args.run_dir),
            "errors": [f"{type(exc).__name__}: {exc}"],
            "warnings": [],
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

