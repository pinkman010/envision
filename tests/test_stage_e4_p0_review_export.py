from __future__ import annotations

import csv
import io
import json


def _seed_store(tmp_path):
    from src.storage.p0_review_store import P0ReviewStore

    store = P0ReviewStore(db_path=tmp_path / "export.sqlite3")
    store.init_schema()
    store.upsert_review_run(
        {
            "run_id": "export-run",
            "source_stage": "stage_e_accepted",
            "report_id": "envision_energy_2024_zh",
            "company": "Envision Energy",
            "report_year": 2024,
            "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
            "assessment_count": 1,
            "advisor_coverage_count": 1,
            "source_manifest": {"traceability_cleanup_dir": "cleanup-dir"},
        }
    )
    store.upsert_assessments(
        "export-run",
        [
            {
                "assessment_id": "assessment-1",
                "manifest_item_id": "current_gap:GRI302:302-4",
                "canonical_disclosure_id": "302-4",
                "standard_id": "GRI302",
                "topic": "energy",
                "verdict": "partially_disclosed",
                "manual_review_reason_codes": ["weak_evidence_support"],
                "evidence": [
                    {
                        "evidence_id": "evidence-1",
                        "chunk_id": "chunk-1",
                        "source_page": 63,
                        "report_page_label": "62",
                        "source_text": "节能措施促成的节电量 292,106.00 kWh",
                    }
                ],
                "requirement_checks": [
                    {
                        "requirement_id": "current_gap:GRI302:302-4:a",
                        "support_status": "met",
                    }
                ],
            }
        ],
    )
    store.upsert_advisor_items(
        "export-run",
        [
            {
                "advisor_item_id": "advisor-1",
                "manifest_item_id": "current_gap:GRI302:302-4",
                "canonical_disclosure_id": "302-4",
                "coverage_type": "recommendation",
                "priority": "high",
                "requires_internal_data": True,
                "recommendation": "补充披露计算方法。",
                "basis": "基于 requirement checks。",
            }
        ],
    )
    store.save_review_decision(
        {
            "run_id": "export-run",
            "assessment_id": "assessment-1",
            "manifest_item_id": "current_gap:GRI302:302-4",
            "reviewer": "reviewer-a",
            "human_verdict": "partially_disclosed",
            "evidence_page_check": "ok",
            "requirement_gap_check": "ok",
            "error_type": "none",
            "source": "streamlit",
        }
    )
    return store


def test_assessment_export_rows_keep_ai_human_traceability_and_pending_status(tmp_path):
    from src.services.p0_review_export import build_assessment_export_rows

    rows = build_assessment_export_rows(_seed_store(tmp_path), "export-run")

    assert rows[0]["assessment_id"] == "assessment-1"
    assert rows[0]["ai_verdict"] == "partially_disclosed"
    assert rows[0]["human_verdict"] == "partially_disclosed"
    assert rows[0]["review_status"] == "pending"
    assert rows[0]["final_evaluation_status"] == "pending_human_evaluation"
    assert rows[0]["requirement_ids"] == "current_gap:GRI302:302-4:a"
    assert rows[0]["evidence_ids"] == "evidence-1"
    assert rows[0]["chunk_ids"] == "chunk-1"
    assert rows[0]["source_pages"] == "63"
    assert rows[0]["report_page_labels"] == "62"
    assert rows[0]["source_text_preview"].startswith("节能措施促成")
    assert "final_accuracy" not in rows[0]


def test_advisor_and_review_decision_exports_keep_pending_recommendation_status(tmp_path):
    from src.services.p0_review_export import (
        build_advisor_export_rows,
        build_review_decision_export_rows,
    )

    store = _seed_store(tmp_path)
    advisor_rows = build_advisor_export_rows(store, "export-run")
    decision_rows = build_review_decision_export_rows(store, "export-run")

    assert advisor_rows[0]["advisor_item_id"] == "advisor-1"
    assert advisor_rows[0]["recommendation_status"] == "ai_assisted_pending_human_review"
    assert advisor_rows[0]["final_evaluation_status"] == "pending_human_evaluation"
    assert advisor_rows[0]["recommendation_text"] == "补充披露计算方法。"
    assert decision_rows[0]["reviewer"] == "reviewer-a"
    assert decision_rows[0]["source"] == "streamlit"


def test_export_csv_and_json_shapes(tmp_path):
    from src.services.p0_review_export import export_csv, export_json

    rows = [
        {
            "manifest_item_id": "current_gap:GRI302:302-4",
            "ai_verdict": "partially_disclosed",
            "evidence_ids": "evidence-1",
        }
    ]

    csv_text = export_csv(rows)
    json_text = export_json(rows)

    parsed_csv = list(csv.DictReader(io.StringIO(csv_text)))
    parsed_json = json.loads(json_text)
    assert parsed_csv[0]["manifest_item_id"] == "current_gap:GRI302:302-4"
    assert parsed_json[0]["evidence_ids"] == "evidence-1"
