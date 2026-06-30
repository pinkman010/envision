"""Build Stage E3 traceability cleanup mapping and waiver artifacts.

The script audits the accepted E3 effective assessments and emits cleanup
maps. It intentionally does not mutate raw LLM artifacts or effective
assessment artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _write_json  # noqa: E402

DEFAULT_EFFECTIVE_ARTIFACTS = PROJECT_ROOT / "docs" / "stage_e3" / "e3_current_scope_effective_artifacts.json"
DEFAULT_REQUIREMENT_CHECKLIST = PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_gri_requirement_checklist.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e_traceability_cleanup"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _relative_or_absolute(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_effective_assessments(index_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    payload = _load_json(index_path)
    paths = [str(path) for path in payload.get("aggregate_effective_inputs", {}).get("effective_assessment_artifacts", [])]
    assessments: list[dict[str, Any]] = []
    for artifact in paths:
        source = _relative_or_absolute(artifact)
        artifact_payload = _load_json(source)
        for assessment in _as_list(artifact_payload.get("disclosure_assessments")):
            if isinstance(assessment, dict):
                copied = dict(assessment)
                copied["_source_artifact"] = artifact
                assessments.append(copied)
    return assessments, paths


def _load_checklist_ids(path: Path) -> tuple[set[str], set[str]]:
    payload = _load_json(path)
    requirement_ids: set[str] = set()
    parent_ids: set[str] = set()
    for requirement in _as_list(payload.get("requirements")):
        if not isinstance(requirement, dict):
            continue
        requirement_id = str(requirement.get("requirement_id", ""))
        parent_id = str(requirement.get("parent_requirement_id", ""))
        if requirement_id:
            requirement_ids.add(requirement_id)
        if parent_id:
            parent_ids.add(parent_id)
    return requirement_ids, parent_ids


def _dot_to_colon_requirement_id(value: str) -> str:
    # Normalize only the sub-requirement suffix after the canonical disclosure id.
    match = re.match(r"^(current_gap:GRI\d+:\d+-\d+:)(.+)$", value)
    if not match:
        return value
    return match.group(1) + match.group(2).replace(".", ":")


def _requirement_references(assessment: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for check in _as_list(assessment.get("requirement_checks")):
        if isinstance(check, dict) and check.get("requirement_id"):
            refs.append({"source": "requirement_checks[].requirement_id", "requirement_id": str(check["requirement_id"])})
    for field in ("missing_requirements", "partial_requirements", "not_applicable_requirements", "manual_review_requirements"):
        for requirement_id in _as_list(assessment.get(field)):
            refs.append({"source": field, "requirement_id": str(requirement_id)})
    for evidence in _as_list(assessment.get("evidence")):
        if not isinstance(evidence, dict):
            continue
        for requirement_id in _as_list(evidence.get("supports_requirement_ids")):
            refs.append({"source": "evidence[].supports_requirement_ids", "requirement_id": str(requirement_id)})
    return refs


def _build_requirement_cleanup_map(
    assessments: list[dict[str, Any]],
    checklist_ids: set[str],
    parent_ids: set[str],
) -> dict[str, Any]:
    invalid: list[dict[str, Any]] = []
    counter: Counter[str] = Counter()
    for assessment in assessments:
        for ref in _requirement_references(assessment):
            requirement_id = ref["requirement_id"]
            if requirement_id in checklist_ids:
                continue
            counter[requirement_id] += 1
            normalized = _dot_to_colon_requirement_id(requirement_id)
            if normalized in checklist_ids:
                action = "normalize_dot_suffix_to_colon_suffix"
                replacement = normalized
                waiver_required = False
            elif requirement_id in parent_ids:
                action = "remove_parent_disclosure_id_from_requirement_reference_or_replace_with_leaf_requirements"
                replacement = None
                waiver_required = False
            else:
                action = "manual_requirement_mapping_review_required"
                replacement = None
                waiver_required = True
            invalid.append(
                {
                    "source_artifact": assessment.get("_source_artifact"),
                    "manifest_item_id": assessment.get("manifest_item_id"),
                    "assessment_id": assessment.get("assessment_id"),
                    "reference_source": ref["source"],
                    "requirement_id": requirement_id,
                    "suggested_action": action,
                    "suggested_replacement_requirement_id": replacement,
                    "waiver_required": waiver_required,
                }
            )
    return {
        "document_version": "p0_stage_e3_requirement_id_cleanup_map_v1",
        "recorded_at": _now_iso(),
        "status": "cleanup_map_generated_no_effective_artifact_mutation",
        "invalid_reference_occurrence_count": len(invalid),
        "invalid_reference_unique_count": len(counter),
        "invalid_reference_top_counts": [
            {"requirement_id": requirement_id, "occurrences": count}
            for requirement_id, count in counter.most_common()
        ],
        "cleanup_entries": invalid,
    }


def _build_evidence_binding_cleanup_map(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    entries: list[dict[str, Any]] = []
    for assessment in assessments:
        evidence_by_id = {
            str(evidence.get("evidence_id")): evidence
            for evidence in _as_list(assessment.get("evidence"))
            if isinstance(evidence, dict) and evidence.get("evidence_id")
        }
        evidence_by_chunk = {
            str(evidence.get("chunk_id")): evidence
            for evidence in _as_list(assessment.get("evidence"))
            if isinstance(evidence, dict) and evidence.get("chunk_id")
        }
        for check in _as_list(assessment.get("requirement_checks")):
            if not isinstance(check, dict):
                continue
            for binding in _as_list(check.get("supporting_evidence_ids")):
                binding_id = str(binding)
                if binding_id in evidence_by_id:
                    binding_type = "evidence_id"
                    replacement = binding_id
                    action = "keep"
                elif binding_id in evidence_by_chunk:
                    binding_type = "chunk_id"
                    replacement = str(evidence_by_chunk[binding_id].get("evidence_id"))
                    action = "replace_chunk_id_with_evidence_id"
                else:
                    binding_type = "unknown"
                    replacement = None
                    action = "manual_binding_review_required"
                counts[binding_type] += 1
                if action != "keep":
                    entries.append(
                        {
                            "source_artifact": assessment.get("_source_artifact"),
                            "manifest_item_id": assessment.get("manifest_item_id"),
                            "assessment_id": assessment.get("assessment_id"),
                            "requirement_id": check.get("requirement_id"),
                            "supporting_evidence_id": binding_id,
                            "observed_binding_type": binding_type,
                            "suggested_action": action,
                            "suggested_replacement_evidence_id": replacement,
                        }
                    )
    return {
        "document_version": "p0_stage_e3_evidence_binding_cleanup_map_v1",
        "recorded_at": _now_iso(),
        "status": "cleanup_map_generated_no_effective_artifact_mutation",
        "recommended_final_rule": "supporting_evidence_ids should reference evidence[].evidence_id; chunk_id remains evidence metadata.",
        "binding_counts": dict(counts),
        "cleanup_entry_count": len(entries),
        "cleanup_entries": entries,
    }


def _build_pdf_source_text_waiver() -> dict[str, Any]:
    return {
        "document_version": "p0_stage_e3_pdf_source_text_location_waiver_v1",
        "recorded_at": _now_iso(),
        "status": "manual_waiver_package_generated_pending_human_acceptance",
        "baseline_from_e3_current_scope_acceptance_audit": {
            "substantive_report_evidence_snippets": 159,
            "pypdf2_matched": 28,
            "pypdf2_unmatched": 131,
        },
        "waiver_scope": (
            "The E3 validators already require source_page, report_page_label, source_text, evidence_kind, and chunk_id. "
            "PyPDF2 full-string matching is not treated as a hard blocker because PDF table layout and extraction order "
            "are known to differ from report visual text."
        ),
        "conditions": [
            "Do not claim all source_text snippets are machine-verified against PDF rendering.",
            "For final thesis statistics, report this as a traceability limitation or perform visual/manual spot validation.",
            "For future normalized artifacts, prefer short verbatim snippets extracted from page text or OCR-rendered text.",
        ],
    }


def build_traceability_cleanup_artifacts(
    *,
    effective_artifacts_path: Path = DEFAULT_EFFECTIVE_ARTIFACTS,
    requirement_checklist_path: Path = DEFAULT_REQUIREMENT_CHECKLIST,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    assessments, effective_paths = _load_effective_assessments(effective_artifacts_path)
    checklist_ids, parent_ids = _load_checklist_ids(requirement_checklist_path)
    if len(assessments) != 114:
        raise ValueError(f"Expected 114 effective E3 assessments, got {len(assessments)}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_traceability_cleanup")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    requirement_map = _build_requirement_cleanup_map(assessments, checklist_ids, parent_ids)
    evidence_map = _build_evidence_binding_cleanup_map(assessments)
    pdf_waiver = _build_pdf_source_text_waiver()

    result = {
        "document_version": "p0_stage_e3_traceability_cleanup_result_v1",
        "recorded_at": _now_iso(),
        "run_id": run_id,
        "status": "cleanup_maps_generated_pdf_location_waiver_pending_human_acceptance",
        "effective_artifacts_modified": False,
        "raw_artifacts_modified": False,
        "assessment_count": len(assessments),
        "effective_assessment_artifacts": effective_paths,
        "requirement_id_cleanup": {
            "invalid_reference_occurrence_count": requirement_map["invalid_reference_occurrence_count"],
            "invalid_reference_unique_count": requirement_map["invalid_reference_unique_count"],
            "map_file": "requirement_id_cleanup_map.json",
        },
        "supporting_evidence_id_binding_cleanup": {
            "binding_counts": evidence_map["binding_counts"],
            "cleanup_entry_count": evidence_map["cleanup_entry_count"],
            "map_file": "evidence_binding_cleanup_map.json",
        },
        "pdf_source_text_location": {
            "waiver_file": "pdf_source_text_location_waiver.json",
            "status": pdf_waiver["status"],
        },
        "final_advisor_readiness": {
            "ready_to_prepare_unified_input": True,
            "deepseek_call_authorization_required": True,
            "basis": "Unified final advisor is based on the 114 accepted effective assessments, not on stale batch-level advisor outputs.",
        },
        "limitations": [
            "This cleanup package records mappings and waiver conditions; it does not rewrite the accepted effective artifacts.",
            "Final evaluation or thesis hard statistics should use a future normalized artifact or an explicit human acceptance of these cleanup maps and PDF waiver.",
        ],
    }
    run_summary = {
        "status": "ok",
        "run_id": run_id,
        "run_mode": "stage_e3_traceability_cleanup",
        "run_dir": str(run_dir),
        "assessment_count": len(assessments),
        "effective_artifacts_modified": False,
        "raw_artifacts_modified": False,
        "errors": [],
        "warnings": result["limitations"],
    }

    _write_json(run_dir / "traceability_cleanup_result.json", result)
    _write_json(run_dir / "requirement_id_cleanup_map.json", requirement_map)
    _write_json(run_dir / "evidence_binding_cleanup_map.json", evidence_map)
    _write_json(run_dir / "pdf_source_text_location_waiver.json", pdf_waiver)
    _write_json(run_dir / "run_summary.json", run_summary)

    printable = {
        "status": "ok",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "assessment_count": len(assessments),
        "invalid_requirement_reference_unique_count": requirement_map["invalid_reference_unique_count"],
        "evidence_binding_cleanup_entry_count": evidence_map["cleanup_entry_count"],
        "pdf_waiver_status": pdf_waiver["status"],
    }
    print(json.dumps(printable, ensure_ascii=False, indent=2))
    return printable


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build E3 traceability cleanup artifacts.")
    parser.add_argument("--effective-artifacts", type=Path, default=DEFAULT_EFFECTIVE_ARTIFACTS)
    parser.add_argument("--requirement-checklist", type=Path, default=DEFAULT_REQUIREMENT_CHECKLIST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    build_traceability_cleanup_artifacts(
        effective_artifacts_path=args.effective_artifacts,
        requirement_checklist_path=args.requirement_checklist,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
