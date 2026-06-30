from __future__ import annotations

from pathlib import Path


def test_streamlit_p0_review_workbench_page_is_registered_and_pending_only() -> None:
    app_source = Path("src/ui/app.py").read_text(encoding="utf-8")
    page_source = Path("src/ui/pages/09_p0_review_workbench.py").read_text(encoding="utf-8")

    assert "09_p0_review_workbench.py" in app_source
    assert "pending_human_evaluation" in page_source
    assert "AI-assisted recommendation pending human review" in page_source
    assert "final_accuracy" not in page_source
    forbidden_phrases = ["最终准确率", "人工验证通过", "最终建议已确认"]
    assert not any(phrase in page_source for phrase in forbidden_phrases)
