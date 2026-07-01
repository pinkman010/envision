from __future__ import annotations

from scripts.archive_stage_e.run_stage_e3_143_unified_final_advisor import (
    _sanitize_assessment_for_advisor,
    validate_final_advisor_result,
)


def test_sanitize_assessment_for_advisor_excludes_source_text() -> None:
    assessment = {
        "manifest_item_id": "current_gap:GRI301:3-3",
        "standard_id": "GRI301",
        "canonical_disclosure_id": "3-3",
        "assessment_mode": "current_gap",
        "verdict": "partially_disclosed",
        "confidence": 0.7,
        "aggregation_reason": "partial support",
        "rationale": "report evidence supports part of 3-3",
        "missing_requirements": ["current_gap:GRI301:3-3:a"],
        "not_applicable_requirements": [],
        "manual_review_requirements": [],
        "manual_review_reason_codes": [],
        "readiness_verdict": None,
        "evidence": [
            {
                "evidence_id": "ev1",
                "evidence_kind": "substantive_report_evidence",
                "source_text": "public report source text",
            }
        ],
        "requirement_checks": [
            {
                "requirement_id": "current_gap:GRI301:3-3:a",
                "support_status": "not_met",
                "missing_reason": "not disclosed",
                "manual_review_reason": "",
                "requirement_text": "Describe impacts.",
            }
        ],
    }

    sanitized = _sanitize_assessment_for_advisor(assessment)

    assert sanitized["evidence"] == [{"evidence_kind": "substantive_report_evidence"}]
    assert "source_text" not in sanitized["evidence"][0]
    assert sanitized["requirement_checks"] == [
        {
            "requirement_id": "current_gap:GRI301:3-3:a",
            "support_status": "not_met",
            "missing_reason": "not disclosed",
            "manual_review_reason": "",
        }
    ]


def test_final_advisor_validation_rejects_internal_absence_inference() -> None:
    advisor_result = {
        "status": "completed",
        "p0_recommendations": [
            {
                "manifest_item_id": "current_gap:GRI301:3-3",
                "canonical_disclosure_id": "3-3",
                "requirement_id": "current_gap:GRI301:3-3:a",
                "recommendation_type": "report_content_improvement",
                "priority": "high",
                "current_disclosure": "报告已有部分披露。",
                "gap": "企业没有相关流程。",
                "next_report_addition": "补充公开披露。",
                "requires_internal_data": True,
                "recommendation": "补充披露。",
                "basis": "基于公开报告。",
                "review_status": "pending",
            }
        ],
        "overall_recommendation": "",
        "summary": {"total_recommendations": 1},
    }

    result = validate_final_advisor_result(advisor_result, {"current_gap:GRI301:3-3"})

    assert result["status"] == "failed"
    assert any("forbidden" in error for error in result["errors"])


def test_final_advisor_validation_accepts_valid_schema() -> None:
    advisor_result = {
        "status": "completed",
        "p0_recommendations": [
            {
                "manifest_item_id": "current_gap:GRI301:3-3",
                "canonical_disclosure_id": "3-3",
                "requirement_id": "current_gap:GRI301:3-3:a",
                "recommendation_type": "report_content_improvement",
                "priority": "high",
                "current_disclosure": "报告已有部分披露。",
                "gap": "报告未披露完整影响描述。",
                "next_report_addition": "下一期报告可补充影响描述。",
                "requires_internal_data": True,
                "recommendation": "建议补充公开披露。",
                "basis": "基于公开报告和 requirement checks。",
                "review_status": "pending",
            }
        ],
        "overall_recommendation": "建议优先补齐报告披露缺口。",
        "summary": {"total_recommendations": 1},
    }

    result = validate_final_advisor_result(advisor_result, {"current_gap:GRI301:3-3"})

    assert result["status"] == "ok"
    assert result["recommendation_count"] == 1
