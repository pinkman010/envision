import importlib
import json
from collections import Counter


REQUIRED_ITEM_FIELDS = {
    "requirement_id",
    "parent_requirement_id",
    "canonical_disclosure_id",
    "requirement_text",
    "requirement_type",
    "conditional",
    "condition_text",
    "official_pdf_page",
    "is_mandatory",
    "scoring_role",
    "standard_year",
    "published_at",
    "effective_date",
    "analysis_applicability_date",
    "replaced_standard",
    "assessment_mode",
    "standard_profile_id",
    "extraction_review_status",
}


def _load_pack(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_requirement_checklist_manifest_parses_with_required_model_fields():
    paths = importlib.import_module("src.config.paths")
    models = importlib.import_module("src.models.evidence_layer")

    payload = _load_pack(paths.P0_GRI_REQUIREMENT_CHECKLIST_PATH)
    checklist = models.P0RequirementChecklist.model_validate(payload)

    assert checklist.metadata.standard_profile_id == "gri_p0_2024_current_disclosure_v1"
    assert checklist.requirements
    first_item = checklist.requirements[0].model_dump(mode="json")
    assert REQUIRED_ITEM_FIELDS.issubset(first_item)
    assert first_item["extraction_review_status"] == "pending_review"
    assert not first_item["requirement_id"].endswith(":seed")

    by_id = {
        item.requirement_id: item.model_dump(mode="json")
        for item in checklist.requirements
    }
    assert by_id["current_gap:GRI302:302-4:2.7"]["scoring_role"] == "aggregation_parent"
    assert by_id["current_gap:GRI302:302-4:2.7"]["extraction_review_status"] == "reviewed_parent_not_scored"
    assert by_id["current_gap:GRI306:306-4:2.2"]["scoring_role"] == "aggregation_parent"
    assert by_id["current_gap:GRI306:306-4:2.2"]["extraction_review_status"] == "reviewed_parent_not_scored"
    assert by_id["current_gap:GRI401:401-1:2.1"]["scoring_role"] == "scope_review"
    assert by_id["current_gap:GRI401:401-1:2.1"]["extraction_review_status"] == "needs_scope_review"


def test_requirement_checklist_validator_returns_ok_and_counts_contract():
    validator = importlib.import_module("scripts.validate_p0_requirement_checklist")

    result = validator.validate_p0_requirement_checklist()

    assert result["status"] == "ok"
    assert result["current_gap_scored_requirement_count"] > 114
    assert result["topic_instantiation_required_count"] == 1
    assert result["excluded_counts_by_mode"] == {
        "readiness_2026": 1,
        "watchlist_2027": 2,
    }
    assert "missing_effective_date_count" in result
    assert result["seed_requirement_count"] == 0


def test_current_gap_leaf_items_cover_non_3_3_disclosures_and_exclude_generic_3_3():
    paths = importlib.import_module("src.config.paths")
    payload = _load_pack(paths.P0_GRI_REQUIREMENT_CHECKLIST_PATH)
    pack = _load_pack(paths.P0_GRI_REQUIREMENT_PACK_PATH)

    current_gap_parent_ids = {
        item["manifest_item_id"]
        for item in pack["requirements"]
        if item["analysis_mode"] == "current_gap"
        and item["canonical_disclosure_id"] != "3-3_generic"
    }
    checklist_parent_ids = {
        item["parent_requirement_id"]
        for item in payload["requirements"]
        if item["assessment_mode"] == "current_gap"
    }
    topic_parent_ids = {
        item["parent_requirement_id"]
        for item in payload["topic_instantiation_required"]
    }

    assert current_gap_parent_ids <= checklist_parent_ids
    assert "current_gap:GRI3:3-3_generic" not in checklist_parent_ids
    assert topic_parent_ids == {"current_gap:GRI3:3-3_generic"}
    assert not any(item["requirement_id"].endswith(":seed") for item in payload["requirements"])


def test_future_modes_do_not_enter_current_hard_score_requirements():
    paths = importlib.import_module("src.config.paths")
    payload = _load_pack(paths.P0_GRI_REQUIREMENT_CHECKLIST_PATH)

    hard_score_modes = Counter(
        item["assessment_mode"]
        for item in payload["requirements"]
        if item["scoring_role"] == "hard_score"
    )

    assert set(hard_score_modes) == {"current_gap"}
    assert hard_score_modes["current_gap"] > 114


def test_requirement_checklist_contains_extracted_leaf_examples():
    paths = importlib.import_module("src.config.paths")
    payload = _load_pack(paths.P0_GRI_REQUIREMENT_CHECKLIST_PATH)
    by_id = {item["requirement_id"]: item for item in payload["requirements"]}

    assert by_id["current_gap:GRI2:2-1:a"]["requirement_text"] == "report its legal name;"
    assert by_id["current_gap:GRI2:2-1:d"]["requirement_text"] == "report its countries of operation."
    assert by_id["current_gap:GRI302:302-4:2.7.1"]["requirement_type"] == "compilation_requirement"
    assert "exclude reductions resulting from reduced production capacity" in by_id[
        "current_gap:GRI302:302-4:2.7.1"
    ]["requirement_text"]

def test_requirement_checklist_validator_uses_pydantic_model_for_schema_errors(tmp_path):
    paths = importlib.import_module("src.config.paths")
    validator = importlib.import_module("scripts.validate_p0_requirement_checklist")
    payload = _load_pack(paths.P0_GRI_REQUIREMENT_CHECKLIST_PATH)
    payload["requirements"][0]["unexpected_extra_field"] = "must fail pydantic extra=forbid"
    invalid_path = tmp_path / "invalid_checklist.json"
    invalid_path.write_text(json.dumps(payload), encoding="utf-8")

    result = validator.validate_p0_requirement_checklist(checklist_path=invalid_path)

    assert result["status"] == "failed"
    assert any("Checklist schema validation failed" in str(error) for error in result["errors"])