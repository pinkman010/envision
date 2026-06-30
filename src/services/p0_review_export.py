"""Export helpers for E4 P0 pending-review data."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from src.storage.p0_review_store import P0ReviewStore


def build_assessment_export_rows(store: P0ReviewStore, run_id: str) -> list[dict[str, Any]]:
    decisions = _decisions_by_assessment(store.list_review_decisions(run_id))
    rows = []
    for assessment in store.list_assessments(run_id):
        evidence = assessment.get("evidence") or []
        requirement_checks = assessment.get("requirement_checks") or []
        decision = decisions.get(assessment["assessment_id"], {})
        rows.append(
            {
                "assessment_id": assessment["assessment_id"],
                "manifest_item_id": assessment["manifest_item_id"],
                "disclosure_id": assessment["disclosure_id"],
                "standard_id": assessment.get("standard_id"),
                "topic": assessment.get("topic"),
                "ai_verdict": assessment.get("ai_verdict"),
                "review_status": assessment.get("review_status"),
                "final_evaluation_status": assessment.get("final_evaluation_status"),
                "manual_review_reason_codes": _join(assessment.get("manual_review_reason_codes")),
                "requirement_ids": _join(
                    item.get("requirement_id") for item in requirement_checks if item.get("requirement_id")
                ),
                "requirement_support_statuses": _join(
                    f"{item.get('requirement_id')}={item.get('support_status')}"
                    for item in requirement_checks
                    if item.get("requirement_id")
                ),
                "evidence_ids": _join(item.get("evidence_id") for item in evidence if item.get("evidence_id")),
                "chunk_ids": _join(item.get("chunk_id") for item in evidence if item.get("chunk_id")),
                "source_pages": _join(
                    str(item.get("source_page")) for item in evidence if item.get("source_page") is not None
                ),
                "report_page_labels": _join(
                    str(item.get("report_page_label"))
                    for item in evidence
                    if item.get("report_page_label") is not None
                ),
                "source_text_preview": _source_text_preview(evidence),
                "cleanup_map_references": _cleanup_reference(assessment),
                "human_verdict": decision.get("human_verdict"),
                "evidence_page_check": decision.get("evidence_page_check"),
                "requirement_gap_check": decision.get("requirement_gap_check"),
                "error_type": decision.get("error_type"),
                "correction_note": decision.get("correction_note"),
                "reviewer": decision.get("reviewer"),
                "review_comment": decision.get("review_comment"),
            }
        )
    return rows


def build_advisor_export_rows(store: P0ReviewStore, run_id: str) -> list[dict[str, Any]]:
    decisions = _decisions_by_advisor(store.list_review_decisions(run_id))
    rows = []
    for item in store.list_advisor_items(run_id):
        raw = item.get("raw_advisor") or {}
        decision = decisions.get(item["advisor_item_id"], {})
        rows.append(
            {
                "advisor_item_id": item["advisor_item_id"],
                "manifest_item_id": item["manifest_item_id"],
                "disclosure_id": item["disclosure_id"],
                "coverage_type": item["coverage_type"],
                "recommendation_type": raw.get("recommendation_type"),
                "recommendation_status": item["recommendation_status"],
                "final_evaluation_status": item["final_evaluation_status"],
                "priority": item.get("priority"),
                "requires_internal_data": item.get("requires_internal_data"),
                "requirement_id": raw.get("requirement_id"),
                "current_disclosure": raw.get("current_disclosure"),
                "gap": raw.get("gap"),
                "next_report_addition": raw.get("next_report_addition"),
                "basis": raw.get("basis"),
                "recommendation_text": item.get("recommendation_text"),
                "advisor_usefulness_rating": decision.get("advisor_usefulness_rating"),
                "error_type": decision.get("error_type"),
                "correction_note": decision.get("correction_note"),
                "reviewer": decision.get("reviewer"),
                "review_comment": decision.get("review_comment"),
            }
        )
    return rows


def build_review_decision_export_rows(store: P0ReviewStore, run_id: str) -> list[dict[str, Any]]:
    return store.list_review_decisions(run_id)


def export_csv(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    fieldnames = sorted({key for row in rows for key in row.keys()})
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows([{key: _csv_value(value) for key, value in row.items()} for row in rows])
    return output.getvalue()


def export_json(rows: list[dict[str, Any]]) -> str:
    return json.dumps(rows, ensure_ascii=False, indent=2)


def _decisions_by_assessment(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        decision["assessment_id"]: decision
        for decision in decisions
        if decision.get("assessment_id")
    }


def _decisions_by_advisor(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        decision["advisor_item_id"]: decision
        for decision in decisions
        if decision.get("advisor_item_id")
    }


def _join(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return values
    return "; ".join(str(value) for value in values if value not in (None, ""))


def _source_text_preview(evidence: list[dict[str, Any]], limit: int = 240) -> str:
    joined = " | ".join(item.get("source_text", "") for item in evidence if item.get("source_text"))
    return joined[:limit]


def _cleanup_reference(assessment: dict[str, Any]) -> str:
    raw = assessment.get("raw_assessment") or {}
    refs = []
    for key in ("requirement_id_cleanup_map", "evidence_binding_cleanup_map", "pdf_source_text_location_waiver"):
        if raw.get(key):
            refs.append(key)
    return "; ".join(refs)


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return value
