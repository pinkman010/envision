from __future__ import annotations

import shutil
import sqlite3
import uuid
from pathlib import Path

import pytest


@pytest.fixture()
def project_tmp_path():
    path = Path(__file__).resolve().parents[1] / "tmp" / f"stage_e4_store_{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _store(project_tmp_path):
    from src.storage.p0_review_store import P0ReviewStore

    store = P0ReviewStore(db_path=project_tmp_path / "p0_review.sqlite3")
    store.init_schema()
    return store


def _run_payload(run_id: str = "stage-e4-run") -> dict:
    return {
        "run_id": run_id,
        "source_stage": "stage_e_accepted",
        "report_id": "envision-2024",
        "company": "Envision Energy",
        "report_year": 2024,
        "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
        "assessment_count": 2,
        "advisor_coverage_count": 2,
        "review_status": "final",
        "final_evaluation_status": "confirmed",
        "source_manifest": {"files": ["accepted.json"], "note": "中文"},
    }


def _assessments() -> list[dict]:
    return [
        {
            "assessment_id": "assessment-1",
            "manifest_item_id": "current_gap:GRI2:2-1",
            "disclosure_id": "2-1",
            "canonical_disclosure_id": "2-1",
            "standard_id": "GRI2",
            "topic": "Organization",
            "ai_verdict": "fully_disclosed",
            "verdict": "fully_disclosed",
            "review_status": "final",
            "final_evaluation_status": "confirmed",
            "manual_review_reason_codes": ["needs_page_check"],
            "evidence": [{"page": 4, "source_text": "公司名称：远景能源"}],
            "requirement_checks": [{"requirement_id": "r1", "support_status": "met"}],
        },
        {
            "assessment_id": "assessment-2",
            "manifest_item_id": "current_gap:GRI2:2-2",
            "disclosure_id": "2-2",
            "standard_id": "GRI2",
            "topic": "Entities",
            "ai_verdict": "manual_review",
            "review_status": "accepted",
            "final_evaluation_status": "finalized",
            "manual_review_reason_codes": [],
            "evidence": [],
            "requirement_checks": [],
        },
    ]


def _advisor_items() -> list[dict]:
    return [
        {
            "advisor_item_id": "advisor-1",
            "manifest_item_id": "current_gap:GRI2:2-1",
            "disclosure_id": "2-1",
            "canonical_disclosure_id": "2-1",
            "coverage_type": "recommendation",
            "recommendation_status": "confirmed",
            "final_evaluation_status": "finalized",
            "priority": "high",
            "requires_internal_data": True,
            "recommendation_text": "补充披露边界。",
        },
        {
            "advisor_item_id": "advisor-2",
            "manifest_item_id": "current_gap:GRI2:2-2",
            "disclosure_id": "2-2",
            "coverage_type": "no_action",
            "recommendation_status": "final",
            "final_evaluation_status": "confirmed",
            "priority": None,
            "requires_internal_data": False,
            "recommendation_text": None,
        },
    ]


def test_init_schema_creates_stage_e4_tables(project_tmp_path) -> None:
    store = _store(project_tmp_path)

    with sqlite3.connect(store.db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert {
        "p0_review_runs",
        "p0_assessments",
        "p0_advisor_items",
        "p0_review_decisions",
    } <= tables


def test_seed_upserts_are_idempotent_and_normalize_pending_statuses(project_tmp_path) -> None:
    store = _store(project_tmp_path)

    for _ in range(2):
        store.upsert_review_run(_run_payload())
        store.upsert_assessments("stage-e4-run", _assessments())
        store.upsert_advisor_items("stage-e4-run", _advisor_items())

    runs = store.list_review_runs()
    assessments = store.list_assessments("stage-e4-run")
    advisor_items = store.list_advisor_items("stage-e4-run")

    assert len(runs) == 1
    assert len(assessments) == 2
    assert len(advisor_items) == 2
    assert runs[0]["review_status"] == "pending"
    assert runs[0]["final_evaluation_status"] == "pending_human_evaluation"
    assert {item["review_status"] for item in assessments} == {"pending"}
    assert {item["final_evaluation_status"] for item in assessments} == {
        "pending_human_evaluation"
    }
    assert {item["recommendation_status"] for item in advisor_items} == {
        "ai_assisted_pending_human_review"
    }
    assert {item["final_evaluation_status"] for item in advisor_items} == {
        "pending_human_evaluation"
    }


def test_read_methods_support_filters_and_parse_raw_json(project_tmp_path) -> None:
    store = _store(project_tmp_path)
    store.upsert_review_run(_run_payload())
    store.upsert_assessments("stage-e4-run", _assessments())
    store.upsert_advisor_items("stage-e4-run", _advisor_items())

    filtered = store.list_assessments(
        "stage-e4-run",
        filters={"ai_verdict": "manual_review", "standard_id": "GRI2", "keyword": "Entities"},
    )
    assessment = store.get_assessment("stage-e4-run", "assessment-1")
    advisor_items = store.list_advisor_items(
        "stage-e4-run", filters={"coverage_type": "recommendation", "disclosure_id": "2-1"}
    )

    assert [item["assessment_id"] for item in filtered] == ["assessment-2"]
    assert assessment["evidence"] == [{"page": 4, "source_text": "公司名称：远景能源"}]
    assert assessment["raw_assessment"]["assessment_id"] == "assessment-1"
    assert advisor_items[0]["advisor_item_id"] == "advisor-1"
    assert advisor_items[0]["raw_advisor"]["recommendation_text"] == "补充披露边界。"


def test_save_review_decision_generates_stable_id_and_overwrites(project_tmp_path) -> None:
    store = _store(project_tmp_path)
    store.upsert_review_run(_run_payload())
    store.upsert_assessments("stage-e4-run", _assessments())

    first = store.save_review_decision(
        {
            "run_id": "stage-e4-run",
            "assessment_id": "assessment-1",
            "manifest_item_id": "current_gap:GRI2:2-1",
            "reviewer": "reviewer-a",
            "human_verdict": "accepted",
            "source": "manual_workbench",
            "review_comment": "初审",
        }
    )
    second = store.save_review_decision(
        {
            "run_id": "stage-e4-run",
            "assessment_id": "assessment-1",
            "manifest_item_id": "current_gap:GRI2:2-1",
            "reviewer": "reviewer-b",
            "human_verdict": "needs_correction",
            "source": "manual_workbench",
            "review_comment": "复核覆盖",
        }
    )

    decisions = store.list_review_decisions("stage-e4-run")

    assert first["review_decision_id"] == second["review_decision_id"]
    assert len(decisions) == 1
    assert decisions[0]["reviewer"] == "reviewer-b"
    assert decisions[0]["human_verdict"] == "needs_correction"
    assert decisions[0]["review_comment"] == "复核覆盖"


def test_get_run_summary_returns_pending_counts_and_no_final_metrics(project_tmp_path) -> None:
    store = _store(project_tmp_path)
    store.upsert_review_run(_run_payload())
    store.upsert_assessments("stage-e4-run", _assessments())
    store.upsert_advisor_items("stage-e4-run", _advisor_items())

    summary = store.get_run_summary("stage-e4-run")

    assert summary["assessment_count"] == 2
    assert summary["advisor_coverage_count"] == 2
    assert summary["ai_verdict_distribution"] == {
        "fully_disclosed": 1,
        "manual_review": 1,
    }
    assert summary["review_status_counts"] == {"pending": 2}
    assert summary["final_evaluation_status_counts"] == {"pending_human_evaluation": 2}
    assert summary["advisor_recommendation_status_counts"] == {
        "ai_assisted_pending_human_review": 2
    }
    forbidden_metric_keys = {
        "accuracy",
        "precision",
        "recall",
        "final_accuracy",
        "human_verified_count",
        "confirmed_recommendation_count",
    }
    assert not forbidden_metric_keys & set(summary)
