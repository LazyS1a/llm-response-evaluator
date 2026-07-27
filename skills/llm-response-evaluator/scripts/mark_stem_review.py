#!/usr/bin/env python3
"""Update the human-review status of selected STEM cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_stem_cases import REVIEW_STATUSES, load_cases, validate_cases


def mark_cases(
    cases: list[dict],
    case_ids: set[str],
    status: str,
) -> list[dict]:
    known_ids = {case["case_id"] for case in cases}
    unknown_ids = sorted(case_ids - known_ids)
    if unknown_ids:
        raise ValueError("unknown case IDs: " + ", ".join(unknown_ids))

    for case in cases:
        if case["case_id"] in case_ids:
            case["review_status"] = status
    validate_cases(cases)
    return cases


def write_cases(path: Path, cases: list[dict]) -> None:
    content = "\n".join(
        json.dumps(case, ensure_ascii=False, separators=(",", ":"))
        for case in cases
    )
    path.write_text(content + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="STEM case JSONL file")
    parser.add_argument("case_ids", nargs="+", help="Case IDs to update")
    parser.add_argument(
        "--status",
        choices=sorted(REVIEW_STATUSES),
        default="human_reviewed",
    )
    args = parser.parse_args()

    try:
        cases = load_cases(args.input)
        validate_cases(cases)
        mark_cases(cases, set(args.case_ids), args.status)
        write_cases(args.input, cases)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"update failed: {exc}\n")

    print(
        f"updated {len(set(args.case_ids))} case(s) to {args.status}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
