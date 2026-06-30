"""Validate P0 requirement checklist sampling manifest."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.paths import P0_GRI_REQUIREMENT_CHECKLIST_PATH  # noqa: E402

DEFAULT_SAMPLING_MANIFEST_PATH = (
    REPO_ROOT / "data" / "knowledge_base" / "manifests" / "p0_requirement_checklist_sampling_manifest.json"
)
HIGH_RISK_PARENT_IDS = {
    "current_gap:GRI2:2-1",
    "current_gap:GRI2:2-21",
    "current_gap:GRI302:302-4",
    "current_gap:GRI306:306-4",
    "current_gap:GRI401:401-1",
}
QUANTITATIVE_KEYWORDS = [
    "amount",
    "total",
    "number",
    "rate",
    "ratio",
    "percentage",
    "weight",
    "energy",
    "consumption",
    "emissions",
    "employees",
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _standard_id(item: dict[str, Any]) -> str:
    parent_id = str(item.get("parent_requirement_id", ""))
    parts = parent_id.split(":")
    return parts[1] if len(parts) >= 3 else ""


def _sampling_reasons(item: dict[str, Any]) -> set[str]:
    reasons = item.get("sampling_reasons")
    if isinstance(reasons, list):
        return {str(reason) for reason in reasons}
    return {str(item.get("sampling_reason"))}


def _has_quantitative_text(item: dict[str, Any]) -> bool:
    text = str(item.get("requirement_text", "")).lower()
    return any(keyword in text for keyword in QUANTITATIVE_KEYWORDS)


def _has_conditional_marker(item: dict[str, Any]) -> bool:
    return item.get("conditional") is True or "conditional_review_candidate" in _sampling_reasons(item)


def validate_sampling_manifest(path: Path = DEFAULT_SAMPLING_MANIFEST_PATH) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest = _load_json(path)
    checklist = _load_json(P0_GRI_REQUIREMENT_CHECKLIST_PATH)
    checklist_items = [
        item
        for item in checklist.get("requirements", [])
        if isinstance(item, dict) and item.get("assessment_mode") == "current_gap"
    ]
    valid_by_id = {str(item.get("requirement_id")): item for item in checklist_items}
    parent_counts = Counter(str(item.get("parent_requirement_id")) for item in checklist_items)

    samples = manifest.get("sampled_requirements", [])
    if not isinstance(samples, list):
        return {"status": "failed", "errors": ["sampled_requirements must be list"], "warnings": warnings}
    if len(samples) < 30 or len(samples) > 50:
        errors.append("sampled_requirements count must be between 30 and 50")

    sample_ids = [str(item.get("requirement_id")) for item in samples if isinstance(item, dict)]
    if len(sample_ids) != len(set(sample_ids)):
        errors.append("sampled requirement_id values must be unique")
    missing_ids = sorted(set(sample_ids) - set(valid_by_id))
    if missing_ids:
        errors.append(f"sampled requirement IDs missing from checklist: {missing_ids[:10]}")

    parent_ids = {str(item.get("parent_requirement_id")) for item in samples if isinstance(item, dict)}
    missing_parents = sorted(HIGH_RISK_PARENT_IDS - parent_ids)
    if missing_parents:
        errors.append(f"missing high-risk parent coverage: {missing_parents}")

    requirement_types = {str(item.get("requirement_type")) for item in samples if isinstance(item, dict)}
    if "requirement" not in requirement_types:
        errors.append("sampling must include requirement type")
    if "compilation_requirement" not in requirement_types:
        errors.append("sampling must include compilation_requirement type")

    scoring_roles = {str(item.get("scoring_role")) for item in samples if isinstance(item, dict)}
    if "hard_score" not in scoring_roles:
        errors.append("sampling must include hard_score scoring role")

    standard_ids = {_standard_id(item) for item in samples if isinstance(item, dict) and _standard_id(item)}
    if len(standard_ids) < 5:
        errors.append("sampling must cover at least 5 standard_id values")

    official_pages = {
        item.get("official_pdf_page")
        for item in samples
        if isinstance(item, dict) and isinstance(item.get("official_pdf_page"), int)
    }
    if len(official_pages) < 5:
        errors.append("sampling must cover at least 5 official_pdf_page values")

    multi_requirement_parents = {
        str(item.get("parent_requirement_id"))
        for item in samples
        if isinstance(item, dict) and parent_counts[str(item.get("parent_requirement_id"))] > 1
    }
    if len(multi_requirement_parents) < 5:
        errors.append("sampling must cover at least 5 multi-requirement parent disclosures")

    quantitative_samples = [item for item in samples if isinstance(item, dict) and _has_quantitative_text(item)]
    if len(quantitative_samples) < 5:
        errors.append("sampling must include at least 5 quantitative disclosure candidates")

    conditional_samples = [item for item in samples if isinstance(item, dict) and _has_conditional_marker(item)]
    if len(conditional_samples) < 3:
        errors.append("sampling must include at least 3 conditional review candidates")

    all_reasons = set()
    for item in samples:
        if isinstance(item, dict):
            all_reasons.update(_sampling_reasons(item))
    if not any(reason.startswith("high_risk_parent:") for reason in all_reasons):
        errors.append("sampling must include high_risk_parent reasons")
    if "quantitative_disclosure_candidate" not in all_reasons:
        warnings.append("sampling has no quantitative_disclosure_candidate reason")
    if "conditional_review_candidate" not in all_reasons:
        warnings.append("sampling has no conditional_review_candidate reason")

    return {
        "status": "ok" if not errors else "failed",
        "sample_count": len(samples),
        "errors": errors,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate P0 requirement checklist sampling manifest.")
    parser.add_argument("--sampling-manifest", type=Path, default=DEFAULT_SAMPLING_MANIFEST_PATH)
    args = parser.parse_args(argv)
    result = validate_sampling_manifest(args.sampling_manifest)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
