"""
差距分析Agent（对照标准找差距）
核心职责：对照ISSB/HKEX标准，与同行对比，识别披露差距

变化点（v2.0）：
- 不再校验validation_status
- 输入从extract_result改为retrieval_result
- 输出从compliance_notes改为gap_analysis + peer_comparison
- 使用clean_and_parse_json替代validate_json_format
"""

from typing import Dict, Any, List

from src.agent.base_agent import BaseAgent
from src.models.analysis_contract import (
    AssessmentVerdict,
    DisclosureAssessment,
    Evidence,
    EvidenceKind,
    ManualReviewReason,
    RequirementSupportStatus,
)
from src.utils import (
    load_prompt_template,
    load_esg_standards,
    call_llm,
    clean_and_parse_json,
    ValidationException,
)


class AnalystAgent(BaseAgent):
    """差距分析Agent（对照标准+同行对比找差距）"""

    def __init__(self):
        super().__init__(
            agent_name="analyst_agent",
            agent_role="ESG差距分析专家（对照标准找差距，与同行对比找差异）",
        )
        # 加载Prompt模板和ESG标准
        self.analyst_prompt = load_prompt_template("analyst_prompt")
        self.esg_standards = load_esg_standards()

    @staticmethod
    def _context_by_manifest_item(contexts: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        return {
            str(context.get("manifest_item_id")): context
            for context in contexts
            if isinstance(context, dict) and context.get("manifest_item_id")
        }

    @staticmethod
    def _mandatory_requirement_ids(context: Dict[str, Any]) -> List[str]:
        ids: List[str] = []
        for requirement in context.get("requirement_checklist_items", []) or []:
            if not isinstance(requirement, dict) or not requirement.get("requirement_id"):
                continue
            if requirement.get("is_mandatory", True) is False:
                continue
            if requirement.get("scoring_role", "hard_score") != "hard_score":
                continue
            ids.append(str(requirement["requirement_id"]))
        return ids

    @staticmethod
    def _checked_requirement_ids(requirement_checks: List[Dict[str, Any]]) -> set[str]:
        return {
            str(check.get("requirement_id"))
            for check in requirement_checks
            if isinstance(check, dict) and check.get("requirement_id")
        }
    @staticmethod
    def _manual_review_requirement_ids(context: Dict[str, Any]) -> List[str]:
        return AnalystAgent._mandatory_requirement_ids(context) or ["all_applicable_requirements"]

    @staticmethod
    def _hard_score_requirement_id_set(context: Dict[str, Any]) -> set[str]:
        return set(AnalystAgent._mandatory_requirement_ids(context))

    @staticmethod
    def _missing_llm_assessment_payload(context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "manifest_item_id": str(context.get("manifest_item_id", "")),
            "standard_id": str(context.get("standard_id", "")),
            "standard_year": context.get("standard_year"),
            "canonical_disclosure_id": context.get("canonical_disclosure_id"),
            "canonical_status": context.get("canonical_status"),
            "assessment_mode": context.get("analysis_mode", "current_gap"),
            "verdict": AssessmentVerdict.MANUAL_REVIEW.value,
            "confidence": 0.0,
            "evidence": [],
            "requirement_checks": [],
            "missing_requirements": [],
            "manual_review_requirements": AnalystAgent._manual_review_requirement_ids(context),
            "aggregation_reason": "missing_llm_assessment_for_manifest_item",
            "manual_review_reason_codes": [ManualReviewReason.MISSING_LLM_ASSESSMENT_FOR_MANIFEST_ITEM.value],
            "rationale": "Guardrail: missing_llm_assessment_for_manifest_item",
            "review_status": "pending",
        }

    @staticmethod
    def _chunk_lookup(context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        chunks: Dict[str, Dict[str, Any]] = {}
        for chunk in context.get("report_evidence_chunks", []) or []:
            if isinstance(chunk, dict) and chunk.get("chunk_id"):
                chunks[str(chunk["chunk_id"])] = chunk
        bundle = context.get("evidence_bundle", {}) or {}
        if isinstance(bundle, dict):
            for evidence_items in bundle.values():
                if not isinstance(evidence_items, list):
                    continue
                for chunk in evidence_items:
                    if isinstance(chunk, dict) and chunk.get("chunk_id"):
                        chunks[str(chunk["chunk_id"])] = chunk
        return chunks


    @staticmethod
    def _manual_review_reason_code(reason: str) -> str:
        mapping = {
            "needs_topic_instantiation": ManualReviewReason.NEEDS_TOPIC_INSTANTIATION.value,
            "omission_reason_requires_review": ManualReviewReason.OMISSION_REASON_REQUIRES_REVIEW.value,
            "missing_llm_assessment_for_manifest_item": ManualReviewReason.MISSING_LLM_ASSESSMENT_FOR_MANIFEST_ITEM.value,
            "index_evidence_cannot_support_disclosed": ManualReviewReason.INDEX_EVIDENCE_CANNOT_SUPPORT_DISCLOSED.value,
            "not_applicable_requires_explicit_company_explanation": ManualReviewReason.OMISSION_REASON_REQUIRES_REVIEW.value,
            "no_report_evidence_requires_manual_review": ManualReviewReason.ADDITIONAL_EVIDENCE_NEEDED.value,
            "disclosed_requires_requirement_checks": ManualReviewReason.REQUIREMENT_SCOPE_ISSUE.value,
            "partially_disclosed_requires_missing_requirements": ManualReviewReason.REQUIREMENT_SCOPE_ISSUE.value,
            "missing_p0_context": ManualReviewReason.ADDITIONAL_EVIDENCE_NEEDED.value,
        }
        return mapping.get(reason, ManualReviewReason.ADDITIONAL_EVIDENCE_NEEDED.value)

    @staticmethod
    def _add_manual_review_reason_code(item_payload: Dict[str, Any], reason: str) -> None:
        code = AnalystAgent._manual_review_reason_code(reason)
        codes = [str(item) for item in item_payload.get("manual_review_reason_codes", []) or [] if item]
        if code not in codes:
            codes.append(code)
        item_payload["manual_review_reason_codes"] = codes
    @staticmethod
    def _manual_review_payload(item_payload: Dict[str, Any], reason: str) -> None:
        item_payload["verdict"] = AssessmentVerdict.MANUAL_REVIEW.value
        item_payload["confidence"] = min(float(item_payload.get("confidence", 0.0) or 0.0), 0.5)
        item_payload["aggregation_reason"] = reason
        AnalystAgent._add_manual_review_reason_code(item_payload, reason)
        existing = str(item_payload.get("rationale", "")).strip()
        item_payload["rationale"] = f"{existing} Guardrail: {reason}" if existing else f"Guardrail: {reason}"

    def _normalize_evidence_items(
        self,
        evidence_items: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        chunks = self._chunk_lookup(context)
        normalized: List[Dict[str, Any]] = []
        for raw in evidence_items:
            if not isinstance(raw, dict):
                continue
            item = dict(raw)
            chunk = chunks.get(str(item.get("chunk_id"))) if item.get("chunk_id") else None
            if "source_page" not in item and "pdf_page" in item:
                item["source_page"] = item.get("pdf_page")
            if "source_text" not in item and "text" in item:
                item["source_text"] = item.get("text")
            if chunk is not None:
                item.setdefault("source_document", chunk.get("source_document") or chunk.get("source_document_relative_path"))
                item.setdefault("source_page", chunk.get("source_page") or chunk.get("pdf_page"))
                item.setdefault("report_page_label", chunk.get("report_page_label"))
                item.setdefault("source_text", chunk.get("source_text") or chunk.get("text"))
                item.setdefault("source_document_sha256", chunk.get("source_document_sha256"))
                item.setdefault("company", chunk.get("company"))
                item.setdefault("report_year", chunk.get("report_year"))
                item.setdefault("industry", chunk.get("industry"))
                item.setdefault("topic", chunk.get("topic"))
                item.setdefault("evidence_kind", chunk.get("evidence_kind", EvidenceKind.INDEX_EVIDENCE.value))
                item.setdefault("extraction_method", chunk.get("extraction_method", "p0_report_evidence_index"))
                item.setdefault("source_section", chunk.get("source_section"))
                item.setdefault("judgment_reason", chunk.get("judgment_reason", ""))
            item.setdefault("evidence_kind", EvidenceKind.SUBSTANTIVE_REPORT_EVIDENCE.value)
            item.setdefault("supports_requirement_ids", [])
            item.setdefault("judgment_reason", "")
            allowed_fields = set(Evidence.model_fields)
            normalized.append(
                Evidence.model_validate({key: value for key, value in item.items() if key in allowed_fields}).model_dump(
                    mode="json"
                )
            )
        return normalized

    def _apply_p0_guardrails(
        self,
        item_payload: Dict[str, Any],
        context: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        item_payload = dict(item_payload)
        item_payload["review_status"] = "pending"
        if context is None:
            self._manual_review_payload(item_payload, "missing_p0_context")
            return item_payload

        item_payload.setdefault("standard_year", context.get("standard_year"))
        item_payload.setdefault("canonical_status", context.get("canonical_status"))
        if context.get("analysis_mode") == "readiness_2026" and item_payload.get("verdict") == AssessmentVerdict.NOT_APPLICABLE.value:
            item_payload["readiness_verdict"] = context.get("readiness_verdict") or "readiness_gap"
        evidence_items = item_payload.get("evidence", []) or []
        item_payload["evidence"] = self._normalize_evidence_items(evidence_items, context)
        requirement_checks = item_payload.get("requirement_checks", []) or []
        item_payload["requirement_checks"] = requirement_checks
        checklist_ids = [
            str(req.get("requirement_id"))
            for req in context.get("requirement_checklist_items", []) or []
            if isinstance(req, dict) and req.get("requirement_id")
        ]

        if context.get("canonical_disclosure_id") == "3-3_generic":
            item_payload["requirement_checks"] = []
            item_payload["missing_requirements"] = []
            item_payload["partial_requirements"] = []
            item_payload["not_applicable_requirements"] = []
            item_payload["manual_review_requirements"] = ["needs_topic_instantiation"]
            item_payload["not_scored_reason"] = "not_scored_requires_topic_instantiation"
            self._manual_review_payload(item_payload, "needs_topic_instantiation")
            return item_payload

        forced_verdict = context.get("forced_verdict")
        if forced_verdict and item_payload.get("verdict") != forced_verdict:
            item_payload["verdict"] = forced_verdict
            item_payload["aggregation_reason"] = f"forced_verdict_applied: {context.get('policy_reason', '')}"

        if context.get("analysis_mode") == "readiness_2026" and item_payload.get("verdict") == AssessmentVerdict.NOT_APPLICABLE.value:
            item_payload["readiness_verdict"] = context.get("readiness_verdict") or "readiness_gap"

        is_policy_excluded_from_current_gap = (
            context.get("can_score_current_gap") is False
            and context.get("analysis_mode") != "current_gap"
            and item_payload.get("verdict") == AssessmentVerdict.NOT_APPLICABLE.value
        )
        if is_policy_excluded_from_current_gap:
            item_payload["aggregation_reason"] = item_payload.get("aggregation_reason") or str(
                context.get("policy_reason", "")
            )
            return item_payload

        if (
            context.get("analysis_mode") == "current_gap"
            and not item_payload["evidence"]
            and item_payload.get("verdict") != AssessmentVerdict.MANUAL_REVIEW.value
        ):
            item_payload["manual_review_requirements"] = self._manual_review_requirement_ids(context)
            self._manual_review_payload(item_payload, "no_report_evidence_requires_manual_review")
            return item_payload

        if item_payload.get("verdict") == AssessmentVerdict.NOT_APPLICABLE.value:
            has_explanation = any(
                evidence.get("evidence_kind") == EvidenceKind.OMISSION_OR_NOT_APPLICABLE_EXPLANATION.value
                for evidence in item_payload["evidence"]
            )
            if not has_explanation:
                item_payload["not_applicable_requirements"] = checklist_ids or item_payload.get("not_applicable_requirements", [])
                self._manual_review_payload(item_payload, "not_applicable_requires_explicit_company_explanation")
                return item_payload
            if context.get("analysis_mode") == "current_gap":
                item_payload["manual_review_requirements"] = item_payload.get("manual_review_requirements") or checklist_ids
                self._manual_review_payload(item_payload, "omission_reason_requires_review")
                return item_payload
            item_payload["manual_review_requirements"] = item_payload.get("manual_review_requirements") or checklist_ids
            item_payload["review_status"] = "pending"

        if item_payload.get("verdict") == AssessmentVerdict.DISCLOSED.value:
            if not requirement_checks:
                item_payload["manual_review_requirements"] = self._manual_review_requirement_ids(context)
                self._manual_review_payload(item_payload, "disclosed_requires_requirement_checks")
                return item_payload
            if not item_payload["evidence"] or all(
                evidence.get("evidence_kind") == EvidenceKind.INDEX_EVIDENCE.value
                for evidence in item_payload["evidence"]
            ):
                item_payload["manual_review_requirements"] = self._manual_review_requirement_ids(context)
                self._manual_review_payload(item_payload, "index_evidence_cannot_support_disclosed")
                return item_payload

            missing_mandatory_checks = [
                requirement_id
                for requirement_id in self._mandatory_requirement_ids(context)
                if requirement_id not in self._checked_requirement_ids(requirement_checks)
            ]
            if missing_mandatory_checks:
                item_payload["verdict"] = AssessmentVerdict.PARTIALLY_DISCLOSED.value
                item_payload["missing_requirements"] = sorted(
                    set(item_payload.get("missing_requirements", []) or []) | set(missing_mandatory_checks)
                )
                item_payload["aggregation_reason"] = "mandatory_requirement_checks_missing"

            hard_score_ids = self._hard_score_requirement_id_set(context)
            partially_met = [
                str(check.get("requirement_id"))
                for check in requirement_checks
                if str(check.get("requirement_id")) in hard_score_ids
                and check.get("support_status") == RequirementSupportStatus.PARTIALLY_MET.value
            ]
            unmet = [
                check.get("requirement_id")
                for check in requirement_checks
                if str(check.get("requirement_id")) in hard_score_ids
                and check.get("support_status")
                in {
                    RequirementSupportStatus.NOT_MET.value,
                    RequirementSupportStatus.NOT_ASSESSED.value,
                    RequirementSupportStatus.MANUAL_REVIEW.value,
                }
            ]
            if partially_met:
                item_payload["partial_requirements"] = sorted(
                    set(item_payload.get("partial_requirements", []) or []) | {item for item in partially_met if item}
                )
                item_payload["verdict"] = AssessmentVerdict.PARTIALLY_DISCLOSED.value
                item_payload["aggregation_reason"] = "mandatory_requirements_not_all_met"
            if unmet:
                item_payload["verdict"] = AssessmentVerdict.PARTIALLY_DISCLOSED.value
                item_payload["missing_requirements"] = sorted(
                    set(item_payload.get("missing_requirements", []) or []) | {str(item) for item in unmet if item}
                )
                item_payload["aggregation_reason"] = "mandatory_requirements_not_all_met"

        if item_payload.get("verdict") == AssessmentVerdict.PARTIALLY_DISCLOSED.value:
            hard_score_ids = self._hard_score_requirement_id_set(context)
            existing_missing = {
                str(item)
                for item in item_payload.get("missing_requirements", []) or []
                if str(item) in hard_score_ids
            }
            manual_review_ids = {
                str(item)
                for item in item_payload.get("manual_review_requirements", []) or []
                if str(item) in hard_score_ids
            }
            checked_ids = self._checked_requirement_ids(requirement_checks)
            missing_from_checks = {
                str(check.get("requirement_id"))
                for check in requirement_checks
                if str(check.get("requirement_id")) in hard_score_ids
                and check.get("support_status")
                in {
                    RequirementSupportStatus.NOT_MET.value,
                    RequirementSupportStatus.NOT_ASSESSED.value,
                    RequirementSupportStatus.MANUAL_REVIEW.value,
                }
            }
            partial_from_checks = {
                str(check.get("requirement_id"))
                for check in requirement_checks
                if str(check.get("requirement_id")) in hard_score_ids
                and check.get("support_status") == RequirementSupportStatus.PARTIALLY_MET.value
            }
            existing_missing -= partial_from_checks
            uncovered_hard_score_ids = hard_score_ids - checked_ids - existing_missing - manual_review_ids
            item_payload["partial_requirements"] = sorted(
                {
                    str(item)
                    for item in item_payload.get("partial_requirements", []) or []
                    if str(item) in hard_score_ids
                }
                | partial_from_checks
            )
            item_payload["missing_requirements"] = sorted(
                (existing_missing | missing_from_checks | uncovered_hard_score_ids) - set(item_payload["partial_requirements"])
            )
            if (
                not item_payload.get("missing_requirements")
                and not item_payload.get("partial_requirements")
                and not manual_review_ids
            ):
                self._manual_review_payload(item_payload, "partially_disclosed_requires_missing_requirements")

        return item_payload

    def _execute(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行差距分析任务
        :param task_input: 必须包含 retrieval_result 字段
        :return: 差距分析结果 + 同行对比结果
        """
        # 每次执行前热重载ESG标准配置，确保 UI 添加新标准后立即生效
        self.esg_standards = load_esg_standards()

        # 1. 解析任务输入
        retrieval_result = task_input.get("retrieval_result")
        if not retrieval_result:
            raise ValidationException("任务输入缺少必填字段: retrieval_result")

        identified_topics = retrieval_result.get("identified_topics", [])
        retrieved_standards = retrieval_result.get("retrieved_standards", [])
        retrieved_peers = retrieval_result.get("retrieved_peers", [])
        input_text = retrieval_result.get("input_text", "")
        is_p0_branch = "p0_requirement_contexts" in retrieval_result
        p0_requirement_contexts = retrieval_result.get("p0_requirement_contexts", [])

        if not is_p0_branch and not identified_topics:
            self.logger.warning("未识别到任何议题，跳过差距分析")
            return {
                "identified_topics": [],
                "gap_analysis": [],
                "peer_comparison": [],
                "overall_assessment": "未识别到ESG议题，无法进行分析",
                "status": "skipped",
            }

        if is_p0_branch:
            # P0 branch is selected by key presence, so an explicit empty list
            # still renders the P0 schema instead of falling back to legacy analysis.
            self.logger.debug("Building P0 disclosure assessment prompt")
            prompt = self.analyst_prompt.render(
                p0_requirement_contexts=p0_requirement_contexts,
                input_text=input_text,
            )
            messages = [{"role": "user", "content": prompt}]

            self.logger.debug("Calling LLM for P0 disclosure assessment")
            llm_output = call_llm(messages)

            self.logger.debug("Parsing P0 disclosure assessment result")
            analyst_data = clean_and_parse_json(llm_output, logger=self.logger)

            disclosure_assessments = analyst_data.get("disclosure_assessments", [])
            contexts_by_id = self._context_by_manifest_item(p0_requirement_contexts)
            validated_assessments = []
            seen_manifest_item_ids = set()
            for item in disclosure_assessments:
                item_payload = dict(item)
                manifest_item_id = str(item_payload.get("manifest_item_id", ""))
                seen_manifest_item_ids.add(manifest_item_id)
                item_payload = self._apply_p0_guardrails(
                    item_payload,
                    contexts_by_id.get(manifest_item_id),
                )
                validated_assessments.append(
                    DisclosureAssessment.model_validate(item_payload).model_dump(mode="json")
                )

            for manifest_item_id, context in contexts_by_id.items():
                if manifest_item_id in seen_manifest_item_ids:
                    continue
                item_payload = self._apply_p0_guardrails(
                    self._missing_llm_assessment_payload(context),
                    context,
                )
                validated_assessments.append(
                    DisclosureAssessment.model_validate(item_payload).model_dump(mode="json")
                )

            return {
                "p0_contract_version": "p0_stage_d_agent_contract_v1",
                "disclosure_assessments": validated_assessments,
                "overall_assessment": analyst_data.get("overall_assessment", "未生成整体评估"),
                "summary": analyst_data.get("summary", {}),
                "raw_llm_output": llm_output,
                "status": "completed",
            }

        # 2. 构建Prompt
        self.logger.debug("开始构建差距分析Prompt")
        prompt = self.analyst_prompt.render(
            identified_topics=identified_topics,
            retrieved_standards=retrieved_standards,
            retrieved_peers=retrieved_peers,
            input_text=input_text,
        )
        messages = [{"role": "user", "content": prompt}]

        # 3. 调用大模型
        self.logger.debug("开始调用大模型进行差距分析")
        llm_output = call_llm(messages)

        # 4. 宽松解析JSON（替代原来的validate_json_format）
        self.logger.debug("开始解析差距分析结果")
        analyst_data = clean_and_parse_json(llm_output, logger=self.logger)

        # 5. 确保必要字段存在
        if "gap_analysis" not in analyst_data:
            self.logger.warning("LLM输出缺少gap_analysis字段，返回空列表")
            analyst_data["gap_analysis"] = []

        if "peer_comparison" not in analyst_data:
            self.logger.warning("LLM输出缺少peer_comparison字段，返回空列表")
            analyst_data["peer_comparison"] = []

        if "overall_assessment" not in analyst_data:
            analyst_data["overall_assessment"] = "未生成整体评估"

        gap_analysis = analyst_data["gap_analysis"]
        peer_comparison = analyst_data["peer_comparison"]

        # 6. 统计差距分布
        major_count = len([g for g in gap_analysis if g.get("gap_level") == "major"])
        minor_count = len([g for g in gap_analysis if g.get("gap_level") == "minor"])
        none_count = len([g for g in gap_analysis if g.get("gap_level") == "none"])

        # 7. 返回结果
        self.logger.info(
            f"差距分析完成: 重大差距={major_count}, 轻微差距={minor_count}, 无差距={none_count}"
        )

        return {
            "identified_topics": identified_topics,
            "gap_analysis": gap_analysis,
            "peer_comparison": peer_comparison,
            "overall_assessment": analyst_data["overall_assessment"],
            "raw_llm_output": llm_output,
            "analysis_summary": {
                "major_gaps": major_count,
                "minor_gaps": minor_count,
                "no_gaps": none_count,
                "total_topics": len(identified_topics),
            },
            "status": "completed",
        }







