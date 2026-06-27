"""Builders for the P0 GRI requirement pack and report evidence index."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from pypdf import PdfReader

from src.config.paths import (
    ENVISION_2024_ZH_REPORT_PATH,
    GRI_REFERENCE_PDF_PATH,
    P0_GRI_DISCLOSURE_MANIFEST_PATH,
    P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH,
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

MANUAL_LOCATOR_REVIEWS_BY_MANIFEST_ITEM_ID: Dict[str, Dict[str, Any]] = {
    "current_gap:GRI2:2-21": {
        "review_status": "confirmed",
        "confirmed_official_pdf_pages": [68],
        "confirmed_title": "Disclosure 2-21 Annual total compensation ratio",
        "review_reason": "Page 68 contains the formal Disclosure 2-21 title and reporting requirement; page 51 is guidance text and is excluded.",
        "reviewed_at": "2026-06-26",
    },
    "current_gap:GRI207:207-4": {
        "review_status": "confirmed",
        "confirmed_official_pdf_pages": [663],
        "confirmed_title": "Disclosure 207-4 Country-by-country reporting",
        "review_reason": "Page 663 contains the formal Disclosure 207-4 title and reporting requirement; pages 664 and 665 are guidance text for Disclosure 207-4-b-i and Disclosure 207-4-b-viii and are excluded.",
        "reviewed_at": "2026-06-26",
    },
    "current_gap:GRI306:306-4": {
        "review_status": "confirmed",
        "confirmed_official_pdf_pages": [779],
        "confirmed_title": "Disclosure 306-4 Waste diverted from disposal",
        "review_reason": "Page 779 contains the formal Disclosure 306-4 title and reporting requirement; page 789 is appendix content and is excluded.",
        "reviewed_at": "2026-06-26",
    },
    "current_gap:GRI401:401-1": {
        "review_status": "confirmed",
        "confirmed_official_pdf_pages": [807],
        "confirmed_title": "Disclosure 401-1 New employee hires and employee turnover",
        "review_reason": "Page 807 contains the formal Disclosure 401-1 title and reporting requirement; page 814 is Standard Interpretations content and is excluded.",
        "reviewed_at": "2026-06-26",
    },
    "current_gap:GRI403:403-2": {
        "review_status": "confirmed",
        "confirmed_official_pdf_pages": [833],
        "confirmed_title": "Disclosure 403-2 Hazard identification, risk assessment, and incident investigation",
        "review_reason": "Page 833 contains the formal Disclosure 403-2 title and reporting requirement; page 844 is guidance text for Disclosure 403-9-c and is excluded.",
        "reviewed_at": "2026-06-26",
    },
}

@dataclass(frozen=True)
class GRIStandardSection:
    standard_id: str
    standard_year: str
    title: str
    start_pdf_page: int
    end_pdf_page: int


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _requirement_pack_payload_for_json(pack: GRIRequirementPack) -> Dict[str, Any]:
    payload = pack.model_dump(mode="json")
    for requirement in payload.get("requirements", []):
        if requirement.get("manual_locator_review") is None:
            requirement.pop("manual_locator_review", None)
    return payload


def write_gri_requirement_pack(
    pack: GRIRequirementPack,
    path: Path = P0_GRI_REQUIREMENT_PACK_PATH,
) -> None:
    _write_json(path, _requirement_pack_payload_for_json(pack))


def write_report_evidence_index(
    index: ReportEvidenceIndex,
    path: Path = P0_REPORT_EVIDENCE_INDEX_PATH,
) -> None:
    _write_json(path, index.model_dump(mode="json"))


def write_gri_locator_refinement_audit(
    audit: Dict[str, Any],
    path: Path = P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH,
) -> None:
    _write_json(path, audit)


def _source_by_document_type(source_manifest: Dict[str, Any], document_type: str) -> Dict[str, Any]:
    matches = [item for item in source_manifest.get("sources", []) if item.get("document_type") == document_type]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one source with document_type={document_type!r}, got {len(matches)}")
    return matches[0]


def _report_metadata_for_chunks(source_manifest: Dict[str, Any]) -> Dict[str, Any]:
    report_source = _source_by_document_type(source_manifest, REPORT_DOCUMENT_TYPE)
    reporting_period = report_source.get("reporting_period") or {}
    report_year = report_source.get("year")
    if report_year is None:
        period_end = str(reporting_period.get("end") or "")
        report_year = int(period_end[:4]) if period_end[:4].isdigit() else 2024
    return {
        "company": report_source.get("company") or report_source.get("publisher") or "Envision Energy",
        "report_year": int(report_year),
        "industry": report_source.get("industry") or "renewable_energy",
    }


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


def _standard_id_from_outline_title(title: str) -> Optional[str]:
    match = re.match(r"^(GRI\s+\d+):", title.strip())
    return match.group(1) if match else None


def _standard_year_from_outline_title(title: str) -> str:
    match = re.search(r"\b(20\d{2})\b", title)
    return match.group(1) if match else ""


def _flatten_pdf_outline(reader: PdfReader) -> List[Tuple[int, str, int]]:
    rows: List[Tuple[int, str, int]] = []

    def walk(items: Iterable[Any], depth: int = 0) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item, depth + 1)
                continue
            title = getattr(item, "title", str(item)).strip()
            try:
                page_number = reader.get_destination_page_number(item) + 1
            except Exception:
                continue
            rows.append((depth, title, page_number))

    walk(reader.outline)
    return rows


def _extract_gri_standard_sections(pdf_path: Path = GRI_REFERENCE_PDF_PATH) -> List[GRIStandardSection]:
    reader = PdfReader(str(pdf_path))
    outline_rows = _flatten_pdf_outline(reader)
    top_level_standards = [
        (title, page)
        for depth, title, page in outline_rows
        if depth == 0 and _standard_id_from_outline_title(title)
    ]
    top_level_standards.sort(key=lambda item: item[1])

    sections: List[GRIStandardSection] = []
    for index, (title, start_page) in enumerate(top_level_standards):
        end_page = top_level_standards[index + 1][1] - 1 if index + 1 < len(top_level_standards) else len(reader.pages)
        standard_id = _standard_id_from_outline_title(title)
        if not standard_id:
            continue
        sections.append(
            GRIStandardSection(
                standard_id=standard_id,
                standard_year=_standard_year_from_outline_title(title),
                title=title,
                start_pdf_page=start_page,
                end_pdf_page=end_page,
            )
        )
    return sections


def _section_for_standard(
    sections: Sequence[GRIStandardSection],
    *,
    standard_id: str,
    standard_year: str,
) -> Optional[GRIStandardSection]:
    matching_id = [section for section in sections if section.standard_id == standard_id]
    matching_year = [section for section in matching_id if section.standard_year == standard_year]
    if matching_year:
        return matching_year[0]
    return None


def _line_starts_disclosure_heading(line: str, disclosure_id: str) -> bool:
    stripped = line.strip()
    return bool(
        re.match(
            rf"^Disclosure\s+{re.escape(disclosure_id)}(?:\b|(?=[A-Z]))",
            stripped,
            flags=re.IGNORECASE,
        )
    )


def _line_starts_short_disclosure_heading(line: str, disclosure_id: str) -> bool:
    stripped = line.strip()
    return bool(re.match(rf"^{re.escape(disclosure_id)}\s+[A-Z][A-Za-z]", stripped))


def _is_cross_reference_line(line: str, disclosure_id: str) -> bool:
    lowered = _norm_text(line).lower()
    compact_double_space = f"disclosure  {disclosure_id}".lower()
    reference_markers = [
        "through disclosure",
        "in this standard",
        "is related to",
        "does not require",
        "see references",
        "referred to in disclosure",
    ]
    return (
        "•" in line
        or compact_double_space in lowered
        or any(marker in lowered for marker in reference_markers)
    )


def _score_disclosure_candidate_page(page_text: str, disclosure_id: str) -> Tuple[int, List[str]]:
    lines = [line.strip() for line in page_text.splitlines() if line.strip()]
    matched_lines: List[str] = []
    best_score = 0

    for line in lines:
        is_full_heading = _line_starts_disclosure_heading(line, disclosure_id)
        is_short_heading = _line_starts_short_disclosure_heading(line, disclosure_id)
        if not is_full_heading and not is_short_heading:
            continue

        matched_lines.append(_norm_text(line)[:240])
        if _is_cross_reference_line(line, disclosure_id):
            best_score = max(best_score, 10)
            continue
        if is_full_heading:
            best_score = max(best_score, 100)
            continue
        if is_short_heading:
            best_score = max(best_score, 80)

    return best_score, matched_lines


def _rank_disclosure_pages_within_section(
    *,
    canonical_disclosure_id: str,
    section: GRIStandardSection,
    gri_pages: Sequence[Dict[str, object]],
) -> Tuple[List[int], List[str], List[str]]:
    scored_pages: List[Tuple[int, int, str, str]] = []
    for page in gri_pages:
        page_number = int(page["pdf_page"])
        if page_number < section.start_pdf_page or page_number > section.end_pdf_page:
            continue
        text = str(page.get("text") or "")
        score, matched_lines = _score_disclosure_candidate_page(text, canonical_disclosure_id)
        if score <= 0:
            continue
        title = matched_lines[0] if matched_lines else _title_candidate(text, canonical_disclosure_id, section.standard_id)
        excerpt = _candidate_excerpt(text, matched_lines or [canonical_disclosure_id])
        scored_pages.append((score, page_number, title, excerpt))

    if not scored_pages:
        return [], [], []

    best_score = max(score for score, _, _, _ in scored_pages)
    best_pages = [(page, title, excerpt) for score, page, title, excerpt in scored_pages if score == best_score]
    unique_pages = sorted({page for page, _, _ in best_pages})
    titles = list(dict.fromkeys(title for _, title, _ in best_pages if title))[:8]
    excerpts = list(dict.fromkeys(excerpt for _, _, excerpt in best_pages if excerpt))[:8]
    return unique_pages, titles, excerpts


def _locate_gri_requirement(
    *,
    analysis_mode: str,
    canonical_disclosure_id: Optional[str],
    standard_id: str,
    standard_year: str,
    gri_pages: Sequence[Dict[str, object]],
    sections: Sequence[GRIStandardSection],
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

    if not canonical_disclosure_id:
        return (
            RequirementLocatorStatus.NOT_FOUND,
            [],
            [],
            [],
            True,
            "No canonical disclosure ID is available for locator refinement.",
        )

    section = _section_for_standard(sections, standard_id=standard_id, standard_year=standard_year)
    if not section:
        return (
            RequirementLocatorStatus.NOT_FOUND,
            [],
            [],
            [],
            True,
            f"No official GRI PDF section found for {standard_id} {standard_year}.",
        )

    pages, titles, excerpts = _rank_disclosure_pages_within_section(
        canonical_disclosure_id=canonical_disclosure_id,
        section=section,
        gri_pages=gri_pages,
    )

    if len(pages) == 1:
        return RequirementLocatorStatus.FOUND, pages, titles, excerpts, False, None
    if len(pages) > 1:
        return (
            RequirementLocatorStatus.MULTIPLE_CANDIDATES,
            pages,
            titles,
            excerpts,
            True,
            f"Multiple title-page candidates remain within {section.title}; manual locator review is required.",
        )
    return (
        RequirementLocatorStatus.NOT_FOUND,
        [],
        [],
        [],
        True,
        f"No disclosure heading candidate found within {section.title}.",
    )


def _requirement_payloads(
    gri_pages: Sequence[Dict[str, object]],
    sections: Sequence[GRIStandardSection],
) -> List[Dict[str, Any]]:
    load_p0_gri_disclosure_manifest()
    source_manifest = load_p0_source_manifest()
    gri_source = _source_by_document_type(source_manifest, GRI_DOCUMENT_TYPE)
    requirements: List[Dict[str, Any]] = []
    for item in load_p0_disclosure_items():
        manual_review = MANUAL_LOCATOR_REVIEWS_BY_MANIFEST_ITEM_ID.get(item.manifest_item_id)
        status, pages, titles, excerpts, review_required, review_reason = _locate_gri_requirement(
            analysis_mode=item.analysis_mode.value,
            canonical_disclosure_id=item.canonical_disclosure_id,
            standard_id=item.standard_id,
            standard_year=item.standard_year,
            gri_pages=gri_pages,
            sections=sections,
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
                "manual_locator_review": dict(manual_review) if manual_review else None,
            }
        )
    return requirements


def build_p0_gri_requirement_pack() -> GRIRequirementPack:
    """Build the P0 GRI requirement pack from the disclosure manifest and GRI PDF."""
    metadata = _metadata()
    gri_pages = extract_pdf_pages(GRI_REFERENCE_PDF_PATH)
    sections = _extract_gri_standard_sections(GRI_REFERENCE_PDF_PATH)
    requirements = [GRIRequirement(**payload) for payload in _requirement_payloads(gri_pages, sections)]
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


def build_p0_gri_locator_refinement_audit(
    pack: GRIRequirementPack,
    sections: Sequence[GRIStandardSection],
) -> Dict[str, Any]:
    locator_counts = Counter(req.requirement_locator_status.value for req in pack.requirements)
    review_items = [
        {
            "manifest_item_id": req.manifest_item_id,
            "standard_id": req.standard_id,
            "standard_year": req.standard_year,
            "canonical_disclosure_id": req.canonical_disclosure_id,
            "requirement_locator_status": req.requirement_locator_status.value,
            "official_pdf_page_candidates": req.official_pdf_page_candidates,
            "locator_review_reason": req.locator_review_reason,
            "manual_locator_review": req.manual_locator_review.model_dump(mode="json") if req.manual_locator_review else None,
        }
        for req in pack.requirements
        if req.locator_review_required
    ]
    return {
        "metadata": pack.metadata.model_dump(mode="json"),
        "locator_counts": dict(sorted(locator_counts.items())),
        "locator_review_required_count": len(review_items),
        "sections": [
            {
                "standard_id": section.standard_id,
                "standard_year": section.standard_year,
                "title": section.title,
                "start_pdf_page": section.start_pdf_page,
                "end_pdf_page": section.end_pdf_page,
            }
            for section in sections
        ],
        "locator_review_required": review_items,
    }


def load_existing_p0_report_evidence_index(
    path: Path = P0_REPORT_EVIDENCE_INDEX_PATH,
) -> ReportEvidenceIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ReportEvidenceIndex.model_validate(payload)


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
    report_metadata = _report_metadata_for_chunks(source_manifest)
    for payload in chunk_payloads:
        payload.update(report_metadata)
        payload.setdefault("topic", "general")
    index = ReportEvidenceIndex.model_validate(
        {
            "metadata": metadata.model_dump(mode="json"),
            "chunks": chunk_payloads,
        }
    )
    return index


def build_and_write_p0_evidence_layer(*, rebuild_report_index: bool = False) -> Dict[str, Any]:
    """Build Stage C locator manifests and reuse the report evidence index by default."""
    requirement_pack = build_p0_gri_requirement_pack()
    if rebuild_report_index or not P0_REPORT_EVIDENCE_INDEX_PATH.exists():
        report_index = build_p0_report_evidence_index()
        write_report_index = True
    else:
        report_index = load_existing_p0_report_evidence_index()
        write_report_index = False
    sections = _extract_gri_standard_sections(GRI_REFERENCE_PDF_PATH)
    locator_audit = build_p0_gri_locator_refinement_audit(requirement_pack, sections)
    write_gri_requirement_pack(requirement_pack)
    if write_report_index:
        write_report_evidence_index(report_index)
    write_gri_locator_refinement_audit(locator_audit)
    locator_counts = Counter(req.requirement_locator_status.value for req in requirement_pack.requirements)
    return {
        "status": "ok",
        "requirements_written": len(requirement_pack.requirements),
        "report_chunks_written": len(report_index.chunks),
        "report_evidence_index_rebuilt": write_report_index,
        "requirement_pack_path": str(P0_GRI_REQUIREMENT_PACK_PATH),
        "report_evidence_index_path": str(P0_REPORT_EVIDENCE_INDEX_PATH),
        "locator_refinement_audit_path": str(P0_GRI_LOCATOR_REFINEMENT_AUDIT_PATH),
        "locator_counts": dict(sorted(locator_counts.items())),
        "locator_review_required": requirement_pack.locator_review_required,
        "locator_review_required_count": len(requirement_pack.locator_review_required),
    }

