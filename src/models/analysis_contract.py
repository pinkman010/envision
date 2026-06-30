"""
P0 单报告 ESG 分析领域契约。

这些模型用于连接 manifest、Agent 输出、后续持久化、Streamlit 展示和人工复核。
本文件不调用 LLM，不访问数据库，只定义可验证的数据结构。
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalysisMode(str, Enum):
    """P0 分析模式。"""

    CURRENT_GAP = "current_gap"
    READINESS_2026 = "readiness_2026"
    WATCHLIST_2027 = "watchlist_2027"


class CanonicalStatus(str, Enum):
    """披露项编号映射状态。"""

    CONFIRMED_FROM_REPORT_INDEX = "confirmed_from_report_index"
    SOURCE_TYPO_CONFIRMED = "source_typo_confirmed"
    REQUIRES_TOPIC_INSTANTIATION = "requires_topic_instantiation"
    FUTURE_STANDARD_NOT_CURRENT_GAP = "future_standard_not_current_gap"


class AssessmentVerdict(str, Enum):
    """条款级披露判断。"""

    DISCLOSED = "disclosed"
    PARTIALLY_DISCLOSED = "partially_disclosed"
    NOT_DISCLOSED = "not_disclosed"
    NOT_APPLICABLE = "not_applicable"
    MANUAL_REVIEW = "manual_review"



class ManualReviewReason(str, Enum):
    """Structured reason codes for manual review routing."""

    WEAK_EVIDENCE_SUPPORT = "weak_evidence_support"
    ADDITIONAL_EVIDENCE_NEEDED = "additional_evidence_needed"
    OMISSION_REASON_REQUIRES_REVIEW = "omission_reason_requires_review"
    NEEDS_TOPIC_INSTANTIATION = "needs_topic_instantiation"
    SOURCE_TEXT_EXTRACTION_ERROR = "source_text_extraction_error"
    READINESS_ITEM_NEEDS_SEPARATE_VERDICT = "readiness_item_needs_separate_verdict"
    REQUIREMENT_SCOPE_ISSUE = "requirement_scope_issue"
    MISSING_LLM_ASSESSMENT_FOR_MANIFEST_ITEM = "missing_llm_assessment_for_manifest_item"
    INDEX_EVIDENCE_CANNOT_SUPPORT_DISCLOSED = "index_evidence_cannot_support_disclosed"


class ReadinessVerdict(str, Enum):
    """Readiness-specific conclusion outside 2024 current-gap scoring."""

    READINESS_GAP = "readiness_gap"
    READINESS_ALIGNED = "readiness_aligned"
    MANUAL_REVIEW = "manual_review"


class EvidenceKind(str, Enum):
    """Evidence role used by requirement-level disclosure checks."""

    INDEX_EVIDENCE = "index_evidence"
    SUBSTANTIVE_REPORT_EVIDENCE = "substantive_report_evidence"
    OMISSION_OR_NOT_APPLICABLE_EXPLANATION = "omission_or_not_applicable_explanation"
    EXTERNAL_REFERENCE_EVIDENCE = "external_reference_evidence"


class RequirementSupportStatus(str, Enum):
    """Support status for a single leaf requirement."""

    MET = "met"
    PARTIALLY_MET = "partially_met"
    NOT_MET = "not_met"
    NOT_APPLICABLE_CLAIMED = "not_applicable_claimed"
    NOT_ASSESSED = "not_assessed"
    MANUAL_REVIEW = "manual_review"


class ReviewStatus(str, Enum):
    """人工复核状态。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class AnalysisRunStatus(str, Enum):
    """分析任务状态。"""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"


class SourceDocumentRef(BaseModel):
    """原始资料引用。"""

    model_config = ConfigDict(extra="forbid")

    relative_path: str
    document_type: str
    sha256: str
    provenance_status: str


class DisclosureManifestItem(BaseModel):
    """P0 GRI disclosure manifest 中的一行。"""

    model_config = ConfigDict(extra="forbid")

    analysis_mode: AnalysisMode
    manifest_item_id: str
    standard_id: str
    standard_title_zh_or_en: str
    standard_year: str
    source_disclosure_id: Optional[str] = None
    canonical_disclosure_id: Optional[str] = None
    canonical_status: CanonicalStatus
    report_index_pdf_page: Optional[int] = None
    report_index_report_page: Optional[int] = None
    evidence_expectation: str
    notes: str = ""
    effective_date: Optional[str] = None
    related_current_standard: Optional[str] = None

    @field_validator("canonical_disclosure_id")
    @classmethod
    def current_gap_requires_canonical_id(cls, value: Optional[str], info):
        analysis_mode = info.data.get("analysis_mode")
        if analysis_mode == AnalysisMode.CURRENT_GAP and not value:
            raise ValueError("current_gap disclosure must have canonical_disclosure_id")
        return value


class Evidence(BaseModel):
    """报告证据片段。"""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(default_factory=lambda: f"evidence_{uuid4().hex}")
    source_document: str
    source_page: Optional[int] = None
    report_page_label: Optional[str] = None
    source_text: str
    relevance: float = Field(ge=0.0, le=1.0)
    evidence_kind: EvidenceKind = EvidenceKind.SUBSTANTIVE_REPORT_EVIDENCE
    evidence_subtype: Optional[str] = None
    supports_requirement_ids: List[str] = Field(default_factory=list)
    source_section: Optional[str] = None
    judgment_reason: str = ""
    corpus_id: Optional[str] = None
    chunk_id: Optional[str] = None
    extraction_method: str = "retrieval_or_manual"
    source_document_sha256: Optional[str] = None
    company: Optional[str] = None
    report_year: Optional[int] = None
    industry: Optional[str] = None
    topic: Optional[str] = None
    source_text_extraction_warning: Optional[str] = None
    retrieval_method: Optional[str] = None
class RequirementCheck(BaseModel):
    """Assessment result for one leaf requirement."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    requirement_text: str
    is_mandatory: bool
    conditional: bool = False
    condition_text: str = ""
    support_status: RequirementSupportStatus
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    missing_reason: str = ""
    manual_review_reason: str = ""

    @field_validator("requirement_id", "requirement_text")
    @classmethod
    def requirement_text_fields_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("requirement check text fields must not be empty")
        return value


class DisclosureAssessment(BaseModel):
    """单个披露项的分析结论。"""

    model_config = ConfigDict(extra="forbid")

    assessment_id: str = Field(default_factory=lambda: f"assessment_{uuid4().hex}")
    manifest_item_id: str
    standard_id: str
    standard_year: Optional[str] = None
    canonical_disclosure_id: Optional[str] = None
    canonical_status: Optional[CanonicalStatus] = None
    assessment_mode: AnalysisMode
    verdict: AssessmentVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    requirement_checks: List[RequirementCheck] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    partial_requirements: List[str] = Field(default_factory=list)
    not_applicable_requirements: List[str] = Field(default_factory=list)
    manual_review_requirements: List[str] = Field(default_factory=list)
    aggregation_reason: str = ""
    rationale: str
    recommendation: str = ""
    manual_review_reason_codes: List[ManualReviewReason] = Field(default_factory=list)
    readiness_verdict: Optional[ReadinessVerdict] = None
    not_scored_reason: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.PENDING


class ReviewDecision(BaseModel):
    """人工复核记录。"""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(default_factory=lambda: f"review_{uuid4().hex}")
    assessment_id: str
    reviewer: str
    decision: ReviewStatus
    comment: str = ""
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalysisRun(BaseModel):
    """一次完整 P0 单报告分析任务。"""

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(default_factory=lambda: f"analysis_run_{uuid4().hex}")
    report_id: str
    standard_profile_id: str
    manifest_version: str
    status: AnalysisRunStatus = AnalysisRunStatus.CREATED
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    source_documents: List[SourceDocumentRef] = Field(default_factory=list)
    assessments: List[DisclosureAssessment] = Field(default_factory=list)
    review_decisions: List[ReviewDecision] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)




