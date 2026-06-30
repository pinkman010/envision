"""Validate the P0 E2.1-A requirement checklist manifest.

This script performs local JSON/model checks only. It does not call LLMs,
rebuild vector stores, or write databases.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Any, Dict, List, Sequence

from pydantic import ValidationError

from src.config.paths import (
    P0_GRI_REQUIREMENT_CHECKLIST_PATH,
    P0_GRI_REQUIREMENT_PACK_PATH,
)
from src.models import (
    AnalysisMode,
    GRIRequirementPack,
    P0RequirementChecklist,
    RequirementChecklistType,
)

CURRENT_PROFILE_ID = "gri_p0_2024_current_disclosure_v1"
GENERIC_3_3_PARENT_ID = "current_gap:GRI3:3-3_generic"
SEED_REQUIREMENT_SUFFIX = ":seed"
ALLOWED_SCORING_ROLES = {"hard_score", "aggregation_parent", "scope_review"}


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _duplicates(values: Sequence[str]) -> List[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def validate_p0_requirement_checklist(
    checklist_path: Path = P0_GRI_REQUIREMENT_CHECKLIST_PATH,
    requirement_pack_path: Path = P0_GRI_REQUIREMENT_PACK_PATH,
) -> Dict[str, Any]:
    """Validate the frozen E2.1-A requirement checklist contract."""
    errors: List[str] = []

    try:
        raw_checklist = _load_json(checklist_path)
    except Exception as exc:  # pragma: no cover - exercised from CLI on broken files
        return {
            "status": "failed",
            "errors": [f"Could not parse checklist JSON: {exc}"],
        }

    try:
        raw_pack = _load_json(requirement_pack_path)
        requirement_pack = GRIRequirementPack.model_validate(raw_pack)
    except Exception as exc:  # pragma: no cover - exercised from CLI on broken files
        return {
            "status": "failed",
            "errors": [f"Could not parse requirement pack JSON: {exc}"],
        }

    try:
        checklist = P0RequirementChecklist.model_validate(raw_checklist)
    except ValidationError as exc:
        return {
            "status": "failed",
            "errors": ["Checklist schema validation failed", json.loads(exc.json())],
        }

    requirement_ids = [item.requirement_id for item in checklist.requirements]
    duplicate_requirement_ids = _duplicates(requirement_ids)
    if duplicate_requirement_ids:
        errors.append(f"Duplicate requirement_id values: {duplicate_requirement_ids}")
    seed_requirement_ids = sorted(
        item.requirement_id
        for item in checklist.requirements
        if item.requirement_id.endswith(SEED_REQUIREMENT_SUFFIX)
    )
    if seed_requirement_ids:
        errors.append(
            "Seed placeholder requirements are not allowed in the frozen checklist: "
            f"{seed_requirement_ids[:20]}"
        )

    pack_parent_ids = {item.manifest_item_id for item in requirement_pack.requirements}
    missing_parent_ids = sorted(
        item.parent_requirement_id
        for item in checklist.requirements
        if item.parent_requirement_id not in pack_parent_ids
    )
    missing_topic_parent_ids = sorted(
        item.parent_requirement_id
        for item in checklist.topic_instantiation_required
        if item.parent_requirement_id not in pack_parent_ids
    )
    if missing_parent_ids:
        errors.append(f"Checklist parent_requirement_id not found in requirement pack: {missing_parent_ids}")
    if missing_topic_parent_ids:
        errors.append(f"Topic-instantiation parent_requirement_id not found in requirement pack: {missing_topic_parent_ids}")

    current_gap_disclosures = [
        item
        for item in requirement_pack.requirements
        if item.analysis_mode == AnalysisMode.CURRENT_GAP
    ]
    current_gap_parent_ids = {
        item.manifest_item_id
        for item in current_gap_disclosures
        if item.canonical_disclosure_id != "3-3_generic"
    }
    checklist_current_parent_ids = {
        item.parent_requirement_id
        for item in checklist.requirements
        if item.assessment_mode == AnalysisMode.CURRENT_GAP.value
    }
    missing_current_gap_items = sorted(current_gap_parent_ids - checklist_current_parent_ids)
    if missing_current_gap_items:
        errors.append(f"current_gap disclosures missing checklist item: {missing_current_gap_items}")
    generic_3_3_in_requirements = [
        item.requirement_id
        for item in checklist.requirements
        if item.parent_requirement_id == GENERIC_3_3_PARENT_ID
        or item.canonical_disclosure_id == "3-3_generic"
    ]
    topic_parent_ids = {item.parent_requirement_id for item in checklist.topic_instantiation_required}
    if generic_3_3_in_requirements:
        errors.append(f"3-3_generic must not be scored as a checklist requirement: {generic_3_3_in_requirements}")
    if GENERIC_3_3_PARENT_ID not in topic_parent_ids:
        errors.append("3-3_generic must be present in topic_instantiation_required")

    hard_score_types = {
        RequirementChecklistType.REQUIREMENT.value,
        RequirementChecklistType.COMPILATION_REQUIREMENT.value,
    }
    illegal_scoring_combinations = []
    non_current_hard_score_items = []
    for item in checklist.requirements:
        if item.scoring_role == "hard_score":
            if item.requirement_type not in hard_score_types or not item.is_mandatory:
                illegal_scoring_combinations.append(item.requirement_id)
            if item.assessment_mode != AnalysisMode.CURRENT_GAP.value:
                non_current_hard_score_items.append(item.requirement_id)
        if (
            item.scoring_role not in ALLOWED_SCORING_ROLES
            or (item.scoring_role != "hard_score" and item.is_mandatory)
        ):
            illegal_scoring_combinations.append(item.requirement_id)
    if illegal_scoring_combinations:
        errors.append(f"Illegal scoring_role/type combinations: {sorted(illegal_scoring_combinations)}")
    if non_current_hard_score_items:
        errors.append(f"Non-current items entered hard_score checklist: {sorted(non_current_hard_score_items)}")

    if checklist.metadata.standard_profile_id != CURRENT_PROFILE_ID:
        errors.append(
            f"metadata.standard_profile_id expected {CURRENT_PROFILE_ID}, got {checklist.metadata.standard_profile_id}"
        )
    wrong_profile_items = sorted(
        item.requirement_id
        for item in checklist.requirements
        if item.standard_profile_id != checklist.metadata.standard_profile_id
    )
    if wrong_profile_items:
        errors.append(f"Checklist items with unexpected standard_profile_id: {wrong_profile_items}")

    raw_requirement_items = raw_checklist.get("requirements", [])
    missing_effective_date_field_items = sorted(
        str(item.get("requirement_id", "<unknown>"))
        for item in raw_requirement_items
        if "effective_date" not in item
    )
    if missing_effective_date_field_items:
        errors.append(f"Checklist items missing effective_date field: {missing_effective_date_field_items}")
    missing_effective_date_count = sum(
        1
        for item in raw_requirement_items
        if item.get("effective_date") in (None, "")
    )

    pack_excluded_counts = Counter(
        item.analysis_mode.value
        for item in requirement_pack.requirements
        if item.analysis_mode != AnalysisMode.CURRENT_GAP
    )
    excluded_counts_by_mode = dict(sorted(checklist.metadata.excluded_counts_by_mode.items()))
    expected_excluded_counts = dict(sorted(pack_excluded_counts.items()))
    if excluded_counts_by_mode != expected_excluded_counts:
        errors.append(
            f"metadata.excluded_counts_by_mode expected {expected_excluded_counts}, got {excluded_counts_by_mode}"
        )

    current_gap_scored_requirement_count = sum(
        1
        for item in checklist.requirements
        if item.assessment_mode == AnalysisMode.CURRENT_GAP.value
        and item.scoring_role == "hard_score"
    )

    return {
        "status": "ok" if not errors else "failed",
        "manifest_version": checklist.metadata.manifest_version,
        "standard_profile_id": checklist.metadata.standard_profile_id,
        "requirement_count": len(checklist.requirements),
        "current_gap_scored_requirement_count": current_gap_scored_requirement_count,
        "topic_instantiation_required_count": len(checklist.topic_instantiation_required),
        "excluded_counts_by_mode": excluded_counts_by_mode,
        "missing_effective_date_count": missing_effective_date_count,
        "requirement_ids_unique": not duplicate_requirement_ids,
        "covered_current_gap_disclosure_count": len(checklist_current_parent_ids),
        "expected_current_gap_disclosure_count": len(current_gap_parent_ids),
        "seed_requirement_count": len(seed_requirement_ids),
        "has_3_3_topic_instantiation": GENERIC_3_3_PARENT_ID in topic_parent_ids,
        "errors": errors,
    }


def main() -> int:
    result = validate_p0_requirement_checklist()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
