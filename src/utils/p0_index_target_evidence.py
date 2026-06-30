"""Build P0 body evidence candidates from GRI index locators and full-text keywords."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.config.paths import P0_GRI_REQUIREMENT_PACK_PATH, P0_REPORT_EVIDENCE_INDEX_PATH

REPORT_SOURCE_SECTION = "Envision Energy 2024 ESG report body"
INDEX_REASON = "Fetched from GRI index referenced page; requires requirement-level support judgment."
FULLTEXT_REASON = "Fetched by deterministic requirement keyword scan; requires requirement-level support judgment."

P0_REQUIREMENT_KEYWORDS: Dict[str, List[str]] = {
    "current_gap:GRI2:2-1": ["法定名称", "总部", "运营", "远景能源"],
    "current_gap:GRI2:2-21": ["年度总薪酬", "薪酬比率", "商业保密", "从略披露"],
    "current_gap:GRI302:302-4": ["节能", "节电", "能源消耗", "kWh", "千瓦时"],
    "current_gap:GRI306:306-4": ["废弃物回收", "危险废物", "非危险废物", "5R", "吨"],
    "current_gap:GRI401:401-1": ["新进员工", "离职", "员工流失率", "性别", "年龄"],
    "readiness_2026:GRI101": ["生物多样性", "生态", "自然", "保护区", "栖息地"],
}

_DISCLOSURE_ID_RE = re.compile(r"\b\d{1,3}-\d{1,3}\b")
_PAGE_RE = re.compile(r"(?<![A-Za-z0-9-])([1-9]\d{0,2})(?![A-Za-z0-9-])")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_pack(path: Path = P0_GRI_REQUIREMENT_PACK_PATH) -> Dict[str, Any]:
    return _load_json(path)


def _load_report_index(path: Path = P0_REPORT_EVIDENCE_INDEX_PATH) -> Dict[str, Any]:
    return _load_json(path)


def _manifest_lookup(pack: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    payload = pack or _load_pack()
    return {item["manifest_item_id"]: item for item in payload.get("requirements", [])}


def _canonical_disclosure_id(manifest_item_id: str, item: Optional[Dict[str, Any]]) -> str:
    if item and item.get("canonical_disclosure_id"):
        return str(item["canonical_disclosure_id"])
    return manifest_item_id.rsplit(":", 1)[-1]


def _report_page_label_for_pdf_page(pdf_page: int) -> int:
    return max(1, pdf_page - 1)


def _pdf_page_for_report_page_label(report_page_label: int) -> int:
    return report_page_label + 1


def parse_index_target_pages(index_text: str) -> List[int]:
    """Return report page labels referenced by a GRI index row."""
    normalized = index_text.strip()
    if not normalized or normalized in {"/", "／"}:
        return []
    if "/" in normalized and not _PAGE_RE.search(normalized):
        return []

    pages: List[int] = []
    for match in _PAGE_RE.finditer(normalized):
        page = int(match.group(1))
        if page not in pages:
            pages.append(page)
    return pages


def _index_text_for_item(item: Dict[str, Any], report_index: Dict[str, Any]) -> str:
    index_pdf_page = item.get("report_index_pdf_page")
    if not index_pdf_page:
        return ""
    return "\n".join(
        chunk.get("text", "")
        for chunk in report_index.get("chunks", [])
        if chunk.get("pdf_page") == index_pdf_page
    )


def _line_window_for_disclosure(index_text: str, disclosure_id: str) -> str:
    lines = index_text.splitlines()
    for index, line in enumerate(lines):
        if disclosure_id not in line:
            continue
        selected = [line]
        prefix = disclosure_id.split("-", 1)[0]
        for following in lines[index + 1 : index + 4]:
            stripped = following.strip()
            if not stripped:
                continue
            if re.search(rf"\b{re.escape(prefix)}-\d+\b", stripped):
                break
            if stripped.startswith("附录"):
                selected.append(stripped)
                continue
            if _DISCLOSURE_ID_RE.search(stripped):
                continue
        return "\n".join(selected)
    return ""


def _index_target_pages_for_item(item: Dict[str, Any], report_index: Dict[str, Any]) -> List[int]:
    index_text = _index_text_for_item(item, report_index)
    disclosure_id = _canonical_disclosure_id(item["manifest_item_id"], item)
    row_text = _line_window_for_disclosure(index_text, disclosure_id)
    return parse_index_target_pages(row_text)


def _chunks_by_report_page(report_index: Dict[str, Any], report_page: int) -> List[Dict[str, Any]]:
    pdf_page = _pdf_page_for_report_page_label(report_page)
    return [chunk for chunk in report_index.get("chunks", []) if chunk.get("pdf_page") == pdf_page]


def _body_evidence_from_chunk(
    chunk: Dict[str, Any],
    manifest_item_id: str,
    report_page: int,
    subtype: str,
    retrieval_method: str,
    judgment_reason: str,
    relevance: float = 0.7,
) -> Dict[str, Any]:
    source_page = chunk.get("pdf_page")
    if source_page is None:
        source_page = _pdf_page_for_report_page_label(report_page)
    return {
        **chunk,
        "manifest_item_id": manifest_item_id,
        "evidence_kind": "substantive_report_evidence",
        "evidence_subtype": subtype,
        "source_document": chunk.get("source_document_relative_path", ""),
        "source_page": source_page,
        "report_page_label": str(report_page),
        "source_text": chunk.get("text", ""),
        "source_section": REPORT_SOURCE_SECTION,
        "relevance": relevance,
        "retrieval_method": retrieval_method,
        "extraction_method": "p0_report_evidence_index",
        "judgment_reason": judgment_reason,
        "supports_requirement_ids": [],
    }


def _dedupe_evidence(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    deduped: List[Dict[str, Any]] = []
    for item in items:
        key = (item.get("chunk_id"), item.get("evidence_subtype"), item.get("source_page"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def build_index_target_evidence(
    manifest_item_ids: List[str], include_nearby_pages: bool = True
) -> Dict[str, List[Dict[str, Any]]]:
    """Return substantive evidence candidates from index target pages and nearby pages."""
    pack = _load_pack()
    report_index = _load_report_index()
    by_id = _manifest_lookup(pack)
    output: Dict[str, List[Dict[str, Any]]] = {}

    for manifest_item_id in manifest_item_ids:
        item = by_id.get(manifest_item_id)
        if item is None:
            output[manifest_item_id] = []
            continue
        target_pages = _index_target_pages_for_item(item, report_index)
        evidence: List[Dict[str, Any]] = []
        for page in target_pages:
            for chunk in _chunks_by_report_page(report_index, page):
                evidence.append(
                    _body_evidence_from_chunk(
                        chunk,
                        manifest_item_id,
                        page,
                        "index_referenced_page",
                        "gri_index_target_page",
                        INDEX_REASON,
                        relevance=0.8,
                    )
                )
            if include_nearby_pages:
                for nearby_page in (page - 1, page + 1):
                    if nearby_page < 1:
                        continue
                    for chunk in _chunks_by_report_page(report_index, nearby_page):
                        evidence.append(
                            _body_evidence_from_chunk(
                                chunk,
                                manifest_item_id,
                                nearby_page,
                                "index_referenced_nearby_page",
                                "gri_index_nearby_page",
                                INDEX_REASON,
                                relevance=0.55,
                            )
                        )
        output[manifest_item_id] = _dedupe_evidence(evidence)
    return output


def _score_page_text(text: str, keywords: List[str]) -> int:
    return sum(1 for keyword in keywords if keyword and keyword in text)


def build_fulltext_requirement_evidence(manifest_item_ids: List[str], top_n: int = 8) -> Dict[str, List[Dict[str, Any]]]:
    """Return requirement-level full-text evidence candidates from deterministic keyword search."""
    report_index = _load_report_index()
    output: Dict[str, List[Dict[str, Any]]] = {}

    for manifest_item_id in manifest_item_ids:
        keywords = P0_REQUIREMENT_KEYWORDS.get(manifest_item_id, [])
        page_scores: Dict[int, int] = {}
        for chunk in report_index.get("chunks", []):
            report_page = _report_page_label_for_pdf_page(int(chunk.get("pdf_page", 1)))
            score = _score_page_text(chunk.get("text", ""), keywords)
            if score > 0:
                page_scores[report_page] = page_scores.get(report_page, 0) + score

        ranked_pages = [
            page for page, _ in sorted(page_scores.items(), key=lambda row: (-row[1], row[0]))[:top_n]
        ]
        evidence: List[Dict[str, Any]] = []
        for page in ranked_pages:
            for chunk in _chunks_by_report_page(report_index, page):
                evidence.append(
                    _body_evidence_from_chunk(
                        chunk,
                        manifest_item_id,
                        page,
                        "fulltext_requirement_candidate",
                        "fulltext_keyword_requirement_candidate",
                        FULLTEXT_REASON,
                        relevance=0.65,
                    )
                )
        output[manifest_item_id] = _dedupe_evidence(evidence)
    return output

