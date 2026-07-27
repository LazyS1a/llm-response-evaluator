"""EvalFlow: an interactive LLM response evaluation workspace."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import streamlit as st

from app_core import (
    DIMENSION_LABELS,
    ERROR_TAG_LABELS,
    EvaluationValidationError,
    build_evaluation_record,
    load_jsonl,
    merge_review_updates,
    must_require_human_review,
    normalize_error_tags,
    parse_records_text,
    records_to_jsonl,
    render_single_evaluation_markdown,
    summarize_records,
)


ROOT = Path(__file__).resolve().parent
STEM_CASES_PATH = ROOT / "data" / "stem_cases.jsonl"
STEM_EVALUATIONS_PATH = ROOT / "data" / "stem_draft_evaluations.jsonl"
SAMPLE_EVALUATIONS_PATH = ROOT / "data" / "sample_evaluations.jsonl"


st.set_page_config(
    page_title="EvalFlow",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #18232b;
        --muted: #64727c;
        --line: #d9e1e5;
        --panel: #f7f9fa;
        --teal: #087f78;
        --coral: #c8553d;
        --green: #2f7d55;
    }
    .stApp {
        background: #ffffff;
        color: var(--ink);
    }
    .block-container {
        max-width: 1320px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1, h2, h3 {
        color: var(--ink);
        letter-spacing: 0;
    }
    h1 {
        font-size: 2.15rem;
        margin-bottom: 0.2rem;
    }
    [data-testid="stMetric"] {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 0.85rem 1rem;
    }
    [data-testid="stMetricLabel"] {
        color: var(--muted);
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid var(--line);
        background: #f6f8f9;
    }
    [data-baseweb="tab-list"] {
        gap: 1.4rem;
        border-bottom: 1px solid var(--line);
    }
    [data-baseweb="tab"] {
        height: 3rem;
        padding-left: 0;
        padding-right: 0;
    }
    .status-ok {
        color: var(--green);
        font-weight: 700;
    }
    .status-review {
        color: var(--coral);
        font-weight: 700;
    }
    .muted {
        color: var(--muted);
    }
    .evidence-boundary {
        border-top: 1px solid var(--line);
        margin-top: 2rem;
        padding-top: 1rem;
        color: var(--muted);
        font-size: 0.88rem;
    }
    @media (max-width: 760px) {
        .block-container {
            padding-top: 1rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        h1 {
            font-size: 1.8rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_project_data() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    return (
        load_jsonl(STEM_CASES_PATH),
        load_jsonl(STEM_EVALUATIONS_PATH),
        load_jsonl(SAMPLE_EVALUATIONS_PATH),
    )


def evaluation_index(
    records: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {record["case_id"]: record for record in records}


def average_score(record: dict[str, Any]) -> float:
    return sum(record["scores"].values()) / len(record["scores"])


def render_case_context(case: dict[str, Any]) -> None:
    st.markdown("#### 评测材料")
    st.text_area(
        "用户问题",
        value=case.get("prompt", ""),
        height=105,
        key=f"prompt-{case['case_id']}",
    )
    st.text_area(
        "模型回答",
        value=case.get("candidate_answer", ""),
        height=135,
        key=f"candidate-{case['case_id']}",
    )
    st.text_area(
        "参考答案",
        value=case.get("reference_answer", ""),
        height=135,
        key=f"reference-{case['case_id']}",
    )
    if case.get("sources"):
        source = case["sources"][0]
        pages = "、".join(str(page) for page in source.get("pages", []))
        st.caption(f"来源：{source.get('file', '未提供')} · 第 {pages} 页")


def render_score_controls(
    default_record: dict[str, Any],
    key_prefix: str,
) -> tuple[dict[str, int], list[str], float, bool]:
    st.markdown("#### 五维评分")
    scores: dict[str, int] = {}
    score_columns = st.columns(2)
    for index, (dimension, label) in enumerate(DIMENSION_LABELS.items()):
        with score_columns[index % 2]:
            scores[dimension] = st.slider(
                label,
                min_value=1,
                max_value=5,
                value=int(default_record["scores"][dimension]),
                key=f"{key_prefix}-score-{dimension}",
            )

    tags = st.multiselect(
        "错误标签",
        options=list(ERROR_TAG_LABELS),
        default=default_record["error_tags"],
        format_func=lambda value: ERROR_TAG_LABELS[value],
        key=f"{key_prefix}-tags",
    )
    confidence = st.slider(
        "评测置信度",
        min_value=0.0,
        max_value=1.0,
        value=float(default_record["confidence"]),
        step=0.01,
        key=f"{key_prefix}-confidence",
    )
    manual_review = st.checkbox(
        "额外加入人工复核",
        value=bool(default_record["human_review_required"]),
        key=f"{key_prefix}-manual-review",
    )
    mandatory_review = must_require_human_review(
        scores,
        normalize_error_tags(tags),
        confidence,
    )
    status_class = "status-review" if mandatory_review or manual_review else "status-ok"
    status_text = "需要人工复核" if mandatory_review or manual_review else "可直接归档"
    st.markdown(
        f'<p class="{status_class}">{status_text}</p>',
        unsafe_allow_html=True,
    )
    return scores, tags, confidence, manual_review


def render_record_fields(
    default_record: dict[str, Any],
    key_prefix: str,
) -> tuple[list[str], str, str]:
    evidence_text = st.text_area(
        "判断证据（每行一条）",
        value="\n".join(default_record["evidence"]),
        height=120,
        key=f"{key_prefix}-evidence",
    )
    rationale = st.text_area(
        "评测理由",
        value=default_record["rationale"],
        height=95,
        key=f"{key_prefix}-rationale",
    )
    revision = st.text_area(
        "修改建议",
        value=default_record["suggested_revision"],
        height=95,
        key=f"{key_prefix}-revision",
    )
    return evidence_text.splitlines(), rationale, revision


def render_single_evaluation(
    cases: list[dict[str, Any]],
    reviewed_records: list[dict[str, Any]],
) -> None:
    mode = st.segmented_control(
        "评测来源",
        options=["内置天气学案例", "自定义案例"],
        default="内置天气学案例",
        key="single-mode",
    )

    reviewed_by_id = evaluation_index(reviewed_records)
    if mode == "自定义案例":
        case = {
            "case_id": st.text_input("案例编号", value="custom-001"),
            "prompt": st.text_area("用户问题", height=105),
            "candidate_answer": st.text_area("模型回答", height=135),
            "reference_answer": st.text_area("参考答案（可选）", height=135),
        }
        default_record = {
            "case_id": case["case_id"],
            "scores": {dimension: 3 for dimension in DIMENSION_LABELS},
            "error_tags": ["none"],
            "evidence": ["请记录支持评分判断的具体内容。"],
            "rationale": "请概括这段回答的主要质量表现。",
            "confidence": 0.70,
            "human_review_required": False,
            "suggested_revision": "请给出一条可执行的修改建议。",
        }
    else:
        case_labels = {
            item["case_id"]: f"{item['case_id']} · {item['domain']} · {item['difficulty']}"
            for item in cases
        }
        selected_id = st.selectbox(
            "选择案例",
            options=list(case_labels),
            format_func=lambda value: case_labels[value],
        )
        case = next(item for item in cases if item["case_id"] == selected_id)
        default_record = reviewed_by_id[selected_id]
        st.caption("当前预填内容来自已人工复核的课程样例。")

    left, right = st.columns([1.2, 1], gap="large")
    key_prefix = f"single-{case['case_id']}"
    with left:
        if mode != "自定义案例":
            render_case_context(case)
        evidence, rationale, revision = render_record_fields(
            default_record,
            key_prefix,
        )
    with right:
        scores, tags, confidence, manual_review = render_score_controls(
            default_record,
            key_prefix,
        )

    if st.button(
        "生成评测记录",
        type="primary",
        icon=":material/task_alt:",
        width="stretch",
    ):
        try:
            record = build_evaluation_record(
                case_id=case["case_id"],
                scores=scores,
                error_tags=tags,
                evidence=evidence,
                rationale=rationale,
                confidence=confidence,
                manual_review=manual_review,
                suggested_revision=revision,
            )
        except EvaluationValidationError as exc:
            st.error(f"记录未通过规则校验：{exc}")
        else:
            st.session_state["single-result"] = record
            st.session_state["single-case"] = case

    record = st.session_state.get("single-result")
    result_case = st.session_state.get("single-case")
    if record:
        st.divider()
        st.markdown("#### 结构化结果")
        result_columns = st.columns(4)
        result_columns[0].metric("平均分", f"{average_score(record):.2f} / 5")
        result_columns[1].metric("置信度", f"{record['confidence']:.0%}")
        result_columns[2].metric("错误标签", len(record["error_tags"]))
        result_columns[3].metric(
            "复核状态",
            "待复核" if record["human_review_required"] else "可归档",
        )
        with st.expander("查看 JSON", expanded=False):
            st.json(record)
        download_columns = st.columns(2)
        download_columns[0].download_button(
            "下载 JSON",
            data=json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            file_name=f"{record['case_id']}.json",
            mime="application/json",
            icon=":material/download:",
            width="stretch",
        )
        download_columns[1].download_button(
            "下载 Markdown",
            data=render_single_evaluation_markdown(record, result_case),
            file_name=f"{record['case_id']}.md",
            mime="text/markdown",
            icon=":material/download:",
            width="stretch",
        )


def render_batch_analysis(
    sample_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    source = st.segmented_control(
        "数据来源",
        options=["内置通用样例", "上传评测文件"],
        default="内置通用样例",
        key="batch-source",
    )
    records = sample_records
    if source == "上传评测文件":
        uploaded = st.file_uploader(
            "上传 JSON 或 JSONL",
            type=["json", "jsonl"],
            key="batch-upload",
        )
        if uploaded is None:
            st.info("上传评测文件后显示统计结果。")
            return []
        try:
            records = parse_records_text(
                uploaded.getvalue().decode("utf-8-sig"),
                Path(uploaded.name).suffix,
            )
        except (UnicodeDecodeError, EvaluationValidationError) as exc:
            st.error(f"无法读取文件：{exc}")
            return []

    pass_threshold = st.slider(
        "通过阈值",
        min_value=1.0,
        max_value=5.0,
        value=4.0,
        step=0.1,
        key="pass-threshold",
    )
    try:
        summary, markdown_report = summarize_records(records, pass_threshold)
    except EvaluationValidationError as exc:
        st.error(f"文件未通过规则校验：{exc}")
        return []

    metric_columns = st.columns(4)
    metric_columns[0].metric("案例总数", summary["total_cases"])
    metric_columns[1].metric(
        "平均得分",
        f"{summary['average_overall_score']:.2f} / 5",
    )
    metric_columns[2].metric("通过案例", summary["passed_cases"])
    metric_columns[3].metric("待人工复核", summary["human_review_cases"])

    chart_left, chart_right = st.columns([1.35, 1], gap="large")
    with chart_left:
        st.markdown("#### 维度均分")
        score_rows = [
            {
                "维度": DIMENSION_LABELS[dimension],
                "平均分": value,
            }
            for dimension, value in summary["average_scores"].items()
        ]
        st.bar_chart(score_rows, x="维度", y="平均分", horizontal=True)
    with chart_right:
        st.markdown("#### 错误分布")
        if summary["error_tag_counts"]:
            tag_rows = [
                {
                    "标签": ERROR_TAG_LABELS.get(tag, tag),
                    "数量": count,
                }
                for tag, count in summary["error_tag_counts"].items()
            ]
            st.bar_chart(tag_rows, x="标签", y="数量")
        else:
            st.success("当前数据没有记录明显错误标签。")

    st.markdown("#### 案例明细")
    filter_review = st.toggle("仅查看待复核案例", value=False)
    table_records = [
        {
            "案例": record["case_id"],
            "平均分": round(average_score(record), 2),
            "复核状态": (
                "待复核" if record["human_review_required"] else "可归档"
            ),
            "错误标签": "、".join(
                ERROR_TAG_LABELS.get(tag, tag) for tag in record["error_tags"]
            ),
        }
        for record in records
        if not filter_review or record["human_review_required"]
    ]
    st.dataframe(
        table_records,
        width="stretch",
        hide_index=True,
        column_config={
            "平均分": st.column_config.ProgressColumn(
                "平均分",
                min_value=1,
                max_value=5,
                format="%.2f",
            )
        },
    )

    download_columns = st.columns(2)
    download_columns[0].download_button(
        "下载汇总 JSON",
        data=json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        file_name="evaluation-summary.json",
        mime="application/json",
        icon=":material/download:",
        width="stretch",
    )
    download_columns[1].download_button(
        "下载 Markdown 报告",
        data=markdown_report,
        file_name="evaluation-report.md",
        mime="text/markdown",
        icon=":material/download:",
        width="stretch",
    )
    return records


def render_review_queue(
    cases: list[dict[str, Any]],
    reviewed_records: list[dict[str, Any]],
    batch_records: list[dict[str, Any]],
) -> None:
    source = st.segmented_control(
        "复核队列",
        options=["天气学专业样例", "当前批量数据"],
        default="天气学专业样例",
        key="review-source",
    )
    records = reviewed_records if source == "天气学专业样例" else batch_records
    if not records:
        st.info("当前批量页没有可复核数据。")
        return

    updates = st.session_state.setdefault("review-updates", {})
    working_records = merge_review_updates(records, updates)
    queue = [record for record in working_records if record["human_review_required"]]
    if not queue:
        st.success("当前队列没有强制人工复核案例。")
        return

    status_columns = st.columns(3)
    status_columns[0].metric("待复核", len(queue))
    status_columns[1].metric("本次已修改", len(updates))
    status_columns[2].metric("数据总量", len(records))

    selected_id = st.selectbox(
        "选择待复核案例",
        options=[record["case_id"] for record in queue],
        key="review-case",
    )
    current_record = deepcopy(
        next(record for record in queue if record["case_id"] == selected_id)
    )
    case_by_id = {case["case_id"]: case for case in cases}
    current_case = case_by_id.get(selected_id)

    left, right = st.columns([1.2, 1], gap="large")
    key_prefix = f"review-{selected_id}-{len(updates)}"
    with left:
        if current_case:
            render_case_context(current_case)
        evidence, rationale, revision = render_record_fields(
            current_record,
            key_prefix,
        )
    with right:
        scores, tags, confidence, manual_review = render_score_controls(
            current_record,
            key_prefix,
        )

    if st.button(
        "确认并暂存复核结果",
        type="primary",
        icon=":material/rule:",
        width="stretch",
    ):
        try:
            updated = build_evaluation_record(
                case_id=selected_id,
                scores=scores,
                error_tags=tags,
                evidence=evidence,
                rationale=rationale,
                confidence=confidence,
                manual_review=manual_review,
                suggested_revision=revision,
            )
        except EvaluationValidationError as exc:
            st.error(f"复核结果未通过规则校验：{exc}")
        else:
            updates[selected_id] = updated
            st.session_state["review-updates"] = updates
            st.success(f"{selected_id} 已暂存。")

    merged_records = merge_review_updates(records, updates)
    st.download_button(
        "下载复核后的 JSONL",
        data=records_to_jsonl(merged_records),
        file_name="reviewed-evaluations.jsonl",
        mime="application/x-ndjson",
        icon=":material/download:",
        width="stretch",
    )


stem_cases, stem_evaluations, sample_evaluations = load_project_data()

with st.sidebar:
    st.markdown("## EvalFlow")
    st.caption("LLM 回答质量评测与人工复核")
    st.divider()
    st.metric("专业案例", len(stem_cases))
    st.metric(
        "人工复核覆盖",
        f"{sum(case.get('review_status') == 'human_reviewed' for case in stem_cases)}/{len(stem_cases)}",
    )
    st.metric("评分维度", len(DIMENSION_LABELS))
    st.divider()
    st.markdown("**评测原则**")
    st.caption("证据优先 · 规则透明 · 风险升级 · 人工可控")

st.title("EvalFlow")
st.markdown(
    '<p class="muted">LLM 回答质量评测与人工复核工作台</p>',
    unsafe_allow_html=True,
)

tab_single, tab_batch, tab_review = st.tabs(
    ["单条评测", "批量分析", "人工复核"]
)

with tab_single:
    render_single_evaluation(stem_cases, stem_evaluations)

with tab_batch:
    active_batch_records = render_batch_analysis(sample_evaluations)

with tab_review:
    render_review_queue(stem_cases, stem_evaluations, active_batch_records)

st.markdown(
    """
    <div class="evidence-boundary">
    当前页面不调用真实模型 API。内置天气学结果来自已人工复核样例；
    自定义结果由评测人员填写并通过确定性规则校验，不用于宣称模型准确率或线上效果。
    </div>
    """,
    unsafe_allow_html=True,
)
