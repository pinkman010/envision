"""P0 pending-review workbench for accepted Stage E assessments."""

from __future__ import annotations

from typing import Any

import pandas as pd
import requests
import streamlit as st

from src.config import settings


API_ROOT = f"{settings.API_BASE_URL}{settings.API_PREFIX}/p0-review"
PENDING_FINAL_STATUS = "pending_human_evaluation"
PENDING_ADVISOR_LABEL = "AI-assisted recommendation pending human review"


st.title("P0 条款级复核工作台")
st.caption(
    "当前数据来自 Stage E accepted artifacts；所有判断保持 pending-review，等待人工评测回传。"
)


def api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{API_ROOT}{path}", params=params, timeout=20)
    response.raise_for_status()
    return response.json()["data"]


def api_post(path: str, payload: dict[str, Any]) -> Any:
    response = requests.post(f"{API_ROOT}{path}", json=payload, timeout=20)
    response.raise_for_status()
    return response.json()["data"]


def api_download(path: str) -> bytes:
    response = requests.get(f"{API_ROOT}{path}", timeout=30)
    response.raise_for_status()
    return response.content


def compact_json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False, indent=2)


def load_runs() -> list[dict[str, Any]]:
    try:
        return api_get("/runs")
    except requests.RequestException as exc:
        st.error(f"E4 API 暂不可用：{exc}")
        st.info("请先启动 FastAPI，并确认已执行 E4 seed 脚本。")
        st.stop()


runs = load_runs()
if not runs:
    st.warning("暂无 E4 pending-review run。请先执行 `scripts/seed_stage_e4_pending_review.py`。")
    st.stop()

run_options = {f"{item['run_id']} · {item['report_id']}": item["run_id"] for item in runs}
selected_label = st.selectbox("Run", options=list(run_options.keys()))
run_id = run_options[selected_label]

try:
    summary = api_get(f"/runs/{run_id}/summary")
except requests.RequestException as exc:
    st.error(f"读取 run summary 失败：{exc}")
    st.stop()

st.info(
    f"final_evaluation_status = {summary.get('final_evaluation_status', PENDING_FINAL_STATUS)}；"
    f"Advisor 状态 = {PENDING_ADVISOR_LABEL}"
)

top_cols = st.columns(4)
top_cols[0].metric("Assessment rows", summary.get("assessment_count", 0))
top_cols[1].metric("Advisor coverage", summary.get("advisor_coverage_count", 0))
top_cols[2].metric("Review status", summary.get("review_status", "pending"))
top_cols[3].metric("Evaluation status", summary.get("final_evaluation_status", PENDING_FINAL_STATUS))

with st.expander("Source manifest", expanded=False):
    source_manifest = next((item for item in runs if item["run_id"] == run_id), {}).get(
        "source_manifest", {}
    )
    st.code(compact_json(source_manifest), language="json")

st.divider()

filter_cols = st.columns([1, 1, 1, 1.3, 1.5])
with filter_cols[0]:
    verdict_filter = st.selectbox(
        "AI verdict",
        ["", "disclosed", "partially_disclosed", "not_disclosed", "manual_review"],
    )
with filter_cols[1]:
    status_filter = st.selectbox("Review status", ["", "pending"])
with filter_cols[2]:
    standard_filter = st.text_input("GRI standard", placeholder="GRI302")
with filter_cols[3]:
    disclosure_filter = st.text_input("Disclosure", placeholder="302-4")
with filter_cols[4]:
    keyword_filter = st.text_input("Keyword", placeholder="证据、议题或条款")

params = {
    "ai_verdict": verdict_filter or None,
    "review_status": status_filter or None,
    "standard_id": standard_filter.strip() or None,
    "disclosure_id": disclosure_filter.strip() or None,
    "keyword": keyword_filter.strip() or None,
}
params = {key: value for key, value in params.items() if value}

try:
    assessments = api_get(f"/runs/{run_id}/assessments", params=params)
    advisor_items = api_get(f"/runs/{run_id}/advisor-items")
except requests.RequestException as exc:
    st.error(f"读取 E4 数据失败：{exc}")
    st.stop()

assessment_df = pd.DataFrame(
    [
        {
            "assessment_id": item["assessment_id"],
            "manifest_item_id": item["manifest_item_id"],
            "standard_id": item.get("standard_id"),
            "disclosure_id": item.get("disclosure_id"),
            "ai_verdict": item.get("ai_verdict"),
            "review_status": item.get("review_status"),
            "manual_review_reason": "; ".join(item.get("manual_review_reason_codes") or []),
        }
        for item in assessments
    ]
)

st.subheader("Assessment review")
st.dataframe(assessment_df, use_container_width=True, hide_index=True, height=320)

if not assessments:
    st.warning("当前筛选条件下没有 assessment。")
    st.stop()

assessment_labels = {
    f"{item['manifest_item_id']} · {item.get('ai_verdict')}": item["assessment_id"]
    for item in assessments
}
selected_assessment_label = st.selectbox("Assessment detail", options=list(assessment_labels.keys()))
assessment_id = assessment_labels[selected_assessment_label]

try:
    assessment_detail = api_get(f"/runs/{run_id}/assessments/{assessment_id}")
except requests.RequestException as exc:
    st.error(f"读取 assessment detail 失败：{exc}")
    st.stop()

detail_cols = st.columns([1.1, 1.1, 1])
with detail_cols[0]:
    st.markdown("#### 条款")
    st.write(f"manifest_item_id: `{assessment_detail['manifest_item_id']}`")
    st.write(f"disclosure_id: `{assessment_detail.get('disclosure_id')}`")
    st.write(f"standard_id: `{assessment_detail.get('standard_id')}`")
    st.write(f"AI verdict: `{assessment_detail.get('ai_verdict')}`")
with detail_cols[1]:
    st.markdown("#### Evidence")
    evidence_rows = [
        {
            "evidence_id": item.get("evidence_id"),
            "chunk_id": item.get("chunk_id"),
            "source_page": item.get("source_page"),
            "report_page_label": item.get("report_page_label"),
            "evidence_kind": item.get("evidence_kind"),
        }
        for item in assessment_detail.get("evidence", [])
    ]
    st.dataframe(pd.DataFrame(evidence_rows), use_container_width=True, hide_index=True, height=180)
with detail_cols[2]:
    st.markdown("#### Pending status")
    st.write(f"review_status: `{assessment_detail.get('review_status')}`")
    st.write(f"final_evaluation_status: `{assessment_detail.get('final_evaluation_status')}`")
    st.write(
        "manual_review_reason: "
        + "; ".join(assessment_detail.get("manual_review_reason_codes") or [])
    )

with st.expander("Requirement checks", expanded=True):
    requirement_rows = [
        {
            "requirement_id": item.get("requirement_id"),
            "support_status": item.get("support_status"),
            "supporting_evidence_ids": "; ".join(item.get("supporting_evidence_ids") or []),
            "missing_reason": item.get("missing_reason"),
            "manual_review_reason": item.get("manual_review_reason"),
        }
        for item in assessment_detail.get("requirement_checks", [])
    ]
    st.dataframe(pd.DataFrame(requirement_rows), use_container_width=True, hide_index=True, height=260)

with st.expander("Evidence text", expanded=False):
    for idx, item in enumerate(assessment_detail.get("evidence", []), start=1):
        st.markdown(
            f"**{idx}. PDF page {item.get('source_page')} / report page {item.get('report_page_label')}**"
        )
        st.text_area(
            f"source_text_{idx}",
            value=item.get("source_text", ""),
            height=120,
            disabled=True,
            label_visibility="collapsed",
        )

matched_advisor_items = [
    item for item in advisor_items if item.get("manifest_item_id") == assessment_detail["manifest_item_id"]
]
st.subheader("Advisor coverage")
if matched_advisor_items:
    advisor_df = pd.DataFrame(
        [
            {
                "advisor_item_id": item.get("advisor_item_id"),
                "coverage_type": item.get("coverage_type"),
                "priority": item.get("priority"),
                "requires_internal_data": item.get("requires_internal_data"),
                "recommendation_status": item.get("recommendation_status"),
                "recommendation_text": item.get("recommendation_text"),
            }
            for item in matched_advisor_items
        ]
    )
    st.dataframe(advisor_df, use_container_width=True, hide_index=True)
else:
    st.write("当前条款暂无 Advisor coverage。")

st.subheader("人工复核录入")
with st.form("p0_review_decision_form", clear_on_submit=False):
    form_cols = st.columns(3)
    with form_cols[0]:
        human_verdict = st.selectbox(
            "Human verdict",
            ["", "disclosed", "partially_disclosed", "not_disclosed", "not_applicable", "manual_review"],
        )
        evidence_page_check = st.selectbox("Evidence page check", ["", "ok", "issue", "not_checked"])
    with form_cols[1]:
        requirement_gap_check = st.selectbox("Requirement gap check", ["", "ok", "issue", "not_checked"])
        error_type = st.text_input("Error type", placeholder="例如 evidence_binding_issue")
    with form_cols[2]:
        reviewer = st.text_input("Reviewer")
        source = st.text_input("Source", value="streamlit_p0_review_workbench")
    correction_note = st.text_area("Correction note", height=90)
    review_comment = st.text_area("Review comment", height=90)
    submitted = st.form_submit_button("保存复核记录")

if submitted:
    payload = {
        "assessment_id": assessment_detail["assessment_id"],
        "manifest_item_id": assessment_detail["manifest_item_id"],
        "reviewer": reviewer or None,
        "human_verdict": human_verdict or None,
        "evidence_page_check": evidence_page_check or None,
        "requirement_gap_check": requirement_gap_check or None,
        "error_type": error_type or None,
        "correction_note": correction_note or None,
        "review_comment": review_comment or None,
        "source": source or "streamlit_p0_review_workbench",
    }
    try:
        decision = api_post(f"/runs/{run_id}/review-decisions", payload)
        st.success(f"复核记录已保存：{decision['review_decision_id']}")
    except requests.RequestException as exc:
        st.error(f"保存复核记录失败：{exc}")

st.subheader("导出")
download_cols = st.columns(3)
exports = [
    ("Assessment CSV", f"/runs/{run_id}/exports/assessments.csv", "assessment_review_export.csv", "text/csv"),
    ("Advisor CSV", f"/runs/{run_id}/exports/advisor-items.csv", "advisor_review_export.csv", "text/csv"),
    (
        "Review CSV",
        f"/runs/{run_id}/exports/review-decisions.csv",
        "review_decisions_export.csv",
        "text/csv",
    ),
    (
        "Assessment JSON",
        f"/runs/{run_id}/exports/assessments.json",
        "assessment_review_export.json",
        "application/json",
    ),
    (
        "Advisor JSON",
        f"/runs/{run_id}/exports/advisor-items.json",
        "advisor_review_export.json",
        "application/json",
    ),
    (
        "Review JSON",
        f"/runs/{run_id}/exports/review-decisions.json",
        "review_decisions_export.json",
        "application/json",
    ),
]
for index, (label, path, filename, mime) in enumerate(exports):
    with download_cols[index % 3]:
        try:
            data = api_download(path)
            st.download_button(label, data=data, file_name=filename, mime=mime, use_container_width=True)
        except requests.RequestException:
            st.button(label, disabled=True, use_container_width=True)
