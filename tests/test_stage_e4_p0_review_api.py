from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _client(tmp_path, monkeypatch) -> TestClient:
    import src.api.p0_review_router as p0_review_router
    from src.storage.p0_review_store import P0ReviewStore

    store = P0ReviewStore(db_path=tmp_path / "api_review.sqlite3")
    store.init_schema()
    store.upsert_review_run(
        {
            "run_id": "api-run",
            "source_stage": "stage_e_accepted",
            "report_id": "envision_energy_2024_zh",
            "company": "Envision Energy",
            "report_year": 2024,
            "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
            "assessment_count": 2,
            "advisor_coverage_count": 2,
            "source_manifest": {"source": "fixture"},
        }
    )
    store.upsert_assessments(
        "api-run",
        [
            {
                "assessment_id": "assessment-1",
                "manifest_item_id": "current_gap:GRI2:2-1",
                "canonical_disclosure_id": "2-1",
                "standard_id": "GRI2",
                "topic": "Organization",
                "verdict": "partially_disclosed",
                "manual_review_reason_codes": [],
                "evidence": [{"source_page": 3, "source_text": "本报告为远景能源有限公司"}],
                "requirement_checks": [],
            },
            {
                "assessment_id": "assessment-2",
                "manifest_item_id": "current_gap:GRI2:2-2",
                "canonical_disclosure_id": "2-2",
                "standard_id": "GRI2",
                "topic": "Entities",
                "verdict": "manual_review",
                "manual_review_reason_codes": ["additional_evidence_needed"],
                "evidence": [],
                "requirement_checks": [],
            },
        ],
    )
    store.upsert_advisor_items(
        "api-run",
        [
            {
                "advisor_item_id": "advisor-1",
                "manifest_item_id": "current_gap:GRI2:2-1",
                "canonical_disclosure_id": "2-1",
                "coverage_type": "recommendation",
                "priority": "high",
                "requires_internal_data": False,
                "recommendation": "补充披露。",
            },
            {
                "advisor_item_id": "advisor-2",
                "manifest_item_id": "current_gap:GRI2:2-22",
                "canonical_disclosure_id": "2-22",
                "coverage_type": "no_action",
                "priority": "low",
                "requires_internal_data": False,
                "recommendation": "",
            },
        ],
    )
    monkeypatch.setattr(p0_review_router, "get_store", lambda: store)
    app = FastAPI()
    app.include_router(p0_review_router.router, prefix="/p0-review")
    return TestClient(app)


def test_p0_review_api_lists_runs_and_summary(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    runs = client.get("/p0-review/runs")
    summary = client.get("/p0-review/runs/api-run/summary")

    assert runs.status_code == 200
    assert runs.json()["data"][0]["run_id"] == "api-run"
    assert summary.status_code == 200
    data = summary.json()["data"]
    assert data["assessment_count"] == 2
    assert data["advisor_coverage_count"] == 2
    assert data["final_evaluation_status"] == "pending_human_evaluation"
    assert "final_accuracy" not in data


def test_p0_review_api_filters_assessments_and_gets_detail(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    filtered = client.get("/p0-review/runs/api-run/assessments", params={"ai_verdict": "manual_review"})
    detail = client.get("/p0-review/runs/api-run/assessments/assessment-1")

    assert filtered.status_code == 200
    assert [item["assessment_id"] for item in filtered.json()["data"]] == ["assessment-2"]
    assert detail.status_code == 200
    assert detail.json()["data"]["evidence"][0]["source_text"] == "本报告为远景能源有限公司"


def test_p0_review_api_saves_review_decision_without_changing_ai_fields(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/p0-review/runs/api-run/review-decisions",
        json={
            "assessment_id": "assessment-1",
            "manifest_item_id": "current_gap:GRI2:2-1",
            "reviewer": "human-a",
            "human_verdict": "partially_disclosed",
            "evidence_page_check": "ok",
            "source": "streamlit",
        },
    )
    decisions = client.get("/p0-review/runs/api-run/review-decisions")
    detail = client.get("/p0-review/runs/api-run/assessments/assessment-1")

    assert response.status_code == 200
    assert response.json()["data"]["human_verdict"] == "partially_disclosed"
    assert decisions.json()["data"][0]["reviewer"] == "human-a"
    assert detail.json()["data"]["ai_verdict"] == "partially_disclosed"
    assert detail.json()["data"]["review_status"] == "pending"


def test_p0_review_api_lists_advisor_items_and_exports_csv(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    advisor_items = client.get("/p0-review/runs/api-run/advisor-items", params={"coverage_type": "no_action"})
    assessment_csv = client.get("/p0-review/runs/api-run/exports/assessments.csv")
    advisor_csv = client.get("/p0-review/runs/api-run/exports/advisor-items.csv")
    review_csv = client.get("/p0-review/runs/api-run/exports/review-decisions.csv")

    assert advisor_items.status_code == 200
    assert advisor_items.json()["data"][0]["coverage_type"] == "no_action"
    for response in (assessment_csv, advisor_csv, review_csv):
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
