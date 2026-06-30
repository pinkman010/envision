"""Apply field-only evidence corrections for Stage E3 batch 05.

The script preserves raw LLM artifacts and writes corrected artifacts next to
them. It only replaces non-verbatim body evidence excerpts with the exact
chunk text from p0_report_evidence_index.json.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _manual_review_input, _write_json  # noqa: E402
from scripts.validate_stage_e3_batch_outputs import validate_run_dir  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402

DEFAULT_RUN_DIR = (
    PROJECT_ROOT
    / "data"
    / "runs"
    / "stage_e"
    / "20260630T070123Z_e3_batch_05_governance_supply_chain_economic"
)
DEFAULT_EVIDENCE_INDEX = PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_report_evidence_index.json"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _chunk_index(path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(path)
    chunks = payload.get("chunks", [])
    if not isinstance(chunks, list):
        raise ValueError(f"chunks must be a list: {path}")
    return {
        str(chunk.get("chunk_id")): chunk
        for chunk in chunks
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }


def _iter_assessments(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    assessments = payload.get(key)
    if not isinstance(assessments, list):
        raise ValueError(f"{key} must be a list")
    return [item for item in assessments if isinstance(item, dict)]


def _apply_chunk_text(evidence: dict[str, Any], chunk: dict[str, Any]) -> None:
    pdf_page = chunk.get("pdf_page")
    evidence["source_text"] = str(chunk.get("text", ""))
    evidence["source_document"] = chunk.get("source_document_relative_path", evidence.get("source_document"))
    evidence["source_document_sha256"] = chunk.get("source_document_sha256", evidence.get("source_document_sha256"))
    evidence["company"] = chunk.get("company", evidence.get("company"))
    evidence["report_year"] = chunk.get("report_year", evidence.get("report_year"))
    evidence["industry"] = chunk.get("industry", evidence.get("industry"))
    evidence["topic"] = chunk.get("topic", evidence.get("topic"))
    if isinstance(pdf_page, int):
        evidence["source_page"] = pdf_page
        evidence["report_page_label"] = str(pdf_page - 1)
    evidence["extraction_method"] = "p0_report_evidence_index_field_correction"
    evidence["retrieval_method"] = "field_correction_from_evidence_index"
    evidence["source_text_extraction_warning"] = None


def _fix_payload(payload: dict[str, Any], key: str, chunks: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    corrected = copy.deepcopy(payload)
    fixes: list[dict[str, Any]] = []
    for assessment in _iter_assessments(corrected, key):
        manifest_item_id = str(assessment.get("manifest_item_id", ""))
        for evidence in assessment.get("evidence", []) or []:
            if not isinstance(evidence, dict):
                continue
            source_text = str(evidence.get("source_text", ""))
            if "..." not in source_text and "\u2026" not in source_text:
                continue
            chunk_id = str(evidence.get("chunk_id", ""))
            chunk = chunks.get(chunk_id)
            if not chunk:
                raise ValueError(f"missing chunk for {manifest_item_id}: {chunk_id}")
            before = {
                "source_page": evidence.get("source_page"),
                "report_page_label": evidence.get("report_page_label"),
                "source_text": source_text,
            }
            _apply_chunk_text(evidence, chunk)
            fixes.append(
                {
                    "manifest_item_id": manifest_item_id,
                    "evidence_id": evidence.get("evidence_id"),
                    "chunk_id": chunk_id,
                    "before": before,
                    "after": {
                        "source_page": evidence.get("source_page"),
                        "report_page_label": evidence.get("report_page_label"),
                        "source_text_length": len(str(evidence.get("source_text", ""))),
                    },
                }
            )
    if key == "assessments":
        summary = corrected.setdefault("summary", {})
        if isinstance(summary, dict):
            summary["field_corrections_applied"] = True
            summary["field_correction_type"] = "source_text_verbatim_from_evidence_index"
    return corrected, fixes


def apply_corrections(run_dir: Path, evidence_index: Path) -> dict[str, Any]:
    chunks = _chunk_index(evidence_index)
    analyst_result = _load_json(run_dir / "analyst_result.json")
    analysis_run = _load_json(run_dir / "analysis_run.json")
    run_summary = _load_json(run_dir / "run_summary.json")
    run_id = str(run_summary["run_id"])
    batch_id = str(run_summary["batch_id"])

    corrected_analyst, analyst_fixes = _fix_payload(analyst_result, "disclosure_assessments", chunks)
    corrected_analysis, analysis_fixes = _fix_payload(analysis_run, "assessments", chunks)
    analysis_model = AnalysisRun.model_validate(corrected_analysis)

    analyst_path = run_dir / "analyst_result_corrected.json"
    analysis_path = run_dir / "analysis_run_corrected.json"
    manual_review_path = run_dir / "manual_review_input_corrected.json"
    validation_path = run_dir / "batch_validation_result_corrected.json"
    gate_path = run_dir / "stage_gate_result.json"

    _write_json(analyst_path, corrected_analyst)
    _write_json(analysis_path, corrected_analysis)
    _write_json(manual_review_path, _manual_review_input(analysis_model))

    validation = validate_run_dir(run_dir)
    _write_json(validation_path, validation)

    corrected_artifacts = [str(analyst_path), str(analysis_path), str(manual_review_path)]
    run_summary["validation_status_after_field_correction"] = validation["status"]
    run_summary["validation_errors_after_field_correction"] = validation.get("errors", [])
    run_summary["corrected_artifacts"] = corrected_artifacts
    _write_json(run_dir / "run_summary.json", run_summary)

    gate_result = {
        "run_id": run_id,
        "batch_id": batch_id,
        "review_status": "pending_smoke_review",
        "gate_status": "pending_smoke_review_before_e3_current_scope_acceptance",
        "raw_validation_status": run_summary.get("validation_status"),
        "raw_validation_error_count": run_summary.get("validation_error_count"),
        "field_corrections_applied": True,
        "field_correction_reasons": ["source_text_not_verbatim"],
        "field_correction_count": len(analyst_fixes),
        "validation_status_after_field_correction": validation["status"],
        "validation_errors_after_field_correction": validation.get("errors", []),
        "corrected_artifacts": corrected_artifacts,
        "batch_validation_result_corrected": str(validation_path),
        "next_required_action": "complete_human_smoke_review_before_e3_current_scope_acceptance",
        "notes": [
            "Raw LLM artifacts are preserved.",
            "Corrections only replace ellipsis summaries with p0_report_evidence_index chunk text.",
            "Smoke review must still validate verdicts, requirement binding, page traceability and over-manual-review risk.",
        ],
    }
    _write_json(gate_path, gate_result)

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "analyst_fix_count": len(analyst_fixes),
        "analysis_fix_count": len(analysis_fixes),
        "validation_status_after_field_correction": validation["status"],
        "validation_error_count_after_field_correction": len(validation.get("errors", [])),
        "corrected_artifacts": corrected_artifacts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply Stage E3 batch 05 field-only corrections.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    args = parser.parse_args(argv)

    result = apply_corrections(args.run_dir, args.evidence_index)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
