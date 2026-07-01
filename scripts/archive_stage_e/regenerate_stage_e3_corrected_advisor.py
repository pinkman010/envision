"""Regenerate Advisor output from a corrected Stage E3 analyst artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").exists())
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.archive_stage_e.run_p0_stage_e1_real_run import _write_json, _write_text  # noqa: E402
from scripts.validate_stage_e3_batch_outputs import validate_run_dir  # noqa: E402
from src.agent.advisor_agent import AdvisorAgent  # noqa: E402
from src.config import settings  # noqa: E402

DEFAULT_RUN_DIR = (
    PROJECT_ROOT
    / "data"
    / "runs"
    / "stage_e"
    / "20260630T070123Z_e3_batch_05_governance_supply_chain_economic"
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _append_unique(values: list[Any], *items: str) -> list[Any]:
    existing = {str(value) for value in values}
    result = list(values)
    for item in items:
        if item not in existing:
            result.append(item)
            existing.add(item)
    return result


def regenerate_corrected_advisor(run_dir: Path) -> dict[str, Any]:
    analyst_path = run_dir / "analyst_result_corrected.json"
    if not analyst_path.exists():
        raise FileNotFoundError(f"corrected analyst artifact not found: {analyst_path}")

    run_summary = _load_json(run_dir / "run_summary.json")
    run_id = str(run_summary["run_id"])
    batch_id = str(run_summary["batch_id"])
    analyst_result = _load_json(analyst_path)

    advisor_result = AdvisorAgent().run(
        {"analyst_result": analyst_result},
        task_id=f"{run_id}_advisor_corrected",
    )

    advisor_path = run_dir / "advisor_result_corrected.json"
    advisor_raw_path = run_dir / "advisor_raw_llm_output_corrected.txt"
    _write_json(advisor_path, advisor_result)
    _write_text(advisor_raw_path, str(advisor_result.get("raw_llm_output", "")))

    require_smoke_review = (run_dir / "smoke_review_result.json").exists()
    validation = validate_run_dir(run_dir, require_smoke_review_result=require_smoke_review)
    validation_path = run_dir / "batch_validation_result_after_corrected_advisor.json"
    _write_json(validation_path, validation)

    advisor_artifacts = [str(advisor_path), str(advisor_raw_path)]
    run_summary["advisor_result_corrected_path"] = str(advisor_path)
    run_summary["advisor_raw_llm_output_corrected_path"] = str(advisor_raw_path)
    run_summary["advisor_regenerated_from"] = str(analyst_path)
    run_summary["advisor_corrected_llm_called"] = True
    run_summary["advisor_corrected_model"] = settings.LLM_MODEL
    run_summary["advisor_corrected_base_url"] = settings.LLM_BASE_URL
    run_summary["advisor_corrected_status"] = str(advisor_result.get("status", ""))
    run_summary["raw_advisor_result_status"] = "superseded_by_advisor_result_corrected"
    run_summary["validation_status_after_corrected_advisor"] = validation["status"]
    run_summary["validation_errors_after_corrected_advisor"] = validation.get("errors", [])
    run_summary["corrected_artifacts"] = _append_unique(
        run_summary.get("corrected_artifacts", []),
        str(advisor_path),
    )
    _write_json(run_dir / "run_summary.json", run_summary)

    stage_gate_path = run_dir / "stage_gate_result.json"
    if stage_gate_path.exists():
        stage_gate = _load_json(stage_gate_path)
    else:
        stage_gate = {"run_id": run_id, "batch_id": batch_id}

    stage_gate["advisor_result_corrected"] = str(advisor_path)
    stage_gate["advisor_raw_llm_output_corrected"] = str(advisor_raw_path)
    stage_gate["advisor_regenerated_from_corrected_analyst"] = True
    stage_gate["advisor_corrected_llm_called"] = True
    stage_gate["raw_advisor_result_status"] = "superseded_by_advisor_result_corrected"
    stage_gate["validation_status_after_corrected_advisor"] = validation["status"]
    stage_gate["validation_errors_after_corrected_advisor"] = validation.get("errors", [])
    stage_gate["corrected_artifacts"] = _append_unique(
        stage_gate.get("corrected_artifacts", []),
        str(advisor_path),
    )
    stage_gate["accepted_stage_gate_input_files"] = _append_unique(
        stage_gate.get("accepted_stage_gate_input_files", []),
        str(advisor_path),
    )
    stage_gate["next_required_action"] = "complete_e3_current_scope_acceptance_audit"
    _write_json(stage_gate_path, stage_gate)

    return {
        "run_id": run_id,
        "batch_id": batch_id,
        "advisor_result_corrected": str(advisor_path),
        "advisor_raw_llm_output_corrected": str(advisor_raw_path),
        "advisor_status": advisor_result.get("status", ""),
        "recommendation_count": len(advisor_result.get("p0_recommendations", [])),
        "validation_status_after_corrected_advisor": validation["status"],
        "validation_error_count_after_corrected_advisor": len(validation.get("errors", [])),
        "advisor_artifacts": advisor_artifacts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Regenerate Stage E3 corrected Advisor output.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--confirm-llm", action="store_true", help="Required to call the configured external LLM.")
    args = parser.parse_args(argv)

    if not args.confirm_llm:
        print("Corrected Advisor regeneration requires --confirm-llm after model/cost/output policy confirmation.")
        return 2

    result = regenerate_corrected_advisor(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
