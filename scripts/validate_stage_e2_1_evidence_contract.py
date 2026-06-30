"""Validate the Stage E2.1 evidence contract.

This script performs local structure checks only. It does not call LLMs,
rebuild indexes, import model clients, or write run artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_REGRESSION_MANIFEST_PATH = (
    PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_stage_e2_regression_manifest.json"
)
DEFAULT_REQUIREMENT_CHECKLIST_PATH = (
    PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_gri_requirement_checklist.json"
)

REQUIRED_REGRESSION_ITEM_IDS = {
    "current_gap:GRI2:2-1",
    "current_gap:GRI302:302-4",
    "current_gap:GRI3:3-3_generic",
}
GENERIC_3_3_PARENT_ID = "current_gap:GRI3:3-3_generic"
E2_1_D_BODY_EVIDENCE_REQUIRED_IDS = {
    "current_gap:GRI2:2-1",
    "current_gap:GRI302:302-4",
    "current_gap:GRI306:306-4",
    "current_gap:GRI401:401-1",
}

DISCLOSED = "disclosed"
PARTIALLY_DISCLOSED = "partially_disclosed"
NOT_APPLICABLE = "not_applicable"
MANUAL_REVIEW = "manual_review"
PENDING_REVIEW = "pending"

INDEX_EVIDENCE = "index_evidence"
SUBSTANTIVE_EVIDENCE = "substantive_report_evidence"
OMISSION_EXPLANATION = "omission_or_not_applicable_explanation"
EXTERNAL_REFERENCE_EVIDENCE = "external_reference_evidence"
NON_INDEX_EVIDENCE_KINDS = {
    SUBSTANTIVE_EVIDENCE,
    OMISSION_EXPLANATION,
    EXTERNAL_REFERENCE_EVIDENCE,
}

BODY_EVIDENCE_KINDS = {
    SUBSTANTIVE_EVIDENCE,
    EXTERNAL_REFERENCE_EVIDENCE,
}
MET = "met"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _extract_assessments(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("disclosure_assessments", "assessments", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _assessment_label(assessment: dict[str, Any], index: int) -> str:
    return str(assessment.get("manifest_item_id") or assessment.get("assessment_id") or f"assessment[{index}]")


def _evidence_kinds(assessment: dict[str, Any]) -> list[str]:
    kinds: list[str] = []
    for evidence in _as_list(assessment.get("evidence")):
        if isinstance(evidence, dict):
            kinds.append(str(evidence.get("evidence_kind", "")))
    return kinds


def _mandatory_checks(assessment: dict[str, Any]) -> list[dict[str, Any]]:
    checks = _as_list(assessment.get("requirement_checks"))
    return [
        check
        for check in checks
        if isinstance(check, dict) and check.get("is_mandatory") is True
    ]


def _mandatory_requirement_ids_by_parent(checklist_path: Path = DEFAULT_REQUIREMENT_CHECKLIST_PATH) -> tuple[dict[str, set[str]], list[str]]:
    warnings: list[str] = []
    try:
        checklist = _load_json(checklist_path)
    except Exception as exc:  # noqa: BLE001
        return {}, [f"Checklist mandatory coverage cross-check skipped: {exc}"]

    by_parent: dict[str, set[str]] = {}
    for item in _as_list(checklist.get("requirements") if isinstance(checklist, dict) else []):
        if not isinstance(item, dict):
            continue
        if item.get("assessment_mode") != "current_gap":
            continue
        if item.get("is_mandatory") is not True:
            continue
        if item.get("scoring_role", "hard_score") != "hard_score":
            continue
        parent_id = str(item.get("parent_requirement_id", ""))
        requirement_id = str(item.get("requirement_id", ""))
        if parent_id and requirement_id:
            by_parent.setdefault(parent_id, set()).add(requirement_id)
    return by_parent, warnings


def _checked_requirement_ids(assessment: dict[str, Any]) -> set[str]:
    return {
        str(check.get("requirement_id"))
        for check in _as_list(assessment.get("requirement_checks"))
        if isinstance(check, dict) and check.get("requirement_id")
    }

def _has_needs_topic_instantiation_reason(assessment: dict[str, Any]) -> bool:
    text_fields = [
        assessment.get("aggregation_reason"),
        assessment.get("rationale"),
    ]
    text_fields.extend(_as_list(assessment.get("manual_review_requirements")))
    for check in _as_list(assessment.get("requirement_checks")):
        if isinstance(check, dict):
            text_fields.append(check.get("manual_review_reason"))
            text_fields.append(check.get("missing_reason"))
    return any("needs_topic_instantiation" in str(value) for value in text_fields if value is not None)


def _blocked_verdicts_by_item(manifest_path: Path = DEFAULT_REGRESSION_MANIFEST_PATH) -> tuple[dict[str, set[str]], list[str]]:
    warnings: list[str] = []
    blocked: dict[str, set[str]] = {}
    try:
        manifest = _load_json(manifest_path)
    except Exception as exc:  # noqa: BLE001
        return blocked, [f"Regression blocked verdict cross-check skipped: {exc}"]

    for item in _as_list(manifest.get("regression_items") if isinstance(manifest, dict) else []):
        if not isinstance(item, dict):
            continue
        manifest_item_id = item.get("manifest_item_id")
        if not manifest_item_id:
            continue
        blocked[str(manifest_item_id)] = {str(verdict) for verdict in _as_list(item.get("blocked_verdicts"))}
    return blocked, warnings


def validate_assessments(
    assessments: list[dict[str, Any]],
    regression_manifest_path: Path = DEFAULT_REGRESSION_MANIFEST_PATH,
    require_e2_1_d_body_evidence: bool = False,
) -> dict[str, Any]:
    """Validate E2.1 evidence aggregation rules for assessment dictionaries."""
    errors: list[str] = []
    blocked_verdicts, warnings = _blocked_verdicts_by_item(regression_manifest_path)
    mandatory_ids_by_parent, checklist_warnings = _mandatory_requirement_ids_by_parent()
    warnings.extend(checklist_warnings)

    for index, assessment in enumerate(assessments):
        label = _assessment_label(assessment, index)
        verdict = assessment.get("verdict")
        evidence_kinds = _evidence_kinds(assessment)
        requirement_checks = _as_list(assessment.get("requirement_checks"))
        missing_requirements = _as_list(assessment.get("missing_requirements"))
        blocked_for_item = blocked_verdicts.get(label, set())

        if verdict in blocked_for_item:
            errors.append(f"{label}: verdict {verdict} is blocked by E2 regression blocked_verdicts")
        if require_e2_1_d_body_evidence and label in E2_1_D_BODY_EVIDENCE_REQUIRED_IDS:
            if not any(kind in BODY_EVIDENCE_KINDS for kind in evidence_kinds):
                errors.append(f"{label}: requires non-index body evidence candidate for E2.1-D")

        if verdict == DISCLOSED:
            if not requirement_checks:
                errors.append(f"{label}: disclosed requires requirement_checks")
            if not any(kind in NON_INDEX_EVIDENCE_KINDS for kind in evidence_kinds):
                errors.append(f"{label}: index_evidence alone cannot support disclosed")
            missing_check_ids = sorted(mandatory_ids_by_parent.get(label, set()) - _checked_requirement_ids(assessment))
            if missing_check_ids:
                errors.append(f"{label}: missing mandatory requirement checks: {missing_check_ids[:10]}")
            hard_score_ids = mandatory_ids_by_parent.get(label, set())
            for check in _mandatory_checks(assessment):
                requirement_id = str(check.get("requirement_id", "<missing>"))
                if hard_score_ids and requirement_id not in hard_score_ids:
                    continue
                if check.get("support_status") != MET:
                    errors.append(f"{label}: mandatory requirement {requirement_id} is not met")

        if verdict == PARTIALLY_DISCLOSED and not missing_requirements:
            errors.append(f"{label}: partially_disclosed requires missing_requirements")

        if verdict == NOT_APPLICABLE:
            is_policy_excluded = assessment.get("assessment_mode") != "current_gap"
            if not is_policy_excluded and OMISSION_EXPLANATION not in evidence_kinds:
                errors.append(f"{label}: not_applicable requires omission_or_not_applicable_explanation evidence")
            if assessment.get("review_status", PENDING_REVIEW) != PENDING_REVIEW:
                errors.append(f"{label}: not_applicable review_status must default to pending manual review")

        if label == GENERIC_3_3_PARENT_ID or assessment.get("canonical_disclosure_id") == "3-3_generic":
            if verdict != MANUAL_REVIEW:
                errors.append(f"{label}: 3-3_generic must remain manual_review")
            if not _has_needs_topic_instantiation_reason(assessment):
                errors.append(f"{label}: 3-3_generic manual review reason must include needs_topic_instantiation")

    return {
        "status": "ok" if not errors else "failed",
        "mode": "assessment_contract",
        "assessment_count": len(assessments),
        "errors": errors,
        "warnings": warnings,
    }


def validate_regression_manifest(
    manifest_path: Path = DEFAULT_REGRESSION_MANIFEST_PATH,
    checklist_path: Path = DEFAULT_REQUIREMENT_CHECKLIST_PATH,
) -> dict[str, Any]:
    """Validate the local E2 regression manifest structure."""
    errors: list[str] = []
    warnings: list[str] = []

    try:
        manifest = _load_json(manifest_path)
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "failed",
            "mode": "self_check",
            "errors": [f"Could not parse regression manifest: {exc}"],
            "warnings": warnings,
        }

    regression_items = manifest.get("regression_items", [])
    if not isinstance(regression_items, list) or not regression_items:
        errors.append("regression_items must be a non-empty list")
        regression_items = []

    item_ids = {
        str(item.get("manifest_item_id"))
        for item in regression_items
        if isinstance(item, dict)
    }
    missing_required = sorted(REQUIRED_REGRESSION_ITEM_IDS - item_ids)
    if missing_required:
        errors.append(f"regression manifest missing required samples: {missing_required}")

    for item in regression_items:
        if not isinstance(item, dict):
            errors.append("regression_items entries must be objects")
            continue
        manifest_item_id = str(item.get("manifest_item_id", "<missing>"))
        if not item.get("contract_assertions"):
            errors.append(f"{manifest_item_id}: contract_assertions must be non-empty")
        if manifest_item_id in {"current_gap:GRI2:2-1", "current_gap:GRI302:302-4"}:
            blocked = set(_as_list(item.get("blocked_verdicts")))
            if DISCLOSED not in blocked:
                errors.append(f"{manifest_item_id}: disclosed must be listed in blocked_verdicts")
        if manifest_item_id == GENERIC_3_3_PARENT_ID:
            if item.get("forced_verdict") != MANUAL_REVIEW:
                errors.append(f"{GENERIC_3_3_PARENT_ID}: forced_verdict must be manual_review")
            if item.get("manual_review_reason") != "needs_topic_instantiation":
                errors.append(f"{GENERIC_3_3_PARENT_ID}: manual_review_reason must be needs_topic_instantiation")

    try:
        checklist = _load_json(checklist_path)
        checklist_parent_ids = {
            str(item.get("parent_requirement_id"))
            for item in checklist.get("requirements", [])
            if isinstance(item, dict)
        }
        topic_parent_ids = {
            str(item.get("parent_requirement_id"))
            for item in checklist.get("topic_instantiation_required", [])
            if isinstance(item, dict)
        }
        for required_id in REQUIRED_REGRESSION_ITEM_IDS - {GENERIC_3_3_PARENT_ID}:
            if required_id not in checklist_parent_ids:
                errors.append(f"{required_id}: not found in requirement checklist requirements")
        if GENERIC_3_3_PARENT_ID not in topic_parent_ids:
            errors.append(f"{GENERIC_3_3_PARENT_ID}: not found in topic_instantiation_required")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Checklist cross-check skipped: {exc}")

    return {
        "status": "ok" if not errors else "failed",
        "mode": "self_check",
        "manifest_path": str(manifest_path),
        "sample_count": len(regression_items),
        "required_sample_ids": sorted(REQUIRED_REGRESSION_ITEM_IDS),
        "errors": errors,
        "warnings": warnings,
    }


def validate_assessment_file(path: Path, require_e2_1_d_body_evidence: bool = False) -> dict[str, Any]:
    payload = _load_json(path)
    assessments = _extract_assessments(payload)
    if not assessments:
        return {
            "status": "failed",
            "mode": "assessment_file",
            "assessment_file": str(path),
            "assessment_count": 0,
            "errors": ["assessment file must contain disclosure_assessments, assessments, items, or a top-level list"],
            "warnings": [],
        }
    result = validate_assessments(assessments, require_e2_1_d_body_evidence=require_e2_1_d_body_evidence)
    result["mode"] = "assessment_file"
    result["assessment_file"] = str(path)
    return result


def validate_run_dir(path: Path, require_e2_1_d_body_evidence: bool = False) -> dict[str, Any]:
    candidates = [path / "analyst_result.json", path / "analysis_run.json"]
    for candidate in candidates:
        if candidate.exists():
            result = validate_assessment_file(candidate, require_e2_1_d_body_evidence=require_e2_1_d_body_evidence)
            result["mode"] = "run_dir"
            result["run_dir"] = str(path)
            result["source_file"] = str(candidate)
            return result
    return {
        "status": "failed",
        "mode": "run_dir",
        "run_dir": str(path),
        "errors": ["run-dir must contain analyst_result.json or analysis_run.json"],
        "warnings": [],
    }


def validate_manual_review_result(path: Path) -> dict[str, Any]:
    payload = _load_json(path)
    errors: list[str] = []
    warnings: list[str] = []
    blocked_verdicts, blocked_warnings = _blocked_verdicts_by_item()
    warnings.extend(blocked_warnings)
    items = _as_list(payload.get("items") if isinstance(payload, dict) else [])
    if not items:
        errors.append("manual review result must contain non-empty items")

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"items[{index}] must be object")
            continue
        manifest_item_id = str(item.get("manifest_item_id") or f"items[{index}]")
        blocked_for_item = blocked_verdicts.get(manifest_item_id, set())
        for verdict_field in ("human_verdict", "model_verdict"):
            verdict = item.get(verdict_field)
            if verdict in blocked_for_item:
                errors.append(f"{manifest_item_id}: {verdict_field} {verdict} is blocked by E2 regression")
        if manifest_item_id == GENERIC_3_3_PARENT_ID:
            if item.get("human_verdict") != MANUAL_REVIEW:
                errors.append(f"{GENERIC_3_3_PARENT_ID}: human_verdict must remain manual_review")
            reason_text = " ".join(str(item.get(field, "")) for field in ("error_type", "review_note"))
            if "needs_topic_instantiation" not in reason_text:
                errors.append(f"{GENERIC_3_3_PARENT_ID}: manual review reason must include needs_topic_instantiation")

    return {
        "status": "ok" if not errors else "failed",
        "mode": "manual_review_result",
        "manual_review_result": str(path),
        "item_count": len(items),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Stage E2.1 evidence contract without LLM calls.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--assessment-file", type=Path, help="JSON file containing assessments to validate.")
    mode.add_argument("--run-dir", type=Path, help="Run directory containing analyst_result.json or analysis_run.json.")
    mode.add_argument("--manual-review-result", type=Path, help="Manual review result JSON to validate.")
    parser.add_argument(
        "--require-e2-1-d-body-evidence",
        action="store_true",
        help="Require E2.1-D high-risk samples to include substantive or external body evidence.",
    )
    parser.add_argument(
        "--regression-manifest",
        type=Path,
        default=DEFAULT_REGRESSION_MANIFEST_PATH,
        help="Regression manifest used by no-argument self-check.",
    )
    args = parser.parse_args(argv)

    try:
        if args.assessment_file:
            result = validate_assessment_file(args.assessment_file, require_e2_1_d_body_evidence=args.require_e2_1_d_body_evidence)
        elif args.run_dir:
            result = validate_run_dir(args.run_dir, require_e2_1_d_body_evidence=args.require_e2_1_d_body_evidence)
        elif args.manual_review_result:
            result = validate_manual_review_result(args.manual_review_result)
        else:
            result = validate_regression_manifest(args.regression_manifest)
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "failed",
            "mode": "assessment_file" if args.assessment_file else "self_check",
            "errors": [f"{type(exc).__name__}: {exc}"],
            "warnings": [],
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())







