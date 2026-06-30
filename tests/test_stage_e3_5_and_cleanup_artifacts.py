from __future__ import annotations

import json
from pathlib import Path

from scripts.build_stage_e3_5_topic_assessments import build_e3_5_topic_assessments
from scripts.build_stage_e3_5_index_3_3_assessments import build_index_3_3_assessments
from scripts.build_stage_e3_traceability_cleanup_artifacts import build_traceability_cleanup_artifacts
from scripts.prepare_stage_e3_unified_final_advisor import prepare_or_run_final_advisor
from src.models.analysis_contract import AnalysisRun


def _latest_child(path: Path) -> Path:
    children = [item for item in path.iterdir() if item.is_dir()]
    assert children
    return max(children, key=lambda item: item.stat().st_mtime)


def test_build_e3_5_topic_instantiation_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "stage_e3_5"
    result = build_e3_5_topic_assessments(output_dir=output_dir)

    assert result["status"] == "ok"
    assert result["topic_count"] == 16
    run_dir = _latest_child(output_dir)
    analyst_result = json.loads((run_dir / "analyst_result.json").read_text(encoding="utf-8"))
    assert len(analyst_result["disclosure_assessments"]) == 16
    assert all(
        item["manifest_item_id"].startswith("current_gap:GRI3:3-3_")
        for item in analyst_result["disclosure_assessments"]
    )
    assert "current_gap:GRI3:3-3_generic" not in {
        item["manifest_item_id"] for item in analyst_result["disclosure_assessments"]
    }
    AnalysisRun.model_validate_json((run_dir / "analysis_run.json").read_text(encoding="utf-8"))


def test_build_e3_5_index_row_3_3_instantiation_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "stage_e3_5_index"
    scope_output = tmp_path / "index_scope.json"
    result = build_index_3_3_assessments(output_dir=output_dir, scope_output_path=scope_output)

    assert result["status"] == "ok"
    assert result["gri_3_3_instance_count"] == 29
    assert result["expected_final_current_assessment_units"] == 143
    run_dir = _latest_child(output_dir)
    analyst_result = json.loads((run_dir / "analyst_result.json").read_text(encoding="utf-8"))
    ids = [item["manifest_item_id"] for item in analyst_result["disclosure_assessments"]]
    assert len(ids) == 29
    assert len(set(ids)) == 29
    assert all(item.endswith(":3-3") for item in ids)
    assert "current_gap:GRI3:3-3_generic" not in ids
    AnalysisRun.model_validate_json((run_dir / "analysis_run.json").read_text(encoding="utf-8"))


def test_build_traceability_cleanup_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "traceability_cleanup"
    result = build_traceability_cleanup_artifacts(output_dir=output_dir)

    assert result["status"] == "ok"
    assert result["assessment_count"] == 114
    run_dir = _latest_child(output_dir)
    cleanup_result = json.loads((run_dir / "traceability_cleanup_result.json").read_text(encoding="utf-8"))
    assert cleanup_result["effective_artifacts_modified"] is False
    assert cleanup_result["requirement_id_cleanup"]["invalid_reference_unique_count"] >= 1
    assert (run_dir / "pdf_source_text_location_waiver.json").exists()


def test_prepare_unified_final_advisor_input_without_llm(tmp_path: Path) -> None:
    output_dir = tmp_path / "final_advisor"
    approval_doc = tmp_path / "approval.md"
    result = prepare_or_run_final_advisor(output_dir=output_dir, approval_doc_path=approval_doc)

    assert result["status"] == "prepared"
    assert result["assessment_count"] == 114
    assert result["llm_called"] is False
    run_dir = _latest_child(output_dir)
    analyst_result = json.loads((run_dir / "merged_effective_analyst_result.json").read_text(encoding="utf-8"))
    assert len(analyst_result["disclosure_assessments"]) == 114
    assert "current_gap:GRI3:3-3_generic" not in {
        item["manifest_item_id"] for item in analyst_result["disclosure_assessments"]
    }
    assert approval_doc.exists()
