"""Prepare a unified final Advisor input package for Stage E3.

The default mode does not call the external LLM. Use --confirm-llm only after
the user explicitly authorizes sending the merged effective assessments and
Advisor prompt to the configured provider.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _write_json, _write_text  # noqa: E402
from src.agent.advisor_agent import AdvisorAgent  # noqa: E402
from src.config import settings  # noqa: E402

DEFAULT_EFFECTIVE_ARTIFACTS = PROJECT_ROOT / "docs" / "stage_e3" / "e3_current_scope_effective_artifacts.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e_final_advisor"
DEFAULT_DOC_OUTPUT = PROJECT_ROOT / "docs" / "stage_e3" / "e3_final_advisor_invocation_approval.md"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relative_or_absolute(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _load_assessments(index_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    payload = _load_json(index_path)
    artifacts = [str(item) for item in payload.get("aggregate_effective_inputs", {}).get("effective_assessment_artifacts", [])]
    assessments: list[dict[str, Any]] = []
    for artifact in artifacts:
        data = _load_json(_relative_or_absolute(artifact))
        assessments.extend([item for item in data.get("disclosure_assessments", []) if isinstance(item, dict)])
    return assessments, artifacts


def _approval_markdown(run_dir: Path, assessment_count: int, verdict_counts: dict[str, int]) -> str:
    return "\n".join(
        [
            "# E3 Unified Final Advisor Invocation Approval",
            "",
            "## Status",
            "",
            "- Local input package prepared.",
            "- DeepSeek API has not been called by this preparation step.",
            "- External invocation requires explicit user authorization.",
            "",
            "## Send Scope",
            "",
            f"- Merged effective E3 ordinary current-gap assessments: {assessment_count}",
            "- Public Envision Energy 2024 report evidence snippets already embedded in effective assessments.",
            "- Advisor Prompt from `templates/prompt_templates/advisor_prompt.j2`.",
            "- No `.env`, API keys, raw PDFs, or non-public internal data.",
            "",
            "## Local Input Package",
            "",
            f"- Run directory: `{run_dir}`",
            "- Input file: `merged_effective_analyst_result.json`",
            "",
            "## Verdict Distribution",
            "",
            *[f"- `{key}`: {value}" for key, value in sorted(verdict_counts.items())],
            "",
            "## Config Snapshot",
            "",
            f"- `LLM_MODEL`: `{settings.LLM_MODEL}`",
            f"- `LLM_BASE_URL`: `{settings.LLM_BASE_URL}`",
            f"- `LLM_THINKING_TYPE`: `{settings.LLM_THINKING_TYPE}`",
            f"- `LLM_REASONING_EFFORT`: `{settings.LLM_REASONING_EFFORT}`",
            f"- `LLM_RESPONSE_FORMAT`: `{settings.LLM_RESPONSE_FORMAT or ''}`",
            "",
            "## Risk",
            "",
            "- Cost and latency depend on the configured model and current provider behavior.",
            "- Advisor output must be checked for over-inference: recommendations may only say the report did not disclose or could not be verified from public evidence.",
            "- Batch-level stale advisor artifacts remain audit trail only; this run should supersede them for final recommendations after approval.",
            "",
        ]
    )


def prepare_or_run_final_advisor(
    *,
    effective_artifacts_path: Path = DEFAULT_EFFECTIVE_ARTIFACTS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    approval_doc_path: Path = DEFAULT_DOC_OUTPUT,
    confirm_llm: bool = False,
) -> dict[str, Any]:
    assessments, artifacts = _load_assessments(effective_artifacts_path)
    if len(assessments) != 114:
        raise ValueError(f"Expected 114 effective E3 assessments, got {len(assessments)}")
    ids = [str(item.get("manifest_item_id", "")) for item in assessments]
    duplicate_ids = sorted([item for item, count in Counter(ids).items() if count > 1])
    if duplicate_ids:
        raise ValueError(f"Duplicate manifest_item_id in effective assessments: {duplicate_ids}")
    if "current_gap:GRI3:3-3_generic" in ids:
        raise ValueError("3-3_generic must not enter unified final advisor input")

    verdict_counts = dict(Counter(str(item.get("verdict", "")) for item in assessments))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_unified_final_advisor")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    analyst_result = {
        "p0_contract_version": "p0_stage_e3_unified_effective_analyst_result_v1",
        "disclosure_assessments": assessments,
        "overall_assessment": (
            "Unified final Advisor input built from 114 accepted effective ordinary current-gap assessments. "
            "GRI 3-3 topic-level instantiation is handled separately in E3.5 and is not included in this 114-item advisor input."
        ),
        "summary": {
            "run_mode": "stage_e3_unified_final_advisor_input",
            "assessment_count": len(assessments),
            "verdict_distribution": verdict_counts,
            "effective_assessment_artifacts": artifacts,
            "llm_called": bool(confirm_llm),
        },
    }
    _write_json(run_dir / "merged_effective_analyst_result.json", analyst_result)
    _write_json(
        run_dir / "run_summary.json",
        {
            "status": "prepared",
            "run_id": run_id,
            "run_mode": "stage_e3_unified_final_advisor",
            "run_dir": str(run_dir),
            "assessment_count": len(assessments),
            "verdict_distribution": verdict_counts,
            "llm_called": False,
            "authorization_required": True,
            "errors": [],
            "warnings": [
                "DeepSeek API was not called. Run again with --confirm-llm only after explicit user authorization."
            ],
        },
    )
    approval_doc = _approval_markdown(run_dir, len(assessments), verdict_counts)
    _write_text(approval_doc_path, approval_doc)

    result: dict[str, Any] = {
        "status": "prepared",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "assessment_count": len(assessments),
        "llm_called": False,
        "approval_doc": str(approval_doc_path),
    }
    if confirm_llm:
        advisor_result = AdvisorAgent().run({"analyst_result": analyst_result}, task_id=f"{run_id}_advisor")
        _write_json(run_dir / "final_advisor_result.json", advisor_result)
        _write_text(run_dir / "final_advisor_raw_llm_output.txt", str(advisor_result.get("raw_llm_output", "")))
        summary = _load_json(run_dir / "run_summary.json")
        summary.update(
            {
                "status": "completed",
                "llm_called": True,
                "model": settings.LLM_MODEL,
                "base_url": settings.LLM_BASE_URL,
                "final_advisor_result": str(run_dir / "final_advisor_result.json"),
                "recommendation_count": len(advisor_result.get("p0_recommendations", [])),
            }
        )
        _write_json(run_dir / "run_summary.json", summary)
        result.update(
            {
                "status": "completed",
                "llm_called": True,
                "final_advisor_result": str(run_dir / "final_advisor_result.json"),
                "recommendation_count": len(advisor_result.get("p0_recommendations", [])),
            }
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare or run unified Stage E3 final Advisor.")
    parser.add_argument("--effective-artifacts", type=Path, default=DEFAULT_EFFECTIVE_ARTIFACTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--approval-doc", type=Path, default=DEFAULT_DOC_OUTPUT)
    parser.add_argument("--confirm-llm", action="store_true", help="Call the configured external LLM.")
    args = parser.parse_args(argv)
    prepare_or_run_final_advisor(
        effective_artifacts_path=args.effective_artifacts,
        output_dir=args.output_dir,
        approval_doc_path=args.approval_doc,
        confirm_llm=args.confirm_llm,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
