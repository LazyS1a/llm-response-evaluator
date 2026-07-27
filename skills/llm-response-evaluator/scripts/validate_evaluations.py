#!/usr/bin/env python3
"""Validate structured LLM response evaluations stored as JSON or JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DIMENSIONS = (
    "relevance",
    "factuality",
    "completeness",
    "instruction_following",
    "clarity",
)

ERROR_TAGS = {
    "hallucination",
    "unsupported_claim",
    "off_topic",
    "incomplete",
    "instruction_violation",
    "unclear",
    "unsafe",
    "citation_mismatch",
    "none",
}

REQUIRED_FIELDS = {
    "case_id",
    "scores",
    "error_tags",
    "evidence",
    "rationale",
    "confidence",
    "human_review_required",
    "suggested_revision",
}


class EvaluationValidationError(ValueError):
    """Raised when an evaluation record violates the schema."""


def load_records(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise EvaluationValidationError("input file is empty")

    if path.suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvaluationValidationError(
                    f"line {line_number}: invalid JSON: {exc.msg}"
                ) from exc
            if not isinstance(value, dict):
                raise EvaluationValidationError(
                    f"line {line_number}: each JSONL item must be an object"
                )
            records.append(value)
        return records

    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EvaluationValidationError(f"invalid JSON: {exc.msg}") from exc

    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    raise EvaluationValidationError("JSON input must be an object or an array of objects")


def _require_non_empty_string(record: dict[str, Any], field: str) -> None:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationValidationError(f"{field} must be a non-empty string")


def validate_record(record: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        raise EvaluationValidationError(f"missing required fields: {', '.join(missing)}")

    _require_non_empty_string(record, "case_id")
    _require_non_empty_string(record, "rationale")
    _require_non_empty_string(record, "suggested_revision")

    scores = record["scores"]
    if not isinstance(scores, dict):
        raise EvaluationValidationError("scores must be an object")
    if set(scores) != set(DIMENSIONS):
        missing_scores = sorted(set(DIMENSIONS) - set(scores))
        extra_scores = sorted(set(scores) - set(DIMENSIONS))
        details = []
        if missing_scores:
            details.append(f"missing {', '.join(missing_scores)}")
        if extra_scores:
            details.append(f"unknown {', '.join(extra_scores)}")
        raise EvaluationValidationError("invalid score dimensions: " + "; ".join(details))
    for dimension in DIMENSIONS:
        score = scores[dimension]
        if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
            raise EvaluationValidationError(
                f"scores.{dimension} must be an integer from 1 to 5"
            )

    tags = record["error_tags"]
    if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) for tag in tags):
        raise EvaluationValidationError("error_tags must be a non-empty string array")
    unknown_tags = sorted(set(tags) - ERROR_TAGS)
    if unknown_tags:
        raise EvaluationValidationError(f"unknown error tags: {', '.join(unknown_tags)}")
    if len(tags) != len(set(tags)):
        raise EvaluationValidationError("error_tags must not contain duplicates")
    if "none" in tags and len(tags) > 1:
        raise EvaluationValidationError("error tag 'none' cannot be combined with other tags")

    evidence = record["evidence"]
    if (
        not isinstance(evidence, list)
        or not evidence
        or not all(isinstance(item, str) and item.strip() for item in evidence)
    ):
        raise EvaluationValidationError("evidence must be a non-empty string array")

    confidence = record["confidence"]
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0.0 <= float(confidence) <= 1.0
    ):
        raise EvaluationValidationError("confidence must be a number from 0.0 to 1.0")

    human_review = record["human_review_required"]
    if not isinstance(human_review, bool):
        raise EvaluationValidationError("human_review_required must be a boolean")

    must_review = (
        float(confidence) < 0.70
        or scores["factuality"] <= 2
        or bool({"unsafe", "citation_mismatch"} & set(tags))
    )
    if must_review and not human_review:
        raise EvaluationValidationError(
            "human_review_required must be true for low-confidence, low-factuality, "
            "unsafe, or citation-mismatch cases"
        )


def validate_records(records: list[dict[str, Any]]) -> None:
    if not records:
        raise EvaluationValidationError("no evaluation records found")

    case_ids: set[str] = set()
    for index, record in enumerate(records, start=1):
        try:
            validate_record(record)
        except EvaluationValidationError as exc:
            raise EvaluationValidationError(f"record {index}: {exc}") from exc
        case_id = record["case_id"]
        if case_id in case_ids:
            raise EvaluationValidationError(f"record {index}: duplicate case_id '{case_id}'")
        case_ids.add(case_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON or JSONL evaluation file")
    args = parser.parse_args()

    try:
        records = load_records(args.input)
        validate_records(records)
    except (OSError, EvaluationValidationError) as exc:
        parser.exit(1, f"validation failed: {exc}\n")

    print(f"validated {len(records)} evaluation record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

