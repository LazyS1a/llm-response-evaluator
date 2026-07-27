#!/usr/bin/env python3
"""Validate and summarize structured LLM response evaluations."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import mean
from typing import Any

from validate_evaluations import DIMENSIONS, load_records, validate_records


def build_summary(
    records: list[dict[str, Any]], pass_threshold: float = 4.0
) -> dict[str, Any]:
    overall_scores = [
        mean(record["scores"][dimension] for dimension in DIMENSIONS)
        for record in records
    ]
    tag_counts = Counter(
        tag
        for record in records
        for tag in record["error_tags"]
        if tag != "none"
    )

    return {
        "total_cases": len(records),
        "average_scores": {
            dimension: round(
                mean(record["scores"][dimension] for record in records), 3
            )
            for dimension in DIMENSIONS
        },
        "average_overall_score": round(mean(overall_scores), 3),
        "pass_threshold": pass_threshold,
        "passed_cases": sum(score >= pass_threshold for score in overall_scores),
        "human_review_cases": sum(
            record["human_review_required"] for record in records
        ),
        "error_tag_counts": dict(sorted(tag_counts.items())),
        "lowest_scoring_cases": [
            {
                "case_id": record["case_id"],
                "overall_score": round(score, 3),
                "error_tags": record["error_tags"],
            }
            for record, score in sorted(
                zip(records, overall_scores),
                key=lambda item: (item[1], item[0]["case_id"]),
            )[: min(5, len(records))]
        ],
    }


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# LLM Response Evaluation Report",
        "",
        f"- Total cases: {summary['total_cases']}",
        f"- Average overall score: {summary['average_overall_score']:.3f}",
        f"- Pass threshold: {summary['pass_threshold']:.2f}",
        f"- Passed cases: {summary['passed_cases']}",
        f"- Human review cases: {summary['human_review_cases']}",
        "",
        "## Dimension Averages",
        "",
        "| Dimension | Average |",
        "| --- | ---: |",
    ]
    for dimension, value in summary["average_scores"].items():
        lines.append(f"| {dimension.replace('_', ' ').title()} | {value:.3f} |")

    lines.extend(["", "## Error Tags", ""])
    if summary["error_tag_counts"]:
        lines.extend(["| Tag | Count |", "| --- | ---: |"])
        for tag, count in summary["error_tag_counts"].items():
            lines.append(f"| {tag} | {count} |")
    else:
        lines.append("No material error tags were recorded.")

    lines.extend(
        [
            "",
            "## Lowest-Scoring Cases",
            "",
            "| Case | Overall | Error Tags |",
            "| --- | ---: | --- |",
        ]
    )
    for item in summary["lowest_scoring_cases"]:
        tags = ", ".join(item["error_tags"])
        lines.append(f"| {item['case_id']} | {item['overall_score']:.3f} | {tags} |")

    lines.extend(
        [
            "",
            "> This report summarizes rubric records; it does not prove model accuracy.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON or JSONL evaluation file")
    parser.add_argument("--json-out", type=Path, help="write summary JSON")
    parser.add_argument("--markdown-out", type=Path, help="write Markdown report")
    parser.add_argument("--pass-threshold", type=float, default=4.0)
    args = parser.parse_args()

    if not 1.0 <= args.pass_threshold <= 5.0:
        parser.error("--pass-threshold must be from 1.0 to 5.0")

    records = load_records(args.input)
    validate_records(records)
    summary = build_summary(records, args.pass_threshold)
    markdown = render_markdown(summary)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if args.markdown_out:
        args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_out.write_text(markdown, encoding="utf-8")

    if not args.json_out and not args.markdown_out:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"summarized {len(records)} evaluation record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

