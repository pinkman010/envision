"""P0 pending-review API for E4 workbench."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from src.storage.p0_review_store import P0ReviewStore
from src.services.p0_review_export import (
    build_advisor_export_rows,
    build_assessment_export_rows,
    build_review_decision_export_rows,
    export_csv,
    export_json,
)


router = APIRouter()


class ApiResponse(BaseModel):
    code: int = Field(200, description="响应状态码")
    message: str = Field("success", description="响应消息")
    data: Any = Field(..., description="响应数据")


class ReviewDecisionRequest(BaseModel):
    assessment_id: str | None = None
    advisor_item_id: str | None = None
    manifest_item_id: str
    reviewer: str | None = None
    human_verdict: str | None = None
    evidence_page_check: str | None = None
    requirement_gap_check: str | None = None
    advisor_usefulness_rating: str | None = None
    error_type: str | None = None
    correction_note: str | None = None
    review_comment: str | None = None
    source: str = "streamlit"


def get_store() -> P0ReviewStore:
    store = P0ReviewStore()
    store.init_schema()
    return store


@router.get("/runs", response_model=ApiResponse)
async def list_runs() -> ApiResponse:
    return ApiResponse(data=get_store().list_review_runs())


@router.get("/runs/{run_id}/summary", response_model=ApiResponse)
async def get_run_summary(run_id: str) -> ApiResponse:
    try:
        return ApiResponse(data=get_store().get_run_summary(run_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}/assessments", response_model=ApiResponse)
async def list_assessments(
    run_id: str,
    ai_verdict: str | None = None,
    review_status: str | None = None,
    disclosure_id: str | None = None,
    standard_id: str | None = None,
    keyword: str | None = Query(default=None),
) -> ApiResponse:
    filters = _filters(
        ai_verdict=ai_verdict,
        review_status=review_status,
        disclosure_id=disclosure_id,
        standard_id=standard_id,
        keyword=keyword,
    )
    return ApiResponse(data=get_store().list_assessments(run_id, filters=filters))


@router.get("/runs/{run_id}/assessments/{assessment_id}", response_model=ApiResponse)
async def get_assessment(run_id: str, assessment_id: str) -> ApiResponse:
    try:
        return ApiResponse(data=get_store().get_assessment(run_id, assessment_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}/advisor-items", response_model=ApiResponse)
async def list_advisor_items(
    run_id: str,
    coverage_type: str | None = None,
    disclosure_id: str | None = None,
    recommendation_status: str | None = None,
    keyword: str | None = Query(default=None),
) -> ApiResponse:
    filters = _filters(
        coverage_type=coverage_type,
        disclosure_id=disclosure_id,
        recommendation_status=recommendation_status,
        keyword=keyword,
    )
    return ApiResponse(data=get_store().list_advisor_items(run_id, filters=filters))


@router.post("/runs/{run_id}/review-decisions", response_model=ApiResponse)
async def save_review_decision(run_id: str, request: ReviewDecisionRequest) -> ApiResponse:
    payload = request.model_dump()
    payload["run_id"] = run_id
    return ApiResponse(data=get_store().save_review_decision(payload))


@router.get("/runs/{run_id}/review-decisions", response_model=ApiResponse)
async def list_review_decisions(run_id: str) -> ApiResponse:
    return ApiResponse(data=get_store().list_review_decisions(run_id))


@router.get("/runs/{run_id}/exports/assessments.csv")
async def export_assessments_csv(run_id: str) -> Response:
    rows = build_assessment_export_rows(get_store(), run_id)
    return _csv_response(rows, "assessment_review_export.csv")


@router.get("/runs/{run_id}/exports/advisor-items.csv")
async def export_advisor_items_csv(run_id: str) -> Response:
    rows = build_advisor_export_rows(get_store(), run_id)
    return _csv_response(rows, "advisor_review_export.csv")


@router.get("/runs/{run_id}/exports/review-decisions.csv")
async def export_review_decisions_csv(run_id: str) -> Response:
    rows = build_review_decision_export_rows(get_store(), run_id)
    return _csv_response(rows, "review_decisions_export.csv")


@router.get("/runs/{run_id}/exports/assessments.json")
async def export_assessments_json(run_id: str) -> Response:
    rows = build_assessment_export_rows(get_store(), run_id)
    return _json_response(rows, "assessment_review_export.json")


@router.get("/runs/{run_id}/exports/advisor-items.json")
async def export_advisor_items_json(run_id: str) -> Response:
    rows = build_advisor_export_rows(get_store(), run_id)
    return _json_response(rows, "advisor_review_export.json")


@router.get("/runs/{run_id}/exports/review-decisions.json")
async def export_review_decisions_json(run_id: str) -> Response:
    rows = build_review_decision_export_rows(get_store(), run_id)
    return _json_response(rows, "review_decisions_export.json")


def _filters(**kwargs: str | None) -> dict[str, str]:
    return {key: value for key, value in kwargs.items() if value}


def _csv_response(rows: list[dict[str, Any]], filename: str) -> Response:
    return Response(
        content=export_csv(rows),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _json_response(rows: list[dict[str, Any]], filename: str) -> Response:
    return Response(
        content=export_json(rows),
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
