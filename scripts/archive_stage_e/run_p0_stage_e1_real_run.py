"""Stage E1 controlled real LLM run entrypoint.

This script is intentionally guarded by --confirm-llm. Without that flag it
exits before creating a run directory or calling any Agent/LLM.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").exists())
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agent.advisor_agent import AdvisorAgent
from src.agent.analyst_agent import AnalystAgent
from src.config import settings
from src.models.analysis_contract import AnalysisRun, AnalysisRunStatus
from src.utils.manifest_utils import load_p0_gri_disclosure_manifest, load_p0_source_documents
from src.utils.p0_agent_context import build_p0_requirement_contexts

DEFAULT_SAMPLE_MANIFEST_PATH = (
    REPO_ROOT / "data" / "knowledge_base" / "manifests" / "p0_stage_e1_sample_manifest.json"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "runs" / "stage_e"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "", encoding="utf-8")


def _sample_ids(sample_manifest_path: Path) -> list[str]:
    payload = _load_json(sample_manifest_path)
    sample_ids = payload.get("sample_manifest_item_ids", [])
    if not isinstance(sample_ids, list) or not sample_ids:
        raise ValueError(f"sample_manifest_item_ids must be a non-empty list: {sample_manifest_path}")
    return [str(item) for item in sample_ids]


def _sample_contexts(sample_manifest_path: Path) -> list[dict[str, Any]]:
    wanted_ids = _sample_ids(sample_manifest_path)
    contexts = build_p0_requirement_contexts()
    by_id = {item["manifest_item_id"]: item for item in contexts}
    missing = [item_id for item_id in wanted_ids if item_id not in by_id]
    if missing:
        raise ValueError(f"sample manifest contains IDs missing from P0 contexts: {missing}")
    return [by_id[item_id] for item_id in wanted_ids]


def _input_text_from_contexts(contexts: list[dict[str, Any]]) -> str:
    sections: list[str] = []
    for context in contexts:
        manifest_item_id = context["manifest_item_id"]
        chunks = context.get("report_evidence_chunks", []) or []
        if not chunks:
            sections.append(
                f"[{manifest_item_id}]\n"
                f"No report evidence chunk is attached. Policy reason: {context.get('policy_reason', '')}"
            )
            continue
        for chunk in chunks:
            text = str(chunk.get("text", "")).strip()
            if not text:
                continue
            sections.append(
                "\n".join(
                    [
                        f"[{manifest_item_id}]",
                        f"chunk_id: {chunk.get('chunk_id')}",
                        f"pdf_page: {chunk.get('pdf_page')}",
                        f"report_year: {chunk.get('report_year')}",
                        "text:",
                        text,
                    ]
                )
            )
    return "\n\n---\n\n".join(sections)


def _build_retrieval_result(contexts: list[dict[str, Any]], sample_manifest_path: Path) -> dict[str, Any]:
    return {
        "p0_contract_version": "p0_stage_d_agent_contract_v1",
        "input_text": _input_text_from_contexts(contexts),
        "identified_topics": [],
        "retrieved_standards": [],
        "retrieved_peers": [],
        "coverage_summary": "Stage E1 controlled sample run; P0 contexts are pre-filtered by sample manifest.",
        "p0_requirement_contexts": contexts,
        "retrieval_summary": {
            "p0_requirement_count": len(contexts),
            "sampled": True,
            "sample_manifest_path": str(sample_manifest_path),
            "sample_manifest_item_ids": [item["manifest_item_id"] for item in contexts],
        },
    }


def _manual_review_input(analysis_run: AnalysisRun) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for assessment in analysis_run.assessments:
        first_evidence = assessment.evidence[0] if assessment.evidence else None
        rows.append(
            {
                "run_id": analysis_run.run_id,
                "assessment_id": assessment.assessment_id,
                "manifest_item_id": assessment.manifest_item_id,
                "standard_id": assessment.standard_id,
                "canonical_disclosure_id": assessment.canonical_disclosure_id,
                "assessment_mode": assessment.assessment_mode.value,
                "model_verdict": assessment.verdict.value,
                "human_verdict": "",
                "evidence_page": first_evidence.source_page if first_evidence else None,
                "evidence_text": first_evidence.source_text if first_evidence else "",
                "evidence_id": first_evidence.evidence_id if first_evidence else "",
                "evidence_kind": first_evidence.evidence_kind.value if first_evidence else "",
                "chunk_id": first_evidence.chunk_id if first_evidence else "",
                "source_document": first_evidence.source_document if first_evidence else "",
                "source_document_sha256": first_evidence.source_document_sha256 if first_evidence else "",
                "requirement_check_count": len(assessment.requirement_checks),
                "missing_requirements": list(assessment.missing_requirements),
                "manual_review_requirements": list(assessment.manual_review_requirements),
                "review_status": assessment.review_status.value,
                "error_type": "",
                "review_note": "",
            }
        )
    return {"items": rows}


def _analysis_run_from_result(run_id: str, analyst_result: dict[str, Any]) -> AnalysisRun:
    disclosure_manifest = load_p0_gri_disclosure_manifest()
    manifest_version = disclosure_manifest.get("manifest_version") or disclosure_manifest.get("metadata", {}).get("version", "p0")
    return AnalysisRun.model_validate(
        {
            "run_id": run_id,
            "report_id": "envision_energy_2024_zh",
            "standard_profile_id": "gri_p0_profile_2021_current_gap_with_readiness_watchlist",
            "manifest_version": str(manifest_version),
            "status": AnalysisRunStatus.COMPLETED.value,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "source_documents": [doc.model_dump(mode="json") for doc in load_p0_source_documents()],
            "assessments": analyst_result.get("disclosure_assessments", []),
            "summary": {
                **(analyst_result.get("summary", {}) or {}),
                "sample_count": len(analyst_result.get("disclosure_assessments", [])),
                "llm_called": True,
                "model": settings.LLM_MODEL,
                "base_url": settings.LLM_BASE_URL,
                "thinking_type": settings.LLM_THINKING_TYPE,
                "reasoning_effort": settings.LLM_REASONING_EFFORT,
                "response_format": settings.LLM_RESPONSE_FORMAT or None,
                "run_mode": "stage_e1_controlled_real_llm",
            },
        }
    )


def run_e1_real(sample_manifest_path: Path, output_dir: Path) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e1_sample")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    retrieval_result: dict[str, Any] | None = None
    analyst_result: dict[str, Any] | None = None
    advisor_result: dict[str, Any] | None = None

    try:
        contexts = _sample_contexts(sample_manifest_path)
        retrieval_result = _build_retrieval_result(contexts, sample_manifest_path)
        _write_json(run_dir / "retrieval_result.json", retrieval_result)

        analyst_result = AnalystAgent().run(
            {"retrieval_result": retrieval_result},
            task_id=f"{run_id}_analyst",
        )
        _write_json(run_dir / "analyst_result.json", analyst_result)
        _write_text(run_dir / "analyst_raw_llm_output.txt", str(analyst_result.get("raw_llm_output", "")))

        advisor_result = AdvisorAgent().run(
            {"analyst_result": analyst_result},
            task_id=f"{run_id}_advisor",
        )
        _write_json(run_dir / "advisor_result.json", advisor_result)
        _write_text(run_dir / "advisor_raw_llm_output.txt", str(advisor_result.get("raw_llm_output", "")))

        analysis_run = _analysis_run_from_result(run_id, analyst_result)
        analysis_run_path = run_dir / "analysis_run.json"
        _write_json(analysis_run_path, analysis_run.model_dump(mode="json"))
        AnalysisRun.model_validate_json(analysis_run_path.read_text(encoding="utf-8"))

        manual_review_path = run_dir / "manual_review_input.json"
        _write_json(manual_review_path, _manual_review_input(analysis_run))

        summary = {
            "status": "ok",
            "run_id": run_id,
            "run_mode": "stage_e1_controlled_real_llm",
            "sample_count": len(contexts),
            "assessment_count": len(analysis_run.assessments),
            "llm_called": True,
            "model": settings.LLM_MODEL,
            "base_url": settings.LLM_BASE_URL,
            "analysis_run_path": str(analysis_run_path),
            "manual_review_input_path": str(manual_review_path),
            "run_dir": str(run_dir),
            "errors": [],
            "warnings": [],
        }
        _write_json(run_dir / "run_summary.json", summary)
        return summary
    except Exception as exc:
        error_payload = {
            "failed_stage": (
                "retrieval"
                if retrieval_result is None
                else "analyst"
                if analyst_result is None
                else "advisor"
                if advisor_result is None
                else "analysis_run"
            ),
            "exception_type": type(exc).__name__,
            "message": str(exc),
        }
        _write_json(run_dir / "error.json", error_payload)
        summary = {
            "status": "failed",
            "run_id": run_id,
            "run_mode": "stage_e1_controlled_real_llm",
            "llm_called": retrieval_result is not None,
            "run_dir": str(run_dir),
            "errors": [error_payload],
            "warnings": [],
        }
        _write_json(run_dir / "run_summary.json", summary)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Stage E1 controlled real LLM sample analysis.")
    parser.add_argument("--sample-manifest", type=Path, default=DEFAULT_SAMPLE_MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--confirm-llm", action="store_true", help="Required to call the configured external LLM.")
    args = parser.parse_args()

    if not args.confirm_llm:
        print("E1 real LLM run requires --confirm-llm after model/cost/output policy confirmation.")
        return 2

    result = run_e1_real(args.sample_manifest, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
