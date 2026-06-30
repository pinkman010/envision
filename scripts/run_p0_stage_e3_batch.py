"""Stage E3 batched current-disclosure real LLM runner.

The runner is guarded by --confirm-llm. Without that flag it exits before
creating a run directory or calling any Agent/LLM.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.run_p0_stage_e1_real_run import (  # noqa: E402
    _analysis_run_from_result,
    _input_text_from_contexts,
    _manual_review_input,
    _write_json,
    _write_text,
)
from scripts.validate_stage_e3_batch_outputs import validate_run_dir  # noqa: E402
from src.agent.advisor_agent import AdvisorAgent  # noqa: E402
from src.agent.analyst_agent import AnalystAgent  # noqa: E402
from src.config import settings  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402
from src.utils.p0_agent_context import build_p0_requirement_contexts  # noqa: E402

DEFAULT_SCOPE_MANIFEST_PATH = REPO_ROOT / "docs" / "stage_e3" / "e3_current_scope_manifest.json"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "runs" / "stage_e"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _git_status_snapshot() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return [f"git status unavailable: {exc}"]
    if result.returncode != 0:
        return [f"git status failed: {result.stderr.strip()}"]
    return [line for line in result.stdout.splitlines() if line.strip()]


def load_scope_manifest(path: Path = DEFAULT_SCOPE_MANIFEST_PATH) -> dict[str, Any]:
    payload = _load_json(path)
    if payload.get("stage") != "E3":
        raise ValueError(f"scope manifest stage must be E3: {path}")
    if not isinstance(payload.get("batch_plan"), list) or not payload["batch_plan"]:
        raise ValueError(f"scope manifest batch_plan must be a non-empty list: {path}")
    return payload


def batch_config(scope_manifest: dict[str, Any], batch_id: str) -> dict[str, Any]:
    for item in scope_manifest.get("batch_plan", []):
        if isinstance(item, dict) and item.get("batch_id") == batch_id:
            return item
    raise ValueError(f"batch_id not found in scope manifest: {batch_id}")


def _normalize_standard_id(value: Any) -> str:
    return str(value or "").replace(" ", "").upper()


def select_batch_contexts(scope_manifest: dict[str, Any], batch_id: str) -> list[dict[str, Any]]:
    batch = batch_config(scope_manifest, batch_id)
    standards = {_normalize_standard_id(item) for item in batch.get("standards", [])}
    if not standards:
        raise ValueError(f"{batch_id}: standards must be non-empty")

    included = {str(item) for item in batch.get("included_disclosures", []) or []}
    excluded = {str(item) for item in batch.get("excluded_disclosures", []) or []}
    excluded.add("current_gap:GRI3:3-3_generic")

    contexts = []
    for context in build_p0_requirement_contexts():
        manifest_item_id = str(context.get("manifest_item_id", ""))
        if context.get("analysis_mode") != "current_gap":
            continue
        if _normalize_standard_id(context.get("standard_id")) not in standards:
            continue
        if included and manifest_item_id not in included:
            continue
        if manifest_item_id in excluded:
            continue
        contexts.append(context)

    expected = int(batch.get("expected_current_gap_disclosure_count", -1))
    if len(contexts) != expected:
        raise ValueError(f"{batch_id}: selected {len(contexts)} contexts, expected {expected}")
    return contexts


def build_e3_retrieval_result(
    contexts: list[dict[str, Any]],
    scope_manifest_path: Path,
    scope_manifest: dict[str, Any],
    batch_id: str,
) -> dict[str, Any]:
    batch = batch_config(scope_manifest, batch_id)
    selected_ids = [str(context["manifest_item_id"]) for context in contexts]
    return {
        "p0_contract_version": "p0_stage_d_agent_contract_v1",
        "input_text": _input_text_from_contexts(contexts),
        "identified_topics": [],
        "retrieved_standards": [],
        "retrieved_peers": [],
        "coverage_summary": (
            f"Stage E3 batch {batch_id}; P0 contexts are pre-filtered by the frozen "
            "current disclosure scope manifest."
        ),
        "p0_requirement_contexts": contexts,
        "retrieval_summary": {
            "run_mode": "stage_e3_batch",
            "batch_id": batch_id,
            "batch_label": batch.get("label", ""),
            "p0_requirement_count": len(contexts),
            "sampled": False,
            "scope_manifest_path": str(scope_manifest_path),
            "scope_manifest_version": scope_manifest.get("manifest_version"),
            "sample_manifest_item_ids": selected_ids,
            "git_status_snapshot": _git_status_snapshot(),
        },
    }


def _manual_review_template(run_id: str, assessments: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "review_version": "p0_stage_e3_manual_review_template_v1",
        "run_id": run_id,
        "review_status": "pending",
        "items": [
            {
                "manifest_item_id": assessment.get("manifest_item_id", ""),
                "model_verdict": assessment.get("verdict", ""),
                "human_verdict": "",
                "error_type": "",
                "review_note": "",
            }
            for assessment in assessments
        ],
    }


def _has_non_index_evidence(assessment: dict[str, Any]) -> bool:
    return any(
        isinstance(evidence, dict) and evidence.get("evidence_kind") != "index_evidence"
        for evidence in assessment.get("evidence", []) or []
    )


def _has_multi_page_evidence(assessment: dict[str, Any]) -> bool:
    pages = {
        evidence.get("source_page")
        for evidence in assessment.get("evidence", []) or []
        if isinstance(evidence, dict) and evidence.get("source_page") is not None
    }
    return len(pages) > 1


def _smoke_review_template(
    run_id: str,
    batch_id: str,
    assessments: list[dict[str, Any]],
    smoke_review_count: int,
) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add_first(reason: str, predicate) -> None:
        if len(selected) >= smoke_review_count:
            return
        for assessment in assessments:
            item_id = str(assessment.get("manifest_item_id", ""))
            if item_id in selected_ids:
                continue
            if predicate(assessment):
                selected_ids.add(item_id)
                selected.append(
                    {
                        "manifest_item_id": item_id,
                        "model_verdict": assessment.get("verdict", ""),
                        "selection_reason": reason,
                        "human_verdict": "",
                        "evidence_page_check": "",
                        "requirement_gap_check": "",
                        "review_note": "",
                    }
                )
                return

    add_first("first_disclosed", lambda item: item.get("verdict") == "disclosed")
    add_first("first_partially_disclosed", lambda item: item.get("verdict") == "partially_disclosed")
    add_first("first_manual_review", lambda item: item.get("verdict") == "manual_review")
    add_first("multi_page_evidence", _has_multi_page_evidence)
    add_first("no_non_index_evidence", lambda item: not _has_non_index_evidence(item))

    for assessment in assessments:
        if len(selected) >= smoke_review_count:
            break
        item_id = str(assessment.get("manifest_item_id", ""))
        if item_id not in selected_ids:
            selected_ids.add(item_id)
            selected.append(
                {
                    "manifest_item_id": item_id,
                    "model_verdict": assessment.get("verdict", ""),
                    "selection_reason": "fill_to_batch_smoke_review_count",
                    "human_verdict": "",
                    "evidence_page_check": "",
                    "requirement_gap_check": "",
                    "review_note": "",
                }
            )

    return {
        "review_version": "p0_stage_e3_smoke_review_template_v1",
        "run_id": run_id,
        "batch_id": batch_id,
        "review_status": "pending",
        "items": selected,
    }


def _batch_scope_payload(
    scope_manifest_path: Path,
    scope_manifest: dict[str, Any],
    batch_id: str,
    contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    batch = batch_config(scope_manifest, batch_id)
    return {
        "scope_manifest_path": str(scope_manifest_path),
        "scope_manifest_version": scope_manifest.get("manifest_version"),
        "batch": batch,
        "selected_manifest_item_ids": [str(context["manifest_item_id"]) for context in contexts],
    }


def run_e3_batch(scope_manifest_path: Path, batch_id: str, output_dir: Path) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime(f"%Y%m%dT%H%M%SZ_{batch_id}")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    retrieval_result: dict[str, Any] | None = None
    analyst_result: dict[str, Any] | None = None
    advisor_result: dict[str, Any] | None = None

    try:
        scope_manifest = load_scope_manifest(scope_manifest_path)
        batch = batch_config(scope_manifest, batch_id)
        contexts = select_batch_contexts(scope_manifest, batch_id)
        selected_ids = [str(context["manifest_item_id"]) for context in contexts]
        _write_json(run_dir / "batch_scope_manifest.json", _batch_scope_payload(scope_manifest_path, scope_manifest, batch_id, contexts))

        retrieval_result = build_e3_retrieval_result(contexts, scope_manifest_path, scope_manifest, batch_id)
        _write_json(run_dir / "retrieval_result.json", retrieval_result)

        analyst_result = AnalystAgent().run({"retrieval_result": retrieval_result}, task_id=f"{run_id}_analyst")
        _write_json(run_dir / "analyst_result.json", analyst_result)
        _write_text(run_dir / "analyst_raw_llm_output.txt", str(analyst_result.get("raw_llm_output", "")))

        advisor_result = AdvisorAgent().run({"analyst_result": analyst_result}, task_id=f"{run_id}_advisor")
        _write_json(run_dir / "advisor_result.json", advisor_result)
        _write_text(run_dir / "advisor_raw_llm_output.txt", str(advisor_result.get("raw_llm_output", "")))

        analysis_run = _analysis_run_from_result(run_id, analyst_result)
        analysis_run.summary["run_mode"] = "stage_e3_batch"
        analysis_run.summary["batch_id"] = batch_id
        analysis_run.summary["batch_label"] = batch.get("label", "")
        analysis_run.summary["batch_manifest_item_ids"] = selected_ids
        analysis_run.summary["scope_manifest_path"] = str(scope_manifest_path)
        analysis_run.summary["llm_called"] = True
        analysis_run_path = run_dir / "analysis_run.json"
        _write_json(analysis_run_path, analysis_run.model_dump(mode="json"))
        AnalysisRun.model_validate_json(analysis_run_path.read_text(encoding="utf-8"))

        manual_review_path = run_dir / "manual_review_input.json"
        _write_json(manual_review_path, _manual_review_input(analysis_run))
        _write_json(run_dir / "manual_review_result_template.json", _manual_review_template(run_id, analyst_result.get("disclosure_assessments", [])))
        _write_json(
            run_dir / "smoke_review_template.json",
            _smoke_review_template(
                run_id,
                batch_id,
                analyst_result.get("disclosure_assessments", []),
                int(batch.get("smoke_review_count", 5)),
            ),
        )

        summary = {
            "status": "ok",
            "run_id": run_id,
            "run_mode": "stage_e3_batch",
            "batch_id": batch_id,
            "batch_label": batch.get("label", ""),
            "selected_manifest_item_ids": selected_ids,
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
        validation_result = validate_run_dir(run_dir)
        _write_json(run_dir / "batch_validation_result.json", validation_result)
        summary["validation_status"] = validation_result["status"]
        summary["validation_error_count"] = len(validation_result.get("errors", []))
        summary["validation_warning_count"] = len(validation_result.get("warnings", []))
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
                "run_mode": "stage_e3_batch",
                "batch_id": batch_id,
                "llm_called": retrieval_result is not None,
                "run_dir": str(run_dir),
                "errors": [error_payload],
                "warnings": [],
            },
        )
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Stage E3 batched current-disclosure real LLM analysis.")
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--scope-manifest", type=Path, default=DEFAULT_SCOPE_MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--confirm-llm", action="store_true", help="Required to call the configured external LLM.")
    args = parser.parse_args(argv)

    if not args.confirm_llm:
        print("E3 batch run requires --confirm-llm after model/cost/output policy confirmation.")
        return 2

    result = run_e3_batch(args.scope_manifest, args.batch_id, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
