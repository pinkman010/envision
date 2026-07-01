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

def test_visible_streamlit_pages_do_not_link_to_hidden_legacy_pages() -> None:
    visible_page_sources = {
        "app": Path("src/ui/app.py").read_text(encoding="utf-8"),
        "home": Path("src/ui/pages/01_home.py").read_text(encoding="utf-8"),
        "corpus": Path("src/ui/pages/02_corpus.py").read_text(encoding="utf-8"),
        "review_workbench": Path("src/ui/pages/09_p0_review_workbench.py").read_text(encoding="utf-8"),
        "audit": Path("src/ui/pages/07_audit.py").read_text(encoding="utf-8"),
    }
    hidden_pages = [
        "03_materiality.py",
        "04_analysis.py",
        "05_review.py",
        "06_benchmarking.py",
        "08_rules.py",
    ]

    for source_name, source in visible_page_sources.items():
        assert not any(page in source for page in hidden_pages), source_name


def test_legacy_streamlit_pages_are_removed_from_p0_delivery() -> None:
    removed_pages = [
        "03_materiality.py",
        "04_analysis.py",
        "05_review.py",
        "06_benchmarking.py",
        "08_rules.py",
    ]

    for page in removed_pages:
        assert not Path("src/ui/pages", page).exists(), page
