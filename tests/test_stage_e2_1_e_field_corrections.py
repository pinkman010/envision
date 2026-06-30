import json
import importlib
from pathlib import Path


RUN_DIR = Path("data/runs/stage_e/20260629T170447Z_e2_1_regression")
EXPECTATION_PATH = Path("data/review/e2_1_e_field_correction_expectations.json")
ADVISOR_PROMPT_PATH = Path("templates/prompt_templates/advisor_prompt.j2")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _agent_context(**overrides):
    context = {
        "manifest_item_id": "current_gap:GRI2:2-21",
        "analysis_mode": "current_gap",
        "standard_id": "GRI2",
        "standard_year": "2021",
        "canonical_disclosure_id": "2-21",
        "canonical_status": "confirmed_from_report_index",
        "forced_verdict": None,
        "policy_reason": "Current-gap item can be scored if report evidence is sufficient.",
        "can_score_current_gap": True,
        "requirement_checklist_items": [
            {"requirement_id": "current_gap:GRI2:2-21:a", "is_mandatory": True, "scoring_role": "hard_score"}
        ],
        "report_evidence_chunks": [],
        "evidence_bundle": {},
    }
    context.update(overrides)
    return context


def _body_evidence(**overrides):
    evidence = {
        "evidence_id": "evidence_body_1",
        "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
        "source_page": 20,
        "source_text": "The report gives a disclosure limitation.",
        "relevance": 0.8,
        "evidence_kind": "substantive_report_evidence",
        "supports_requirement_ids": ["current_gap:GRI2:2-21:a"],
    }
    evidence.update(overrides)
    return evidence


def _requirement_check(requirement_id, support_status):
    return {
        "requirement_id": requirement_id,
        "requirement_text": "requirement text",
        "is_mandatory": True,
        "conditional": False,
        "condition_text": "",
        "support_status": support_status,
        "supporting_evidence_ids": ["evidence_body_1"],
        "missing_reason": "",
        "manual_review_reason": "",
    }


def _assessment_payload(**overrides):
    payload = {
        "manifest_item_id": "current_gap:GRI2:2-21",
        "standard_id": "GRI2",
        "standard_year": "2021",
        "canonical_disclosure_id": "2-21",
        "canonical_status": "confirmed_from_report_index",
        "assessment_mode": "current_gap",
        "verdict": "not_applicable",
        "confidence": 0.7,
        "evidence": [],
        "requirement_checks": [],
        "missing_requirements": [],
        "rationale": "current_gap:GRI2:2-21 / 2-21 assessment.",
        "review_status": "pending",
    }
    payload.update(overrides)
    return payload


def test_advisor_prompt_forbids_internal_absence_inference():
    prompt = ADVISOR_PROMPT_PATH.read_text(encoding="utf-8")

    for phrase in [
        "报告未披露",
        "无法核实",
        "不得推断企业内部不存在",
        "不要写企业未建立",
    ]:
        assert phrase in prompt


def test_omission_explanation_is_manual_review_not_not_applicable():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    payload = _assessment_payload(
        evidence=[
            _body_evidence(
                evidence_kind="omission_or_not_applicable_explanation",
                source_text="Due to confidentiality constraints, some compensation details are omitted.",
            )
        ],
        requirement_checks=[_requirement_check("current_gap:GRI2:2-21:a", "not_applicable_claimed")],
    )

    guarded = analyst._apply_p0_guardrails(payload, _agent_context())

    assert guarded["verdict"] == "manual_review"
    assert guarded["manual_review_reason_codes"] == ["omission_reason_requires_review"]
    assert guarded["aggregation_reason"] == "omission_reason_requires_review"


def test_partially_met_requirements_are_not_listed_as_missing():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    payload = _assessment_payload(
        manifest_item_id="current_gap:GRI302:302-4",
        standard_id="GRI302",
        canonical_disclosure_id="302-4",
        verdict="partially_disclosed",
        evidence=[_body_evidence(supports_requirement_ids=["current_gap:GRI302:302-4:a"])],
        requirement_checks=[
            _requirement_check("current_gap:GRI302:302-4:a", "partially_met"),
            _requirement_check("current_gap:GRI302:302-4:b", "not_met"),
        ],
        missing_requirements=[
            "current_gap:GRI302:302-4:a",
            "current_gap:GRI302:302-4:b",
        ],
    )
    context = _agent_context(
        manifest_item_id="current_gap:GRI302:302-4",
        standard_id="GRI302",
        canonical_disclosure_id="302-4",
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI302:302-4:a", "is_mandatory": True, "scoring_role": "hard_score"},
            {"requirement_id": "current_gap:GRI302:302-4:b", "is_mandatory": True, "scoring_role": "hard_score"},
        ],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert guarded["partial_requirements"] == ["current_gap:GRI302:302-4:a"]
    assert guarded["missing_requirements"] == ["current_gap:GRI302:302-4:b"]
    assert not set(guarded["partial_requirements"]) & set(guarded["missing_requirements"])


def test_generic_3_3_has_not_scored_topic_instantiation_status():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    payload = _assessment_payload(
        manifest_item_id="current_gap:GRI3:3-3_generic",
        standard_id="GRI3",
        canonical_disclosure_id="3-3_generic",
        verdict="partially_disclosed",
        requirement_checks=[_requirement_check("current_gap:GRI3:3-3_generic:a", "met")],
        missing_requirements=["current_gap:GRI3:3-3_generic:a"],
        partial_requirements=["current_gap:GRI3:3-3_generic:b"],
        not_applicable_requirements=["current_gap:GRI3:3-3_generic:c"],
    )
    context = _agent_context(
        manifest_item_id="current_gap:GRI3:3-3_generic",
        standard_id="GRI3",
        canonical_disclosure_id="3-3_generic",
        requirement_checklist_items=[],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert guarded["verdict"] == "manual_review"
    assert guarded["manual_review_requirements"] == ["needs_topic_instantiation"]
    assert guarded["manual_review_reason_codes"] == ["needs_topic_instantiation"]
    assert guarded["not_scored_reason"] == "not_scored_requires_topic_instantiation"
    assert guarded["missing_requirements"] == []
    assert guarded["partial_requirements"] == []
    assert guarded["not_applicable_requirements"] == []
    assert guarded["requirement_checks"] == []


def test_readiness_policy_overrides_prefilled_readiness_verdict():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    payload = _assessment_payload(
        manifest_item_id="readiness_2026:GRI101",
        standard_id="GRI101",
        canonical_disclosure_id="GRI101",
        assessment_mode="readiness_2026",
        verdict="disclosed",
        readiness_verdict="readiness_aligned",
        evidence=[],
    )
    context = _agent_context(
        manifest_item_id="readiness_2026:GRI101",
        analysis_mode="readiness_2026",
        standard_id="GRI101",
        canonical_disclosure_id="GRI101",
        can_score_current_gap=False,
        forced_verdict="not_applicable",
        policy_reason="GRI101 is a readiness item outside current-gap scoring.",
        readiness_verdict="readiness_gap",
        requirement_checklist_items=[],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert guarded["verdict"] == "not_applicable"
    assert guarded["readiness_verdict"] == "readiness_gap"


def test_e2_1_e_expectations_capture_required_field_corrections():
    payload = _load_json(EXPECTATION_PATH)
    by_id = {item["manifest_item_id"]: item for item in payload["items"]}
    expected_ids = {
        "current_gap:GRI2:2-1",
        "current_gap:GRI2:2-21",
        "current_gap:GRI302:302-4",
        "current_gap:GRI306:306-4",
        "current_gap:GRI401:401-1",
        "current_gap:GRI3:3-3_generic",
        "readiness_2026:GRI101",
    }

    assert payload["source_run_id"] == "20260629T170447Z_e2_1_regression"
    assert payload["stage_gate_decision"] == "conditionally_passed_before_e3"
    assert len(payload["items"]) == 7
    assert set(by_id) == expected_ids

    assert by_id["current_gap:GRI2:2-1"]["required_evidence_pages"] == [
        {"source_page": 1, "report_page_label": "cover"},
        {"source_page": 3, "report_page_label": "2"},
        {"source_page": 28, "report_page_label": "27"},
    ]
    assert set(by_id["current_gap:GRI2:2-1"]["partial_requirements"]) == {
        "current_gap:GRI2:2-1:b",
        "current_gap:GRI2:2-1:c",
    }
    assert by_id["current_gap:GRI2:2-1"]["missing_requirements"] == [
        "current_gap:GRI2:2-1:d"
    ]

    assert by_id["current_gap:GRI2:2-21"]["corrected_verdict"] == "manual_review"
    assert by_id["current_gap:GRI2:2-21"]["manual_review_reason_codes"] == [
        "omission_reason_requires_review"
    ]

    assert by_id["current_gap:GRI302:302-4"]["required_evidence_pages"] == [
        {"source_page": 23, "report_page_label": "22"},
        {"source_page": 63, "report_page_label": "62"},
    ]
    assert by_id["current_gap:GRI302:302-4"]["partial_requirements"] == [
        "current_gap:GRI302:302-4:b"
    ]
    assert set(by_id["current_gap:GRI302:302-4"]["missing_requirements"]) == {
        "current_gap:GRI302:302-4:c",
        "current_gap:GRI302:302-4:d",
        "current_gap:GRI302:302-4:2.7.1",
        "current_gap:GRI302:302-4:2.7.2",
    }

    assert by_id["current_gap:GRI306:306-4"]["required_evidence_pages"] == [
        {"source_page": 21, "report_page_label": "20"},
        {"source_page": 64, "report_page_label": "63"},
    ]
    assert set(by_id["current_gap:GRI306:306-4"]["partial_requirements"]) == {
        "current_gap:GRI306:306-4:b",
        "current_gap:GRI306:306-4:c",
        "current_gap:GRI306:306-4:e",
    }
    assert set(by_id["current_gap:GRI306:306-4"]["missing_requirements"]) == {
        "current_gap:GRI306:306-4:d",
        "current_gap:GRI306:306-4:d:i",
        "current_gap:GRI306:306-4:d:ii",
    }

    assert by_id["current_gap:GRI401:401-1"]["required_evidence_pages"] == [
        {"source_page": 33, "report_page_label": "32"},
        {"source_page": 65, "report_page_label": "64"},
    ]
    assert set(by_id["current_gap:GRI401:401-1"]["partial_requirements"]) == {
        "current_gap:GRI401:401-1:a",
        "current_gap:GRI401:401-1:b",
    }
    assert by_id["current_gap:GRI401:401-1"]["not_scored_requirements"] == [
        "current_gap:GRI401:401-1:2.1"
    ]

    assert (
        by_id["current_gap:GRI3:3-3_generic"]["not_scored_reason"]
        == "not_scored_requires_topic_instantiation"
    )
    assert by_id["readiness_2026:GRI101"]["readiness_verdict"] == "readiness_gap"


def test_manual_review_result_is_readable_and_matches_e2_1_e_gate():
    result = _load_json(RUN_DIR / "manual_review_result.json")
    text = json.dumps(result, ensure_ascii=False)

    assert result["review_status"] == "completed"
    assert result["stage_gate_decision"] == "conditionally_passed_before_e3"
    assert "?" not in text
    assert "PDF" in text
    for phrase in [
        "商业保密",
        "总部大楼",
        "节能措施促成的节电量",
        "废弃物回收总量",
        "员工流失率",
        "not_scored_requires_topic_instantiation",
        "readiness_gap",
    ]:
        assert phrase in text


def test_manual_review_result_uses_source_page_for_field_correction_pages():
    result = _load_json(RUN_DIR / "manual_review_result.json")

    for item in result["items"]:
        for page in item.get("field_corrections", {}).get("evidence_pages_to_add", []):
            assert "source_page" in page
            assert "report_page_label" in page
            assert "pdf_page" not in page


def test_e2_1_e_validator_accepts_manual_review_result_and_expectations():
    validator = importlib.import_module("scripts.validate_stage_e2_1_e_field_corrections")

    result = validator.validate_e2_1_e_field_corrections(
        manual_review_result_path=RUN_DIR / "manual_review_result.json",
        expectation_path=EXPECTATION_PATH,
    )

    assert result["status"] == "ok"
    assert result["stage_gate_decision"] == "conditionally_passed_before_e3"
    assert result["checked_item_count"] == 7
