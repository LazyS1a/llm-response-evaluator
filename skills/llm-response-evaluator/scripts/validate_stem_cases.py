#!/usr/bin/env python3
"""Validate source-grounded STEM evaluation cases stored as JSONL."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "case_id",
    "domain",
    "difficulty",
    "prompt",
    "reference_answer",
    "key_points",
    "sources",
    "candidate_answer",
    "answer_origin",
    "review_status",
}
DIFFICULTIES = {"basic", "intermediate", "advanced"}
ANSWER_ORIGINS = {"synthetic_fixture", "real_model_output"}
REVIEW_STATUSES = {"pending_human_review", "human_reviewed"}


class StemCaseValidationError(ValueError):
    """Raised when a STEM case violates the dataset schema."""


def load_cases(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8-sig").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StemCaseValidationError(
                f"line {line_number}: invalid JSON: {exc.msg}"
            ) from exc
        if not isinstance(value, dict):
            raise StemCaseValidationError(
                f"line {line_number}: each JSONL item must be an object"
            )
        cases.append(value)
    if not cases:
        raise StemCaseValidationError("no STEM cases found")
    return cases


def _require_string(case: dict[str, Any], field: str) -> None:
    value = case.get(field)
    if not isinstance(value, str) or not value.strip():
        raise StemCaseValidationError(f"{field} must be a non-empty string")


def validate_case(case: dict[str, Any]) -> None:
    missing = sorted(REQUIRED_FIELDS - set(case))
    if missing:
        raise StemCaseValidationError(
            f"missing required fields: {', '.join(missing)}"
        )

    for field in (
        "case_id",
        "domain",
        "prompt",
        "reference_answer",
        "candidate_answer",
    ):
        _require_string(case, field)

    if not case["case_id"].startswith("stem-"):
        raise StemCaseValidationError("case_id must begin with 'stem-'")
    if case["difficulty"] not in DIFFICULTIES:
        raise StemCaseValidationError("difficulty is not supported")
    if case["answer_origin"] not in ANSWER_ORIGINS:
        raise StemCaseValidationError("answer_origin is not supported")
    if case["review_status"] not in REVIEW_STATUSES:
        raise StemCaseValidationError("review_status is not supported")

    key_points = case["key_points"]
    if (
        not isinstance(key_points, list)
        or len(key_points) < 2
        or not all(isinstance(item, str) and item.strip() for item in key_points)
    ):
        raise StemCaseValidationError(
            "key_points must contain at least two non-empty strings"
        )

    sources = case["sources"]
    if not isinstance(sources, list) or not sources:
        raise StemCaseValidationError("sources must be a non-empty array")
    for source in sources:
        if not isinstance(source, dict):
            raise StemCaseValidationError("each source must be an object")
        if set(source) != {"file", "pages", "locator"}:
            raise StemCaseValidationError(
                "each source must contain file, pages, and locator"
            )
        if not isinstance(source["file"], str) or not source["file"].endswith(".pdf"):
            raise StemCaseValidationError("source file must be a PDF filename")
        if (
            not isinstance(source["pages"], list)
            or not source["pages"]
            or not all(
                isinstance(page, int) and not isinstance(page, bool) and page > 0
                for page in source["pages"]
            )
        ):
            raise StemCaseValidationError(
                "source pages must be a non-empty array of positive integers"
            )
        if source["pages"] != sorted(set(source["pages"])):
            raise StemCaseValidationError(
                "source pages must be unique and sorted"
            )
        if not isinstance(source["locator"], str) or not source["locator"].strip():
            raise StemCaseValidationError("source locator must be non-empty")


def validate_cases(cases: list[dict[str, Any]]) -> None:
    case_ids: set[str] = set()
    for index, case in enumerate(cases, start=1):
        try:
            validate_case(case)
        except StemCaseValidationError as exc:
            raise StemCaseValidationError(f"record {index}: {exc}") from exc
        if case["case_id"] in case_ids:
            raise StemCaseValidationError(
                f"record {index}: duplicate case_id '{case['case_id']}'"
            )
        case_ids.add(case["case_id"])


def coverage(cases: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        "domains": dict(sorted(Counter(case["domain"] for case in cases).items())),
        "difficulty": dict(
            sorted(Counter(case["difficulty"] for case in cases).items())
        ),
        "answer_origin": dict(
            sorted(Counter(case["answer_origin"] for case in cases).items())
        ),
        "review_status": dict(
            sorted(Counter(case["review_status"] for case in cases).items())
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="STEM case JSONL file")
    parser.add_argument(
        "--coverage-out",
        type=Path,
        help="Optional path for dataset coverage JSON",
    )
    args = parser.parse_args()

    try:
        cases = load_cases(args.input)
        validate_cases(cases)
        if args.coverage_out:
            args.coverage_out.parent.mkdir(parents=True, exist_ok=True)
            args.coverage_out.write_text(
                json.dumps(coverage(cases), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except (OSError, StemCaseValidationError) as exc:
        parser.exit(1, f"validation failed: {exc}\n")

    print(f"validated {len(cases)} STEM case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
