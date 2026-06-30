"""Build a review sampling manifest for P0 requirement checklist extraction quality."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.config.paths import P0_GRI_REQUIREMENT_CHECKLIST_PATH  # noqa: E402

DEFAULT_OUTPUT_PATH = (
    REPO_ROOT / "data" / "knowledge_base" / "manifests" / "p0_requirement_checklist_sampling_manifest.json"
)
DEFAULT_REVIEW_TEMPLATE_PATH = REPO_ROOT / "data" / "review" / "e2_1_requirement_sampling_review_template.json"

HIGH_RISK_PARENT_IDS = [
    "current_gap:GRI2:2-1",
    "current_gap:GRI2:2-21",
    "current_gap:GRI302:302-4",
    "current_gap:GRI306:306-4",
    "current_gap:GRI401:401-1",
]

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

CONDITIONAL_KEYWORDS = [" if ", " where ", " when ", " unless ", " in cases where ", " for each "]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _standard_id(item: dict[str, Any]) -> str:
    parent_id = str(item.get("parent_requirement_id", ""))
    parts = parent_id.split(":")
    return parts[1] if len(parts) >= 3 else ""


def _has_quantitative_text(item: dict[str, Any]) -> bool:
    text = f" {item.get('requirement_text', '')} ".lower()
    return any(keyword in text for keyword in QUANTITATIVE_KEYWORDS)


def _has_conditional_text(item: dict[str, Any]) -> bool:
    text = f" {item.get('requirement_text', '')} ".lower()
    return item.get("conditional") is True or any(keyword in text for keyword in CONDITIONAL_KEYWORDS)


def _add_sample(
    samples: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    item: dict[str, Any],
    reason: str,
) -> None:
    requirement_id = str(item["requirement_id"])
    if requirement_id in by_id:
        existing = by_id[requirement_id]
        reasons = existing.setdefault("sampling_reasons", [existing["sampling_reason"]])
        if reason not in reasons:
            reasons.append(reason)
        return

    row = dict(item)
    row["sampling_reason"] = reason
    row["sampling_reasons"] = [reason]
    samples.append(row)
    by_id[requirement_id] = row


def _add_until(
    samples: list[dict[str, Any]],
    by_id: dict[str, dict[str, Any]],
    candidates: list[dict[str, Any]],
    reason: str,
    predicate: Callable[[dict[str, Any]], bool],
    target_count: int,
) -> None:
    for item in candidates:
        matching = [sample for sample in samples if reason in sample.get("sampling_reasons", [])]
        if len(matching) >= target_count:
            break
        if predicate(item):
            _add_sample(samples, by_id, item, reason)


def _current_requirements() -> list[dict[str, Any]]:
    checklist = _load_json(P0_GRI_REQUIREMENT_CHECKLIST_PATH)
    return [
        item
        for item in checklist["requirements"]
        if isinstance(item, dict) and item.get("assessment_mode") == "current_gap"
    ]


def build_sampling_manifest(sample_size: int = 40) -> dict[str, Any]:
    if sample_size < 30 or sample_size > 50:
        raise ValueError("sample_size must be between 30 and 50")

    requirements = _current_requirements()
    by_parent: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in requirements:
        by_parent[str(item["parent_requirement_id"])].append(item)

    parent_counts = Counter(str(item["parent_requirement_id"]) for item in requirements)
    samples: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}

    for parent_id in HIGH_RISK_PARENT_IDS:
        for item in by_parent.get(parent_id, [])[:3]:
            _add_sample(samples, by_id, item, f"high_risk_parent:{parent_id}")

    _add_until(
        samples,
        by_id,
        requirements,
        "compilation_requirement",
        lambda item: item.get("requirement_type") == "compilation_requirement",
        6,
    )
    _add_until(
        samples,
        by_id,
        requirements,
        "quantitative_disclosure_candidate",
        _has_quantitative_text,
        6,
    )
    _add_until(
        samples,
        by_id,
        requirements,
        "conditional_review_candidate",
        _has_conditional_text,
        4,
    )

    standards_seen = {_standard_id(item) for item in samples if _standard_id(item)}
    for item in requirements:
        if len(standards_seen) >= 5:
            break
        standard_id = _standard_id(item)
        if standard_id and standard_id not in standards_seen:
            _add_sample(samples, by_id, item, f"standard_coverage:{standard_id}")
            standards_seen.add(standard_id)

    pages_seen = {
        item.get("official_pdf_page")
        for item in samples
        if isinstance(item.get("official_pdf_page"), int)
    }
    for item in requirements:
        if len(pages_seen) >= 5:
            break
        page = item.get("official_pdf_page")
        if isinstance(page, int) and page not in pages_seen:
            _add_sample(samples, by_id, item, f"page_coverage:{page}")
            pages_seen.add(page)

    multi_parent_seen = {
        item["parent_requirement_id"]
        for item in samples
        if parent_counts[str(item["parent_requirement_id"])] > 1
    }
    for item in requirements:
        if len(multi_parent_seen) >= 5:
            break
        parent_id = str(item["parent_requirement_id"])
        if parent_counts[parent_id] > 1 and parent_id not in multi_parent_seen:
            _add_sample(samples, by_id, item, f"multi_requirement_parent:{parent_id}")
            multi_parent_seen.add(parent_id)

    for item in requirements:
        if len(samples) >= sample_size:
            break
        _add_sample(samples, by_id, item, "deterministic_fill")

    samples = samples[:sample_size]
    return {
        "metadata": {
            "manifest_version": "p0_requirement_checklist_sampling_manifest_v1",
            "source_requirement_checklist": str(P0_GRI_REQUIREMENT_CHECKLIST_PATH.relative_to(REPO_ROOT)),
            "sample_size": len(samples),
            "sampling_method": "deterministic_high_risk_and_stratified_coverage",
            "llm_required": False,
            "high_risk_parent_ids": HIGH_RISK_PARENT_IDS,
            "minimum_strata": {
                "standard_id": 5,
                "official_pdf_page": 5,
                "multi_requirement_parent": 5,
                "quantitative_disclosure_candidate": 5,
                "conditional_review_candidate": 3,
            },
        },
        "sampled_requirements": samples,
    }


def build_review_template(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_version": "p0_requirement_checklist_sampling_review_v1",
        "review_status": "pending",
        "source_sampling_manifest": str(DEFAULT_OUTPUT_PATH.relative_to(REPO_ROOT)),
        "items": [
            {
                "requirement_id": item["requirement_id"],
                "parent_requirement_id": item["parent_requirement_id"],
                "requirement_type": item["requirement_type"],
                "scoring_role": item["scoring_role"],
                "official_pdf_page": item["official_pdf_page"],
                "sampling_reason": item["sampling_reason"],
                "sampling_reasons": item.get("sampling_reasons", [item["sampling_reason"]]),
                "review_status": "pending",
                "page_correct": None,
                "text_boundary_correct": None,
                "type_correct": None,
                "scoring_role_correct": None,
                "review_note": "",
            }
            for item in manifest["sampled_requirements"]
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build P0 requirement checklist sampling manifest.")
    parser.add_argument("--sample-size", type=int, default=40)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--review-template-output", type=Path, default=DEFAULT_REVIEW_TEMPLATE_PATH)
    args = parser.parse_args(argv)

    manifest = build_sampling_manifest(sample_size=args.sample_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    review_template = build_review_template(manifest)
    args.review_template_output.parent.mkdir(parents=True, exist_ok=True)
    args.review_template_output.write_text(
        json.dumps(review_template, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"status": "ok", "sample_size": len(manifest["sampled_requirements"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
