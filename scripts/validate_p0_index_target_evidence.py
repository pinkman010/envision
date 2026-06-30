"""Validate E2.1-D index target and full-text evidence candidates.

This validator is local-only. It reads the frozen P0 context and deterministic
evidence builders, and does not call LLMs or write run artifacts.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.p0_index_target_evidence import (  # noqa: E402
    build_fulltext_requirement_evidence,
    build_index_target_evidence,
)
from src.utils.p0_agent_context import build_p0_requirement_contexts  # noqa: E402

REQUIRED_INDEX_TARGET_PAGES: dict[str, set[int]] = {
    "current_gap:GRI302:302-4": {22, 62},
    "current_gap:GRI306:306-4": {20, 63},
}
REQUIRED_FULLTEXT_PAGES: dict[str, set[int]] = {
    "current_gap:GRI2:2-1": {2, 27},
    "current_gap:GRI302:302-4": {22, 62},
    "current_gap:GRI306:306-4": {20, 63},
    "current_gap:GRI401:401-1": {32, 64},
}


def _pages(items: list[dict[str, Any]]) -> set[int]:
    return {
        int(item["report_page_label"])
        for item in items
        if str(item.get("report_page_label", "")).isdigit()
    }


def _validate_page_pair(
    errors: list[str],
    manifest_item_id: str,
    evidence_key: str,
    items: list[dict[str, Any]],
) -> None:
    for index, item in enumerate(items):
        source_page = item.get("source_page")
        report_page_label = item.get("report_page_label")
        if source_page is None or report_page_label in {None, ""}:
            errors.append(
                f"{manifest_item_id}: {evidence_key}[{index}] must include source_page and report_page_label"
            )
            continue
        label = str(report_page_label)
        if label.isdigit() and int(source_page) != int(label) + 1:
            errors.append(
                f"{manifest_item_id}: {evidence_key}[{index}] source_page {source_page} "
                f"must equal numeric report_page_label {label} + 1"
            )


def validate_p0_index_target_evidence() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    target_ids = sorted(set(REQUIRED_INDEX_TARGET_PAGES) | set(REQUIRED_FULLTEXT_PAGES))
    index_evidence = build_index_target_evidence(target_ids)
    fulltext_evidence = build_fulltext_requirement_evidence(target_ids)

    for manifest_item_id, expected_pages in REQUIRED_INDEX_TARGET_PAGES.items():
        items = index_evidence.get(manifest_item_id, [])
        _validate_page_pair(errors, manifest_item_id, "index_target_evidence", items)
        actual_pages = _pages(items)
        missing = sorted(expected_pages - actual_pages)
        if missing:
            errors.append(f"{manifest_item_id}: missing index referenced body pages {missing}")
        if any(item.get("supports_requirement_ids") for item in items):
            errors.append(f"{manifest_item_id}: index target evidence must not pre-fill supports_requirement_ids")

    for manifest_item_id, expected_pages in REQUIRED_FULLTEXT_PAGES.items():
        items = fulltext_evidence.get(manifest_item_id, [])
        _validate_page_pair(errors, manifest_item_id, "fulltext_requirement_evidence", items)
        actual_pages = _pages(items)
        missing = sorted(expected_pages - actual_pages)
        if missing:
            errors.append(f"{manifest_item_id}: missing fulltext candidate pages {missing}")
        bad_subtypes = sorted(
            {
                str(item.get("evidence_subtype"))
                for item in items
                if item.get("evidence_subtype") != "fulltext_requirement_candidate"
            }
        )
        if bad_subtypes:
            errors.append(f"{manifest_item_id}: unexpected fulltext evidence_subtype values {bad_subtypes}")

    contexts = build_p0_requirement_contexts()
    contexts_by_id = {context["manifest_item_id"]: context for context in contexts}
    for manifest_item_id in target_ids:
        context = contexts_by_id.get(manifest_item_id)
        if context is None:
            errors.append(f"{manifest_item_id}: missing from P0 requirement contexts")
            continue
        bundle = context.get("evidence_bundle", {})
        for key in ("index_evidence", "referenced_page_evidence", "nearby_page_evidence", "fulltext_requirement_evidence"):
            if key not in bundle:
                errors.append(f"{manifest_item_id}: evidence_bundle missing {key}")
        for key in ("referenced_page_evidence", "nearby_page_evidence", "fulltext_requirement_evidence"):
            _validate_page_pair(errors, manifest_item_id, key, bundle.get(key, []))
        for item in bundle.get("index_evidence", []):
            if item.get("supports_requirement_ids"):
                errors.append(f"{manifest_item_id}: index_evidence must have empty supports_requirement_ids")
            if item.get("evidence_subtype") != "gri_content_index_locator":
                errors.append(f"{manifest_item_id}: index_evidence must use gri_content_index_locator subtype")
            if "locator only" not in str(item.get("judgment_reason", "")):
                errors.append(f"{manifest_item_id}: index_evidence judgment_reason must state locator only")

    return {
        "status": "ok" if not errors else "failed",
        "mode": "p0_index_target_evidence",
        "checked_manifest_item_ids": target_ids,
        "context_count": len(contexts),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    result = validate_p0_index_target_evidence()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

