"""Apply human smoke-review corrections for Stage E3 batch 05.

Raw LLM artifacts remain unchanged. This script updates the corrected
artifacts created after field correction and writes the smoke review gate.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _manual_review_input, _write_json  # noqa: E402
from scripts.validate_stage_e3_batch_outputs import validate_run_dir  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402

DEFAULT_RUN_DIR = (
    PROJECT_ROOT
    / "data"
    / "runs"
    / "stage_e"
    / "20260630T070123Z_e3_batch_05_governance_supply_chain_economic"
)

GATE_STATUS = "blocked_before_e3_current_scope_acceptance_required_field_corrections"
EFFECTIVE_GATE_STATUS = "accepted_after_corrections_for_e3_current_scope_acceptance"
BLOCKING_REASONS = [
    "over_manual_review",
    "wrong_verdict_aggregation",
    "manual_review_to_not_disclosed_required",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assessment_by_id(assessments: list[dict[str, Any]], manifest_item_id: str) -> dict[str, Any]:
    for assessment in assessments:
        if assessment.get("manifest_item_id") == manifest_item_id:
            return assessment
    raise ValueError(f"assessment not found: {manifest_item_id}")


def _hard_missing_requirement_ids(assessment: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for check in assessment.get("requirement_checks", []) or []:
        if not isinstance(check, dict):
            continue
        requirement_id = str(check.get("requirement_id", ""))
        if requirement_id and check.get("is_mandatory") is True:
            ids.append(requirement_id)
    return ids


def _clear_supporting_evidence(assessment: dict[str, Any]) -> None:
    for evidence in assessment.get("evidence", []) or []:
        if isinstance(evidence, dict):
            evidence["supports_requirement_ids"] = []


def _set_not_disclosed(assessment: dict[str, Any], rationale: str, recommendation: str) -> None:
    missing = _hard_missing_requirement_ids(assessment)
    if not missing:
        raise ValueError(f"no mandatory requirement checks found for {assessment.get('manifest_item_id')}")

    assessment["verdict"] = "not_disclosed"
    assessment["missing_requirements"] = missing
    assessment["partial_requirements"] = []
    assessment["not_applicable_requirements"] = []
    assessment["manual_review_requirements"] = []
    assessment["manual_review_reason_codes"] = []
    assessment["aggregation_reason"] = (
        "人工 smoke review 修正：合理检索后未找到可支持该披露项要求的正文实质证据；"
        "无省略理由、无适用性争议，故由 manual_review 改为 not_disclosed。"
    )
    assessment["rationale"] = rationale
    assessment["recommendation"] = recommendation
    _clear_supporting_evidence(assessment)

    for check in assessment.get("requirement_checks", []) or []:
        if not isinstance(check, dict):
            continue
        if str(check.get("requirement_id", "")) in missing:
            check["support_status"] = "not_met"
            check["supporting_evidence_ids"] = []
            check["manual_review_reason"] = ""
            check["missing_reason"] = rationale


def _apply_201_3(assessment: dict[str, Any]) -> None:
    _set_not_disclosed(
        assessment,
        (
            "报告索引指向“关怀员工，幸福职场”正文页，但该页主要披露员工福利、劳工人权、DEI、"
            "培训和卓越职场认证，未披露固定福利计划义务、退休计划负债、养老金基金覆盖、"
            "缴款比例或参与水平等 GRI 201-3 所需信息。"
        ),
        (
            "下一期报告可补充固定福利计划义务、退休计划负债、基金覆盖程度、估计基础、缴款比例"
            "和退休计划参与水平；相关数据通常需要财务、人力资源或养老金计划内部数据支持。"
        ),
    )


def _apply_202_1(assessment: dict[str, Any]) -> None:
    _set_not_disclosed(
        assessment,
        (
            "报告索引指向 ESG 战略与目标页，正文未披露按性别的标准起薪水平工资与当地最低工资之比、"
            "重要运营地点或定义口径；“维生工资基准 100%”相关表述不能替代 GRI 202-1 要求的最低工资比。"
        ),
        (
            "下一期报告可按重要运营地点和性别披露标准起薪与当地最低工资之比，并说明重要运营地点定义；"
            "相关数据通常需要薪酬和当地最低工资基准数据支持。"
        ),
    )


def _apply_payload(payload: dict[str, Any], key: str) -> dict[str, Any]:
    corrected = copy.deepcopy(payload)
    assessments = corrected.get(key)
    if not isinstance(assessments, list):
        raise ValueError(f"{key} must be a list")
    _apply_201_3(_assessment_by_id(assessments, "current_gap:GRI201:201-3"))
    _apply_202_1(_assessment_by_id(assessments, "current_gap:GRI202:202-1"))
    if key == "assessments":
        summary = corrected.setdefault("summary", {})
        if isinstance(summary, dict):
            summary["smoke_review_corrections_applied"] = True
            summary["smoke_review_gate_status"] = GATE_STATUS
    return corrected


def _smoke_review_result(run_id: str, batch_id: str) -> dict[str, Any]:
    return {
        "review_version": "p0_stage_e3_batch05_smoke_review_result_v1",
        "run_id": run_id,
        "batch_id": batch_id,
        "review_status": "completed",
        "gate_status": GATE_STATUS,
        "blocking_reasons": BLOCKING_REASONS,
        "hard_evidence_errors_found": False,
        "items": [
            {
                "manifest_item_id": "current_gap:GRI201:201-2",
                "model_verdict": "partially_disclosed",
                "human_verdict": "partially_disclosed",
                "issue_types": ["none_under_current_contract"],
                "evidence_page_check": "ok",
                "requirement_gap_check": "ok",
                "review_note": (
                    "PDF 第 17/18 页页码正确；正文支持气候风险、机会、影响和管理措施；"
                    "201-2:2.2 作为实质 compilation requirement 保持 missing。"
                ),
            },
            {
                "manifest_item_id": "current_gap:GRI201:201-1",
                "model_verdict": "manual_review",
                "human_verdict": "manual_review",
                "issue_types": ["omission_reason_requires_review"],
                "evidence_page_check": "ok",
                "requirement_gap_check": "ok",
                "review_note": "索引写明因商业保密限制从略披露；全文未发现直接经济价值相关正文数据。",
            },
            {
                "manifest_item_id": "current_gap:GRI201:201-3",
                "model_verdict": "manual_review",
                "human_verdict": "not_disclosed",
                "issue_types": [
                    "over_manual_review",
                    "wrong_verdict_aggregation",
                    "manual_review_to_not_disclosed_required",
                ],
                "evidence_page_check": "ok",
                "requirement_gap_check": "corrected",
                "review_note": "索引无省略理由；正文未披露固定福利计划义务、养老金覆盖、缴款比例或参与水平。",
            },
            {
                "manifest_item_id": "current_gap:GRI201:201-4",
                "model_verdict": "manual_review",
                "human_verdict": "manual_review",
                "issue_types": ["omission_reason_requires_review"],
                "evidence_page_check": "ok",
                "requirement_gap_check": "ok",
                "review_note": "索引写明因商业保密限制从略披露；全文未发现政府财政援助金额或地区拆分。",
            },
            {
                "manifest_item_id": "current_gap:GRI202:202-1",
                "model_verdict": "manual_review",
                "human_verdict": "not_disclosed",
                "issue_types": [
                    "over_manual_review",
                    "wrong_verdict_aggregation",
                    "manual_review_to_not_disclosed_required",
                ],
                "evidence_page_check": "ok",
                "requirement_gap_check": "corrected",
                "review_note": "正文未披露按性别的标准起薪与当地最低工资之比、重要运营地点或定义口径。",
            },
        ],
    }


def apply_corrections(run_dir: Path) -> dict[str, Any]:
    analyst_path = run_dir / "analyst_result_corrected.json"
    analysis_path = run_dir / "analysis_run_corrected.json"
    if not analyst_path.exists() or not analysis_path.exists():
        raise FileNotFoundError("batch05 field-corrected artifacts must exist before smoke corrections")

    analyst_result = _load_json(analyst_path)
    analysis_run = _load_json(analysis_path)
    run_summary = _load_json(run_dir / "run_summary.json")
    run_id = str(run_summary["run_id"])
    batch_id = str(run_summary["batch_id"])

    corrected_analyst = _apply_payload(analyst_result, "disclosure_assessments")
    corrected_analysis = _apply_payload(analysis_run, "assessments")
    analysis_model = AnalysisRun.model_validate(corrected_analysis)

    _write_json(analyst_path, corrected_analyst)
    _write_json(analysis_path, corrected_analysis)
    _write_json(run_dir / "manual_review_input_corrected.json", _manual_review_input(analysis_model))
    _write_json(run_dir / "smoke_review_result.json", _smoke_review_result(run_id, batch_id))

    validation = validate_run_dir(run_dir, require_smoke_review_result=True)
    _write_json(run_dir / "batch_validation_result_after_smoke_review.json", validation)

    corrected_artifacts = [
        str(analyst_path),
        str(analysis_path),
        str(run_dir / "manual_review_input_corrected.json"),
    ]
    run_summary["validation_status_after_smoke_corrections"] = validation["status"]
    run_summary["validation_errors_after_smoke_corrections"] = validation.get("errors", [])
    run_summary["smoke_review_gate_status"] = GATE_STATUS
    run_summary["effective_gate_status"] = EFFECTIVE_GATE_STATUS if validation["status"] == "ok" else GATE_STATUS
    run_summary["corrected_artifacts"] = corrected_artifacts
    _write_json(run_dir / "run_summary.json", run_summary)

    gate_result = {
        "run_id": run_id,
        "batch_id": batch_id,
        "review_status": "completed",
        "gate_status": GATE_STATUS,
        "effective_gate_status": EFFECTIVE_GATE_STATUS if validation["status"] == "ok" else GATE_STATUS,
        "blocking_reasons": BLOCKING_REASONS,
        "hard_evidence_errors_found": False,
        "field_corrections_applied": True,
        "smoke_review_corrections_applied": True,
        "validation_status_after_smoke_corrections": validation["status"],
        "validation_errors_after_smoke_corrections": validation.get("errors", []),
        "corrected_artifacts": corrected_artifacts,
        "smoke_review_result": str(run_dir / "smoke_review_result.json"),
        "corrected_artifacts_accepted_as_stage_gate_input": validation["status"] == "ok",
        "accepted_stage_gate_input_files": corrected_artifacts if validation["status"] == "ok" else [],
        "acceptance_note": (
            "Accepted after E3 validator with smoke review and E2.1 evidence contract validator return ok; "
            "raw artifacts remain preserved and gate_status keeps smoke-review audit state."
        )
        if validation["status"] == "ok"
        else "",
        "next_required_action": "complete_e3_current_scope_acceptance_audit",
    }
    _write_json(run_dir / "stage_gate_result.json", gate_result)

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "corrected_items": ["current_gap:GRI201:201-3", "current_gap:GRI202:202-1"],
        "validation_status_after_smoke_corrections": validation["status"],
        "validation_error_count_after_smoke_corrections": len(validation.get("errors", [])),
        "corrected_artifacts": corrected_artifacts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply Stage E3 batch 05 human smoke-review corrections.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args(argv)

    result = apply_corrections(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
