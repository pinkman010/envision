"""Build the 143-item Stage E3 final current assessment set draft."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").exists())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.archive_stage_e.run_p0_stage_e1_real_run import _write_json  # noqa: E402
from src.models.analysis_contract import AnalysisRun, AnalysisRunStatus, DisclosureAssessment  # noqa: E402
from src.utils.manifest_utils import load_p0_source_documents  # noqa: E402

DEFAULT_ORDINARY_INDEX = PROJECT_ROOT / "docs" / "stage_e3" / "e3_current_scope_effective_artifacts.json"
DEFAULT_E3_5_RUN_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e3_5" / "20260630T085702Z_e3_5_gri3_3_llm_index_assessment"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e_final_assessment_set"
DEFAULT_DOC_OUTPUT = PROJECT_ROOT / "docs" / "stage_e3" / "e3_final_current_effective_assessment_set_draft.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _relative_or_absolute(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_ordinary_assessments(index_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    index = _load_json(index_path)
    paths = [str(path) for path in index.get("aggregate_effective_inputs", {}).get("effective_assessment_artifacts", [])]
    assessments: list[dict[str, Any]] = []
    for artifact in paths:
        payload = _load_json(_relative_or_absolute(artifact))
        assessments.extend([item for item in payload.get("disclosure_assessments", []) if isinstance(item, dict)])
    return assessments, paths


def _load_e3_5_assessments(run_dir: Path) -> tuple[list[dict[str, Any]], str]:
    reviewed = run_dir / "analyst_result_merged_reviewed.json"
    corrected = run_dir / "analyst_result_merged_corrected.json"
    raw = run_dir / "analyst_result_merged.json"
    path = reviewed if reviewed.exists() else corrected if corrected.exists() else raw
    payload = _load_json(path)
    return [item for item in payload.get("disclosure_assessments", []) if isinstance(item, dict)], str(path)


def build_final_current_effective_set(
    *,
    ordinary_index_path: Path = DEFAULT_ORDINARY_INDEX,
    e3_5_run_dir: Path = DEFAULT_E3_5_RUN_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_output_path: Path = DEFAULT_DOC_OUTPUT,
) -> dict[str, Any]:
    ordinary, ordinary_artifacts = _load_ordinary_assessments(ordinary_index_path)
    e3_5, e3_5_artifact = _load_e3_5_assessments(e3_5_run_dir)
    if len(ordinary) != 114:
        raise ValueError(f"Expected 114 ordinary assessments, got {len(ordinary)}")
    if len(e3_5) != 29:
        raise ValueError(f"Expected 29 E3.5 GRI 3-3 assessments, got {len(e3_5)}")

    assessments = ordinary + e3_5
    ids = [str(item.get("manifest_item_id", "")) for item in assessments]
    duplicate_ids = sorted([item for item, count in Counter(ids).items() if count > 1])
    if duplicate_ids:
        raise ValueError(f"Duplicate manifest_item_id in final current set: {duplicate_ids}")
    if "current_gap:GRI3:3-3_generic" in ids:
        raise ValueError("3-3_generic must not enter final current assessment set")
    if len(assessments) != 143:
        raise ValueError(f"Expected 143 final current assessments, got {len(assessments)}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_final_current_effective_set_draft")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    verdict_distribution = dict(Counter(str(item.get("verdict", "")) for item in assessments))
    analysis_run_assessments = [
        DisclosureAssessment.model_validate(
            {key: value for key, value in assessment.items() if key in DisclosureAssessment.model_fields}
        ).model_dump(mode="json")
        for assessment in assessments
    ]
    payload = {
        "document_version": "p0_stage_e3_final_current_effective_assessment_set_draft_v1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "status": "draft_pending_e3_5_human_smoke_review",
        "scope": "2024_current_disclosure_final_assessment_units",
        "ordinary_current_gap_count": len(ordinary),
        "gri_3_3_index_row_count": len(e3_5),
        "total_current_assessment_units": len(assessments),
        "verdict_distribution": verdict_distribution,
        "input_artifacts": {
            "ordinary_effective_assessment_artifacts": ordinary_artifacts,
            "gri_3_3_effective_candidate_artifact": e3_5_artifact,
        },
        "blocking_items": [
            "E3.5 human smoke review is still pending.",
            "Unified final advisor real generation remains blocked until this draft is accepted.",
        ],
        "assessments": assessments,
    }
    analysis_run = AnalysisRun.model_validate(
        {
            "run_id": run_id,
            "report_id": "envision_energy_2024_zh",
            "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
            "manifest_version": "p0_stage_e3_final_current_effective_assessment_set_draft_v1",
            "status": AnalysisRunStatus.COMPLETED.value,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "source_documents": [doc.model_dump(mode="json") for doc in load_p0_source_documents()],
            "assessments": analysis_run_assessments,
            "summary": {
                "run_mode": "stage_e3_final_current_effective_set_draft",
                "effective_set_status": "draft_pending_e3_5_human_smoke_review",
                "ordinary_current_gap_count": len(ordinary),
                "gri_3_3_index_row_count": len(e3_5),
                "total_current_assessment_units": len(assessments),
                "verdict_distribution": verdict_distribution,
            },
        }
    )
    stage_gate = {
        "document_version": "p0_stage_e3_final_current_effective_set_stage_gate_v1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "gate_status": "draft_pending_e3_5_human_smoke_review",
        "total_current_assessment_units": len(assessments),
        "unified_final_advisor_status": "blocked_pending_e3_5_human_smoke_review_acceptance",
    }
    run_summary = {
        "status": "ok",
        "run_id": run_id,
        "run_mode": "stage_e3_final_current_effective_set_draft",
        "run_dir": str(run_dir),
        "ordinary_current_gap_count": len(ordinary),
        "gri_3_3_index_row_count": len(e3_5),
        "total_current_assessment_units": len(assessments),
        "verdict_distribution": verdict_distribution,
        "final_advisor_blocked": True,
        "errors": [],
        "warnings": payload["blocking_items"],
    }

    _write_json(run_dir / "final_current_effective_assessment_set_draft.json", payload)
    _write_json(run_dir / "analysis_run_draft.json", analysis_run.model_dump(mode="json"))
    _write_json(run_dir / "stage_gate_result.json", stage_gate)
    _write_json(run_dir / "run_summary.json", run_summary)
    _write_json(doc_output_path, {key: value for key, value in payload.items() if key != "assessments"} | {"run_dir": str(run_dir)})

    result = {
        "status": "ok",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "total_current_assessment_units": len(assessments),
        "verdict_distribution": verdict_distribution,
        "doc_output": str(doc_output_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Stage E3 143-item final current assessment set draft.")
    parser.add_argument("--ordinary-index", type=Path, default=DEFAULT_ORDINARY_INDEX)
    parser.add_argument("--e3-5-run-dir", type=Path, default=DEFAULT_E3_5_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-output", type=Path, default=DEFAULT_DOC_OUTPUT)
    args = parser.parse_args(argv)
    build_final_current_effective_set(
        ordinary_index_path=args.ordinary_index,
        e3_5_run_dir=args.e3_5_run_dir,
        output_dir=args.output_dir,
        doc_output_path=args.doc_output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
