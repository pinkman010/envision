"""Versioned GRI requirement and report evidence layer models."""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.models.analysis_contract import AnalysisMode, CanonicalStatus

_SHA256_RE = re.compile(r"^[A-F0-9]{64}$")


def _normalize_sha256(value: str) -> str:
    normalized = value.upper()
    if not _SHA256_RE.fullmatch(normalized):
        raise ValueError("SHA-256 must be 64 uppercase hexadecimal characters")
    return normalized


class RequirementLocatorStatus(str, Enum):
    """Status of locating a disclosure in the official GRI PDF."""

    FOUND = "found"
    MULTIPLE_CANDIDATES = "multiple_candidates"
    NOT_FOUND = "not_found"
    REQUIRES_TOPIC_INSTANTIATION = "requires_topic_instantiation"
    NOT_REQUIRED_FOR_FUTURE_WATCH = "not_required_for_future_watch"


class TranslationStatus(str, Enum):
    """Status of any Chinese working translation for the English GRI requirement."""

    NOT_TRANSLATED = "not_translated"
    WORKING_TRANSLATION_PENDING = "working_translation_pending"
    WORKING_TRANSLATION_AVAILABLE = "working_translation_available"


class RequirementChecklistType(str, Enum):
    """Requirement checklist item type for scoring and reference separation."""

    REQUIREMENT = "requirement"
    COMPILATION_REQUIREMENT = "compilation_requirement"
    GUIDANCE = "guidance"
    RECOMMENDATION = "recommendation"
    EXAMPLE = "example"
    BACKGROUND = "background"


class RequirementScoringRole(str, Enum):
    """How a checklist item participates in disclosure scoring."""

    HARD_SCORE = "hard_score"
    AGGREGATION_PARENT = "aggregation_parent"
    SCOPE_REVIEW = "scope_review"
    SOFT_REFERENCE = "soft_reference"
    EXCLUDED = "excluded"


class RequirementExtractionReviewStatus(str, Enum):
    """Manual extraction review status for seed or leaf requirements."""

    PENDING_REVIEW = "pending_review"
    REVIEWED = "reviewed"
    REVIEWED_PARENT_NOT_SCORED = "reviewed_parent_not_scored"
    NEEDS_SCOPE_REVIEW = "needs_scope_review"
    REJECTED = "rejected"


class ManualLocatorReview(BaseModel):
    """Manual confirmation for ambiguous official GRI PDF locators."""

    model_config = ConfigDict(extra="forbid")

    review_status: str
    confirmed_official_pdf_pages: List[int] = Field(min_length=1)
    confirmed_title: str
    review_reason: str
    reviewed_at: str

    @field_validator("review_status", "confirmed_title", "review_reason", "reviewed_at")
    @classmethod
    def text_fields_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("manual locator review text fields must not be empty")
        return value

    @field_validator("confirmed_official_pdf_pages")
    @classmethod
    def confirmed_pages_must_be_positive(cls, value: List[int]) -> List[int]:
        if any(page < 1 for page in value):
            raise ValueError("confirmed official PDF pages must be positive")
        return value


class GRIRequirement(BaseModel):
    """A P0 disclosure requirement with official-source locator metadata."""

    model_config = ConfigDict(extra="forbid")

    analysis_mode: AnalysisMode
    manifest_item_id: str
    standard_id: str
    standard_title_zh_or_en: str
    standard_year: str
    source_disclosure_id: Optional[str] = None
    canonical_disclosure_id: Optional[str] = None
    canonical_status: CanonicalStatus
    effective_date: Optional[str] = None
    related_current_standard: Optional[str] = None
    report_index_pdf_page: Optional[int] = None
    report_index_report_page: Optional[int] = None
    evidence_expectation: str
    notes: str = ""
    requirement_locator_status: RequirementLocatorStatus
    official_pdf_page_candidates: List[int] = Field(default_factory=list)
    english_title_candidates: List[str] = Field(default_factory=list)
    english_excerpt_candidates: List[str] = Field(default_factory=list)
    translation_status: TranslationStatus = TranslationStatus.NOT_TRANSLATED
    source_document_relative_path: str
    source_document_sha256: str
    locator_review_required: bool = False
    locator_review_reason: Optional[str] = None
    manual_locator_review: Optional[ManualLocatorReview] = None

    @field_validator("source_document_sha256")
    @classmethod
    def validate_source_document_sha256(cls, value: str) -> str:
        return _normalize_sha256(value)

    @model_validator(mode="after")
    def manual_locator_review_pages_must_be_candidates(self) -> "GRIRequirement":
        if self.manual_locator_review is None:
            return self
        confirmed_pages = set(self.manual_locator_review.confirmed_official_pdf_pages)
        candidate_pages = set(self.official_pdf_page_candidates)
        if not confirmed_pages.issubset(candidate_pages):
            raise ValueError("confirmed official PDF pages must be a subset of official PDF page candidates")
        return self


class ReportEvidenceChunk(BaseModel):
    """A report text chunk that preserves page and source-hash traceability."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    source_document_relative_path: str
    source_document_sha256: str
    company: str
    report_year: int
    industry: str
    topic: str = "general"
    pdf_page: int = Field(ge=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    text: str

    @field_validator("source_document_sha256")
    @classmethod
    def validate_source_document_sha256(cls, value: str) -> str:
        return _normalize_sha256(value)

    @field_validator("company", "industry", "topic")
    @classmethod
    def chunk_metadata_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("chunk metadata text fields must not be empty")
        return value

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value

    @model_validator(mode="after")
    def char_range_must_be_valid(self) -> "ReportEvidenceChunk":
        if self.char_end < self.char_start:
            raise ValueError("char_end must be greater than or equal to char_start")
        return self


class EvidenceLayerMetadata(BaseModel):
    """Build metadata shared by requirement and report evidence manifests."""

    model_config = ConfigDict(extra="forbid")

    built_at: str
    source_manifest_sha256: str
    disclosure_manifest_sha256: str
    report_source_document_relative_path: str
    report_pdf_sha256: str
    gri_source_document_relative_path: str
    gri_pdf_sha256: str
    chunk_size: int = Field(gt=0)
    chunk_overlap: int = Field(ge=0)

    @field_validator(
        "source_manifest_sha256",
        "disclosure_manifest_sha256",
        "report_pdf_sha256",
        "gri_pdf_sha256",
    )
    @classmethod
    def validate_sha256(cls, value: str) -> str:
        return _normalize_sha256(value)


class P0RequirementChecklistMetadata(BaseModel):
    """Metadata for the P0 requirement checklist seed manifest."""

    model_config = ConfigDict(extra="forbid")

    manifest_version: str
    standard_profile_id: str
    source_requirement_pack: str
    source_disclosure_manifest: str
    created_at: str
    generated_by: str
    notes: str
    excluded_counts_by_mode: Dict[str, int] = Field(default_factory=dict)
    excluded_items: List[Dict[str, Any]] = Field(default_factory=list)

    @field_validator(
        "manifest_version",
        "standard_profile_id",
        "source_requirement_pack",
        "source_disclosure_manifest",
        "created_at",
        "generated_by",
        "notes",
    )
    @classmethod
    def metadata_text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("checklist metadata text fields must not be empty")
        return value


class P0RequirementChecklistItem(BaseModel):
    """A checklist item used to assess one P0 disclosure requirement."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    parent_requirement_id: str
    canonical_disclosure_id: str
    requirement_text: str
    requirement_type: RequirementChecklistType
    conditional: bool = False
    condition_text: str = ""
    official_pdf_page: Optional[int] = Field(default=None, ge=1)
    is_mandatory: bool
    scoring_role: RequirementScoringRole
    standard_year: str
    published_at: Optional[str] = None
    effective_date: Optional[str] = None
    analysis_applicability_date: str
    replaced_standard: Optional[str] = None
    assessment_mode: AnalysisMode
    standard_profile_id: str
    extraction_review_status: RequirementExtractionReviewStatus
    notes: str = ""

    @field_validator(
        "requirement_id",
        "parent_requirement_id",
        "canonical_disclosure_id",
        "requirement_text",
        "standard_year",
        "analysis_applicability_date",
        "standard_profile_id",
    )
    @classmethod
    def checklist_text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("checklist text fields must not be empty")
        return value

    @model_validator(mode="after")
    def scoring_role_must_match_requirement_type(self) -> "P0RequirementChecklistItem":
        hard_score_types = {
            RequirementChecklistType.REQUIREMENT,
            RequirementChecklistType.COMPILATION_REQUIREMENT,
        }
        if self.scoring_role == RequirementScoringRole.HARD_SCORE:
            if self.requirement_type not in hard_score_types:
                raise ValueError("hard_score is only valid for requirement or compilation_requirement items")
            if self.assessment_mode != AnalysisMode.CURRENT_GAP:
                raise ValueError("hard_score checklist items must use current_gap assessment_mode")
        non_scoring_roles = {
            RequirementScoringRole.AGGREGATION_PARENT,
            RequirementScoringRole.SCOPE_REVIEW,
        }
        if self.scoring_role in non_scoring_roles and self.is_mandatory:
            raise ValueError("aggregation_parent and scope_review checklist items must not be mandatory")
        if self.conditional and not self.condition_text.strip():
            raise ValueError("conditional checklist items must include condition_text")
        return self


class P0TopicInstantiationRequirement(BaseModel):
    """A generic disclosure that must be instantiated by material topic before scoring."""

    model_config = ConfigDict(extra="forbid")

    parent_requirement_id: str
    canonical_disclosure_id: str
    reason: str

    @field_validator("parent_requirement_id", "canonical_disclosure_id", "reason")
    @classmethod
    def topic_instantiation_text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("topic instantiation fields must not be empty")
        return value


class P0RequirementChecklist(BaseModel):
    """P0 checklist of current disclosure requirements and topic-instantiation exclusions."""

    model_config = ConfigDict(extra="forbid")

    metadata: P0RequirementChecklistMetadata
    requirements: List[P0RequirementChecklistItem]
    topic_instantiation_required: List[P0TopicInstantiationRequirement] = Field(default_factory=list)

    @model_validator(mode="after")
    def requirement_ids_must_be_unique(self) -> "P0RequirementChecklist":
        seen = set()
        duplicates = set()
        for item in self.requirements:
            if item.requirement_id in seen:
                duplicates.add(item.requirement_id)
            seen.add(item.requirement_id)
        if duplicates:
            raise ValueError(f"duplicate requirement_id values: {sorted(duplicates)}")
        return self


class GRIRequirementPack(BaseModel):
    """Versioned pack of P0 GRI requirements."""

    model_config = ConfigDict(extra="forbid")

    metadata: EvidenceLayerMetadata
    requirements: List[GRIRequirement]
    locator_review_required: List[str] = Field(default_factory=list)


class ReportEvidenceIndex(BaseModel):
    """Versioned evidence index for the P0 source ESG report."""

    model_config = ConfigDict(extra="forbid")

    metadata: EvidenceLayerMetadata
    chunks: List[ReportEvidenceChunk]
