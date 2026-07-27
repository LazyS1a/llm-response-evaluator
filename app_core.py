"""Shared application logic for the EvalFlow Streamlit interface."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "skills" / "llm-response-evaluator" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from summarize_evaluations import build_summary, render_markdown  # noqa: E402
from validate_evaluations import (  # noqa: E402
    EvaluationValidationError,
    validate_record,
    validate_records,
)


DIMENSION_LABELS = {
    "relevance": "相关性",
    "factuality": "事实性",
    "completeness": "完整性",
    "instruction_following": "指令遵循",
    "clarity": "清晰度",
}

ERROR_TAG_LABELS = {
    "hallucination": "事实错误 / 幻觉",
    "unsupported_claim": "缺少依据",
    "off_topic": "答非所问",
    "incomplete": "信息不完整",
    "instruction_violation": "违反指令",
    "unclear": "表达不清",
    "unsafe": "安全风险",
    "citation_mismatch": "引用错位",
    "none": "无明显错误",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL objects without changing their original fields."""
    return parse_records_text(path.read_text(encoding="utf-8-sig"), path.suffix)


def parse_records_text(text: str, suffix: str = ".jsonl") -> list[dict[str, Any]]:
    """Parse evaluation records from JSON or JSONL text."""
    clean_text = text.strip()
    if not clean_text:
        raise EvaluationValidationError("input file is empty")

    if suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(clean_text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluationValidationError(
                    f"line {line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(item, dict):
                raise EvaluationValidationError(
                    f"line {line_number}: each JSONL item must be an object"
                )
            records.append(item)
        return records

    try:
        value = json.loads(clean_text)
    except json.JSONDecodeError as exc:
        raise EvaluationValidationError(f"invalid JSON: {exc.msg}") from exc

    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    raise EvaluationValidationError("JSON input must be an object or an array of objects")


def normalize_error_tags(tags: list[str]) -> list[str]:
    """Keep the schema-safe representation of an error tag selection."""
    unique_tags = list(dict.fromkeys(tags))
    if not unique_tags:
        return ["none"]
    if len(unique_tags) > 1 and "none" in unique_tags:
        unique_tags.remove("none")
    return unique_tags


def must_require_human_review(
    scores: dict[str, int],
    error_tags: list[str],
    confidence: float,
) -> bool:
    """Apply the evaluator's mandatory human-review rules."""
    tags = set(normalize_error_tags(error_tags))
    return (
        confidence < 0.70
        or scores["factuality"] <= 2
        or bool({"unsafe", "citation_mismatch"} & tags)
    )


def build_evaluation_record(
    *,
    case_id: str,
    scores: dict[str, int],
    error_tags: list[str],
    evidence: list[str],
    rationale: str,
    confidence: float,
    manual_review: bool,
    suggested_revision: str,
) -> dict[str, Any]:
    """Build and validate one evaluation record from UI values."""
    normalized_tags = normalize_error_tags(error_tags)
    record = {
        "case_id": case_id.strip(),
        "scores": scores,
        "error_tags": normalized_tags,
        "evidence": [item.strip() for item in evidence if item.strip()],
        "rationale": rationale.strip(),
        "confidence": round(float(confidence), 2),
        "human_review_required": manual_review
        or must_require_human_review(scores, normalized_tags, confidence),
        "suggested_revision": suggested_revision.strip(),
    }
    validate_record(record)
    return record


def records_to_jsonl(records: list[dict[str, Any]]) -> str:
    """Serialize valid records as UTF-8 friendly JSONL."""
    validate_records(records)
    return "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in records
    )


def render_single_evaluation_markdown(
    record: dict[str, Any],
    case: dict[str, Any] | None = None,
) -> str:
    """Render one evaluation as a portable Markdown review note."""
    validate_record(record)
    lines = [
        f"# 评测记录：{record['case_id']}",
        "",
    ]
    if case:
        lines.extend(
            [
                "## 评测输入",
                "",
                f"**问题**：{case.get('prompt', '未提供')}",
                "",
                f"**模型回答**：{case.get('candidate_answer', '未提供')}",
                "",
                f"**参考答案**：{case.get('reference_answer', '未提供')}",
                "",
            ]
        )

    lines.extend(
        [
            "## 五维评分",
            "",
            "| 维度 | 分数 |",
            "| --- | ---: |",
        ]
    )
    for dimension, label in DIMENSION_LABELS.items():
        lines.append(f"| {label} | {record['scores'][dimension]} |")

    tags = "、".join(
        ERROR_TAG_LABELS.get(tag, tag) for tag in record["error_tags"]
    )
    review_text = "需要" if record["human_review_required"] else "不需要"
    lines.extend(
        [
            "",
            "## 判断结果",
            "",
            f"- 错误标签：{tags}",
            f"- 置信度：{record['confidence']:.2f}",
            f"- 人工复核：{review_text}",
            f"- 评测理由：{record['rationale']}",
            f"- 修改建议：{record['suggested_revision']}",
            "",
            "## 证据",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in record["evidence"])
    lines.extend(
        [
            "",
            "> 本记录用于辅助质量判断，不代表对模型准确率或生产效果的证明。",
            "",
        ]
    )
    return "\n".join(lines)


def summarize_records(
    records: list[dict[str, Any]],
    pass_threshold: float = 4.0,
) -> tuple[dict[str, Any], str]:
    """Validate records and return both machine and human-readable reports."""
    validate_records(records)
    summary = build_summary(records, pass_threshold=pass_threshold)
    return summary, render_markdown(summary)


def merge_review_updates(
    records: list[dict[str, Any]],
    updates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace reviewed cases while preserving dataset order."""
    merged = [updates.get(record["case_id"], record) for record in records]
    validate_records(merged)
    return merged
