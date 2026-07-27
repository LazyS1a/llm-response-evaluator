#!/usr/bin/env python3
"""Compare V1 and V2 evaluation records for a Prompt A/B experiment."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from validate_evaluations import DIMENSIONS, load_records, validate_records


VERSION_SUFFIXES = {"v1": "-v1", "v2": "-v2"}


def split_versions(records: list[dict]) -> dict[str, list[dict]]:
    versions = {"v1": [], "v2": []}
    for record in records:
        matches = [
            version
            for version, suffix in VERSION_SUFFIXES.items()
            if record["case_id"].endswith(suffix)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"case_id must end with -v1 or -v2: {record['case_id']}"
            )
        versions[matches[0]].append(record)

    base_ids = {
        version: {
            record["case_id"][: -len(VERSION_SUFFIXES[version])]
            for record in version_records
        }
        for version, version_records in versions.items()
    }
    if base_ids["v1"] != base_ids["v2"]:
        raise ValueError("V1 and V2 case IDs do not form matching pairs")
    return versions


def summarize_version(records: list[dict]) -> dict:
    averages = {
        dimension: round(
            sum(record["scores"][dimension] for record in records) / len(records),
            3,
        )
        for dimension in DIMENSIONS
    }
    overall = round(sum(averages.values()) / len(DIMENSIONS), 3)
    error_counts = Counter(
        tag
        for record in records
        for tag in record["error_tags"]
        if tag != "none"
    )
    return {
        "cases": len(records),
        "overall_average": overall,
        "dimension_averages": averages,
        "human_review_cases": sum(
            record["human_review_required"] for record in records
        ),
        "material_error_cases": sum(
            record["error_tags"] != ["none"] for record in records
        ),
        "error_tag_counts": dict(sorted(error_counts.items())),
    }


def build_comparison(records: list[dict]) -> dict:
    versions = split_versions(records)
    v1 = summarize_version(versions["v1"])
    v2 = summarize_version(versions["v2"])
    return {
        "experiment_type": "simulated_prompt_ab_workflow",
        "disclaimer": (
            "This is a transparent simulation fixture, not a live model "
            "benchmark or evidence of production improvement."
        ),
        "v1_question_only": v1,
        "v2_reference_guided": v2,
        "delta_v2_minus_v1": {
            "overall_average": round(
                v2["overall_average"] - v1["overall_average"], 3
            ),
            "dimension_averages": {
                dimension: round(
                    v2["dimension_averages"][dimension]
                    - v1["dimension_averages"][dimension],
                    3,
                )
                for dimension in DIMENSIONS
            },
            "human_review_cases": (
                v2["human_review_cases"] - v1["human_review_cases"]
            ),
            "material_error_cases": (
                v2["material_error_cases"] - v1["material_error_cases"]
            ),
        },
    }


def render_markdown(comparison: dict) -> str:
    v1 = comparison["v1_question_only"]
    v2 = comparison["v2_reference_guided"]
    delta = comparison["delta_v2_minus_v1"]
    lines = [
        "# 模拟 Prompt V1 / V2 对比报告",
        "",
        "> **重要：这是流程演示用模拟数据，不是真实模型基准测试，不能用于宣称模型效果提升。**",
        "",
        "## 实验设计",
        "",
        "- V1：只提供问题，使用预先编写的混合质量候选答案。",
        "- V2：提供问题、人工复核参考答案和关键点，使用参考约束后的修正版。",
        "- 数据：10 条天气学 / STEM 人工复核样例。",
        "- 目的：验证 Prompt A/B 数据结构、评分、汇总和复核流程。",
        "",
        "## 汇总结果",
        "",
        "| 指标 | V1 仅问题 | V2 参考约束 | 变化 |",
        "| --- | ---: | ---: | ---: |",
        (
            f"| 五维平均分 | {v1['overall_average']:.3f} | "
            f"{v2['overall_average']:.3f} | "
            f"{delta['overall_average']:+.3f} |"
        ),
        (
            f"| 需人工复核案例 | {v1['human_review_cases']} | "
            f"{v2['human_review_cases']} | "
            f"{delta['human_review_cases']:+d} |"
        ),
        (
            f"| 含实质错误案例 | {v1['material_error_cases']} | "
            f"{v2['material_error_cases']} | "
            f"{delta['material_error_cases']:+d} |"
        ),
        "",
        "## 维度对比",
        "",
        "| 维度 | V1 | V2 | 变化 |",
        "| --- | ---: | ---: | ---: |",
    ]
    labels = {
        "relevance": "相关性",
        "factuality": "事实性",
        "completeness": "完整性",
        "instruction_following": "指令遵循",
        "clarity": "清晰度",
    }
    for dimension in DIMENSIONS:
        lines.append(
            f"| {labels[dimension]} | "
            f"{v1['dimension_averages'][dimension]:.3f} | "
            f"{v2['dimension_averages'][dimension]:.3f} | "
            f"{delta['dimension_averages'][dimension]:+.3f} |"
        )
    lines.extend(
        [
            "",
            "## 能说明什么",
            "",
            "- 已实现同一数据集下的 Prompt 版本管理、成对输出、结构化评分和自动汇总。",
            "- 已验证低事实性案例会进入人工复核流程。",
            "- 可以把模拟输出替换为真实模型原始输出，而不改动后续统计流程。",
            "",
            "## 不能说明什么",
            "",
            "- 不能证明 Codex 或其他真实模型提升了上述分数。",
            "- 不能把模拟变化量写成线上效果、准确率提升或业务收益。",
            "- 简历中只能描述实验流程与工具实现，真实效果需另行采样。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--markdown-out", type=Path, required=True)
    args = parser.parse_args()

    try:
        records = load_records(args.input)
        validate_records(records)
        comparison = build_comparison(records)
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        args.markdown_out.write_text(
            render_markdown(comparison),
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        parser.exit(1, f"comparison failed: {exc}\n")

    print(f"compared {len(records)} evaluation record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
