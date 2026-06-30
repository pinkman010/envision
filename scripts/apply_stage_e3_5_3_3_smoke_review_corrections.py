"""Apply E3.5 GRI 3-3 human smoke review field corrections.

This script preserves raw and corrected LLM artifacts. It writes reviewed
artifacts based on the user's smoke review conclusions.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _manual_review_input, _write_json  # noqa: E402
from scripts.run_stage_e3_5_index_3_3_llm import _machine_smoke_review, _smoke_review_template, _validate_merged  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402

DEFAULT_RUN_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e3_5" / "20260630T085702Z_e3_5_gri3_3_llm_index_assessment"
DEFAULT_EVIDENCE_INDEX = PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_report_evidence_index.json"

RUN_ID = "20260630T085702Z_e3_5_gri3_3_llm_index_assessment"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chunk_by_id(path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(path)
    return {
        str(chunk["chunk_id"]): chunk
        for chunk in payload.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }


def _new_evidence(chunk: dict[str, Any], *, evidence_id: str, subtype: str, section: str) -> dict[str, Any]:
    pdf_page = int(chunk["pdf_page"])
    return {
        "evidence_id": evidence_id,
        "source_document": chunk.get("source_document_relative_path") or chunk.get("source_document"),
        "source_page": pdf_page,
        "report_page_label": str(pdf_page - 1),
        "source_text": str(chunk.get("text", "")).strip(),
        "relevance": 0.78,
        "evidence_kind": "substantive_report_evidence",
        "evidence_subtype": subtype,
        "supports_requirement_ids": [],
        "source_section": section,
        "judgment_reason": "Human smoke review field correction evidence binding.",
        "corpus_id": "envision_energy_2024_zh",
        "chunk_id": chunk.get("chunk_id"),
        "extraction_method": "p0_report_evidence_index",
        "source_document_sha256": chunk.get("source_document_sha256"),
        "company": chunk.get("company", "Envision Energy"),
        "report_year": chunk.get("report_year", 2024),
        "industry": chunk.get("industry", "renewable_energy"),
        "topic": "gri_3_3_human_smoke_review_correction",
        "source_text_extraction_warning": None,
        "retrieval_method": "human_smoke_review_correction",
    }


def _ensure_evidence(assessment: dict[str, Any], evidence: dict[str, Any]) -> None:
    existing_ids = {str(item.get("evidence_id")) for item in assessment.get("evidence", []) if isinstance(item, dict)}
    if evidence["evidence_id"] not in existing_ids:
        assessment.setdefault("evidence", []).append(evidence)


def _evidence_ids_by_chunk(assessment: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for evidence in assessment.get("evidence", []) or []:
        if isinstance(evidence, dict) and evidence.get("chunk_id") and evidence.get("evidence_id"):
            result[str(evidence["chunk_id"])] = str(evidence["evidence_id"])
    return result


def _check_by_id(assessment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(check["requirement_id"]): check
        for check in assessment.get("requirement_checks", []) or []
        if isinstance(check, dict) and check.get("requirement_id")
    }


def _set_status(checks: dict[str, dict[str, Any]], rid: str, status: str, evidence_ids: list[str] | None = None, reason: str = "") -> None:
    check = checks[rid]
    check["support_status"] = status
    check["supporting_evidence_ids"] = evidence_ids or []
    check["missing_reason"] = reason if status != "partially_met" else reason
    check["manual_review_reason"] = ""


def _set_lists(assessment: dict[str, Any], *, partial: list[str], missing: list[str]) -> None:
    assessment["partial_requirements"] = sorted(set(partial))
    assessment["missing_requirements"] = sorted(set(missing) - set(assessment["partial_requirements"]))
    assessment["manual_review_requirements"] = []
    assessment["manual_review_reason_codes"] = []


def _apply_301(assessment: dict[str, Any]) -> list[dict[str, Any]]:
    checks = _check_by_id(assessment)
    ids_by_chunk = _evidence_ids_by_chunk(assessment)
    rid = "current_gap:GRI301:3-3:e:ii"
    _set_status(
        checks,
        rid,
        "partially_met",
        [ids_by_chunk.get("chunk_a72a08a70e41881ac2715412", "chunk_a72a08a70e41881ac2715412")],
        "Packaging and circular economy targets are partly disclosed, but full indicators and tracking scope remain incomplete.",
    )
    partial = list(assessment.get("partial_requirements", []) or [])
    if rid not in partial:
        partial.append(rid)
    missing = [item for item in assessment.get("missing_requirements", []) or [] if item != rid]
    _set_lists(assessment, partial=partial, missing=missing)
    return [{"manifest_item_id": assessment["manifest_item_id"], "correction": "set_3_3_e_ii_partially_met"}]


def _apply_303(assessment: dict[str, Any], chunks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    for chunk_id, evidence_id, section in [
        ("chunk_782bdaef2a305f8e9ea6cea9", "evidence_reviewed_gri303_3_3_page22", "废气、废水与噪声管理"),
        ("chunk_56f1dcc90e0ec484e0181e09", "evidence_reviewed_gri303_3_3_page25_water_management", "水资源使用"),
        ("chunk_1a02283af02fbc1a11660d19", "evidence_reviewed_gri303_3_3_page25_water_saving", "水资源节约利用"),
        ("chunk_173043545be67492dfb9c2d6", "evidence_reviewed_gri303_3_3_page63_water_metrics", "环境绩效"),
    ]:
        _ensure_evidence(
            assessment,
            _new_evidence(chunks[chunk_id], evidence_id=evidence_id, subtype="water_management_body_evidence", section=section),
        )
    checks = _check_by_id(assessment)
    partial_map = {
        "current_gap:GRI303:3-3:c": ["evidence_reviewed_gri303_3_3_page25_water_management"],
        "current_gap:GRI303:3-3:d": ["evidence_reviewed_gri303_3_3_page22", "evidence_reviewed_gri303_3_3_page25_water_management"],
        "current_gap:GRI303:3-3:d:i": ["evidence_reviewed_gri303_3_3_page22", "evidence_reviewed_gri303_3_3_page25_water_saving"],
        "current_gap:GRI303:3-3:d:iii": ["evidence_reviewed_gri303_3_3_page25_water_saving"],
        "current_gap:GRI303:3-3:e:ii": ["evidence_reviewed_gri303_3_3_page25_water_management", "evidence_reviewed_gri303_3_3_page63_water_metrics"],
        "current_gap:GRI303:3-3:e:iii": ["evidence_reviewed_gri303_3_3_page63_water_metrics"],
    }
    missing = [
        "current_gap:GRI303:3-3:a",
        "current_gap:GRI303:3-3:b",
        "current_gap:GRI303:3-3:d:ii",
        "current_gap:GRI303:3-3:e",
        "current_gap:GRI303:3-3:e:i",
        "current_gap:GRI303:3-3:e:iv",
        "current_gap:GRI303:3-3:f",
    ]
    for rid, evidence_ids in partial_map.items():
        _set_status(checks, rid, "partially_met", evidence_ids, "Water-resource management evidence partially supports this 3-3 requirement.")
    for rid in missing:
        _set_status(checks, rid, "not_met", [], "Human smoke review: the report does not provide sufficient topic-specific disclosure for this requirement.")
    assessment["verdict"] = "partially_disclosed"
    assessment["confidence"] = max(float(assessment.get("confidence", 0) or 0), 0.55)
    assessment["aggregation_reason"] = "human_smoke_review_field_correction: partially_disclosed_with_water_management_body_evidence"
    assessment["rationale"] = (
        "Human smoke review corrected current_gap:GRI303:3-3 to partially_disclosed: water policies, actions, targets and metrics are partly disclosed, while impact description, involvement with negative impacts, remediation, lessons learned and stakeholder effectiveness remain insufficient."
    )
    assessment["recommendation"] = (
        "Next report should connect water-resource impacts, business relationships, remediation, lessons learned and stakeholder engagement effectiveness to GRI 3-3 requirements."
    )
    _set_lists(assessment, partial=list(partial_map), missing=missing)
    return [{"manifest_item_id": assessment["manifest_item_id"], "correction": "manual_review_to_partially_disclosed"}]


def _apply_401(assessment: dict[str, Any]) -> list[dict[str, Any]]:
    checks = _check_by_id(assessment)
    ids_by_chunk = _evidence_ids_by_chunk(assessment)
    partial_map = {
        "current_gap:GRI401:3-3:c": ["chunk_0e9f0eacd70a0db82bb57dd3", "chunk_3ebc5ba54d2006f017fa0b2c"],
        "current_gap:GRI401:3-3:d": ["chunk_9cf9006d3963ba7e15574d80", "chunk_0e9f0eacd70a0db82bb57dd3", "chunk_3ebc5ba54d2006f017fa0b2c"],
        "current_gap:GRI401:3-3:d:i": ["chunk_0e9f0eacd70a0db82bb57dd3", "chunk_3ebc5ba54d2006f017fa0b2c"],
        "current_gap:GRI401:3-3:d:iii": ["chunk_9cf9006d3963ba7e15574d80", "chunk_3ebc5ba54d2006f017fa0b2c"],
        "current_gap:GRI401:3-3:e": ["chunk_d4f7cef94151465d066f4aa7", "chunk_b5a396a552dffcfca30362a3"],
        "current_gap:GRI401:3-3:e:ii": ["chunk_d4f7cef94151465d066f4aa7", "chunk_b5a396a552dffcfca30362a3"],
        "current_gap:GRI401:3-3:e:iii": ["chunk_d4f7cef94151465d066f4aa7", "chunk_b5a396a552dffcfca30362a3"],
    }
    missing = [
        "current_gap:GRI401:3-3:a",
        "current_gap:GRI401:3-3:b",
        "current_gap:GRI401:3-3:d:ii",
        "current_gap:GRI401:3-3:e:i",
        "current_gap:GRI401:3-3:e:iv",
        "current_gap:GRI401:3-3:f",
    ]
    for rid, chunk_ids in partial_map.items():
        evidence_ids = [ids_by_chunk.get(chunk_id, chunk_id) for chunk_id in chunk_ids]
        _set_status(checks, rid, "partially_met", evidence_ids, "Employment-management body evidence partially supports this 3-3 requirement.")
    for rid in missing:
        _set_status(checks, rid, "not_met", [], "Human smoke review: the report does not provide sufficient topic-specific disclosure for this requirement.")
    assessment["verdict"] = "partially_disclosed"
    assessment["confidence"] = max(float(assessment.get("confidence", 0) or 0), 0.55)
    assessment["aggregation_reason"] = "human_smoke_review_field_correction: partially_disclosed_with_employment_body_evidence"
    assessment["rationale"] = (
        "Human smoke review corrected current_gap:GRI401:3-3 to partially_disclosed: employment policies, actions, employee structure, turnover, welfare and communication evidence partly support GRI 3-3, while impact description, remediation, lessons learned and stakeholder effectiveness remain insufficient."
    )
    assessment["recommendation"] = (
        "Next report should explicitly connect employment impacts, remediation, effectiveness tracking process, lessons learned and employee/stakeholder engagement influence to GRI 3-3."
    )
    _set_lists(assessment, partial=list(partial_map), missing=missing)
    return [{"manifest_item_id": assessment["manifest_item_id"], "correction": "manual_review_to_partially_disclosed"}]


def _apply_414(assessment: dict[str, Any], chunks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    _ensure_evidence(
        assessment,
        _new_evidence(
            chunks["chunk_f1f149fb5a33bd50fdc7bafd"],
            evidence_id="evidence_reviewed_gri414_3_3_page67_supplier_metrics",
            subtype="supplier_social_assessment_metrics",
            section="供应商管理与可持续采购",
        ),
    )
    checks = _check_by_id(assessment)
    partial_add = {
        "current_gap:GRI414:3-3:e:ii": ["evidence_reviewed_gri414_3_3_page67_supplier_metrics"],
        "current_gap:GRI414:3-3:e:iii": ["evidence_reviewed_gri414_3_3_page67_supplier_metrics"],
    }
    for rid, evidence_ids in partial_add.items():
        _set_status(checks, rid, "partially_met", evidence_ids, "Supplier management metrics partially support this effectiveness-tracking requirement.")
    partial = list(assessment.get("partial_requirements", []) or [])
    for rid in partial_add:
        if rid not in partial:
            partial.append(rid)
    missing = [item for item in assessment.get("missing_requirements", []) or [] if item not in partial_add]
    _set_lists(assessment, partial=partial, missing=missing)
    assessment["aggregation_reason"] = "human_smoke_review_field_correction: supplier_metrics_bound_to_3_3_e_requirements"
    return [{"manifest_item_id": assessment["manifest_item_id"], "correction": "set_3_3_e_ii_e_iii_partially_met"}]


def _smoke_review_result() -> dict[str, Any]:
    items = [
        ("current_gap:GRI201:3-3", "not_disclosed", "not_disclosed", "reviewed_no_change", []),
        ("current_gap:GRI202:3-3", "not_disclosed", "not_disclosed", "reviewed_no_change", []),
        ("current_gap:GRI203:3-3", "partially_disclosed", "partially_disclosed", "reviewed_no_change", []),
        ("current_gap:GRI303:3-3", "manual_review", "partially_disclosed", "field_correction_required", ["wrong_verdict_aggregation", "evidence_binding_issue", "manual_review_overuse"]),
        ("current_gap:GRI301:3-3", "partially_disclosed", "partially_disclosed", "field_correction_required", ["wrong_requirement_aggregation"]),
        ("current_gap:GRI401:3-3", "manual_review", "partially_disclosed", "field_correction_required", ["wrong_verdict_aggregation", "evidence_binding_issue", "manual_review_overuse"]),
        ("current_gap:GRI414:3-3", "partially_disclosed", "partially_disclosed", "field_correction_required", ["wrong_requirement_aggregation"]),
    ]
    return {
        "review_version": "p0_stage_e3_5_3_3_smoke_review_result_v1",
        "run_id": RUN_ID,
        "review_status": "completed",
        "gate_status": "blocked_required_field_corrections_before_acceptance",
        "review_scope": {
            "source_file": "analyst_result_merged_corrected.json",
            "sample_count": 7,
            "sample_manifest_item_ids": [item[0] for item in items],
            "ai_verdict_distribution": {"not_disclosed": 2, "partially_disclosed": 3, "manual_review": 2},
            "human_verdict_distribution": {"not_disclosed": 2, "partially_disclosed": 5, "manual_review": 0},
            "changed_verdict_count": 2,
            "blocking_item_count": 4,
        },
        "items": [
            {
                "manifest_item_id": manifest_item_id,
                "model_verdict": model_verdict,
                "human_verdict": human_verdict,
                "treatment": treatment,
                "evidence_page_check": "ok",
                "requirement_gap_check": "field_correction_required" if issue_types else "ok",
                "issue_types": issue_types,
                "review_note": "Human smoke review conclusion supplied by user on 2026-06-30.",
            }
            for manifest_item_id, model_verdict, human_verdict, treatment, issue_types in items
        ],
    }


def apply_smoke_review_corrections(run_dir: Path = DEFAULT_RUN_DIR, evidence_index_path: Path = DEFAULT_EVIDENCE_INDEX) -> dict[str, Any]:
    source_path = run_dir / "analyst_result_merged_corrected.json"
    analysis_run_path = run_dir / "analysis_run_merged_corrected.json"
    analyst = _load_json(source_path)
    analysis_run = _load_json(analysis_run_path)
    chunks = _chunk_by_id(evidence_index_path)
    assessments = json.loads(json.dumps(analyst.get("disclosure_assessments", []), ensure_ascii=False))
    by_id = {str(item.get("manifest_item_id")): item for item in assessments}

    corrections: list[dict[str, Any]] = []
    corrections.extend(_apply_303(by_id["current_gap:GRI303:3-3"], chunks))
    corrections.extend(_apply_301(by_id["current_gap:GRI301:3-3"]))
    corrections.extend(_apply_401(by_id["current_gap:GRI401:3-3"]))
    corrections.extend(_apply_414(by_id["current_gap:GRI414:3-3"], chunks))

    reviewed_analyst = dict(analyst)
    reviewed_analyst["disclosure_assessments"] = assessments
    reviewed_analyst["summary"] = dict(reviewed_analyst.get("summary", {}) or {})
    reviewed_analyst["summary"]["human_smoke_review_status"] = "reviewed_field_corrections_applied"
    reviewed_analyst["summary"]["verdict_distribution_after_reviewed_corrections"] = dict(
        Counter(str(item.get("verdict", "")) for item in assessments)
    )

    reviewed_run = dict(analysis_run)
    reviewed_run["assessments"] = assessments
    reviewed_run.setdefault("summary", {})
    reviewed_run["summary"]["human_smoke_review_status"] = "reviewed_field_corrections_applied"
    reviewed_run["summary"]["verdict_distribution_after_reviewed_corrections"] = reviewed_analyst["summary"][
        "verdict_distribution_after_reviewed_corrections"
    ]
    validated_run = AnalysisRun.model_validate(reviewed_run)
    validation = _validate_merged(assessments)
    smoke_template = _load_json(run_dir / "smoke_review_template.json")
    machine_smoke = _machine_smoke_review(RUN_ID, assessments, smoke_template)
    smoke_result = _smoke_review_result()

    _write_json(run_dir / "smoke_review_result.json", smoke_result)
    _write_json(run_dir / "analyst_result_merged_reviewed.json", reviewed_analyst)
    _write_json(run_dir / "analysis_run_merged_reviewed.json", validated_run.model_dump(mode="json"))
    _write_json(run_dir / "manual_review_input_merged_reviewed.json", _manual_review_input(validated_run))
    _write_json(run_dir / "human_smoke_review_correction_log.json", {"items": corrections})
    _write_json(run_dir / "merged_validation_result_after_human_smoke_review_corrections.json", validation)
    _write_json(run_dir / "machine_smoke_review_result_reviewed.json", machine_smoke)

    stage_gate_path = run_dir / "stage_gate_result.json"
    stage_gate = _load_json(stage_gate_path)
    stage_gate.update(
        {
            "gate_status": "reviewed_field_corrections_applied_pending_acceptance",
            "smoke_review_result": str(run_dir / "smoke_review_result.json"),
            "reviewed_artifacts_generated": True,
            "reviewed_artifacts": [
                str(run_dir / "analyst_result_merged_reviewed.json"),
                str(run_dir / "analysis_run_merged_reviewed.json"),
                str(run_dir / "manual_review_input_merged_reviewed.json"),
            ],
            "validation_status_after_human_smoke_review_corrections": validation["status"],
            "machine_smoke_hard_issue_count_after_human_smoke_review_corrections": len(machine_smoke.get("hard_issues", [])),
            "final_effective_set_status": "ready_to_rebuild_from_reviewed_artifacts",
        }
    )
    _write_json(stage_gate_path, stage_gate)

    run_summary_path = run_dir / "run_summary.json"
    run_summary = _load_json(run_summary_path)
    run_summary.update(
        {
            "human_smoke_review_status": "completed",
            "gate_status_after_human_smoke_review": "blocked_required_field_corrections_before_acceptance",
            "reviewed_artifacts_generated": True,
            "validation_status_after_human_smoke_review_corrections": validation["status"],
            "machine_smoke_hard_issue_count_after_human_smoke_review_corrections": len(machine_smoke.get("hard_issues", [])),
            "verdict_distribution_after_reviewed_corrections": reviewed_analyst["summary"][
                "verdict_distribution_after_reviewed_corrections"
            ],
        }
    )
    _write_json(run_summary_path, run_summary)

    result = {
        "status": "ok" if validation["status"] == "ok" else "needs_review",
        "run_dir": str(run_dir),
        "reviewed_assessment_count": len(assessments),
        "validation_status_after_human_smoke_review_corrections": validation["status"],
        "machine_smoke_hard_issue_count_after_human_smoke_review_corrections": len(machine_smoke.get("hard_issues", [])),
        "verdict_distribution_after_reviewed_corrections": reviewed_analyst["summary"][
            "verdict_distribution_after_reviewed_corrections"
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply E3.5 GRI 3-3 human smoke review corrections.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    args = parser.parse_args(argv)
    apply_smoke_review_corrections(run_dir=args.run_dir, evidence_index_path=args.evidence_index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
