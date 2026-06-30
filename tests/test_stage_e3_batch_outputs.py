from pathlib import Path

from scripts.run_p0_stage_e3_batch import (
    build_e3_retrieval_result,
    load_scope_manifest,
    main,
    select_batch_contexts,
)
from scripts.validate_stage_e3_batch_outputs import ALLOWED_E3_RUN_MODES
from scripts.validate_stage_e3_batch_outputs import ALLOWED_SMOKE_GATE_STATUSES
from scripts.validate_stage_e3_batch_outputs import _artifact_path
from scripts.validate_stage_e3_batch_outputs import _validate_body_evidence_fields
from scripts.validate_stage_e3_batch_outputs import _validate_smoke_review_result


def test_e3_batch_01_selects_only_gri2_current_gap_contexts():
    scope_manifest = load_scope_manifest(Path("docs/stage_e3/e3_current_scope_manifest.json"))

    contexts = select_batch_contexts(scope_manifest, "e3_batch_01_gri2")

    assert len(contexts) == 30
    assert {context["standard_id"].replace(" ", "") for context in contexts} == {"GRI2"}
    assert {context["analysis_mode"] for context in contexts} == {"current_gap"}
    assert "current_gap:GRI3:3-3_generic" not in {context["manifest_item_id"] for context in contexts}


def test_e3_batch_requires_confirm_llm(tmp_path):
    output_dir = tmp_path / "runs"

    exit_code = main(["--batch-id", "e3_batch_01_gri2", "--output-dir", str(output_dir)])

    assert exit_code == 2
    assert not output_dir.exists()


def test_e3_retrieval_result_records_batch_scope():
    scope_manifest_path = Path("docs/stage_e3/e3_current_scope_manifest.json")
    scope_manifest = load_scope_manifest(scope_manifest_path)
    contexts = select_batch_contexts(scope_manifest, "e3_batch_01_gri2")

    retrieval_result = build_e3_retrieval_result(
        contexts[:2],
        scope_manifest_path,
        scope_manifest,
        "e3_batch_01_gri2",
    )

    assert retrieval_result["p0_contract_version"] == "p0_stage_d_agent_contract_v1"
    assert retrieval_result["retrieval_summary"]["run_mode"] == "stage_e3_batch"
    assert retrieval_result["retrieval_summary"]["batch_id"] == "e3_batch_01_gri2"
    assert retrieval_result["retrieval_summary"]["sampled"] is False
    assert retrieval_result["retrieval_summary"]["sample_manifest_item_ids"] == [
        context["manifest_item_id"] for context in contexts[:2]
    ]


def test_e3_validator_rejects_ellipsis_summary_source_text():
    errors = []
    _validate_body_evidence_fields(
        "current_gap:GRI2:2-22",
        {
            "source_page": 4,
            "report_page_label": "3",
            "source_text": "董事长致辞：...可持续发展",
            "evidence_kind": "substantive_report_evidence",
            "chunk_id": "chunk_1",
        },
        errors,
    )

    assert any("verbatim" in error for error in errors)


def test_e3_validator_accepts_batch_specific_smoke_review_gate(tmp_path):
    smoke_path = tmp_path / "smoke_review_result.json"
    smoke_path.write_text(
        """{
  "review_status": "completed",
  "gate_status": "passed_before_batch_03",
  "items": [
    {
      "manifest_item_id": "current_gap:GRI3:3-1",
      "model_verdict": "partially_disclosed",
      "human_verdict": "partially_disclosed",
      "issue_types": ["none_under_current_contract"]
    },
    {
      "manifest_item_id": "current_gap:GRI3:3-2",
      "model_verdict": "partially_disclosed",
      "human_verdict": "partially_disclosed",
      "issue_types": ["none_under_current_contract"]
    }
  ]
}
""",
        encoding="utf-8",
    )
    errors = []

    assert _validate_smoke_review_result(tmp_path, errors, expected_item_count=2) is True
    assert errors == []

def test_e3_validator_allows_split_merged_run_mode():
    assert "stage_e3_batch" in ALLOWED_E3_RUN_MODES
    assert "stage_e3_batch_split_merged" in ALLOWED_E3_RUN_MODES


def test_e3_validator_allows_batch_03_minor_granularity_gate():
    assert "passed_before_batch_04_with_minor_requirement_granularity_issue" in ALLOWED_SMOKE_GATE_STATUSES


def test_e3_validator_allows_batch_04_required_field_corrections_gate():
    assert "blocked_before_batch_05_required_field_corrections" in ALLOWED_SMOKE_GATE_STATUSES


def test_e3_validator_allows_batch_05_current_scope_required_field_corrections_gate():
    assert "blocked_before_e3_current_scope_acceptance_required_field_corrections" in ALLOWED_SMOKE_GATE_STATUSES


def test_e3_validator_prefers_corrected_artifact_when_present(tmp_path):
    raw = tmp_path / "advisor_result.json"
    corrected = tmp_path / "advisor_result_corrected.json"
    raw.write_text("{}", encoding="utf-8")
    corrected.write_text("{}", encoding="utf-8")

    path, corrected_used = _artifact_path(tmp_path, "advisor_result_corrected.json", "advisor_result.json")

    assert path == corrected
    assert corrected_used is True

