import json
from pathlib import Path

from scripts.build_p0_requirement_sampling_manifest import build_sampling_manifest
from scripts.validate_p0_requirement_sampling_manifest import validate_sampling_manifest


def test_sampling_manifest_covers_high_risk_parents_and_types():
    manifest = build_sampling_manifest(sample_size=40)
    parent_ids = {item["parent_requirement_id"] for item in manifest["sampled_requirements"]}
    requirement_types = {item["requirement_type"] for item in manifest["sampled_requirements"]}

    assert "current_gap:GRI2:2-1" in parent_ids
    assert "current_gap:GRI302:302-4" in parent_ids
    assert "current_gap:GRI306:306-4" in parent_ids
    assert "current_gap:GRI401:401-1" in parent_ids
    assert "requirement" in requirement_types
    assert "compilation_requirement" in requirement_types
    assert 30 <= len(manifest["sampled_requirements"]) <= 50


def test_sampling_manifest_validator_accepts_written_manifest(tmp_path):
    manifest = build_sampling_manifest(sample_size=40)
    path = tmp_path / "sampling.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    result = validate_sampling_manifest(path)

    assert result["status"] == "ok"
