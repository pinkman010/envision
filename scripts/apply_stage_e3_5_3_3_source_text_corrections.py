"""Apply non-destructive source_text corrections to E3.5 GRI 3-3 LLM output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _manual_review_input, _write_json  # noqa: E402
from scripts.run_stage_e3_5_index_3_3_llm import _machine_smoke_review, _smoke_review_template, _validate_merged  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402

DEFAULT_RUN_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e3_5" / "20260630T085702Z_e3_5_gri3_3_llm_index_assessment"
DEFAULT_EVIDENCE_INDEX = PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_report_evidence_index.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _chunk_text_by_id(evidence_index_path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(evidence_index_path)
    return {
        str(chunk["chunk_id"]): chunk
        for chunk in payload.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }


def _has_ellipsis(value: str) -> bool:
    return "..." in value or "…" in value


def _correct_assessments(assessments: list[dict[str, Any]], chunks: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    corrected: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    for assessment in assessments:
        item = json.loads(json.dumps(assessment, ensure_ascii=False))
        for evidence in item.get("evidence", []) or []:
            if not isinstance(evidence, dict):
                continue
            chunk_id = str(evidence.get("chunk_id", ""))
            source_text = str(evidence.get("source_text", ""))
            if not chunk_id or not _has_ellipsis(source_text) or chunk_id not in chunks:
                continue
            chunk = chunks[chunk_id]
            evidence["source_text"] = str(chunk.get("text", "")).strip()
            evidence["source_page"] = chunk.get("pdf_page", evidence.get("source_page"))
            evidence["report_page_label"] = str(int(chunk.get("pdf_page")) - 1) if isinstance(chunk.get("pdf_page"), int) else evidence.get("report_page_label")
            evidence["source_document_sha256"] = chunk.get("source_document_sha256") or evidence.get("source_document_sha256")
            evidence["source_text_extraction_warning"] = "source_text_replaced_from_evidence_index_chunk"
            changes.append(
                {
                    "manifest_item_id": item.get("manifest_item_id"),
                    "evidence_id": evidence.get("evidence_id"),
                    "chunk_id": chunk_id,
                    "correction": "source_text_replaced_from_evidence_index_chunk",
                }
            )
        corrected.append(item)
    return corrected, changes


def apply_corrections(run_dir: Path = DEFAULT_RUN_DIR, evidence_index_path: Path = DEFAULT_EVIDENCE_INDEX) -> dict[str, Any]:
    analyst_path = run_dir / "analyst_result_merged.json"
    analysis_run_path = run_dir / "analysis_run_merged.json"
    if not analyst_path.exists() or not analysis_run_path.exists():
        raise FileNotFoundError(f"E3.5 merged artifacts not found in {run_dir}")

    analyst_result = _load_json(analyst_path)
    analysis_run = _load_json(analysis_run_path)
    chunks = _chunk_text_by_id(evidence_index_path)
    assessments, changes = _correct_assessments(analyst_result.get("disclosure_assessments", []), chunks)

    corrected_analyst = dict(analyst_result)
    corrected_analyst["disclosure_assessments"] = assessments
    corrected_analyst["source_text_correction_summary"] = {
        "correction_count": len(changes),
        "method": "replace_ellipsis_source_text_from_p0_report_evidence_index_by_chunk_id",
    }
    corrected_analysis_run = dict(analysis_run)
    corrected_analysis_run["assessments"] = assessments
    corrected_analysis_run.setdefault("summary", {})
    corrected_analysis_run["summary"]["source_text_correction_count"] = len(changes)
    corrected_analysis_run["summary"]["corrected_from"] = "analysis_run_merged.json"
    validated_run = AnalysisRun.model_validate(corrected_analysis_run)

    validation = _validate_merged(assessments)
    smoke_template = _load_json(run_dir / "smoke_review_template.json")
    corrected_machine_smoke = _machine_smoke_review(str(analysis_run.get("run_id", run_dir.name)), assessments, smoke_template)

    _write_json(run_dir / "analyst_result_merged_corrected.json", corrected_analyst)
    _write_json(run_dir / "analysis_run_merged_corrected.json", validated_run.model_dump(mode="json"))
    _write_json(run_dir / "manual_review_input_merged_corrected.json", _manual_review_input(validated_run))
    _write_json(run_dir / "source_text_correction_log.json", {"items": changes})
    _write_json(run_dir / "merged_validation_result_after_source_text_corrections.json", validation)
    _write_json(run_dir / "machine_smoke_review_result_corrected.json", corrected_machine_smoke)

    stage_gate_path = run_dir / "stage_gate_result.json"
    stage_gate = _load_json(stage_gate_path) if stage_gate_path.exists() else {}
    stage_gate.update(
        {
            "corrected_artifacts_generated": True,
            "corrected_artifacts": [
                str(run_dir / "analyst_result_merged_corrected.json"),
                str(run_dir / "analysis_run_merged_corrected.json"),
                str(run_dir / "manual_review_input_merged_corrected.json"),
            ],
            "validation_status_after_source_text_corrections": validation["status"],
            "machine_smoke_hard_issue_count_after_source_text_corrections": len(corrected_machine_smoke.get("hard_issues", [])),
            "gate_status": "pending_human_smoke_review_after_source_text_corrections",
            "final_effective_set_status": "draft_pending_human_smoke_review",
        }
    )
    _write_json(stage_gate_path, stage_gate)

    run_summary_path = run_dir / "run_summary.json"
    run_summary = _load_json(run_summary_path)
    run_summary.update(
        {
            "corrected_artifacts_generated": True,
            "source_text_correction_count": len(changes),
            "validation_status_after_source_text_corrections": validation["status"],
            "machine_smoke_hard_issue_count_after_source_text_corrections": len(corrected_machine_smoke.get("hard_issues", [])),
            "effective_3_3_assessment_candidate": str(run_dir / "analyst_result_merged_corrected.json"),
            "final_effective_set_status": "draft_pending_human_smoke_review",
        }
    )
    _write_json(run_summary_path, run_summary)

    result = {
        "status": "ok" if validation["status"] == "ok" else "needs_review",
        "run_dir": str(run_dir),
        "source_text_correction_count": len(changes),
        "validation_status_after_source_text_corrections": validation["status"],
        "machine_smoke_hard_issue_count_after_source_text_corrections": len(corrected_machine_smoke.get("hard_issues", [])),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Correct E3.5 GRI 3-3 source_text ellipsis artifacts.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    args = parser.parse_args(argv)
    apply_corrections(run_dir=args.run_dir, evidence_index_path=args.evidence_index)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
