"""Stage E2.1 controlled real LLM regression entrypoint.

This script is guarded by --confirm-llm. Without that flag it exits before
creating a run directory or calling any Agent/LLM.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_p0_stage_e1_real_run import (  # noqa: E402
    _analysis_run_from_result,
    _build_retrieval_result,
    _input_text_from_contexts,
    _manual_review_input,
    _write_json,
    _write_text,
)
from src.agent.advisor_agent import AdvisorAgent  # noqa: E402
from src.agent.analyst_agent import AnalystAgent  # noqa: E402
from src.config import settings  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402
from src.utils.p0_agent_context import build_p0_requirement_contexts  # noqa: E402

DEFAULT_E1_SAMPLE_MANIFEST_PATH = (
    REPO_ROOT / "data" / "knowledge_base" / "manifests" / "p0_stage_e1_sample_manifest.json"
)
DEFAULT_E2_REGRESSION_MANIFEST_PATH = (
    REPO_ROOT / "data" / "knowledge_base" / "manifests" / "p0_stage_e2_regression_manifest.json"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "runs" / "stage_e"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _e1_sample_ids(path: Path) -> list[str]:
    payload = _load_json(path)
    sample_ids = payload.get("sample_manifest_item_ids", [])
    if not isinstance(sample_ids, list) or not sample_ids:
        raise ValueError(f"sample_manifest_item_ids must be a non-empty list: {path}")
    return [str(item) for item in sample_ids]


def _e2_regression_ids(path: Path) -> list[str]:
    payload = _load_json(path)
    items = payload.get("regression_items", [])
    if not isinstance(items, list) or not items:
        raise ValueError(f"regression_items must be a non-empty list: {path}")
    ids = [str(item.get("manifest_item_id")) for item in items if isinstance(item, dict) and item.get("manifest_item_id")]
    if not ids:
        raise ValueError(f"regression_items must contain manifest_item_id values: {path}")
    return ids


def load_regression_sample_ids(e1_sample_manifest_path: Path, e2_regression_manifest_path: Path) -> list[str]:
    seen: set[str] = set()
    merged: list[str] = []
    for item_id in [*_e1_sample_ids(e1_sample_manifest_path), *_e2_regression_ids(e2_regression_manifest_path)]:
        if item_id in seen:
            continue
        seen.add(item_id)
        merged.append(item_id)
    return merged


def _sample_contexts(sample_ids: list[str]) -> list[dict[str, Any]]:
    contexts = build_p0_requirement_contexts()
    by_id = {item["manifest_item_id"]: item for item in contexts}
    missing = [item_id for item_id in sample_ids if item_id not in by_id]
    if missing:
        raise ValueError(f"sample IDs missing from P0 contexts: {missing}")
    return [by_id[item_id] for item_id in sample_ids]


def build_e2_1_retrieval_result(
    sample_ids: list[str],
    e1_sample_manifest_path: Path,
    e2_regression_manifest_path: Path,
) -> dict[str, Any]:
    contexts = _sample_contexts(sample_ids)
    retrieval_result = _build_retrieval_result(contexts, e1_sample_manifest_path)
    retrieval_result["p0_contract_version"] = "p0_stage_d_agent_contract_v1"
    retrieval_result["input_text"] = _input_text_from_contexts(contexts)
    retrieval_result["retrieval_summary"]["run_mode"] = "stage_e2_1_regression"
    retrieval_result["retrieval_summary"]["sample_manifest_item_ids"] = sample_ids
    retrieval_result["retrieval_summary"]["e2_regression_manifest_path"] = str(e2_regression_manifest_path)
    return retrieval_result

def _manual_review_template(analysis_run: AnalysisRun) -> dict[str, Any]:
    return {
        "review_version": "p0_stage_e2_1_manual_review_template_v1",
        "run_id": analysis_run.run_id,
        "review_status": "pending",
        "items": [
            {
                "manifest_item_id": assessment.manifest_item_id,
                "model_verdict": assessment.verdict.value,
                "human_verdict": "",
                "error_type": "",
                "review_note": "",
            }
            for assessment in analysis_run.assessments
        ],
    }


def run_e2_1_regression(
    e1_sample_manifest_path: Path,
    e2_regression_manifest_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e2_1_regression")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    retrieval_result: dict[str, Any] | None = None
    analyst_result: dict[str, Any] | None = None
    advisor_result: dict[str, Any] | None = None

    try:
        sample_ids = load_regression_sample_ids(e1_sample_manifest_path, e2_regression_manifest_path)
        retrieval_result = build_e2_1_retrieval_result(
            sample_ids,
            e1_sample_manifest_path,
            e2_regression_manifest_path,
        )
        contexts = _sample_contexts(sample_ids)
        _write_json(run_dir / "retrieval_result.json", retrieval_result)

        analyst_result = AnalystAgent().run({"retrieval_result": retrieval_result}, task_id=f"{run_id}_analyst")
        _write_json(run_dir / "analyst_result.json", analyst_result)
        _write_text(run_dir / "analyst_raw_llm_output.txt", str(analyst_result.get("raw_llm_output", "")))

        advisor_result = AdvisorAgent().run({"analyst_result": analyst_result}, task_id=f"{run_id}_advisor")
        _write_json(run_dir / "advisor_result.json", advisor_result)
        _write_text(run_dir / "advisor_raw_llm_output.txt", str(advisor_result.get("raw_llm_output", "")))

        analysis_run = _analysis_run_from_result(run_id, analyst_result)
        analysis_run.summary["run_mode"] = "stage_e2_1_regression"
        analysis_run.summary["sample_manifest_item_ids"] = sample_ids
        analysis_run.summary["llm_called"] = True
        analysis_run_path = run_dir / "analysis_run.json"
        _write_json(analysis_run_path, analysis_run.model_dump(mode="json"))
        AnalysisRun.model_validate_json(analysis_run_path.read_text(encoding="utf-8"))

        manual_review_path = run_dir / "manual_review_input.json"
        _write_json(manual_review_path, _manual_review_input(analysis_run))
        _write_json(run_dir / "manual_review_result_template.json", _manual_review_template(analysis_run))

        summary = {
            "status": "ok",
            "run_id": run_id,
            "run_mode": "stage_e2_1_regression",
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
        _write_json(
            run_dir / "run_summary.json",
            {
                "status": "failed",
                "run_id": run_id,
                "run_mode": "stage_e2_1_regression",
                "llm_called": retrieval_result is not None,
                "run_dir": str(run_dir),
                "errors": [error_payload],
                "warnings": [],
            },
        )
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage E2.1 controlled real LLM regression.")
    parser.add_argument("--e1-sample-manifest", type=Path, default=DEFAULT_E1_SAMPLE_MANIFEST_PATH)
    parser.add_argument("--e2-regression-manifest", type=Path, default=DEFAULT_E2_REGRESSION_MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--confirm-llm", action="store_true", help="Required to call the configured external LLM.")
    args = parser.parse_args(argv)

    if not args.confirm_llm:
        print("E2.1 regression requires --confirm-llm after model/cost/output policy confirmation.")
        return 2

    result = run_e2_1_regression(args.e1_sample_manifest, args.e2_regression_manifest, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
