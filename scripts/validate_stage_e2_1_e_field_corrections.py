"""Validate Stage E2.1-E manual field correction expectations.

This validator is local and read-only. It does not call LLMs, rebuild indexes,
or modify run artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_MANUAL_REVIEW_RESULT_PATH = (
    PROJECT_ROOT
    / "data"
    / "runs"
    / "stage_e"
    / "20260629T170447Z_e2_1_regression"
    / "manual_review_result.json"
)
DEFAULT_EXPECTATION_PATH = (
    PROJECT_ROOT / "data" / "review" / "e2_1_e_field_correction_expectations.json"
)

EXPECTED_STAGE_GATE_DECISION = "conditionally_passed_before_e3"
EXPECTED_ITEM_COUNT = 7
MODE = "e2_1_e_field_corrections"

REQUIREMENT_LIST_FIELDS = {
    "partial_requirements",
    "missing_requirements",
    "not_scored_requirements",
}
SCALAR_OR_LIST_FIELDS = {
    "manual_review_reason_codes",
    "readiness_verdict",
    "current_gap_verdict",
    "not_scored_reason",
    "omission_review_subtype",
}


def _load_json_with_text(path: Path) -> tuple[Any, str]:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text), text


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _items_by_id(payload: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(payload, dict):
        return {}
    items: dict[str, dict[str, Any]] = {}
    for item in _as_list(payload.get("items")):
        if not isinstance(item, dict):
            continue
        manifest_item_id = item.get("manifest_item_id")
        if manifest_item_id:
            items[str(manifest_item_id)] = item
    return items


def _raw_items(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    return [item for item in _as_list(payload.get("items")) if isinstance(item, dict)]


def _duplicate_item_ids(items: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in items:
        manifest_item_id = str(item.get("manifest_item_id", ""))
        if not manifest_item_id:
            continue
        if manifest_item_id in seen:
            duplicates.add(manifest_item_id)
        seen.add(manifest_item_id)
    return sorted(duplicates)


def _find_encoding_errors(raw_texts: list[tuple[str, str]]) -> list[str]:
    errors: list[str] = []
    cjk_question = re.compile(r"[\u4e00-\u9fff]\?[\u4e00-\u9fff]|\?\?+")

    for label, text in raw_texts:
        if "\ufffd" in text:
            errors.append(f"{label}: contains Unicode replacement character U+FFFD")
        if cjk_question.search(text):
            errors.append(f"{label}: contains likely mojibake '?' inside Chinese text")

    return errors


def _field_corrections(item: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(item.get("field_corrections"))


def _value_from_item_or_corrections(item: dict[str, Any], field_name: str) -> Any:
    if field_name in item:
        return item[field_name]

    corrections = _field_corrections(item)
    if field_name in corrections:
        return corrections[field_name]

    if field_name == "not_scored_reason":
        scoring_status = corrections.get("scoring_status")
        if scoring_status == "not_scored_requires_topic_instantiation":
            return scoring_status

    return None


def _normalize_requirement_corrections(item: dict[str, Any]) -> dict[str, str]:
    corrections = _field_corrections(item).get("missing_requirement_corrections")
    if not isinstance(corrections, dict):
        return {}
    return {str(requirement_id): str(status) for requirement_id, status in corrections.items()}


def _derived_requirement_ids(item: dict[str, Any], field_name: str) -> set[str]:
    explicit = _value_from_item_or_corrections(item, field_name)
    if isinstance(explicit, list):
        return {str(value) for value in explicit}

    statuses = _normalize_requirement_corrections(item)
    if field_name == "partial_requirements":
        return {
            requirement_id
            for requirement_id, status in statuses.items()
            if status.startswith("partial") or "_partial" in status
        }
    if field_name == "missing_requirements":
        return {requirement_id for requirement_id, status in statuses.items() if status.startswith("not_met")}
    if field_name == "not_scored_requirements":
        return {requirement_id for requirement_id, status in statuses.items() if status.startswith("not_scored")}
    return set()


def _requirement_covered(item: dict[str, Any], expected_requirement_id: str, field_name: str) -> bool:
    derived_ids = _derived_requirement_ids(item, field_name)
    return expected_requirement_id in derived_ids


def _pages_from_structured_corrections(item: dict[str, Any]) -> set[tuple[int, str]]:
    pages: set[tuple[int, str]] = set()
    candidates: list[Any] = []
    explicit = _value_from_item_or_corrections(item, "required_evidence_pages")
    candidates.extend(_as_list(explicit))
    candidates.extend(_as_list(_field_corrections(item).get("evidence_pages_to_add")))

    for page in candidates:
        if not isinstance(page, dict):
            continue
        source_page = page.get("source_page")
        report_page_label = page.get("report_page_label")
        if source_page is None or report_page_label is None:
            continue
        try:
            pages.add((int(source_page), str(report_page_label)))
        except (TypeError, ValueError):
            continue
    return pages


def _page_covered(item: dict[str, Any], expected_page: dict[str, Any]) -> bool:
    source_page = expected_page.get("source_page")
    report_page_label = str(expected_page.get("report_page_label"))
    try:
        source_page_int = int(source_page)
    except (TypeError, ValueError):
        return False

    if (source_page_int, report_page_label) in _pages_from_structured_corrections(item):
        return True

    return False


def _compare_expected_field(
    manifest_item_id: str,
    manual_item: dict[str, Any],
    expected_item: dict[str, Any],
    field_name: str,
) -> list[str]:
    errors: list[str] = []
    expected_value = expected_item.get(field_name)
    if expected_value is None:
        return errors

    if field_name == "required_evidence_pages":
        for expected_page in _as_list(expected_value):
            if not isinstance(expected_page, dict):
                errors.append(f"{manifest_item_id}: expected required_evidence_pages entry is not object")
                continue
            if not _page_covered(manual_item, expected_page):
                errors.append(f"{manifest_item_id}: missing required_evidence_pages entry {expected_page}")
        return errors

    if field_name in REQUIREMENT_LIST_FIELDS:
        for requirement_id in {str(value) for value in _as_list(expected_value)}:
            if not _requirement_covered(manual_item, requirement_id, field_name):
                errors.append(f"{manifest_item_id}: missing {field_name} entry {requirement_id}")
        return errors

    actual_value = _value_from_item_or_corrections(manual_item, field_name)
    if actual_value != expected_value:
        errors.append(f"{manifest_item_id}: {field_name} expected {expected_value!r}, got {actual_value!r}")
    return errors


def validate_e2_1_e_field_corrections(
    manual_review_result_path: Path = DEFAULT_MANUAL_REVIEW_RESULT_PATH,
    expectation_path: Path = DEFAULT_EXPECTATION_PATH,
) -> dict[str, Any]:
    """Validate manual review field corrections against E2.1-E expectations."""
    manual_payload, manual_text = _load_json_with_text(Path(manual_review_result_path))
    expectation_payload, expectation_text = _load_json_with_text(Path(expectation_path))

    errors = _find_encoding_errors(
        [
            (str(manual_review_result_path), manual_text),
            (str(expectation_path), expectation_text),
        ]
    )
    warnings: list[str] = []

    stage_gate_decision = None
    if isinstance(manual_payload, dict):
        stage_gate_decision = manual_payload.get("stage_gate_decision")
    if stage_gate_decision != EXPECTED_STAGE_GATE_DECISION:
        errors.append(
            "manual_review_result stage_gate_decision expected "
            f"{EXPECTED_STAGE_GATE_DECISION!r}, got {stage_gate_decision!r}"
        )
    if not isinstance(expectation_payload, dict) or expectation_payload.get("stage_gate_decision") != EXPECTED_STAGE_GATE_DECISION:
        errors.append(
            "expectations stage_gate_decision expected "
            f"{EXPECTED_STAGE_GATE_DECISION!r}, got "
            f"{expectation_payload.get('stage_gate_decision') if isinstance(expectation_payload, dict) else None!r}"
        )

    manual_raw_items = _raw_items(manual_payload)
    expected_raw_items = _raw_items(expectation_payload)
    manual_items = _items_by_id(manual_payload)
    expected_items = _items_by_id(expectation_payload)
    manual_ids = set(manual_items)
    expected_ids = set(expected_items)
    manual_duplicate_ids = _duplicate_item_ids(manual_raw_items)
    expected_duplicate_ids = _duplicate_item_ids(expected_raw_items)

    if manual_ids != expected_ids:
        errors.append(
            "manual and expectation manifest_item_id sets differ: "
            f"missing_in_manual={sorted(expected_ids - manual_ids)}, "
            f"unexpected_in_manual={sorted(manual_ids - expected_ids)}"
        )
    if len(expected_raw_items) != EXPECTED_ITEM_COUNT:
        errors.append(f"expectation raw item count expected {EXPECTED_ITEM_COUNT}, got {len(expected_raw_items)}")
    if len(manual_raw_items) != EXPECTED_ITEM_COUNT:
        errors.append(f"manual raw item count expected {EXPECTED_ITEM_COUNT}, got {len(manual_raw_items)}")
    if len(expected_ids) != EXPECTED_ITEM_COUNT:
        errors.append(f"expectation unique item count expected {EXPECTED_ITEM_COUNT}, got {len(expected_ids)}")
    if len(manual_ids) != EXPECTED_ITEM_COUNT:
        errors.append(f"manual unique item count expected {EXPECTED_ITEM_COUNT}, got {len(manual_ids)}")
    if expected_duplicate_ids:
        errors.append(f"expectation contains duplicate manifest_item_id values: {expected_duplicate_ids}")
    if manual_duplicate_ids:
        errors.append(f"manual contains duplicate manifest_item_id values: {manual_duplicate_ids}")

    fields_to_check = {
        "required_evidence_pages",
        *REQUIREMENT_LIST_FIELDS,
        *SCALAR_OR_LIST_FIELDS,
    }

    for manifest_item_id in sorted(expected_ids & manual_ids):
        manual_item = manual_items[manifest_item_id]
        expected_item = expected_items[manifest_item_id]

        if manual_item.get("corrected_verdict") != expected_item.get("corrected_verdict"):
            errors.append(
                f"{manifest_item_id}: corrected_verdict expected "
                f"{expected_item.get('corrected_verdict')!r}, got {manual_item.get('corrected_verdict')!r}"
            )

        for field_name in sorted(fields_to_check):
            errors.extend(_compare_expected_field(manifest_item_id, manual_item, expected_item, field_name))

    return {
        "status": "ok" if not errors else "failed",
        "mode": MODE,
        "stage_gate_decision": stage_gate_decision,
        "checked_item_count": len(expected_ids & manual_ids),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Stage E2.1-E field corrections.")
    parser.add_argument(
        "--manual-review-result",
        type=Path,
        default=DEFAULT_MANUAL_REVIEW_RESULT_PATH,
        help="Path to manual_review_result.json.",
    )
    parser.add_argument(
        "--expectations",
        type=Path,
        default=DEFAULT_EXPECTATION_PATH,
        help="Path to e2_1_e_field_correction_expectations.json.",
    )
    args = parser.parse_args(argv)

    try:
        result = validate_e2_1_e_field_corrections(
            manual_review_result_path=args.manual_review_result,
            expectation_path=args.expectations,
        )
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "failed",
            "mode": MODE,
            "stage_gate_decision": None,
            "checked_item_count": 0,
            "errors": [f"{type(exc).__name__}: {exc}"],
            "warnings": [],
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
