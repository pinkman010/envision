"""Versioned GRI requirement and report evidence layer models."""

from __future__ import annotations

import re
from enum import Enum
from typing import List, Optional

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

    @field_validator("source_document_sha256")
    @classmethod
    def validate_source_document_sha256(cls, value: str) -> str:
        return _normalize_sha256(value)


class ReportEvidenceChunk(BaseModel):
    """A report text chunk that preserves page and source-hash traceability."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    source_document_relative_path: str
    source_document_sha256: str
    pdf_page: int = Field(ge=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    text: str

    @field_validator("source_document_sha256")
    @classmethod
    def validate_source_document_sha256(cls, value: str) -> str:
        return _normalize_sha256(value)

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