"""Validate Stage E1 sample contexts and, later, Stage E1 run outputs.

The --sample-only mode is the E1 preflight gate: it reads the frozen P0
requirement contexts, filters the controlled E1 sample manifest, and verifies
that each sample has the structured fields needed before any real LLM call.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.models.analysis_contract import AnalysisRun, DisclosureAssessment
from src.utils.p0_agent_context import build_p0_requirement_contexts

DEFAULT_SAMPLE_MANIFEST_PATH = (
    REPO_ROOT / "data" / "knowledge_base" / "manifests" / "p0_stage_e1_sample_manifest.json"
)

CONTEXT_REQUIRED_FIELDS = {
    "manifest_item_id",
    "analysis_mode",
    "standard_id",
    "canonical_disclosure_id",
    "requirement_locator_status",
    "official_pdf_pages_for_agent",
    "official_pdf_page_candidates",
    "locator_review_required",
    "agent_manual_review_required",
    "can_score_current_gap",
    "forced_verdict",
    "report_index_pdf_page",
    "report_index_report_page",
    "report_evidence_chunks",
}

CHUNK_REQUIRED_FIELDS = {
    "chunk_id",
    "source_document_relative_path",
    "source_document_sha256",
    "company",
    "report_year",
    "industry",
    "topic",
    "pdf_page",
    "text",
}

MANUAL_REVIEW_REQUIRED_FIELDS = {
    "run_id",
    "assessment_id",
    "manifest_item_id",
    "standard_id",
    "canonical_disclosure_id",
    "assessment_mode",
    "model_verdict",
    "human_verdict",
    "evidence_page",
    "evidence_text",
    "error_type",
    "review_note",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_sample_ids(sample_manifest_path: Path) -> list[str]:
    payload = _load_json(sample_manifest_path)
    sample_ids = payload.get("sample_manifest_item_ids", [])
    if not isinstance(sample_ids, list) or not sample_ids:
        raise ValueError(f"sample_manifest_item_ids must be a non-empty list: {sample_manifest_path}")
    return [str(item) for item in sample_ids]


def _allowed_empty_evidence(context: dict[str, Any]) -> bool:
    if context.get("requirement_locator_status") == "requires_topic_instantiation":
        return True
    if context.get("analysis_mode") != "current_gap":
        return True
    if context.get("can_score_current_gap") is False:
        return True
    return False


def _validate_chunk(chunk: dict[str, Any], manifest_item_id: str, chunk_index: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(CHUNK_REQUIRED_FIELDS - set(chunk))
    if missing:
        errors.append(f"{manifest_item_id} chunk[{chunk_index}] missing fields: {missing}")
        return errors

    for field in ["chunk_id", "source_document_relative_path", "source_document_sha256", "company", "industry", "topic", "text"]:
        value = chunk.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{manifest_item_id} chunk[{chunk_index}] has empty {field}")

    if not isinstance(chunk.get("report_year"), int):
        errors.append(f"{manifest_item_id} chunk[{chunk_index}] report_year must be int")

    if not isinstance(chunk.get("pdf_page"), int):
        errors.append(f"{manifest_item_id} chunk[{chunk_index}] pdf_page must be int")

    return errors


def _validate_context(context: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    manifest_item_id = str(context.get("manifest_item_id", "<missing>"))

    missing = sorted(CONTEXT_REQUIRED_FIELDS - set(context))
    if missing:
        errors.append(f"{manifest_item_id} missing context fields: {missing}")
        return errors, warnings

    chunks = context.get("report_evidence_chunks")
    if not isinstance(chunks, list):
        errors.append(f"{manifest_item_id} report_evidence_chunks must be list")
        return errors, warnings

    if not chunks:
        if _allowed_empty_evidence(context):
            warnings.append(f"{manifest_item_id} has empty evidence chunks with allowed_empty_evidence=true")
        else:
            errors.append(f"{manifest_item_id} current-gap scorable item has no report_evidence_chunks")
        return errors, warnings

    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            errors.append(f"{manifest_item_id} chunk[{index}] must be object")
            continue
        errors.extend(_validate_chunk(chunk, manifest_item_id, index))

    return errors, warnings


def validate_sample_only(sample_manifest_path: Path) -> dict[str, Any]:
    sample_ids = _load_sample_ids(sample_manifest_path)
    contexts = build_p0_requirement_contexts()
    by_id = {item["manifest_item_id"]: item for item in contexts}

    errors: list[str] = []
    warnings: list[str] = []
    sample_contexts: list[dict[str, Any]] = []

    for sample_id in sample_ids:
        context = by_id.get(sample_id)
        if context is None:
            errors.append(f"missing sample context: {sample_id}")
            continue
        sample_contexts.append(context)
        context_errors, context_warnings = _validate_context(context)
        errors.extend(context_errors)
        warnings.extend(context_warnings)

    return {
        "status": "ok" if not errors else "failed",
        "mode": "sample_only",
        "sample_manifest_path": str(sample_manifest_path),
        "sample_count": len(sample_contexts),
        "sample_manifest_item_ids": sample_ids,
        "total_context_count": len(contexts),
        "errors": errors,
        "warnings": warnings,
    }


def _validate_run_dir(run_dir: Path, sample_manifest_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    required_files = [
        "retrieval_result.json",
        "analyst_result.json",
        "advisor_result.json",
        "analysis_run.json",
        "manual_review_input.json",
        "run_summary.json",
    ]
    for name in required_files:
        if not (run_dir / name).exists():
            errors.append(f"missing run output file: {name}")

    if errors:
        return {
            "status": "failed",
            "mode": "run_dir",
            "run_dir": str(run_dir),
            "errors": errors,
            "warnings": warnings,
        }

    sample_ids = set(_load_sample_ids(sample_manifest_path))

    retrieval_result = _load_json(run_dir / "retrieval_result.json")
    if retrieval_result.get("p0_contract_version") != "p0_stage_d_agent_contract_v1":
        errors.append("retrieval_result.p0_contract_version must be p0_stage_d_agent_contract_v1")
    retrieval_contexts = retrieval_result.get("p0_requirement_contexts", [])
    if not isinstance(retrieval_contexts, list) or not retrieval_contexts:
        errors.append("retrieval_result.p0_requirement_contexts must be non-empty list")
    else:
        by_id = {item.get("manifest_item_id"): item for item in retrieval_contexts if isinstance(item, dict)}
        for sample_id in sample_ids:
            if sample_id not in by_id:
                errors.append(f"retrieval_result missing sample context: {sample_id}")
            else:
                context_errors, context_warnings = _validate_context(by_id[sample_id])
                errors.extend(context_errors)
                warnings.extend(context_warnings)

    analyst_result = _load_json(run_dir / "analyst_result.json")
    if analyst_result.get("p0_contract_version") != "p0_stage_d_agent_contract_v1":
        errors.append("analyst_result.p0_contract_version must be p0_stage_d_agent_contract_v1")
    if analyst_result.get("status") != "completed":
        errors.append("analyst_result.status must be completed")
    assessments = analyst_result.get("disclosure_assessments", [])
    if not isinstance(assessments, list):
        errors.append("analyst_result.disclosure_assessments must be list")
    else:
        for index, assessment in enumerate(assessments):
            try:
                parsed = DisclosureAssessment.model_validate(assessment)
            except Exception as exc:  # noqa: BLE001 - validation script must report all failures
                errors.append(f"assessment[{index}] invalid: {type(exc).__name__}: {exc}")
                continue
            if parsed.manifest_item_id not in sample_ids:
                errors.append(f"assessment[{index}] manifest_item_id is not in E1 sample: {parsed.manifest_item_id}")

    advisor_result = _load_json(run_dir / "advisor_result.json")
    if advisor_result.get("p0_contract_version") != "p0_stage_e0_advisor_contract_v1":
        errors.append("advisor_result.p0_contract_version must be p0_stage_e0_advisor_contract_v1")
    if advisor_result.get("status") != "completed":
        errors.append("advisor_result.status must be completed")
    if not isinstance(advisor_result.get("p0_recommendations"), list):
        errors.append("advisor_result.p0_recommendations must be list")
    if "overall_recommendation" not in advisor_result:
        errors.append("advisor_result.overall_recommendation is missing")
    if "summary" not in advisor_result:
        errors.append("advisor_result.summary is missing")

    try:
        analysis_run = AnalysisRun.model_validate_json((run_dir / "analysis_run.json").read_text(encoding="utf-8"))
        if len(analysis_run.assessments) != len(assessments):
            errors.append("analysis_run.assessments count differs from analyst_result.disclosure_assessments")
        if not analysis_run.source_documents:
            errors.append("analysis_run.source_documents must be non-empty")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"analysis_run.json invalid: {type(exc).__name__}: {exc}")

    manual_review_input = _load_json(run_dir / "manual_review_input.json")
    manual_items = manual_review_input.get("items", [])
    if not isinstance(manual_items, list):
        errors.append("manual_review_input.items must be list")
    else:
        for index, item in enumerate(manual_items):
            if not isinstance(item, dict):
                errors.append(f"manual_review_input.items[{index}] must be object")
                continue
            missing = sorted(MANUAL_REVIEW_REQUIRED_FIELDS - set(item))
            if missing:
                errors.append(f"manual_review_input.items[{index}] missing fields: {missing}")

    return {
        "status": "ok" if not errors else "failed",
        "mode": "run_dir",
        "run_dir": str(run_dir),
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Stage E1 sample contexts or run outputs.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample-only", action="store_true", help="Validate the E1 sample contexts before real LLM calls.")
    mode.add_argument("--run-dir", type=Path, help="Validate a completed Stage E1 run output directory.")
    parser.add_argument("--sample-manifest", type=Path, default=DEFAULT_SAMPLE_MANIFEST_PATH)
    args = parser.parse_args()

    try:
        if args.sample_only:
            result = validate_sample_only(args.sample_manifest)
        else:
            result = _validate_run_dir(args.run_dir, args.sample_manifest)
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "failed",
            "mode": "sample_only" if args.sample_only else "run_dir",
            "errors": [f"{type(exc).__name__}: {exc}"],
            "warnings": [],
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
