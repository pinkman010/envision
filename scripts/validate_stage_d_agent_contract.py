"""Validate Stage D P0 Agent contract without calling an external LLM."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED_MANUAL_PAGES = {
    "current_gap:GRI2:2-21": [68],
    "current_gap:GRI207:207-4": [663],
    "current_gap:GRI306:306-4": [779],
    "current_gap:GRI401:401-1": [807],
    "current_gap:GRI403:403-2": [833],
}


def _failed_result(error: str) -> dict[str, Any]:
    return {
        "status": "failed",
        "context_count": 0,
        "manual_locator_context_count": 0,
        "errors": [error],
    }


def _load_context_builder() -> Callable[[], list[dict[str, Any]]]:
    from src.utils.p0_agent_context import build_p0_requirement_contexts

    return build_p0_requirement_contexts


def _validate_contexts(contexts: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_id = {item["manifest_item_id"]: item for item in contexts}

    if len(contexts) != 118:
        errors.append(f"expected 118 p0 requirement contexts, got {len(contexts)}")

    for manifest_item_id, expected_pages in EXPECTED_MANUAL_PAGES.items():
        item = by_id.get(manifest_item_id)
        if item is None:
            errors.append(f"missing context: {manifest_item_id}")
            continue
        if item["official_pdf_pages_for_agent"] != expected_pages:
            errors.append(
                f"{manifest_item_id} official pages expected {expected_pages}, "
                f"got {item['official_pdf_pages_for_agent']}"
            )
        if not item["agent_manual_review_required"]:
            errors.append(f"{manifest_item_id} should retain agent_manual_review_required=true")

    for item in contexts:
        status = item["requirement_locator_status"]
        if status == "found" and not item["official_pdf_pages_for_agent"]:
            errors.append(f"found item has no official pages: {item['manifest_item_id']}")
        if status == "multiple_candidates" and item["manifest_item_id"] not in EXPECTED_MANUAL_PAGES:
            if item["official_pdf_pages_for_agent"]:
                errors.append(f"unconfirmed multiple candidate item exposed pages: {item['manifest_item_id']}")
        if item["forced_verdict"] and item["can_score_current_gap"]:
            errors.append(f"forced verdict item should not be current-gap scorable: {item['manifest_item_id']}")

    return errors


def main() -> int:
    try:
        build_p0_requirement_contexts = _load_context_builder()
        contexts = build_p0_requirement_contexts()
        errors = _validate_contexts(contexts)
        result = {
            "status": "ok" if not errors else "failed",
            "context_count": len(contexts),
            "manual_locator_context_count": sum(
                1 for item in contexts if item["manifest_item_id"] in EXPECTED_MANUAL_PAGES
            ),
            "errors": errors,
        }
    except Exception as exc:
        result = _failed_result(f"{type(exc).__name__}: {exc}")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
