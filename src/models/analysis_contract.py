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
    source_text: str
    relevance: float = Field(ge=0.0, le=1.0)
    corpus_id: Optional[str] = None
    chunk_id: Optional[str] = None
    extraction_method: str = "retrieval_or_manual"


class DisclosureAssessment(BaseModel):
    """单个披露项的分析结论。"""

    model_config = ConfigDict(extra="forbid")

    assessment_id: str = Field(default_factory=lambda: f"assessment_{uuid4().hex}")
    manifest_item_id: str
    standard_id: str
    canonical_disclosure_id: Optional[str] = None
    assessment_mode: AnalysisMode
    verdict: AssessmentVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Evidence] = Field(default_factory=list)
    rationale: str
    recommendation: str = ""
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