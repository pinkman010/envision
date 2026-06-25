"""Validate Stage C P0 evidence layer manifests."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.paths import (
    ENVISION_2024_ZH_REPORT_PATH,
    GRI_REFERENCE_PDF_PATH,
    P0_GRI_DISCLOSURE_MANIFEST_PATH,
    P0_GRI_REQUIREMENT_PACK_PATH,
    P0_REPORT_EVIDENCE_INDEX_PATH,
    P0_SOURCE_MANIFEST_PATH,
)
from src.models import GRIRequirement, GRIRequirementPack, ReportEvidenceIndex, RequirementLocatorStatus
from src.utils.manifest_utils import EXPECTED_P0_COUNTS, load_p0_source_manifest
from src.utils.pdf_text_utils import sha256_file


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_by_type(source_manifest: Dict[str, Any], document_type: str) -> Dict[str, Any]:
    matches = [item for item in source_manifest.get("sources", []) if item.get("document_type") == document_type]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {document_type} source, got {len(matches)}")
    return matches[0]


def _strict_typo_mapping_matches(
    requirements: List[GRIRequirement],
    *,
    standard_id: str,
    source_disclosure_id: str,
    canonical_disclosure_id: str,
    report_index_pdf_page: int,
    report_index_report_page: int,
) -> bool:
    matches = [req for req in requirements if req.canonical_disclosure_id == canonical_disclosure_id]
    if len(matches) != 1:
        return False
    req = matches[0]
    return (
        req.standard_id == standard_id
        and req.source_disclosure_id == source_disclosure_id
        and req.canonical_status.value == "source_typo_confirmed"
        and req.report_index_pdf_page == report_index_pdf_page
        and req.report_index_report_page == report_index_report_page
    )


def _known_source_issue_exists(
    disclosure_manifest: Dict[str, Any],
    *,
    source_disclosure_id: str,
    canonical_disclosure_id: str,
) -> bool:
    return any(
        issue.get("source_disclosure_id") == source_disclosure_id
        and issue.get("canonical_disclosure_id") == canonical_disclosure_id
        and issue.get("status") == "source_typo_confirmed"
        for issue in disclosure_manifest.get("known_source_issues", [])
    )


def _append_hash_errors(
    errors: List[str],
    *,
    pack: Optional[GRIRequirementPack],
    index: Optional[ReportEvidenceIndex],
) -> None:
    try:
        source_manifest = load_p0_source_manifest()
        report_source = _source_by_type(source_manifest, "esg_report")
        gri_source = _source_by_type(source_manifest, "gri_standards_consolidated_set")
    except Exception as exc:
        errors.append(f"Could not load source manifest for hash validation: {exc}")
        return

    actual_source_manifest_sha = sha256_file(P0_SOURCE_MANIFEST_PATH)
    actual_disclosure_manifest_sha = sha256_file(P0_GRI_DISCLOSURE_MANIFEST_PATH)
    actual_report_pdf_sha = sha256_file(ENVISION_2024_ZH_REPORT_PATH)
    actual_gri_pdf_sha = sha256_file(GRI_REFERENCE_PDF_PATH)
    recorded_report_pdf_sha = str(report_source.get("sha256", "")).upper()
    recorded_gri_pdf_sha = str(gri_source.get("sha256", "")).upper()

    if recorded_report_pdf_sha != actual_report_pdf_sha:
        errors.append("p0_source_manifest report SHA-256 does not match actual Envision report PDF")
    if recorded_gri_pdf_sha != actual_gri_pdf_sha:
        errors.append("p0_source_manifest GRI SHA-256 does not match actual GRI PDF")

    metadata_items = []
    if pack:
        metadata_items.append(("requirement pack", pack.metadata))
    if index:
        metadata_items.append(("report evidence index", index.metadata))
    for label, metadata in metadata_items:
        if metadata.source_manifest_sha256 != actual_source_manifest_sha:
            errors.append(f"{label} source_manifest_sha256 does not match actual p0_source_manifest.json")
        if metadata.disclosure_manifest_sha256 != actual_disclosure_manifest_sha:
            errors.append(f"{label} disclosure_manifest_sha256 does not match actual p0_gri_disclosure_manifest.json")
        if metadata.report_pdf_sha256 != actual_report_pdf_sha:
            errors.append(f"{label} report_pdf_sha256 does not match actual Envision report PDF")
        if metadata.gri_pdf_sha256 != actual_gri_pdf_sha:
            errors.append(f"{label} gri_pdf_sha256 does not match actual GRI PDF")
        if metadata.report_pdf_sha256 != recorded_report_pdf_sha:
            errors.append(f"{label} report_pdf_sha256 does not match p0_source_manifest recorded report SHA-256")
        if metadata.gri_pdf_sha256 != recorded_gri_pdf_sha:
            errors.append(f"{label} gri_pdf_sha256 does not match p0_source_manifest recorded GRI SHA-256")

    if index:
        bad_chunk_hashes = [
            chunk.chunk_id
            for chunk in index.chunks
            if chunk.source_document_sha256 != actual_report_pdf_sha
        ]
        if bad_chunk_hashes:
            errors.append(f"report chunks with non-actual report source hash: {bad_chunk_hashes[:5]}")
    if pack:
        bad_requirement_hashes = [
            req.manifest_item_id
            for req in pack.requirements
            if req.source_document_sha256 != actual_gri_pdf_sha
        ]
        if bad_requirement_hashes:
            errors.append(f"requirements with non-actual GRI source hash: {bad_requirement_hashes[:5]}")


def validate_p0_evidence_layer() -> Dict[str, Any]:
    errors: List[str] = []
    pack = None
    index = None
    disclosure_manifest: Dict[str, Any] = {}

    try:
        disclosure_manifest = _load_json(P0_GRI_DISCLOSURE_MANIFEST_PATH)
    except Exception as exc:
        errors.append(f"Could not load disclosure manifest: {exc}")

    if not P0_GRI_REQUIREMENT_PACK_PATH.exists():
        errors.append(f"Missing requirement pack: {P0_GRI_REQUIREMENT_PACK_PATH}")
    else:
        try:
            pack = GRIRequirementPack.model_validate(_load_json(P0_GRI_REQUIREMENT_PACK_PATH))
        except Exception as exc:
            errors.append(f"Requirement pack failed model validation: {exc}")

    if not P0_REPORT_EVIDENCE_INDEX_PATH.exists():
        errors.append(f"Missing report evidence index: {P0_REPORT_EVIDENCE_INDEX_PATH}")
    else:
        try:
            index = ReportEvidenceIndex.model_validate(_load_json(P0_REPORT_EVIDENCE_INDEX_PATH))
        except Exception as exc:
            errors.append(f"Report evidence index failed model validation: {exc}")

    requirements = pack.requirements if pack else []
    chunks = index.chunks if index else []
    mode_counts = Counter(req.analysis_mode.value for req in requirements)
    locator_counts = Counter(req.requirement_locator_status.value for req in requirements)

    if len(requirements) != 118:
        errors.append(f"requirements expected 118, got {len(requirements)}")
    for mode, expected in EXPECTED_P0_COUNTS.items():
        actual = mode_counts.get(mode, 0)
        if actual != expected:
            errors.append(f"{mode} expected {expected}, got {actual}")

    manifest_item_ids = [req.manifest_item_id for req in requirements]
    duplicate_ids = sorted(item_id for item_id, count in Counter(manifest_item_ids).items() if count > 1)
    if duplicate_ids:
        errors.append(f"Duplicate manifest_item_id values: {duplicate_ids}")

    if not _strict_typo_mapping_matches(
        requirements,
        standard_id="GRI 405",
        source_disclosure_id="405-1",
        canonical_disclosure_id="405-2",
        report_index_pdf_page=75,
        report_index_report_page=74,
    ) or not _known_source_issue_exists(
        disclosure_manifest,
        source_disclosure_id="405-1",
        canonical_disclosure_id="405-2",
    ):
        errors.append("405-2 strict source typo mapping is missing or changed")
    if not _strict_typo_mapping_matches(
        requirements,
        standard_id="GRI 414",
        source_disclosure_id="414-1",
        canonical_disclosure_id="414-2",
        report_index_pdf_page=76,
        report_index_report_page=75,
    ) or not _known_source_issue_exists(
        disclosure_manifest,
        source_disclosure_id="414-1",
        canonical_disclosure_id="414-2",
    ):
        errors.append("414-2 strict source typo mapping is missing or changed")

    if len(chunks) <= 0:
        errors.append("report evidence chunks must be greater than 0")
    for chunk in chunks:
        if not chunk.chunk_id:
            errors.append("chunk_id must not be empty")
            break
        if chunk.pdf_page < 1:
            errors.append(f"chunk {chunk.chunk_id} has invalid pdf_page")
            break
        if not chunk.source_document_sha256:
            errors.append(f"chunk {chunk.chunk_id} has empty source_document_sha256")
            break
        if not chunk.text.strip():
            errors.append(f"chunk {chunk.chunk_id} has empty text")
            break

    _append_hash_errors(errors, pack=pack, index=index)

    if pack:
        review_required_statuses = {
            RequirementLocatorStatus.NOT_FOUND,
            RequirementLocatorStatus.MULTIPLE_CANDIDATES,
        }
        review_required_ids = [
            req.manifest_item_id
            for req in requirements
            if req.requirement_locator_status in review_required_statuses
        ]
        review_set = set(pack.locator_review_required)
        missing_review_ids = sorted(set(review_required_ids) - review_set)
        if missing_review_ids:
            errors.append(f"manual-review locators missing from locator_review_required: {missing_review_ids}")
        hidden_review_ids = sorted(
            req.manifest_item_id
            for req in requirements
            if req.requirement_locator_status in review_required_statuses and not req.locator_review_required
        )
        if hidden_review_ids:
            errors.append(f"manual-review locators without row-level review flag: {hidden_review_ids}")

    return {
        "status": "ok" if not errors else "failed",
        "requirements": len(requirements),
        "report_chunks": len(chunks),
        "mode_counts": {mode: mode_counts.get(mode, 0) for mode in EXPECTED_P0_COUNTS},
        "locator_counts": {
            status.value: locator_counts.get(status.value, 0)
            for status in RequirementLocatorStatus
        },
        "locator_review_required": pack.locator_review_required if pack else [],
        "locator_review_required_count": len(pack.locator_review_required) if pack else 0,
        "errors": errors,
    }


def main() -> int:
    result = validate_p0_evidence_layer()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
