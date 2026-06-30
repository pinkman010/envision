import json
from pathlib import Path

from src.utils.p0_index_target_evidence import (
    build_fulltext_requirement_evidence,
    build_index_target_evidence,
    parse_index_target_pages,
)
from src.utils.p0_agent_context import build_p0_requirement_contexts


def test_e2_1_d_regression_expectations_cover_manual_review_findings():
    path = Path("data/review/e2_1_d_regression_expectations.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    by_id = {item["manifest_item_id"]: item for item in payload["items"]}
    expected_ids = {
        "current_gap:GRI2:2-1",
        "current_gap:GRI2:2-21",
        "current_gap:GRI302:302-4",
        "current_gap:GRI306:306-4",
        "current_gap:GRI401:401-1",
        "current_gap:GRI3:3-3_generic",
        "readiness_2026:GRI101",
    }

    assert payload["source_run_id"] == "20260629T140355Z_e2_1_regression"
    assert Path(payload["source_manual_review_result"]).exists()
    assert payload["stage_gate_decision"] == "blocked_before_e3"
    assert len(payload["items"]) == 7
    assert len(by_id) == len(payload["items"])
    assert set(by_id) == expected_ids
    assert by_id["current_gap:GRI2:2-1"]["target_human_verdict"] == "partially_disclosed"
    assert by_id["current_gap:GRI2:2-1"]["target_evidence_pages"] == [2, 27]
    assert by_id["current_gap:GRI2:2-1"]["target_evidence_page_labels"] == ["cover"]
    assert by_id["current_gap:GRI2:2-21"]["target_human_verdict"] == "manual_review"
    assert by_id["current_gap:GRI2:2-21"]["required_manual_review_reason"] == "omission_reason_requires_review"
    assert by_id["current_gap:GRI302:302-4"]["target_human_verdict"] == "partially_disclosed"
    assert by_id["current_gap:GRI302:302-4"]["target_evidence_pages"] == [22, 62]
    assert by_id["current_gap:GRI306:306-4"]["target_human_verdict"] == "partially_disclosed"
    assert by_id["current_gap:GRI306:306-4"]["target_evidence_pages"] == [20, 63]
    assert by_id["current_gap:GRI401:401-1"]["target_human_verdict"] == "partially_disclosed"
    assert by_id["current_gap:GRI401:401-1"]["scope_issues"] == ["current_gap:GRI401:401-1:2.1"]
    assert by_id["current_gap:GRI3:3-3_generic"]["required_manual_review_reason"] == "needs_topic_instantiation"
    assert by_id["readiness_2026:GRI101"]["target_readiness_verdict"] == "readiness_gap"


def test_parse_index_target_pages_from_chinese_index_text():
    assert parse_index_target_pages("\u667a\u6167\u7528\u80fd\uff0c\u8d44\u6e90\u5584\u7528 22\n\u9644\u5f55\u4e00\uff1a\u5173\u952e\u7ee9\u6548\u6570\u636e\u8868 62") == [22, 62]
    assert parse_index_target_pages("\u56e0\u5546\u4e1a\u4fdd\u5bc6\u9650\u5236\u4ece\u7565\u62ab\u9732 /") == []


def test_build_index_target_evidence_fetches_expected_body_pages():
    evidence = build_index_target_evidence(["current_gap:GRI302:302-4"])
    items = evidence["current_gap:GRI302:302-4"]
    page_labels = {item["report_page_label"] for item in items}
    subtypes = {item["evidence_subtype"] for item in items}

    assert "22" in page_labels
    assert "62" in page_labels
    assert all(item["source_page"] == int(item["report_page_label"]) + 1 for item in items)
    assert all(item["evidence_kind"] == "substantive_report_evidence" for item in items)
    assert all(item.get("supports_requirement_ids", []) == [] for item in items)
    assert {"index_referenced_page", "index_referenced_nearby_page"}.issubset(subtypes)


def test_fulltext_requirement_evidence_finds_known_e2_1_c_pages():
    evidence = build_fulltext_requirement_evidence(["current_gap:GRI401:401-1"])
    items = evidence["current_gap:GRI401:401-1"]
    page_labels = {item["report_page_label"] for item in items}

    assert "32" in page_labels
    assert "64" in page_labels
    assert all(item["source_page"] == int(item["report_page_label"]) + 1 for item in items)
    assert all(
        "新进员工" in item["source_text"] or "离职" in item["source_text"]
        for item in items
        if item["report_page_label"] in {"32", "64"}
    )
    assert all(item["evidence_subtype"] == "fulltext_requirement_candidate" for item in items)
    assert all(item["retrieval_method"] == "fulltext_keyword_requirement_candidate" for item in items)


def test_fulltext_requirement_evidence_keeps_pdf_source_page_and_report_page_label_pair():
    evidence = build_fulltext_requirement_evidence(["current_gap:GRI302:302-4"])
    items = evidence["current_gap:GRI302:302-4"]

    evidence_by_label = {item["report_page_label"]: item for item in items}

    assert evidence_by_label["62"]["source_page"] == 63
    assert evidence_by_label["22"]["source_page"] == 23


def test_build_p0_requirement_contexts_keeps_evidence_bundle_layers():
    contexts = build_p0_requirement_contexts()
    context = next(item for item in contexts if item["manifest_item_id"] == "current_gap:GRI302:302-4")
    bundle = context["evidence_bundle"]

    assert bundle["index_evidence"]
    assert bundle["referenced_page_evidence"]
    assert bundle["nearby_page_evidence"]
    assert "fulltext_requirement_evidence" in bundle


def test_index_evidence_does_not_claim_support_for_all_requirements():
    contexts = build_p0_requirement_contexts()
    context = next(item for item in contexts if item["manifest_item_id"] == "current_gap:GRI302:302-4")
    index_items = context["evidence_bundle"]["index_evidence"]

    assert index_items
    assert all(item["evidence_kind"] == "index_evidence" for item in index_items)
    assert all(item.get("supports_requirement_ids", []) == [] for item in index_items)
    assert all(item["evidence_subtype"] == "gri_content_index_locator" for item in index_items)
    assert any("locator only" in item["judgment_reason"].lower() for item in index_items)
    assert any("source_text_extraction_warning" in item for item in index_items)


