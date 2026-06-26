"""P0 Agent context helpers for consuming the frozen evidence layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.config.paths import (
    P0_GRI_REQUIREMENT_PACK_PATH,
    P0_REPORT_EVIDENCE_INDEX_PATH,
)
from src.models import GRIRequirementPack, ReportEvidenceIndex, RequirementLocatorStatus
from src.models.analysis_contract import AnalysisMode


def load_p0_requirement_pack(path: Path = P0_GRI_REQUIREMENT_PACK_PATH) -> GRIRequirementPack:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return GRIRequirementPack.model_validate(payload)


def load_p0_report_evidence_index(path: Path = P0_REPORT_EVIDENCE_INDEX_PATH) -> ReportEvidenceIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ReportEvidenceIndex.model_validate(payload)


def official_pages_for_agent(requirement: Any) -> List[int]:
    if requirement.manual_locator_review is not None:
        return list(requirement.manual_locator_review.confirmed_official_pdf_pages)
    if requirement.requirement_locator_status == RequirementLocatorStatus.FOUND:
        return list(requirement.official_pdf_page_candidates)
    return []


def locator_manual_review_flag(requirement: Any) -> bool:
    if requirement.locator_review_required:
        return True
    if requirement.requirement_locator_status == RequirementLocatorStatus.MULTIPLE_CANDIDATES:
        return True
    if requirement.requirement_locator_status == RequirementLocatorStatus.NOT_FOUND:
        return True
    return False


def assessment_mode_policy(requirement: Any) -> Dict[str, Any]:
    if requirement.requirement_locator_status == RequirementLocatorStatus.REQUIRES_TOPIC_INSTANTIATION:
        return {
            "can_score_current_gap": False,
            "forced_verdict": "manual_review",
            "reason": "GRI 3-3 must be instantiated per material topic before disclosure scoring.",
        }
    if requirement.requirement_locator_status == RequirementLocatorStatus.NOT_REQUIRED_FOR_FUTURE_WATCH:
        return {
            "can_score_current_gap": False,
            "forced_verdict": "not_applicable",
            "reason": "Future readiness/watchlist item is not scored as a 2024 current disclosure gap.",
        }
    if requirement.analysis_mode != AnalysisMode.CURRENT_GAP:
        return {
            "can_score_current_gap": False,
            "forced_verdict": "not_applicable",
            "reason": "Non-current-gap item is handled as readiness or watchlist narrative.",
        }
    return {
        "can_score_current_gap": True,
        "forced_verdict": None,
        "reason": "Current-gap item can be scored if report evidence is sufficient.",
    }


def report_chunks_for_manifest_item(report_index: ReportEvidenceIndex, requirement: Any) -> List[Dict[str, Any]]:
    if requirement.report_index_pdf_page is None:
        return []
    chunks = [chunk for chunk in report_index.chunks if chunk.pdf_page == requirement.report_index_pdf_page]
    return [chunk.model_dump(mode="json") for chunk in chunks]


def build_p0_requirement_contexts() -> List[Dict[str, Any]]:
    pack = load_p0_requirement_pack()
    report_index = load_p0_report_evidence_index()
    contexts: List[Dict[str, Any]] = []

    for requirement in pack.requirements:
        policy = assessment_mode_policy(requirement)
        contexts.append(
            {
                "manifest_item_id": requirement.manifest_item_id,
                "analysis_mode": requirement.analysis_mode.value,
                "standard_id": requirement.standard_id,
                "standard_year": requirement.standard_year,
                "canonical_disclosure_id": requirement.canonical_disclosure_id,
                "canonical_status": requirement.canonical_status.value,
                "evidence_expectation": requirement.evidence_expectation,
                "requirement_locator_status": requirement.requirement_locator_status.value,
                "official_pdf_pages_for_agent": official_pages_for_agent(requirement),
                "official_pdf_page_candidates": list(requirement.official_pdf_page_candidates),
                "locator_review_required": requirement.locator_review_required,
                "agent_manual_review_required": locator_manual_review_flag(requirement),
                "can_score_current_gap": policy["can_score_current_gap"],
                "forced_verdict": policy["forced_verdict"],
                "policy_reason": policy["reason"],
                "report_index_pdf_page": requirement.report_index_pdf_page,
                "report_index_report_page": requirement.report_index_report_page,
                "report_evidence_chunks": report_chunks_for_manifest_item(report_index, requirement),
            }
        )
    return contexts