from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.storage.p0_review_store import P0ReviewStore


DEFAULT_RUN_ID = "20260630T113930Z_e3_final_current_effective_set_accepted"


def import_review_file(
    store: P0ReviewStore,
    run_id: str,
    review_file: Path,
    *,
    source: str = "f_human_evaluation_import",
) -> dict[str, Any]:
    rows = _load_rows(review_file)
    return import_review_rows(store, run_id, rows, source=source)


def import_review_rows(
    store: P0ReviewStore,
    run_id: str,
    rows: list[dict[str, Any]],
    *,
    source: str = "f_human_evaluation_import",
) -> dict[str, Any]:
    assessment_by_id, assessment_by_manifest, advisor_by_id, advisor_by_manifest = _valid_key_maps(
        store, run_id
    )
    errors: list[dict[str, Any]] = []
    payloads: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        if _is_blank_row(row):
            continue
        payload = _decision_payload_from_row(
            row,
            assessment_by_id=assessment_by_id,
            assessment_by_manifest=assessment_by_manifest,
            advisor_by_id=advisor_by_id,
            advisor_by_manifest=advisor_by_manifest,
            run_id=run_id,
            source=source,
        )
        if payload is None:
            errors.append(
                {
                    "row_number": index,
                    "manifest_item_id": row.get("manifest_item_id") or row.get("review_key"),
                    "assessment_id": row.get("assessment_id"),
                    "advisor_item_id": row.get("advisor_item_id"),
                    "error": "unknown_row_key",
                }
            )
            continue
        payloads.append(payload)

    if errors:
        return {
            "status": "failed",
            "imported_count": 0,
            "error_count": len(errors),
            "errors": errors,
        }

    for payload in payloads:
        store.save_review_decision(payload)
    return {
        "status": "ok",
        "imported_count": len(payloads),
        "error_count": 0,
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import F-stage human review rows into E4 store.")
    parser.add_argument("review_file", type=Path)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--db-path", type=Path, default=None)
    args = parser.parse_args(argv)

    store = P0ReviewStore(db_path=args.db_path)
    store.init_schema()
    result = import_review_file(store, args.run_id, args.review_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 2


def _load_rows(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in (
            "rows",
            "assessment_review_sheet",
            "advisor_review_sheet",
            "items",
            "records",
            "data",
        ):
            if isinstance(payload.get(key), list):
                return payload[key]
    raise ValueError(f"Unsupported review file shape: {path}")


def _valid_key_maps(store: P0ReviewStore, run_id: str):
    assessments = store.list_assessments(run_id)
    advisor_items = store.list_advisor_items(run_id)
    assessment_by_id = {item["assessment_id"]: item for item in assessments}
    assessment_by_manifest = {item["manifest_item_id"]: item for item in assessments}
    advisor_by_id = {item["advisor_item_id"]: item for item in advisor_items}
    advisor_by_manifest = {item["manifest_item_id"]: item for item in advisor_items}
    return assessment_by_id, assessment_by_manifest, advisor_by_id, advisor_by_manifest


def _decision_payload_from_row(
    row: dict[str, Any],
    *,
    assessment_by_id: dict[str, dict[str, Any]],
    assessment_by_manifest: dict[str, dict[str, Any]],
    advisor_by_id: dict[str, dict[str, Any]],
    advisor_by_manifest: dict[str, dict[str, Any]],
    run_id: str,
    source: str,
) -> dict[str, Any] | None:
    row_type = str(row.get("row_type") or "").strip().lower()
    assessment_id = _clean(row.get("assessment_id"))
    advisor_item_id = _clean(row.get("advisor_item_id"))
    manifest_item_id = _clean(row.get("manifest_item_id") or row.get("review_key"))

    assessment = None
    advisor = None
    if advisor_item_id or row_type == "advisor_review":
        advisor = advisor_by_id.get(advisor_item_id or "")
        if advisor is None and manifest_item_id:
            advisor = advisor_by_manifest.get(manifest_item_id)
        if advisor is None:
            return None
        advisor_item_id = advisor["advisor_item_id"]
        manifest_item_id = advisor["manifest_item_id"]
    else:
        assessment = assessment_by_id.get(assessment_id or "")
        if assessment is None and manifest_item_id:
            assessment = assessment_by_manifest.get(manifest_item_id)
        if assessment is None:
            return None
        assessment_id = assessment["assessment_id"]
        manifest_item_id = assessment["manifest_item_id"]

    return {
        "run_id": run_id,
        "assessment_id": assessment_id if assessment else None,
        "advisor_item_id": advisor_item_id if advisor else None,
        "manifest_item_id": manifest_item_id,
        "reviewer": _clean(row.get("reviewer") or row.get("human_reviewer")),
        "human_verdict": _clean(row.get("human_verdict")),
        "evidence_page_check": _clean(row.get("evidence_page_check")),
        "requirement_gap_check": _clean(row.get("requirement_gap_check")),
        "advisor_usefulness_rating": _clean(row.get("advisor_usefulness_rating")),
        "error_type": _clean(row.get("error_type") or row.get("human_error_type")),
        "correction_note": _clean(row.get("correction_note") or row.get("human_correction_note")),
        "review_comment": _clean(row.get("review_comment") or row.get("human_review_comment")),
        "source": source,
    }


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_blank_row(row: dict[str, Any]) -> bool:
    return not any(_clean(value) for value in row.values())


if __name__ == "__main__":
    raise SystemExit(main())
