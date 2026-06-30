from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _assessment(manifest_item_id: str, verdict: str = "partially_disclosed") -> dict:
    disclosure_id = manifest_item_id.split(":")[-1]
    return {
        "assessment_id": f"assessment-{disclosure_id}",
        "manifest_item_id": manifest_item_id,
        "standard_id": "GRI 2",
        "canonical_disclosure_id": disclosure_id,
        "verdict": verdict,
        "review_status": "accepted",
        "evidence": [],
        "requirement_checks": [],
        "manual_review_reason_codes": [],
    }


def _write_seed_inputs(tmp_path: Path) -> dict[str, Path]:
    assessments = [
        _assessment("current_gap:GRI2:2-1"),
        _assessment("current_gap:GRI2:2-22", "disclosed"),
        _assessment("current_gap:GRI2:2-29", "disclosed"),
    ]
    analysis_run = {
        "run_id": "accepted-run",
        "report_id": "envision_energy_2024_zh",
        "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
        "manifest_version": "accepted-test-v1",
        "status": "completed",
        "source_documents": [],
        "assessments": assessments,
        "review_decisions": [],
        "summary": {},
    }
    advisor_result = {
        "status": "completed",
        "p0_recommendations": [
            {
                "manifest_item_id": "current_gap:GRI2:2-1",
                "canonical_disclosure_id": "2-1",
                "requirement_id": "current_gap:GRI2:2-1:a",
                "recommendation_type": "report_content_improvement",
                "priority": "high",
                "requires_internal_data": False,
                "recommendation": "补充披露。",
                "review_status": "accepted",
            }
        ],
    }
    advisor_review_sheet = {
        "rows": [
            {
                "manifest_item_id": "current_gap:GRI2:2-1",
                "row_type": "advisor_recommendation",
                "recommendation_type": "report_content_improvement",
            },
            {
                "manifest_item_id": "current_gap:GRI2:2-22",
                "canonical_disclosure_id": "2-22",
                "row_type": "disclosed_no_action_coverage",
                "recommendation_type": "no_action",
                "priority": "low",
                "linked_ai_verdict": "disclosed",
                "requires_internal_data": False,
                "gap": "No Advisor recommendation generated because AI verdict is disclosed; coverage row added for human confirmation.",
                "next_report_addition": "",
                "recommendation": "",
                "basis": "Coverage row added to make Advisor review cover all final assessment units.",
                "advisor_review_status": "pending",
                "human_usefulness_rating": "",
                "human_error_type": "",
            },
            {
                "manifest_item_id": "current_gap:GRI2:2-29",
                "canonical_disclosure_id": "2-29",
                "row_type": "disclosed_no_action_coverage",
                "recommendation_type": "no_action",
                "priority": "low",
                "linked_ai_verdict": "disclosed",
                "requires_internal_data": False,
                "gap": "No Advisor recommendation generated because AI verdict is disclosed; coverage row added for human confirmation.",
                "next_report_addition": "",
                "recommendation": "",
                "basis": "Coverage row added to make Advisor review cover all final assessment units.",
                "advisor_review_status": "pending",
                "human_usefulness_rating": "",
                "human_error_type": "",
            },
        ]
    }
    cleanup_dir = tmp_path / "cleanup"
    cleanup_dir.mkdir()
    _write_json(cleanup_dir / "requirement_id_cleanup_map.json", {"items": []})
    _write_json(cleanup_dir / "evidence_binding_cleanup_map.json", {"items": []})
    _write_json(cleanup_dir / "pdf_source_text_location_waiver.json", {"status": "accepted"})
    return {
        "assessment_set": _write_json(
            tmp_path / "final_current_effective_assessment_set.json",
            {"run_id": "accepted-run", "assessments": assessments},
        ),
        "analysis_run": _write_json(tmp_path / "analysis_run.json", analysis_run),
        "advisor_result": _write_json(tmp_path / "final_advisor_result_corrected.json", advisor_result),
        "advisor_review_sheet": _write_json(tmp_path / "advisor_review_sheet.json", advisor_review_sheet),
        "cleanup_dir": cleanup_dir,
    }


def test_build_pending_review_seed_payload_adds_no_action_coverage_and_pending_status(tmp_path: Path):
    from scripts.seed_stage_e4_pending_review import build_seed_payload

    paths = _write_seed_inputs(tmp_path)

    payload = build_seed_payload(
        assessment_set_path=paths["assessment_set"],
        analysis_run_path=paths["analysis_run"],
        advisor_result_path=paths["advisor_result"],
        advisor_review_sheet_path=paths["advisor_review_sheet"],
        cleanup_dir=paths["cleanup_dir"],
        expected_assessment_count=3,
        expected_advisor_coverage_count=3,
    )

    assert payload["run"]["run_id"] == "accepted-run"
    assert payload["run"]["assessment_count"] == 3
    assert payload["run"]["advisor_coverage_count"] == 3
    assert payload["run"]["review_status"] == "pending"
    assert payload["run"]["final_evaluation_status"] == "pending_human_evaluation"
    assert {item["review_status"] for item in payload["assessments"]} == {"pending"}
    assert {item["final_evaluation_status"] for item in payload["assessments"]} == {
        "pending_human_evaluation"
    }
    advisor_items = payload["advisor_items"]
    assert len(advisor_items) == 3
    assert {item["recommendation_status"] for item in advisor_items} == {
        "ai_assisted_pending_human_review"
    }
    assert {
        item["manifest_item_id"]
        for item in advisor_items
        if item["coverage_type"] == "no_action"
    } == {"current_gap:GRI2:2-22", "current_gap:GRI2:2-29"}
    assert all("sha256" in entry for entry in payload["source_manifest"]["input_files"])


def test_build_pending_review_seed_payload_rejects_count_mismatch(tmp_path: Path):
    from scripts.seed_stage_e4_pending_review import build_seed_payload

    paths = _write_seed_inputs(tmp_path)

    with pytest.raises(ValueError, match="assessment count"):
        build_seed_payload(
            assessment_set_path=paths["assessment_set"],
            analysis_run_path=paths["analysis_run"],
            advisor_result_path=paths["advisor_result"],
            advisor_review_sheet_path=paths["advisor_review_sheet"],
            cleanup_dir=paths["cleanup_dir"],
            expected_assessment_count=143,
            expected_advisor_coverage_count=3,
        )


def test_seed_pending_review_store_is_idempotent(tmp_path: Path):
    from scripts.seed_stage_e4_pending_review import build_seed_payload, seed_store
    from src.storage.p0_review_store import P0ReviewStore

    paths = _write_seed_inputs(tmp_path)
    payload = build_seed_payload(
        assessment_set_path=paths["assessment_set"],
        analysis_run_path=paths["analysis_run"],
        advisor_result_path=paths["advisor_result"],
        advisor_review_sheet_path=paths["advisor_review_sheet"],
        cleanup_dir=paths["cleanup_dir"],
        expected_assessment_count=3,
        expected_advisor_coverage_count=3,
    )
    store = P0ReviewStore(db_path=tmp_path / "review.sqlite3")

    seed_store(store, payload)
    seed_store(store, payload)

    summary = store.get_run_summary("accepted-run")
    assert summary["assessment_count"] == 3
    assert summary["advisor_coverage_count"] == 3
    assert summary["final_evaluation_status"] == "pending_human_evaluation"
