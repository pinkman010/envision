"""SQLite persistence for P0 pending-review workflows."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config.paths import SQLITE_DB_DIR
from src.config.settings import settings


PENDING_REVIEW_STATUS = "pending"
PENDING_FINAL_EVALUATION_STATUS = "pending_human_evaluation"
PENDING_ADVISOR_STATUS = "ai_assisted_pending_human_review"


class P0ReviewStore:
    """Small SQLite store for E4 pending-review data."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = SQLITE_DB_DIR / settings.SQLITE_DB_NAME
        self.db_path = Path(db_path)

    def init_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS p0_review_runs (
                    run_id TEXT PRIMARY KEY,
                    source_stage TEXT NOT NULL,
                    report_id TEXT NOT NULL,
                    company TEXT,
                    report_year INTEGER,
                    standard_profile_id TEXT,
                    assessment_count INTEGER NOT NULL,
                    advisor_coverage_count INTEGER NOT NULL,
                    review_status TEXT NOT NULL,
                    final_evaluation_status TEXT NOT NULL,
                    source_manifest_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS p0_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    manifest_item_id TEXT NOT NULL,
                    disclosure_id TEXT NOT NULL,
                    standard_id TEXT,
                    topic TEXT,
                    ai_verdict TEXT NOT NULL,
                    review_status TEXT NOT NULL,
                    final_evaluation_status TEXT NOT NULL,
                    manual_review_reason_codes_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    requirement_checks_json TEXT NOT NULL,
                    raw_assessment_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES p0_review_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS p0_advisor_items (
                    advisor_item_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    manifest_item_id TEXT NOT NULL,
                    disclosure_id TEXT NOT NULL,
                    coverage_type TEXT NOT NULL,
                    recommendation_status TEXT NOT NULL,
                    final_evaluation_status TEXT NOT NULL,
                    priority TEXT,
                    requires_internal_data INTEGER NOT NULL DEFAULT 0,
                    recommendation_text TEXT,
                    raw_advisor_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES p0_review_runs(run_id)
                );

                CREATE TABLE IF NOT EXISTS p0_review_decisions (
                    review_decision_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    assessment_id TEXT,
                    advisor_item_id TEXT,
                    manifest_item_id TEXT NOT NULL,
                    reviewer TEXT,
                    human_verdict TEXT,
                    evidence_page_check TEXT,
                    requirement_gap_check TEXT,
                    advisor_usefulness_rating TEXT,
                    error_type TEXT,
                    correction_note TEXT,
                    review_comment TEXT,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES p0_review_runs(run_id)
                );
                """
            )

    def upsert_review_run(self, run_payload: dict[str, Any]) -> None:
        now = _utc_now()
        source_manifest = run_payload.get("source_manifest", run_payload.get("source_manifest_json", {}))
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM p0_review_runs WHERE run_id = ?",
                (run_payload["run_id"],),
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO p0_review_runs (
                    run_id, source_stage, report_id, company, report_year,
                    standard_profile_id, assessment_count, advisor_coverage_count,
                    review_status, final_evaluation_status, source_manifest_json,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    source_stage = excluded.source_stage,
                    report_id = excluded.report_id,
                    company = excluded.company,
                    report_year = excluded.report_year,
                    standard_profile_id = excluded.standard_profile_id,
                    assessment_count = excluded.assessment_count,
                    advisor_coverage_count = excluded.advisor_coverage_count,
                    review_status = excluded.review_status,
                    final_evaluation_status = excluded.final_evaluation_status,
                    source_manifest_json = excluded.source_manifest_json,
                    updated_at = excluded.updated_at
                """,
                (
                    run_payload["run_id"],
                    run_payload.get("source_stage", "stage_e_accepted"),
                    run_payload["report_id"],
                    run_payload.get("company"),
                    run_payload.get("report_year"),
                    run_payload.get("standard_profile_id"),
                    int(run_payload.get("assessment_count", 0)),
                    int(run_payload.get("advisor_coverage_count", 0)),
                    PENDING_REVIEW_STATUS,
                    PENDING_FINAL_EVALUATION_STATUS,
                    _to_json(source_manifest),
                    created_at,
                    now,
                ),
            )

    def upsert_assessments(self, run_id: str, assessments: list[dict[str, Any]]) -> None:
        now = _utc_now()
        with self._connect() as conn:
            for assessment in assessments:
                existing = conn.execute(
                    "SELECT created_at FROM p0_assessments WHERE assessment_id = ?",
                    (assessment["assessment_id"],),
                ).fetchone()
                created_at = existing["created_at"] if existing else now
                conn.execute(
                    """
                    INSERT INTO p0_assessments (
                        assessment_id, run_id, manifest_item_id, disclosure_id, standard_id,
                        topic, ai_verdict, review_status, final_evaluation_status,
                        manual_review_reason_codes_json, evidence_json,
                        requirement_checks_json, raw_assessment_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(assessment_id) DO UPDATE SET
                        run_id = excluded.run_id,
                        manifest_item_id = excluded.manifest_item_id,
                        disclosure_id = excluded.disclosure_id,
                        standard_id = excluded.standard_id,
                        topic = excluded.topic,
                        ai_verdict = excluded.ai_verdict,
                        review_status = excluded.review_status,
                        final_evaluation_status = excluded.final_evaluation_status,
                        manual_review_reason_codes_json = excluded.manual_review_reason_codes_json,
                        evidence_json = excluded.evidence_json,
                        requirement_checks_json = excluded.requirement_checks_json,
                        raw_assessment_json = excluded.raw_assessment_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        assessment["assessment_id"],
                        run_id,
                        assessment["manifest_item_id"],
                        _disclosure_id(assessment),
                        assessment.get("standard_id"),
                        assessment.get("topic"),
                        assessment.get("ai_verdict", assessment.get("verdict", "")),
                        PENDING_REVIEW_STATUS,
                        PENDING_FINAL_EVALUATION_STATUS,
                        _to_json(assessment.get("manual_review_reason_codes", [])),
                        _to_json(assessment.get("evidence", [])),
                        _to_json(assessment.get("requirement_checks", [])),
                        _to_json(assessment),
                        created_at,
                        now,
                    ),
                )

    def upsert_advisor_items(self, run_id: str, advisor_items: list[dict[str, Any]]) -> None:
        now = _utc_now()
        with self._connect() as conn:
            for item in advisor_items:
                advisor_item_id = item.get("advisor_item_id") or _stable_id(
                    "advisor",
                    run_id,
                    item["manifest_item_id"],
                    item.get("requirement_id", ""),
                    item.get("coverage_type", ""),
                )
                existing = conn.execute(
                    "SELECT created_at FROM p0_advisor_items WHERE advisor_item_id = ?",
                    (advisor_item_id,),
                ).fetchone()
                created_at = existing["created_at"] if existing else now
                conn.execute(
                    """
                    INSERT INTO p0_advisor_items (
                        advisor_item_id, run_id, manifest_item_id, disclosure_id,
                        coverage_type, recommendation_status, final_evaluation_status,
                        priority, requires_internal_data, recommendation_text,
                        raw_advisor_json, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(advisor_item_id) DO UPDATE SET
                        run_id = excluded.run_id,
                        manifest_item_id = excluded.manifest_item_id,
                        disclosure_id = excluded.disclosure_id,
                        coverage_type = excluded.coverage_type,
                        recommendation_status = excluded.recommendation_status,
                        final_evaluation_status = excluded.final_evaluation_status,
                        priority = excluded.priority,
                        requires_internal_data = excluded.requires_internal_data,
                        recommendation_text = excluded.recommendation_text,
                        raw_advisor_json = excluded.raw_advisor_json,
                        updated_at = excluded.updated_at
                    """,
                    (
                        advisor_item_id,
                        run_id,
                        item["manifest_item_id"],
                        _disclosure_id(item),
                        item.get("coverage_type", "recommendation"),
                        PENDING_ADVISOR_STATUS,
                        PENDING_FINAL_EVALUATION_STATUS,
                        item.get("priority"),
                        1 if item.get("requires_internal_data") else 0,
                        item.get("recommendation_text") or item.get("recommendation"),
                        _to_json({**item, "advisor_item_id": advisor_item_id}),
                        created_at,
                        now,
                    ),
                )

    def save_review_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = _utc_now()
        review_decision_id = payload.get("review_decision_id") or _stable_id(
            "review",
            payload["run_id"],
            payload["manifest_item_id"],
            payload.get("assessment_id", ""),
            payload.get("advisor_item_id", ""),
            payload.get("source", ""),
        )
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM p0_review_decisions WHERE review_decision_id = ?",
                (review_decision_id,),
            ).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO p0_review_decisions (
                    review_decision_id, run_id, assessment_id, advisor_item_id,
                    manifest_item_id, reviewer, human_verdict, evidence_page_check,
                    requirement_gap_check, advisor_usefulness_rating, error_type,
                    correction_note, review_comment, source, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_decision_id) DO UPDATE SET
                    run_id = excluded.run_id,
                    assessment_id = excluded.assessment_id,
                    advisor_item_id = excluded.advisor_item_id,
                    manifest_item_id = excluded.manifest_item_id,
                    reviewer = excluded.reviewer,
                    human_verdict = excluded.human_verdict,
                    evidence_page_check = excluded.evidence_page_check,
                    requirement_gap_check = excluded.requirement_gap_check,
                    advisor_usefulness_rating = excluded.advisor_usefulness_rating,
                    error_type = excluded.error_type,
                    correction_note = excluded.correction_note,
                    review_comment = excluded.review_comment,
                    source = excluded.source,
                    updated_at = excluded.updated_at
                """,
                (
                    review_decision_id,
                    payload["run_id"],
                    payload.get("assessment_id"),
                    payload.get("advisor_item_id"),
                    payload["manifest_item_id"],
                    payload.get("reviewer"),
                    payload.get("human_verdict"),
                    payload.get("evidence_page_check"),
                    payload.get("requirement_gap_check"),
                    payload.get("advisor_usefulness_rating"),
                    payload.get("error_type"),
                    payload.get("correction_note"),
                    payload.get("review_comment"),
                    payload.get("source", "streamlit"),
                    created_at,
                    now,
                ),
            )
        return self._get_review_decision(review_decision_id)

    def list_review_runs(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM p0_review_runs ORDER BY created_at DESC").fetchall()
        return [_row_to_run(row) for row in rows]

    def get_run_summary(self, run_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            run = conn.execute("SELECT * FROM p0_review_runs WHERE run_id = ?", (run_id,)).fetchone()
            if run is None:
                raise KeyError(f"Run not found: {run_id}")
            assessments = conn.execute(
                "SELECT ai_verdict, review_status, final_evaluation_status FROM p0_assessments WHERE run_id = ?",
                (run_id,),
            ).fetchall()
            advisor_items = conn.execute(
                "SELECT recommendation_status, final_evaluation_status FROM p0_advisor_items WHERE run_id = ?",
                (run_id,),
            ).fetchall()
        return {
            "run_id": run["run_id"],
            "report_id": run["report_id"],
            "standard_profile_id": run["standard_profile_id"],
            "assessment_count": len(assessments),
            "advisor_coverage_count": len(advisor_items),
            "review_status": run["review_status"],
            "final_evaluation_status": run["final_evaluation_status"],
            "ai_verdict_distribution": dict(Counter(row["ai_verdict"] for row in assessments)),
            "review_status_counts": dict(Counter(row["review_status"] for row in assessments)),
            "final_evaluation_status_counts": dict(
                Counter(row["final_evaluation_status"] for row in assessments)
            ),
            "advisor_recommendation_status_counts": dict(
                Counter(row["recommendation_status"] for row in advisor_items)
            ),
            "advisor_final_evaluation_status_counts": dict(
                Counter(row["final_evaluation_status"] for row in advisor_items)
            ),
        }

    def list_assessments(
        self, run_id: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        query = "SELECT * FROM p0_assessments WHERE run_id = ?"
        params: list[Any] = [run_id]
        for field in ("ai_verdict", "review_status", "disclosure_id", "standard_id"):
            if filters.get(field):
                query += f" AND {field} = ?"
                params.append(filters[field])
        keyword = filters.get("keyword")
        if keyword:
            query += (
                " AND (manifest_item_id LIKE ? OR disclosure_id LIKE ? OR standard_id LIKE ? "
                "OR topic LIKE ? OR raw_assessment_json LIKE ?)"
            )
            like = f"%{keyword}%"
            params.extend([like, like, like, like, like])
        query += " ORDER BY manifest_item_id"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_assessment(row) for row in rows]

    def get_assessment(self, run_id: str, assessment_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM p0_assessments WHERE run_id = ? AND assessment_id = ?",
                (run_id, assessment_id),
            ).fetchone()
        if row is None:
            raise KeyError(f"Assessment not found: {assessment_id}")
        return _row_to_assessment(row)

    def list_advisor_items(
        self, run_id: str, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        query = "SELECT * FROM p0_advisor_items WHERE run_id = ?"
        params: list[Any] = [run_id]
        for field in ("coverage_type", "disclosure_id", "recommendation_status"):
            if filters.get(field):
                query += f" AND {field} = ?"
                params.append(filters[field])
        keyword = filters.get("keyword")
        if keyword:
            query += (
                " AND (manifest_item_id LIKE ? OR disclosure_id LIKE ? "
                "OR recommendation_text LIKE ? OR raw_advisor_json LIKE ?)"
            )
            like = f"%{keyword}%"
            params.extend([like, like, like, like])
        query += " ORDER BY manifest_item_id, advisor_item_id"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_advisor_item(row) for row in rows]

    def list_review_decisions(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM p0_review_decisions WHERE run_id = ? ORDER BY updated_at DESC",
                (run_id,),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def _get_review_decision(self, review_decision_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM p0_review_decisions WHERE review_decision_id = ?",
                (review_decision_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Review decision not found: {review_decision_id}")
        return _row_to_dict(row)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _from_json(value: str) -> Any:
    return json.loads(value) if value else None


def _stable_id(prefix: str, *parts: Any) -> str:
    material = "|".join("" if part is None else str(part) for part in parts)
    return f"{prefix}_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:16]}"


def _disclosure_id(payload: dict[str, Any]) -> str:
    return (
        payload.get("disclosure_id")
        or payload.get("canonical_disclosure_id")
        or str(payload["manifest_item_id"]).split(":")[-1]
    )


def _row_to_run(row: sqlite3.Row) -> dict[str, Any]:
    data = _row_to_dict(row)
    data["source_manifest"] = _from_json(data.pop("source_manifest_json"))
    return data


def _row_to_assessment(row: sqlite3.Row) -> dict[str, Any]:
    data = _row_to_dict(row)
    data["manual_review_reason_codes"] = _from_json(data.pop("manual_review_reason_codes_json"))
    data["evidence"] = _from_json(data.pop("evidence_json"))
    data["requirement_checks"] = _from_json(data.pop("requirement_checks_json"))
    data["raw_assessment"] = _from_json(data.pop("raw_assessment_json"))
    return data


def _row_to_advisor_item(row: sqlite3.Row) -> dict[str, Any]:
    data = _row_to_dict(row)
    data["requires_internal_data"] = bool(data["requires_internal_data"])
    data["raw_advisor"] = _from_json(data.pop("raw_advisor_json"))
    return data


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}
