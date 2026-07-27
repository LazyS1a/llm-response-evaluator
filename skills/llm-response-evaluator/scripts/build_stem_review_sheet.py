#!/usr/bin/env python3
"""Build a human-readable review worksheet for STEM evaluation cases."""

from __future__ import annotations

import argparse
from pathlib import Path

from validate_evaluations import load_records, validate_records
from validate_stem_cases import load_cases, validate_cases


DOMAIN_LABELS = {
    "finite_difference": "有限差分",
    "temperature_humidity": "温湿参数",
    "wind_kinematics": "风场运动学",
    "velocity_potential_streamfunction": "速度势与流函数",
    "atmospheric_moisture": "大气水汽",
    "atmospheric_stability": "大气稳定度",
}
DIFFICULTY_LABELS = {
    "basic": "基础",
    "intermediate": "进阶",
    "advanced": "高级",
}
SCORE_LABELS = {
    "relevance": "相关性",
    "factuality": "事实性",
    "completeness": "完整性",
    "instruction_following": "指令遵循",
    "clarity": "清晰度",
}
ERROR_LABELS = {
    "hallucination": "事实幻觉",
    "unsupported_claim": "缺少依据",
    "off_topic": "偏题",
    "incomplete": "信息遗漏",
    "instruction_violation": "违反指令",
    "unclear": "表述不清",
    "unsafe": "安全风险",
    "citation_mismatch": "引用不匹配",
    "none": "无明显错误",
}


def render_review_sheet(
    cases: list[dict],
    evaluations: list[dict],
) -> str:
    evaluations_by_id = {
        evaluation["case_id"]: evaluation for evaluation in evaluations
    }
    case_ids = {case["case_id"] for case in cases}
    if set(evaluations_by_id) != case_ids:
        missing = sorted(case_ids - set(evaluations_by_id))
        extra = sorted(set(evaluations_by_id) - case_ids)
        details = []
        if missing:
            details.append("missing evaluations: " + ", ".join(missing))
        if extra:
            details.append("unknown evaluations: " + ", ".join(extra))
        raise ValueError("; ".join(details))

    lines = [
        "# 天气学 / STEM 评测集人工复核表",
        "",
        "> 当前候选答案均为用于校验流程的合成样例，不是任何真实模型的跑分。",
        "> 请先查看标注页码，再决定是否接受草拟评分。",
        "",
        "## 复核方法",
        "",
        "1. 打开来源 PDF 的对应页，确认参考答案和关键点没有理解错。",
        "2. 不看草拟评分，先独立判断候选答案是否可用。",
        "3. 再比较草拟评分；若不同意，在“人工意见”中写下原因。",
        "4. 只有你亲自核过的条目，后续才可改为 `human_reviewed`。",
        "",
    ]

    for case in cases:
        evaluation = evaluations_by_id[case["case_id"]]
        reviewed = case["review_status"] == "human_reviewed"
        accepted_mark = "x" if reviewed else " "
        score_text = " / ".join(
            f"{SCORE_LABELS[name]} {score}"
            for name, score in evaluation["scores"].items()
        )
        error_text = "、".join(
            ERROR_LABELS[tag] for tag in evaluation["error_tags"]
        )
        source_text = "；".join(
            f"{source['file']}，PDF 第 {', '.join(map(str, source['pages']))} 页"
            for source in case["sources"]
        )
        lines.extend(
            [
                (
                    f"## {case['case_id']} · "
                    f"{DOMAIN_LABELS[case['domain']]} · "
                    f"{DIFFICULTY_LABELS[case['difficulty']]}"
                ),
                "",
                f"**题目：** {case['prompt']}",
                "",
                f"**参考答案：** {case['reference_answer']}",
                "",
                "**关键点：** " + "；".join(case["key_points"]),
                "",
                f"**来源：** {source_text}",
                "",
                f"**候选答案：** {case['candidate_answer']}",
                "",
                f"**草拟评分：** {score_text}",
                "",
                f"**草拟标签：** {error_text}",
                "",
                f"**草拟理由：** {evaluation['rationale']}",
                "",
                f"- [{accepted_mark}] 接受参考答案与关键点",
                f"- [{accepted_mark}] 接受草拟评分与标签",
                "- [ ] 需要修改",
                "",
                "**人工意见：** 已复核通过" if reviewed else "**人工意见：**",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path, help="STEM case JSONL file")
    parser.add_argument("evaluations", type=Path, help="Draft evaluation JSONL file")
    parser.add_argument("--output", type=Path, required=True, help="Markdown output")
    args = parser.parse_args()

    try:
        cases = load_cases(args.cases)
        validate_cases(cases)
        evaluations = load_records(args.evaluations)
        validate_records(evaluations)
        output = render_review_sheet(cases, evaluations)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"build failed: {exc}\n")

    print(f"wrote review sheet for {len(cases)} case(s) to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
