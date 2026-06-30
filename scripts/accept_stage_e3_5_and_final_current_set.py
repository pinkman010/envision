"""Accept reviewed E3.5 GRI 3-3 artifacts into the 143-item final E3 set."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _write_json  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402

DEFAULT_E3_5_RUN_DIR = (
    PROJECT_ROOT
    / "data"
    / "runs"
    / "stage_e3_5"
    / "20260630T085702Z_e3_5_gri3_3_llm_index_assessment"
)
DEFAULT_DRAFT_RUN_DIR = (
    PROJECT_ROOT
    / "data"
    / "runs"
    / "stage_e_final_assessment_set"
    / "20260630T112719Z_e3_final_current_effective_set_draft"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e_final_assessment_set"
DEFAULT_DOC_OUTPUT = PROJECT_ROOT / "docs" / "stage_e3" / "e3_final_current_effective_assessment_set.json"

ACCEPTED_GATE_STATUS = "accepted_after_human_smoke_review_field_corrections"
FINAL_SET_STATUS = "accepted_effective_input_for_unified_final_advisor"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_unique(values: list[Any], *items: str) -> list[Any]:
    existing = {str(value) for value in values}
    result = list(values)
    for item in items:
        if item not in existing:
            result.append(item)
            existing.add(item)
    return result


def _validate_assessment_scope(assessments: list[dict[str, Any]]) -> dict[str, int]:
    if len(assessments) != 143:
        raise ValueError(f"Expected 143 final current assessments, got {len(assessments)}")
    ids = [str(item.get("manifest_item_id", "")) for item in assessments]
    duplicates = sorted([item for item, count in Counter(ids).items() if count > 1])
    if duplicates:
        raise ValueError(f"Duplicate manifest_item_id in accepted set: {duplicates}")
    if "current_gap:GRI3:3-3_generic" in ids:
        raise ValueError("3-3_generic must not enter accepted final current set")
    non_current = sorted(item for item in ids if not item.startswith("current_gap:"))
    if non_current:
        raise ValueError(f"Accepted set contains non-current scope ids: {non_current[:10]}")
    return dict(Counter(str(item.get("verdict", "")) for item in assessments))


def _accept_e3_5_reviewed_artifacts(e3_5_run_dir: Path, accepted_set_path: Path) -> None:
    reviewed_artifacts = [
        e3_5_run_dir / "analyst_result_merged_reviewed.json",
        e3_5_run_dir / "analysis_run_merged_reviewed.json",
        e3_5_run_dir / "manual_review_input_merged_reviewed.json",
    ]
    missing = [str(path) for path in reviewed_artifacts if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing reviewed E3.5 artifacts: {missing}")

    reviewed_payload = _load_json(reviewed_artifacts[0])
    reviewed_assessments = [
        item for item in reviewed_payload.get("disclosure_assessments", []) if isinstance(item, dict)
    ]
    if len(reviewed_assessments) != 29:
        raise ValueError(f"Expected 29 reviewed E3.5 assessments, got {len(reviewed_assessments)}")

    stage_gate_path = e3_5_run_dir / "stage_gate_result.json"
    stage_gate = _load_json(stage_gate_path)
    previous_gate_status = str(stage_gate.get("gate_status", ""))
    stage_gate.setdefault("pre_effective_acceptance_gate_status", previous_gate_status)
    stage_gate["gate_status"] = ACCEPTED_GATE_STATUS
    stage_gate["effective_gate_status"] = ACCEPTED_GATE_STATUS
    stage_gate["reviewed_artifacts_accepted_as_effective_input"] = True
    stage_gate["reviewed_artifacts_effective_input_accepted_at"] = _now_iso()
    stage_gate["accepted_effective_input_artifacts"] = [str(path) for path in reviewed_artifacts]
    stage_gate["accepted_final_current_effective_set"] = str(accepted_set_path)
    stage_gate["final_effective_set_status"] = FINAL_SET_STATUS
    stage_gate["unified_final_advisor_status"] = "authorized_for_143_assessment_real_invocation"
    _write_json(stage_gate_path, stage_gate)

    run_summary_path = e3_5_run_dir / "run_summary.json"
    run_summary = _load_json(run_summary_path)
    run_summary.setdefault("warnings_before_effective_acceptance", run_summary.get("warnings", []))
    run_summary["warnings"] = []
    run_summary["effective_gate_status"] = ACCEPTED_GATE_STATUS
    run_summary["reviewed_artifacts_accepted_as_effective_input"] = True
    run_summary["reviewed_artifacts_effective_input_accepted_at"] = _now_iso()
    run_summary["accepted_effective_input_artifacts"] = [str(path) for path in reviewed_artifacts]
    run_summary["accepted_final_current_effective_set"] = str(accepted_set_path)
    run_summary["final_effective_set_status"] = FINAL_SET_STATUS
    run_summary["unified_final_advisor_status"] = "authorized_for_143_assessment_real_invocation"
    _write_json(run_summary_path, run_summary)


def accept_final_current_effective_set(
    *,
    e3_5_run_dir: Path = DEFAULT_E3_5_RUN_DIR,
    draft_run_dir: Path = DEFAULT_DRAFT_RUN_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    doc_output_path: Path = DEFAULT_DOC_OUTPUT,
) -> dict[str, Any]:
    draft_path = draft_run_dir / "final_current_effective_assessment_set_draft.json"
    draft_analysis_run_path = draft_run_dir / "analysis_run_draft.json"
    if not draft_path.exists():
        raise FileNotFoundError(f"Draft final current set not found: {draft_path}")
    if not draft_analysis_run_path.exists():
        raise FileNotFoundError(f"Draft analysis run not found: {draft_analysis_run_path}")

    draft_payload = _load_json(draft_path)
    assessments = [item for item in draft_payload.get("assessments", []) if isinstance(item, dict)]
    verdict_distribution = _validate_assessment_scope(assessments)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_final_current_effective_set_accepted")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    accepted_set_path = run_dir / "final_current_effective_assessment_set.json"

    accepted_payload = copy.deepcopy(draft_payload)
    accepted_payload.update(
        {
            "document_version": "p0_stage_e3_final_current_effective_assessment_set_accepted_v1",
            "recorded_at": _now_iso(),
            "accepted_at": _now_iso(),
            "run_id": run_id,
            "status": FINAL_SET_STATUS,
            "source_draft_run_dir": str(draft_run_dir),
            "source_draft_assessment_set": str(draft_path),
            "e3_5_effective_input_status": ACCEPTED_GATE_STATUS,
            "blocking_items": [],
            "acceptance_basis": [
                "E3.5 human smoke review corrections applied.",
                "E3.5 reviewed artifacts explicitly accepted as effective input by user authorization.",
                "143 current assessment units validated for final unified Advisor input.",
            ],
        }
    )
    accepted_payload.setdefault("input_artifacts", {})
    accepted_payload["input_artifacts"]["gri_3_3_effective_artifact"] = str(
        e3_5_run_dir / "analyst_result_merged_reviewed.json"
    )

    analysis_run_payload = _load_json(draft_analysis_run_path)
    analysis_run_payload["run_id"] = run_id
    analysis_run_payload["manifest_version"] = "p0_stage_e3_final_current_effective_assessment_set_accepted_v1"
    analysis_run_payload["completed_at"] = _now_iso()
    analysis_run_payload.setdefault("summary", {})
    analysis_run_payload["summary"].update(
        {
            "run_mode": "stage_e3_final_current_effective_set_accepted",
            "effective_set_status": FINAL_SET_STATUS,
            "total_current_assessment_units": len(assessments),
            "verdict_distribution": verdict_distribution,
            "source_draft_run_dir": str(draft_run_dir),
            "e3_5_effective_input_status": ACCEPTED_GATE_STATUS,
        }
    )
    analysis_run = AnalysisRun.model_validate(analysis_run_payload)

    stage_gate = {
        "document_version": "p0_stage_e3_final_current_effective_set_stage_gate_v1",
        "recorded_at": _now_iso(),
        "run_id": run_id,
        "gate_status": FINAL_SET_STATUS,
        "source_draft_run_dir": str(draft_run_dir),
        "e3_5_effective_gate_status": ACCEPTED_GATE_STATUS,
        "total_current_assessment_units": len(assessments),
        "verdict_distribution": verdict_distribution,
        "unified_final_advisor_status": "authorized_for_143_assessment_real_invocation",
        "accepted_assessment_set": str(accepted_set_path),
        "accepted_analysis_run": str(run_dir / "analysis_run.json"),
    }
    run_summary = {
        "status": "ok",
        "run_id": run_id,
        "run_mode": "stage_e3_final_current_effective_set_accepted",
        "run_dir": str(run_dir),
        "ordinary_current_gap_count": 114,
        "gri_3_3_index_row_count": 29,
        "total_current_assessment_units": len(assessments),
        "verdict_distribution": verdict_distribution,
        "final_advisor_blocked": False,
        "unified_final_advisor_status": "authorized_for_143_assessment_real_invocation",
        "errors": [],
        "warnings": [],
    }

    _write_json(accepted_set_path, accepted_payload)
    _write_json(run_dir / "analysis_run.json", analysis_run.model_dump(mode="json"))
    _write_json(run_dir / "stage_gate_result.json", stage_gate)
    _write_json(run_dir / "run_summary.json", run_summary)
    _write_json(
        doc_output_path,
        {key: value for key, value in accepted_payload.items() if key != "assessments"} | {"run_dir": str(run_dir)},
    )

    _accept_e3_5_reviewed_artifacts(e3_5_run_dir, accepted_set_path)

    result = {
        "status": "ok",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "accepted_assessment_set": str(accepted_set_path),
        "analysis_run": str(run_dir / "analysis_run.json"),
        "total_current_assessment_units": len(assessments),
        "verdict_distribution": verdict_distribution,
        "doc_output": str(doc_output_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Accept E3.5 reviewed artifacts into the 143-item final E3 set.")
    parser.add_argument("--e3-5-run-dir", type=Path, default=DEFAULT_E3_5_RUN_DIR)
    parser.add_argument("--draft-run-dir", type=Path, default=DEFAULT_DRAFT_RUN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--doc-output", type=Path, default=DEFAULT_DOC_OUTPUT)
    args = parser.parse_args(argv)
    accept_final_current_effective_set(
        e3_5_run_dir=args.e3_5_run_dir,
        draft_run_dir=args.draft_run_dir,
        output_dir=args.output_dir,
        doc_output_path=args.doc_output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
