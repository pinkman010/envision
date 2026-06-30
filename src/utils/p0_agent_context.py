"""P0 Agent context helpers for consuming the frozen evidence layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from src.config.paths import (
    P0_GRI_REQUIREMENT_CHECKLIST_PATH,
    P0_GRI_REQUIREMENT_PACK_PATH,
    P0_REPORT_EVIDENCE_INDEX_PATH,
)
from src.models import (
    GRIRequirementPack,
    P0RequirementChecklist,
    ReportEvidenceIndex,
    RequirementLocatorStatus,
)
from src.models.analysis_contract import AnalysisMode, EvidenceKind
from src.utils.p0_index_target_evidence import (
    build_fulltext_requirement_evidence,
    build_index_target_evidence,
)


def load_p0_requirement_pack(path: Path = P0_GRI_REQUIREMENT_PACK_PATH) -> GRIRequirementPack:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return GRIRequirementPack.model_validate(payload)


def load_p0_report_evidence_index(path: Path = P0_REPORT_EVIDENCE_INDEX_PATH) -> ReportEvidenceIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ReportEvidenceIndex.model_validate(payload)


def load_p0_requirement_checklist(path: Path = P0_GRI_REQUIREMENT_CHECKLIST_PATH) -> P0RequirementChecklist:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return P0RequirementChecklist.model_validate(payload)


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


def _has_horizontal_index_concatenation(text: str) -> bool:
    gri_id_count = len(__import__("re").findall(r"\b\d{1,3}-\d{1,3}\b", text))
    return gri_id_count > 1


def evidence_bundle_for_manifest_item(
    report_index: ReportEvidenceIndex,
    requirement: Any,
    referenced_page_evidence: List[Dict[str, Any]] | None = None,
    nearby_page_evidence: List[Dict[str, Any]] | None = None,
    fulltext_requirement_evidence: List[Dict[str, Any]] | None = None,
) -> Dict[str, List[Dict[str, Any]]]:
    index_evidence: List[Dict[str, Any]] = []
    for chunk in report_chunks_for_manifest_item(report_index, requirement):
        source_text = chunk.get("text", "")
        enriched = dict(chunk)
        enriched.update(
            {
                "evidence_kind": EvidenceKind.INDEX_EVIDENCE.value,
                "evidence_subtype": "gri_content_index_locator",
                "source_document": chunk.get("source_document_relative_path", ""),
                "source_page": chunk.get("pdf_page"),
                "report_page_label": str(requirement.report_index_report_page or ""),
                "source_text": source_text,
                "source_section": "GRI content index",
                "relevance": 1.0,
                "extraction_method": "p0_report_evidence_index",
                "retrieval_method": "gri_content_index_locator",
                "supports_requirement_ids": [],
                "judgment_reason": "GRI index locator only; cannot substantively support requirement.",
            }
        )
        if _has_horizontal_index_concatenation(source_text):
            enriched["source_text_extraction_warning"] = "possible_horizontal_table_concatenation"
        index_evidence.append(enriched)

    return {
        EvidenceKind.INDEX_EVIDENCE.value: index_evidence,
        "referenced_page_evidence": referenced_page_evidence or [],
        "nearby_page_evidence": nearby_page_evidence or [],
        "fulltext_requirement_evidence": fulltext_requirement_evidence or [],
        EvidenceKind.SUBSTANTIVE_REPORT_EVIDENCE.value: [],
        EvidenceKind.OMISSION_OR_NOT_APPLICABLE_EXPLANATION.value: [],
        EvidenceKind.EXTERNAL_REFERENCE_EVIDENCE.value: [],
    }


def build_p0_requirement_contexts() -> List[Dict[str, Any]]:
    pack = load_p0_requirement_pack()
    checklist = load_p0_requirement_checklist()
    report_index = load_p0_report_evidence_index()
    checklist_by_parent: Dict[str, List[Dict[str, Any]]] = {}
    for item in checklist.requirements:
        checklist_by_parent.setdefault(item.parent_requirement_id, []).append(item.model_dump(mode="json"))
    topic_instantiation_by_parent = {
        item.parent_requirement_id: item.model_dump(mode="json")
        for item in checklist.topic_instantiation_required
    }
    contexts: List[Dict[str, Any]] = []

    manifest_item_ids = [item.manifest_item_id for item in pack.requirements]
    index_target_evidence = build_index_target_evidence(manifest_item_ids)
    fulltext_evidence = build_fulltext_requirement_evidence(manifest_item_ids)

    for requirement in pack.requirements:
        policy = assessment_mode_policy(requirement)
        item_index_evidence = index_target_evidence.get(requirement.manifest_item_id, [])
        referenced_page_evidence = [
            item for item in item_index_evidence if item.get("evidence_subtype") == "index_referenced_page"
        ]
        nearby_page_evidence = [
            item for item in item_index_evidence if item.get("evidence_subtype") == "index_referenced_nearby_page"
        ]
        evidence_bundle = evidence_bundle_for_manifest_item(
            report_index,
            requirement,
            referenced_page_evidence=referenced_page_evidence,
            nearby_page_evidence=nearby_page_evidence,
            fulltext_requirement_evidence=fulltext_evidence.get(requirement.manifest_item_id, []),
        )
        report_chunks = [
            {**chunk, "evidence_kind": EvidenceKind.INDEX_EVIDENCE.value}
            for chunk in report_chunks_for_manifest_item(report_index, requirement)
        ]
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
                "requirement_checklist_items": checklist_by_parent.get(requirement.manifest_item_id, []),
                "topic_instantiation_requirement": topic_instantiation_by_parent.get(requirement.manifest_item_id),
                "evidence_bundle": evidence_bundle,
                "report_evidence_chunks": report_chunks,
            }
        )
    return contexts
