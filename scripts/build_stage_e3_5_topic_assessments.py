"""Build Stage E3.5 GRI 3-3 topic-level instantiation artifacts.

This script does not call an external LLM. It converts the approved E3.5
topic scope into auditable topic-level DisclosureAssessment records, all
marked manual_review / not_assessed until an authorized 3-3 assessment run.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _manual_review_input, _write_json  # noqa: E402
from src.models.analysis_contract import AnalysisRun, AnalysisRunStatus  # noqa: E402
from src.utils.manifest_utils import load_p0_source_documents  # noqa: E402

DEFAULT_TOPIC_SCOPE = PROJECT_ROOT / "docs" / "stage_e3_5" / "e3_5_gri_3_3_topic_scope.json"
DEFAULT_EVIDENCE_INDEX = PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_report_evidence_index.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e3_5"

REPORT_PATH = "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf"
REPORT_SHA256 = "57360DCDA8E6256726BE5D2A49F8921E13187B40AE44661549903F702DF38068"

GRI_3_3_REQUIREMENTS = [
    (
        "a",
        "describe the actual and potential, negative and positive impacts on the economy, environment, and people, including impacts on their human rights;",
    ),
    (
        "b",
        "report whether the organization is involved with the negative impacts through its activities or as a result of its business relationships, and describe the activities or business relationships;",
    ),
    ("c", "describe its policies or commitments regarding the material topic;"),
    ("d", "describe actions taken to manage the topic and related impacts;"),
    ("d:i", "describe actions to prevent or mitigate potential negative impacts;"),
    ("d:ii", "describe actions to address actual negative impacts, including remediation;"),
    ("d:iii", "describe actions to manage actual and potential positive impacts;"),
    ("e", "report information about tracking the effectiveness of the actions taken;"),
    ("e:i", "describe processes used to track the effectiveness of the actions;"),
    ("e:ii", "describe goals, targets, and indicators used to evaluate progress;"),
    ("e:iii", "describe the effectiveness of the actions, including progress toward goals and targets;"),
    (
        "e:iv",
        "describe lessons learned and how these have been incorporated into operational policies and procedures;",
    ),
    (
        "f",
        "describe how engagement with stakeholders has informed the actions taken and how it has informed whether the actions have been effective;",
    ),
]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _chunk_lookup(evidence_index_path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(evidence_index_path)
    return {
        str(chunk["chunk_id"]): chunk
        for chunk in payload.get("chunks", [])
        if isinstance(chunk, dict) and chunk.get("chunk_id")
    }


def _evidence_for_chunk(
    *,
    slug: str,
    role: str,
    chunk: dict[str, Any],
    report_page_label: str | None,
) -> dict[str, Any]:
    return {
        "evidence_id": f"evidence_e3_5_3_3_{slug}_{role}",
        "source_document": REPORT_PATH,
        "source_page": chunk.get("pdf_page"),
        "report_page_label": str(report_page_label or int(chunk.get("pdf_page", 0)) - 1),
        "source_text": str(chunk.get("text", "")).strip(),
        "relevance": 0.75 if role == "materiality_scope" else 0.55,
        "evidence_kind": "substantive_report_evidence",
        "evidence_subtype": role,
        "supports_requirement_ids": [],
        "source_section": "重要性评估" if role == "materiality_scope" else "ESG战略与目标",
        "judgment_reason": (
            "Topic instantiation evidence only. This evidence identifies the material topic scope; "
            "it does not by itself support any GRI 3-3 requirement as met."
        ),
        "corpus_id": "envision_energy_2024_zh",
        "chunk_id": chunk.get("chunk_id"),
        "extraction_method": "stage_e3_5_topic_scope_instantiation",
        "source_document_sha256": REPORT_SHA256,
        "company": chunk.get("company", "Envision Energy"),
        "report_year": chunk.get("report_year", 2024),
        "industry": chunk.get("industry", "renewable_energy"),
        "topic": "gri_3_3_topic_instantiation",
        "source_text_extraction_warning": None,
        "retrieval_method": "accepted_e3_5_topic_scope",
    }


def _requirement_checks(manifest_item_id: str) -> list[dict[str, Any]]:
    checks = []
    for suffix, text in GRI_3_3_REQUIREMENTS:
        requirement_id = f"{manifest_item_id}:{suffix}"
        checks.append(
            {
                "requirement_id": requirement_id,
                "requirement_text": text,
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_assessed",
                "supporting_evidence_ids": [],
                "missing_reason": "",
                "manual_review_reason": (
                    "Pending authorized E3.5 topic-level LLM assessment and human review; "
                    "topic scope evidence alone cannot support GRI 3-3 as disclosed."
                ),
            }
        )
    return checks


def _build_assessment(topic: dict[str, Any], chunks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    slug = str(topic["topic_name_en_slug"])
    manifest_item_id = f"current_gap:GRI3:3-3_{slug}"
    primary_chunk = chunks[str(topic["source_chunk_id"])]

    evidence = [
        _evidence_for_chunk(
            slug=slug,
            role="materiality_scope",
            chunk=primary_chunk,
            report_page_label=str(topic.get("report_page_label") or ""),
        )
    ]

    cross_check = topic.get("cross_check") or {}
    cross_check_chunk_id = str(cross_check.get("source_chunk_id", ""))
    if cross_check_chunk_id and cross_check_chunk_id in chunks:
        evidence.append(
            _evidence_for_chunk(
                slug=slug,
                role="strategy_cross_check",
                chunk=chunks[cross_check_chunk_id],
                report_page_label=str(cross_check.get("report_page_label") or ""),
            )
        )

    checks = _requirement_checks(manifest_item_id)
    requirement_ids = [check["requirement_id"] for check in checks]
    return {
        "assessment_id": f"assessment_e3_5_3_3_{slug}",
        "manifest_item_id": manifest_item_id,
        "standard_id": "GRI 3",
        "standard_year": "2021",
        "canonical_disclosure_id": "3-3",
        "canonical_status": "confirmed_from_report_index",
        "assessment_mode": "current_gap",
        "verdict": "manual_review",
        "confidence": 0.0,
        "evidence": evidence,
        "requirement_checks": checks,
        "missing_requirements": [],
        "partial_requirements": [],
        "not_applicable_requirements": [],
        "manual_review_requirements": requirement_ids,
        "aggregation_reason": (
            "GRI 3-3 has been instantiated at topic level, but no authorized topic-level "
            "requirement assessment has been run in this step."
        ),
        "rationale": (
            f"{topic.get('topic_name_zh')} is included in the report's material topic list. "
            "The current artifact records scope instantiation only; it does not score the "
            "topic as disclosed or partially disclosed."
        ),
        "recommendation": "Run the authorized E3.5 topic-level GRI 3-3 assessment before scoring or final evaluation.",
        "manual_review_reason_codes": ["additional_evidence_needed"],
        "readiness_verdict": None,
        "not_scored_reason": "pending_e3_5_topic_level_llm_assessment",
        "review_status": "pending",
    }


def build_e3_5_topic_assessments(
    *,
    topic_scope_path: Path = DEFAULT_TOPIC_SCOPE,
    evidence_index_path: Path = DEFAULT_EVIDENCE_INDEX,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    topic_scope = _load_json(topic_scope_path)
    chunks = _chunk_lookup(evidence_index_path)
    topics = topic_scope.get("topic_instances", [])
    if len(topics) != 16:
        raise ValueError(f"E3.5 topic scope must contain 16 topic instances, got {len(topics)}")

    primary_cross_check = topic_scope.get("materiality_source_evidence", {}).get("cross_check", {})
    for topic in topics:
        topic.setdefault("cross_check", primary_cross_check)
        chunk_id = str(topic.get("source_chunk_id", ""))
        if chunk_id not in chunks:
            raise ValueError(f"topic source_chunk_id not found in evidence index: {chunk_id}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_5_gri3_3_topic_instantiation")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    assessments = [_build_assessment(topic, chunks) for topic in topics]
    analyst_result = {
        "p0_contract_version": "p0_stage_e3_5_topic_instantiation_v1",
        "disclosure_assessments": assessments,
        "overall_assessment": (
            "GRI 3-3 generic has been split into 16 report material topic instances. "
            "All instances are pending authorized topic-level requirement assessment."
        ),
        "summary": {
            "run_mode": "stage_e3_5_gri_3_3_topic_instantiation",
            "topic_count": len(assessments),
            "llm_called": False,
            "status": "instantiated_pending_authorized_llm_assessment",
            "source_topic_scope": str(topic_scope_path),
        },
        "raw_llm_output": "",
        "status": "completed_without_llm",
    }

    analysis_run = AnalysisRun.model_validate(
        {
            "run_id": run_id,
            "report_id": "envision_energy_2024_zh",
            "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
            "manifest_version": "p0_stage_e3_5_gri_3_3_topic_instantiation_v1",
            "status": AnalysisRunStatus.COMPLETED.value,
            "completed_at": _now_iso(),
            "source_documents": [doc.model_dump(mode="json") for doc in load_p0_source_documents()],
            "assessments": assessments,
            "summary": analyst_result["summary"],
        }
    )

    manual_review = _manual_review_input(analysis_run)
    run_summary = {
        "status": "ok",
        "run_id": run_id,
        "run_mode": "stage_e3_5_gri_3_3_topic_instantiation",
        "run_dir": str(run_dir),
        "topic_count": len(assessments),
        "assessment_count": len(assessments),
        "llm_called": False,
        "verdict_distribution": {"manual_review": len(assessments)},
        "not_scored_reason": "pending_e3_5_topic_level_llm_assessment",
        "errors": [],
        "warnings": [
            "This is an instantiation artifact only; it must not be used as final GRI 3-3 scoring output."
        ],
    }
    stage_gate = {
        "document_version": "p0_stage_e3_5_stage_gate_result_v1",
        "recorded_at": _now_iso(),
        "run_id": run_id,
        "gate_status": "instantiated_pending_authorized_llm_assessment",
        "topic_count": len(assessments),
        "generic_item_excluded": True,
        "llm_called": False,
        "allowed_next_steps": [
            "prepare_authorized_e3_5_topic_level_llm_run",
            "continue_e3_traceability_cleanup",
            "prepare_unified_final_advisor_input_from_114_effective_assessments",
        ],
        "blocked_next_steps": [
            "final_gri_3_3_scoring",
            "thesis_experiment_statistics_including_gri_3_3",
        ],
    }

    _write_json(run_dir / "topic_scope.json", topic_scope)
    _write_json(run_dir / "analyst_result.json", analyst_result)
    _write_json(run_dir / "analysis_run.json", analysis_run.model_dump(mode="json"))
    _write_json(run_dir / "manual_review_input.json", manual_review)
    _write_json(run_dir / "run_summary.json", run_summary)
    _write_json(run_dir / "stage_gate_result.json", stage_gate)

    result = {
        "status": "ok",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "topic_count": len(assessments),
        "llm_called": False,
        "analysis_run_schema_valid": True,
        "stage_gate_status": stage_gate["gate_status"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build E3.5 GRI 3-3 topic-level instantiation artifacts.")
    parser.add_argument("--topic-scope", type=Path, default=DEFAULT_TOPIC_SCOPE)
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args(argv)
    build_e3_5_topic_assessments(
        topic_scope_path=args.topic_scope,
        evidence_index_path=args.evidence_index,
        output_dir=args.output_dir,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
