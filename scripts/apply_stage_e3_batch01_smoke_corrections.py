"""Apply audited smoke-review corrections for Stage E3 batch 01.

This script preserves raw LLM artifacts and writes corrected artifacts next to
them:
- smoke_review_result.json
- analyst_result_corrected.json
- analysis_run_corrected.json
- stage_gate_result.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_p0_stage_e1_real_run import _write_json  # noqa: E402
from src.models.analysis_contract import AnalysisRun  # noqa: E402

DEFAULT_RUN_DIR = PROJECT_ROOT / "data" / "runs" / "stage_e" / "20260630T021253Z_e3_batch_01_gri2"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _assessment_by_id(assessments: list[dict[str, Any]], manifest_item_id: str) -> dict[str, Any]:
    for assessment in assessments:
        if assessment.get("manifest_item_id") == manifest_item_id:
            return assessment
    raise ValueError(f"assessment not found: {manifest_item_id}")


def _check_by_id(assessment: dict[str, Any], requirement_id: str) -> dict[str, Any]:
    for check in assessment.get("requirement_checks", []) or []:
        if check.get("requirement_id") == requirement_id:
            return check
    raise ValueError(f"requirement check not found: {assessment.get('manifest_item_id')} {requirement_id}")


def _upsert_evidence(assessment: dict[str, Any], evidence: dict[str, Any]) -> None:
    evidence_items = assessment.setdefault("evidence", [])
    for index, item in enumerate(evidence_items):
        if item.get("evidence_id") == evidence["evidence_id"]:
            evidence_items[index] = evidence
            return
    evidence_items.append(evidence)


def _remove_from_list(values: list[str], *items: str) -> list[str]:
    remove = set(items)
    return [value for value in values if value not in remove]


def _apply_2_22(assessment: dict[str, Any]) -> None:
    snippets = {
        "evidence_7e5df366b4b24eccbb5beb58f889d250": (
            "作为一家致力于长期价值创造的绿色科技企业，我们深知ESG\n"
            "不仅是全球趋势，更是驱动企业高质量发展\n"
            "的核心动力。"
        ),
        "evidence_9f844f286f27454bb1e038f19df52a6d": (
            "可持续发展不是选择题，而是必答题。远景\n"
            "将继续以技术为引擎、以全球合作为纽带，\n"
            "深化可持续发展战略，与各方伙伴共同应对\n"
            "气候挑战，共创繁荣、可持续的未来。"
        ),
    }
    for evidence in assessment.get("evidence", []) or []:
        evidence_id = evidence.get("evidence_id")
        if evidence_id in snippets:
            evidence["source_text"] = snippets[evidence_id]
            evidence["source_text_extraction_warning"] = None
    assessment["aggregation_reason"] = "人工 smoke review 修正：source_text 已替换为 PDF 可定位逐字短片段。"


def _apply_2_1(assessment: dict[str, Any]) -> None:
    legal_name_evidence = assessment["evidence"][0]
    supports = set(legal_name_evidence.get("supports_requirement_ids", []))
    supports.add("current_gap:GRI2:2-1:b")
    legal_name_evidence["supports_requirement_ids"] = sorted(supports)
    legal_name_evidence["judgment_reason"] = "披露了法定名称；“有限公司”可部分支持法律形式，但未披露所有权性质。"

    headquarters_evidence_id = "evidence_manual_smoke_2_1_headquarters"
    _upsert_evidence(
        assessment,
        {
            "evidence_id": headquarters_evidence_id,
            "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
            "source_page": 28,
            "report_page_label": "27",
            "source_text": "上海总部大楼智能楼宇项目提升能源效率\n远景能源在上海总部大楼实施智能楼宇项目",
            "relevance": 0.65,
            "evidence_kind": "substantive_report_evidence",
            "evidence_subtype": "manual_smoke_review_correction",
            "supports_requirement_ids": ["current_gap:GRI2:2-1:c"],
            "source_section": "绿色办公",
            "judgment_reason": "报告提及上海总部大楼，可间接支持总部所在地，但未明确披露完整总部地址。",
            "corpus_id": None,
            "chunk_id": "chunk_69b04e4bd7cb562808d02317",
            "extraction_method": "manual_smoke_review",
            "source_document_sha256": "57360DCDA8E6256726BE5D2A49F8921E13187B40AE44661549903F702DF38068",
            "company": "Envision Energy",
            "report_year": 2024,
            "industry": "renewable_energy",
            "topic": "general",
            "source_text_extraction_warning": None,
            "retrieval_method": "manual_smoke_review",
        },
    )

    check_b = _check_by_id(assessment, "current_gap:GRI2:2-1:b")
    check_b["support_status"] = "partially_met"
    check_b["supporting_evidence_ids"] = [legal_name_evidence["chunk_id"]]
    check_b["missing_reason"] = "“有限公司”可部分支持法律形式，但未披露所有权性质。"

    check_c = _check_by_id(assessment, "current_gap:GRI2:2-1:c")
    check_c["support_status"] = "partially_met"
    check_c["supporting_evidence_ids"] = ["chunk_69b04e4bd7cb562808d02317"]
    check_c["missing_reason"] = "报告提及上海总部大楼，但未明确披露完整总部所在地。"

    check_d = _check_by_id(assessment, "current_gap:GRI2:2-1:d")
    check_d["support_status"] = "not_met"
    check_d["supporting_evidence_ids"] = []
    check_d["missing_reason"] = "未披露经营国家清单。"

    assessment["missing_requirements"] = ["current_gap:GRI2:2-1:d"]
    assessment["partial_requirements"] = ["current_gap:GRI2:2-1:b", "current_gap:GRI2:2-1:c"]
    assessment["aggregation_reason"] = "人工 smoke review 修正：2-1-b/c 为部分支持，2-1-d 仍缺失。"
    assessment["rationale"] = "法定名称已披露；法律形式和总部所在地仅有部分或间接支持；经营国家清单未披露。"


def _apply_2_6(assessment: dict[str, Any]) -> None:
    for evidence in assessment.get("evidence", []) or []:
        if evidence.get("evidence_id") == "evidence_efd78d872c9b4652a9b01b5202eb96f7":
            evidence["source_page"] = 9
            evidence["report_page_label"] = "8"
            evidence["source_text"] = (
                "远景能源加入联合国全球契约组织\n"
                "（UNGC），承诺支持全球契约关于人权、\n"
                "劳工、环境和反腐败四个领域的十项原则，\n"
                "积极参与促进联合国可持续发展目标的合\n"
                "作项目。"
            )
            evidence["supports_requirement_ids"] = []
            evidence["judgment_reason"] = "页码经 smoke review 修正；该证据仅作 ESG 合作网络背景，不作为 2-6-c 主要支持。"

    _upsert_evidence(
        assessment,
        {
            "evidence_id": "evidence_manual_smoke_2_6_supply_chain",
            "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
            "source_page": 52,
            "report_page_label": "51",
            "source_text": (
                "远景能源致力于实施负责任、可持续的采购，\n"
                "积极响应全球公认的倡议、准则，通过数字\n"
                "化、智能化、体系化等多种途径和手段，充\n"
                "分加强供应链的可溯性与透明度"
            ),
            "relevance": 0.75,
            "evidence_kind": "substantive_report_evidence",
            "evidence_subtype": "manual_smoke_review_correction",
            "supports_requirement_ids": ["current_gap:GRI2:2-6:b:ii"],
            "source_section": "责任采购，产业共荣",
            "judgment_reason": "部分支持供应链披露，但未形成完整价值链结构说明。",
            "corpus_id": None,
            "chunk_id": "chunk_e5c3b8538eb07621c5d069cc",
            "extraction_method": "manual_smoke_review",
            "source_document_sha256": "57360DCDA8E6256726BE5D2A49F8921E13187B40AE44661549903F702DF38068",
            "company": "Envision Energy",
            "report_year": 2024,
            "industry": "renewable_energy",
            "topic": "supplier_management",
            "source_text_extraction_warning": None,
            "retrieval_method": "manual_smoke_review",
        },
    )
    _upsert_evidence(
        assessment,
        {
            "evidence_id": "evidence_manual_smoke_2_6_business_relationships",
            "source_document": "data/knowledge_base/peer_reports/Envision Energy 2024-zh.pdf",
            "source_page": 4,
            "report_page_label": "3",
            "source_text": (
                "在交通领域，我们与全球物流巨头DHL集\n"
                "团签署战略备忘录，提供可持续航空燃料\n"
                "（SAF）、绿色电力和零碳产业园解决方案，\n"
                "加速航空脱碳进程。在能源和化工领域，与\n"
                "西班牙政府合作"
            ),
            "relevance": 0.8,
            "evidence_kind": "substantive_report_evidence",
            "evidence_subtype": "manual_smoke_review_correction",
            "supports_requirement_ids": ["current_gap:GRI2:2-6:c"],
            "source_section": "董事长致辞",
            "judgment_reason": "披露部分客户、物流和政府合作关系，可部分支持其他业务关系。",
            "corpus_id": None,
            "chunk_id": "chunk_206cfc7403ae3a5cde39c9f2",
            "extraction_method": "manual_smoke_review",
            "source_document_sha256": "57360DCDA8E6256726BE5D2A49F8921E13187B40AE44661549903F702DF38068",
            "company": "Envision Energy",
            "report_year": 2024,
            "industry": "renewable_energy",
            "topic": "general",
            "source_text_extraction_warning": None,
            "retrieval_method": "manual_smoke_review",
        },
    )

    check_b = _check_by_id(assessment, "current_gap:GRI2:2-6:b")
    check_b["support_status"] = "partially_met"
    check_b["supporting_evidence_ids"] = ["chunk_daf4347b908c17deba8980b9", "chunk_e5c3b8538eb07621c5d069cc"]
    check_b["missing_reason"] = "披露了业务活动和供应链管理片段，但未系统描述完整价值链。"

    check_bii = _check_by_id(assessment, "current_gap:GRI2:2-6:b:ii")
    check_bii["support_status"] = "partially_met"
    check_bii["supporting_evidence_ids"] = ["chunk_e5c3b8538eb07621c5d069cc"]
    check_bii["missing_reason"] = "披露供应链管理框架和可持续采购，但未完整描述供应链结构。"

    check_c = _check_by_id(assessment, "current_gap:GRI2:2-6:c")
    check_c["support_status"] = "partially_met"
    check_c["supporting_evidence_ids"] = ["chunk_206cfc7403ae3a5cde39c9f2"]
    check_c["missing_reason"] = "披露部分客户、DHL 和西班牙政府合作关系，但不是完整业务关系清单。"

    assessment["missing_requirements"] = ["current_gap:GRI2:2-6:b:iii", "current_gap:GRI2:2-6:d"]
    assessment["partial_requirements"] = [
        "current_gap:GRI2:2-6:b",
        "current_gap:GRI2:2-6:b:ii",
        "current_gap:GRI2:2-6:c",
    ]
    assessment["aggregation_reason"] = "人工 smoke review 修正：业务活动披露充分，供应链和其他业务关系部分披露，下游实体和重大变化缺失。"
    assessment["rationale"] = "报告披露主要业务活动、供应链管理片段和部分合作关系；未完整披露下游实体及报告期重大变化。"


def _apply_2_8(assessment: dict[str, Any]) -> None:
    assessment["verdict"] = "not_disclosed"
    assessment["manual_review_requirements"] = []
    assessment["manual_review_reason_codes"] = []
    assessment["aggregation_reason"] = "人工 smoke review 修正：合理检索后未找到 GRI 2-8 所需非员工工作者数量、类型、方法和波动披露。"
    assessment["rationale"] = "报告中的外部供方安全和供应商管理内容不能替代 GRI 2-8 对非员工工作者数量、类型、合同关系、工作类型、统计方法和波动说明的披露要求。"
    for check in assessment.get("requirement_checks", []) or []:
        check["support_status"] = "not_met"
        check["supporting_evidence_ids"] = []
        check["manual_review_reason"] = ""
    assessment["review_status"] = "pending"


def _apply_batch_wide_verbatim_fixes(assessments: list[dict[str, Any]]) -> None:
    fixes: dict[tuple[str, str], dict[str, Any]] = {
        (
            "current_gap:GRI2:2-2",
            "evidence_4e7d078ed5454a48b4224d65bc1fdfba",
        ): {
            "source_text": (
                "本报告覆盖公司2024年1月1日至12月31\n"
                "日（以下简称“报告期”）期间的信息和数据，\n"
                "部分信息和数据追溯到2023年及之前、或\n"
                "延伸至2025年。报告边界包含远景能源所\n"
                "有实际运营场所。"
            ),
        },
        (
            "current_gap:GRI2:2-3",
            "evidence_deb4409b424f4a9ba67442f78f70753a",
        ): {
            "source_text": (
                "本报告覆盖公司2024年1月1日至12月31\n"
                "日（以下简称“报告期”）期间的信息和数据，\n"
                "部分信息和数据追溯到2023年及之前、或\n"
                "延伸至2025年。\n"
                "如需在线浏览或下载本报告，敬请访问公司\n"
                "官方网站获取报告电子版。\n"
                "E-mail：f_esg_office@envision-energy.com"
            ),
        },
        (
            "current_gap:GRI2:2-13",
            "evidence_3b9634dd9f204709b4e4ab6ceb1f9e31",
        ): {
            "source_text": (
                "ESG办公室是ESG常设管理机构，由CSO\n"
                "直接领导，主要职责包括基于重要性分析确\n"
                "定ESG实质性议题矩阵；洞察全球ESG相关\n"
                "最新理念、法规、行动，预判风险对业务的\n"
                "影响；制定 ESG战略、政策、目标、行动路\n"
                "径及制度"
            ),
        },
        (
            "current_gap:GRI2:2-23",
            "evidence_c4b4410f34484d2a8f5c8aef37c7aa1e",
        ): {
            "source_page": 9,
            "report_page_label": "8",
            "source_text": (
                "远景能源加入联合国全球契约组织\n"
                "（UNGC），承诺支持全球契约关于人权、\n"
                "劳工、环境和反腐败四个领域的十项原则，\n"
                "积极参与促进联合国可持续发展目标的合\n"
                "作项目。"
            ),
        },
        (
            "current_gap:GRI2:2-24",
            "evidence_41bc45a77dd4478686cffb8db0aa490c",
        ): {
            "source_page": 9,
            "report_page_label": "8",
            "source_text": (
                "远景能源加入联合国全球契约组织\n"
                "（UNGC），承诺支持全球契约关于人权、\n"
                "劳工、环境和反腐败四个领域的十项原则，\n"
                "积极参与促进联合国可持续发展目标的合\n"
                "作项目。"
            ),
        },
        (
            "current_gap:GRI2:2-25",
            "evidence_3ccb4f20271442fb8fe26e7b4b130b75",
        ): {
            "source_page": 47,
            "report_page_label": "46",
            "chunk_id": "chunk_1c28d24dd47a8cf7a43aa325",
            "source_text": (
                "远景能源将客户反馈视为企业发展的重要驱动力，积极回应和改进客户反馈，持续提升服务质量，\n"
                "为客户提供卓越的产品和服务体验。我们遵照《客户之声控制程序》政策文件，通过远景之眼\n"
                "（Envision Eye）系统中的客户之声（VoC）在线管理流程，倾听客户声音，了解客户需求，跟\n"
                "进客户反馈问题，不断提升客户满意度，为客户创造更大的价值。"
            ),
        },
        (
            "current_gap:GRI2:2-26",
            "evidence_724412e207174558b9973d813b980696",
        ): {
            "source_text": (
                "员工 • 职业健康与安全 • 合同、培训、员工手册\n"
                "• 劳工与人权 • 公司意见反馈及员工满意度调研\n"
                "• 人力资本发展 • “雅典广场”\n"
                "• 员工委员会"
            ),
        },
        (
            "current_gap:GRI2:2-28",
            "evidence_31e6a3c1d8ca484296b20834709cb450",
        ): {
            "source_page": 9,
            "report_page_label": "8",
            "source_text": (
                "远景能源加入联合国全球契约组织\n"
                "（UNGC），承诺支持全球契约关于人权、\n"
                "劳工、环境和反腐败四个领域的十项原则，\n"
                "积极参与促进联合国可持续发展目标的合\n"
                "作项目。\n"
                "远景能源成为世界经济论坛（WEF）首席\n"
                "执行官气候领袖联盟成员。"
            ),
        },
        (
            "current_gap:GRI2:2-29",
            "evidence_b8b9d7bc7c4645a3a47ed2bbffa57c27",
        ): {
            "source_text": (
                "远景能源系统性识别影响利益相关方的关键议题，通过与利\n"
                "益相关方的常态化沟通精准评估ESG因素对各方的影响情况，\n"
                "有效回应投资者、客户、员工等多元主体的核心诉求，将反\n"
                "馈建议融入公司可持续发展计划和未来业务方针制定的全过\n"
                "程，从而实现企业可持续发展战略与利益相关方期望的高度\n"
                "契合。"
            ),
        },
    }

    for assessment in assessments:
        manifest_item_id = str(assessment.get("manifest_item_id", ""))
        for evidence in assessment.get("evidence", []) or []:
            fix = fixes.get((manifest_item_id, str(evidence.get("evidence_id"))))
            if fix:
                evidence.update(fix)


def _apply_corrections(payload: dict[str, Any], key: str) -> dict[str, Any]:
    corrected = copy.deepcopy(payload)
    assessments = corrected[key]
    _apply_2_22(_assessment_by_id(assessments, "current_gap:GRI2:2-22"))
    _apply_2_1(_assessment_by_id(assessments, "current_gap:GRI2:2-1"))
    _apply_2_6(_assessment_by_id(assessments, "current_gap:GRI2:2-6"))
    _apply_2_8(_assessment_by_id(assessments, "current_gap:GRI2:2-8"))
    _apply_batch_wide_verbatim_fixes(assessments)
    if key == "assessments":
        corrected.setdefault("summary", {})["smoke_review_gate_status"] = "blocked_before_batch_02"
        corrected.setdefault("summary", {})["manual_smoke_corrections_applied"] = True
    return corrected


def _smoke_review_result(run_id: str) -> dict[str, Any]:
    return {
        "review_version": "p0_stage_e3_batch01_smoke_review_result_v1",
        "run_id": run_id,
        "batch_id": "e3_batch_01_gri2",
        "review_status": "completed",
        "gate_status": "blocked_before_batch_02",
        "correction_status": "applied_pending_validation",
        "blocking_reasons": [
            "evidence_page_error",
            "source_text_not_verbatim",
            "verdict_rule_adjustment_required",
        ],
        "items": [
            {
                "manifest_item_id": "current_gap:GRI2:2-22",
                "model_verdict": "disclosed",
                "human_verdict": "disclosed",
                "issue_types": ["source_text_not_verbatim"],
                "review_note": "结论方向合理；source_text 已替换为 PDF 可定位逐字短片段。",
            },
            {
                "manifest_item_id": "current_gap:GRI2:2-1",
                "model_verdict": "partially_disclosed",
                "human_verdict": "partially_disclosed",
                "issue_types": ["requirement_granularity_issue"],
                "review_note": "2-1-b/c 调整为 partial_requirements，2-1-d 保持 missing_requirements。",
            },
            {
                "manifest_item_id": "current_gap:GRI2:2-4",
                "model_verdict": "manual_review",
                "human_verdict": "manual_review",
                "issue_types": ["none_under_current_contract"],
                "review_note": "索引证据不能单独支持 disclosed；保留 manual_review。",
            },
            {
                "manifest_item_id": "current_gap:GRI2:2-6",
                "model_verdict": "partially_disclosed",
                "human_verdict": "partially_disclosed",
                "issue_types": [
                    "evidence_page_error",
                    "evidence_requirement_binding_issue",
                    "requirement_granularity_issue",
                ],
                "review_note": "修正 UNGC 证据页码；补充供应链和业务关系证据；b:ii/c 改为部分支持。",
            },
            {
                "manifest_item_id": "current_gap:GRI2:2-8",
                "model_verdict": "manual_review",
                "human_verdict": "not_disclosed",
                "issue_types": ["wrong_verdict_aggregation", "over_manual_review"],
                "review_note": "无正文证据、无省略说明、无适用性争议时，改为 not_disclosed。",
            },
        ],
    }


def apply_corrections(run_dir: Path) -> dict[str, Any]:
    analyst_result = _load_json(run_dir / "analyst_result.json")
    analysis_run = _load_json(run_dir / "analysis_run.json")
    run_summary = _load_json(run_dir / "run_summary.json")
    run_id = str(run_summary["run_id"])

    corrected_analyst = _apply_corrections(analyst_result, "disclosure_assessments")
    corrected_analysis = _apply_corrections(analysis_run, "assessments")
    AnalysisRun.model_validate(corrected_analysis)

    _write_json(run_dir / "analyst_result_corrected.json", corrected_analyst)
    _write_json(run_dir / "analysis_run_corrected.json", corrected_analysis)
    _write_json(run_dir / "smoke_review_result.json", _smoke_review_result(run_id))
    gate_result = {
        "run_id": run_id,
        "batch_id": "e3_batch_01_gri2",
        "gate_status": "blocked_before_batch_02",
        "blocking_reasons": [
            "evidence_page_error",
            "source_text_not_verbatim",
            "verdict_rule_adjustment_required",
        ],
        "corrected_artifacts": {
            "analyst_result_corrected": str(run_dir / "analyst_result_corrected.json"),
            "analysis_run_corrected": str(run_dir / "analysis_run_corrected.json"),
            "smoke_review_result": str(run_dir / "smoke_review_result.json"),
        },
        "next_gate": "run validators and obtain human confirmation before e3_batch_02_gri3_without_3_3",
    }
    _write_json(run_dir / "stage_gate_result.json", gate_result)
    return gate_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply Stage E3 batch 01 smoke-review field corrections.")
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args(argv)

    result = apply_corrections(args.run_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
