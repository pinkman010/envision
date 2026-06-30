import json

from src.agent.analyst_agent import AnalystAgent
from src.config.paths import P0_GRI_REQUIREMENT_CHECKLIST_PATH


def _requirement_by_id():
    payload = json.loads(P0_GRI_REQUIREMENT_CHECKLIST_PATH.read_text(encoding="utf-8"))
    return {item["requirement_id"]: item for item in payload["requirements"]}


def test_aggregation_parent_rows_do_not_replace_hard_score_children():
    by_id = _requirement_by_id()

    assert by_id["current_gap:GRI302:302-4:2.7"]["scoring_role"] == "aggregation_parent"
    assert by_id["current_gap:GRI306:306-4:2.2"]["scoring_role"] == "aggregation_parent"
    assert by_id["current_gap:GRI302:302-4:2.7.1"]["scoring_role"] == "hard_score"
    assert by_id["current_gap:GRI306:306-4:2.2.1"]["scoring_role"] == "hard_score"


def test_scope_review_rows_are_excluded_from_mandatory_coverage():
    by_id = _requirement_by_id()
    scope_review = by_id["current_gap:GRI401:401-1:2.1"]

    assert scope_review["scoring_role"] == "scope_review"
    assert scope_review["extraction_review_status"] == "needs_scope_review"

    context = {
        "requirement_checklist_items": [
            by_id["current_gap:GRI302:302-4:2.7"],
            by_id["current_gap:GRI302:302-4:2.7.1"],
            scope_review,
        ]
    }

    assert AnalystAgent._mandatory_requirement_ids(context) == ["current_gap:GRI302:302-4:2.7.1"]
