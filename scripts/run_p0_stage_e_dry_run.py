"""Stage E dry-run entrypoint for P0 analysis outputs.

The default supported E0 path is --no-llm, which creates a stub AnalysisRun
without calling any external model. --use-llm is intentionally blocked until
Stage E model/cost/output policy is confirmed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.analysis_contract import AnalysisRun, AnalysisRunStatus, SourceDocumentRef
from src.utils.manifest_utils import load_p0_gri_disclosure_manifest, load_p0_source_manifest


def _source_documents() -> List[Dict[str, Any]]:
    source_manifest = load_p0_source_manifest()
    docs: List[Dict[str, Any]] = []
    for item in source_manifest.get("sources", []):
        docs.append(
            SourceDocumentRef.model_validate(
                {
                    "relative_path": item["relative_path"],
                    "document_type": item["document_type"],
                    "sha256": str(item["sha256"]).upper(),
                    "provenance_status": item["provenance_status"],
                }
            ).model_dump(mode="json")
        )
    return docs


def _stub_analysis_run() -> AnalysisRun:
    disclosure_manifest = load_p0_gri_disclosure_manifest()
    manifest_version = disclosure_manifest.get("manifest_version") or disclosure_manifest.get("metadata", {}).get("version", "p0")
    return AnalysisRun.model_validate(
        {
            "report_id": "envision_energy_2024_zh",
            "standard_profile_id": "gri_p0_profile_2021_current_gap_with_readiness_watchlist",
            "manifest_version": str(manifest_version),
            "status": AnalysisRunStatus.COMPLETED.value,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "source_documents": _source_documents(),
            "assessments": [
                {
                    "manifest_item_id": "current_gap:GRI2:2-1",
                    "standard_id": "GRI 2",
                    "canonical_disclosure_id": "2-1",
                    "assessment_mode": "current_gap",
                    "verdict": "manual_review",
                    "confidence": 0.5,
                    "evidence": [],
                    "rationale": "Stage E no-LLM dry-run stub; not a real ESG disclosure conclusion.",
                    "recommendation": "",
                    "review_status": "pending",
                }
            ],
            "summary": {
                "dry_run": True,
                "llm_called": False,
                "manual_review_count": 1,
            },
        }
    )


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_no_llm(output_dir: Path) -> Dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_stub")
    run_dir = output_dir / run_id
    analysis_run = _stub_analysis_run()
    analysis_run_path = run_dir / "analysis_run.json"
    run_summary_path = run_dir / "run_summary.json"
    manual_review_input_path = run_dir / "manual_review_input.json"

    _write_json(analysis_run_path, analysis_run.model_dump(mode="json"))
    AnalysisRun.model_validate_json(analysis_run_path.read_text(encoding="utf-8"))

    manual_review_rows = [
        {
            "run_id": analysis_run.run_id,
            "assessment_id": assessment.assessment_id,
            "manifest_item_id": assessment.manifest_item_id,
            "standard_id": assessment.standard_id,
            "canonical_disclosure_id": assessment.canonical_disclosure_id,
            "assessment_mode": assessment.assessment_mode.value,
            "model_verdict": assessment.verdict.value,
            "human_verdict": "",
            "evidence_page": None,
            "evidence_text": "",
            "error_type": "",
            "review_note": "",
        }
        for assessment in analysis_run.assessments
    ]
    _write_json(manual_review_input_path, {"items": manual_review_rows})

    summary = {
        "status": "ok",
        "mode": "no_llm",
        "llm_called": False,
        "analysis_run_path": str(analysis_run_path),
        "run_summary_path": str(run_summary_path),
        "manual_review_input_path": str(manual_review_input_path),
        "assessment_count": len(analysis_run.assessments),
    }
    _write_json(run_summary_path, summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Stage E P0 dry-run.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--no-llm", action="store_true", help="Run a stub dry-run without calling any external LLM.")
    mode.add_argument("--use-llm", action="store_true", help="Reserved for Stage E real execution; currently blocked.")
    parser.add_argument("--output-dir", default="data/runs/stage_e", help="Directory for dry-run outputs.")
    args = parser.parse_args()

    if args.use_llm:
        print("--use-llm is reserved for Stage E execution. Confirm model/cost/output policy before enabling.")
        return 2

    result = run_no_llm(Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
