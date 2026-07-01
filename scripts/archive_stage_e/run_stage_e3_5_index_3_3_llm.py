"""Run Stage E3.5 GRI-index-row Disclosure 3-3 LLM assessment.

The runner sends the approved 29 GRI 3-3 index-row instances, public report
evidence snippets, GRI 3-3 requirements, and Analyst prompt to the configured
LLM. It keeps per-batch raw artifacts and writes a merged 29-assessment output.
"""

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

from scripts.archive_stage_e.build_stage_e3_5_index_3_3_assessments import (  # noqa: E402
    DEFAULT_EVIDENCE_INDEX,
    DEFAULT_SCOPE_OUTPUT,
    GRI_3_3_REQUIREMENTS,
    REPORT_PATH,
    REPORT_SHA256,
)
from scripts.archive_stage_e.run_p0_stage_e1_real_run import _manual_review_input, _write_json, _write_text  # noqa: E402
from src.agent.analyst_agent import AnalystAgent  # noqa: E402
from src.config import settings  # noqa: E402
from src.models.analysis_contract import AnalysisRun, AnalysisRunStatus  # noqa: E402
from src.utils.manifest_utils import load_p0_source_documents  # noqa: E402

DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e3_5"

BATCHES = [
    {
        "batch_id": "e3_5_batch_01_3_3_economic_governance",
        "standards": ["GRI 201", "GRI 202", "GRI 203", "GRI 204", "GRI 205", "GRI 206", "GRI 207"],
        "smoke_review_count": 3,
    },
    {
        "batch_id": "e3_5_batch_02_3_3_environment",
        "standards": ["GRI 301", "GRI 302", "GRI 303", "GRI 304", "GRI 305", "GRI 306", "GRI 308"],
        "smoke_review_count": 3,
    },
    {
        "batch_id": "e3_5_batch_03_3_3_employees",
        "standards": ["GRI 401", "GRI 402", "GRI 403", "GRI 404", "GRI 405"],
        "smoke_review_count": 3,
    },
    {
        "batch_id": "e3_5_batch_04_3_3_human_rights_product",
        "standards": [
            "GRI 406",
            "GRI 407",
            "GRI 408",
            "GRI 409",
            "GRI 410",
            "GRI 413",
            "GRI 414",
            "GRI 416",
            "GRI 417",
            "GRI 418",
        ],
        "smoke_review_count": 4,
    },
]

TARGET_PAGES = {
    "GRI 201": [15, 17, 18, 19],
    "GRI 202": [6, 11, 33],
    "GRI 203": [31, 42, 43, 44],
    "GRI 204": [52, 53, 54, 55],
    "GRI 205": [56, 57, 58],
    "GRI 206": [56, 57, 58],
    "GRI 207": [56, 57, 58],
    "GRI 301": [26, 27, 63],
    "GRI 302": [23, 24, 63],
    "GRI 303": [23, 24, 63],
    "GRI 304": [29, 30],
    "GRI 305": [17, 18, 19, 63],
    "GRI 306": [21, 63, 64],
    "GRI 308": [52, 53, 54, 55, 64],
    "GRI 401": [32, 33, 34, 65, 66],
    "GRI 402": [33, 66],
    "GRI 403": [38, 39, 40, 41, 66],
    "GRI 404": [32, 35, 36, 65],
    "GRI 405": [32, 65],
    "GRI 406": [32, 52, 54],
    "GRI 407": [32, 52, 54],
    "GRI 408": [32, 52, 54],
    "GRI 409": [32, 52, 54],
    "GRI 410": [32],
    "GRI 413": [42, 43, 44],
    "GRI 414": [52, 53, 54, 55, 64],
    "GRI 416": [45, 46, 47],
    "GRI 417": [45, 46, 47],
    "GRI 418": [60, 61],
}

STANDARD_YEAR = {
    "GRI 207": "2019",
    "GRI 303": "2018",
    "GRI 403": "2018",
    "GRI 306": "2020",
}

NON_INDEX_EVIDENCE_KINDS = {"substantive_report_evidence", "omission_or_not_applicable_explanation", "external_reference_evidence"}
POSITIVE_VERDICTS = {"disclosed", "partially_disclosed"}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chunk_lookup(evidence_index_path: Path) -> dict[int, dict[str, Any]]:
    payload = _load_json(evidence_index_path)
    chunks: dict[int, dict[str, Any]] = {}
    for chunk in payload.get("chunks", []):
        if isinstance(chunk, dict) and isinstance(chunk.get("pdf_page"), int):
            chunks[int(chunk["pdf_page"])] = chunk
    return chunks


def _source_doc(chunk: dict[str, Any]) -> str:
    return str(chunk.get("source_document") or chunk.get("source_document_relative_path") or REPORT_PATH)


def _evidence_from_chunk(
    chunk: dict[str, Any],
    *,
    evidence_kind: str,
    evidence_subtype: str,
    retrieval_method: str,
    source_section: str,
    report_page_label: str | None = None,
    relevance: float = 0.75,
) -> dict[str, Any]:
    pdf_page = int(chunk.get("pdf_page"))
    return {
        "chunk_id": chunk.get("chunk_id"),
        "source_document": _source_doc(chunk),
        "source_document_sha256": chunk.get("source_document_sha256") or REPORT_SHA256,
        "pdf_page": pdf_page,
        "source_page": pdf_page,
        "report_page_label": str(report_page_label if report_page_label is not None else pdf_page - 1),
        "source_section": source_section,
        "evidence_kind": evidence_kind,
        "evidence_subtype": evidence_subtype,
        "retrieval_method": retrieval_method,
        "supports_requirement_ids": [],
        "source_text_extraction_warning": None,
        "source_text": str(chunk.get("text", "")).strip(),
        "text": str(chunk.get("text", "")).strip(),
        "relevance": relevance,
        "company": chunk.get("company", "Envision Energy"),
        "report_year": chunk.get("report_year", 2024),
        "industry": chunk.get("industry", "renewable_energy"),
        "topic": "gri_3_3_index_row_assessment",
        "extraction_method": "p0_report_evidence_index",
        "judgment_reason": (
            "Candidate evidence for GRI 3-3 assessment. Index and materiality evidence are locators; "
            "requirements may be marked met only when topic-specific management disclosure is present."
        ),
    }


def _requirement_items(manifest_item_id: str) -> list[dict[str, Any]]:
    return [
        {
            "requirement_id": f"{manifest_item_id}:{suffix}",
            "requirement_text": text,
            "requirement_type": "requirement",
            "is_mandatory": True,
            "conditional": False,
            "condition_text": "",
            "scoring_role": "hard_score",
            "official_pdf_page": 110,
        }
        for suffix, text in GRI_3_3_REQUIREMENTS
    ]


def _contexts_for_batch(
    *,
    instances: list[dict[str, Any]],
    chunks_by_page: dict[int, dict[str, Any]],
    batch: dict[str, Any],
) -> list[dict[str, Any]]:
    standards = set(batch["standards"])
    contexts: list[dict[str, Any]] = []
    materiality_chunk = chunks_by_page[15]
    strategy_chunk = chunks_by_page[11]

    for instance in instances:
        standard_id = str(instance["standard_id"])
        if standard_id not in standards:
            continue
        manifest_item_id = str(instance["manifest_item_id"])
        index_page = int(instance["index_source_page"])
        index_chunk = chunks_by_page[index_page]
        target_pages = TARGET_PAGES.get(standard_id, [])
        referenced = [
            _evidence_from_chunk(
                chunks_by_page[page],
                evidence_kind="substantive_report_evidence",
                evidence_subtype="index_referenced_page",
                retrieval_method="gri_index_3_3_target_page",
                source_section="report_body_topic_section",
            )
            for page in target_pages
            if page in chunks_by_page
        ]
        fulltext = [
            _evidence_from_chunk(
                materiality_chunk,
                evidence_kind="substantive_report_evidence",
                evidence_subtype="materiality_topic_mapping",
                retrieval_method="materiality_topic_crosswalk",
                source_section="重要性评估",
                relevance=0.55,
            ),
            _evidence_from_chunk(
                strategy_chunk,
                evidence_kind="substantive_report_evidence",
                evidence_subtype="strategy_topic_crosswalk",
                retrieval_method="materiality_topic_crosswalk",
                source_section="ESG战略与目标",
                relevance=0.55,
            ),
        ]
        index_evidence = _evidence_from_chunk(
            index_chunk,
            evidence_kind="index_evidence",
            evidence_subtype="gri_index_3_3_row_locator",
            retrieval_method="gri_content_index_locator",
            source_section="GRI content index",
            report_page_label=str(instance["index_report_page_label"]),
            relevance=1.0,
        )
        contexts.append(
            {
                "manifest_item_id": manifest_item_id,
                "analysis_mode": "current_gap",
                "standard_id": standard_id,
                "standard_year": STANDARD_YEAR.get(standard_id, "2016"),
                "canonical_disclosure_id": "3-3",
                "canonical_status": "confirmed_from_report_index",
                "evidence_expectation": (
                    "Assess Disclosure 3-3 for this GRI index row. Index evidence and materiality "
                    "crosswalk evidence only identify the instance; they cannot by themselves support "
                    "any 3-3 requirement as met. Use topic-specific management disclosure pages."
                ),
                "requirement_locator_status": "found",
                "official_pdf_pages_for_agent": [110],
                "official_pdf_page_candidates": [110],
                "locator_review_required": False,
                "agent_manual_review_required": False,
                "can_score_current_gap": True,
                "forced_verdict": None,
                "policy_reason": (
                    "GRI 3-3 index-row instance can be scored only after topic-specific management "
                    "evidence is checked requirement by requirement."
                ),
                "report_index_pdf_page": index_page,
                "report_index_report_page": int(instance["index_report_page_label"]),
                "mapped_materiality_topic_zh": instance.get("mapped_materiality_topic_zh"),
                "requirement_checklist_items": _requirement_items(manifest_item_id),
                "evidence_bundle": {
                    "index_evidence": [index_evidence],
                    "referenced_page_evidence": referenced,
                    "nearby_page_evidence": [],
                    "fulltext_requirement_evidence": fulltext,
                    "substantive_report_evidence": [],
                    "omission_or_not_applicable_explanation": [],
                    "external_reference_evidence": [],
                },
                "report_evidence_chunks": [index_evidence],
            }
        )
    return contexts


def _retrieval_result(contexts: list[dict[str, Any]], batch_id: str, run_id: str) -> dict[str, Any]:
    return {
        "p0_contract_version": "p0_stage_e3_5_index_3_3_contract_v1",
        "input_text": "",
        "identified_topics": [],
        "retrieved_standards": [],
        "retrieved_peers": [],
        "coverage_summary": "Stage E3.5 GRI index-row Disclosure 3-3 real LLM assessment batch.",
        "p0_requirement_contexts": contexts,
        "retrieval_summary": {
            "run_mode": "stage_e3_5_index_3_3_llm",
            "run_id": run_id,
            "batch_id": batch_id,
            "p0_requirement_count": len(contexts),
            "sampled": False,
            "llm_authorized_by_user": True,
        },
    }


def _analysis_run(run_id: str, analyst_result: dict[str, Any], *, run_mode: str, batch_id: str | None = None) -> AnalysisRun:
    summary = {
        **(analyst_result.get("summary", {}) or {}),
        "run_mode": run_mode,
        "batch_id": batch_id,
        "assessment_count": len(analyst_result.get("disclosure_assessments", [])),
        "llm_called": True,
        "model": settings.LLM_MODEL,
        "base_url": settings.LLM_BASE_URL,
        "thinking_type": settings.LLM_THINKING_TYPE,
        "reasoning_effort": settings.LLM_REASONING_EFFORT,
        "response_format": settings.LLM_RESPONSE_FORMAT or None,
    }
    return AnalysisRun.model_validate(
        {
            "run_id": run_id,
            "report_id": "envision_energy_2024_zh",
            "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
            "manifest_version": "p0_stage_e3_5_index_3_3_llm_v1",
            "status": AnalysisRunStatus.COMPLETED.value,
            "completed_at": _now_iso(),
            "source_documents": [doc.model_dump(mode="json") for doc in load_p0_source_documents()],
            "assessments": analyst_result.get("disclosure_assessments", []),
            "summary": summary,
        }
    )


def _smoke_review_template(run_id: str, assessments: list[dict[str, Any]], count: int = 7) -> dict[str, Any]:
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(reason: str, predicate) -> None:
        if len(selected) >= count:
            return
        for assessment in assessments:
            item_id = str(assessment.get("manifest_item_id"))
            if item_id in seen:
                continue
            if predicate(assessment):
                seen.add(item_id)
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

    add("first_disclosed", lambda item: item.get("verdict") == "disclosed")
    add("first_partially_disclosed", lambda item: item.get("verdict") == "partially_disclosed")
    add("first_not_disclosed", lambda item: item.get("verdict") == "not_disclosed")
    add("first_manual_review", lambda item: item.get("verdict") == "manual_review")
    add("environment_sample", lambda item: "GRI30" in str(item.get("manifest_item_id")))
    add("people_sample", lambda item: "GRI40" in str(item.get("manifest_item_id")))
    add("supply_chain_or_product_sample", lambda item: any(code in str(item.get("manifest_item_id")) for code in ["GRI414", "GRI416", "GRI418"]))
    for assessment in assessments:
        if len(selected) >= count:
            break
        item_id = str(assessment.get("manifest_item_id"))
        if item_id not in seen:
            seen.add(item_id)
            selected.append(
                {
                    "manifest_item_id": item_id,
                    "model_verdict": assessment.get("verdict", ""),
                    "selection_reason": "fill_to_smoke_review_count",
                    "human_verdict": "",
                    "evidence_page_check": "",
                    "requirement_gap_check": "",
                    "review_note": "",
                }
            )
    return {
        "review_version": "p0_stage_e3_5_3_3_smoke_review_template_v1",
        "run_id": run_id,
        "review_status": "pending_human_review",
        "items": selected,
    }


def _machine_smoke_review(run_id: str, assessments: list[dict[str, Any]], template: dict[str, Any]) -> dict[str, Any]:
    by_id = {str(item.get("manifest_item_id")): item for item in assessments}
    items: list[dict[str, Any]] = []
    hard_issues: list[str] = []
    for item in template.get("items", []):
        assessment = by_id.get(str(item.get("manifest_item_id")), {})
        issue_types: list[str] = []
        verdict = str(assessment.get("verdict", ""))
        evidence = [e for e in assessment.get("evidence", []) or [] if isinstance(e, dict)]
        if verdict in POSITIVE_VERDICTS and not any(e.get("evidence_kind") in NON_INDEX_EVIDENCE_KINDS for e in evidence):
            issue_types.append("index_only_positive_disclosure")
        for evidence_item in evidence:
            source_text = str(evidence_item.get("source_text", ""))
            if "..." in source_text or "…" in source_text:
                issue_types.append("source_text_not_verbatim")
            source_page = evidence_item.get("source_page")
            label = str(evidence_item.get("report_page_label", "")).strip()
            if isinstance(source_page, int) and label.isdigit() and source_page != int(label) + 1:
                issue_types.append("page_offset_mismatch")
        if verdict == "partially_disclosed" and not (
            assessment.get("missing_requirements") or assessment.get("partial_requirements")
        ):
            issue_types.append("partial_without_gap_fields")
        if verdict == "manual_review" and not assessment.get("manual_review_reason_codes"):
            issue_types.append("manual_review_without_reason_codes")
        if issue_types:
            hard_issues.extend([f"{item.get('manifest_item_id')}: {issue}" for issue in issue_types])
        items.append(
            {
                **item,
                "machine_issue_types": sorted(set(issue_types)),
                "machine_evidence_page_check": "needs_review" if issue_types else "ok",
                "machine_requirement_gap_check": "needs_review" if issue_types else "ok",
            }
        )
    return {
        "review_version": "p0_stage_e3_5_3_3_machine_smoke_review_v1",
        "run_id": run_id,
        "review_status": "machine_completed_pending_human_review",
        "gate_status": "pending_human_smoke_review",
        "items": items,
        "hard_issues": hard_issues,
    }


def _validate_merged(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[str] = []
    ids = [str(item.get("manifest_item_id", "")) for item in assessments]
    if len(assessments) != 29:
        errors.append(f"expected 29 E3.5 GRI 3-3 assessments, got {len(assessments)}")
    duplicates = [item for item, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"duplicate manifest_item_id: {duplicates}")
    if "current_gap:GRI3:3-3_generic" in ids:
        errors.append("3-3_generic must not enter E3.5 index-row assessments")
    for assessment in assessments:
        label = str(assessment.get("manifest_item_id"))
        if not label.endswith(":3-3"):
            errors.append(f"{label}: manifest_item_id must end with :3-3")
        if assessment.get("assessment_mode") != "current_gap":
            errors.append(f"{label}: assessment_mode must be current_gap")
        if assessment.get("canonical_disclosure_id") != "3-3":
            errors.append(f"{label}: canonical_disclosure_id must be 3-3")
        verdict = str(assessment.get("verdict", ""))
        evidence = [e for e in assessment.get("evidence", []) or [] if isinstance(e, dict)]
        if verdict in POSITIVE_VERDICTS and not any(e.get("evidence_kind") in NON_INDEX_EVIDENCE_KINDS for e in evidence):
            errors.append(f"{label}: positive verdict cannot be supported by index evidence alone")
        if verdict == "partially_disclosed" and not (
            assessment.get("missing_requirements") or assessment.get("partial_requirements")
        ):
            errors.append(f"{label}: partially_disclosed requires missing_requirements or partial_requirements")
        if verdict == "manual_review" and not assessment.get("manual_review_reason_codes"):
            errors.append(f"{label}: manual_review requires reason codes")
    return {
        "status": "ok" if not errors else "failed",
        "mode": "stage_e3_5_index_3_3_merged_validation",
        "assessment_count": len(assessments),
        "errors": errors,
        "warnings": [],
    }


def run_e3_5_index_3_3_llm(
    *,
    scope_path: Path = DEFAULT_SCOPE_OUTPUT,
    evidence_index_path: Path = DEFAULT_EVIDENCE_INDEX,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_5_gri3_3_llm_index_assessment")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    scope = _load_json(scope_path)
    chunks_by_page = _chunk_lookup(evidence_index_path)
    instances = [item for item in scope.get("instances", []) if isinstance(item, dict)]
    all_assessments: list[dict[str, Any]] = []
    batch_summaries: list[dict[str, Any]] = []

    for batch in BATCHES:
        batch_id = str(batch["batch_id"])
        batch_dir = run_dir / batch_id
        batch_dir.mkdir(parents=True, exist_ok=False)
        contexts = _contexts_for_batch(instances=instances, chunks_by_page=chunks_by_page, batch=batch)
        retrieval = _retrieval_result(contexts, batch_id, run_id)
        _write_json(batch_dir / "retrieval_result.json", retrieval)
        analyst_result = AnalystAgent().run({"retrieval_result": retrieval}, task_id=f"{run_id}_{batch_id}_analyst")
        _write_json(batch_dir / "analyst_result.json", analyst_result)
        _write_text(batch_dir / "analyst_raw_llm_output.txt", str(analyst_result.get("raw_llm_output", "")))
        analysis_run = _analysis_run(f"{run_id}_{batch_id}", analyst_result, run_mode="stage_e3_5_index_3_3_llm_batch", batch_id=batch_id)
        _write_json(batch_dir / "analysis_run.json", analysis_run.model_dump(mode="json"))
        _write_json(batch_dir / "manual_review_input.json", _manual_review_input(analysis_run))
        assessments = [item for item in analyst_result.get("disclosure_assessments", []) if isinstance(item, dict)]
        all_assessments.extend(assessments)
        batch_summaries.append(
            {
                "batch_id": batch_id,
                "standards": batch["standards"],
                "context_count": len(contexts),
                "assessment_count": len(assessments),
                "verdict_distribution": dict(Counter(str(item.get("verdict", "")) for item in assessments)),
                "batch_dir": str(batch_dir),
            }
        )

    merged_result = {
        "p0_contract_version": "p0_stage_e3_5_index_3_3_llm_v1",
        "disclosure_assessments": all_assessments,
        "overall_assessment": "Merged E3.5 GRI index-row Disclosure 3-3 LLM assessment results.",
        "summary": {
            "run_mode": "stage_e3_5_index_3_3_llm_merged",
            "assessment_count": len(all_assessments),
            "ordinary_current_gap_count": 114,
            "expected_final_current_assessment_units": 143,
            "llm_called": True,
            "model": settings.LLM_MODEL,
            "base_url": settings.LLM_BASE_URL,
            "verdict_distribution": dict(Counter(str(item.get("verdict", "")) for item in all_assessments)),
            "batch_summaries": batch_summaries,
        },
        "raw_llm_output": "",
        "status": "completed",
    }
    merged_analysis_run = _analysis_run(run_id, merged_result, run_mode="stage_e3_5_index_3_3_llm_merged")
    validation = _validate_merged(all_assessments)
    smoke_template = _smoke_review_template(run_id, all_assessments)
    machine_smoke = _machine_smoke_review(run_id, all_assessments, smoke_template)
    stage_gate = {
        "document_version": "p0_stage_e3_5_index_3_3_llm_stage_gate_result_v1",
        "recorded_at": _now_iso(),
        "run_id": run_id,
        "gate_status": "pending_human_smoke_review",
        "llm_called": True,
        "assessment_count": len(all_assessments),
        "ordinary_current_gap_count": 114,
        "expected_final_current_assessment_units": 143,
        "validation_status": validation["status"],
        "machine_smoke_review_status": machine_smoke["review_status"],
        "human_smoke_review_required": True,
        "final_effective_set_status": "draft_pending_human_smoke_review",
    }
    run_summary = {
        "status": "ok" if validation["status"] == "ok" else "needs_review",
        "run_id": run_id,
        "run_mode": "stage_e3_5_index_3_3_llm",
        "run_dir": str(run_dir),
        "assessment_count": len(all_assessments),
        "ordinary_current_gap_count": 114,
        "expected_final_current_assessment_units": 143,
        "llm_called": True,
        "model": settings.LLM_MODEL,
        "base_url": settings.LLM_BASE_URL,
        "verdict_distribution": merged_result["summary"]["verdict_distribution"],
        "validation_status": validation["status"],
        "machine_smoke_hard_issue_count": len(machine_smoke["hard_issues"]),
        "errors": validation["errors"],
        "warnings": [
            "Human smoke review is still required before accepting these 3-3 assessments as effective.",
            "Unified final advisor remains blocked until 3-3 human smoke review is accepted.",
        ],
    }

    _write_json(run_dir / "index_instance_scope.json", scope)
    _write_json(run_dir / "batch_summaries.json", {"items": batch_summaries})
    _write_json(run_dir / "analyst_result_merged.json", merged_result)
    _write_json(run_dir / "analysis_run_merged.json", merged_analysis_run.model_dump(mode="json"))
    _write_json(run_dir / "manual_review_input_merged.json", _manual_review_input(merged_analysis_run))
    _write_json(run_dir / "merged_validation_result.json", validation)
    _write_json(run_dir / "smoke_review_template.json", smoke_template)
    _write_json(run_dir / "machine_smoke_review_result.json", machine_smoke)
    _write_json(run_dir / "stage_gate_result.json", stage_gate)
    _write_json(run_dir / "run_summary.json", run_summary)

    result = {
        "status": run_summary["status"],
        "run_id": run_id,
        "run_dir": str(run_dir),
        "assessment_count": len(all_assessments),
        "validation_status": validation["status"],
        "machine_smoke_hard_issue_count": len(machine_smoke["hard_issues"]),
        "human_smoke_review_required": True,
        "verdict_distribution": merged_result["summary"]["verdict_distribution"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run E3.5 GRI index-row Disclosure 3-3 real LLM assessment.")
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE_OUTPUT)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--confirm-llm", action="store_true", help="Required to call the configured external LLM.")
    args = parser.parse_args(argv)
    if not args.confirm_llm:
        print("E3.5 GRI 3-3 LLM run requires --confirm-llm after user authorization.")
        return 2
    run_e3_5_index_3_3_llm(
        scope_path=args.scope,
        evidence_index_path=args.evidence_index,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
