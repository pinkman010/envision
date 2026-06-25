"""
P0 manifest 读取与契约校验工具。

该模块只读取 JSON 文件并转换为领域模型，不调用 LLM，不写数据库。
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from src.config.paths import (
    P0_GRI_DISCLOSURE_MANIFEST_PATH,
    P0_SOURCE_MANIFEST_PATH,
)
from src.models import (
    AnalysisMode,
    AnalysisRun,
    DisclosureManifestItem,
    SourceDocumentRef,
)

EXPECTED_P0_COUNTS = {
    AnalysisMode.CURRENT_GAP.value: 115,
    AnalysisMode.READINESS_2026.value: 1,
    AnalysisMode.WATCHLIST_2027.value: 2,
}

_SOURCE_DOCUMENT_REF_FIELDS = (
    "relative_path",
    "document_type",
    "sha256",
    "provenance_status",
)


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _to_source_document_ref(item: Dict[str, Any]) -> SourceDocumentRef:
    """将 manifest source 记录收敛为契约内允许的引用字段。"""
    missing_fields = [field for field in _SOURCE_DOCUMENT_REF_FIELDS if field not in item]
    if missing_fields:
        raise ValueError(f"Source document is missing required fields: {missing_fields}")
    return SourceDocumentRef(**{field: item[field] for field in _SOURCE_DOCUMENT_REF_FIELDS})


def _source_doc_key(document: SourceDocumentRef) -> Dict[str, str]:
    return document.model_dump(mode="json")


def load_p0_source_manifest(path: Path = P0_SOURCE_MANIFEST_PATH) -> Dict[str, Any]:
    """读取 P0 原始资料来源清单。"""
    return _load_json(path)


def load_p0_gri_disclosure_manifest(path: Path = P0_GRI_DISCLOSURE_MANIFEST_PATH) -> Dict[str, Any]:
    """读取 P0 GRI 披露项范围与契约清单。"""
    return _load_json(path)


def load_p0_source_documents(path: Path = P0_SOURCE_MANIFEST_PATH) -> List[SourceDocumentRef]:
    """读取来源清单中的 source documents。"""
    manifest = load_p0_source_manifest(path)
    return [_to_source_document_ref(item) for item in manifest.get("sources", [])]


def load_p0_embedded_source_documents(
    path: Path = P0_GRI_DISCLOSURE_MANIFEST_PATH,
) -> List[SourceDocumentRef]:
    """读取 disclosure manifest 内嵌的 source document 引用。"""
    manifest = load_p0_gri_disclosure_manifest(path)
    return [_to_source_document_ref(item) for item in manifest.get("source_documents", [])]


def load_p0_disclosure_items(
    analysis_mode: Optional[AnalysisMode] = None,
    path: Path = P0_GRI_DISCLOSURE_MANIFEST_PATH,
) -> List[DisclosureManifestItem]:
    """读取 disclosure manifest，并可按分析模式过滤。"""
    manifest = load_p0_gri_disclosure_manifest(path)
    items = [DisclosureManifestItem(**item) for item in manifest.get("disclosures", [])]
    if analysis_mode is None:
        return items
    return [item for item in items if item.analysis_mode == analysis_mode]


def count_disclosures_by_mode(items: Iterable[DisclosureManifestItem]) -> Dict[str, int]:
    """统计不同 analysis_mode 下的 disclosure 数量。"""
    counts = Counter(item.analysis_mode.value for item in items)
    return dict(sorted(counts.items()))


def _find_duplicate_values(values: Sequence[str]) -> List[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def _source_documents_match(
    source_documents: Sequence[SourceDocumentRef],
    embedded_source_documents: Sequence[SourceDocumentRef],
) -> bool:
    return [_source_doc_key(item) for item in source_documents] == [
        _source_doc_key(item) for item in embedded_source_documents
    ]


def _has_known_source_issue(
    known_source_issues: Sequence[Dict[str, Any]],
    *,
    source_disclosure_id: str,
    canonical_disclosure_id: str,
) -> bool:
    return any(
        issue.get("source_disclosure_id") == source_disclosure_id
        and issue.get("canonical_disclosure_id") == canonical_disclosure_id
        and issue.get("status") == "source_typo_confirmed"
        for issue in known_source_issues
    )


def _strict_source_typo_mapping_exists(
    items: Sequence[DisclosureManifestItem],
    *,
    standard_id: str,
    source_disclosure_id: str,
    canonical_disclosure_id: str,
    report_index_pdf_page: int,
    report_index_report_page: int,
) -> bool:
    matches = [
        item
        for item in items
        if item.canonical_disclosure_id == canonical_disclosure_id
    ]
    if len(matches) != 1:
        return False
    item = matches[0]
    return (
        item.standard_id == standard_id
        and item.source_disclosure_id == source_disclosure_id
        and item.canonical_status.value == "source_typo_confirmed"
        and item.report_index_pdf_page == report_index_pdf_page
        and item.report_index_report_page == report_index_report_page
    )


def validate_p0_manifest_contract(
    path: Path = P0_GRI_DISCLOSURE_MANIFEST_PATH,
    source_path: Path = P0_SOURCE_MANIFEST_PATH,
) -> Dict[str, Any]:
    """校验 P0 disclosure manifest 的关键契约。"""
    manifest = load_p0_gri_disclosure_manifest(path)
    items = [DisclosureManifestItem(**item) for item in manifest.get("disclosures", [])]
    counts = count_disclosures_by_mode(items)
    source_documents = load_p0_source_documents(source_path)
    embedded_source_documents = load_p0_embedded_source_documents(path)
    source_documents_match_manifest = _source_documents_match(
        source_documents,
        embedded_source_documents,
    )

    errors: List[str] = []
    for mode, expected_count in EXPECTED_P0_COUNTS.items():
        actual_count = counts.get(mode, 0)
        if actual_count != expected_count:
            errors.append(f"{mode} expected {expected_count}, got {actual_count}")

    if not source_documents_match_manifest:
        errors.append("Source documents in p0_source_manifest do not match embedded source_documents in disclosure manifest")

    manifest_item_ids = [item.manifest_item_id for item in items]
    duplicate_manifest_item_ids = _find_duplicate_values(manifest_item_ids)
    manifest_item_ids_unique = not duplicate_manifest_item_ids
    if duplicate_manifest_item_ids:
        errors.append(f"Duplicate manifest_item_id values: {duplicate_manifest_item_ids}")

    current_gap_items = [item for item in items if item.analysis_mode == AnalysisMode.CURRENT_GAP]
    missing_current_gap_canonical_ids = [
        item.manifest_item_id for item in current_gap_items if not item.canonical_disclosure_id
    ]
    if missing_current_gap_canonical_ids:
        errors.append(f"current_gap items missing canonical_disclosure_id: {missing_current_gap_canonical_ids}")

    current_gap_canonical_ids = [
        str(item.canonical_disclosure_id) for item in current_gap_items if item.canonical_disclosure_id
    ]
    duplicate_current_gap_canonical_ids = _find_duplicate_values(current_gap_canonical_ids)
    current_gap_canonical_ids_unique = not duplicate_current_gap_canonical_ids and not missing_current_gap_canonical_ids
    if duplicate_current_gap_canonical_ids:
        errors.append(f"Duplicate current_gap canonical_disclosure_id values: {duplicate_current_gap_canonical_ids}")

    known_source_issues = manifest.get("known_source_issues", [])

    has_405_2_typo = _strict_source_typo_mapping_exists(
        items,
        standard_id="GRI 405",
        source_disclosure_id="405-1",
        canonical_disclosure_id="405-2",
        report_index_pdf_page=75,
        report_index_report_page=74,
    ) and _has_known_source_issue(
        known_source_issues,
        source_disclosure_id="405-1",
        canonical_disclosure_id="405-2",
    )
    if not has_405_2_typo:
        errors.append("Missing or invalid strict source typo mapping for canonical disclosure 405-2")

    has_414_2_typo = _strict_source_typo_mapping_exists(
        items,
        standard_id="GRI 414",
        source_disclosure_id="414-1",
        canonical_disclosure_id="414-2",
        report_index_pdf_page=76,
        report_index_report_page=75,
    ) and _has_known_source_issue(
        known_source_issues,
        source_disclosure_id="414-1",
        canonical_disclosure_id="414-2",
    )
    if not has_414_2_typo:
        errors.append("Missing or invalid strict source typo mapping for canonical disclosure 414-2")

    has_3_3_scope_marker = any(
        item.canonical_disclosure_id == "3-3_generic"
        and item.canonical_status.value == "requires_topic_instantiation"
        for item in items
    )
    if not has_3_3_scope_marker:
        errors.append("Missing GRI 3-3 generic scope marker")

    return {
        "status": "ok" if not errors else "failed",
        "manifest_version": manifest.get("manifest_version"),
        "total_disclosures": len(items),
        "counts": counts,
        "current_gap": counts.get(AnalysisMode.CURRENT_GAP.value, 0),
        "readiness_2026": counts.get(AnalysisMode.READINESS_2026.value, 0),
        "watchlist_2027": counts.get(AnalysisMode.WATCHLIST_2027.value, 0),
        "source_documents_loaded": len(source_documents),
        "embedded_source_documents_loaded": len(embedded_source_documents),
        "source_documents_match_manifest": source_documents_match_manifest,
        "manifest_item_ids_unique": manifest_item_ids_unique,
        "current_gap_canonical_ids_unique": current_gap_canonical_ids_unique,
        "has_405_2_typo": has_405_2_typo,
        "has_414_2_typo": has_414_2_typo,
        "has_3_3_scope_marker": has_3_3_scope_marker,
        "errors": errors,
    }


def build_empty_p0_analysis_run(
    report_id: str = "envision_energy_2024_zh",
    standard_profile_id: str = "p0_gri_disclosure_manifest",
) -> AnalysisRun:
    """构造一个尚未执行 Agent 的空 AnalysisRun，用于契约验证和后续持久化入口。"""
    manifest = load_p0_gri_disclosure_manifest()
    source_documents = [_to_source_document_ref(item) for item in manifest.get("source_documents", [])]
    return AnalysisRun(
        report_id=report_id,
        standard_profile_id=standard_profile_id,
        manifest_version=str(manifest.get("manifest_version", "unknown")),
        source_documents=source_documents,
        summary={"contract_status": "initialized_from_manifest"},
    )