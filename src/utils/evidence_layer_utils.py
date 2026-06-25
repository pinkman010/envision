"""Builders for the P0 GRI requirement pack and report evidence index."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from src.config.paths import (
    ENVISION_2024_ZH_REPORT_PATH,
    GRI_REFERENCE_PDF_PATH,
    P0_GRI_DISCLOSURE_MANIFEST_PATH,
    P0_GRI_REQUIREMENT_PACK_PATH,
    P0_REPORT_EVIDENCE_INDEX_PATH,
    P0_SOURCE_MANIFEST_PATH,
)
from src.models import (
    AnalysisMode,
    GRIRequirement,
    GRIRequirementPack,
    EvidenceLayerMetadata,
    ReportEvidenceIndex,
    RequirementLocatorStatus,
)
from src.utils.manifest_utils import (
    load_p0_disclosure_items,
    load_p0_gri_disclosure_manifest,
    load_p0_source_manifest,
)
from src.utils.pdf_text_utils import chunk_text_by_page, extract_pdf_pages, sha256_file

DEFAULT_CHUNK_SIZE = 1600
DEFAULT_CHUNK_OVERLAP = 200
REPORT_DOCUMENT_TYPE = "esg_report"
GRI_DOCUMENT_TYPE = "gri_standards_consolidated_set"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_gri_requirement_pack(
    pack: GRIRequirementPack,
    path: Path = P0_GRI_REQUIREMENT_PACK_PATH,
) -> None:
    _write_json(path, pack.model_dump(mode="json"))


def write_report_evidence_index(
    index: ReportEvidenceIndex,
    path: Path = P0_REPORT_EVIDENCE_INDEX_PATH,
) -> None:
    _write_json(path, index.model_dump(mode="json"))


def _source_by_document_type(source_manifest: Dict[str, Any], document_type: str) -> Dict[str, Any]:
    matches = [item for item in source_manifest.get("sources", []) if item.get("document_type") == document_type]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one source with document_type={document_type!r}, got {len(matches)}")
    return matches[0]


def _verify_file_hash(path: Path, expected_sha256: str) -> str:
    actual = sha256_file(path)
    if actual != expected_sha256.upper():
        raise ValueError(f"SHA-256 mismatch for {path}: expected {expected_sha256.upper()}, got {actual}")
    return actual


def _metadata(
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> EvidenceLayerMetadata:
    source_manifest = load_p0_source_manifest()
    report_source = _source_by_document_type(source_manifest, REPORT_DOCUMENT_TYPE)
    gri_source = _source_by_document_type(source_manifest, GRI_DOCUMENT_TYPE)
    report_sha = _verify_file_hash(ENVISION_2024_ZH_REPORT_PATH, str(report_source["sha256"]))
    gri_sha = _verify_file_hash(GRI_REFERENCE_PDF_PATH, str(gri_source["sha256"]))
    return EvidenceLayerMetadata(
        built_at=datetime.now(timezone.utc).isoformat(),
        source_manifest_sha256=sha256_file(P0_SOURCE_MANIFEST_PATH),
        disclosure_manifest_sha256=sha256_file(P0_GRI_DISCLOSURE_MANIFEST_PATH),
        report_source_document_relative_path=str(report_source["relative_path"]),
        report_pdf_sha256=report_sha,
        gri_source_document_relative_path=str(gri_source["relative_path"]),
        gri_pdf_sha256=gri_sha,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def _candidate_excerpt(page_text: str, needle_patterns: Sequence[str]) -> str:
    normalized = _norm_text(page_text)
    lowered = normalized.lower()
    positions = [lowered.find(pattern.lower()) for pattern in needle_patterns if pattern and lowered.find(pattern.lower()) >= 0]
    start = max(min(positions) - 300, 0) if positions else 0
    end = min(start + 900, len(normalized))
    return normalized[start:end].strip()


def _title_candidate(page_text: str, disclosure_id: Optional[str], standard_id: str) -> str:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    probes = []
    if disclosure_id:
        probes.extend([f"Disclosure {disclosure_id}", disclosure_id])
    probes.append(standard_id.replace("GRI ", ""))
    for line in lines:
        for probe in probes:
            if probe and probe.lower() in line.lower():
                return _norm_text(line)[:240]
    return _norm_text(lines[0])[:240] if lines else ""


def _page_matches(page_text: str, canonical_disclosure_id: Optional[str], standard_id: str) -> Tuple[bool, List[str]]:
    normalized = _norm_text(page_text)
    patterns: List[str] = []
    if canonical_disclosure_id:
        patterns.append(f"Disclosure {canonical_disclosure_id}")
        compact_pattern = rf"(?<!\d){re.escape(canonical_disclosure_id)}\s"
        if re.search(re.escape(patterns[0]), normalized, flags=re.IGNORECASE):
            return True, patterns
        if re.search(compact_pattern, normalized, flags=re.IGNORECASE):
            return True, [canonical_disclosure_id]

    standard_number = standard_id.replace("GRI", "").strip()
    if standard_number:
        standard_pattern = rf"(?<!\d){re.escape(standard_number)}(?!\d)"
        if re.search(standard_pattern, normalized, flags=re.IGNORECASE):
            return True, [standard_number]
    return False, patterns


def _locate_gri_requirement(
    *,
    analysis_mode: str,
    canonical_disclosure_id: Optional[str],
    standard_id: str,
    gri_pages: Sequence[Dict[str, object]],
) -> Tuple[RequirementLocatorStatus, List[int], List[str], List[str], bool, Optional[str]]:
    if canonical_disclosure_id == "3-3_generic":
        return (
            RequirementLocatorStatus.REQUIRES_TOPIC_INSTANTIATION,
            [],
            [],
            [],
            False,
            "GRI 3-3 must be instantiated per material topic before disclosure scoring.",
        )
    if analysis_mode != AnalysisMode.CURRENT_GAP.value and not canonical_disclosure_id:
        return (
            RequirementLocatorStatus.NOT_REQUIRED_FOR_FUTURE_WATCH,
            [],
            [],
            [],
            False,
            "Future readiness/watchlist item is not scored as a 2024 disclosure gap.",
        )

    candidate_pages: List[int] = []
    title_candidates: List[str] = []
    excerpt_candidates: List[str] = []
    match_patterns: List[str] = []
    for page in gri_pages:
        text = str(page.get("text") or "")
        matched, patterns = _page_matches(text, canonical_disclosure_id, standard_id)
        if not matched:
            continue
        page_number = int(page["pdf_page"])
        candidate_pages.append(page_number)
        match_patterns = patterns or match_patterns
        title = _title_candidate(text, canonical_disclosure_id, standard_id)
        if title:
            title_candidates.append(title)
        excerpt = _candidate_excerpt(text, patterns)
        if excerpt:
            excerpt_candidates.append(excerpt)

    unique_pages = sorted(set(candidate_pages))
    unique_titles = list(dict.fromkeys(title_candidates))[:8]
    unique_excerpts = list(dict.fromkeys(excerpt_candidates))[:8]
    if len(unique_pages) == 1:
        return RequirementLocatorStatus.FOUND, unique_pages, unique_titles, unique_excerpts, False, None
    if len(unique_pages) > 1:
        return (
            RequirementLocatorStatus.MULTIPLE_CANDIDATES,
            unique_pages,
            unique_titles,
            unique_excerpts,
            True,
            "Multiple official GRI PDF page candidates require manual locator review.",
        )
    return (
        RequirementLocatorStatus.NOT_FOUND,
        [],
        [],
        [],
        True,
        "No page candidate found in the official GRI PDF by disclosure phrase or fallback standard search.",
    )


def _requirement_payloads(gri_pages: Sequence[Dict[str, object]]) -> List[Dict[str, Any]]:
    load_p0_gri_disclosure_manifest()
    source_manifest = load_p0_source_manifest()
    gri_source = _source_by_document_type(source_manifest, GRI_DOCUMENT_TYPE)
    requirements: List[Dict[str, Any]] = []
    for item in load_p0_disclosure_items():
        status, pages, titles, excerpts, review_required, review_reason = _locate_gri_requirement(
            analysis_mode=item.analysis_mode.value,
            canonical_disclosure_id=item.canonical_disclosure_id,
            standard_id=item.standard_id,
            gri_pages=gri_pages,
        )
        requirements.append(
            {
                "analysis_mode": item.analysis_mode.value,
                "manifest_item_id": item.manifest_item_id,
                "standard_id": item.standard_id,
                "standard_title_zh_or_en": item.standard_title_zh_or_en,
                "standard_year": item.standard_year,
                "source_disclosure_id": item.source_disclosure_id,
                "canonical_disclosure_id": item.canonical_disclosure_id,
                "canonical_status": item.canonical_status.value,
                "effective_date": item.effective_date,
                "related_current_standard": item.related_current_standard,
                "report_index_pdf_page": item.report_index_pdf_page,
                "report_index_report_page": item.report_index_report_page,
                "evidence_expectation": item.evidence_expectation,
                "notes": item.notes,
                "requirement_locator_status": status.value,
                "official_pdf_page_candidates": pages,
                "english_title_candidates": titles,
                "english_excerpt_candidates": excerpts,
                "translation_status": "not_translated",
                "source_document_relative_path": str(gri_source["relative_path"]),
                "source_document_sha256": str(gri_source["sha256"]).upper(),
                "locator_review_required": review_required,
                "locator_review_reason": review_reason,
            }
        )
    return requirements


def build_p0_gri_requirement_pack() -> GRIRequirementPack:
    """Build the P0 GRI requirement pack from the disclosure manifest and GRI PDF."""
    metadata = _metadata()
    gri_pages = extract_pdf_pages(GRI_REFERENCE_PDF_PATH)
    requirements = [GRIRequirement(**payload) for payload in _requirement_payloads(gri_pages)]
    locator_review_required = [
        requirement.manifest_item_id
        for requirement in requirements
        if requirement.requirement_locator_status
        in {RequirementLocatorStatus.NOT_FOUND, RequirementLocatorStatus.MULTIPLE_CANDIDATES}
    ]
    pack = GRIRequirementPack.model_validate(
        {
            "metadata": metadata.model_dump(mode="json"),
            "requirements": [item.model_dump(mode="json") for item in requirements],
            "locator_review_required": locator_review_required,
        }
    )
    return pack


def build_p0_report_evidence_index(
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> ReportEvidenceIndex:
    """Build the P0 report evidence index from the Envision 2024 Chinese ESG report."""
    source_manifest = load_p0_source_manifest()
    report_source = _source_by_document_type(source_manifest, REPORT_DOCUMENT_TYPE)
    metadata = _metadata(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    pages = extract_pdf_pages(ENVISION_2024_ZH_REPORT_PATH)
    chunk_payloads = chunk_text_by_page(
        pages,
        source_document_relative_path=str(report_source["relative_path"]),
        source_document_sha256=str(report_source["sha256"]),
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    index = ReportEvidenceIndex.model_validate(
        {
            "metadata": metadata.model_dump(mode="json"),
            "chunks": chunk_payloads,
        }
    )
    return index


def build_and_write_p0_evidence_layer() -> Dict[str, Any]:
    """Build both Stage C manifests and write them to disk."""
    requirement_pack = build_p0_gri_requirement_pack()
    report_index = build_p0_report_evidence_index()
    write_gri_requirement_pack(requirement_pack)
    write_report_evidence_index(report_index)
    locator_counts = Counter(req.requirement_locator_status.value for req in requirement_pack.requirements)
    return {
        "status": "ok",
        "requirements_written": len(requirement_pack.requirements),
        "report_chunks_written": len(report_index.chunks),
        "requirement_pack_path": str(P0_GRI_REQUIREMENT_PACK_PATH),
        "report_evidence_index_path": str(P0_REPORT_EVIDENCE_INDEX_PATH),
        "locator_counts": dict(sorted(locator_counts.items())),
        "locator_review_required": requirement_pack.locator_review_required,
    }
