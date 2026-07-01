"""Run the unified final Advisor for the accepted 143-item Stage E3 set."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").exists())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.archive_stage_e.run_p0_stage_e1_real_run import _write_json, _write_text  # noqa: E402
from scripts.validate_stage_e3_batch_outputs import FORBIDDEN_ADVISOR_PHRASES  # noqa: E402
from src.agent.advisor_agent import AdvisorAgent  # noqa: E402
from src.config import settings  # noqa: E402

DEFAULT_ACCEPTED_SUMMARY = PROJECT_ROOT / "docs" / "stage_e3" / "e3_final_current_effective_assessment_set.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e_final_advisor"
DEFAULT_DOC_OUTPUT = PROJECT_ROOT / "docs" / "stage_e3" / "e3_final_advisor_invocation_approval.md"
ACCEPTED_SET_STATUS = "accepted_effective_input_for_unified_final_advisor"
ALLOWED_RECOMMENDATION_TYPES = {
    "report_content_improvement",
    "internal_management_followup",
    "manual_review",
    "no_action",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_accepted_set_path(summary_or_set_path: Path) -> Path:
    payload = _load_json(summary_or_set_path)
    if "assessments" in payload:
        return summary_or_set_path
    path_value = payload.get("run_dir")
    if not path_value:
        raise ValueError(f"Accepted summary missing run_dir: {summary_or_set_path}")
    accepted_path = Path(path_value) / "final_current_effective_assessment_set.json"
    if not accepted_path.exists():
        raise FileNotFoundError(f"Accepted assessment set not found: {accepted_path}")
    return accepted_path


def _advisor_text(advisor_result: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("overall_recommendation", "generated_content"):
        value = advisor_result.get(key)
        if value:
            parts.append(str(value))
    for item in advisor_result.get("p0_recommendations", []):
        parts.append(json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item))
    return "\n".join(parts)


def _validate_assessment_set(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    if payload.get("status") != ACCEPTED_SET_STATUS:
        raise ValueError(f"Accepted set status must be {ACCEPTED_SET_STATUS}, got {payload.get('status')}")
    assessments = [item for item in payload.get("assessments", []) if isinstance(item, dict)]
    if len(assessments) != 143:
        raise ValueError(f"Expected 143 assessments, got {len(assessments)}")
    ids = [str(item.get("manifest_item_id", "")) for item in assessments]
    duplicates = sorted([item for item, count in Counter(ids).items() if count > 1])
    if duplicates:
        raise ValueError(f"Duplicate manifest_item_id in final Advisor input: {duplicates}")
    if "current_gap:GRI3:3-3_generic" in ids:
        raise ValueError("3-3_generic must not enter final Advisor input")
    non_current = sorted(item for item in ids if not item.startswith("current_gap:"))
    if non_current:
        raise ValueError(f"Final Advisor input contains non-current scope ids: {non_current[:10]}")
    return assessments, dict(Counter(str(item.get("verdict", "")) for item in assessments))


def _sanitize_assessment_for_advisor(assessment: dict[str, Any]) -> dict[str, Any]:
    result = {
        "manifest_item_id": assessment.get("manifest_item_id"),
        "standard_id": assessment.get("standard_id"),
        "canonical_disclosure_id": assessment.get("canonical_disclosure_id"),
        "assessment_mode": assessment.get("assessment_mode"),
        "verdict": assessment.get("verdict"),
        "confidence": assessment.get("confidence"),
        "aggregation_reason": assessment.get("aggregation_reason", ""),
        "rationale": assessment.get("rationale", ""),
        "missing_requirements": assessment.get("missing_requirements", []),
        "not_applicable_requirements": assessment.get("not_applicable_requirements", []),
        "manual_review_requirements": assessment.get("manual_review_requirements", []),
        "manual_review_reason_codes": assessment.get("manual_review_reason_codes", []),
        "readiness_verdict": assessment.get("readiness_verdict"),
        "evidence": [
            {"evidence_kind": evidence.get("evidence_kind")}
            for evidence in assessment.get("evidence", [])
            if isinstance(evidence, dict)
        ],
        "requirement_checks": [],
    }
    for check in assessment.get("requirement_checks", []):
        if not isinstance(check, dict):
            continue
        result["requirement_checks"].append(
            {
                "requirement_id": check.get("requirement_id"),
                "support_status": check.get("support_status"),
                "missing_reason": check.get("missing_reason", ""),
                "manual_review_reason": check.get("manual_review_reason", ""),
            }
        )
    return result


def validate_final_advisor_result(
    advisor_result: dict[str, Any],
    assessment_ids: set[str],
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if advisor_result.get("status") != "completed":
        errors.append("advisor_result.status must be completed")
    recommendations = advisor_result.get("p0_recommendations")
    if not isinstance(recommendations, list):
        errors.append("advisor_result.p0_recommendations must be a list")
        recommendations = []
    if not recommendations:
        errors.append("advisor_result.p0_recommendations must not be empty for the 143-item final set")

    text = _advisor_text(advisor_result)
    for phrase in FORBIDDEN_ADVISOR_PHRASES:
        if phrase in text:
            errors.append(f"advisor_result contains forbidden internal absence inference phrase: {phrase}")

    required_fields = {
        "manifest_item_id",
        "canonical_disclosure_id",
        "requirement_id",
        "recommendation_type",
        "priority",
        "current_disclosure",
        "gap",
        "next_report_addition",
        "requires_internal_data",
        "recommendation",
        "basis",
        "review_status",
    }
    for index, item in enumerate(recommendations):
        if not isinstance(item, dict):
            errors.append(f"p0_recommendations[{index}] must be an object")
            continue
        missing = sorted(field for field in required_fields if field not in item)
        if missing:
            errors.append(f"p0_recommendations[{index}] missing fields: {missing}")
        manifest_item_id = str(item.get("manifest_item_id", ""))
        if manifest_item_id and manifest_item_id not in assessment_ids:
            errors.append(f"p0_recommendations[{index}] references unknown manifest_item_id: {manifest_item_id}")
        recommendation_type = str(item.get("recommendation_type", ""))
        if recommendation_type and recommendation_type not in ALLOWED_RECOMMENDATION_TYPES:
            errors.append(
                f"p0_recommendations[{index}] invalid recommendation_type: {recommendation_type}"
            )
        if item.get("review_status") not in {None, "pending"}:
            warnings.append(f"p0_recommendations[{index}] review_status is not pending")

    summary = advisor_result.get("summary")
    if not isinstance(summary, dict):
        warnings.append("advisor_result.summary is missing or not an object")
    elif summary.get("total_recommendations") != len(recommendations):
        warnings.append("advisor_result.summary.total_recommendations does not match p0_recommendations length")

    return {
        "status": "ok" if not errors else "failed",
        "mode": "stage_e3_143_unified_final_advisor",
        "recommendation_count": len(recommendations),
        "errors": errors,
        "warnings": warnings,
    }


def _approval_markdown(
    *,
    run_dir: Path,
    accepted_set_path: Path,
    assessment_count: int,
    verdict_distribution: dict[str, int],
    llm_called: bool,
    validation_status: str | None = None,
    recommendation_count: int | None = None,
) -> str:
    status_line = (
        "DeepSeek API has been called for the accepted 143-item final current disclosure set."
        if llm_called
        else "Local 143-assessment final Advisor input package prepared; DeepSeek API not called."
    )
    lines = [
        "# E3 143-Item Unified Final Advisor Invocation",
        "",
        "## Status",
        "",
        f"- {status_line}",
        "- E3.5 reviewed artifacts are accepted as effective input.",
        "- Input includes 114 ordinary current-gap assessments and 29 GRI 3-3 index-row assessments.",
        "",
        "## Send Scope",
        "",
        f"- Accepted current assessment units: {assessment_count}",
        "- Advisor input is reduced to assessment fields, requirement checks, and evidence kinds rendered by `advisor_prompt.j2`.",
        "- No `.env`, API keys, raw PDFs, or non-public internal data.",
        "",
        "## Local Artifacts",
        "",
        f"- Accepted set: `{accepted_set_path}`",
        f"- Advisor run directory: `{run_dir}`",
        "- Input file: `final_effective_analyst_input.json`",
        "- Output file: `final_advisor_result.json`",
        "",
        "## Verdict Distribution",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in sorted(verdict_distribution.items()))
    lines.extend(
        [
            "",
            "## Config Snapshot",
            "",
            f"- `LLM_MODEL`: `{settings.LLM_MODEL}`",
            f"- `LLM_BASE_URL`: `{settings.LLM_BASE_URL}`",
            f"- `LLM_THINKING_TYPE`: `{settings.LLM_THINKING_TYPE}`",
            f"- `LLM_REASONING_EFFORT`: `{settings.LLM_REASONING_EFFORT}`",
            f"- `LLM_RESPONSE_FORMAT`: `{settings.LLM_RESPONSE_FORMAT or ''}`",
            "",
            "## Validation",
            "",
            f"- Advisor validation status: `{validation_status or 'not_run'}`",
            f"- Recommendation count: `{recommendation_count if recommendation_count is not None else 'not_run'}`",
            "",
            "## Risk",
            "",
            "- Advisor output remains AI-assisted and must be treated as pending review until final human evaluation.",
            "- Recommendations may describe public-report disclosure gaps only; internal management claims require internal confirmation.",
        ]
    )
    return "\n".join(lines) + "\n"


def run_unified_final_advisor(
    *,
    accepted_summary_or_set_path: Path = DEFAULT_ACCEPTED_SUMMARY,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    approval_doc_path: Path = DEFAULT_DOC_OUTPUT,
    confirm_llm: bool = False,
) -> dict[str, Any]:
    accepted_set_path = _resolve_accepted_set_path(accepted_summary_or_set_path)
    accepted_payload = _load_json(accepted_set_path)
    assessments, verdict_distribution = _validate_assessment_set(accepted_payload)
    assessment_ids = {str(item.get("manifest_item_id", "")) for item in assessments}

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_143_unified_final_advisor")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    sanitized_assessments = [_sanitize_assessment_for_advisor(item) for item in assessments]
    analyst_result = {
        "p0_contract_version": "p0_stage_e3_143_unified_final_analyst_result_v1",
        "disclosure_assessments": sanitized_assessments,
        "overall_assessment": (
            "Unified final Advisor input built from 143 accepted current disclosure assessment units: "
            "114 ordinary current-gap assessments plus 29 GRI 3-3 index-row assessments."
        ),
        "summary": {
            "run_mode": "stage_e3_143_unified_final_advisor_input",
            "assessment_count": len(sanitized_assessments),
            "verdict_distribution": verdict_distribution,
            "accepted_assessment_set": str(accepted_set_path),
            "llm_called": bool(confirm_llm),
        },
    }
    _write_json(run_dir / "final_effective_analyst_input.json", analyst_result)

    base_summary = {
        "status": "prepared",
        "run_id": run_id,
        "run_mode": "stage_e3_143_unified_final_advisor",
        "run_dir": str(run_dir),
        "accepted_assessment_set": str(accepted_set_path),
        "assessment_count": len(sanitized_assessments),
        "verdict_distribution": verdict_distribution,
        "llm_called": False,
        "errors": [],
        "warnings": [],
    }
    _write_json(run_dir / "run_summary.json", base_summary)
    _write_text(
        approval_doc_path,
        _approval_markdown(
            run_dir=run_dir,
            accepted_set_path=accepted_set_path,
            assessment_count=len(sanitized_assessments),
            verdict_distribution=verdict_distribution,
            llm_called=False,
        ),
    )

    result: dict[str, Any] = {
        "status": "prepared",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "accepted_assessment_set": str(accepted_set_path),
        "assessment_count": len(sanitized_assessments),
        "llm_called": False,
    }
    if not confirm_llm:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    advisor_result = AdvisorAgent().run({"analyst_result": analyst_result}, task_id=f"{run_id}_advisor")
    advisor_path = run_dir / "final_advisor_result.json"
    advisor_raw_path = run_dir / "final_advisor_raw_llm_output.txt"
    _write_json(advisor_path, advisor_result)
    _write_text(advisor_raw_path, str(advisor_result.get("raw_llm_output", "")))

    validation = validate_final_advisor_result(advisor_result, assessment_ids)
    validation_path = run_dir / "advisor_validation_result.json"
    _write_json(validation_path, validation)
    summary = _load_json(run_dir / "run_summary.json")
    summary.update(
        {
            "status": "completed" if validation["status"] == "ok" else "completed_with_validation_errors",
            "llm_called": True,
            "model": settings.LLM_MODEL,
            "base_url": settings.LLM_BASE_URL,
            "final_advisor_result": str(advisor_path),
            "final_advisor_raw_llm_output": str(advisor_raw_path),
            "advisor_validation_result": str(validation_path),
            "advisor_validation_status": validation["status"],
            "recommendation_count": validation["recommendation_count"],
            "errors": validation.get("errors", []),
            "warnings": validation.get("warnings", []),
        }
    )
    _write_json(run_dir / "run_summary.json", summary)
    _write_text(
        approval_doc_path,
        _approval_markdown(
            run_dir=run_dir,
            accepted_set_path=accepted_set_path,
            assessment_count=len(sanitized_assessments),
            verdict_distribution=verdict_distribution,
            llm_called=True,
            validation_status=validation["status"],
            recommendation_count=validation["recommendation_count"],
        ),
    )
    result.update(
        {
            "status": summary["status"],
            "llm_called": True,
            "final_advisor_result": str(advisor_path),
            "advisor_validation_result": str(validation_path),
            "advisor_validation_status": validation["status"],
            "recommendation_count": validation["recommendation_count"],
            "validation_error_count": len(validation.get("errors", [])),
        }
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage E3 unified final Advisor for accepted 143-item set.")
    parser.add_argument("--accepted-summary-or-set", type=Path, default=DEFAULT_ACCEPTED_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--approval-doc", type=Path, default=DEFAULT_DOC_OUTPUT)
    parser.add_argument("--confirm-llm", action="store_true", help="Call the configured external LLM.")
    args = parser.parse_args(argv)
    result = run_unified_final_advisor(
        accepted_summary_or_set_path=args.accepted_summary_or_set,
        output_dir=args.output_dir,
        approval_doc_path=args.approval_doc,
        confirm_llm=args.confirm_llm,
    )
    if result.get("status") == "completed_with_validation_errors":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
