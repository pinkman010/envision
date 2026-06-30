from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.storage.p0_review_store import (
    P0ReviewStore,
    PENDING_ADVISOR_STATUS,
    PENDING_FINAL_EVALUATION_STATUS,
    PENDING_REVIEW_STATUS,
)


DEFAULT_ASSESSMENT_SET_PATH = ROOT_DIR / (
    "data/runs/stage_e_final_assessment_set/"
    "20260630T113930Z_e3_final_current_effective_set_accepted/"
    "final_current_effective_assessment_set.json"
)
DEFAULT_ANALYSIS_RUN_PATH = ROOT_DIR / (
    "data/runs/stage_e_final_assessment_set/"
    "20260630T113930Z_e3_final_current_effective_set_accepted/analysis_run.json"
)
DEFAULT_ADVISOR_RESULT_PATH = ROOT_DIR / (
    "data/runs/stage_e_final_advisor/20260630T114005Z_e3_143_unified_final_advisor/"
    "final_advisor_result_corrected.json"
)
DEFAULT_ADVISOR_REVIEW_SHEET_PATH = ROOT_DIR / (
    "data/runs/stage_f/20260630T132346Z_f_human_evaluation_package/"
    "advisor_review_sheet.json"
)
DEFAULT_CLEANUP_DIR = ROOT_DIR / (
    "data/runs/stage_e_traceability_cleanup/20260630T083619Z_e3_traceability_cleanup"
)
DEFAULT_OUTPUT_ROOT = ROOT_DIR / "data/runs/stage_e4"


def build_seed_payload(
    *,
    assessment_set_path: Path,
    analysis_run_path: Path,
    advisor_result_path: Path,
    advisor_review_sheet_path: Path,
    cleanup_dir: Path,
    expected_assessment_count: int = 143,
    expected_advisor_coverage_count: int = 143,
) -> dict[str, Any]:
    assessment_set = _load_json(assessment_set_path)
    analysis_run = _load_json(analysis_run_path)
    advisor_result = _load_json(advisor_result_path)
    advisor_review_sheet = _load_json(advisor_review_sheet_path)

    assessments = assessment_set.get("assessments") or analysis_run.get("assessments") or []
    if len(assessments) != expected_assessment_count:
        raise ValueError(
            f"assessment count mismatch: expected {expected_assessment_count}, got {len(assessments)}"
        )

    normalized_assessments = [_normalize_assessment(item) for item in assessments]
    advisor_items = _build_advisor_items(
        advisor_result=advisor_result,
        advisor_review_sheet=advisor_review_sheet,
        assessment_manifest_ids={item["manifest_item_id"] for item in normalized_assessments},
    )
    if len(advisor_items) != expected_advisor_coverage_count:
        raise ValueError(
            "advisor coverage count mismatch: "
            f"expected {expected_advisor_coverage_count}, got {len(advisor_items)}"
        )

    source_manifest = _build_source_manifest(
        [
            assessment_set_path,
            analysis_run_path,
            advisor_result_path,
            advisor_review_sheet_path,
            cleanup_dir / "requirement_id_cleanup_map.json",
            cleanup_dir / "evidence_binding_cleanup_map.json",
            cleanup_dir / "pdf_source_text_location_waiver.json",
        ],
        cleanup_dir,
    )
    run = {
        "run_id": analysis_run.get("run_id", assessment_set.get("run_id", "stage_e4_pending_review")),
        "source_stage": "stage_e_final_accepted_pending_review",
        "report_id": analysis_run.get("report_id", "envision_energy_2024_zh"),
        "company": "Envision Energy",
        "report_year": 2024,
        "standard_profile_id": analysis_run.get(
            "standard_profile_id", "gri_p0_2024_current_disclosure_v1"
        ),
        "assessment_count": len(normalized_assessments),
        "advisor_coverage_count": len(advisor_items),
        "review_status": PENDING_REVIEW_STATUS,
        "final_evaluation_status": PENDING_FINAL_EVALUATION_STATUS,
        "source_manifest": source_manifest,
    }
    return {
        "run": run,
        "assessments": normalized_assessments,
        "advisor_items": advisor_items,
        "source_manifest": source_manifest,
    }


def seed_store(store: P0ReviewStore, payload: dict[str, Any]) -> None:
    store.init_schema()
    store.upsert_review_run(payload["run"])
    store.upsert_assessments(payload["run"]["run_id"], payload["assessments"])
    store.upsert_advisor_items(payload["run"]["run_id"], payload["advisor_items"])


def write_seed_summary(payload: dict[str, Any], output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    run_id = payload["run"]["run_id"]
    output_dir = output_root / f"{_timestamp()}_e4_pending_review_seed"
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_id": run_id,
        "created_at": _utc_now(),
        "status": "completed",
        "assessment_count": len(payload["assessments"]),
        "advisor_coverage_count": len(payload["advisor_items"]),
        "review_status": PENDING_REVIEW_STATUS,
        "final_evaluation_status": PENDING_FINAL_EVALUATION_STATUS,
        "source_manifest": payload["source_manifest"],
    }
    summary_path = output_dir / "seed_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed E4 pending-review SQLite store.")
    parser.add_argument("--assessment-set", type=Path, default=DEFAULT_ASSESSMENT_SET_PATH)
    parser.add_argument("--analysis-run", type=Path, default=DEFAULT_ANALYSIS_RUN_PATH)
    parser.add_argument("--advisor-result", type=Path, default=DEFAULT_ADVISOR_RESULT_PATH)
    parser.add_argument("--advisor-review-sheet", type=Path, default=DEFAULT_ADVISOR_REVIEW_SHEET_PATH)
    parser.add_argument("--cleanup-dir", type=Path, default=DEFAULT_CLEANUP_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--db-path", type=Path, default=None)
    args = parser.parse_args(argv)

    payload = build_seed_payload(
        assessment_set_path=args.assessment_set,
        analysis_run_path=args.analysis_run,
        advisor_result_path=args.advisor_result,
        advisor_review_sheet_path=args.advisor_review_sheet,
        cleanup_dir=args.cleanup_dir,
    )
    store = P0ReviewStore(db_path=args.db_path)
    seed_store(store, payload)
    summary_path = write_seed_summary(payload, args.output_root)
    print(f"Seeded E4 pending-review store for {payload['run']['run_id']}")
    print(f"Summary: {summary_path}")
    return 0


def _normalize_assessment(item: dict[str, Any]) -> dict[str, Any]:
    return {
        **item,
        "disclosure_id": item.get("disclosure_id")
        or item.get("canonical_disclosure_id")
        or item["manifest_item_id"].split(":")[-1],
        "ai_verdict": item.get("ai_verdict", item.get("verdict", "")),
        "review_status": PENDING_REVIEW_STATUS,
        "final_evaluation_status": PENDING_FINAL_EVALUATION_STATUS,
    }


def _build_advisor_items(
    *,
    advisor_result: dict[str, Any],
    advisor_review_sheet: dict[str, Any],
    assessment_manifest_ids: set[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    covered_manifest_ids: set[str] = set()
    for recommendation in advisor_result.get("p0_recommendations", []):
        manifest_item_id = recommendation["manifest_item_id"]
        covered_manifest_ids.add(manifest_item_id)
        items.append(
            {
                **recommendation,
                "advisor_item_id": _advisor_item_id(manifest_item_id, recommendation),
                "disclosure_id": recommendation.get("canonical_disclosure_id")
                or manifest_item_id.split(":")[-1],
                "coverage_type": "recommendation",
                "recommendation_status": PENDING_ADVISOR_STATUS,
                "final_evaluation_status": PENDING_FINAL_EVALUATION_STATUS,
                "recommendation_text": recommendation.get("recommendation"),
            }
        )

    rows = _advisor_review_rows(advisor_review_sheet)
    no_action_rows = [
        row
        for row in rows
        if row.get("row_type") == "disclosed_no_action_coverage"
        and row.get("manifest_item_id") in assessment_manifest_ids
        and row.get("manifest_item_id") not in covered_manifest_ids
    ]
    for row in no_action_rows:
        manifest_item_id = row["manifest_item_id"]
        items.append(
            {
                **_drop_human_fields(row),
                "advisor_item_id": _advisor_item_id(manifest_item_id, row),
                "manifest_item_id": manifest_item_id,
                "disclosure_id": row.get("canonical_disclosure_id") or manifest_item_id.split(":")[-1],
                "coverage_type": "no_action",
                "recommendation_status": PENDING_ADVISOR_STATUS,
                "final_evaluation_status": PENDING_FINAL_EVALUATION_STATUS,
                "recommendation_text": None,
                "requires_internal_data": bool(row.get("requires_internal_data", False)),
            }
        )
    return sorted(items, key=lambda item: (item["manifest_item_id"], item["advisor_item_id"]))


def _advisor_review_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("rows", "advisor_review_sheet", "items", "records"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def _drop_human_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in row.items()
        if not key.startswith("human_") and key not in {"reviewer", "reviewed_at"}
    }


def _advisor_item_id(manifest_item_id: str, payload: dict[str, Any]) -> str:
    material = "|".join(
        [
            manifest_item_id,
            payload.get("requirement_id", ""),
            payload.get("recommendation_type", ""),
            payload.get("row_type", ""),
        ]
    )
    return f"advisor_{hashlib.sha256(material.encode('utf-8')).hexdigest()[:16]}"


def _build_source_manifest(paths: list[Path], cleanup_dir: Path) -> dict[str, Any]:
    input_files = []
    for path in paths:
        if path.exists() and path.is_file():
            input_files.append(
                {
                    "path": str(path.as_posix()),
                    "sha256": _sha256(path),
                }
            )
    return {
        "created_at": _utc_now(),
        "input_files": input_files,
        "traceability_cleanup_dir": str(cleanup_dir.as_posix()),
        "stage_boundary": "pending_review_no_final_evaluation_metrics",
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
