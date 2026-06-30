"""Build Stage E3.5 GRI-index-row Disclosure 3-3 instances.

The E3.5 materiality topic draft has 16 report topics. The final current
assessment unit scope, however, follows the report GRI index row granularity:
one Disclosure 3-3 instance per topic-specific GRI Standard listed in the
report index. This script creates those 29 placeholder assessments without
calling an external LLM.
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

from scripts.build_stage_e3_5_topic_assessments import GRI_3_3_REQUIREMENTS  # noqa: E402
from scripts.run_p0_stage_e1_real_run import _manual_review_input, _write_json  # noqa: E402
from src.models.analysis_contract import AnalysisRun, AnalysisRunStatus  # noqa: E402
from src.utils.manifest_utils import load_p0_source_documents  # noqa: E402

DEFAULT_EVIDENCE_INDEX = PROJECT_ROOT / "data" / "knowledge_base" / "manifests" / "p0_report_evidence_index.json"
DEFAULT_TOPIC_SCOPE = PROJECT_ROOT / "docs" / "stage_e3_5" / "e3_5_gri_3_3_topic_scope.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e3_5"
DEFAULT_SCOPE_OUTPUT = PROJECT_ROOT / "docs" / "stage_e3_5" / "e3_5_gri_3_3_index_instance_scope.json"

REPORT_PATH = "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf"
REPORT_SHA256 = "57360DCDA8E6256726BE5D2A49F8921E13187B40AE44661549903F702DF38068"

INDEX_INSTANCES = [
    ("GRI 201", "经济绩效", "economic_performance", 72, "chunk_84014d6613aea4be1f3f24be", "社会经济贡献与社区关系"),
    ("GRI 202", "市场表现", "market_presence", 72, "chunk_84014d6613aea4be1f3f24be", "人力资本发展"),
    ("GRI 203", "间接经济影响", "indirect_economic_impacts", 73, "chunk_6bca4a60cd18caaec91a6a7d", "社会经济贡献与社区关系"),
    ("GRI 204", "采购实践", "procurement_practices", 73, "chunk_6bca4a60cd18caaec91a6a7d", "可持续供应链管理"),
    ("GRI 205", "反腐败", "anti_corruption", 73, "chunk_6bca4a60cd18caaec91a6a7d", "商业道德行为"),
    ("GRI 206", "反竞争行为", "anti_competitive_behavior", 73, "chunk_6bca4a60cd18caaec91a6a7d", "商业道德行为"),
    ("GRI 207", "税务", "tax", 73, "chunk_6bca4a60cd18caaec91a6a7d", "公司治理"),
    ("GRI 301", "物料", "materials", 73, "chunk_6bca4a60cd18caaec91a6a7d", "循环经济"),
    ("GRI 302", "能源", "energy", 73, "chunk_6bca4a60cd18caaec91a6a7d", "能源管理"),
    ("GRI 303", "水资源和污水", "water_and_effluents", 74, "chunk_9a93636fdb98fdb67025ba3b", "水资源管理"),
    ("GRI 304", "生物多样性", "biodiversity", 74, "chunk_9a93636fdb98fdb67025ba3b", "生物多样性与土地利用"),
    ("GRI 305", "排放", "emissions", 74, "chunk_9a93636fdb98fdb67025ba3b", "应对气候变化"),
    ("GRI 306", "废弃物", "waste", 74, "chunk_9a93636fdb98fdb67025ba3b", "废弃物管理"),
    ("GRI 308", "供应商环境评估", "supplier_environmental_assessment", 75, "chunk_fba438acfe0779de7ea1095e", "可持续供应链管理"),
    ("GRI 401", "雇佣", "employment", 75, "chunk_fba438acfe0779de7ea1095e", "人力资本发展"),
    ("GRI 402", "劳资关系", "labor_management_relations", 75, "chunk_fba438acfe0779de7ea1095e", "劳工与人权"),
    ("GRI 403", "职业健康与安全", "occupational_health_and_safety", 75, "chunk_fba438acfe0779de7ea1095e", "职业健康与安全"),
    ("GRI 404", "培训与教育", "training_and_education", 75, "chunk_fba438acfe0779de7ea1095e", "人力资本发展"),
    ("GRI 405", "多元化与平等机会", "diversity_and_equal_opportunity", 75, "chunk_fba438acfe0779de7ea1095e", "劳工与人权"),
    ("GRI 406", "反歧视", "non_discrimination", 76, "chunk_83b9331d62b6d81a81d62f67", "劳工与人权"),
    ("GRI 407", "结社自由与集体谈判", "freedom_of_association_and_collective_bargaining", 76, "chunk_83b9331d62b6d81a81d62f67", "劳工与人权"),
    ("GRI 408", "童工", "child_labor", 76, "chunk_83b9331d62b6d81a81d62f67", "劳工与人权"),
    ("GRI 409", "强迫或强制劳动", "forced_or_compulsory_labor", 76, "chunk_83b9331d62b6d81a81d62f67", "劳工与人权"),
    ("GRI 410", "安保实践", "security_practices", 76, "chunk_83b9331d62b6d81a81d62f67", "劳工与人权"),
    ("GRI 413", "当地社区", "local_communities", 76, "chunk_83b9331d62b6d81a81d62f67", "社会经济贡献与社区关系"),
    ("GRI 414", "供应商社会评估", "supplier_social_assessment", 76, "chunk_83b9331d62b6d81a81d62f67", "可持续供应链管理"),
    ("GRI 416", "客户健康与安全", "customer_health_and_safety", 76, "chunk_83b9331d62b6d81a81d62f67", "产品质量与安全"),
    ("GRI 417", "营销与标识", "marketing_and_labeling", 76, "chunk_83b9331d62b6d81a81d62f67", "产品质量与安全"),
    ("GRI 418", "客户隐私", "customer_privacy", 76, "chunk_83b9331d62b6d81a81d62f67", "数据安全与隐私保护"),
]


def _load_json(path: Path) -> Any:
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


def _topic_lookup(topic_scope_path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(topic_scope_path)
    return {
        str(topic["topic_name_zh"]): topic
        for topic in payload.get("topic_instances", [])
        if isinstance(topic, dict) and topic.get("topic_name_zh")
    }


def _standard_slug(standard_id: str) -> str:
    return standard_id.replace(" ", "").lower()


def _requirement_checks(manifest_item_id: str) -> list[dict[str, Any]]:
    checks = []
    for suffix, text in GRI_3_3_REQUIREMENTS:
        checks.append(
            {
                "requirement_id": f"{manifest_item_id}:{suffix}",
                "requirement_text": text,
                "is_mandatory": True,
                "conditional": False,
                "condition_text": "",
                "support_status": "not_assessed",
                "supporting_evidence_ids": [],
                "missing_reason": "",
                "manual_review_reason": (
                    "Pending authorized E3.5 GRI-index-row 3-3 LLM assessment and human smoke review."
                ),
            }
        )
    return checks


def _evidence(
    *,
    evidence_id: str,
    evidence_kind: str,
    evidence_subtype: str,
    chunk: dict[str, Any],
    report_page_label: str,
    relevance: float,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_document": REPORT_PATH,
        "source_page": chunk.get("pdf_page"),
        "report_page_label": report_page_label,
        "source_text": str(chunk.get("text", "")).strip(),
        "relevance": relevance,
        "evidence_kind": evidence_kind,
        "evidence_subtype": evidence_subtype,
        "supports_requirement_ids": [],
        "source_section": "GRI 指标索引" if evidence_kind == "index_evidence" else "重要性评估",
        "judgment_reason": (
            "Locator and mapping evidence only. It does not by itself support Disclosure 3-3 as met."
        ),
        "corpus_id": "envision_energy_2024_zh",
        "chunk_id": chunk.get("chunk_id"),
        "extraction_method": "stage_e3_5_index_row_instantiation",
        "source_document_sha256": REPORT_SHA256,
        "company": chunk.get("company", "Envision Energy"),
        "report_year": chunk.get("report_year", 2024),
        "industry": chunk.get("industry", "renewable_energy"),
        "topic": "gri_3_3_index_row_instantiation",
        "source_text_extraction_warning": None,
        "retrieval_method": "report_gri_index_row_scope",
    }


def _scope_payload(chunks: dict[str, dict[str, Any]], topic_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    instances = []
    for index, (standard_id, standard_title_zh, slug, pdf_page, chunk_id, materiality_topic) in enumerate(INDEX_INSTANCES, 1):
        topic = topic_lookup.get(materiality_topic, {})
        instances.append(
            {
                "instance_order": index,
                "instance_id": f"gri_3_3_index_{_standard_slug(standard_id)}",
                "manifest_item_id": f"current_gap:{standard_id.replace(' ', '')}:3-3",
                "standard_id": standard_id,
                "standard_title_zh": standard_title_zh,
                "canonical_disclosure_id": "3-3",
                "index_source_page": pdf_page,
                "index_report_page_label": str(pdf_page - 1),
                "index_source_chunk_id": chunk_id,
                "index_chunk_available": chunk_id in chunks,
                "mapped_materiality_topic_zh": materiality_topic,
                "mapped_materiality_topic_instance_id": topic.get("topic_instance_id"),
                "mapped_materiality_topic_slug": topic.get("topic_name_en_slug"),
                "requires_llm_assessment": True,
                "initial_status": "pending_llm_assessment",
            }
        )
    return {
        "document_version": "p0_stage_e3_5_gri_3_3_index_instance_scope_v1",
        "recorded_at": "2026-06-30",
        "stage": "E3.5",
        "scope": "gri_3_3_index_row_instances_for_2024_current_disclosure",
        "status": "draft_pending_deepseek_authorized_assessment",
        "scope_policy": {
            "final_current_assessment_unit_policy": (
                "Use report GRI index row granularity for Disclosure 3-3 instances. "
                "The 16 materiality-topic draft is retained as a topic aggregation and crosswalk reference."
            ),
            "ordinary_current_gap_count": 114,
            "gri_3_3_instance_count": 29,
            "expected_final_current_assessment_units": 143,
            "unified_final_advisor_status": "paused_until_gri_3_3_effective_assessments_are_available",
        },
        "inputs": {
            "report_evidence_index": str(DEFAULT_EVIDENCE_INDEX.relative_to(PROJECT_ROOT)),
            "materiality_topic_scope": str(DEFAULT_TOPIC_SCOPE.relative_to(PROJECT_ROOT)),
        },
        "instances": instances,
    }


def _assessment(instance: dict[str, Any], chunks: dict[str, dict[str, Any]], topic_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    manifest_item_id = instance["manifest_item_id"]
    standard_slug = _standard_slug(instance["standard_id"])
    index_chunk = chunks[str(instance["index_source_chunk_id"])]
    mapped_topic = topic_lookup.get(str(instance["mapped_materiality_topic_zh"]), {})
    evidence_items = [
        _evidence(
            evidence_id=f"evidence_e3_5_index_3_3_{standard_slug}_index",
            evidence_kind="index_evidence",
            evidence_subtype="gri_index_3_3_row",
            chunk=index_chunk,
            report_page_label=instance["index_report_page_label"],
            relevance=0.8,
        )
    ]
    topic_chunk_id = str(mapped_topic.get("source_chunk_id", ""))
    if topic_chunk_id in chunks:
        evidence_items.append(
            _evidence(
                evidence_id=f"evidence_e3_5_index_3_3_{standard_slug}_materiality_topic",
                evidence_kind="substantive_report_evidence",
                evidence_subtype="materiality_topic_mapping",
                chunk=chunks[topic_chunk_id],
                report_page_label=str(mapped_topic.get("report_page_label", "")),
                relevance=0.55,
            )
        )

    checks = _requirement_checks(manifest_item_id)
    requirement_ids = [check["requirement_id"] for check in checks]
    return {
        "assessment_id": f"assessment_e3_5_index_3_3_{standard_slug}",
        "manifest_item_id": manifest_item_id,
        "standard_id": instance["standard_id"],
        "standard_year": "",
        "canonical_disclosure_id": "3-3",
        "canonical_status": "confirmed_from_report_index",
        "assessment_mode": "current_gap",
        "verdict": "manual_review",
        "confidence": 0.0,
        "evidence": evidence_items,
        "requirement_checks": checks,
        "missing_requirements": [],
        "partial_requirements": [],
        "not_applicable_requirements": [],
        "manual_review_requirements": requirement_ids,
        "aggregation_reason": (
            "Disclosure 3-3 instance was created from the report GRI index row. "
            "No authorized requirement-level assessment has been run yet."
        ),
        "rationale": (
            f"{instance['standard_id']} {instance['standard_title_zh']} has a Disclosure 3-3 row in the report GRI index. "
            f"It is cross-mapped to the materiality topic '{instance['mapped_materiality_topic_zh']}' for later aggregation."
        ),
        "recommendation": "Run the authorized E3.5 3-3 LLM assessment before final scoring or final advisor generation.",
        "manual_review_reason_codes": ["additional_evidence_needed"],
        "readiness_verdict": None,
        "not_scored_reason": "pending_e3_5_index_row_3_3_llm_assessment",
        "review_status": "pending",
    }


def build_index_3_3_assessments(
    *,
    evidence_index_path: Path = DEFAULT_EVIDENCE_INDEX,
    topic_scope_path: Path = DEFAULT_TOPIC_SCOPE,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    scope_output_path: Path = DEFAULT_SCOPE_OUTPUT,
) -> dict[str, Any]:
    chunks = _chunk_lookup(evidence_index_path)
    topics = _topic_lookup(topic_scope_path)
    scope = _scope_payload(chunks, topics)
    if len(scope["instances"]) != 29:
        raise ValueError(f"Expected 29 GRI 3-3 index instances, got {len(scope['instances'])}")
    missing_chunks = [item for item in scope["instances"] if not item["index_chunk_available"]]
    if missing_chunks:
        raise ValueError(f"Missing index chunks for instances: {missing_chunks}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_e3_5_gri3_3_index_instantiation")
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    assessments = [_assessment(instance, chunks, topics) for instance in scope["instances"]]
    analyst_result = {
        "p0_contract_version": "p0_stage_e3_5_index_3_3_instantiation_v1",
        "disclosure_assessments": assessments,
        "overall_assessment": (
            "Disclosure 3-3 has been instantiated at report GRI-index-row granularity: "
            "29 topic-specific GRI Standard instances. All remain pending authorized LLM assessment."
        ),
        "summary": {
            "run_mode": "stage_e3_5_gri_3_3_index_row_instantiation",
            "ordinary_current_gap_count": 114,
            "gri_3_3_instance_count": len(assessments),
            "expected_final_current_assessment_units": 143,
            "llm_called": False,
            "status": "instantiated_pending_authorized_llm_assessment",
        },
        "raw_llm_output": "",
        "status": "completed_without_llm",
    }
    analysis_run = AnalysisRun.model_validate(
        {
            "run_id": run_id,
            "report_id": "envision_energy_2024_zh",
            "standard_profile_id": "gri_p0_2024_current_disclosure_v1",
            "manifest_version": "p0_stage_e3_5_index_3_3_instantiation_v1",
            "status": AnalysisRunStatus.COMPLETED.value,
            "completed_at": _now_iso(),
            "source_documents": [doc.model_dump(mode="json") for doc in load_p0_source_documents()],
            "assessments": assessments,
            "summary": analyst_result["summary"],
        }
    )
    stage_gate = {
        "document_version": "p0_stage_e3_5_index_3_3_stage_gate_result_v1",
        "recorded_at": _now_iso(),
        "run_id": run_id,
        "gate_status": "index_row_instances_prepared_pending_authorized_llm_assessment",
        "ordinary_current_gap_count": 114,
        "gri_3_3_instance_count": len(assessments),
        "expected_final_current_assessment_units": 143,
        "llm_called": False,
        "unified_final_advisor_status": "paused_until_gri_3_3_effective_assessments_are_available",
    }
    run_summary = {
        "status": "ok",
        "run_id": run_id,
        "run_mode": "stage_e3_5_gri_3_3_index_row_instantiation",
        "run_dir": str(run_dir),
        "assessment_count": len(assessments),
        "ordinary_current_gap_count": 114,
        "expected_final_current_assessment_units": 143,
        "llm_called": False,
        "errors": [],
        "warnings": [
            "This is an instantiation artifact only; it must not be used as final GRI 3-3 scoring output.",
            "The previous 16-topic materiality scope is retained only as an aggregation crosswalk.",
        ],
    }

    _write_json(scope_output_path, scope)
    _write_json(run_dir / "index_instance_scope.json", scope)
    _write_json(run_dir / "analyst_result.json", analyst_result)
    _write_json(run_dir / "analysis_run.json", analysis_run.model_dump(mode="json"))
    _write_json(run_dir / "manual_review_input.json", _manual_review_input(analysis_run))
    _write_json(run_dir / "stage_gate_result.json", stage_gate)
    _write_json(run_dir / "run_summary.json", run_summary)

    result = {
        "status": "ok",
        "run_id": run_id,
        "run_dir": str(run_dir),
        "gri_3_3_instance_count": len(assessments),
        "expected_final_current_assessment_units": 143,
        "llm_called": False,
        "scope_output": str(scope_output_path),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build E3.5 GRI-index-row Disclosure 3-3 instances.")
    parser.add_argument("--evidence-index", type=Path, default=DEFAULT_EVIDENCE_INDEX)
    parser.add_argument("--topic-scope", type=Path, default=DEFAULT_TOPIC_SCOPE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scope-output", type=Path, default=DEFAULT_SCOPE_OUTPUT)
    args = parser.parse_args(argv)
    build_index_3_3_assessments(
        evidence_index_path=args.evidence_index,
        topic_scope_path=args.topic_scope,
        output_dir=args.output_dir,
        scope_output_path=args.scope_output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
