import importlib
import json
from pathlib import Path

import pytest


def _base_assessment(**overrides):
    assessment = {
        "manifest_item_id": "current_gap:GRI2:2-1",
        "standard_id": "GRI2",
        "canonical_disclosure_id": "2-1",
        "assessment_mode": "current_gap",
        "verdict": "partially_disclosed",
        "confidence": 0.65,
        "evidence": [
            {
                "evidence_id": "evidence_body_1",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_page": 10,
                "source_text": "Envision Energy is headquartered in Shanghai.",
                "relevance": 0.8,
                "evidence_kind": "substantive_report_evidence",
                "supports_requirement_ids": ["current_gap:GRI2:2-1:c"],
            }
        ],
        "requirement_checks": [
            {
                "requirement_id": "current_gap:GRI2:2-1:a",
                "requirement_text": "report its legal name;",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_met",
                "supporting_evidence_ids": [],
                "missing_reason": "Legal name is not found outside the index.",
                "manual_review_reason": "",
            }
        ],
        "missing_requirements": ["current_gap:GRI2:2-1:a"],
        "rationale": "Requirement-level checks drive the verdict.",
    }
    assessment.update(overrides)
    return assessment


def _validate_assessments(assessments):
    validator = importlib.import_module("scripts.validate_stage_e2_1_evidence_contract")
    return validator.validate_assessments(assessments)


def _met_requirement_check(requirement_id="current_gap:GRI2:2-1:a"):
    return {
        "requirement_id": requirement_id,
        "requirement_text": "requirement text",
        "is_mandatory": True,
        "conditional": False,
        "condition_text": "",
        "support_status": "met",
        "supporting_evidence_ids": ["evidence_body_1"],
        "missing_reason": "",
        "manual_review_reason": "",
    }


def _agent_context(**overrides):
    context = {
        "manifest_item_id": "current_gap:GRI2:2-1",
        "analysis_mode": "current_gap",
        "standard_year": "2021",
        "canonical_disclosure_id": "2-1",
        "canonical_status": "confirmed_from_report_index",
        "forced_verdict": None,
        "policy_reason": "Current-gap item can be scored if report evidence is sufficient.",
        "requirement_checklist_items": [{"requirement_id": "current_gap:GRI2:2-1:a", "is_mandatory": True, "scoring_role": "hard_score"}],
        "report_evidence_chunks": [
            {
                "chunk_id": "idx1",
                "source_document_relative_path": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_document_sha256": "A" * 64,
                "pdf_page": 72,
                "text": "GRI 2-1 page reference",
                "company": "Envision Energy",
                "report_year": 2024,
                "industry": "energy",
                "topic": "index",
                "evidence_kind": "index_evidence",
            }
        ],
        "evidence_bundle": {},
    }
    context.update(overrides)
    return context


def test_contract_models_expose_e2_1_enums_and_requirement_check():
    contract = importlib.import_module("src.models.analysis_contract")

    assert contract.EvidenceKind.INDEX_EVIDENCE.value == "index_evidence"
    assert contract.EvidenceKind.SUBSTANTIVE_REPORT_EVIDENCE.value == "substantive_report_evidence"
    assert contract.EvidenceKind.OMISSION_OR_NOT_APPLICABLE_EXPLANATION.value == (
        "omission_or_not_applicable_explanation"
    )
    assert contract.RequirementSupportStatus.MET.value == "met"
    assert contract.RequirementSupportStatus.MANUAL_REVIEW.value == "manual_review"

    check = contract.RequirementCheck(
        requirement_id="current_gap:GRI2:2-1:a",
        requirement_text="report its legal name;",
        is_mandatory=True,
        conditional=False,
        condition_text="",
        support_status=contract.RequirementSupportStatus.MET,
        supporting_evidence_ids=["evidence_body_1"],
    )
    assert check.missing_reason == ""
    assert check.manual_review_reason == ""


def test_manual_review_reason_is_classified_for_omission_and_topic_instantiation():
    contract = importlib.import_module("src.models.analysis_contract")

    assert contract.ManualReviewReason.OMISSION_REASON_REQUIRES_REVIEW.value == "omission_reason_requires_review"
    assert contract.ManualReviewReason.NEEDS_TOPIC_INSTANTIATION.value == "needs_topic_instantiation"
    assert contract.ManualReviewReason.WEAK_EVIDENCE_SUPPORT.value == "weak_evidence_support"
    assert contract.ManualReviewReason.MISSING_LLM_ASSESSMENT_FOR_MANIFEST_ITEM.value == (
        "missing_llm_assessment_for_manifest_item"
    )
    assert contract.ManualReviewReason.INDEX_EVIDENCE_CANNOT_SUPPORT_DISCLOSED.value == (
        "index_evidence_cannot_support_disclosed"
    )


def test_readiness_item_can_carry_readiness_verdict_separately():
    contract = importlib.import_module("src.models.analysis_contract")
    assessment = contract.DisclosureAssessment(
        manifest_item_id="readiness_2026:GRI101",
        standard_id="GRI101",
        canonical_disclosure_id=None,
        assessment_mode="readiness_2026",
        verdict=contract.AssessmentVerdict.NOT_APPLICABLE,
        confidence=0.0,
        readiness_verdict="readiness_gap",
        evidence=[],
        requirement_checks=[],
        rationale="Not part of 2024 current gap; readiness gap remains.",
        review_status="pending",
    )

    assert assessment.verdict.value == "not_applicable"
    assert assessment.readiness_verdict == "readiness_gap"
    assert assessment.manual_review_reason_codes == []


def test_evidence_can_carry_retrieval_method_and_extraction_warning():
    contract = importlib.import_module("src.models.analysis_contract")
    evidence = contract.Evidence(
        source_document="data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
        source_page=73,
        source_text="302-4 降低能源消耗量 智慧用能，资源善用 22",
        relevance=0.9,
        evidence_kind="index_evidence",
        retrieval_method="index_target_page",
        source_text_extraction_warning="table cell boundary may be incomplete",
    )

    assert evidence.retrieval_method == "index_target_page"
    assert evidence.source_text_extraction_warning == "table cell boundary may be incomplete"
def test_index_evidence_alone_cannot_support_disclosed():
    assessment = _base_assessment(
        verdict="disclosed",
        evidence=[
            {
                "evidence_id": "evidence_index_1",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_page": 136,
                "source_text": "GRI 2-1 Organization details: page 8.",
                "relevance": 0.9,
                "evidence_kind": "index_evidence",
                "supports_requirement_ids": ["current_gap:GRI2:2-1:a"],
            }
        ],
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI2:2-1:a",
                "requirement_text": "report its legal name;",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "met",
                "supporting_evidence_ids": ["evidence_index_1"],
                "missing_reason": "",
                "manual_review_reason": "",
            }
        ],
        missing_requirements=[],
    )

    result = _validate_assessments([assessment])

    assert result["status"] == "failed"
    assert any("index_evidence" in error and "disclosed" in error for error in result["errors"])


def test_regression_blocked_samples_cannot_return_disclosed_even_with_body_evidence():
    assessment = _base_assessment(
        verdict="disclosed",
        evidence=[
            {
                "evidence_id": "evidence_body_1",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_page": 8,
                "source_text": "The company reports organization details in a narrative section.",
                "relevance": 0.9,
                "evidence_kind": "substantive_report_evidence",
                "supports_requirement_ids": ["current_gap:GRI2:2-1:a"],
            }
        ],
        requirement_checks=[_met_requirement_check()],
        missing_requirements=[],
    )

    result = _validate_assessments([assessment])

    assert result["status"] == "failed"
    assert any("blocked_verdicts" in error and "disclosed" in error for error in result["errors"])


def test_disclosed_requires_requirement_checks_and_all_mandatory_requirements_met():
    no_checks = _base_assessment(verdict="disclosed", requirement_checks=[], missing_requirements=[])
    unmet_check = _base_assessment(
        verdict="disclosed",
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI2:2-1:a",
                "requirement_text": "report its legal name;",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_met",
                "supporting_evidence_ids": [],
                "missing_reason": "Missing legal name.",
                "manual_review_reason": "",
            }
        ],
        missing_requirements=[],
    )

    result = _validate_assessments([no_checks, unmet_check])

    assert result["status"] == "failed"
    assert any("requires requirement_checks" in error for error in result["errors"])
    assert any("mandatory requirement" in error and "not met" in error for error in result["errors"])


def test_disclosed_requires_all_mandatory_checklist_requirements_covered():
    assessment = _base_assessment(
        manifest_item_id="current_gap:GRI401:401-1",
        standard_id="GRI401",
        canonical_disclosure_id="401-1",
        verdict="disclosed",
        evidence=[
            {
                "evidence_id": "evidence_body_1",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_page": 50,
                "source_text": "The report discloses new employee hires and turnover by category.",
                "relevance": 0.9,
                "evidence_kind": "substantive_report_evidence",
                "supports_requirement_ids": ["current_gap:GRI401:401-1:a"],
            }
        ],
        requirement_checks=[_met_requirement_check("current_gap:GRI401:401-1:a")],
        missing_requirements=[],
    )

    result = _validate_assessments([assessment])

    assert result["status"] == "failed"
    assert any("missing mandatory requirement checks" in error for error in result["errors"])

def test_partially_disclosed_must_list_missing_requirements():
    assessment = _base_assessment(verdict="partially_disclosed", missing_requirements=[])

    result = _validate_assessments([assessment])

    assert result["status"] == "failed"
    assert any("partially_disclosed" in error and "missing_requirements or partial_requirements" in error for error in result["errors"])


def test_partially_disclosed_can_be_supported_by_partial_requirements():
    assessment = _base_assessment(
        verdict="partially_disclosed",
        missing_requirements=[],
        partial_requirements=["current_gap:GRI2:2-1:a"],
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI2:2-1:a",
                "requirement_text": "report its legal name;",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "partially_met",
                "supporting_evidence_ids": ["evidence_body_1"],
                "missing_reason": "Partially supported.",
                "manual_review_reason": "",
            }
        ],
    )

    result = _validate_assessments([assessment])

    assert result["status"] == "ok"


def test_not_applicable_requires_omission_explanation_and_pending_manual_review():
    assessment = _base_assessment(
        verdict="not_applicable",
        review_status="approved",
        evidence=[
            {
                "evidence_id": "evidence_body_1",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_page": 20,
                "source_text": "The report mentions the topic but gives no explicit omission explanation.",
                "relevance": 0.5,
                "evidence_kind": "substantive_report_evidence",
                "supports_requirement_ids": [],
            }
        ],
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI302:302-4:a",
                "requirement_text": "Amount of reductions in energy consumption achieved.",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_applicable_claimed",
                "supporting_evidence_ids": [],
                "missing_reason": "",
                "manual_review_reason": "",
            }
        ],
        missing_requirements=[],
    )

    result = _validate_assessments([assessment])

    assert result["status"] == "failed"
    assert any("omission_or_not_applicable_explanation" in error for error in result["errors"])
    assert any("review_status" in error and "pending" in error for error in result["errors"])


def test_non_current_gap_policy_not_applicable_does_not_require_omission_evidence():
    assessment = _base_assessment(
        manifest_item_id="readiness_2026:GRI101",
        standard_id="GRI101",
        canonical_disclosure_id="101",
        assessment_mode="readiness_2026",
        verdict="not_applicable",
        evidence=[],
        requirement_checks=[],
        missing_requirements=[],
        rationale="readiness_2026:GRI101 is not scored in 2024 current disclosure results.",
    )

    result = _validate_assessments([assessment])

    assert result["status"] == "ok"


def test_generic_3_3_requires_manual_review_with_topic_instantiation_reason():
    assessment = _base_assessment(
        manifest_item_id="current_gap:GRI3:3-3_generic",
        standard_id="GRI3",
        canonical_disclosure_id="3-3_generic",
        verdict="partially_disclosed",
        manual_review_requirements=[],
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI3:3-3_generic",
                "requirement_text": "GRI 3-3 must be assessed per material topic.",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_assessed",
                "supporting_evidence_ids": [],
                "missing_reason": "Generic 3-3 cannot be scored directly.",
                "manual_review_reason": "",
            }
        ],
    )

    result = _validate_assessments([assessment])

    assert result["status"] == "failed"
    assert any("3-3_generic" in error and "manual_review" in error for error in result["errors"])
    assert any("needs_topic_instantiation" in error for error in result["errors"])


def test_regression_manifest_contains_required_high_risk_samples():
    manifest_path = Path("data/knowledge_base/manifests/p0_stage_e2_regression_manifest.json")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    sample_ids = {item["manifest_item_id"] for item in payload["regression_items"]}

    assert {
        "current_gap:GRI2:2-1",
        "current_gap:GRI302:302-4",
        "current_gap:GRI3:3-3_generic",
    } <= sample_ids


def test_analyst_guardrail_sanitizes_chunk_shaped_evidence_and_handles_no_evidence_verdicts():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context()
    payload = _base_assessment(
        verdict="disclosed",
        evidence=[
            {
                "chunk_id": "idx1",
                "pdf_page": 72,
                "text": "GRI 2-1 page reference",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_text": "GRI 2-1 page reference",
                "relevance": 0.9,
            }
        ],
        requirement_checks=[_met_requirement_check()],
        missing_requirements=[],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert guarded["verdict"] == "manual_review"
    assert guarded["evidence"][0]["source_page"] == 72
    assert "pdf_page" not in guarded["evidence"][0]
    assert "text" not in guarded["evidence"][0]

    no_evidence_disclosed = analyst._apply_p0_guardrails(
        _base_assessment(verdict="disclosed", evidence=[], missing_requirements=[]),
        context,
    )
    assert no_evidence_disclosed["verdict"] == "manual_review"

    no_evidence_not_disclosed = analyst._apply_p0_guardrails(
        _base_assessment(verdict="not_disclosed", evidence=[], missing_requirements=[]),
        context,
    )
    assert no_evidence_not_disclosed["verdict"] == "not_disclosed"
    assert no_evidence_not_disclosed["manual_review_requirements"] == []

    future_context = _agent_context(
        manifest_item_id="readiness_2026:GRI101",
        analysis_mode="readiness_2026",
        canonical_disclosure_id="101",
        forced_verdict="not_applicable",
        can_score_current_gap=False,
        policy_reason="Non-current-gap item is handled as readiness or watchlist narrative.",
        requirement_checklist_items=[],
        report_evidence_chunks=[],
    )
    future_payload = _base_assessment(
        manifest_item_id="readiness_2026:GRI101",
        canonical_disclosure_id="101",
        assessment_mode="readiness_2026",
        verdict="disclosed",
        evidence=[],
        requirement_checks=[],
        missing_requirements=[],
    )
    guarded_future = analyst._apply_p0_guardrails(future_payload, future_context)
    assert guarded_future["verdict"] == "not_applicable"
    assert guarded_future["readiness_verdict"] == "readiness_gap"


def test_analyst_guardrail_downgrades_disclosed_when_mandatory_checks_are_missing():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context(
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI401:401-1:a", "is_mandatory": True, "scoring_role": "hard_score"},
            {"requirement_id": "current_gap:GRI401:401-1:b", "is_mandatory": True, "scoring_role": "hard_score"},
        ],
    )
    payload = _base_assessment(
        manifest_item_id="current_gap:GRI401:401-1",
        canonical_disclosure_id="401-1",
        verdict="disclosed",
        evidence=[
            {
                "evidence_id": "evidence_body_1",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_page": 50,
                "source_text": "The report discloses new hires.",
                "relevance": 0.9,
                "evidence_kind": "substantive_report_evidence",
                "supports_requirement_ids": ["current_gap:GRI401:401-1:a"],
            }
        ],
        requirement_checks=[_met_requirement_check("current_gap:GRI401:401-1:a")],
        missing_requirements=[],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert guarded["verdict"] == "partially_disclosed"
    assert "current_gap:GRI401:401-1:b" in guarded["missing_requirements"]
    assert guarded["aggregation_reason"] == "mandatory_requirement_checks_missing"



def test_analyst_p0_branch_adds_manual_review_for_missing_llm_assessments(monkeypatch):
    analyst_module = importlib.import_module("src.agent.analyst_agent")
    analyst = analyst_module.AnalystAgent()
    analyst.analyst_prompt = type("Prompt", (), {"render": lambda self, **kwargs: "prompt"})()
    returned_context = _agent_context(
        standard_id="GRI2",
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI2:2-1:a", "is_mandatory": True, "scoring_role": "hard_score"}
        ],
    )
    missing_context = _agent_context(
        manifest_item_id="current_gap:GRI2:2-2",
        standard_id="GRI2",
        canonical_disclosure_id="2-2",
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI2:2-2:a", "is_mandatory": True, "scoring_role": "hard_score"},
            {"requirement_id": "current_gap:GRI2:2-2:parent", "is_mandatory": False, "scoring_role": "aggregation_parent"},
        ],
    )
    llm_assessment = _base_assessment(
        requirement_checks=[_met_requirement_check("current_gap:GRI2:2-1:a")],
        missing_requirements=[],
    )

    monkeypatch.setattr(analyst_module, "call_llm", lambda messages: "{}")
    monkeypatch.setattr(
        analyst_module,
        "clean_and_parse_json",
        lambda output, logger=None: {"disclosure_assessments": [llm_assessment]},
    )

    result = analyst._execute(
        {
            "retrieval_result": {
                "p0_requirement_contexts": [returned_context, missing_context],
                "input_text": "",
            }
        }
    )

    by_id = {item["manifest_item_id"]: item for item in result["disclosure_assessments"]}
    assert set(by_id) == {"current_gap:GRI2:2-1", "current_gap:GRI2:2-2"}
    missing = by_id["current_gap:GRI2:2-2"]
    assert missing["verdict"] == "manual_review"
    assert missing["aggregation_reason"] == "missing_llm_assessment_for_manifest_item"
    assert missing["manual_review_requirements"] == ["current_gap:GRI2:2-2:a"]
    assert missing["manual_review_reason_codes"] == ["missing_llm_assessment_for_manifest_item"]


def test_analyst_guardrail_ignores_non_hard_score_fake_mandatory_checks():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context(
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI401:401-1:a", "is_mandatory": True, "scoring_role": "hard_score"},
            {"requirement_id": "current_gap:GRI401:401-1:2.1", "is_mandatory": False, "scoring_role": "scope_review"},
            {"requirement_id": "current_gap:GRI401:401-1:parent", "is_mandatory": False, "scoring_role": "aggregation_parent"},
        ],
    )
    payload = _base_assessment(
        manifest_item_id="current_gap:GRI401:401-1",
        canonical_disclosure_id="401-1",
        verdict="disclosed",
        evidence=[
            {
                "evidence_id": "evidence_body_1",
                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                "source_page": 50,
                "source_text": "The report discloses new hires.",
                "relevance": 0.9,
                "evidence_kind": "substantive_report_evidence",
                "supports_requirement_ids": ["current_gap:GRI401:401-1:a"],
            }
        ],
        requirement_checks=[
            _met_requirement_check("current_gap:GRI401:401-1:a"),
            {
                "requirement_id": "current_gap:GRI401:401-1:2.1",
                "requirement_text": "scope review item",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_met",
                "supporting_evidence_ids": [],
                "missing_reason": "Fake mandatory flag from LLM.",
                "manual_review_reason": "",
            },
            {
                "requirement_id": "current_gap:GRI401:401-1:parent",
                "requirement_text": "aggregation parent item",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_met",
                "supporting_evidence_ids": [],
                "missing_reason": "Fake mandatory flag from LLM.",
                "manual_review_reason": "",
            },
        ],
        missing_requirements=[],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert guarded["verdict"] == "disclosed"
    assert guarded.get("missing_requirements", []) == []


def test_analyst_guardrail_backfills_uncovered_hard_score_requirements_for_partial():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context(
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI401:401-1:a", "is_mandatory": True, "scoring_role": "hard_score"},
            {"requirement_id": "current_gap:GRI401:401-1:b", "is_mandatory": True, "scoring_role": "hard_score"},
            {"requirement_id": "current_gap:GRI401:401-1:2.1", "is_mandatory": False, "scoring_role": "scope_review"},
        ],
    )
    payload = _base_assessment(
        manifest_item_id="current_gap:GRI401:401-1",
        canonical_disclosure_id="401-1",
        verdict="partially_disclosed",
        requirement_checks=[_met_requirement_check("current_gap:GRI401:401-1:a")],
        missing_requirements=["current_gap:GRI401:401-1:2.1"],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert "current_gap:GRI401:401-1:b" in guarded["missing_requirements"]
    assert "current_gap:GRI401:401-1:2.1" not in guarded["missing_requirements"]


def test_analyst_guardrail_excludes_parent_intro_compilation_nodes_from_missing():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context(
        manifest_item_id="current_gap:GRI301:301-2",
        canonical_disclosure_id="301-2",
        requirement_checklist_items=[
            {
                "requirement_id": "current_gap:GRI301:301-2:a",
                "requirement_type": "requirement",
                "requirement_text": "Percentage of recycled input materials used.",
                "is_mandatory": True,
                "scoring_role": "hard_score",
            },
            {
                "requirement_id": "current_gap:GRI301:301-2:2.2",
                "requirement_type": "compilation_requirement",
                "requirement_text": "When compiling the information specified in Disclosure 301-2, the reporting organization shall:",
                "is_mandatory": True,
                "scoring_role": "hard_score",
            },
            {
                "requirement_id": "current_gap:GRI301:301-2:2.2.1",
                "requirement_type": "compilation_requirement",
                "requirement_text": "use the total weight or volume of materials used as specified in Disclosure 301-1;",
                "is_mandatory": True,
                "scoring_role": "hard_score",
            },
            {
                "requirement_id": "current_gap:GRI301:301-2:2.2.2",
                "requirement_type": "compilation_requirement",
                "requirement_text": "calculate the percentage of recycled input materials used by applying the formula;",
                "is_mandatory": True,
                "scoring_role": "hard_score",
            },
        ],
    )
    payload = _base_assessment(
        manifest_item_id="current_gap:GRI301:301-2",
        canonical_disclosure_id="301-2",
        verdict="partially_disclosed",
        requirement_checks=[_met_requirement_check("current_gap:GRI301:301-2:a")],
        missing_requirements=["current_gap:GRI301:301-2:2.2"],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert "current_gap:GRI301:301-2:2.2" not in guarded["missing_requirements"]
    assert "current_gap:GRI301:301-2:2.2.1" in guarded["missing_requirements"]
    assert "current_gap:GRI301:301-2:2.2.2" in guarded["missing_requirements"]


def test_validation_script_supports_assessment_file_and_no_arg_self_check(tmp_path):
    validator = importlib.import_module("scripts.validate_stage_e2_1_evidence_contract")
    assessment_path = tmp_path / "assessment.json"
    assessment_path.write_text(json.dumps({"disclosure_assessments": [_base_assessment()]}), encoding="utf-8")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "analyst_result.json").write_text(
        json.dumps({"disclosure_assessments": [_base_assessment()]}),
        encoding="utf-8",
    )
    manual_review_path = tmp_path / "manual_review_result.json"
    manual_review_path.write_text(
        json.dumps(
            {
                "items": [
                    {"manifest_item_id": "current_gap:GRI2:2-1", "human_verdict": "partially_disclosed"},
                    {
                        "manifest_item_id": "current_gap:GRI3:3-3_generic",
                        "human_verdict": "manual_review",
                        "error_type": "needs_topic_instantiation",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    assert validator.main([]) == 0
    assert validator.main(["--assessment-file", str(assessment_path)]) == 0
    assert validator.main(["--run-dir", str(run_dir)]) == 0
    assert validator.main(["--manual-review-result", str(manual_review_path)]) == 0


def test_validator_excludes_parent_intro_compilation_nodes_from_mandatory_coverage(tmp_path):
    validator = importlib.import_module("scripts.validate_stage_e2_1_evidence_contract")
    checklist_path = tmp_path / "checklist.json"
    checklist_path.write_text(
        json.dumps(
            {
                "requirements": [
                    {
                        "requirement_id": "current_gap:GRI301:301-2:2.2",
                        "parent_requirement_id": "current_gap:GRI301:301-2",
                        "requirement_type": "compilation_requirement",
                        "requirement_text": "When compiling the information specified in Disclosure 301-2, the reporting organization shall:",
                        "assessment_mode": "current_gap",
                        "is_mandatory": True,
                        "scoring_role": "hard_score",
                    },
                    {
                        "requirement_id": "current_gap:GRI301:301-2:2.2.1",
                        "parent_requirement_id": "current_gap:GRI301:301-2",
                        "requirement_type": "compilation_requirement",
                        "requirement_text": "use the total weight or volume of materials used as specified in Disclosure 301-1;",
                        "assessment_mode": "current_gap",
                        "is_mandatory": True,
                        "scoring_role": "hard_score",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    by_parent, warnings = validator._mandatory_requirement_ids_by_parent(checklist_path)

    assert warnings == []
    assert "current_gap:GRI301:301-2:2.2" not in by_parent["current_gap:GRI301:301-2"]
    assert "current_gap:GRI301:301-2:2.2.1" in by_parent["current_gap:GRI301:301-2"]


def test_analyst_guardrail_sets_reason_for_generic_3_3_and_not_applicable_without_explanation():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()

    generic = analyst._apply_p0_guardrails(
        _base_assessment(
            manifest_item_id="current_gap:GRI3:3-3_generic",
            standard_id="GRI3",
            canonical_disclosure_id="3-3_generic",
            verdict="partially_disclosed",
        ),
        _agent_context(
            manifest_item_id="current_gap:GRI3:3-3_generic",
            standard_id="GRI3",
            canonical_disclosure_id="3-3_generic",
            requirement_checklist_items=[],
        ),
    )
    assert generic["verdict"] == "manual_review"
    assert generic["manual_review_reason_codes"] == ["needs_topic_instantiation"]

    not_applicable = analyst._apply_p0_guardrails(
        _base_assessment(verdict="not_applicable", missing_requirements=[]),
        _agent_context(),
    )
    assert not_applicable["verdict"] == "manual_review"
    assert not_applicable["manual_review_reason_codes"] == ["omission_reason_requires_review"]


def test_e2_1_d_validator_requires_body_evidence_for_known_over_manual_review_samples(tmp_path):
    validator = importlib.import_module("scripts.validate_stage_e2_1_evidence_contract")
    assessment_path = tmp_path / "analyst_result.json"
    assessment_path.write_text(
        json.dumps(
            {
                "disclosure_assessments": [
                    _base_assessment(
                        manifest_item_id="current_gap:GRI302:302-4",
                        standard_id="GRI302",
                        canonical_disclosure_id="302-4",
                        verdict="manual_review",
                        evidence=[
                            {
                                "evidence_id": "idx",
                                "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
                                "source_page": 73,
                                "source_text": "302-4 降低能源消耗量 智慧用能，资源善用 22",
                                "relevance": 0.9,
                                "evidence_kind": "index_evidence",
                                "supports_requirement_ids": [],
                            }
                        ],
                        requirement_checks=[],
                    )
                ]
            }
        ),
        encoding="utf-8",
    )

    result = validator.validate_assessment_file(assessment_path, require_e2_1_d_body_evidence=True)

    assert result["status"] == "failed"
    assert any("requires non-index body evidence candidate" in error for error in result["errors"])

def test_analyst_treats_missing_scoring_role_as_hard_score_for_backward_compatibility():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context(
        requirement_checklist_items=[{"requirement_id": "current_gap:GRI2:2-1:a", "is_mandatory": True}]
    )

    assert analyst._mandatory_requirement_ids(context) == ["current_gap:GRI2:2-1:a"]


def test_analyst_guardrail_normalizes_requirement_support_status_aliases():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context(
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI2:2-1:a", "is_mandatory": True, "scoring_role": "hard_score"}
        ],
    )
    payload = _base_assessment(
        verdict="partially_disclosed",
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI2:2-1:a",
                "requirement_text": "report its legal name;",
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "partial_met",
                "supporting_evidence_ids": ["evidence_body_1"],
                "missing_reason": "",
                "manual_review_reason": "",
            }
        ],
        missing_requirements=[],
        partial_requirements=[],
    )

    guarded = analyst._apply_p0_guardrails(payload, context)

    assert guarded["requirement_checks"][0]["support_status"] == "partially_met"
    assert guarded["partial_requirements"] == ["current_gap:GRI2:2-1:a"]


def test_analyst_guardrail_keeps_no_evidence_not_disclosed_only_with_full_not_met_checks():
    analyst = importlib.import_module("src.agent.analyst_agent").AnalystAgent()
    context = _agent_context(
        requirement_checklist_items=[
            {"requirement_id": "current_gap:GRI2:2-8:a", "is_mandatory": True, "scoring_role": "hard_score"},
            {"requirement_id": "current_gap:GRI2:2-8:b", "is_mandatory": True, "scoring_role": "hard_score"},
        ],
    )
    incomplete_payload = _base_assessment(
        manifest_item_id="current_gap:GRI2:2-8",
        canonical_disclosure_id="2-8",
        verdict="not_disclosed",
        evidence=[],
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI2:2-8:a",
                "requirement_text": "report the total number of workers who are not employees;",
                "is_mandatory": True,
                "support_status": "not_met",
            }
        ],
        missing_requirements=["current_gap:GRI2:2-8:a"],
    )
    guarded_incomplete = analyst._apply_p0_guardrails(incomplete_payload, context)
    assert guarded_incomplete["verdict"] == "manual_review"

    complete_payload = _base_assessment(
        manifest_item_id="current_gap:GRI2:2-8",
        canonical_disclosure_id="2-8",
        verdict="not_disclosed",
        evidence=[],
        requirement_checks=[
            {
                "requirement_id": "current_gap:GRI2:2-8:a",
                "requirement_text": "report the total number of workers who are not employees;",
                "is_mandatory": True,
                "support_status": "not_met",
            },
            {
                "requirement_id": "current_gap:GRI2:2-8:b",
                "requirement_text": "describe methodologies used to compile the data;",
                "is_mandatory": True,
                "support_status": "not_met",
            },
        ],
        missing_requirements=["current_gap:GRI2:2-8:a", "current_gap:GRI2:2-8:b"],
    )
    guarded_complete = analyst._apply_p0_guardrails(complete_payload, context)
    assert guarded_complete["verdict"] == "not_disclosed"


def test_disclosure_assessment_rejects_unknown_manual_review_and_readiness_codes():
    contract = importlib.import_module("src.models.analysis_contract")

    with pytest.raises(Exception):
        contract.DisclosureAssessment(
            manifest_item_id="current_gap:GRI2:2-1",
            standard_id="GRI2",
            assessment_mode="current_gap",
            verdict="manual_review",
            confidence=0.2,
            evidence=[],
            requirement_checks=[],
            rationale="bad reason code",
            manual_review_reason_codes=["typo_reason"],
        )

    with pytest.raises(Exception):
        contract.DisclosureAssessment(
            manifest_item_id="readiness_2026:GRI101",
            standard_id="GRI101",
            assessment_mode="readiness_2026",
            verdict="not_applicable",
            confidence=0.2,
            evidence=[],
            requirement_checks=[],
            rationale="bad readiness code",
            readiness_verdict="ready_enough",
        )


def test_validator_ignores_non_hard_score_fake_mandatory_checks_for_disclosed():
    validator = importlib.import_module("scripts.validate_stage_e2_1_evidence_contract")
    hard_score_ids, warnings = validator._mandatory_requirement_ids_by_parent()
    assert not warnings
    parent_id = "current_gap:GRI401:401-1"
    checks = [
        {
            "requirement_id": requirement_id,
            "requirement_text": "hard score requirement",
            "is_mandatory": True,
            "support_status": "met",
        }
        for requirement_id in sorted(hard_score_ids[parent_id])
    ]
    checks.append(
        {
            "requirement_id": "current_gap:GRI401:401-1:2.1",
            "requirement_text": "scope review row",
            "is_mandatory": True,
            "support_status": "not_met",
        }
    )
    assessment = _base_assessment(
        manifest_item_id=parent_id,
        standard_id="GRI401",
        canonical_disclosure_id="401-1",
        verdict="disclosed",
        requirement_checks=checks,
        missing_requirements=[],
    )

    result = validator.validate_assessments([assessment])

    assert result["status"] == "ok"



