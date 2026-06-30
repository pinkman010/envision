from __future__ import annotations

import csv
import json
from pathlib import Path


def _seed_store(tmp_path):
    from src.storage.p0_review_store import P0ReviewStore

    store = P0ReviewStore(db_path=tmp_path / "f_import.sqlite3")
    store.init_schema()
    store.upsert_review_run(
        {
            "run_id": "f-import-run",
            "source_stage": "stage_e_accepted",
            "report_id": "envision_energy_2024_zh",
            "company": "Envision Energy",
            "report_year": 2024,
            "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
            "assessment_count": 1,
            "advisor_coverage_count": 1,
            "source_manifest": {"source": "fixture"},
        }
    )
    store.upsert_assessments(
        "f-import-run",
        [
            {
                "assessment_id": "assessment-1",
                "manifest_item_id": "current_gap:GRI302:302-4",
                "canonical_disclosure_id": "302-4",
                "standard_id": "GRI302",
                "verdict": "partially_disclosed",
                "manual_review_reason_codes": [],
                "evidence": [],
                "requirement_checks": [],
            }
        ],
    )
    store.upsert_advisor_items(
        "f-import-run",
        [
            {
                "advisor_item_id": "advisor-1",
                "manifest_item_id": "current_gap:GRI302:302-4",
                "canonical_disclosure_id": "302-4",
                "coverage_type": "recommendation",
                "priority": "high",
                "requires_internal_data": True,
                "recommendation": "补充披露计算方法。",
            }
        ],
    )
    return store


def test_import_f_review_json_rows_upserts_assessment_and_advisor_decisions(tmp_path: Path):
    from scripts.import_f_human_review_results import import_review_file

    store = _seed_store(tmp_path)
    review_path = tmp_path / "f_review.json"
    review_path.write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "row_type": "assessment_review",
                        "assessment_id": "assessment-1",
                        "manifest_item_id": "current_gap:GRI302:302-4",
                        "human_verdict": "partially_disclosed",
                        "evidence_page_check": "ok",
                        "requirement_gap_check": "ok",
                        "error_type": "none",
                        "correction_note": "人工确认。",
                        "reviewer": "reviewer-a",
                        "review_comment": "JSON import",
                    },
                    {
                        "row_type": "advisor_review",
                        "advisor_item_id": "advisor-1",
                        "manifest_item_id": "current_gap:GRI302:302-4",
                        "advisor_usefulness_rating": "useful",
                        "error_type": "none",
                        "correction_note": "建议可用。",
                        "reviewer": "reviewer-a",
                        "review_comment": "Advisor JSON import",
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = import_review_file(store, "f-import-run", review_path)
    result_again = import_review_file(store, "f-import-run", review_path)
    decisions = store.list_review_decisions("f-import-run")

    assert result["status"] == "ok"
    assert result["imported_count"] == 2
    assert result_again["imported_count"] == 2
    assert len(decisions) == 2
    assert {decision["source"] for decision in decisions} == {"f_human_evaluation_import"}
    assert {decision["reviewer"] for decision in decisions} == {"reviewer-a"}


def test_import_f_review_csv_rejects_unknown_row_key(tmp_path: Path):
    from scripts.import_f_human_review_results import import_review_file

    store = _seed_store(tmp_path)
    review_path = tmp_path / "f_review.csv"
    with review_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "row_type",
                "assessment_id",
                "manifest_item_id",
                "human_verdict",
                "reviewer",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "row_type": "assessment_review",
                "assessment_id": "missing-assessment",
                "manifest_item_id": "current_gap:GRI999:999-9",
                "human_verdict": "not_disclosed",
                "reviewer": "reviewer-b",
            }
        )

    result = import_review_file(store, "f-import-run", review_path)

    assert result["status"] == "failed"
    assert result["imported_count"] == 0
    assert result["errors"][0]["error"] == "unknown_row_key"
    assert store.list_review_decisions("f-import-run") == []


def test_import_f_review_preserves_ai_raw_assessment(tmp_path: Path):
    from scripts.import_f_human_review_results import import_review_file

    store = _seed_store(tmp_path)
    before = store.get_assessment("f-import-run", "assessment-1")
    review_path = tmp_path / "f_review.json"
    review_path.write_text(
        json.dumps(
            [
                {
                    "assessment_id": "assessment-1",
                    "manifest_item_id": "current_gap:GRI302:302-4",
                    "human_verdict": "not_disclosed",
                    "reviewer": "reviewer-c",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    import_review_file(store, "f-import-run", review_path)
    after = store.get_assessment("f-import-run", "assessment-1")

    assert before["ai_verdict"] == "partially_disclosed"
    assert after["ai_verdict"] == "partially_disclosed"
    assert after["review_status"] == "pending"
