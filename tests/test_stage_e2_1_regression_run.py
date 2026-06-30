from pathlib import Path

from scripts.run_p0_stage_e2_1_regression import build_e2_1_retrieval_result, load_regression_sample_ids, main


def test_load_regression_sample_ids_merges_e1_and_e2_samples():
    sample_ids = load_regression_sample_ids(
        Path("data/knowledge_base/manifests/p0_stage_e1_sample_manifest.json"),
        Path("data/knowledge_base/manifests/p0_stage_e2_regression_manifest.json"),
    )

    assert "current_gap:GRI2:2-1" in sample_ids
    assert "current_gap:GRI302:302-4" in sample_ids
    assert "current_gap:GRI3:3-3_generic" in sample_ids
    assert "readiness_2026:GRI101" in sample_ids
    assert len(sample_ids) == len(set(sample_ids))


def test_e2_1_regression_requires_confirm_llm(tmp_path):
    output_dir = tmp_path / "runs"

    exit_code = main(["--output-dir", str(output_dir)])

    assert exit_code == 2
    assert not output_dir.exists()

def test_e2_1_retrieval_result_keeps_e1_validator_contract_version():
    sample_ids = ["current_gap:GRI2:2-1", "current_gap:GRI302:302-4"]
    retrieval_result = build_e2_1_retrieval_result(
        sample_ids,
        Path("data/knowledge_base/manifests/p0_stage_e1_sample_manifest.json"),
        Path("data/knowledge_base/manifests/p0_stage_e2_regression_manifest.json"),
    )

    assert retrieval_result["p0_contract_version"] == "p0_stage_d_agent_contract_v1"
    assert retrieval_result["retrieval_summary"]["run_mode"] == "stage_e2_1_regression"
    assert retrieval_result["retrieval_summary"]["sample_manifest_item_ids"] == sample_ids
