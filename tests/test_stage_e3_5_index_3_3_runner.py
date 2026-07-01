from __future__ import annotations

import json
from pathlib import Path

from scripts.archive_stage_e.run_stage_e3_5_index_3_3_llm import (
    BATCHES,
    DEFAULT_SCOPE_OUTPUT,
    _chunk_lookup,
    _contexts_for_batch,
    _validate_merged,
)


def test_e3_5_index_3_3_contexts_cover_29_instances() -> None:
    scope = json.loads(DEFAULT_SCOPE_OUTPUT.read_text(encoding="utf-8"))
    chunks = _chunk_lookup(Path("data/knowledge_base/manifests/p0_report_evidence_index.json"))
    total = 0
    for batch in BATCHES:
        contexts = _contexts_for_batch(instances=scope["instances"], chunks_by_page=chunks, batch=batch)
        assert contexts
        total += len(contexts)
        for context in contexts:
            assert context["canonical_disclosure_id"] == "3-3"
            assert context["analysis_mode"] == "current_gap"
            assert len(context["requirement_checklist_items"]) == 13
            assert context["evidence_bundle"]["index_evidence"]
            assert context["evidence_bundle"]["referenced_page_evidence"]
    assert total == 29


def test_e3_5_index_3_3_merged_validator_accepts_minimal_assessments() -> None:
    assessments = [
        {
            "manifest_item_id": f"current_gap:GRI{201 + index}:3-3",
            "canonical_disclosure_id": "3-3",
            "assessment_mode": "current_gap",
            "verdict": "manual_review",
            "manual_review_reason_codes": ["additional_evidence_needed"],
            "evidence": [],
            "requirement_checks": [],
        }
        for index in range(29)
    ]
    result = _validate_merged(assessments)
    assert result["status"] == "ok"
